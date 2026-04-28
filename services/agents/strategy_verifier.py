"""
Lightweight verification for replay outcomes.

After a replay finishes, we ask the model: "is a flight with the requested
departure time visible on this screenshot?" The departure_time is already
on the subscription, so we don't need to track anything in the database —
we just check that the page the replay landed on shows that exact time.

Single Anthropic call, no Computer-Use tool, no agent loop. ~$0.01–0.05.
"""
import logging
import os
import re

from anthropic import AsyncAnthropic
from playwright.async_api import Page

from agents.vision_common import MODEL, resolve_active_page, take_screenshot_b64

logger = logging.getLogger(__name__)


VERIFY_PROMPT = """You are looking at a screenshot of an airline's website
that should display flight search results or fare details for a specific flight.

Decide whether the screenshot CLEARLY shows a flight with all of:
  - Route: {origin} → {destination}
  - Date: {date}
  - Departure time: {time}

The departure time must be visible on the page (HH:MM format or equivalent,
e.g. "20:35"), attached to a flight that matches the route and date.

Reply with EXACTLY one word, on a single line:
  - YES   if such a flight is visible on the screenshot.
  - NO    otherwise.

Do not explain. Do not add anything else."""


async def verify_departure_time_visible(
    page: Page,
    origin: str,
    destination: str,
    date: str,
    time: str,
) -> bool:
    """
    Single-shot LLM check: does the current page show a flight at the
    requested departure time on the requested route and date?

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
