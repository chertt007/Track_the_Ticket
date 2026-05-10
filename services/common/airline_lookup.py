"""
IATA → airline display name lookup.

Backed by the OpenFlights `airlines.dat` dump (Open Database License) shipped
at the project's `/data/airlines.dat`. The file is loaded once, lazily, on
first call and cached for the process lifetime.

A small overrides dict layered on top fixes upstream gaps and pins names for
codes that are missing or ambiguous in OpenFlights.
"""
from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# services/common/airline_lookup.py → ../../data/airlines.dat
_DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "airlines.dat"

# Applied after the OpenFlights load — overrides win on conflict.
# Add codes here when OpenFlights is missing them, marks them inactive,
# or returns the wrong carrier (e.g. historical IATA reuse).
_OVERRIDES: dict[str, str] = {
    # Russian / CIS carriers — OpenFlights has stale or wrong entries
    # (defunct airlines marked Active=Y, pre-rebranding names, etc.).
    "WZ": "Red Wings",          # OpenFlights OK; pinned defensively
    "DP": "Pobeda",             # OpenFlights returns "First Choice Airways" (defunct UK charter)
    "N4": "Nordwind Airlines",  # OpenFlights returns "Regionalia México"
    "5N": "Smartavia",          # OpenFlights returns pre-rebrand "Aeroflot-Nord"
    "IO": "IrAero",             # OpenFlights returns "Indonesian Airlines"
    "7R": "RusLine",            # OpenFlights returns "Svyaz Rossiya"
    "HZ": "Aurora",             # OpenFlights returns pre-merger "Sat Airlines"
    "YC": "Yamal Airlines",     # OpenFlights returns "Ciel Canadien"
    "R3": "Yakutia Airlines",   # OpenFlights returns more verbose "Aircompany Yakutia"
    "KP": "Pegas Fly",          # OpenFlights returns "Dense Airways"
}

_cache: Optional[dict[str, str]] = None


def _load() -> dict[str, str]:
    """Parse OpenFlights airlines.dat into a dict[IATA → name]."""
    mapping: dict[str, str] = {}

    if not _DATA_PATH.exists():
        logger.warning(
            f"[airline_lookup] {_DATA_PATH} not found — falling back to overrides only"
        )
    else:
        with _DATA_PATH.open("r", encoding="utf-8") as f:
            for row in csv.reader(f):
                if len(row) < 8:
                    continue
                _id, name, _alias, iata, _icao, _cs, _country, active = row[:8]
                # Skip inactive carriers, missing/sentinel IATAs, and non-2-letter codes.
                if active != "Y":
                    continue
                if not iata or iata == r"\N" or len(iata) != 2:
                    continue
                # First active entry wins on collision; manual overrides
                # handle the cases where the first entry is wrong.
                mapping.setdefault(iata, name)
        logger.info(
            f"[airline_lookup] loaded {len(mapping)} active airlines from {_DATA_PATH.name}"
        )

    mapping.update(_OVERRIDES)
    return mapping


def get_airline_name(iata: Optional[str]) -> Optional[str]:
    """Return the display name for an IATA code, or None if unknown."""
    global _cache
    if not iata:
        return None
    if _cache is None:
        _cache = _load()
    return _cache.get(iata.upper())
