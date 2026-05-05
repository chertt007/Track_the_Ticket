import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from agents.airline_url_finder import find_airline_url_online
from agents.strategy_replay import (
    discard_strategy,
    load_strategy,
    replay_strategy,
    save_strategy,
)
from agents.strategy_verifier import verify_and_extract_price
from agents.vision_common import (
    VIEWPORT_HEIGHT,
    VIEWPORT_WIDTH,
    PriceResult,
    resolve_active_page,
)
from agents.vision_pick_flight_agent import pick_flight
from agents.vision_search_agent import fill_search_form
from common.database import SessionLocal
from common.exceptions import SubscriptionNotFoundError
from common.queries import (
    get_airline_url_by_name,
    get_subscription,
    save_airline,
    save_price_check,
)

logger = logging.getLogger(__name__)

# Visible browser while we're still iterating; flip to True once stable.
HEADLESS = False
# Anchor to services/screenshots/ regardless of cwd, override via env if needed.
_DEFAULT_SCREENSHOTS_DIR = Path(__file__).resolve().parent.parent / "screenshots"
SCREENSHOTS_DIR = Path(os.environ.get("SCREENSHOTS_DIR") or _DEFAULT_SCREENSHOTS_DIR)
# Subfolder for the verifier's view of each replay attempt — useful when
# the verifier disagrees with the human eye and we need to see exactly
# what frame it judged.
VERIFIER_DEBUG_DIR = SCREENSHOTS_DIR / "verifier"

# Replay retry schedule. Each attempt opens a fresh incognito context, navigates
# to the airline URL, replays the saved actions with the given inter-action
# delay, then runs the verifier. First verified success wins. If all attempts
# fail to verify, the strategy is discarded and we fall back to the LLM path.
REPLAY_RETRY_DELAYS = [2.5, 4, 7.0]

# Screenshots are user-facing artefacts (Telegram messages, history view) but
# only need to live as long as a person might want to reopen them. After that
# the row in `price_checks` carries the price forever; the JPEG is purged.
SCREENSHOT_RETENTION_DAYS = 7


@dataclass(frozen=True)
class _Job:
    """All per-subscription parameters used across the price-check pipeline."""
    subscription_id: int
    airline_name: str
    airline_url: str
    origin: str
    destination: str
    departure_date: str
    departure_time: str
    flight_number: Optional[str]
    need_baggage: bool


async def _resolve_job(subscription_id: int) -> Optional[_Job]:
    """
    Fetch subscription details and the airline's website URL.

    Snapshots all needed fields off the SQLAlchemy entity so the rest of
    the pipeline can work outside the DB session.

    Returns:
        A frozen `_Job`, or None if the airline URL cannot be resolved
        (cache miss + url-finder agent gave up).

    Raises:
        SubscriptionNotFoundError if the subscription does not exist.
    """
    with SessionLocal() as db:
        sub = get_subscription(db, subscription_id)
        if sub is None:
            logger.warning(f"[price_checker] subscription id={subscription_id} not found")
            raise SubscriptionNotFoundError(subscription_id)

        airline_name = sub.airline
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
                return None
        else:
            logger.info(f"[price_checker] airline '{airline_name}' → url={airline_url}")

    return _Job(
        subscription_id=subscription_id,
        airline_name=airline_name,
        airline_url=airline_url,
        origin=origin,
        destination=destination,
        departure_date=departure_date,
        departure_time=departure_time,
        flight_number=flight_number,
        need_baggage=need_baggage,
    )


async def _open_fresh_page(browser: Browser, url: str) -> tuple[BrowserContext, Page]:
    """Open a new incognito context at the airline URL. Caller closes the context."""
    context = await browser.new_context(
        viewport={"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT}
    )
    page = await context.new_page()
    await page.goto(url, wait_until="domcontentloaded")
    return context, page


def _prune_old_screenshots(retention_days: int = SCREENSHOT_RETENTION_DAYS) -> None:
    """
    Delete files under SCREENSHOTS_DIR (and the verifier/ subfolder) older than
    `retention_days` based on mtime. The matching `price_checks` rows are kept
    forever — only the on-disk artefact is purged.

    Opportunistically called at the start of every `check_price` so we don't
    need a separate cron. The cost is one recursive listdir, negligible against
    a price-check that takes minutes.

    Per-file errors are swallowed so a single locked/missing file can't break
    a price-check.
    """
    if not SCREENSHOTS_DIR.exists():
        return

    cutoff = time.time() - retention_days * 86400
    deleted_count = 0
    freed_bytes = 0
    for entry in SCREENSHOTS_DIR.rglob("*"):
        if not entry.is_file():
            continue
        try:
            if entry.stat().st_mtime >= cutoff:
                continue
            size = entry.stat().st_size
            entry.unlink()
            deleted_count += 1
            freed_bytes += size
        except OSError as exc:
            logger.warning(f"[price_checker] could not prune {entry}: {exc}")

    if deleted_count:
        logger.info(
            f"[price_checker] pruned {deleted_count} screenshot(s) older than "
            f"{retention_days}d, freed {freed_bytes / 1024:.1f} KB"
        )


async def _save_final_screenshot(page: Page, job: _Job, via: str) -> Path:
    """Take a full-page JPEG of the active tab and write it to SCREENSHOTS_DIR."""
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    screenshot_path = (
        SCREENSHOTS_DIR / f"{job.origin}_{job.destination}_{job.departure_date}_{stamp}.jpg"
    )
    final_page = await resolve_active_page(page)
    await final_page.screenshot(
        path=str(screenshot_path),
        full_page=True,
        type="jpeg",
        quality=85,
    )
    logger.info(
        f"[price_checker] sub id={job.subscription_id} screenshot saved → {screenshot_path} (via {via})"
    )
    return screenshot_path


async def _save_check_result(
    page: Page, job: _Job, via: str, price: Optional[PriceResult]
) -> None:
    """
    Persist the outcome of a successful price-check:
      1. JPEG of the final page on disk (for future Telegram delivery).
      2. A row in `price_checks` with whatever the verifier read for
         price — amount/currency are NULL when the model could not
         resolve a price for our flight.

    Price is passed in (not extracted here) because the unified verifier
    already produced it during landing-page verification on the same
    screenshot. DB write swallows its own exceptions — a price-check
    pipeline must not be killed by a transient SQLite hiccup.
    """
    screenshot_path = await _save_final_screenshot(page, job, via)

    amount = price.amount if price else None
    currency = price.currency if price else None

    try:
        with SessionLocal() as db:
            save_price_check(
                db,
                subscription_id=job.subscription_id,
                amount=amount,
                currency=currency,
                via=via,
                screenshot_path=str(screenshot_path),
            )
    except Exception as exc:
        logger.error(
            f"[price_checker] sub id={job.subscription_id} "
            f"failed to persist price_check row: {exc}",
            exc_info=True,
        )


async def _try_replay_with_retries(
    browser: Browser, strategy: dict, job: _Job
) -> bool:
    """
    Replay the saved strategy up to len(REPLAY_RETRY_DELAYS) times with
    growing inter-action delays. After each replay the verifier confirms
    that a flight with `job.departure_time` is visible on the final page.

    Returns True on the first verified attempt; False if every attempt
    either crashed or failed verification.
    """
    for attempt, delay in enumerate(REPLAY_RETRY_DELAYS, 1):
        logger.info(
            f"[price_checker] sub id={job.subscription_id} "
            f"replay attempt {attempt}/{len(REPLAY_RETRY_DELAYS)} | delay={delay}s"
        )
        context, page = await _open_fresh_page(browser, job.airline_url)
        try:
            replay_ok = await replay_strategy(
                page, strategy, delay_between_actions=delay
            )
            if not replay_ok:
                logger.warning(
                    f"[price_checker] sub id={job.subscription_id} "
                    f"replay attempt {attempt} crashed mid-flow"
                )
                continue

            stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            debug_screenshot_path = (
                VERIFIER_DEBUG_DIR
                / f"sub{job.subscription_id}_attempt{attempt}_{delay}s_{stamp}.png"
            )
            result = await verify_and_extract_price(
                page=page,
                time=job.departure_time,
                debug_screenshot_path=debug_screenshot_path,
            )
            if result.verified:
                await _save_check_result(
                    page,
                    job,
                    via=f"replay/attempt{attempt}/{delay}s",
                    price=result.price,
                )
                return True

            logger.warning(
                f"[price_checker] sub id={job.subscription_id} "
                f"replay attempt {attempt} executed but verifier said NO"
            )
        finally:
            await context.close()
    return False


async def _run_llm_pipeline_and_record(browser: Browser, job: _Job) -> None:
    """
    Drive the airline website end-to-end via the two vision agents,
    take the final screenshot, and persist the executed actions as a
    fresh strategy so the next run can use the cheap replay path.
    """
    context, page = await _open_fresh_page(browser, job.airline_url)
    try:
        stage_a_ok, actions_a = await fill_search_form(
            page=page,
            origin_iata=job.origin,
            destination_iata=job.destination,
            departure_date=job.departure_date,
            departure_time=job.departure_time,
        )
        if not stage_a_ok:
            logger.warning(f"[price_checker] sub id={job.subscription_id} stage A failed")
            return

        stage_b_ok, no_match, actions_b = await pick_flight(
            page=page,
            origin_iata=job.origin,
            destination_iata=job.destination,
            departure_date=job.departure_date,
            departure_time=job.departure_time,
            need_baggage=job.need_baggage,
            flight_number=job.flight_number,
        )
        if no_match:
            logger.warning(
                f"[price_checker] sub id={job.subscription_id} "
                f"no flight at {job.departure_time} on {job.departure_date}"
            )
            return
        if not stage_b_ok:
            logger.warning(f"[price_checker] sub id={job.subscription_id} stage B failed")
            return

        # Same Sonnet call as in the replay path — sanity-check we're on
        # the right flight and harvest the price for our row. If the LLM
        # pipeline thought it succeeded but the verifier disagrees, that's
        # noteworthy: log loudly, save NULL price, keep the screenshot.
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        debug_screenshot_path = (
            VERIFIER_DEBUG_DIR / f"sub{job.subscription_id}_llm_{stamp}.png"
        )
        result = await verify_and_extract_price(
            page=page,
            time=job.departure_time,
            debug_screenshot_path=debug_screenshot_path,
        )
        if not result.verified:
            logger.warning(
                f"[price_checker] sub id={job.subscription_id} "
                "LLM pipeline finished but verifier said NO — saving with NULL price"
            )

        await _save_check_result(page, job, via="llm", price=result.price)

        recorded_actions = actions_a + actions_b
        if recorded_actions:
            save_strategy(
                subscription_id=job.subscription_id,
                airline_url=job.airline_url,
                viewport=(VIEWPORT_WIDTH, VIEWPORT_HEIGHT),
                actions=recorded_actions,
            )
    finally:
        await context.close()


async def check_price(subscription_id: int) -> None:
    """
    Trigger a price re-check for the given subscription.

    Two execution paths:
      1. Replay path — saved strategy exists. Try to replay up to
         `len(REPLAY_RETRY_DELAYS)` times with growing inter-action
         delays; the verifier confirms after each attempt that a flight
         with the requested departure_time is visible. First verified
         success wins.
      2. LLM path — no strategy or all replay attempts failed
         verification. Run the two vision agents end-to-end, take the
         screenshot, and persist a fresh strategy so the next run can
         take the cheap replay path again.

    Raises:
        SubscriptionNotFoundError: if no subscription exists with this id.
    """
    _prune_old_screenshots()

    job = await _resolve_job(subscription_id)
    if job is None:
        return

    logger.info(
        f"[price_checker] sub id={job.subscription_id} | {job.airline_name} "
        f"{job.origin}→{job.destination} on {job.departure_date} {job.departure_time} | "
        f"baggage={job.need_baggage}"
    )

    strategy = load_strategy(job.subscription_id)
    if strategy is not None:
        logger.info(
            f"[price_checker] sub id={job.subscription_id} replay path — strategy with "
            f"{len(strategy.get('actions', []))} steps"
        )
    else:
        logger.info(f"[price_checker] sub id={job.subscription_id} no saved strategy")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=HEADLESS)
        try:
            replayed = False
            if strategy is not None:
                replayed = await _try_replay_with_retries(browser, strategy, job)
                if not replayed:
                    logger.warning(
                        f"[price_checker] sub id={job.subscription_id} "
                        f"all {len(REPLAY_RETRY_DELAYS)} replay attempts failed verification — "
                        "discarding strategy and falling through to LLM"
                    )
                    discard_strategy(job.subscription_id)

            if not replayed:
                logger.info(f"[price_checker] sub id={job.subscription_id} LLM path")
                await _run_llm_pipeline_and_record(browser, job)
        finally:
            await browser.close()
