"""
Unit tests for url_decoder.py — no network, no browser, just pure logic.
Run: pytest tests/test_url_decoder.py -v
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from datetime import date
from url_decoder import decode_url, DecodedUrl


# Fixed "today" so tests don't break after the date passes
TODAY = date(2026, 1, 1)


# ── One-way flights ───────────────────────────────────────────────────────────

class TestOneWay:
    def test_basic_one_way(self):
        url = "https://www.aviasales.com/search/MRV2804MOW1"
        decoded = decode_url(url, today=TODAY)

        assert decoded.is_round_trip is False
        assert decoded.origin_iata == "MRV"
        assert decoded.destination_iata == "MOW"
        assert decoded.outbound.departure_date == date(2026, 4, 28)
        assert decoded.passengers == 1
        assert decoded.departure_date_str == "2026-04-28"

    def test_two_passengers(self):
        url = "https://www.aviasales.com/search/MOW1506LED2"
        decoded = decode_url(url, today=TODAY)

        assert decoded.passengers == 2
        assert decoded.origin_iata == "MOW"
        assert decoded.destination_iata == "LED"
        assert decoded.outbound.departure_date == date(2026, 6, 15)

    def test_year_rollover(self):
        """Date in the past for this year should roll over to next year."""
        yesterday = date(2026, 3, 15)
        # March 10 is in the past relative to March 15 → use 2027
        url = "https://www.aviasales.com/search/SVO1003LED1"
        decoded = decode_url(url, today=yesterday)

        assert decoded.outbound.departure_date == date(2027, 3, 10)

    def test_today_is_not_past(self):
        """Departure on today itself should NOT roll to next year."""
        today = date(2026, 4, 28)
        url = "https://www.aviasales.com/search/MRV2804MOW1"
        decoded = decode_url(url, today=today)

        assert decoded.outbound.departure_date == date(2026, 4, 28)

    def test_http_without_www(self):
        url = "http://aviasales.com/search/SVO0107AER1"
        decoded = decode_url(url, today=TODAY)

        assert decoded.origin_iata == "SVO"
        assert decoded.destination_iata == "AER"
        assert decoded.outbound.departure_date == date(2026, 7, 1)

    def test_trailing_query_params_ignored(self):
        url = "https://www.aviasales.com/search/MRV2804MOW1?some_param=value"
        decoded = decode_url(url, today=TODAY)

        assert decoded.origin_iata == "MRV"
        assert decoded.destination_iata == "MOW"

    def test_fragment_ignored(self):
        url = "https://www.aviasales.com/search/MRV2804MOW1#dd0e1160ebf8ff65c1f6ffb8631f8149"
        decoded = decode_url(url, today=TODAY)

        assert decoded.origin_iata == "MRV"


# ── Round-trip flights ────────────────────────────────────────────────────────

class TestRoundTrip:
    def test_round_trip_detected(self):
        # MOW → LED June 15, return June 20, 1 pax
        url = "https://www.aviasales.com/search/MOW1506LED12006MOW1"
        decoded = decode_url(url, today=TODAY)

        assert decoded.is_round_trip is True
        assert decoded.origin_iata == "MOW"
        assert decoded.destination_iata == "LED"
        assert decoded.outbound.departure_date == date(2026, 6, 15)

        assert decoded.return_leg is not None
        assert decoded.return_leg.origin == "LED"
        assert decoded.return_leg.destination == "MOW"
        assert decoded.return_leg.departure_date == date(2026, 6, 20)

    def test_round_trip_same_day(self):
        url = "https://www.aviasales.com/search/MOW1506LED11506LED1"
        decoded = decode_url(url, today=TODAY)

        assert decoded.is_round_trip is True
        assert decoded.return_leg.departure_date == date(2026, 6, 15)


# ── Error handling ────────────────────────────────────────────────────────────

class TestErrors:
    def test_invalid_url_raises(self):
        with pytest.raises(ValueError, match="does not look like"):
            decode_url("https://google.com/", today=TODAY)

    def test_no_direction_raises(self):
        with pytest.raises(ValueError):
            decode_url("https://www.aviasales.com/search/BADTOKEN", today=TODAY)

    def test_empty_string_raises(self):
        with pytest.raises(ValueError):
            decode_url("", today=TODAY)


# ── Edge cases ────────────────────────────────────────────────────────────────

class TestEdgeCases:
    def test_december_to_january_rollover(self):
        """Flight on Jan 5 when today is Dec 20 — should be in next year."""
        today = date(2026, 12, 20)
        url = "https://www.aviasales.com/search/MOW0501LED1"
        decoded = decode_url(url, today=today)

        assert decoded.outbound.departure_date == date(2027, 1, 5)

    def test_9_passengers(self):
        url = "https://www.aviasales.com/search/SVO1506AER9"
        decoded = decode_url(url, today=TODAY)
        assert decoded.passengers == 9
