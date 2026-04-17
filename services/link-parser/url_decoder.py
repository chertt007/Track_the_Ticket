"""
Deterministic Aviasales URL decoder — no network required.

Aviasales search URL format:
    https://www.aviasales.com/search/{ORIGIN}{DD}{MM}{DESTINATION}{N}[{RETURN_DD}{RETURN_MM}{N}]

Examples:
    MRV2804MOW1           one-way  MRV → MOW, 28 Apr, 1 pax
    MOW1506LED2           one-way  MOW → LED, 15 Jun, 2 pax
    MOW1506LED11506MOW1   round-trip MOW → LED 15 Jun, return LED → MOW 15 Jun, 1 pax

Segment grammar (regex):
    [A-Z]{3}   origin IATA (3 uppercase letters)
    \d{2}      departure day
    \d{2}      departure month
    [A-Z]{3}   destination IATA (3 uppercase letters)
    \d{1}      passenger count (1-9)
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date


# One parsed direction inside a URL (e.g. outbound or return leg)
@dataclass
class UrlDirection:
    origin: str
    destination: str
    departure_date: date
    passengers: int


@dataclass
class DecodedUrl:
    """Result of decoding an Aviasales search URL."""
    raw_url: str
    outbound: UrlDirection
    return_leg: UrlDirection | None = None   # None for one-way flights

    @property
    def is_round_trip(self) -> bool:
        return self.return_leg is not None

    @property
    def origin_iata(self) -> str:
        return self.outbound.origin

    @property
    def destination_iata(self) -> str:
        return self.outbound.destination

    @property
    def departure_date_str(self) -> str:
        return self.outbound.departure_date.isoformat()

    @property
    def passengers(self) -> int:
        return self.outbound.passengers


# Full direction: 3-letter origin + 2-digit day + 2-digit month + 3-letter dest + 1-digit pax
# Example: MRV2804MOW1
_DIRECTION_FULL_RE = re.compile(r'([A-Z]{3})(\d{2})(\d{2})([A-Z]{3})(\d)')

# Return-leg short form (origin implied = outbound destination):
# 2-digit day + 2-digit month + 3-letter dest + 1-digit pax
# Example: 2006MOW1  (the return-origin LED is implicit)
_DIRECTION_SHORT_RE = re.compile(r'(\d{2})(\d{2})([A-Z]{3})(\d)')

# Full search-path segment from the URL
_SEARCH_PATH_RE = re.compile(r'/search/([A-Z0-9]+)', re.IGNORECASE)


def _resolve_year(day: int, month: int, ref_date: date) -> date:
    dep = date(ref_date.year, month, day)
    if dep < ref_date:
        dep = date(ref_date.year + 1, month, day)
    return dep


def _parse_direction_full(raw: str, ref_date: date) -> UrlDirection:
    """Parse a full direction string like "MRV2804MOW1"."""
    m = _DIRECTION_FULL_RE.fullmatch(raw.upper())
    if not m:
        raise ValueError(f"Cannot parse direction string: {raw!r}")
    origin, day_s, month_s, destination, pax_s = m.groups()
    dep = _resolve_year(int(day_s), int(month_s), ref_date)
    return UrlDirection(origin=origin, destination=destination,
                        departure_date=dep, passengers=int(pax_s))


def _parse_return_short(raw: str, implied_origin: str, ref_date: date) -> UrlDirection:
    """
    Parse a short return-leg string like "2006MOW1".
    The origin is inferred from the outbound destination.
    """
    m = _DIRECTION_SHORT_RE.fullmatch(raw.upper())
    if not m:
        raise ValueError(f"Cannot parse short return string: {raw!r}")
    day_s, month_s, destination, pax_s = m.groups()
    dep = _resolve_year(int(day_s), int(month_s), ref_date)
    return UrlDirection(origin=implied_origin, destination=destination,
                        departure_date=dep, passengers=int(pax_s))


def decode_url(url: str, today: date | None = None) -> DecodedUrl:
    """
    Decode an Aviasales search URL.

    Supports two round-trip formats:
      • Full:  MOW1506LED1LED2006MOW1   (both origins explicit)
      • Short: MOW1506LED12006MOW1      (return origin implied = LED)

    Args:
        url:   Full Aviasales URL, e.g. "https://www.aviasales.com/search/MRV2804MOW1"
        today: Reference date for year resolution (defaults to date.today()).

    Returns:
        DecodedUrl with outbound (and optionally return_leg) filled in.

    Raises:
        ValueError: If the URL cannot be parsed.
    """
    if today is None:
        today = date.today()

    path_match = _SEARCH_PATH_RE.search(url)
    if not path_match:
        raise ValueError(f"URL does not look like an Aviasales search link: {url!r}")

    search_token = path_match.group(1).upper()

    # Try to find full direction tokens (3-letter origin + DDMM + 3-letter dest + N)
    full_matches = _DIRECTION_FULL_RE.findall(search_token)
    if not full_matches:
        raise ValueError(f"No valid direction found in search token: {search_token!r}")

    # Reconstruct the matched direction strings
    full_strings = ["".join(parts) for parts in full_matches]

    outbound = _parse_direction_full(full_strings[0], today)
    return_leg: UrlDirection | None = None

    if len(full_strings) >= 2:
        # Round-trip, full format: both origins explicit (e.g. MOW1506LED1LED2006MOW1)
        return_leg = _parse_direction_full(full_strings[1], outbound.departure_date)
    else:
        # Check for short return-leg format: outbound consumed 11 chars, remainder may be DDMM+DEST+N
        # E.g. MOW1506LED12006MOW1 → outbound=MOW1506LED1, short_return=2006MOW1
        outbound_len = 11  # 3 + 2 + 2 + 3 + 1
        remainder = search_token[outbound_len:]
        short_m = _DIRECTION_SHORT_RE.fullmatch(remainder) if remainder else None
        if short_m:
            return_leg = _parse_return_short(
                remainder,
                implied_origin=outbound.destination,
                ref_date=outbound.departure_date,
            )

    return DecodedUrl(
        raw_url=url,
        outbound=outbound,
        return_leg=return_leg,
    )
