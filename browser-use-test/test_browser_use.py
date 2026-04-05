"""
browser-use PoC: find flight price on flypobeda.ru
Route: VKO -> LED, departure 2026-04-08
"""

import asyncio
import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from browser_use import Agent

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
ORIGIN = "VKO"
DESTINATION = "LED"
DEPARTURE_DATE = "2026-04-08"
AIRLINE_URL = "https://www.flypobeda.ru"

TASK = (
    f"Go to {AIRLINE_URL} and find the price for a one-way flight.\n"
    f"- Origin airport: Vnukovo (VKO), Moscow\n"
    f"- Destination: Pulkovo (LED), Saint Petersburg\n"
    f"- Departure date: {DEPARTURE_DATE}\n"
    "- Passengers: 1 adult, no baggage\n"
    "\n"
    "Steps:\n"
    "1. Open the website.\n"
    "2. Select one-way trip mode if available.\n"
    "3. Set the origin: type only the IATA code 'VKO' into the origin field and select the suggestion.\n"
    "4. Set the destination: type only the IATA code 'LED' into the destination field and select the suggestion.\n"
    f"5. Set the departure date to {DEPARTURE_DATE}.\n"
    "6. Click the search button.\n"
    "7. Wait for the results page to load.\n"
    "8. Find the cheapest available flight price and currency.\n"
    "9. Return the result in this exact format:\n"
    "   PRICE: <amount> <currency>\n"
    "   FLIGHT: <flight number if visible>\n"
    f"   DATE: {DEPARTURE_DATE}\n"
)


async def main() -> None:
    llm = ChatOpenAI(
        model="google/gemini-2.5-flash",
        openai_api_key=OPENROUTER_API_KEY,
        openai_api_base="https://openrouter.ai/api/v1",
    )

    agent = Agent(
        task=TASK,
        llm=llm,
        use_vision=True,
        enable_memory=False,
    )

    result = await agent.run()
    print("=== Agent Result ===")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
