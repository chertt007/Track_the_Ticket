"""
Price checker — runs browser-use agent to find current flight price.
Used both by the manual trigger endpoint and the scheduled Lambda.

On Windows, uvicorn runs a SelectorEventLoop which cannot spawn subprocesses
(required by Playwright). The agent is therefore run in a separate thread
that creates its own ProactorEventLoop via asyncio.run().
"""

import asyncio
import logging
import sys
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Available models for easy reference:
#   google/gemini-2.5-flash          — default, best quality for web navigation
#   qwen/qwen3-vl-8b-instruct        — 3x cheaper, good GUI understanding
AVAILABLE_MODELS = {
    "gemini": "google/gemini-2.5-flash",
    "qwen3":  "qwen/qwen3-vl-8b-instruct",
}


def _get_openrouter_key() -> str:
    """Read OPENROUTER_API_KEY from app settings (populated from .env)."""
    from app.config import settings
    return settings.openrouter_api_key


def _get_model() -> str:
    """Read active model from settings. Override via PRICE_CHECKER_MODEL in .env."""
    from app.config import settings
    return settings.price_checker_model


@dataclass
class PriceResult:
    price: float
    currency: str
    flight_number: str | None
    screenshot_b64: str | None = None
    raw_output: str = ""
    domain_used: str | None = None   # airline website domain discovered by the agent


# ── Task builder ──────────────────────────────────────────────────────────────

def _build_task(
    airline_name: str,
    airline_iata: str,
    origin_iata: str,
    destination_iata: str,
    departure_date: str,
    flight_number: str,
    with_baggage: bool,
) -> str:
    from datetime import datetime
    dt = datetime.strptime(departure_date, "%Y-%m-%d")
    departure_date_human = dt.strftime("%d %B %Y")   # e.g. "10 May 2026"
    target_year_month   = dt.strftime("%Y-%m")        # e.g. "2026-05"  (for comparison)

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


# ── Agent runner (async, runs inside its own thread's event loop) ─────────────

async def _run_agent_async(task: str) -> tuple[str, str | None]:
    """
    Runs the browser-use agent and returns (raw_text_result, screenshot_b64).
    Must be called from a thread that owns a fresh ProactorEventLoop (Windows)
    or any loop (Linux/macOS). Do NOT call from the uvicorn event loop directly.
    """
    from browser_use import Agent, Browser, BrowserConfig
    from langchain_openai import ChatOpenAI

    api_key = _get_openrouter_key()
    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not set. "
            "Add it to services/api/.env and restart the server."
        )

    model = _get_model()
    logger.info(f"price_checker: using model '{model}'")

    llm = ChatOpenAI(
        model=model,
        openai_api_key=api_key,
        openai_api_base="https://openrouter.ai/api/v1",
    )

    browser = Browser(config=BrowserConfig(keep_alive=True))
    agent = Agent(
        task=task,
        llm=llm,
        browser=browser,
        use_vision=True,
        enable_memory=False,
    )

    history = await agent.run(max_steps=50)

    # browser-use 0.1.x: final_result() returns the last extracted_content or None
    raw = history.final_result() or ""

    screenshot_b64: str | None = None
    try:
        screenshot_b64 = await agent.browser_context.take_screenshot()
    except Exception as exc:
        logger.warning(f"screenshot capture failed: {exc}")

    # Extract the domain the agent actually landed on (for caching)
    domain_used: str | None = None
    try:
        from urllib.parse import urlparse
        page = await agent.browser_context.get_current_page()
        parsed = urlparse(page.url)
        if parsed.hostname and parsed.hostname not in ("", "about:blank"):
            domain_used = parsed.hostname
    except Exception as exc:
        logger.warning(f"domain extraction failed: {exc}")

    try:
        await browser.close()
    except Exception:
        pass

    return raw, screenshot_b64, domain_used


def _run_agent_in_thread(task: str) -> tuple[str, str | None, str | None]:
    """
    Synchronous wrapper executed in a background thread.
    Creates a fresh event loop — on Windows this is ProactorEventLoop,
    which supports asyncio.create_subprocess_exec (required by Playwright).
    Returns (raw_text, screenshot_b64, domain_used).
    """
    if sys.platform == "win32":
        # Must set policy before creating the loop so asyncio.run() uses Proactor
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    return asyncio.run(_run_agent_async(task))


# ── Retry config ──────────────────────────────────────────────────────────────

# Returned by browser-use when the LLM produces no parseable action.
_AGENT_FAILURE_MARKER = "No next action returned by LLM!"

MAX_ATTEMPTS = 3          # 1 initial run + 2 retries
RETRY_DELAY_SECONDS = 5   # pause between attempts


def _is_agent_failure(raw: str) -> bool:
    """Return True if the agent produced no usable output."""
    return not raw or raw.strip() == _AGENT_FAILURE_MARKER


# ── Public entry point ────────────────────────────────────────────────────────

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
    Runs the price-check agent and returns a PriceResult.
    The agent navigates to the airline's official website using its name and IATA code —
    no hardcoded domain map needed. After a successful run, domain_used is populated
    so the caller can cache it on the subscription for future checks.
    Retries up to MAX_ATTEMPTS times if the LLM returns no action.
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
                extra={"airline": airline_name, "iata": airline_iata, "route": route, "date": departure_date, "model": model},
            )
        else:
            logger.warning(
                "price_checker: retrying agent after failure",
                extra={
                    "attempt": attempt,
                    "max_attempts": MAX_ATTEMPTS,
                    "airline": airline_name,
                    "route": route,
                    "date": departure_date,
                    "previous_raw": raw,
                },
            )
            await asyncio.sleep(RETRY_DELAY_SECONDS)

        # Run in a separate thread so Playwright gets a fresh ProactorEventLoop on Windows
        raw, screenshot_b64, domain_used = await asyncio.to_thread(_run_agent_in_thread, task)

        logger.info(
            "price_checker: agent raw output",
            extra={"attempt": attempt, "raw": raw, "route": route, "domain_used": domain_used, "model": model},
        )

        if not _is_agent_failure(raw):
            # Agent produced a result — proceed
            break

        # Log the failure to CloudWatch with enough context to query later
        logger.error(
            "price_checker: agent returned no action",
            extra={
                "attempt": attempt,
                "max_attempts": MAX_ATTEMPTS,
                "airline": airline_name,
                "route": route,
                "date": departure_date,
                "raw": raw,
                "will_retry": attempt < MAX_ATTEMPTS,
            },
        )

    return _parse_result(raw, flight_number, screenshot_b64, domain_used)


# ── Result parser ─────────────────────────────────────────────────────────────

def _parse_result(raw: str, fallback_flight: str, screenshot_b64: str | None, domain_used: str | None = None) -> PriceResult:
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
