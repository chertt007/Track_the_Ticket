"""
Price checker — runs browser-use agent to find current flight price.
Used both by the manual trigger endpoint and the scheduled Lambda.
"""

import base64
import logging
import os
from dataclasses import dataclass, field

from browser_use import Agent, Browser, BrowserConfig
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
MODEL = "google/gemini-2.5-flash"


@dataclass
class PriceResult:
    price: float
    currency: str
    flight_number: str
    screenshot_b64: str | None = None
    raw_output: str = ""


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
    return (
        f"Go to https://{airline_domain} and find the price for a one-way flight.\n"
        f"- Origin: type only IATA code '{origin_iata}' into the origin field and select the suggestion.\n"
        f"- Destination: type only IATA code '{destination_iata}' into the destination field and select the suggestion.\n"
        f"- Departure date: {departure_date}\n"
        f"- Passengers: 1 adult, {baggage_note}\n"
        f"- Target flight: {flight_number}\n"
        "\n"
        "Steps:\n"
        "1. Open the website.\n"
        "2. Select one-way trip mode if available.\n"
        "3. Type only the IATA code into origin and select the suggestion.\n"
        "4. Type only the IATA code into destination and select the suggestion.\n"
        f"5. Set departure date to {departure_date}.\n"
        "6. Click search and wait for results to load.\n"
        f"7. Find flight {flight_number} or the cheapest available.\n"
        "8. Return the result in EXACTLY this format:\n"
        "   PRICE: <number> <currency>\n"
        "   FLIGHT: <flight number>\n"
        f"   DATE: {departure_date}\n"
    )


async def run_price_check(
    airline_domain: str,
    origin_iata: str,
    destination_iata: str,
    departure_date: str,
    flight_number: str,
    with_baggage: bool = False,
) -> PriceResult:
    llm = ChatOpenAI(
        model=MODEL,
        openai_api_key=OPENROUTER_API_KEY,
        openai_api_base="https://openrouter.ai/api/v1",
    )

    task = _build_task(
        airline_domain=airline_domain,
        origin_iata=origin_iata,
        destination_iata=destination_iata,
        departure_date=departure_date,
        flight_number=flight_number,
        with_baggage=with_baggage,
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

    # Extract text result
    raw = ""
    for result in history.all_results:
        if result.is_done and result.extracted_content:
            raw = result.extracted_content
            break

    # Capture screenshot of the final page
    screenshot_b64 = None
    try:
        screenshot_b64 = await agent.browser_context.take_screenshot()
    except Exception as e:
        logger.warning(f"screenshot capture failed: {e}")

    try:
        await browser.close()
    except Exception:
        pass

    return _parse_result(raw, flight_number, screenshot_b64)


def _parse_result(raw: str, fallback_flight: str, screenshot_b64: str | None) -> PriceResult:
    price = 0.0
    currency = "RUB"
    flight = fallback_flight

    for line in raw.splitlines():
        line = line.strip()
        if line.startswith("PRICE:"):
            parts = line.replace("PRICE:", "").strip().split()
            if parts:
                try:
                    price = float(parts[0].replace(",", "").replace("\xa0", "").replace(" ", ""))
                except ValueError:
                    pass
            if len(parts) > 1:
                currency = parts[1]
        elif line.startswith("FLIGHT:"):
            flight = line.replace("FLIGHT:", "").strip() or fallback_flight

    return PriceResult(
        price=price,
        currency=currency,
        flight_number=flight,
        screenshot_b64=screenshot_b64,
        raw_output=raw,
    )
