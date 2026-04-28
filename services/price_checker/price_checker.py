import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from playwright.async_api import async_playwright

from agents.airline_url_finder import find_airline_url_online
from agents.strategy_replay import (
    discard_strategy,
    load_strategy,
    replay_strategy,
    save_strategy,
)
from agents.vision_common import VIEWPORT_HEIGHT, VIEWPORT_WIDTH, resolve_active_page
from agents.vision_pick_flight_agent import pick_flight
from agents.vision_search_agent import fill_search_form
from common.database import SessionLocal
from common.exceptions import SubscriptionNotFoundError
from common.queries import get_airline_url_by_name, get_subscription, save_airline

logger = logging.getLogger(__name__)

# Visible browser while we're still iterating; flip to True once stable.
HEADLESS = False
# Anchor to services/screenshots/ regardless of cwd, override via env if needed.
_DEFAULT_SCREENSHOTS_DIR = Path(__file__).resolve().parent.parent / "screenshots"
SCREENSHOTS_DIR = Path(os.environ.get("SCREENSHOTS_DIR") or _DEFAULT_SCREENSHOTS_DIR)


async def check_price(subscription_id: int) -> None:
    """
    Trigger a price re-check for the given subscription.

    Two execution paths:
      A. Replay path — a saved strategy exists for this subscription.
         Open the airline URL, replay the recorded actions step by step,
         take the final screenshot. No LLM calls.
      B. LLM path — no strategy yet (or it was discarded after a failure).
         Run vision_search_agent → vision_pick_flight_agent, take the
         screenshot, and persist the executed actions as a new strategy
         so the next run can use the cheap replay path.

    Raises:
        SubscriptionNotFoundError: if no subscription exists with this id.
    """
    with SessionLocal() as db:
        sub = get_subscription(db, subscription_id)
        if sub is None:
            logger.warning(f"[price_checker] subscription id={subscription_id} not found")
            raise SubscriptionNotFoundError(subscription_id)

        airline_name = sub.airline
        # Snapshot fields we need outside the DB session — Subscription
        # becomes detached once the `with` block exits.
        origin = sub.departure_airport
        destination = sub.arrival_airport
        departure_date = sub.departure_date
        departure_time = sub.departure_time
        flight_number = sub.flight_number
        need_baggage = bool(sub.need_baggage)

        airline_url = get_airline_url_by_name(db, airline_name)
        if airline_url is None:
            logger.info(f"[price_checker] airline '{airline_name}' not in table — calling agent")
            airline_url = await find_airline_url_online(airline_name)
            if airline_url:
                save_airline(db, airline_name, airline_url)
                logger.info(f"[price_checker] saved '{airline_name}' → {airline_url}")
            else:
                logger.warning(f"[price_checker] no URL for '{airline_name}' — skipping")
                return
        else:
            logger.info(f"[price_checker] airline '{airline_name}' → url={airline_url}")

    logger.info(
        f"[price_checker] sub id={subscription_id} | {airline_name} "
        f"{origin}→{destination} on {departure_date} {departure_time} | baggage={need_baggage}"
    )

    strategy = load_strategy(subscription_id)
    used_replay = strategy is not None
    if used_replay:
        logger.info(
            f"[price_checker] sub id={subscription_id} replay path — strategy with "
            f"{len(strategy.get('actions', []))} steps"
        )
    else:
        logger.info(f"[price_checker] sub id={subscription_id} LLM path — no saved strategy")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=HEADLESS)
        context = await browser.new_context(
            viewport={"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT}
        )
        try:
            page = await context.new_page()
            await page.goto(airline_url, wait_until="domcontentloaded")

            success = False
            recorded_actions: list[dict] = []

            if used_replay:
                replay_ok = await replay_strategy(page, strategy)
                if replay_ok:
                    success = True
                else:
                    logger.warning(
                        f"[price_checker] sub id={subscription_id} replay failed — "
                        "discarding strategy; next run will re-record via LLM"
                    )
                    discard_strategy(subscription_id)
                    # For prototype we exit here. User can rerun and the
                    # second run will go through the LLM path and produce
                    # a fresh strategy.
                    return
            else:
                stage_a_ok, actions_a = await fill_search_form(
                    page=page,
                    origin_iata=origin,
                    destination_iata=destination,
                    departure_date=departure_date,
                    departure_time=departure_time,
                )
                if not stage_a_ok:
                    logger.warning(f"[price_checker] sub id={subscription_id} stage A failed")
                    return

                stage_b_ok, no_match, actions_b = await pick_flight(
                    page=page,
                    origin_iata=origin,
                    destination_iata=destination,
                    departure_date=departure_date,
                    departure_time=departure_time,
                    need_baggage=need_baggage,
                    flight_number=flight_number,
                )
                if no_match:
                    logger.warning(
                        f"[price_checker] sub id={subscription_id} no flight at {departure_time} on {departure_date}"
                    )
                    return
                if not stage_b_ok:
                    logger.warning(f"[price_checker] sub id={subscription_id} stage B failed")
                    return

                recorded_actions = actions_a + actions_b
                success = True

            if not success:
                return

            # Final screenshot. Re-resolve the active page in case stage B
            # (or the replay) ended on a tab opened mid-flow.
            SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            screenshot_path = (
                SCREENSHOTS_DIR / f"{origin}_{destination}_{departure_date}_{stamp}.jpg"
            )
            final_page = await resolve_active_page(page)
            await final_page.screenshot(
                path=str(screenshot_path),
                full_page=True,
                type="jpeg",
                quality=85,
            )
            logger.info(
                f"[price_checker] sub id={subscription_id} screenshot saved → {screenshot_path} "
                f"(via {'replay' if used_replay else 'LLM'})"
            )

            # Persist the strategy only when we ran the LLM path successfully.
            if not used_replay and recorded_actions:
                save_strategy(
                    subscription_id=subscription_id,
                    airline_url=airline_url,
                    viewport=(VIEWPORT_WIDTH, VIEWPORT_HEIGHT),
                    actions=recorded_actions,
                )
        finally:
            await context.close()
            await browser.close()
