"""
Ticket parser — headless Chromium via Playwright.

Opens an Aviasales URL, intercepts the internal tickets-api.aviasales.com
response, extracts the highlighted (or first) proposal, and returns
structured flight data.

Usage context
─────────────
  • Local dev:   called directly from POST /subscriptions/parse
  • Production:  this module is NOT used; the separate link-parser Lambda
                 (services/link-parser/) handles parsing via SQS.

Playwright must be installed:
    pip install playwright
    playwright install chromium
"""
from __future__ import annotations

import re
import sys
import threading
import time
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.parse import parse_qs, urlparse

from app.logging_config import get_logger

logger = get_logger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

TICKETS_API_HOST = "tickets-api.aviasales.com"

# Seconds to wait for the tickets-api response before giving up
PARSE_TIMEOUT_SECONDS = 50

# After receiving the first proposals batch, wait this long for more to arrive
EXTRA_WAIT_SECONDS = 4

VIEWPORT = {"width": 390, "height": 844}

USER_AGENT = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
)


# ── Result dataclass (plain dict — avoids circular imports with Pydantic) ─────

def _empty_result(source_url: str) -> dict:
    return {
        "source_url": source_url,
        "origin_iata": None,
        "destination_iata": None,
        "departure_date": None,
        "passengers": None,
        "is_round_trip": False,
        "flight_number": None,
        "airline": None,
        "airline_iata": None,
        "departure_time": None,
        "baggage_info": None,
        "price": None,
        "currency": "RUB",
        "ticket_sign": None,
    }


# ── Low-level helpers ─────────────────────────────────────────────────────────

def _ts_to_date_time(ts: int | float) -> tuple[str, str]:
    """Unix timestamp → ("YYYY-MM-DD", "HH:MM") in UTC."""
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    return dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M")


def _parse_baggage(terms: dict[str, Any]) -> str:
    """Return a human-readable baggage string from the first gate's terms."""
    if not terms:
        return "—"
    gate = next(iter(terms.values()), {})
    raw = gate.get("baggage") or gate.get("bags")
    if raw is None:
        checked = gate.get("luggage_info", {}).get("checked", 0)
        return f"{checked}pc"
    if isinstance(raw, dict):
        value = raw.get("value", 0)
        unit = raw.get("unit", "pc")
        return f"{value}{unit}"
    if isinstance(raw, int):
        return f"{raw}pc"
    return str(raw)


def _decode_url_data(source_url: str, final_url: str) -> dict:
    """
    Extract flight data directly from the Aviasales search URL after redirect.

    Aviasales share links encode a lot of data in the URL itself:
      - Path /search/LED0704MOW1  → origin, date, destination, passengers
      - ?expected_price=28&expected_price_currency=usd → price
      - ?t=SU{dep_ts}{arr_ts}{...}{ORIGIN}{DEST}_hash_rub_price → carrier, times, airports

    Returns a partial result dict — fields not found in the URL remain None.
    """
    result = _empty_result(source_url)

    parsed = urlparse(final_url)
    qs = parse_qs(parsed.query)

    # ── Decode search path: /search/ORIGIN(3) DD(2) MM(2) DEST(3) PAX(1) ──────
    path_m = re.search(r'/search/([A-Z]{3})(\d{2})(\d{2})([A-Z]{3})(\d+)', parsed.path)
    if path_m:
        origin, day, month, dest, pax = path_m.groups()
        # Use timestamp year if available, otherwise current year
        year = datetime.now(timezone.utc).year
        result.update({
            'origin_iata': origin,
            'destination_iata': dest,
            'departure_date': f"{year}-{month}-{day}",
            'passengers': int(pax),
            'is_round_trip': False,
        })
        logger.info(f"[PARSER][URL] path decoded: {origin} → {dest} on {year}-{month}-{day}, pax={pax}")

    # ── Decode t parameter: carrier + dep_ts(10) + arr_ts(10) + ... + ORIG + DEST ──
    t_raw = qs.get('t', [None])[0]
    if t_raw:
        # Pattern: {CARRIER(2)}{dep_unix(10)}{arr_unix(10)}{padding}{ORIGIN(3)}{DEST(3)}
        t_m = re.match(r'^([A-Z0-9]{2})(\d{10})(\d{10})\d*([A-Z]{3})([A-Z]{3})', t_raw)
        if t_m:
            carrier, dep_ts, arr_ts, t_origin, t_dest = t_m.groups()
            dep_date, dep_time = _ts_to_date_time(int(dep_ts))
            logger.info(
                f"[PARSER][URL] t-param decoded: carrier={carrier} "
                f"dep={dep_date} {dep_time} UTC  {t_origin}→{t_dest}"
            )
            result.update({
                'airline_iata': carrier,
                'departure_date': dep_date,
                'departure_time': dep_time,
                'origin_iata': t_origin,
                'destination_iata': t_dest,
            })
            # Last segment of t often contains RUB price: ..._{hash}_{price}
            t_parts = t_raw.split('_')
            if len(t_parts) >= 3:
                try:
                    rub_price = float(t_parts[-1])
                    logger.info(f"[PARSER][URL] t-param price (RUB): {rub_price:.2f}")
                    # Only use if no USD price found below
                    result['_rub_price'] = int(rub_price)
                except ValueError:
                    pass
        else:
            logger.warning(f"[PARSER][URL] t-param pattern mismatch: {t_raw[:60]}")

    # ── Expected price (USD usually) ──────────────────────────────────────────
    ep = qs.get('expected_price', [None])[0]
    ep_currency = (qs.get('expected_price_currency', ['usd'])[0]).upper()
    if ep:
        result['price'] = int(float(ep))
        result['currency'] = ep_currency
        logger.info(f"[PARSER][URL] expected_price: {ep} {ep_currency}")
    elif result.get('_rub_price'):
        result['price'] = result['_rub_price']
        result['currency'] = 'RUB'
    result.pop('_rub_price', None)

    # ── Check completeness ────────────────────────────────────────────────────
    filled = {k: v for k, v in result.items() if v is not None and v is not False}
    missing = [k for k in ('origin_iata', 'destination_iata', 'departure_date',
                            'airline_iata', 'departure_time', 'price')
               if not result.get(k)]
    logger.info(f"[PARSER][URL] decoded fields: {list(filled.keys())}")
    if missing:
        logger.warning(f"[PARSER][URL] still missing: {missing} — will try tickets-api")
    else:
        logger.info("[PARSER][URL] ✅ All essential fields found in URL — tickets-api not needed")

    return result


def _extract_highlighted_sign(url: str) -> Optional[str]:
    """
    Pull the highlighted ticket hash from the URL if present.
    Aviasales encodes it as:
      - ?highlighted_ticket=<hash>
      - ?sign=<hash>
      - #<32-char hex>
    """
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    for key in ("highlighted_ticket", "sign", "ticket_sign"):
        if key in qs:
            logger.debug(f"[PARSER] highlighted_sign found via query param '{key}'")
            return qs[key][0]
    frag = parsed.fragment.strip()
    if re.fullmatch(r"[0-9a-f]{32}", frag):
        logger.debug(f"[PARSER] highlighted_sign found via URL fragment")
        return frag
    return None


def _build_result(url: str, proposal: dict, airlines: dict[str, str]) -> dict:
    """Map a raw Aviasales proposal dict to our result schema."""
    result = _empty_result(url)

    segments = proposal.get("segment") or proposal.get("segments") or []
    terms = proposal.get("terms") or {}

    if not segments:
        logger.warning("[PARSER] Proposal has no segments")
        return result

    first_segment = segments[0]
    flights = first_segment.get("flight") or first_segment.get("flights") or []

    if not flights:
        logger.warning("[PARSER] First segment has no flights")
        return result

    first_flight = flights[0]
    last_flight = flights[-1]

    # Carrier + flight number
    carrier = str(
        first_flight.get("operating_carrier") or first_flight.get("carrier") or ""
    ).upper()
    number = first_flight.get("number") or first_flight.get("flight_number") or ""
    flight_number = f"{carrier} {number}".strip() if carrier else str(number)

    # Departure / arrival from timestamps or string fields
    dep_ts = first_flight.get("departure_timestamp") or first_flight.get("local_departure_timestamp")
    if dep_ts:
        dep_date, dep_time = _ts_to_date_time(dep_ts)
    else:
        dep_date = first_flight.get("departure_date", "")
        dep_time = (first_flight.get("departure_time") or "")[:5]

    # Route
    origin = str(first_flight.get("departure") or first_flight.get("origin") or "").upper()
    destination = str(last_flight.get("arrival") or last_flight.get("destination") or "").upper()

    # Price
    gate = next(iter(terms.values()), {}) if terms else {}
    price_raw = gate.get("price") or gate.get("unified_price")
    currency = (gate.get("currency") or "rub").upper()

    result.update({
        "origin_iata": origin,
        "destination_iata": destination,
        "departure_date": dep_date,
        "is_round_trip": len(segments) > 1,
        "flight_number": flight_number or None,
        "airline": airlines.get(carrier) or carrier or None,
        "airline_iata": carrier or None,
        "departure_time": dep_time or None,
        "baggage_info": _parse_baggage(terms),
        "price": int(price_raw) if price_raw else None,
        "currency": currency,
        "ticket_sign": proposal.get("sign"),
    })
    return result


# ── Playwright entry point ────────────────────────────────────────────────────

def parse_ticket(url: str) -> dict:
    """
    Open *url* in a headless browser, intercept the Aviasales tickets-api
    response, and return a structured dict with flight data.

    Runs synchronously — call via asyncio.to_thread() from an async context
    so the uvicorn event loop is not blocked.

    Raises
    ------
    RuntimeError   if Playwright is not installed.
    TimeoutError   if the tickets-api does not respond in time.
    """
    # On Windows, sync_playwright creates its own internal asyncio event loop
    # inside a background thread. By default that loop is SelectorEventLoop,
    # which cannot spawn subprocesses (needed to launch Chromium).
    # Setting ProactorEventLoopPolicy here (global per-process) ensures the
    # new loop is ProactorEventLoop. No-op on Linux/macOS.
    if sys.platform == "win32":
        import asyncio
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    t0 = time.perf_counter()
    logger.info("[PARSER] ── START ──────────────────────────────────────────")
    logger.info(f"[PARSER] URL: {url}")

    # Graceful import — Playwright may not be installed in all environments
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise RuntimeError(
            "Playwright is not installed. "
            "Run: pip install playwright && playwright install chromium"
        )

    highlighted_sign = _extract_highlighted_sign(url)
    logger.info(f"[PARSER] highlighted_sign={highlighted_sign!r}")

    # Shared state updated by the response listener
    proposals_data: dict = {}
    got_proposals = threading.Event()

    def on_response(response) -> None:
        if got_proposals.is_set():
            return

        # Skip static assets — they are noise (CSS, JS bundles, fonts, images)
        url = response.url
        if "static.aviasales.com" in url:
            return

        # Log all non-static responses so we can see what APIs are being called
        logger.debug(f"[PARSER] response {response.status} {url[:160]}")

        # Highlight any Aviasales domain hits
        if "aviasales" in url or "avs.io" in url:
            logger.info(f"[PARSER] aviasales API response {response.status} {url[:200]}")

        if TICKETS_API_HOST not in response.url:
            return

        logger.info(f"[PARSER] tickets-api candidate: status={response.status} url={response.url[:200]}")

        if response.status != 200:
            logger.warning(f"[PARSER] tickets-api non-200 status: {response.status}")
            return
        try:
            body = response.json()
        except Exception as e:
            logger.warning(f"[PARSER] tickets-api JSON parse failed: {e}")
            return

        top_keys = list(body.keys())[:10]
        logger.info(f"[PARSER] tickets-api body keys: {top_keys}")

        if not isinstance(body.get("proposals"), list) or not body["proposals"]:
            logger.warning(
                f"[PARSER] tickets-api body has no proposals "
                f"(proposals={body.get('proposals')!r:.50})"
            )
            return

        logger.info(f"[PARSER] tickets-api hit: {response.url}")
        logger.info(
            f"[PARSER] proposals received: {len(body['proposals'])} | "
            f"airlines in dict: {len(body.get('airlines', {}))}"
        )
        proposals_data.update(body)
        got_proposals.set()

    with sync_playwright() as pw:
        logger.info("[PARSER] Launching Chromium (headless)")
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            viewport=VIEWPORT,
            user_agent=USER_AGENT,
            locale="ru-RU",
        )
        page = context.new_page()
        page.on("response", on_response)

        # ── Navigate ──────────────────────────────────────────────────────
        logger.info("[PARSER] Navigating...")
        # domcontentloaded is enough to get the final redirect URL
        page.goto(url, wait_until="domcontentloaded", timeout=PARSE_TIMEOUT_SECONDS * 1000)
        final_url = page.url
        logger.info(f"[PARSER] DOM ready — final URL: {final_url}")

        # ── Try to extract all data from the URL itself ───────────────────────
        url_result = _decode_url_data(url, final_url)
        essential = ('origin_iata', 'destination_iata', 'departure_date',
                     'airline_iata', 'departure_time', 'price')
        if all(url_result.get(f) for f in essential):
            logger.info("[PARSER] ✅ Returning early — all data extracted from URL")
            await_browser_close = True
        else:
            await_browser_close = False
            logger.info("[PARSER] Waiting for tickets-api response...")

        if await_browser_close:
            browser.close()
            elapsed = time.perf_counter() - t0
            logger.info(f"[PARSER] ── DONE (URL decode) in {elapsed:.1f}s ──────────────")
            return url_result

        if not got_proposals.wait(timeout=PARSE_TIMEOUT_SECONDS):
            browser.close()
            raise TimeoutError(
                f"[PARSER] tickets-api did not respond within {PARSE_TIMEOUT_SECONDS}s"
            )

        # Wait briefly for additional proposals to stream in
        logger.info(f"[PARSER] First batch received — waiting {EXTRA_WAIT_SECONDS}s for more...")
        time.sleep(EXTRA_WAIT_SECONDS)
        browser.close()

    proposals: list = proposals_data.get("proposals", [])
    airlines: dict = proposals_data.get("airlines") or {}

    logger.info(f"[PARSER] Total proposals after wait: {len(proposals)}")

    if not proposals:
        raise RuntimeError("[PARSER] No proposals found in tickets-api response")

    # ── Select target proposal ────────────────────────────────────────────────
    target = None
    if highlighted_sign:
        for p in proposals:
            if p.get("sign") == highlighted_sign:
                target = p
                logger.info(f"[PARSER] Matched highlighted_sign={highlighted_sign!r}")
                break
        if target is None:
            logger.warning(
                f"[PARSER] highlighted_sign={highlighted_sign!r} not found in "
                f"{len(proposals)} proposals — falling back to first"
            )

    if target is None:
        target = proposals[0]
        logger.info(f"[PARSER] Using first proposal sign={target.get('sign')!r}")

    # ── Build result ──────────────────────────────────────────────────────────
    result = _build_result(url, target, airlines)

    elapsed = time.perf_counter() - t0
    logger.info(
        f"[PARSER] ── DONE in {elapsed:.1f}s ──────────────────────────────"
    )
    logger.info(
        f"[PARSER] route:       {result['origin_iata']} → {result['destination_iata']}"
    )
    logger.info(f"[PARSER] airline:     {result['airline']} ({result['airline_iata']})")
    logger.info(f"[PARSER] flight:      {result['flight_number']}")
    logger.info(f"[PARSER] departure:   {result['departure_date']} {result['departure_time']}")
    logger.info(f"[PARSER] baggage:     {result['baggage_info']}")
    logger.info(f"[PARSER] price:       {result['price']} {result['currency']}")
    logger.info(f"[PARSER] sign:        {result['ticket_sign']}")

    return result
