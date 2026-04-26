"""
Stage B — on the airline's search-results page, pick the specific flight by
departure time, choose the requested fare (with/without checked baggage),
and stop on a screen where the final price is visible.

Entry point: pick_flight(page, ..., need_baggage)

Returns one of three outcomes via the (ok, no_match) tuple:
  - ok=True,  no_match=False — agent reached the price view; caller can screenshot.
  - ok=True,  no_match=True  — no flight at the requested time was offered.
  - ok=False, no_match=False — loop crashed / API error / hit MAX_STEPS.
"""
import logging
from typing import Optional

from playwright.async_api import Page

from agents.vision_common import run_agent_loop

logger = logging.getLogger(__name__)


# The prompt deliberately defines two distinct end-states ("Done" / "No matching flight")
# so the caller can tell apart "agent worked, no flight exists" from "agent failed".
SYSTEM_PROMPT = """You are a browser automation agent. The airline's flight-search results
page is already open in the browser.

CONTEXT:
- Wanted flight: {origin} → {destination} on {date}, departing at {time}.
  {flight_number_line}
- Baggage required: {baggage_required}
  * TRUE  = passenger needs a checked bag — match the fare that includes it.
  * FALSE = passenger does NOT need a checked bag — match the cheapest fare
    that excludes it.

YOUR DECISION ON EVERY SCREENSHOT — IS THE LIST VIEW ALREADY ENOUGH?

The results page often shows, for each flight, both the schedule AND the price
of one or more fare tiers (e.g. "Basic 4990 ₽" / "Standard 6490 ₽"). If for the
matching flight you can see, in the current screenshot, ALL of:
  (a) the correct departure time and route,
  (b) a clearly visible price,
  (c) the price corresponds to the requested baggage option (the matching tier
      is visible — Basic-like for FALSE, Standard-like with bag icon for TRUE),
  (d) one adult, economy is the implicit default,

→ then the agent is DONE. Reply with the single word "Done" and STOP.
   Do NOT click into the flight to "verify" the price. The list view is
   the result — a screenshot is being taken right after you finish.

DRILL DOWN ONLY WHEN NEEDED:

If the list view does NOT clearly show the price for the requested baggage
option (e.g. only one combined price, or the fare tiers are hidden behind
"Select" buttons), THEN:
  1. Click the matching flight to open its fare options.
  2. Pick the cheapest fare matching the baggage requirement above.
  3. Stop on the FIRST screen where the final price for one adult, economy,
     with the correct baggage choice, is clearly visible.

DO NOT:
- Fill any personal data (name, email, phone, document, payment details).
- Add extras (seat selection, insurance, meals, lounge, transfers).
- Click through to a payment / checkout step.
- Change the trip type, dates, or airports.

WHEN DONE — reply with one of these EXACTLY:
- "Done"               — list view OR fare page shows the correct price.
- "No matching flight" — there is no flight at {time} on {date} in the list
                         after you have scrolled through all results.

If the screenshot is ambiguous, scroll, wait briefly, or take another
screenshot before deciding. Do not repeat the same click more than twice."""


NO_MATCH_PHRASE = "no matching flight"


async def pick_flight(
    page: Page,
    origin_iata: str,
    destination_iata: str,
    departure_date: str,
    departure_time: str,
    need_baggage: bool,
    flight_number: Optional[str] = None,
) -> tuple[bool, bool]:
    """
    Drive the results page to a state where the price for the requested flight
    is visible.

    Returns:
        (ok, no_match)
            ok=True  + no_match=False  → caller can screenshot the price.
            ok=True  + no_match=True   → flight at this time is not offered.
            ok=False + no_match=False  → agent loop failed (timeout / API / steps).
    """
    logger.info(
        f"[vision_pick_flight_agent] called | {origin_iata}→{destination_iata} on {departure_date} "
        f"at {departure_time} | flight_number={flight_number} | need_baggage={need_baggage}"
    )

    flight_number_line = (
        f"If multiple flights match the time, prefer flight number {flight_number}."
        if flight_number
        else "There may be only one flight at this time; if so, that's the one."
    )

    prompt = SYSTEM_PROMPT.format(
        origin=origin_iata,
        destination=destination_iata,
        date=departure_date,
        time=departure_time,
        flight_number_line=flight_number_line,
        baggage_required="TRUE" if need_baggage else "FALSE",
    )

    ok, final_text = await run_agent_loop(
        page, prompt, log_prefix="[vision_pick_flight_agent]"
    )

    no_match = NO_MATCH_PHRASE in final_text.lower()
    if no_match:
        logger.info(
            f"[vision_pick_flight_agent] agent reported no flight at {departure_time}"
        )
    return ok, no_match
