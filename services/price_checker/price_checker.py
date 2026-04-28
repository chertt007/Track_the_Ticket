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
from agents.strategy_verifier import verify_departure_time_visible
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

# Replay retry schedule. Each attempt opens a fresh incognito context, navigates
# to the airline URL, replays the saved actions with the given inter-action
# delay, then runs the verifier. First verified success wins. If all attempts
# fail to verify, the strategy is discarded and we fall back to the LLM path.
REPLAY_RETRY_DELAYS = [2.5, 10.0, 20.0]


async def _save_final_screenshot(
    page,
    origin: str,
    destination: str,
    departure_date: str,
    via: str,
    subscription_id: int,
) -> Path:
    """Take a full-page JPEG of the active tab and write it to SCREENSHOTS_DIR."""
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
        f"[price_checker] sub id={subscription_id} screenshot saved → {screenshot_path} (via {via})"
    )
    return screenshot_path


async def check_price(subscription_id: int) -> None:
    """
    Trigger a price re-check for the given subscription.

    Flow:
      1. Resolve the airline's website URL (DB cache or url-finder agent).
      2. If a saved strategy exists, try to replay it up to 3 times with
         growing inter-action delays (2.5s → 10s → 15s). After each replay
         a verifier agent confirms whether a flight with the requested
         departure_time is visible on the final page. First verified
         attempt wins.
      3. If all replay attempts fail to verify (or no strategy exists),
         fall through to the LLM path: vision_search_agent (Stage A) →
         vision_pick_flight_agent (Stage B). On success, persist the
         executed actions as a fresh strategy.
      4. Either way, take a final full-page screenshot.

    Raises:
        SubscriptionNotFoundError: if no subscription exists with this id.
    """
    with SessionLocal() as db:
        sub = get_subscription(db, subscription_id)
        if sub is None:
            logger.warning(
                f"[price_checker] subscription id={subscription_id} not found"
            )
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
            logger.info(
                f"[price_checker] airline '{airline_name}' not in table — calling agent"
            )
            airline_url = await find_airline_url_online(airline_name)
            if airline_url:
                save_airline(db, airline_name, airline_url)
                logger.info(f"[price_checker] saved '{airline_name}' → {airline_url}")
            else:
                logger.warning(
                    f"[price_checker] no URL for '{airline_name}' — skipping"
                )
                return
        else:
            logger.info(f"[price_checker] airline '{airline_name}' → url={airline_url}")

    logger.info(
        f"[price_checker] sub id={subscription_id} | {airline_name} "
        f"{origin}→{destination} on {departure_date} {departure_time} | baggage={need_baggage}"
    )

    strategy = load_strategy(subscription_id)
    if strategy is not None:
        logger.info(
            f"[price_checker] sub id={subscription_id} replay path — strategy with "
            f"{len(strategy.get('actions', []))} steps"
        )
    else:
        logger.info(f"[price_checker] sub id={subscription_id} no saved strategy")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=HEADLESS)
        try:
            success = False

            # === REPLAY PATH: up to 3 attempts with growing delays. ===
            if strategy is not None:
                for attempt, delay in enumerate(REPLAY_RETRY_DELAYS, 1):
                    logger.info(
                        f"[price_checker] sub id={subscription_id} "
                        f"replay attempt {attempt}/{len(REPLAY_RETRY_DELAYS)} | delay={delay}s"
                    )
                    context = await browser.new_context(
                        viewport={"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT}
                    )
                    try:
                        page = await context.new_page()
                        await page.goto(airline_url, wait_until="domcontentloaded")

                        replay_ok = await replay_strategy(
                            page, strategy, delay_between_actions=delay
                        )
                        if not replay_ok:
                            logger.warning(
                                f"[price_checker] sub id={subscription_id} "
                                f"replay attempt {attempt} crashed mid-flow"
                            )
                            continue

                        verified = await verify_departure_time_visible(
                            page=page,
                            origin=origin,
                            destination=destination,
                            date=departure_date,
                            time=departure_time,
                        )
                        if verified:
                            await _save_final_screenshot(
                                page=page,
                                origin=origin,
                                destination=destination,
                                departure_date=departure_date,
                                via=f"replay/attempt{attempt}/{delay}s",
                                subscription_id=subscription_id,
                            )
                            success = True
                            break

                        logger.warning(
                            f"[price_checker] sub id={subscription_id} "
                            f"replay attempt {attempt} executed but verifier said NO"
                        )
                    finally:
                        await context.close()

                if not success:
                    logger.warning(
                        f"[price_checker] sub id={subscription_id} "
                        f"all {len(REPLAY_RETRY_DELAYS)} replay attempts failed verification — "
                        "discarding strategy and falling through to LLM"
                    )
                    discard_strategy(subscription_id)

            # === LLM PATH: only if replay didn't succeed. ===
            if not success:
                logger.info(f"[price_checker] sub id={subscription_id} LLM path")
                context = await browser.new_context(
                    viewport={"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT}
                )
                try:
                    page = await context.new_page()
                    await page.goto(airline_url, wait_until="domcontentloaded")

                    stage_a_ok, actions_a = await fill_search_form(
                        page=page,
                        origin_iata=origin,
                        destination_iata=destination,
                        departure_date=departure_date,
                        departure_time=departure_time,
                    )
                    if not stage_a_ok:
                        logger.warning(
                            f"[price_checker] sub id={subscription_id} stage A failed"
                        )
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
                            f"[price_checker] sub id={subscription_id} "
                            f"no flight at {departure_time} on {departure_date}"
                        )
                        return
                    if not stage_b_ok:
                        logger.warning(
                            f"[price_checker] sub id={subscription_id} stage B failed"
                        )
                        return

                    await _save_final_screenshot(
                        page=page,
                        origin=origin,
                        destination=destination,
                        departure_date=departure_date,
                        via="llm",
                        subscription_id=subscription_id,
                    )

                    recorded_actions = actions_a + actions_b
                    if recorded_actions:
                        save_strategy(
                            subscription_id=subscription_id,
                            airline_url=airline_url,
                            viewport=(VIEWPORT_WIDTH, VIEWPORT_HEIGHT),
                            actions=recorded_actions,
                        )
                finally:
                    await context.close()
        finally:
            await browser.close()
