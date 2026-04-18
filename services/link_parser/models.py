"""Dataclasses produced by the link parser."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FlightLeg:
    """One individual flight segment (airport-to-airport, no stops)."""
    carrier_iata: str           # e.g. "A9"
    origin: str                 # IATA airport code e.g. "MRV"
    destination: str            # IATA airport code e.g. "AER"
    departure_date: str         # "YYYY-MM-DD"
    departure_time: str         # "HH:MM"
    arrival_date: str           # "YYYY-MM-DD"
    arrival_time: str           # "HH:MM"
    flight_number: Optional[str] = None  # e.g. "A9 519"; None when not available from URL
    duration_minutes: Optional[int] = None


@dataclass
class TravelSegment:
    """
    One direction of travel (e.g. outbound leg of a round-trip).
    A direct flight has exactly one FlightLeg.
    A flight with a layover has 2+ FlightLegs.
    """
    legs: list[FlightLeg] = field(default_factory=list)

    @property
    def origin(self) -> str:
        return self.legs[0].origin if self.legs else ""

    @property
    def destination(self) -> str:
        return self.legs[-1].destination if self.legs else ""

    @property
    def departure_date(self) -> str:
        return self.legs[0].departure_date if self.legs else ""

    @property
    def departure_time(self) -> str:
        return self.legs[0].departure_time if self.legs else ""

    @property
    def arrival_date(self) -> str:
        return self.legs[-1].arrival_date if self.legs else ""

    @property
    def arrival_time(self) -> str:
        return self.legs[-1].arrival_time if self.legs else ""

    @property
    def is_direct(self) -> bool:
        return len(self.legs) == 1


@dataclass
class BaggageInfo:
    """Baggage allowance for a ticket."""
    hand_luggage: bool = True
    checked_pieces: int = 0
    checked_weight_kg: Optional[int] = None
    raw: str = ""

    def __str__(self) -> str:
        if self.raw:
            return self.raw
        if self.checked_pieces == 0:
            return "no checked baggage"
        if self.checked_weight_kg:
            return f"{self.checked_pieces}pc / {self.checked_weight_kg}kg"
        return f"{self.checked_pieces}pc"


@dataclass
class ParsedTicket:
    """Final parsed result returned by the link parser."""
    origin_iata: str
    destination_iata: str
    departure_date: str
    passengers: int

    flight_number: Optional[str] = None
    airline: Optional[str] = None
    airline_iata: Optional[str] = None
    departure_time: Optional[str] = None
    baggage_info: Optional[str] = None

    segments: list[TravelSegment] = field(default_factory=list)
    is_round_trip: bool = False
    price: Optional[int] = None
    currency: str = "RUB"
    ticket_sign: Optional[str] = None
