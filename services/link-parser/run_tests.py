"""Simple test runner — no pytest dependency required."""
import sys
import os
import traceback

sys.path.insert(0, os.path.dirname(__file__))

# Stub out playwright so flight_parser.py can be imported without the browser installed
import types
_pw_mod = types.ModuleType("playwright")
_pw_async = types.ModuleType("playwright.async_api")
for _name in ("async_playwright", "Page", "Request", "Response"):
    setattr(_pw_async, _name, None)
sys.modules["playwright"] = _pw_mod
sys.modules["playwright.async_api"] = _pw_async

# ─── Run inline test logic ────────────────────────────────────────────────────
passed = 0
failed = 0

def ok(name):
    global passed
    passed += 1
    print(f"  ✓ {name}")

def fail(name, err):
    global failed
    failed += 1
    print(f"  ✗ {name}")
    print(f"    {err}")

# ─── url_decoder tests ────────────────────────────────────────────────────────
print("\n── url_decoder tests ──")
from datetime import date
from url_decoder import decode_url

TODAY = date(2026, 1, 1)

tests = [
    ("one-way basic",
     lambda: decode_url("https://www.aviasales.com/search/MRV2804MOW1", today=TODAY),
     lambda d: d.origin_iata == "MRV" and d.destination_iata == "MOW"
               and d.outbound.departure_date == date(2026, 4, 28)
               and d.passengers == 1 and not d.is_round_trip),

    ("two passengers",
     lambda: decode_url("https://www.aviasales.com/search/MOW1506LED2", today=TODAY),
     lambda d: d.passengers == 2 and d.origin_iata == "MOW" and d.destination_iata == "LED"),

    ("year rollover — past date",
     lambda: decode_url("https://www.aviasales.com/search/SVO1003LED1", today=date(2026, 3, 15)),
     lambda d: d.outbound.departure_date == date(2027, 3, 10)),

    ("today not treated as past",
     lambda: decode_url("https://www.aviasales.com/search/MRV2804MOW1", today=date(2026, 4, 28)),
     lambda d: d.outbound.departure_date == date(2026, 4, 28)),

    ("http without www",
     lambda: decode_url("http://aviasales.com/search/SVO0107AER1", today=TODAY),
     lambda d: d.origin_iata == "SVO" and d.destination_iata == "AER"
               and d.outbound.departure_date == date(2026, 7, 1)),

    ("trailing query params ignored",
     lambda: decode_url("https://www.aviasales.com/search/MRV2804MOW1?some=val", today=TODAY),
     lambda d: d.origin_iata == "MRV"),

    # Short format: MOW1506LED1 + 2006MOW1  (return origin LED is implied)
    ("round-trip short format",
     lambda: decode_url("https://www.aviasales.com/search/MOW1506LED12006MOW1", today=TODAY),
     lambda d: d.is_round_trip
               and d.return_leg.origin == "LED"
               and d.return_leg.destination == "MOW"
               and d.return_leg.departure_date == date(2026, 6, 20)),

    # Full format: both origins explicit
    ("round-trip full format",
     lambda: decode_url("https://www.aviasales.com/search/MOW1506LED1LED2006MOW1", today=TODAY),
     lambda d: d.is_round_trip
               and d.return_leg.origin == "LED"
               and d.return_leg.destination == "MOW"
               and d.return_leg.departure_date == date(2026, 6, 20)),

    ("december → january rollover",
     lambda: decode_url("https://www.aviasales.com/search/MOW0501LED1", today=date(2026, 12, 20)),
     lambda d: d.outbound.departure_date == date(2027, 1, 5)),

    ("9 passengers",
     lambda: decode_url("https://www.aviasales.com/search/SVO1506AER9", today=TODAY),
     lambda d: d.passengers == 9),
]

for name, run, check in tests:
    try:
        result = run()
        assert check(result), f"Check failed on result: {result}"
        ok(name)
    except Exception as e:
        fail(name, traceback.format_exc().strip().split("\n")[-1])

# Error cases
error_cases = [
    ("invalid URL raises ValueError",
     lambda: decode_url("https://google.com/", today=TODAY)),
    ("empty string raises ValueError",
     lambda: decode_url("", today=TODAY)),
]
for name, run in error_cases:
    try:
        run()
        fail(name, "Expected ValueError but none was raised")
    except ValueError:
        ok(name)
    except Exception as e:
        fail(name, f"Expected ValueError, got {type(e).__name__}: {e}")


# ─── flight_parser unit tests ────────────────────────────────────────────────────────
print("\n── flight_parser unit tests ──")
from flight_parser import (
    _ts_to_str, _parse_baggage, _parse_price,
    _parse_flight_leg, _build_parsed_ticket, _extract_highlighted_sign
)

parser_tests = [
    ("timestamp → date/time",
     lambda: _ts_to_str(1777383300),
     lambda r: r == ("2026-04-28", "13:35")),

    ("baggage 0pc dict",
     lambda: _parse_baggage({"s7": {"baggage": {"value": 0, "unit": "pc"}, "price": 5000, "currency": "rub"}}),
     lambda b: b.checked_pieces == 0 and str(b) == "0pc"),

    ("baggage 1pc dict",
     lambda: _parse_baggage({"s7": {"baggage": {"value": 1, "unit": "pc"}, "price": 8000, "currency": "rub"}}),
     lambda b: b.checked_pieces == 1 and str(b) == "1pc"),

    ("baggage 23kg dict",
     lambda: _parse_baggage({"s7": {"baggage": {"value": 23, "unit": "kg"}, "price": 8000, "currency": "rub"}}),
     lambda b: b.checked_weight_kg == 23 and str(b) == "23kg"),

    ("baggage integer",
     lambda: _parse_baggage({"gate1": {"baggage": 1, "price": 7000, "currency": "rub"}}),
     lambda b: b.checked_pieces == 1),

    ("baggage empty terms",
     lambda: _parse_baggage({}),
     lambda b: b.checked_pieces == 0),

    ("price parsing",
     lambda: _parse_price({"gate1": {"price": 12500, "currency": "rub"}}),
     lambda r: r == (12500, "RUB")),

    ("price empty terms",
     lambda: _parse_price({}),
     lambda r: r == (None, "RUB")),

    ("flight leg number",
     lambda: _parse_flight_leg({"number": 519, "operating_carrier": "A9",
                                 "departure": "MRV", "arrival": "AER",
                                 "departure_timestamp": 1777383300,
                                 "arrival_timestamp": 1777389000, "duration": 5700}),
     lambda l: l.flight_number == "A9 519" and l.origin == "MRV"
               and l.destination == "AER" and l.departure_time == "13:35"
               and l.duration_minutes == 95),

    ("flight leg string time fallback",
     lambda: _parse_flight_leg({"number": "A9 519", "operating_carrier": "A9",
                                 "departure": "MRV", "arrival": "AER",
                                 "departure_date": "2026-04-28",
                                 "departure_time": "13:35:00",
                                 "arrival_date": "2026-04-28",
                                 "arrival_time": "15:10:00"}),
     lambda l: l.departure_time == "13:35" and l.arrival_time == "15:10"),
]

PROPOSAL = {
    "sign": "abc123",
    "segment": [{"flight": [
        {"number": 519, "operating_carrier": "A9", "departure": "MRV", "arrival": "AER",
         "departure_timestamp": 1777383300, "arrival_timestamp": 1777389000, "duration": 5700},
        {"number": 521, "operating_carrier": "A9", "departure": "AER", "arrival": "DME",
         "departure_timestamp": 1777401900, "arrival_timestamp": 1777413000, "duration": 11100},
    ]}],
    "terms": {"gate1": {"price": 12500, "currency": "rub",
                        "baggage": {"value": 0, "unit": "pc"}}},
}
AIRLINES = {"A9": "Azimuth"}
URL = "https://www.aviasales.com/search/MRV2804DME1"

parser_tests += [
    ("full proposal — origin/destination",
     lambda: _build_parsed_ticket(URL, PROPOSAL, AIRLINES),
     lambda t: t.origin_iata == "MRV" and t.destination_iata == "DME"),

    ("full proposal — flight info",
     lambda: _build_parsed_ticket(URL, PROPOSAL, AIRLINES),
     lambda t: t.flight_number == "A9 519" and t.airline == "Azimuth"
               and t.departure_time == "13:35"),

    ("full proposal — baggage",
     lambda: _build_parsed_ticket(URL, PROPOSAL, AIRLINES),
     lambda t: t.baggage_info == "0pc"),

    ("full proposal — price",
     lambda: _build_parsed_ticket(URL, PROPOSAL, AIRLINES),
     lambda t: t.price == 12500 and t.currency == "RUB"),

    ("full proposal — segments",
     lambda: _build_parsed_ticket(URL, PROPOSAL, AIRLINES),
     lambda t: len(t.segments) == 1 and len(t.segments[0].legs) == 2),

    ("full proposal — not round trip",
     lambda: _build_parsed_ticket(URL, PROPOSAL, AIRLINES),
     lambda t: not t.is_round_trip),

    ("highlighted sign — query param",
     lambda: _extract_highlighted_sign(
         "https://www.aviasales.com/search/MRV2804MOW1?highlighted_ticket=dd0e1160ebf8ff65c1f6ffb8631f8149"),
     lambda r: r == "dd0e1160ebf8ff65c1f6ffb8631f8149"),

    ("highlighted sign — fragment",
     lambda: _extract_highlighted_sign(
         "https://www.aviasales.com/search/MRV2804MOW1#dd0e1160ebf8ff65c1f6ffb8631f8149"),
     lambda r: r == "dd0e1160ebf8ff65c1f6ffb8631f8149"),

    ("highlighted sign — none",
     lambda: _extract_highlighted_sign("https://www.aviasales.com/search/MRV2804MOW1"),
     lambda r: r is None),

    ("highlighted sign — non-hex fragment ignored",
     lambda: _extract_highlighted_sign("https://www.aviasales.com/search/MRV2804MOW1#someanchor"),
     lambda r: r is None),
]

for name, run, check in parser_tests:
    try:
        result = run()
        assert check(result), f"Check failed on: {result!r}"
        ok(name)
    except Exception as e:
        fail(name, traceback.format_exc().strip().split("\n")[-1])


# ─── Summary ──────────────────────────────────────────────────────────────────
print(f"\n{'─'*40}")
print(f"  {passed} passed  |  {failed} failed")
print(f"{'─'*40}\n")
sys.exit(0 if failed == 0 else 1)
