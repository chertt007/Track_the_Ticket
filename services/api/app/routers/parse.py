import asyncio

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import get_current_user
from app.logging_config import get_logger
from app.models.user import User
from app.schemas.parse import ParseRequest, ParseResponse
from app.ticket_parser import parse_ticket

router = APIRouter(prefix="/parse", tags=["parse"])
logger = get_logger(__name__)


# ── POST /parse ───────────────────────────────────────────────────────────────
# Parses an Aviasales URL and returns structured flight data.
# Primary path: URL decode (no browser).
# Fallback: Playwright + network interception.

@router.post("", response_model=ParseResponse)
async def parse_ticket_url(
    body: ParseRequest,
    current_user: User = Depends(get_current_user),
) -> ParseResponse:
    logger.info(
        "[PARSE] request",
        extra={"user_id": current_user.id, "url": body.source_url},
    )
    try:
        result = await asyncio.to_thread(parse_ticket, body.source_url)
        logger.info(
            "[PARSE] success",
            extra={
                "user_id": current_user.id,
                "flight": result.get("flight_number"),
                "route": f"{result.get('origin_iata')}->{result.get('destination_iata')}",
            },
        )
        return ParseResponse(**result)

    except TimeoutError as exc:
        logger.error("[PARSE] timeout", extra={"user_id": current_user.id, "error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Parser timed out waiting for Aviasales API response.",
        )
    except RuntimeError as exc:
        logger.error("[PARSE] runtime error", extra={"user_id": current_user.id, "error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error(
            "[PARSE] unexpected error",
            extra={"user_id": current_user.id, "error_type": type(exc).__name__, "error": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error during parsing.",
        )
