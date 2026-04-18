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
import sys
from datetime import datetime

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    stream=sys.stdout,
    force=True,
)
logger = logging.getLogger(__name__)

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from common.database import engine, get_db
from common.db_models import Base, Subscription
from link_parser import fetch_parsed_ticket
from price_checker import check_price
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


# ── Helpers ───────────────────────────────────────────────────────────────────

def _sub_to_dict(sub: Subscription) -> dict:
    """Map SQLAlchemy Subscription → dict the frontend expects."""
    return {
        "id":               sub.id,
        "user_id":          sub.user_id,
        "origin_iata":      sub.departure_airport,
        "destination_iata": sub.arrival_airport,
        "airline":          sub.airline,
        "departure_date":   sub.departure_date,
        "departure_time":   sub.departure_time,
        "flight_number":    sub.flight_number,
        "airline_iata":     sub.airline_iata,
        "need_baggage":     sub.need_baggage,
        "baggage_info":     "with_baggage" if sub.need_baggage else "no_baggage",
        "source_url":       sub.source_url,
        "is_active":        sub.is_active,
        "created_at":       sub.created_at.isoformat(),
        "last_checked_at":  None,
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
    return [_sub_to_dict(s) for s in subs]


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
def check_subscription(sub_id: int, db: Session = Depends(get_db)) -> dict:
    sub = db.get(Subscription, sub_id)
    if sub is None:
        raise HTTPException(status_code=404, detail=f"Subscription {sub_id} not found")

    check_price(sub.id)

    # Stub response — frontend reducer expects these fields.
    # Real price will be filled in once price_checker is implemented.
    return {
        "price":         None,
        "currency":      "RUB",
        "flight_number": sub.flight_number,
        "checked_at":    datetime.utcnow().isoformat(),
    }
