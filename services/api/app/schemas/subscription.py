from datetime import date, datetime, time

from pydantic import BaseModel, HttpUrl


class SubscriptionCreate(BaseModel):
    # All flight data comes from POST /parse, baggage choice from the user.
    source_url: HttpUrl
    origin_iata: str
    destination_iata: str
    departure_date: date
    departure_time: time | None = None
    flight_number: str | None = None
    airline: str | None = None
    airline_iata: str | None = None
    airline_domain: str | None = None
    baggage_info: str | None = None
    check_frequency: int = 3


class SubscriptionOut(BaseModel):
    id: int
    source_url: str
    status: str  # active | inactive

    origin_iata: str | None
    destination_iata: str | None
    departure_date: date | None
    departure_time: time | None
    flight_number: str | None
    airline: str | None
    airline_iata: str | None
    airline_domain: str | None
    baggage_info: str | None

    is_active: bool
    expires_at: datetime | None
    check_frequency: int
    last_checked_at: datetime | None
    last_notified_at: datetime | None

    model_config = {"from_attributes": True}
