from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from .database import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id                = Column(Integer, primary_key=True, index=True)
    user_id           = Column(String, nullable=False, default="default", index=True)

    # Required fields
    departure_airport = Column(String, nullable=False)
    arrival_airport   = Column(String, nullable=False)
    airline           = Column(String, nullable=False)
    departure_date    = Column(String, nullable=False)   # "YYYY-MM-DD"
    need_baggage      = Column(Boolean, nullable=False)

    # Optional fields from the parser
    source_url        = Column(String, nullable=True)
    departure_time    = Column(String, nullable=True)    # "HH:MM"
    flight_number     = Column(String, nullable=True)
    airline_iata      = Column(String, nullable=True)

    is_active         = Column(Boolean, default=True, nullable=False)
    created_at        = Column(DateTime, default=datetime.utcnow, nullable=False)


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
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False, index=True)
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
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), unique=True, nullable=False, index=True)
    airline_url     = Column(String, nullable=False)
    viewport_w      = Column(Integer, nullable=False)
    viewport_h      = Column(Integer, nullable=False)
    actions_json    = Column(Text, nullable=False)
    recorded_at     = Column(DateTime, default=datetime.utcnow, nullable=False)
