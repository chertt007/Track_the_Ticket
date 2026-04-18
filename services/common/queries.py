"""Database query helpers — one place for all SELECT logic."""
from typing import Optional
from sqlalchemy.orm import Session

from .db_models import Subscription


def get_subscription(db: Session, subscription_id: int) -> Optional[Subscription]:
    """Fetch a single subscription by primary key. Returns None if not found."""
    return db.get(Subscription, subscription_id)
