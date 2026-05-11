import uuid
from datetime import datetime
from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship
from .database import Base


def _new_id() -> str:
    """Opaque, globally unique subscription/PK string.

    32-char uuid4 hex — never reused, no enumeration, no collision risk.
    Used instead of integer auto-increment to avoid orphaned-FK reuse: when
    a row is deleted SQLite happily hands the same INTEGER PK to the next
    INSERT, which let stale rows in child tables (e.g. `strategies`) match
    a brand-new subscription.
    """
    return uuid.uuid4().hex


class User(Base):
    """
    Application user, keyed by Firebase Authentication UID. A row is
    lazily created on the first authenticated request (see
    `upsert_user` in queries.py). `telegram_chat_id` is set when the
    user redeems a deep-link token via the Telegram bot.
    """
    __tablename__ = "users"

    id               = Column(String, primary_key=True)                       # Firebase UID
    email            = Column(String, nullable=True)
    telegram_chat_id = Column(BigInteger, nullable=True, index=True)
    created_at       = Column(DateTime, default=datetime.utcnow, nullable=False)


class TelegramLinkToken(Base):
    """
    One-time deep-link token used to bind a Telegram chat to a `users` row.

    Flow: web app calls POST /telegram/link-token → row inserted here. User
    opens https://t.me/<bot>?start=<token>; bot forwards token to API which
    validates expiry/single-use, sets `users.telegram_chat_id`, and stamps
    `used_at`. Tokens are short-lived (10 min) and single-use.
    """
    __tablename__ = "telegram_link_tokens"

    token      = Column(String, primary_key=True)                              # uuid4 hex
    user_id    = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    used_at    = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Subscription(Base):
    __tablename__ = "subscriptions"

    id                = Column(String(32), primary_key=True, default=_new_id)
    user_id           = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    # Required fields
    departure_airport = Column(String, nullable=False)
    arrival_airport   = Column(String, nullable=False)
    airline           = Column(String, nullable=False)
    departure_date    = Column(String, nullable=False)   # "YYYY-MM-DD"

    # Optional fields from the parser
    source_url        = Column(String, nullable=True)
    departure_time    = Column(String, nullable=True)    # "HH:MM"
    flight_number     = Column(String, nullable=True)
    airline_iata      = Column(String, nullable=True)

    is_active         = Column(Boolean, default=True, nullable=False)
    created_at        = Column(DateTime, default=datetime.utcnow, nullable=False)

    # ORM-level cascade: deleting a Subscription deletes all child
    # strategies/price_checks. Without this an orphaned strategy from a
    # deleted subscription could match a future subscription that reused
    # the same id (no longer possible with uuid PKs, but the cascade is
    # still the correct contract — child rows have no meaning without
    # their parent).
    strategies    = relationship(
        "Strategy", cascade="all, delete-orphan", passive_deletes=False
    )
    price_checks  = relationship(
        "PriceCheck", cascade="all, delete-orphan", passive_deletes=False
    )


class Airline(Base):
    """Lookup table mapping an airline display name to its website URL."""
    __tablename__ = "airlines"

    id           = Column(Integer, primary_key=True, index=True)
    airline_name = Column(String, nullable=False, unique=True, index=True)
    airline_url  = Column(String, nullable=False)


class PriceCheck(Base):
    """
    History of price checks for each subscription. One row per successful
    end-of-pipeline screenshot — both the LLM-driven first run and the
    cheap replay path land here. `amount`/`currency` are NULL when the
    extractor agent could not read the price off the final page.
    """
    __tablename__ = "price_checks"

    id              = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(String(32), ForeignKey("subscriptions.id"), nullable=False, index=True)
    checked_at      = Column(DateTime, default=datetime.utcnow, nullable=False)
    amount          = Column(Numeric(10, 2), nullable=True)
    currency        = Column(String, nullable=True)
    via             = Column(String, nullable=False)
    screenshot_path = Column(String, nullable=False)


class Strategy(Base):
    """
    Saved replay strategy for a subscription — the ordered list of
    Computer-Use actions the LLM agent executed during the first
    successful run. Replay path reads this table instead of calling
    the LLM, so subsequent price checks for the same subscription
    cost ~$0 in tokens.

    `actions_json` stores the action list as a JSON blob. We always
    read/write it as one ordered list, never query individual actions,
    so normalising to a separate table would only add joins for nothing.

    One strategy per subscription (UNIQUE on subscription_id) — re-records
    overwrite via UPSERT.
    """
    __tablename__ = "strategies"

    id              = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(String(32), ForeignKey("subscriptions.id"), unique=True, nullable=False, index=True)
    airline_url     = Column(String, nullable=False)
    viewport_w      = Column(Integer, nullable=False)
    viewport_h      = Column(Integer, nullable=False)
    actions_json    = Column(Text, nullable=False)
    recorded_at     = Column(DateTime, default=datetime.utcnow, nullable=False)
