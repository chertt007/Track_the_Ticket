"""
Unit tests for flight_parser.py helper functions — no Playwright, no network.
Tests the proposal parsing logic with mocked API response data.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from flight_parser import (
    _ts_to_str,
    _parse_baggage,
    _parse_price,
    _parse_flight_leg,
    _build_parsed_ticket,
    _extract_highlighted_sign,
)
from models import BaggageInfo


# ── Timestamp helper ──────────────────────────────────────────────────────────

class TestTimestampHelper:
    def test_known_timestamp(self):
        # 2026-04-28 13:35 UTC
        ts = 1777383300
        d, t = _ts_to_str(ts)
        assert d == "2026-04-28"
        assert t == "13:35"


# ── Baggage parsing ───────────────────────────────────────────────────────────

class TestBaggageParsing:
    def test_no_checked_bag_dict(self):
        terms = {"s7": {"baggage": {"value": 0, "unit": "pc"}, "price": 5000, "currency": "rub"}}
        b = _parse_baggage(terms)
        assert b.checked_pieces == 0
        assert str(b) == "0pc"

    def test_one_checked_bag_dict(self):
        terms = {"s7": {"baggage": {"value": 1, "unit": "pc"}, "price": 8000, "currency": "rub"}}
        b = _parse_baggage(terms)
        assert b.checked_pieces == 1
        assert str(b) == "1pc"

    def test_weight_based_baggage(self):
        terms = {"s7": {"baggage": {"value": 23, "unit": "kg"}, "price": 8000, "currency": "rub"}}
        b = _parse_baggage(terms)
        assert b.checked_weight_kg == 23
        assert str(b) == "23kg"

    def test_integer_baggage(self):
        terms = {"gate1": {"baggage": 1, "price": 7000, "currency": "rub"}}
        b = _parse_baggage(terms)
        assert b.checked_pieces == 1

    def test_empty_terms(self):
        b = _parse_baggage({})
        assert b.checked_pieces == 0


# ── Price parsing ─────────────────────────────────────────────────────────────

class TestPriceParsing:
    def test_basic_price(self):
        terms = {"gate1": {"price": 12500, "currency": "rub"}}
        price, currency = _parse_price(terms)
        assert price == 12500
        assert currency == "RUB"

    def test_empty_terms(self):
        price, currency = _parse_price({})
        assert price is None
        assert currency == "RUB"


# ── Flight leg parsing ────────────────────────────────────────────────────────

class TestFlightLegParsing:
    # Aviasales format with timestamps
    FLIGHT_WITH_TS = {
        "number": 519,
        "operating_carrier": "A9",
        "departure": "MRV",
        "arrival": "AER",
        "departure_timestamp": 1777383300,   # 2026-04-28 13:35 UTC
        "arrival_timestamp": 1777389000,     # 2026-04-28 15:10 UTC
        "duration": 5700,                    # 95 minutes
    }

    def test_flight_number_constructed(self):
        leg = _parse_flight_leg(self.FLIGHT_WITH_TS)
        assert leg.flight_number == "A9 519"

    def test_airports(self):
        leg = _parse_flight_leg(self.FLIGHT_WITH_TS)
        assert leg.origin == "MRV"
        assert leg.destination == "AER"

    def test_times_from_timestamp(self):
        leg = _parse_flight_leg(self.FLIGHT_WITH_TS)
        assert leg.departure_date == "2026-04-28"
        assert leg.departure_time == "13:35"

    def test_duration(self):
        leg = _parse_flight_leg(self.FLIGHT_WITH_TS)
        assert leg.duration_minutes == 95

    def test_fallback_to_string_fields(self):
        flight = {
            "number": "A9 519",
            "operating_carrier": "A9",
            "departure": "MRV",
            "arrival": "AER",
            "departure_date": "2026-04-28",
            "departure_time": "13:35:00",
            "arrival_date": "2026-04-28",
            "arrival_time": "15:10:00",
        }
        leg = _parse_flight_leg(flight)
        assert leg.departure_time == "13:35"  # sliced to HH:MM
        assert leg.arrival_time == "15:10"


# ── Full proposal → ParsedTicket ──────────────────────────────────────────────

class TestBuildParsedTicket:
    PROPOSAL = {
        "sign": "abc123",
        "segment": [
            {
                "flight": [
                    {
                        "number": 519,
                        "operating_carrier": "A9",
                        "departure": "MRV",
                        "arrival": "AER",
                        "departure_timestamp": 1777383300,
                        "arrival_timestamp": 1777389000,
                        "duration": 5700,
                    },
                    {
                        "number": 521,
                        "operating_carrier": "A9",
                        "departure": "AER",
                        "arrival": "DME",
                        "departure_timestamp": 1777401900,  # +3h35m layover
                        "arrival_timestamp": 1777413000,
                        "duration": 11100,
                    },
                ]
            }
        ],
        "terms": {
            "gate1": {
                "price": 12500,
                "currency": "rub",
                "baggage": {"value": 0, "unit": "pc"},
            }
        },
    }
    AIRLINES = {"A9": "Azimuth"}
    URL = "https://www.aviasales.com/search/MRV2804DME1"

    def test_basic_fields(self):
        from datetime import date
        ticket = _build_parsed_ticket(self.URL, self.PROPOSAL, self.AIRLINES)

        assert ticket.origin_iata == "MRV"
        assert ticket.destination_iata == "DME"
        assert ticket.departure_date == "2026-04-28"
        assert ticket.passengers == 1

    def test_flight_info(self):
        ticket = _build_parsed_ticket(self.URL, self.PROPOSAL, self.AIRLINES)
        assert ticket.flight_number == "A9 519"
        assert ticket.airline == "Azimuth"
        assert ticket.airline_iata == "A9"
        assert ticket.departure_time == "13:35"

    def test_baggage(self):
        ticket = _build_parsed_ticket(self.URL, self.PROPOSAL, self.AIRLINES)
        assert ticket.baggage_info == "0pc"

    def test_price(self):
        ticket = _build_parsed_ticket(self.URL, self.PROPOSAL, self.AIRLINES)
        assert ticket.price == 12500
        assert ticket.currency == "RUB"

    def test_segments_count(self):
        ticket = _build_parsed_ticket(self.URL, self.PROPOSAL, self.AIRLINES)
        assert len(ticket.segments) == 1
        assert len(ticket.segments[0].legs) == 2  # two flights = layover

    def test_is_not_round_trip(self):
        ticket = _build_parsed_ticket(self.URL, self.PROPOSAL, self.AIRLINES)
        assert ticket.is_round_trip is False

    def test_sign(self):
        ticket = _build_parsed_ticket(self.URL, self.PROPOSAL, self.AIRLINES)
        assert ticket.ticket_sign == "abc123"


# ── Highlighted sign extraction ───────────────────────────────────────────────

class TestHighlightedSignExtraction:
    def test_query_param(self):
        url = "https://www.aviasales.com/search/MRV2804MOW1?highlighted_ticket=dd0e1160ebf8ff65c1f6ffb8631f8149"
        assert _extract_highlighted_sign(url) == "dd0e1160ebf8ff65c1f6ffb8631f8149"

    def test_sign_param(self):
        url = "https://www.aviasales.com/search/MRV2804MOW1?sign=abcdef1234567890abcdef1234567890"
        assert _extract_highlighted_sign(url) == "abcdef1234567890abcdef1234567890"

    def test_fragment(self):
        url = "https://www.aviasales.com/search/MRV2804MOW1#dd0e1160ebf8ff65c1f6ffb8631f8149"
        assert _extract_highlighted_sign(url) == "dd0e1160ebf8ff65c1f6ffb8631f8149"

    def test_no_sign(self):
        url = "https://www.aviasales.com/search/MRV2804MOW1"
        assert _extract_highlighted_sign(url) is None

    def test_non_hex_fragment_ignored(self):
        url = "https://www.aviasales.com/search/MRV2804MOW1#someanchor"
        assert _extract_highlighted_sign(url) is None
