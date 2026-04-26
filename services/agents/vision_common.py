"""
Shared building blocks for Anthropic Computer Use vision agents:
constants, action mapper (Anthropic actions → Playwright), and the
agent loop. Each agent file just supplies its own system prompt and
calls `run_agent_loop`.
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

# Throttle the loop to give us a wider safety margin against Tier 1
# rate limits (RPM and ITPM). Cheap insurance, ~45s extra over a 30-step run.
PAUSE_BETWEEN_STEPS = 1.5


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


async def take_screenshot_b64(page: Page) -> str:
    """Capture a PNG screenshot of the current viewport, return base64."""
    png_bytes = await page.screenshot(type="png", full_page=False)
    return base64.standard_b64encode(png_bytes).decode("ascii")


def _refresh_rolling_cache_marker(messages: list[dict]) -> None:
    """
    Keep a single rolling `cache_control` marker on the last user message's
    last block, and strip it from any older messages. Together with the
    static `cache_control` we put on the system prompt, this gives us
    exactly two markers per request — well under Anthropic's limit of 4 —
    while making the entire prior conversation a cache-hit on the next turn.
    """
    for msg in messages:
        if msg.get("role") != "user":
            continue
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if isinstance(block, dict) and "cache_control" in block:
                del block["cache_control"]

    for msg in reversed(messages):
        if msg.get("role") != "user":
            continue
        content = msg.get("content")
        if isinstance(content, list) and content:
            last = content[-1]
            if isinstance(last, dict):
                last["cache_control"] = {"type": "ephemeral"}
        return


async def resolve_active_page(current: Page) -> Page:
    """
    Return the page the agent should be working on right now.

    Some airlines open the booking flow in a new tab (target=_blank or
    window.open); others stay in the same tab. We always pick the most
    recently opened, non-closed page in the context — if no new tab was
    opened, that's just `current` and nothing changes. From the model's
    perspective, a tab switch is invisible: the next screenshot just
    shows the new content.
    """
    context = current.context
    candidates = [p for p in context.pages if not p.is_closed()]
    if not candidates:
        return current
    newest = candidates[-1]
    if newest is current:
        return current
    try:
        await newest.bring_to_front()
    except Exception:
        pass
    logger.info(
        f"[vision_common] active tab switched: {current.url!r} → {newest.url!r}"
    )
    return newest


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
        return
    else:
        raise ValueError(f"unsupported action: {action!r}")


async def run_agent_loop(
    page: Page,
    system_prompt: str,
    log_prefix: str = "[vision_agent]",
) -> tuple[bool, str]:
    """
    Run an Anthropic Computer Use agent loop until the model stops calling tools.

    Args:
        page:           Playwright page already navigated to the target screen.
        system_prompt:  Fully-formed system prompt (no placeholders left).
        log_prefix:     Prefix for log lines so multiple agents are distinguishable.

    Returns:
        (ok, final_text):
          - ok: True if the loop exited cleanly via end_turn, False on
                API error, timeout, MAX_STEPS, or unexpected stop_reason.
          - final_text: concatenation of the model's last text blocks
                (used by callers to detect custom signals like "Done"
                vs "No matching flight"). Empty string if there was no
                text in the final turn.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error(f"{log_prefix} ANTHROPIC_API_KEY is not set in environment")
        return False, ""
    logger.info(f"{log_prefix} API key present (len={len(api_key)})")

    try:
        client = AsyncAnthropic(api_key=api_key)
    except Exception as exc:
        logger.error(f"{log_prefix} failed to init anthropic client: {exc}", exc_info=True)
        return False, ""

    system_blocks = [
        {
            "type": "text",
            "text": system_prompt,
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

    logger.info(f"{log_prefix} taking initial screenshot…")
    try:
        page = await resolve_active_page(page)
        initial_shot = await take_screenshot_b64(page)
    except Exception as exc:
        logger.error(f"{log_prefix} initial screenshot failed: {exc}", exc_info=True)
        return False, ""

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
        f"{log_prefix} entering loop (max_steps={MAX_STEPS}, timeout={HARD_TIMEOUT_SECONDS}s)"
    )

    last_text = ""
    # Hold the active page in a mutable cell so the inner loop can
    # update it without using `nonlocal` for both fields.
    active_page = [page]

    async def _run() -> bool:
        nonlocal last_text
        for step in range(1, MAX_STEPS + 1):
            if step > 1:
                await asyncio.sleep(PAUSE_BETWEEN_STEPS)

            _refresh_rolling_cache_marker(messages)

            logger.info(f"{log_prefix} step {step} → calling Anthropic API…")
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
                    f"{log_prefix} step {step} API call failed: {type(exc).__name__}: {exc}",
                    exc_info=True,
                )
                return False
            logger.info(
                f"{log_prefix} step {step} API ok | stop_reason={response.stop_reason} "
                f"usage={getattr(response, 'usage', None)}"
            )

            assistant_blocks = [b.model_dump() for b in response.content]
            messages.append({"role": "assistant", "content": assistant_blocks})

            tool_uses = [b for b in response.content if b.type == "tool_use"]
            text_blocks = [b for b in response.content if b.type == "text"]

            text_in_turn = " ".join(tb.text for tb in text_blocks).strip()
            if text_in_turn:
                last_text = text_in_turn
                logger.info(f"{log_prefix} step {step} text: {text_in_turn!r}")

            if response.stop_reason == "end_turn" and not tool_uses:
                logger.info(f"{log_prefix} done at step {step} (end_turn)")
                return True

            if not tool_uses:
                logger.warning(
                    f"{log_prefix} step {step} no tool_use, stop_reason={response.stop_reason} — bailing"
                )
                return False

            tool_results = []
            for tu in tool_uses:
                action = tu.input.get("action")
                logger.info(f"{log_prefix} step {step} action={action} input={tu.input}")
                try:
                    await _execute_action(active_page[0], tu.input)
                except Exception as exc:
                    logger.error(
                        f"{log_prefix} step {step} action {action} failed: {exc}",
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

                # After the action, the airline may have opened a new tab.
                # Re-resolve the active page so the next screenshot reflects
                # whichever tab is now driving the booking flow.
                active_page[0] = await resolve_active_page(active_page[0])
                shot = await take_screenshot_b64(active_page[0])
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

        logger.warning(f"{log_prefix} hit MAX_STEPS={MAX_STEPS} without finishing")
        return False

    try:
        ok = await asyncio.wait_for(_run(), timeout=HARD_TIMEOUT_SECONDS)
    except asyncio.TimeoutError:
        logger.error(f"{log_prefix} hard timeout after {HARD_TIMEOUT_SECONDS}s")
        return False, last_text
    except Exception as exc:
        logger.error(f"{log_prefix} loop crashed: {exc}", exc_info=True)
        return False, last_text

    return ok, last_text
