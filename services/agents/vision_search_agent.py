"""
Stage A — fill the airline's flight-search form (origin, destination, date)
and click the search button. Uses Anthropic Computer Use via vision_common.

Entry point: fill_search_form(page, origin, destination, date, time)
"""
import logging

from playwright.async_api import Page

from agents.vision_common import run_agent_loop

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You are a browser automation agent. The airline's website is already open in the browser.
Your only job is to fill out the flight-search form.

GOAL:
- "From" / "Origin" airport: {origin}
- "To" / "Destination" airport: {destination}
- Departure date: {date}
- After all three are set, click the search / find button.

BEFORE FILLING THE FORM:
- If a cookie / GDPR banner covers the page, dismiss it first.
- If a promotional modal or popup is blocking the form, close it.
- If the form is not visible, scroll down until you can see it.
- If the site asks for a language, pick English.

UNIVERSAL TACTICS (apply on any airline):
- Filling airport fields: TYPE the IATA code or the city name into the field
  to filter the dropdown. Do NOT scroll a long alphabetic list of cities.
- Picking a date: click the day in the calendar grid, then close the calendar
  by pressing Escape OR clicking on empty area outside the picker. Do not
  click on labels like "no return ticket needed", "one-way", or anything
  that switches trip mode — those are NOT how you close the picker.
- If the same click does not have the intended effect after 2 attempts,
  try a different element rather than repeating. Re-read the screenshot.
- Use `wait` for 1–2 seconds after a click that loads new content, before
  the next screenshot.

ONLY TOUCH:
- The three fields above and the search button.

DO NOT TOUCH:
- Trip type (one-way / round-trip) — leave default.
- Return-date field — leave empty.
- Passenger count, cabin class, promo codes.

WHEN DONE:
- Once the search button has been clicked and results start to load,
  reply with the single word "Done" and stop calling tools.

Do not navigate away. Do not open new tabs. If the screenshot is ambiguous,
take another screenshot or wait briefly and reassess."""


async def fill_search_form(
    page: Page,
    origin_iata: str,
    destination_iata: str,
    departure_date: str,
    departure_time: str,
) -> bool:
    """
    Fill the flight-search form on the currently-open airline page and submit it.

    `departure_time` is accepted to keep the call site stable for the next stage,
    but it is NOT used in the prompt at this step — the form does not know about
    individual flight times, only dates.

    Returns True if the agent loop finished cleanly via end_turn.
    """
    logger.info(
        f"[vision_search_agent] called | {origin_iata}→{destination_iata} on {departure_date} (time={departure_time})"
    )

    prompt = SYSTEM_PROMPT.format(
        origin=origin_iata,
        destination=destination_iata,
        date=departure_date,
    )
    ok, _ = await run_agent_loop(page, prompt, log_prefix="[vision_search_agent]")
    return ok
