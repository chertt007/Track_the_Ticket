"""
TrackTheTicket HTTP API.

Endpoints:
  GET  /health               — liveness check
  POST /parse                — parse an Aviasales URL, return flight details
  POST /subscriptions        — save a subscription to the DB
  GET  /subscriptions        — list subscriptions for a user
  DELETE /subscriptions/{id} — delete a subscription
"""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from common.logging_config import setup_logging
setup_logging()
logger = logging.getLogger(__name__)

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session

from common.database import engine, get_db
from common.db_models import Base, PriceCheck, Subscription
from common.exceptions import SubscriptionNotFoundError
from common.queries import get_latest_price_check
from link_parser import fetch_parsed_ticket
from price_checker import check_price
from price_checker.price_checker import SCREENSHOTS_DIR
from schemas import SubscriptionCreate, SubscriptionOut  # noqa: F401

# Create tables on startup if they don't exist yet
Base.metadata.create_all(bind=engine)

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(title="TrackTheTicket", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static mount so the frontend can request final-page screenshots directly
# (`<img src="{API_URL}/screenshots/<file>.jpg">`). Files are pruned by
# the price-checker's retention policy, so the URL may 404 — the frontend
# is expected to handle that gracefully.
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/screenshots", StaticFiles(directory=str(SCREENSHOTS_DIR)), name="screenshots")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _sub_to_dict(sub: Subscription, latest: Optional[PriceCheck] = None) -> dict:
    """
    Map SQLAlchemy Subscription → dict the frontend expects.

    `latest` is the most recent row from `price_checks` for this subscription,
    or None if the subscription has never been checked. We surface its
    timestamp/amount/currency directly on the card, plus a relative URL
    for the screenshot (when the file still exists on disk — see retention
    policy in `price_checker._prune_old_screenshots`).
    """
    last_checked_at: Optional[str] = None
    last_amount: Optional[float] = None
    last_currency: Optional[str] = None
    last_screenshot_url: Optional[str] = None

    if latest is not None:
        last_checked_at = latest.checked_at.isoformat()
        last_amount = float(latest.amount) if latest.amount is not None else None
        last_currency = latest.currency
        if latest.screenshot_path:
            screenshot_name = Path(latest.screenshot_path).name
            if (SCREENSHOTS_DIR / screenshot_name).exists():
                last_screenshot_url = f"/screenshots/{screenshot_name}"

    return {
        "id":                  sub.id,
        "user_id":             sub.user_id,
        "origin_iata":         sub.departure_airport,
        "destination_iata":    sub.arrival_airport,
        "airline":             sub.airline,
        "departure_date":      sub.departure_date,
        "departure_time":      sub.departure_time,
        "flight_number":       sub.flight_number,
        "airline_iata":        sub.airline_iata,
        "need_baggage":        sub.need_baggage,
        "baggage_info":        "with_baggage" if sub.need_baggage else "no_baggage",
        "source_url":          sub.source_url,
        "is_active":           sub.is_active,
        "created_at":          sub.created_at.isoformat(),
        "last_checked_at":     last_checked_at,
        "last_amount":         last_amount,
        "last_currency":       last_currency,
        "last_screenshot_url": last_screenshot_url,
    }


# ── Parse route ───────────────────────────────────────────────────────────────

class ParseRequest(BaseModel):
    source_url: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/parse")
async def parse(req: ParseRequest) -> dict:
    logger.info(f"[parse] → {req.source_url}")
    try:
        ticket = await fetch_parsed_ticket(req.source_url)
    except TimeoutError as exc:
        logger.warning(f"[parse] TIMEOUT — {req.source_url}", exc_info=True)
        raise HTTPException(status_code=504, detail=str(exc))
    except (ValueError, RuntimeError) as exc:
        logger.error(f"[parse] ERROR (422) — {type(exc).__name__}: {exc}", exc_info=True)
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.error(f"[parse] ERROR (500) — {type(exc).__name__}: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal parser error")

    return {
        "origin_iata":      ticket.origin_iata,
        "destination_iata": ticket.destination_iata,
        "departure_date":   ticket.departure_date,
        "departure_time":   ticket.departure_time,
        "flight_number":    ticket.flight_number,
        "airline":          ticket.airline,
        "airline_iata":     ticket.airline_iata,
        "baggage_info":     ticket.baggage_info,
        "is_round_trip":    ticket.is_round_trip,
        "price":            ticket.price,
        "currency":         ticket.currency,
        "passengers":       ticket.passengers,
        "ticket_sign":      ticket.ticket_sign,
    }


# ── Subscriptions routes ──────────────────────────────────────────────────────

@app.post("/subscriptions", status_code=201)
def create_subscription(
    payload: SubscriptionCreate,
    db: Session = Depends(get_db),
) -> dict:
    logger.info(f"[subscriptions] create | {payload.origin_iata}→{payload.destination_iata}")

    sub = Subscription(
        user_id           = "default",
        departure_airport = payload.origin_iata,
        arrival_airport   = payload.destination_iata,
        airline           = payload.airline,
        departure_date    = payload.departure_date,
        need_baggage      = payload.need_baggage,
        source_url        = payload.source_url,
        departure_time    = payload.departure_time,
        flight_number     = payload.flight_number,
        airline_iata      = payload.airline_iata,
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)

    logger.info(f"[subscriptions] saved | id={sub.id}")
    return _sub_to_dict(sub)


@app.get("/subscriptions")
def list_subscriptions(db: Session = Depends(get_db)) -> list[dict]:
    subs = db.query(Subscription).filter(Subscription.user_id == "default").all()
    logger.info(f"[subscriptions] list | count={len(subs)}")
    # N+1 by design — typical user has <20 subs, the readability win
    # (no manual GROUP-BY-on-max-checked_at) is worth the extra queries.
    return [_sub_to_dict(s, get_latest_price_check(db, s.id)) for s in subs]


@app.delete("/subscriptions/{sub_id}")
def delete_subscription(sub_id: int, db: Session = Depends(get_db)) -> dict:
    sub = db.get(Subscription, sub_id)
    if sub is None:
        raise HTTPException(status_code=404, detail=f"Subscription {sub_id} not found")
    db.delete(sub)
    db.commit()
    logger.info(f"[subscriptions] deleted | id={sub_id}")
    return {"ok": True}


@app.post("/subscriptions/{sub_id}/check")
async def check_subscription(sub_id: int) -> dict:
    try:
        await check_price(sub_id)
    except SubscriptionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    # Stub response — frontend reducer expects these fields.
    # Real price will be filled in once price_checker is implemented.
    return {
        "price":         None,
        "currency":      "RUB",
        "flight_number": None,
        "checked_at":    datetime.utcnow().isoformat(),
    }
