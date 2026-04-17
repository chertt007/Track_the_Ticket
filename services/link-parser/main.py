"""
Link-parser HTTP service.

Endpoints:
  POST /parse   — parse an Aviasales URL, return flight details
  GET  /health  — liveness check
"""
from __future__ import annotations

import logging
import sys

# Configure logging before any other imports so all module loggers inherit this.
# force=True overrides any handlers already set by uvicorn or third-party libs.
# stream=sys.stdout ensures honcho picks up the output.
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    stream=sys.stdout,
    force=True,
)
logger = logging.getLogger(__name__)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from flight_parser import fetch_parsed_ticket

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(title="TrackTheTicket — Link Parser", version="1.0.0")

# Allow requests from the frontend dev server and production origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Schemas ───────────────────────────────────────────────────────────────────

class ParseRequest(BaseModel):
    source_url: str


# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/parse")
async def parse(req: ParseRequest) -> dict:
    """
    Parse an Aviasales search URL and return extracted flight details.
    Launches headless Chromium, intercepts the tickets-api response,
    and returns structured ticket data.
    """
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
        "origin_iata": ticket.origin_iata,
        "destination_iata": ticket.destination_iata,
        "departure_date": ticket.departure_date,
        "departure_time": ticket.departure_time,
        "flight_number": ticket.flight_number,
        "airline": ticket.airline,
        "airline_iata": ticket.airline_iata,
        "baggage_info": ticket.baggage_info,
        "is_round_trip": ticket.is_round_trip,
        "price": ticket.price,
        "currency": ticket.currency,
        "passengers": ticket.passengers,
        "ticket_sign": ticket.ticket_sign,
    }
