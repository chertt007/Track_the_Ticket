"""
Automated price-check jobs.

Twice a day (default 07:00 and 17:00 Asia/Jerusalem, override via env vars
SCHEDULE_MORNING_HOUR / SCHEDULE_AFTERNOON_HOUR) we iterate over every
active subscription and run the same `check_price` pipeline the user
triggers manually from the UI. The Telegram notifier is already wired
into `check_price`, so each successful run pings the linked chat.

Checks run sequentially — Playwright/Chromium per check is memory-heavy,
and a fanout would only mask price-checker bugs as flaky timing issues.
"""
from __future__ import annotations

import logging
import os
from typing import Final

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from common.database import SessionLocal
from common.db_models import Subscription
from price_checker import check_price

logger = logging.getLogger(__name__)

# Schedule in local user time (Israel). APScheduler stores the absolute
# moment in UTC and converts on each fire, so the VPS system timezone
# does not matter — only this string does. DST jumps are handled by tzdata.
SCHEDULE_TZ: Final = "Asia/Jerusalem"


def _hour_env(name: str, default: int) -> int:
    """Read an hour-of-day from env (0-23), fall back to default on bad input."""
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        hour = int(raw)
        if 0 <= hour <= 23:
            return hour
    except ValueError:
        pass
    logger.warning(f"[scheduler] ignoring bad {name}={raw!r}, using default {default}")
    return default


async def run_all_active_checks() -> None:
    """Snapshot active subscription ids, then run `check_price` on each.

    Each check is wrapped so one failure (network, browser crash, verifier
    timeout) never blocks the remaining subscriptions. The job is fire-
    and-forget — its result lives in the `price_checks` table and the
    Telegram message the notifier sends from inside `check_price`.
    """
    with SessionLocal() as db:
        sub_ids = [
            s.id
            for s in db.query(Subscription).filter(Subscription.is_active.is_(True)).all()
        ]

    if not sub_ids:
        logger.info("[scheduler] no active subscriptions, skipping run")
        return

    logger.info(f"[scheduler] starting scheduled run for {len(sub_ids)} subscription(s)")
    for sub_id in sub_ids:
        try:
            await check_price(sub_id)
        except Exception as exc:
            logger.error(
                f"[scheduler] check_price failed for sub={sub_id}: {exc}",
                exc_info=True,
            )
    logger.info("[scheduler] scheduled run finished")


def build_scheduler() -> AsyncIOScheduler:
    """Wire two cron triggers (morning + afternoon Moscow time) onto a fresh
    AsyncIOScheduler. Caller is responsible for `start()` / `shutdown()`.
    """
    morning_hour = _hour_env("SCHEDULE_MORNING_HOUR", 7)
    afternoon_hour = _hour_env("SCHEDULE_AFTERNOON_HOUR", 17)

    scheduler = AsyncIOScheduler(timezone=SCHEDULE_TZ)
    scheduler.add_job(
        run_all_active_checks,
        CronTrigger(hour=morning_hour, minute=0, timezone=SCHEDULE_TZ),
        id="price_check_morning",
        # If the API was down at the trigger time, run on startup within
        # an hour — beyond that the price is already stale enough that
        # waiting for the next slot is fine.
        misfire_grace_time=3600,
        coalesce=True,
        max_instances=1,
    )
    scheduler.add_job(
        run_all_active_checks,
        CronTrigger(hour=afternoon_hour, minute=0, timezone=SCHEDULE_TZ),
        id="price_check_afternoon",
        misfire_grace_time=3600,
        coalesce=True,
        max_instances=1,
    )
    logger.info(
        f"[scheduler] configured: daily at {morning_hour:02d}:00 and "
        f"{afternoon_hour:02d}:00 {SCHEDULE_TZ}"
    )
    return scheduler
