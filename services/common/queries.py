"""Database query helpers — one place for all SELECT logic."""
import json
import logging
import secrets
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .db_models import Airline, PriceCheck, Strategy, Subscription, TelegramLinkToken, User

logger = logging.getLogger(__name__)


def get_user(db: Session, user_id: str) -> Optional[User]:
    """Fetch a single user by Firebase UID. Returns None if not found."""
    return db.get(User, user_id)


def upsert_user(db: Session, user_id: str, email: Optional[str]) -> User:
    """
    Lazily create a `users` row on the user's first authenticated request,
    or refresh the cached email if Firebase reports a new one. Returns the
    persisted SQLAlchemy User.
    """
    user = db.get(User, user_id)
    if user is None:
        user = User(id=user_id, email=email)
        db.add(user)
        try:
            db.commit()
        except IntegrityError:
            # Concurrent first-login: another request inserted the row between
            # our SELECT and INSERT. Roll back and re-fetch — the row is now
            # visible to this session.
            db.rollback()
            user = db.get(User, user_id)
            if user is None:
                raise
            return user
        db.refresh(user)
        logger.info(f"[queries] created user uid={user_id} email={email}")
        return user

    if email and user.email != email:
        user.email = email
        db.commit()
        db.refresh(user)
        logger.info(f"[queries] updated user uid={user_id} email={email}")
    return user


# ── Telegram link tokens ──────────────────────────────────────────────────────

LINK_TOKEN_TTL_MINUTES = 10


def create_link_token(db: Session, user_id: str) -> TelegramLinkToken:
    """
    Issue a fresh deep-link token for this user and invalidate any previous
    unused tokens (one active token per user at a time). Returns the row so
    the caller can build the deep-link URL and report `expires_at`.
    """
    db.query(TelegramLinkToken).filter(
        TelegramLinkToken.user_id == user_id,
        TelegramLinkToken.used_at.is_(None),
    ).delete()

    row = TelegramLinkToken(
        token=secrets.token_hex(16),  # 32-char hex, ~128 bits
        user_id=user_id,
        expires_at=datetime.utcnow() + timedelta(minutes=LINK_TOKEN_TTL_MINUTES),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    logger.info(f"[queries] issued tg link token user={user_id}")
    return row


def claim_link_token(db: Session, token: str, chat_id: int) -> tuple[bool, str]:
    """
    Redeem a deep-link token: bind `chat_id` to the user and mark the token
    used. Re-binding a different chat_id to a user is allowed and silently
    overwrites — users may switch Telegram accounts/devices.

    Returns (ok, reason) where reason is one of:
      "ok", "not_found", "expired", "already_used".
    """
    row = db.get(TelegramLinkToken, token)
    if row is None:
        return False, "not_found"
    if row.used_at is not None:
        return False, "already_used"
    if row.expires_at < datetime.utcnow():
        return False, "expired"

    user = db.get(User, row.user_id)
    if user is None:
        # Token references a user that no longer exists — treat as not_found.
        return False, "not_found"

    user.telegram_chat_id = chat_id
    row.used_at = datetime.utcnow()
    db.commit()
    logger.info(f"[queries] tg link claimed user={user.id} chat_id={chat_id}")
    return True, "ok"


def unlink_telegram(db: Session, user_id: str) -> None:
    """Drop the Telegram binding for a user. No-op if not linked."""
    user = db.get(User, user_id)
    if user is None or user.telegram_chat_id is None:
        return
    user.telegram_chat_id = None
    db.commit()
    logger.info(f"[queries] tg unlinked user={user_id}")


def get_subscription(db: Session, subscription_id: str) -> Optional[Subscription]:
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


def get_strategy(db: Session, subscription_id: str) -> Optional[dict]:
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
    subscription_id: str,
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


def delete_strategy(db: Session, subscription_id: str) -> None:
    """Remove the saved strategy for this subscription, if any."""
    deleted = db.query(Strategy).filter(Strategy.subscription_id == subscription_id).delete()
    db.commit()
    if deleted:
        logger.info(f"[queries] deleted strategy sub={subscription_id}")


def get_latest_price_check(db: Session, subscription_id: str) -> Optional[PriceCheck]:
    """
    Return the most recent price-check row for this subscription, or None.
    Used by the API to populate "last checked" info on subscription cards.
    """
    return (
        db.query(PriceCheck)
        .filter(PriceCheck.subscription_id == subscription_id)
        .order_by(PriceCheck.checked_at.desc())
        .first()
    )


def save_price_check(
    db: Session,
    subscription_id: str,
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
