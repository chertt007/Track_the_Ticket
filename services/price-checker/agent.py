"""
Price-checker agent.
Uses browser-use to navigate to the airline's official website and find the current price.

This module runs inside the price-checker Lambda (Linux, headless Chromium).
It mirrors the logic in services/api/app/price_checker.py but is self-contained
with no FastAPI or API-specific imports.
"""

import asyncio
import logging
import os
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


# ── Result dataclass ───────────────────────────────────────────────────────────

@dataclass
class PriceResult:
    price: float
    currency: str
    flight_number: str | None
    screenshot_b64: str | None = None
    raw_output: str = ""
    domain_used: str | None = None


# ── Config helpers ─────────────────────────────────────────────────────────────

def _get_openrouter_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY environment variable is not set.")
    return key


def _get_model() -> str:
    return os.environ.get("PRICE_CHECKER_MODEL", "google/gemini-2.5-flash")


# ── Task builder ───────────────────────────────────────────────────────────────

def _build_task(
    airline_name: str,
    airline_iata: str,
    origin_iata: str,
    destination_iata: str,
    departure_date: str,
    flight_number: str,
    with_baggage: bool,
) -> str:
    dt = datetime.strptime(departure_date, "%Y-%m-%d")
    departure_date_human = dt.strftime("%d %B %Y")   # e.g. "24 April 2026"
    target_year_month   = dt.strftime("%Y-%m")        # e.g. "2026-04"

    baggage_note = (
        "with 1 checked baggage bag included"
        if with_baggage
        else "without checked baggage (hand luggage only)"
    )
    flight_hint = f"flight {flight_number}" if flight_number else "the cheapest available flight"

    return (
        f"Go to the OFFICIAL website of {airline_name} (IATA code: {airline_iata}) "
        f"and find the price for a one-way flight.\n"
        f"IMPORTANT: Navigate directly to the airline's own booking website. "
        f"Do NOT use Google Flights, Expedia, Kayak, Skyscanner, or any other aggregator.\n"
        f"\n"
        f"- Origin: type first two letters of IATA code '{origin_iata}' into the origin field, "
        f"wait for the dropdown, then select the correct airport from the list.\n"
        f"- Destination: type first two letters of IATA code '{destination_iata}' into the destination field, "
        f"wait for the dropdown, then select the correct airport from the list.\n"
        f"- Departure date: {departure_date_human} (ISO: {departure_date})\n"
        f"- Passengers: 1 adult, {baggage_note}\n"
        "\n"
        "Steps:\n"
        "1. Open the official airline website.\n"
        "2. Select one-way trip mode if available.\n"
        f"3. Type first two letters of '{origin_iata}' into the origin field, wait for dropdown, "
        f"select the airport matching IATA code {origin_iata}.\n"
        f"4. Type first two letters of '{destination_iata}' into the destination field, wait for dropdown, "
        f"select the airport matching IATA code {destination_iata}.\n"
        f"5. Set departure date to {departure_date_human}. When the datepicker opens:\n"
        f"   a. Read the MONTH and YEAR shown in the calendar header (e.g. 'May 2026').\n"
        f"   b. The target month is: {departure_date_human}. Convert it to YYYY-MM = {target_year_month}.\n"
        f"      Convert the visible header month to YYYY-MM the same way and compare:\n"
        f"      - If visible YYYY-MM > {target_year_month}: the calendar is TOO FAR AHEAD — click '<' or 'prev'.\n"
        f"      - If visible YYYY-MM < {target_year_month}: the calendar is TOO FAR BACK — click '>' or 'next'.\n"
        f"      - If visible YYYY-MM == {target_year_month}: the correct month is shown — click day {dt.day}.\n"
        f"   c. After each navigation click, re-read the header and repeat step (b).\n"
        f"   d. Do NOT click the date until the correct month AND year are visible in the header.\n"
        f"   e. IMPORTANT: if after 15 navigation clicks you still cannot reach {departure_date_human}, "
        f"stop immediately and call done with success=False.\n"
        "6. Click the main SEARCH / FIND FLIGHTS button on the booking form "
        "(it may be labeled 'Search', 'Find flights', 'Search flights', 'Book now', etc.). "
        "Do NOT click on any advertisements, banners, promotional offers, or pop-ups — "
        "focus only on the primary submit button of the search form. "
        "After clicking, wait for the results page to load.\n"
        f"7. Find {flight_hint}.\n"
        "8. Return the result in EXACTLY this format:\n"
        "   PRICE: <number> <currency>\n"
        "   FLIGHT: <flight number>\n"
        f"   DATE: {departure_date}\n"
    )


# ── Agent runner ───────────────────────────────────────────────────────────────

async def _run_agent_async(task: str) -> tuple[str, str | None, str | None]:
    """
    Runs the browser-use agent.
    Returns (raw_text, screenshot_b64, domain_used).
    Must be called from a fresh event loop (use asyncio.run()).
    """
    from browser_use import Agent, Browser, BrowserConfig
    from langchain_openai import ChatOpenAI

    api_key = _get_openrouter_key()
    model   = _get_model()

    logger.info(f"agent: initializing LLM model={model}")

    llm = ChatOpenAI(
        model=model,
        openai_api_key=api_key,
        openai_api_base="https://openrouter.ai/api/v1",
    )

    # headless=False — same as running locally.
    # Xvfb is started by entrypoint.sh (xvfb-run) before Lambda bootstrap,
    # so DISPLAY is already set when Python starts. No subprocess magic needed.
    # --disable-gpu: GPU acceleration is unavailable in Xvfb; without this flag
    # Chrome hangs when Playwright tries to capture a screenshot (rendering stall).
    # --disable-dev-shm-usage: /dev/shm in Lambda is tiny (64MB); Chrome uses it
    # for shared memory between renderer processes — overflow causes crashes.
    logger.info("agent: launching browser (headless=False, display via Xvfb entrypoint)")
    browser = Browser(config=BrowserConfig(
        headless=False,
        keep_alive=False,
        extra_chromium_args=["--disable-gpu", "--disable-dev-shm-usage"],
    ))
    agent = Agent(
        task=task,
        llm=llm,
        browser=browser,
        use_vision=True,
        enable_memory=False,
    )

    logger.info("agent: starting agent.run(max_steps=50)")
    history = await agent.run(max_steps=50)
    raw = history.final_result() or ""
    logger.info(
        "agent: run() completed",
        extra={
            "raw_length": len(raw),
            "raw_preview": raw[:300] if raw else "<empty>",
            "steps_taken": len(history.history) if hasattr(history, "history") else "unknown",
        },
    )

    screenshot_b64: str | None = None
    try:
        screenshot_b64 = await agent.browser_context.take_screenshot()
        logger.info(f"agent: screenshot captured ({len(screenshot_b64)} chars b64)")
    except Exception as exc:
        logger.warning(f"screenshot capture failed: {exc}")

    domain_used: str | None = None
    try:
        from urllib.parse import urlparse
        page = await agent.browser_context.get_current_page()
        parsed = urlparse(page.url)
        if parsed.hostname and parsed.hostname not in ("", "about:blank"):
            domain_used = parsed.hostname
            logger.info(f"agent: final page domain = {domain_used}")
    except Exception as exc:
        logger.warning(f"domain extraction failed: {exc}")

    try:
        await browser.close()
        logger.info("agent: browser closed")
    except Exception:
        pass

    return raw, screenshot_b64, domain_used


# ── Result parser ──────────────────────────────────────────────────────────────

_AGENT_FAILURE_MARKER = "No next action returned by LLM!"


def _is_agent_failure(raw: str) -> bool:
    return not raw or raw.strip() == _AGENT_FAILURE_MARKER


def _parse_result(
    raw: str,
    fallback_flight: str,
    screenshot_b64: str | None,
    domain_used: str | None,
) -> PriceResult:
    price = 0.0
    currency = "RUB"
    flight = fallback_flight or None

    for line in raw.splitlines():
        line = line.strip()
        if line.startswith("PRICE:"):
            parts = line.replace("PRICE:", "").strip().split()
            if parts:
                try:
                    price = float(
                        parts[0]
                        .replace(",", "")
                        .replace("\xa0", "")
                        .replace("\u202f", "")
                        .replace(" ", "")
                    )
                except ValueError:
                    pass
            if len(parts) > 1:
                currency = parts[1].upper()
        elif line.startswith("FLIGHT:"):
            value = line.replace("FLIGHT:", "").strip()
            if value:
                flight = value

    return PriceResult(
        price=price,
        currency=currency,
        flight_number=flight,
        screenshot_b64=screenshot_b64,
        raw_output=raw,
        domain_used=domain_used,
    )


# ── Public entry point ─────────────────────────────────────────────────────────

MAX_ATTEMPTS     = 3
RETRY_DELAY_SECS = 5


async def run_price_check(
    airline_name: str,
    airline_iata: str,
    origin_iata: str,
    destination_iata: str,
    departure_date: str,
    flight_number: str,
    with_baggage: bool = False,
) -> PriceResult:
    """
    Runs the browser-use agent and returns a PriceResult.
    Retries up to MAX_ATTEMPTS times on LLM failure.
    This is an async function — call it from asyncio.run().
    """
    model = _get_model()
    route = f"{origin_iata}->{destination_iata}"
    task = _build_task(
        airline_name=airline_name,
        airline_iata=airline_iata,
        origin_iata=origin_iata,
        destination_iata=destination_iata,
        departure_date=departure_date,
        flight_number=flight_number,
        with_baggage=with_baggage,
    )

    raw: str = ""
    screenshot_b64: str | None = None
    domain_used: str | None = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        if attempt == 1:
            logger.info(
                "price_checker: starting agent",
                extra={"airline": airline_name, "route": route, "date": departure_date, "model": model},
            )
        else:
            logger.warning(
                "price_checker: retrying after failure",
                extra={"attempt": attempt, "route": route, "previous_raw": raw},
            )
            await asyncio.sleep(RETRY_DELAY_SECS)

        try:
            raw, screenshot_b64, domain_used = await _run_agent_async(task)
        except Exception as exc:
            logger.error(
                "price_checker: agent raised exception",
                extra={"attempt": attempt, "error": str(exc), "route": route},
                exc_info=True,
            )
            raw = ""

        logger.info(
            "price_checker: agent raw output",
            extra={"attempt": attempt, "raw": raw, "route": route, "model": model},
        )

        if not _is_agent_failure(raw):
            break

        logger.error(
            "price_checker: agent returned no action",
            extra={"attempt": attempt, "max_attempts": MAX_ATTEMPTS, "will_retry": attempt < MAX_ATTEMPTS},
        )

    return _parse_result(raw, flight_number, screenshot_b64, domain_used)
