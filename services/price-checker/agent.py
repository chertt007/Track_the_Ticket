"""
Price-checker agent.
Uses browser-use to navigate to the airline website and find the current price.
"""

import os
from dataclasses import dataclass

from langchain_openai import ChatOpenAI
from browser_use import Agent

OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]
MODEL = "google/gemini-2.5-flash"


@dataclass
class PriceResult:
    price: float
    currency: str
    flight_number: str | None
    screenshot_base64: str | None = None
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
        "with 1 checked baggage bag included in the price"
        if with_baggage
        else "without checked baggage (hand luggage only)"
    )
    return (
        f"Go to https://{airline_domain} and find the current price for a one-way flight.\n"
        f"- Origin IATA code: {origin_iata} (type only the code into the origin field)\n"
        f"- Destination IATA code: {destination_iata} (type only the code into the destination field)\n"
        f"- Departure date: {departure_date}\n"
        f"- Passengers: 1 adult, {baggage_note}\n"
        f"- Target flight: {flight_number}\n"
        "\n"
        "Steps:\n"
        "1. Open the website.\n"
        "2. Select one-way trip mode if available.\n"
        "3. Type only the IATA code into the origin field and select the suggestion.\n"
        "4. Type only the IATA code into the destination field and select the suggestion.\n"
        f"5. Set departure date to {departure_date}.\n"
        "6. Click search and wait for results.\n"
        f"7. Find flight {flight_number} or the cheapest available flight.\n"
        "8. Take a screenshot of the results page.\n"
        "9. Return the result in EXACTLY this format:\n"
        "   PRICE: <number> <currency>\n"
        "   FLIGHT: <flight number>\n"
        f"   DATE: {departure_date}\n"
    )


async def check_price(
    airline_domain: str,
    origin_iata: str,
    destination_iata: str,
    departure_date: str,
    flight_number: str,
    with_baggage: bool = False,
) -> PriceResult:
    """Run browser-use agent to find current flight price."""
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

    agent = Agent(
        task=task,
        llm=llm,
        use_vision=True,
        enable_memory=False,
    )

    history = await agent.run()

    # Extract final text result from agent history
    raw = ""
    for action_result in history.all_results:
        if action_result.is_done and action_result.extracted_content:
            raw = action_result.extracted_content
            break

    return _parse_result(raw, flight_number)


def _parse_result(raw: str, fallback_flight: str) -> PriceResult:
    """Parse agent output into PriceResult."""
    price = 0.0
    currency = ""
    flight = fallback_flight

    for line in raw.splitlines():
        line = line.strip()
        if line.startswith("PRICE:"):
            parts = line.replace("PRICE:", "").strip().split()
            if parts:
                try:
                    price = float(parts[0].replace(",", "").replace(" ", ""))
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
        raw_output=raw,
    )
