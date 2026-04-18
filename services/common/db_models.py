from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String
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
