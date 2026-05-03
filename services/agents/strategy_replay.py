"""
Record-and-replay for vision agents.

When a successful LLM-driven price check finishes, we persist the executed
action list into the `strategies` table keyed by subscription. Next time
we run for that same subscription we replay the saved actions deterministically
— no LLM calls, near-zero cost.

The public API (load / save / discard / replay) keeps the same signatures
as before; only the storage backend changed from JSON files to SQLite.

Limitations (intentionally not handled here):
  - Cookie banners / promo modals appear non-deterministically. If they
    differ between record and replay, clicks will land off-target.
  - Layout changes invalidate saved coordinates.

On replay failure the caller deletes the strategy via discard_strategy
so the next run re-records via the LLM path.
"""
import asyncio
import logging
from typing import Optional

from playwright.async_api import Page

from agents.vision_common import _execute_action, resolve_active_page
from common.database import SessionLocal
from common.queries import (
    delete_strategy as _db_delete_strategy,
    get_strategy as _db_get_strategy,
    upsert_strategy as _db_upsert_strategy,
)

logger = logging.getLogger(__name__)

# Pause after each action during replay. Mirrors the natural cadence of the
# LLM loop (action → screenshot → API call ≈ 3–5s) so the page has time to
# settle before the next click.
REPLAY_DELAY_BETWEEN_ACTIONS = 2.5

# One-off pause right after the caller navigated to the airline URL,
# BEFORE the first recorded click. Lets heavy SPAs (cookie banners,
# promo modals, async hero scripts) fully initialise so the saved
# coordinates land on stable elements.
INITIAL_REPLAY_DELAY = 15.0


def load_strategy(subscription_id: int) -> Optional[dict]:
    """Return the saved strategy dict for this subscription, or None."""
    with SessionLocal() as db:
        return _db_get_strategy(db, subscription_id)


def save_strategy(
    subscription_id: int,
    airline_url: str,
    viewport: tuple[int, int],
    actions: list[dict],
) -> None:
    """Insert/replace the strategy for this subscription."""
    with SessionLocal() as db:
        _db_upsert_strategy(
            db=db,
            subscription_id=subscription_id,
            airline_url=airline_url,
            viewport=viewport,
            actions=actions,
        )


def discard_strategy(subscription_id: int) -> None:
    """Remove the strategy row (e.g. after a replay failure)."""
    with SessionLocal() as db:
        _db_delete_strategy(db, subscription_id)


async def replay_strategy(
    page: Page,
    strategy: dict,
    delay_between_actions: float = REPLAY_DELAY_BETWEEN_ACTIONS,
) -> bool:
    """
    Execute the saved actions on the currently-open page in order, with a
    pause between steps. Re-resolves the active page after every action
    so we follow new tabs the same way the LLM loop does.

    Args:
        delay_between_actions: seconds to wait after each action.
            Caller may pass a larger value on retry attempts when slow
            networks or heavy SPAs are suspected.

    Returns:
        True  if every action ran without raising — does NOT prove we
              landed on the right page; caller should verify visually
              or via a verifier agent.
        False on any execution error.
    """
    actions = strategy.get("actions", [])
    if not actions:
        logger.warning("[strategy] empty action list")
        return False

    logger.info(
        f"[strategy] replaying {len(actions)} steps (delay between actions: {delay_between_actions}s)"
    )
    logger.info(f"[strategy] settling for {INITIAL_REPLAY_DELAY}s before first action…")
    await asyncio.sleep(INITIAL_REPLAY_DELAY)
    current_page = page
    for i, action_input in enumerate(actions, 1):
        action = action_input.get("action")
        try:
            current_page = await resolve_active_page(current_page)
            await _execute_action(current_page, action_input)
            logger.info(f"[strategy] step {i}/{len(actions)} {action} ok")
        except Exception as exc:
            logger.error(
                f"[strategy] step {i}/{len(actions)} {action} failed: {exc}",
                exc_info=True,
            )
            return False

        # Per-step extra wait, baked into the recorded action by the agent
        # that produced it (e.g. the search-button click at the end of Stage A
        # carries a 20s wait so the results page has time to render).
        wait_after_ms = action_input.get("wait_after_ms")
        if wait_after_ms:
            extra_s = wait_after_ms / 1000.0
            logger.info(
                f"[strategy] step {i}/{len(actions)} extra wait_after_ms={wait_after_ms} → sleeping {extra_s}s"
            )
            await asyncio.sleep(extra_s)

        await asyncio.sleep(delay_between_actions)
    return True
