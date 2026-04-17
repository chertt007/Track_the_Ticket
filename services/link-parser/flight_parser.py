"""
Aviasales link parser.

Strategy
--------
Shared Aviasales URLs embed all flight data in the `t` query parameter.
We parse carrier, timestamps, airports, price, and baggage directly from
the URL — no API interception needed.

Short link resolution (avs.io/xxx etc.):
  Playwright navigates to the short URL, grabs the final URL after redirect
  (domcontentloaded → page.url → close browser immediately). ~3 s.

`t` parameter format (inferred from Aviasales network traffic):
  {carrier:2}{dep_unix:10}{arr_unix:10}{duration_min:N}{origin:3}{dest:3}_{sign:32}_{extra}

  Example:
    DP17783589001778363700000080SVOLED_724141339cfc181d667dd3f920ef9e2d_4948.16...
    DP         = carrier IATA (Pobeda)
    1778358900 = departure Unix timestamp (UTC)
    1778363700 = arrival Unix timestamp (UTC)
    000080     = duration in minutes (80 min), 6 digits
    SVO        = departure airport IATA
    LED        = arrival airport IATA
    724141339cfc181d667dd3f920ef9e2d = ticket sign
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse, parse_qs

from playwright.async_api import async_playwright

from models import BaggageInfo, FlightLeg, ParsedTicket, TravelSegment
from url_decoder import decode_url

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

NAV_TIMEOUT_MS = 30_000
VIEWPORT = {"width": 390, "height": 844}

# Aviasales search URL (all regional domains)
_AVIASALES_SEARCH_RE = re.compile(
    r'aviasales\.(ru|com|co\.il|com\.ua|kz|by)/search/', re.IGNORECASE
)

# t=DP17783589001778363700000080SVOLED_<sign>_<extra>
# Groups are self-delimiting: digits vs uppercase letters don't overlap.
_T_PARAM_RE = re.compile(
    r'^(?P<carrier>[A-Z0-9]{2})'
    r'(?P<dep_ts>\d{10})'
    r'(?P<arr_ts>\d{10})'
    r'(?P<dur_min>\d+)'
    r'(?P<origin>[A-Z]{3})'
    r'(?P<dest>[A-Z]{3})'
    r'(?:_(?P<sign>[0-9a-f]{32}))?'
)

# static_fare_key baggage: L0 = no bags, L1 = 1 bag, etc.
_FARE_LUGGAGE_RE = re.compile(r'L(\d+)')

AIRLINE_NAMES: dict[str, str] = {
    "SU": "Aeroflot",
    "S7": "S7 Airlines",
    "DP": "Pobeda",
    "U6": "Ural Airlines",
    "N4": "Nordwind Airlines",
    "5N": "SmartAvia",
    "A9": "Azimuth",
    "UT": "UTair",
    "IO": "IrAero",
    "7R": "RusLine",
    "Y7": "NordStar",
    "TK": "Turkish Airlines",
    "LY": "El Al",
    "IZ": "Arkia",
    "FZ": "flydubai",
    "EK": "Emirates",
    "QR": "Qatar Airways",
    "EY": "Etihad Airways",
    "LH": "Lufthansa",
    "AF": "Air France",
    "KL": "KLM",
    "BA": "British Airways",
    "FR": "Ryanair",
    "W6": "Wizz Air",
    "U2": "easyJet",
    "SQ": "Singapore Airlines",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _ts_to_str(ts: int | float) -> tuple[str, str]:
    """Convert Unix timestamp to ("YYYY-MM-DD", "HH:MM") in UTC."""
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    return dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M")


# ── URL parsing ───────────────────────────────────────────────────────────────

def _parse_from_url_params(url: str) -> Optional[ParsedTicket]:
    """
    Parse ParsedTicket from Aviasales shared URL parameters.
    Returns None if the URL does not contain the `t` parameter.
    """
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)

    def _first(key: str) -> Optional[str]:
        vals = qs.get(key)
        return vals[0] if vals else None

    t_raw = _first("t")
    if not t_raw:
        return None

    m = _T_PARAM_RE.match(t_raw)
    if not m:
        logger.debug(f"[url_parse] t param did not match pattern: {t_raw[:80]}")
        return None

    carrier    = m.group("carrier")
    dep_ts     = int(m.group("dep_ts"))
    arr_ts     = int(m.group("arr_ts"))
    dur_min    = int(m.group("dur_min"))
    origin_ap  = m.group("origin")
    dest_ap    = m.group("dest")
    sign       = m.group("sign")

    dep_date, dep_time = _ts_to_str(dep_ts)
    arr_date, arr_time = _ts_to_str(arr_ts)

    # Price
    price_raw    = _first("expected_price")
    currency_raw = (_first("expected_price_currency") or "rub").upper()
    price        = int(float(price_raw)) if price_raw else None

    # Baggage from static_fare_key e.g. "TY|P0|H1|L0|CH1|R0|TBC0"
    fare_key = _first("static_fare_key") or ""
    lug_m    = _FARE_LUGGAGE_RE.search(fare_key)
    checked  = int(lug_m.group(1)) if lug_m else 0
    baggage  = BaggageInfo(checked_pieces=checked, raw=f"{checked}pc")

    # Route from URL path segment (origin city, destination, date, passengers)
    try:
        decoded      = decode_url(url)
        origin_iata  = decoded.origin_iata
        dest_iata    = decoded.destination_iata
        dep_date_str = decoded.departure_date_str
        passengers   = decoded.passengers
        is_round_trip = decoded.is_round_trip
    except ValueError:
        origin_iata   = origin_ap
        dest_iata     = dest_ap
        dep_date_str  = dep_date
        passengers    = 1
        is_round_trip = False

    leg = FlightLeg(
        carrier_iata=carrier,
        origin=origin_ap,
        destination=dest_ap,
        departure_date=dep_date,
        departure_time=dep_time,
        arrival_date=arr_date,
        arrival_time=arr_time,
        duration_minutes=dur_min,
    )

    airline_name = AIRLINE_NAMES.get(carrier, carrier)

    logger.info(
        f"[url_parse] {origin_iata}→{dest_iata} | {dep_date_str} {dep_time} "
        f"| {airline_name} ({carrier}) | {dur_min}min "
        f"| price={price} {currency_raw} | baggage={baggage}"
    )

    return ParsedTicket(
        origin_iata=origin_iata,
        destination_iata=dest_iata,
        departure_date=dep_date_str,
        passengers=passengers,
        flight_number=None,
        airline=airline_name,
        airline_iata=carrier,
        departure_time=dep_time,
        baggage_info=str(baggage),
        segments=[TravelSegment(legs=[leg])],
        is_round_trip=is_round_trip,
        price=price,
        currency=currency_raw,
        ticket_sign=sign,
    )


# ── Short URL resolution ──────────────────────────────────────────────────────

def _is_full_aviasales_url(url: str) -> bool:
    return bool(_AVIASALES_SEARCH_RE.search(url))


async def _resolve_url_via_playwright(url: str, *, headless: bool = True) -> str:
    """Follow redirects (e.g. avs.io → aviasales.com/search/...) and return the final URL."""
    logger.info(f"[resolve] following redirect: {url}")
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=headless)
        context = await browser.new_context(
            viewport=VIEWPORT,
            user_agent=(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
            ),
            locale="ru-RU",
        )
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=NAV_TIMEOUT_MS)
            final = page.url
        finally:
            await browser.close()
    logger.info(f"[resolve] → {final}")
    return final


# ── Public entry point ────────────────────────────────────────────────────────

async def fetch_parsed_ticket(url: str, *, headless: bool = True) -> ParsedTicket:
    """
    Parse an Aviasales URL and return a ParsedTicket.

    1. If the URL is a short link (avs.io etc.), resolve it to the full URL (~3 s).
    2. Parse ticket data from URL parameters (instant).

    Raises:
        ValueError: URL cannot be resolved or does not contain parseable ticket data.
    """
    logger.info(f"[fetch] start | url={url}")

    final_url = url
    if not _is_full_aviasales_url(url):
        final_url = await _resolve_url_via_playwright(url, headless=headless)

    ticket = _parse_from_url_params(final_url)
    if ticket is None:
        raise ValueError(
            f"URL does not contain ticket data (no `t` parameter): {final_url}"
        )

    logger.info(f"[fetch] done | {ticket.origin_iata}→{ticket.destination_iata}")
    return ticket
