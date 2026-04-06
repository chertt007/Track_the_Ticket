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

MODEL = "google/gemini-2.5-flash"


def _get_openrouter_key() -> str:
    """Read OPENROUTER_API_KEY from app settings (populated from .env)."""
    from app.config import settings
    return settings.openrouter_api_key


@dataclass
class PriceResult:
    price: float
    currency: str
    flight_number: str | None
    screenshot_b64: str | None = None
    raw_output: str = ""


# ── Task builder ──────────────────────────────────────────────────────────────

def _build_task(
    airline_domain: str,
    origin_iata: str,
    destination_iata: str,
    departure_date: str,
    flight_number: str,
    with_baggage: bool,
) -> str:
    baggage_note = (
        "with 1 checked baggage bag included"
        if with_baggage
        else "without checked baggage (hand luggage only)"
    )
    flight_hint = f"flight {flight_number}" if flight_number else "the cheapest available flight"
    return (
        f"Go to https://{airline_domain} and find the price for a one-way flight.\n"
        f"- Origin: type only IATA code '{origin_iata}' into the origin field and select the suggestion.\n"
        f"- Destination: type only IATA code '{destination_iata}' into the destination field and select the suggestion.\n"
        f"- Departure date: {departure_date}\n"
        f"- Passengers: 1 adult, {baggage_note}\n"
        "\n"
        "Steps:\n"
        "1. Open the website.\n"
        "2. Select one-way trip mode if available.\n"
        "3. Type only the IATA code into origin and select the suggestion.\n"
        "4. Type only the IATA code into destination and select the suggestion.\n"
        f"5. Set departure date to {departure_date}.\n"
        "6. Click search and wait for results to load.\n"
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

    llm = ChatOpenAI(
        model=MODEL,
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

    history = await agent.run()

    # browser-use 0.1.x: final_result() returns the last extracted_content or None
    raw = history.final_result() or ""

    screenshot_b64: str | None = None
    try:
        screenshot_b64 = await agent.browser_context.take_screenshot()
    except Exception as exc:
        logger.warning(f"screenshot capture failed: {exc}")

    try:
        await browser.close()
    except Exception:
        pass

    return raw, screenshot_b64


def _run_agent_in_thread(task: str) -> tuple[str, str | None]:
    """
    Synchronous wrapper executed in a background thread.
    Creates a fresh event loop — on Windows this is ProactorEventLoop,
    which supports asyncio.create_subprocess_exec (required by Playwright).
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
    airline_domain: str,
    origin_iata: str,
    destination_iata: str,
    departure_date: str,
    flight_number: str,
    with_baggage: bool = False,
) -> PriceResult:
    """
    Runs the price-check agent and returns a PriceResult.
    Retries up to MAX_ATTEMPTS times if the LLM returns no action.
    Safe to await from any async context (FastAPI, Lambda, tests).
    The heavy browser work runs in a separate thread with its own event loop.
    """
    route = f"{origin_iata}->{destination_iata}"
    task = _build_task(
        airline_domain=airline_domain,
        origin_iata=origin_iata,
        destination_iata=destination_iata,
        departure_date=departure_date,
        flight_number=flight_number,
        with_baggage=with_baggage,
    )

    raw: str = ""
    screenshot_b64: str | None = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        if attempt == 1:
            logger.info(
                "price_checker: starting agent",
                extra={"airline_domain": airline_domain, "route": route, "date": departure_date},
            )
        else:
            logger.warning(
                "price_checker: retrying agent after failure",
                extra={
                    "attempt": attempt,
                    "max_attempts": MAX_ATTEMPTS,
                    "airline_domain": airline_domain,
                    "route": route,
                    "date": departure_date,
                    "previous_raw": raw,
                },
            )
            await asyncio.sleep(RETRY_DELAY_SECONDS)

        # Run in a separate thread so Playwright gets a fresh ProactorEventLoop on Windows
        raw, screenshot_b64 = await asyncio.to_thread(_run_agent_in_thread, task)

        logger.info(
            "price_checker: agent raw output",
            extra={"attempt": attempt, "raw": raw, "route": route},
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
                "airline_domain": airline_domain,
                "route": route,
                "date": departure_date,
                "raw": raw,
                "will_retry": attempt < MAX_ATTEMPTS,
            },
        )

    return _parse_result(raw, flight_number, screenshot_b64)


# ── Result parser ─────────────────────────────────────────────────────────────

def _parse_result(raw: str, fallback_flight: str, screenshot_b64: str | None) -> PriceResult:
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
    )
