"""
Agent: fill the flight-search form on an airline's website using
Anthropic Computer Use (Sonnet + computer_20250124 tool).

The model sees screenshots and returns mouse / keyboard actions; we execute
them in Playwright. The browser session is provided by the caller and is
NOT closed here — extracting the price / screenshotting results is a separate
stage on the same Page.
"""
import asyncio
import base64
import logging
import os
from typing import Any

from anthropic import AsyncAnthropic
from playwright.async_api import Page

logger = logging.getLogger(__name__)

# Computer Use is currently bound to Sonnet 4.5 — Sonnet 4.6 does not yet
# expose the `computer_20250124` tool (Anthropic returns 400).
MODEL = "claude-sonnet-4-5"
BETA_HEADER = "computer-use-2025-01-24"
TOOL_VERSION = "computer_20250124"

VIEWPORT_WIDTH = 1280
VIEWPORT_HEIGHT = 800

MAX_STEPS = 30
HARD_TIMEOUT_SECONDS = 300
MAX_TOKENS_PER_TURN = 4096


SYSTEM_PROMPT = """You are a browser automation agent. The airline's website is already open in the browser.
Your only job is to fill out the flight-search form.

GOAL:
- "From" / "Origin" airport: {origin}
- "To" / "Destination" airport: {destination}
- Departure date: {date}
- After all three are set, click the search / find button.

BEFORE FILLING THE FORM:
- If a cookie / GDPR banner covers the page, dismiss it first.
- If a promotional modal or popup is blocking the form, close it.
- If the form is not visible, scroll down until you can see it.
- If the site asks for a language, pick English.

ONLY TOUCH:
- The three fields above and the search button.

DO NOT TOUCH:
- Trip type (one-way / round-trip) — leave default.
- Return-date field — leave empty.
- Passenger count, cabin class, promo codes.

WHEN DONE:
- Once the search button has been clicked and results start to load,
  reply with the single word "Done" and stop calling tools.

Do not navigate away. Do not open new tabs. If the screenshot is ambiguous,
take another screenshot or wait briefly and reassess."""


# xdotool key names → Playwright key names. Only entries that actually differ.
KEY_MAP = {
    "Return": "Enter",
    "KP_Enter": "Enter",
    "Escape": "Escape",
    "BackSpace": "Backspace",
    "Delete": "Delete",
    "Tab": "Tab",
    "Home": "Home",
    "End": "End",
    "Page_Up": "PageUp",
    "Page_Down": "PageDown",
    "Up": "ArrowUp",
    "Down": "ArrowDown",
    "Left": "ArrowLeft",
    "Right": "ArrowRight",
    "space": " ",
    "ctrl": "Control",
    "alt": "Alt",
    "shift": "Shift",
    "super": "Meta",
    "cmd": "Meta",
    "win": "Meta",
}


def _translate_key(xdo_key: str) -> str:
    """Convert an xdotool-style key (possibly a combo like 'ctrl+a') to Playwright."""
    parts = xdo_key.split("+")
    translated = [KEY_MAP.get(p, KEY_MAP.get(p.lower(), p)) for p in parts]
    return "+".join(translated)


async def _take_screenshot_b64(page: Page) -> str:
    """Capture a PNG screenshot of the current viewport, return base64."""
    png_bytes = await page.screenshot(type="png", full_page=False)
    return base64.standard_b64encode(png_bytes).decode("ascii")


async def _execute_action(page: Page, action_input: dict[str, Any]) -> None:
    """Translate a single Anthropic computer-tool action into a Playwright call."""
    action = action_input.get("action")
    coord = action_input.get("coordinate")

    if action == "screenshot":
        return  # caller will take the screenshot afterwards anyway

    if action == "left_click":
        x, y = coord
        await page.mouse.click(x, y)
    elif action == "right_click":
        x, y = coord
        await page.mouse.click(x, y, button="right")
    elif action == "middle_click":
        x, y = coord
        await page.mouse.click(x, y, button="middle")
    elif action == "double_click":
        x, y = coord
        await page.mouse.dblclick(x, y)
    elif action == "triple_click":
        x, y = coord
        await page.mouse.click(x, y, click_count=3)
    elif action == "mouse_move":
        x, y = coord
        await page.mouse.move(x, y)
    elif action == "left_click_drag":
        sx, sy = action_input["start_coordinate"]
        ex, ey = coord
        await page.mouse.move(sx, sy)
        await page.mouse.down()
        await page.mouse.move(ex, ey)
        await page.mouse.up()
    elif action == "left_mouse_down":
        await page.mouse.down()
    elif action == "left_mouse_up":
        await page.mouse.up()
    elif action == "type":
        await page.keyboard.type(action_input["text"])
    elif action == "key":
        await page.keyboard.press(_translate_key(action_input["text"]))
    elif action == "hold_key":
        key = _translate_key(action_input["text"])
        duration = float(action_input.get("duration", 1.0))
        await page.keyboard.down(key)
        await asyncio.sleep(duration)
        await page.keyboard.up(key)
    elif action == "scroll":
        x, y = coord
        direction = action_input.get("scroll_direction", "down")
        amount = int(action_input.get("scroll_amount", 3))
        # 100px per "click" of the wheel feels close to a real scroll.
        dy = amount * 100 * (1 if direction == "down" else -1) if direction in ("down", "up") else 0
        dx = amount * 100 * (1 if direction == "right" else -1) if direction in ("left", "right") else 0
        await page.mouse.move(x, y)
        await page.mouse.wheel(dx, dy)
    elif action == "wait":
        await asyncio.sleep(float(action_input.get("duration", 1.0)))
    elif action == "cursor_position":
        # Read-only; no mutation. Caller's screenshot is the response.
        return
    else:
        raise ValueError(f"unsupported action: {action!r}")


async def fill_search_form(
    page: Page,
    origin_iata: str,
    destination_iata: str,
    departure_date: str,
    departure_time: str,
) -> bool:
    """
    Drive the airline's flight-search form to a submitted state via Anthropic
    Computer Use. The browser must already be navigated to the airline's site
    and sized to (VIEWPORT_WIDTH, VIEWPORT_HEIGHT).

    Note: `departure_time` is accepted now so the call site is stable for the
    next stage (picking the right flight from results), but it is NOT included
    in the system prompt at this stage — the form itself does not know about it.

    Returns True if the loop exited cleanly (model said it was done).
    """
    logger.info(
        f"[vision_search_agent] called | {origin_iata}→{destination_iata} on {departure_date} (time={departure_time})"
    )

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("[vision_search_agent] ANTHROPIC_API_KEY is not set in environment")
        return False
    logger.info(f"[vision_search_agent] API key present (len={len(api_key)})")

    try:
        client = AsyncAnthropic(api_key=api_key)
        logger.info(f"[vision_search_agent] anthropic client OK; model={MODEL}")
    except Exception as exc:
        logger.error(f"[vision_search_agent] failed to init anthropic client: {exc}", exc_info=True)
        return False

    system_blocks = [
        {
            "type": "text",
            "text": SYSTEM_PROMPT.format(
                origin=origin_iata,
                destination=destination_iata,
                date=departure_date,
            ),
            "cache_control": {"type": "ephemeral"},
        }
    ]

    tools = [
        {
            "type": TOOL_VERSION,
            "name": "computer",
            "display_width_px": VIEWPORT_WIDTH,
            "display_height_px": VIEWPORT_HEIGHT,
            "display_number": 1,
        }
    ]

    logger.info("[vision_search_agent] taking initial screenshot…")
    try:
        initial_shot = await _take_screenshot_b64(page)
        logger.info(f"[vision_search_agent] initial screenshot OK (b64 len={len(initial_shot)})")
    except Exception as exc:
        logger.error(f"[vision_search_agent] initial screenshot failed: {exc}", exc_info=True)
        return False

    messages: list[dict[str, Any]] = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Begin."},
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": initial_shot,
                    },
                },
            ],
        }
    ]

    logger.info(
        f"[vision_search_agent] entering loop (max_steps={MAX_STEPS}, timeout={HARD_TIMEOUT_SECONDS}s)"
    )

    async def _run_loop() -> bool:
        for step in range(1, MAX_STEPS + 1):
            logger.info(f"[vision_search_agent] step {step} → calling Anthropic API…")
            try:
                response = await client.beta.messages.create(
                    model=MODEL,
                    max_tokens=MAX_TOKENS_PER_TURN,
                    system=system_blocks,
                    tools=tools,
                    betas=[BETA_HEADER],
                    messages=messages,
                )
            except Exception as exc:
                logger.error(
                    f"[vision_search_agent] step {step} API call failed: {type(exc).__name__}: {exc}",
                    exc_info=True,
                )
                return False
            logger.info(
                f"[vision_search_agent] step {step} API ok | stop_reason={response.stop_reason} "
                f"usage={getattr(response, 'usage', None)}"
            )

            assistant_blocks = [b.model_dump() for b in response.content]
            messages.append({"role": "assistant", "content": assistant_blocks})

            tool_uses = [b for b in response.content if b.type == "tool_use"]
            text_blocks = [b for b in response.content if b.type == "text"]
            for tb in text_blocks:
                logger.info(f"[vision_search_agent] step {step} text: {tb.text!r}")

            if response.stop_reason == "end_turn" and not tool_uses:
                logger.info(f"[vision_search_agent] done at step {step} (end_turn)")
                return True

            if not tool_uses:
                logger.warning(
                    f"[vision_search_agent] step {step} no tool_use, stop_reason={response.stop_reason} — bailing"
                )
                return False

            tool_results = []
            for tu in tool_uses:
                action = tu.input.get("action")
                logger.info(f"[vision_search_agent] step {step} action={action} input={tu.input}")
                try:
                    await _execute_action(page, tu.input)
                except Exception as exc:
                    logger.error(
                        f"[vision_search_agent] step {step} action {action} failed: {exc}",
                        exc_info=True,
                    )
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": tu.id,
                            "content": f"Error executing {action}: {exc}",
                            "is_error": True,
                        }
                    )
                    continue

                shot = await _take_screenshot_b64(page)
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": tu.id,
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": shot,
                                },
                            }
                        ],
                    }
                )

            messages.append({"role": "user", "content": tool_results})

        logger.warning(f"[vision_search_agent] hit MAX_STEPS={MAX_STEPS} without finishing")
        return False

    try:
        return await asyncio.wait_for(_run_loop(), timeout=HARD_TIMEOUT_SECONDS)
    except asyncio.TimeoutError:
        logger.error(f"[vision_search_agent] hard timeout after {HARD_TIMEOUT_SECONDS}s")
        return False
    except Exception as exc:
        logger.error(f"[vision_search_agent] loop crashed: {exc}", exc_info=True)
        return False
