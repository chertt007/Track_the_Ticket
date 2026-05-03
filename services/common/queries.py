"""Database query helpers — one place for all SELECT logic."""
import json
import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session

from .db_models import Airline, PriceCheck, Strategy, Subscription

logger = logging.getLogger(__name__)


def get_subscription(db: Session, subscription_id: int) -> Optional[Subscription]:
    """Fetch a single subscription by primary key. Returns None if not found."""
    return db.get(Subscription, subscription_id)


def get_airline_url_by_name(db: Session, name: str) -> Optional[str]:
    """Look up an airline's website URL by its display name. None if not registered."""
    row = db.query(Airline).filter(Airline.airline_name == name).first()
    return row.airline_url if row else None


def save_airline(db: Session, name: str, url: str) -> None:
    """Insert a new airline into the `airlines` table and commit."""
    db.add(Airline(airline_name=name, airline_url=url))
    db.commit()
    logger.info(f"[queries] saved airline '{name}' → {url}")


def get_strategy(db: Session, subscription_id: int) -> Optional[dict]:
    """
    Return the saved strategy for this subscription as a dict shaped like
    the legacy JSON file (so callers like replay_strategy keep working
    unchanged), or None if no strategy is stored.
    """
    row = db.query(Strategy).filter(Strategy.subscription_id == subscription_id).first()
    if row is None:
        return None
    return {
        "subscription_id": row.subscription_id,
        "airline_url": row.airline_url,
        "viewport": [row.viewport_w, row.viewport_h],
        "recorded_at": row.recorded_at.isoformat() if row.recorded_at else None,
        "actions": json.loads(row.actions_json),
    }


def upsert_strategy(
    db: Session,
    subscription_id: int,
    airline_url: str,
    viewport: tuple[int, int],
    actions: list[dict],
) -> None:
    """Insert a new strategy or replace an existing one for this subscription."""
    actions_json = json.dumps(actions, ensure_ascii=False)
    row = db.query(Strategy).filter(Strategy.subscription_id == subscription_id).first()
    if row is None:
        db.add(Strategy(
            subscription_id=subscription_id,
            airline_url=airline_url,
            viewport_w=viewport[0],
            viewport_h=viewport[1],
            actions_json=actions_json,
        ))
    else:
        row.airline_url = airline_url
        row.viewport_w = viewport[0]
        row.viewport_h = viewport[1]
        row.actions_json = actions_json
        row.recorded_at = datetime.utcnow()
    db.commit()
    logger.info(f"[queries] upserted strategy sub={subscription_id} steps={len(actions)}")


def delete_strategy(db: Session, subscription_id: int) -> None:
    """Remove the saved strategy for this subscription, if any."""
    deleted = db.query(Strategy).filter(Strategy.subscription_id == subscription_id).delete()
    db.commit()
    if deleted:
        logger.info(f"[queries] deleted strategy sub={subscription_id}")


def save_price_check(
    db: Session,
    subscription_id: int,
    amount: Optional[Decimal],
    currency: Optional[str],
    via: str,
    screenshot_path: str,
) -> PriceCheck:
    """Insert a price-check row. amount/currency may be NULL when the extractor failed."""
    row = PriceCheck(
        subscription_id=subscription_id,
        amount=amount,
        currency=currency,
        via=via,
        screenshot_path=screenshot_path,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    logger.info(
        f"[queries] saved price_check sub={subscription_id} "
        f"amount={amount} currency={currency} via={via}"
    )
    return row
