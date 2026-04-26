"""
Smoke test for vision_search_agent — runs end-to-end on subscription id=1
against the cached airline URL, with a visible browser, then waits 30 seconds
so a human can eyeball the result before the window closes.

Usage (from project root, with .venv active):
    python services/scripts/run_vision_agent_smoke.py
"""
import asyncio
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root (../../.env relative to this file).
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

# Make `services/` importable so we can use `agents.*`, `common.*`.
SERVICES_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SERVICES_DIR))

# common.database resolves DATABASE_PATH at import time, relative to cwd by default.
# Pin it to the file in services/ so the script works from any cwd.
os.environ.setdefault("DATABASE_PATH", str(SERVICES_DIR / "tracktheticket.db"))

# Windows: Playwright needs ProactorEventLoop to spawn Chromium subprocess.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from playwright.async_api import async_playwright  # noqa: E402

from agents.vision_common import (  # noqa: E402
    VIEWPORT_HEIGHT,
    VIEWPORT_WIDTH,
    resolve_active_page,
)
from agents.vision_pick_flight_agent import pick_flight  # noqa: E402
from agents.vision_search_agent import fill_search_form  # noqa: E402
from common.database import SessionLocal  # noqa: E402
from common.queries import get_airline_url_by_name, get_subscription  # noqa: E402

SUBSCRIPTION_ID = 1
POST_RUN_HOLD_SECONDS = 30
SCREENSHOTS_DIR = SERVICES_DIR / "screenshots"

# Force unbuffered stdout so log lines appear immediately (Windows terminals
# sometimes buffer hard, hiding what the agent is doing in real time).
try:
    sys.stdout.reconfigure(line_buffering=True)
except AttributeError:
    pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
    force=True,
)
logger = logging.getLogger("smoke")


async def main() -> int:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    logger.info(
        f"ANTHROPIC_API_KEY: {'present (len=' + str(len(api_key)) + ')' if api_key else 'MISSING'}"
    )
    if not api_key:
        logger.error("set ANTHROPIC_API_KEY in .env at project root")
        return 1

    with SessionLocal() as db:
        sub = get_subscription(db, SUBSCRIPTION_ID)
        if sub is None:
            logger.error(f"subscription id={SUBSCRIPTION_ID} not found")
            return 1
        airline_url = get_airline_url_by_name(db, sub.airline)
        if not airline_url:
            logger.error(f"no cached URL for airline '{sub.airline}'")
            return 1

    logger.info(
        f"sub id={sub.id} | {sub.airline} {sub.departure_airport}→{sub.arrival_airport} "
        f"on {sub.departure_date} {sub.departure_time} | url={airline_url}"
    )

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        # Fresh incognito context per run — clean state, no cookies/popups carry-over.
        context = await browser.new_context(
            viewport={"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT}
        )
        page = await context.new_page()

        logger.info(f"opening {airline_url}")
        await page.goto(airline_url, wait_until="domcontentloaded")

        # Stage A — fill search form, click submit.
        stage_a_ok = await fill_search_form(
            page=page,
            origin_iata=sub.departure_airport,
            destination_iata=sub.arrival_airport,
            departure_date=sub.departure_date,
            departure_time=sub.departure_time,
        )
        logger.info(f"stage A (fill_search_form): ok={stage_a_ok}")

        stage_b_ok = False
        no_match = False
        screenshot_path = None

        if stage_a_ok:
            # Stage B — pick the specific flight, configure fare, land on price view.
            stage_b_ok, no_match = await pick_flight(
                page=page,
                origin_iata=sub.departure_airport,
                destination_iata=sub.arrival_airport,
                departure_date=sub.departure_date,
                departure_time=sub.departure_time,
                need_baggage=bool(sub.need_baggage),
                flight_number=sub.flight_number,
            )
            logger.info(f"stage B (pick_flight): ok={stage_b_ok} no_match={no_match}")

            # Stage C — mechanical screenshot of the price view.
            # The price page may live on a tab opened by stage B (some airlines
            # use target=_blank), so resolve the active page once more here.
            if stage_b_ok and not no_match:
                SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
                stamp = asyncio.get_event_loop().time()
                screenshot_path = (
                    SCREENSHOTS_DIR
                    / f"{sub.departure_airport}_{sub.arrival_airport}_{sub.departure_date}_{int(stamp)}.jpg"
                )
                final_page = await resolve_active_page(page)
                await final_page.screenshot(
                    path=str(screenshot_path),
                    full_page=True,
                    type="jpeg",
                    quality=85,
                )
                logger.info(f"stage C: screenshot saved → {screenshot_path}")

        logger.info(f"holding browser open for {POST_RUN_HOLD_SECONDS}s for inspection…")
        await asyncio.sleep(POST_RUN_HOLD_SECONDS)

        await context.close()
        await browser.close()

    if not stage_a_ok:
        return 2
    if no_match:
        return 3
    if not stage_b_ok:
        return 4
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
