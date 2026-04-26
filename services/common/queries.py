"""Database query helpers — one place for all SELECT logic."""
import logging
from typing import Optional
from sqlalchemy.orm import Session

from .db_models import Airline, Subscription

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
