"""
Record-and-replay for vision agents — proof of concept.

Idea: after a successful LLM-driven price check we dump the executed action
list to a JSON file keyed by subscription. Next time we run for that same
subscription, we replay the saved action list deterministically — no LLM
calls, near-zero cost.

Layout: services/strategies/sub_<id>.json
{
  "subscription_id": 1,
  "airline_url": "https://www.flypobeda.ru",
  "viewport": [1280, 800],
  "recorded_at": "2026-04-28T13:06:59+00:00",
  "actions": [{"action": "left_click", "coordinate": [1239, 771]}, ...]
}

Limitations (intentionally not handled here):
  - Cookie banners / promo modals appear non-deterministically. If they
    differ between record and replay, clicks will land off-target.
  - Layout changes invalidate saved coordinates.

On replay failure we delete the strategy file so the next run re-records.
"""
import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from playwright.async_api import Page

from agents.vision_common import _execute_action, resolve_active_page

logger = logging.getLogger(__name__)

_DEFAULT_STRATEGIES_DIR = Path(__file__).resolve().parent.parent / "strategies"
STRATEGIES_DIR = Path(os.environ.get("STRATEGIES_DIR") or _DEFAULT_STRATEGIES_DIR)

# Pause after each action during replay. Mirrors the natural cadence of the
# LLM loop (action → screenshot → API call ≈ 3–5s) so the page has time to
# settle before the next click.
REPLAY_DELAY_BETWEEN_ACTIONS = 2.5

# One-off pause right after the caller navigated to the airline URL,
# BEFORE the first recorded click. Lets heavy SPAs (cookie banners,
# promo modals, async hero scripts) fully initialise so the saved
# coordinates land on stable elements.
INITIAL_REPLAY_DELAY = 15.0


def strategy_path(subscription_id: int) -> Path:
    return STRATEGIES_DIR / f"sub_{subscription_id}.json"


def load_strategy(subscription_id: int) -> Optional[dict]:
    """Return the saved strategy dict for this subscription, or None."""
    path = strategy_path(subscription_id)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning(f"[strategy] failed to read {path}: {exc}")
        return None


def save_strategy(
    subscription_id: int,
    airline_url: str,
    viewport: tuple[int, int],
    actions: list[dict],
) -> Path:
    """Write a strategy file for this subscription. Returns the path."""
    STRATEGIES_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "subscription_id": subscription_id,
        "airline_url": airline_url,
        "viewport": list(viewport),
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "actions": actions,
    }
    path = strategy_path(subscription_id)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info(f"[strategy] saved {len(actions)} steps → {path}")
    return path


def discard_strategy(subscription_id: int) -> None:
    """Remove the strategy file (e.g. after a replay failure)."""
    strategy_path(subscription_id).unlink(missing_ok=True)
    logger.info(f"[strategy] discarded sub_{subscription_id}.json")


async def replay_strategy(page: Page, strategy: dict) -> bool:
    """
    Execute the saved actions on the currently-open page in order, with a
    fixed pause between steps. Re-resolves the active page after every
    action so we follow new tabs the same way the LLM loop does.

    Returns True if every action ran without raising, False otherwise.
    A True return does NOT prove the right thing happened on screen —
    the caller should still inspect the final screenshot.
    """
    actions = strategy.get("actions", [])
    if not actions:
        logger.warning("[strategy] empty action list")
        return False

    logger.info(f"[strategy] replaying {len(actions)} steps")
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
        await asyncio.sleep(REPLAY_DELAY_BETWEEN_ACTIONS)
    return True
