from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, model_validator


class SubscriptionCreate(BaseModel):
    # Frontend sends origin_iata / destination_iata — we map to DB field names
    origin_iata:      str
    destination_iata: str
    airline:          str
    departure_date:   str            # "YYYY-MM-DD"

    # Optional
    source_url:       Optional[str] = None
    departure_time:   Optional[str] = None   # "HH:MM"
    flight_number:    Optional[str] = None
    airline_iata:     Optional[str] = None
    airline_domain:   Optional[str] = None   # accepted but not stored

    @model_validator(mode="after")
    def check_required_fields(self) -> SubscriptionCreate:
        if not self.origin_iata:
            raise ValueError("origin_iata is required")
        if not self.destination_iata:
            raise ValueError("destination_iata is required")
        if not self.airline:
            raise ValueError("airline is required")
        if not self.departure_date:
            raise ValueError("departure_date is required")
        return self


class SubscriptionOut(BaseModel):
    id:               str
    user_id:          str

    # Named to match frontend mapSubscription expectations
    origin_iata:      str
    destination_iata: str
    airline:          str
    departure_date:   str

    source_url:       Optional[str] = None
    departure_time:   Optional[str] = None
    flight_number:    Optional[str] = None
    airline_iata:     Optional[str] = None
    is_active:        bool
    created_at:       str            # ISO string
    last_checked_at:  Optional[str] = None

    model_config = {"from_attributes": True}  # allows creating from SQLAlchemy model
