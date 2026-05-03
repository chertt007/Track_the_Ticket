"""
Verification + price extraction for the final page of a price-check.

After replay (or LLM pipeline) finishes, we ask Sonnet ONE question:
"is the flight at {departure_time} visible, and if yes, what's its price?"

The departure_time on the subscription anchors the flight in the list,
so the model picks the price for OUR row, not the cheapest on the page.

Two jobs in one Anthropic call — verifier and price-reader were originally
separate agents, but they always ran back-to-back on the same screenshot.
Merging saves a round-trip and uses Sonnet's stronger vision for OCR.
"""
import base64
import logging
import os
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Optional

from anthropic import AsyncAnthropic
from playwright.async_api import Page

from agents.vision_common import (
    MODEL,
    PriceResult,
    VerificationResult,
    resolve_active_page,
    take_screenshot_b64,
)

logger = logging.getLogger(__name__)


VERIFY_PROMPT = """You are looking at a screenshot of an airline's website
showing a list of flights.

Two-step task:

1) FIND the row in the flight list whose departure time equals {time}.
   Accept any time format that means the same hour and minute, for example:
   "06:10", "6:10", "6:10 AM", "06:10 AM".
   The row must look like an actual flight schedule entry — not a generic
   clock or unrelated number elsewhere on the page.
   If the screenshot is dominated by a popup / modal / cookie banner that
   hides flight content, treat as not found.

2) If the row from step 1 exists, READ its price. If that specific row has
   multiple fare tariffs (economy / standard / flex / etc.), pick the
   cheapest one shown FOR THAT ROW — never the cheapest price on the page
   if it belongs to a different flight.

Reply with EXACTLY one line, in one of these formats:
  NO
  YES <amount> <ISO-4217 currency>
  YES NONE

Examples of valid replies:
  NO                  -- flight at {time} is not visible
  YES 12850 RUB       -- flight visible, price for that row is 12850 RUB
  YES 499.99 EUR      -- flight visible, decimal price
  YES NONE            -- flight visible, but its price is hidden / loading

Rules for the amount:
  - Strip thousands separators and currency symbols.
  - Currency code MUST be three uppercase Latin letters.

Do not explain. Do not add anything else."""


def _parse_reply(text: str) -> VerificationResult:
    """
    Parse the model's single-line reply into a VerificationResult.
    Conservative: anything malformed → not verified, no price.
    """
    parts = text.strip().split()
    if not parts:
        return VerificationResult(verified=False, price=None)

    head = parts[0].upper()
    if head == "NO":
        return VerificationResult(verified=False, price=None)
    if head != "YES":
        logger.warning(f"[verifier] unexpected reply head: {text!r}")
        return VerificationResult(verified=False, price=None)

    if len(parts) == 2 and parts[1].upper() == "NONE":
        return VerificationResult(verified=True, price=None)

    if len(parts) == 3:
        amount_raw, currency_raw = parts[1], parts[2]
        currency = currency_raw.upper()
        if len(currency) != 3 or not currency.isalpha():
            logger.warning(f"[verifier] bad currency code: {currency_raw!r}")
            return VerificationResult(verified=True, price=None)
        try:
            amount = Decimal(amount_raw)
        except InvalidOperation:
            logger.warning(f"[verifier] bad amount: {amount_raw!r}")
            return VerificationResult(verified=True, price=None)
        return VerificationResult(
            verified=True, price=PriceResult(amount=amount, currency=currency)
        )

    logger.warning(f"[verifier] unexpected YES-shape: {text!r}")
    return VerificationResult(verified=True, price=None)


async def verify_and_extract_price(
    page: Page,
    time: str,
    debug_screenshot_path: Optional[Path] = None,
) -> VerificationResult:
    """
    Single-shot Sonnet check on the current page:
      - is the flight at `time` visible?
      - if yes, what's its price (cheapest tariff in THAT row)?

    Returns VerificationResult(verified=False, price=None) on any error
    (no API key, screenshot/network/API failure, malformed reply) —
    uncertainty must not crash the surrounding price-check.

    Args:
        debug_screenshot_path: if given, the exact PNG sent to the model
            is also saved there. Useful when the verdict disagrees with
            what's on screen.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("[verifier] ANTHROPIC_API_KEY not set")
        return VerificationResult(verified=False, price=None)

    page = await resolve_active_page(page)
    try:
        screenshot_b64 = await take_screenshot_b64(page)
    except Exception as exc:
        logger.error(f"[verifier] screenshot failed: {exc}", exc_info=True)
        return VerificationResult(verified=False, price=None)

    if debug_screenshot_path is not None:
        try:
            debug_screenshot_path.parent.mkdir(parents=True, exist_ok=True)
            debug_screenshot_path.write_bytes(base64.standard_b64decode(screenshot_b64))
            logger.info(f"[verifier] debug screenshot → {debug_screenshot_path}")
        except Exception as exc:
            logger.warning(f"[verifier] could not save debug screenshot: {exc}")

    prompt = VERIFY_PROMPT.format(time=time)

    try:
        client = AsyncAnthropic(api_key=api_key)
        response = await client.messages.create(
            model=MODEL,
            max_tokens=20,
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
        return VerificationResult(verified=False, price=None)

    text = "".join(getattr(b, "text", "") for b in response.content)
    result = _parse_reply(text)
    logger.info(
        f"[verifier] raw={text!r} verified={result.verified} price={result.price} "
        f"usage={getattr(response, 'usage', None)}"
    )
    return result
