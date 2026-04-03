from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class ParseRequest(BaseModel):
    source_url: str


class ParseResponse(BaseModel):
    source_url: str

    # Route — decoded from URL or extracted from API response
    origin_iata: Optional[str] = None
    destination_iata: Optional[str] = None
    departure_date: Optional[str] = None       # "YYYY-MM-DD"
    passengers: Optional[int] = None
    is_round_trip: bool = False

    # Flight details — from Playwright / tickets-api response
    flight_number: Optional[str] = None
    airline: Optional[str] = None
    airline_iata: Optional[str] = None
    departure_time: Optional[str] = None       # "HH:MM"
    baggage_info: Optional[str] = None
    price: Optional[int] = None
    currency: str = "RUB"
    ticket_sign: Optional[str] = None         # Aviasales internal proposal ID
