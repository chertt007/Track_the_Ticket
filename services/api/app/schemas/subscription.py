from datetime import date, datetime, time

from pydantic import BaseModel, HttpUrl


class SubscriptionCreate(BaseModel):
    # User only provides the Aviasales URL.
    # All flight details are extracted by the link-parser + strategy-agent pipeline.
    source_url: HttpUrl
    check_frequency: int = 3


class SubscriptionOut(BaseModel):
    id: int
    source_url: str
    status: str  # pending | active | failed

    # Filled in by link-parser — present when status = active
    origin_iata: str | None
    destination_iata: str | None
    departure_date: date | None
    departure_time: time | None      # mandatory once active — identifies exact flight
    flight_number: str | None        # mandatory once active
    airline: str | None              # mandatory once active
    baggage_info: str | None

    is_active: bool
    check_frequency: int
    last_checked_at: datetime | None
    last_notified_at: datetime | None

    model_config = {"from_attributes": True}
