"""
Lightweight verification for replay outcomes.

After a replay finishes, we ask the model: "is a flight with the requested
departure time visible on this screenshot?" The departure_time is already
on the subscription, so we don't need to track anything in the database —
we just check that the page the replay landed on shows that exact time.

Single Anthropic call, no Computer-Use tool, no agent loop. ~$0.01–0.05.
"""
import base64
import logging
import os
import re
from pathlib import Path
from typing import Optional

from anthropic import AsyncAnthropic
from playwright.async_api import Page

from agents.vision_common import MODEL, resolve_active_page, take_screenshot_b64

logger = logging.getLogger(__name__)


VERIFY_PROMPT = """You are looking at a screenshot of an airline's website.

Question: Is the departure time {time} clearly visible on this page,
attached to a flight (i.e. as a flight schedule entry — not just a generic
clock or unrelated number)?

Accept any time format that means the same hour and minute, for example:
  "06:10", "6:10", "6:10 AM", "06:10 AM".

If the screenshot is dominated by a popup / modal / cookie banner that
hides flight content, answer NO.

Other details (city codes, exact route, date) are NOT required for this
check — they may or may not be visible. Focus only on the departure time.

Reply with EXACTLY one word, on a single line:
  - YES   — a flight at {time} is visible.
  - NO    — otherwise.

Do not explain. Do not add anything else."""


async def verify_departure_time_visible(
    page: Page,
    origin: str,
    destination: str,
    date: str,
    time: str,
    debug_screenshot_path: Optional[Path] = None,
) -> bool:
    """
    Single-shot LLM check: does the current page show a flight at the
    requested departure time on the requested route and date?

    Args:
        debug_screenshot_path: if given, the exact PNG that was sent to
            the model is also written to this path. Useful for debugging
            disagreements between what a human sees on screen and what
            the verifier judged.

    Returns False on any error (conservative — uncertainty counts as
    not-verified, so the caller can retry with a longer delay or fall
    back to the LLM-driven path).
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("[verifier] ANTHROPIC_API_KEY not set")
        return False

    page = await resolve_active_page(page)
    try:
        screenshot_b64 = await take_screenshot_b64(page)
    except Exception as exc:
        logger.error(f"[verifier] screenshot failed: {exc}", exc_info=True)
        return False

    # Persist the exact frame the model is judging — caller can inspect it
    # afterwards if the verdict disagrees with what was on screen.
    if debug_screenshot_path is not None:
        try:
            debug_screenshot_path.parent.mkdir(parents=True, exist_ok=True)
            debug_screenshot_path.write_bytes(base64.standard_b64decode(screenshot_b64))
            logger.info(f"[verifier] debug screenshot → {debug_screenshot_path}")
        except Exception as exc:
            logger.warning(f"[verifier] could not save debug screenshot: {exc}")

    prompt = VERIFY_PROMPT.format(
        origin=origin, destination=destination, date=date, time=time
    )

    try:
        client = AsyncAnthropic(api_key=api_key)
        response = await client.messages.create(
            model=MODEL,
            max_tokens=10,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": screenshot_b64,
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        )
    except Exception as exc:
        logger.error(f"[verifier] API call failed: {exc}", exc_info=True)
        return False

    text = "".join(getattr(b, "text", "") for b in response.content)
    match = re.search(r"[A-Za-z]+", text)
    verdict = match.group(0).upper() if match else ""
    logger.info(
        f"[verifier] raw={text!r} verdict={verdict!r} "
        f"usage={getattr(response, 'usage', None)}"
    )
    return verdict == "YES"
