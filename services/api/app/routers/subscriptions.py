from datetime import datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.config import settings
from app.dependencies import get_db
from app.logging_config import get_logger
from app.models.price_history import PriceHistory
from app.models.subscription import Subscription
from app.models.user import User
from app.schemas.price_history import PriceHistoryOut
from app.schemas.subscription import SubscriptionCreate, SubscriptionOut

SUBSCRIPTION_LIFETIME_DAYS = 14

# Mapping from airline IATA code to the domain used for price checking.
# The price-checker agent navigates to this domain to find current prices.
AIRLINE_DOMAIN_MAP: dict[str, str] = {
    "SU": "aeroflot.ru",
    "S7": "s7.ru",
    "U6": "uralairlines.ru",
    "DP": "pobeda.aero",
    "FV": "rossiya-airlines.com",
    "N4": "nordwindairlines.ru",
    "TK": "turkishairlines.com",
    "PC": "flypgs.com",
    "LH": "lufthansa.com",
    "BA": "britishairways.com",
    "EK": "emirates.com",
    "QR": "qatarairways.com",
    "SQ": "singaporeair.com",
    "AF": "airfrance.com",
    "KL": "klm.com",
    "W6": "wizzair.com",
    "FR": "ryanair.com",
    "U2": "easyjet.com",
    "KC": "airastana.com",
    "HY": "uzairways.com",
    "B2": "belavia.by",
    "EY": "etihad.com",
}

# Reverse mapping: airline full name (lowercase) → domain.
# Used as a fallback when airline_iata is not stored on the subscription.
AIRLINE_NAME_DOMAIN_MAP: dict[str, str] = {
    name.lower(): domain
    for iata, domain in AIRLINE_DOMAIN_MAP.items()
    for name in [
        {"SU": "aeroflot", "S7": "s7 airlines", "U6": "ural airlines",
         "DP": "pobeda", "FV": "rossiya airlines", "N4": "nordwind airlines",
         "TK": "turkish airlines", "PC": "pegasus airlines", "LH": "lufthansa",
         "BA": "british airways", "EK": "emirates", "QR": "qatar airways",
         "SQ": "singapore airlines", "AF": "air france", "KL": "klm",
         "W6": "wizz air", "FR": "ryanair", "U2": "easyjet",
         "KC": "air astana", "HY": "uzbekistan airways", "B2": "belavia",
         "EY": "etihad airways"}.get(iata, "")
    ]
    if name
}


class CheckResult(BaseModel):
    price: float
    currency: str
    flight_number: str | None = None
    checked_at: datetime
    screenshot_b64: str | None = None

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])
logger = get_logger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _get_own_subscription(
    subscription_id: int,
    current_user: User,
    db: AsyncSession,
) -> Subscription:
    """Fetch subscription by id and verify it belongs to current user."""
    result = await db.execute(
        select(Subscription).where(Subscription.id == subscription_id)
    )
    subscription = result.scalar_one_or_none()
    if subscription is None or subscription.user_id != current_user.id:
        logger.warning(
            "subscription not found or access denied",
            extra={"subscription_id": subscription_id, "user_id": current_user.id},
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    return subscription


# ── API-05: POST /subscriptions ───────────────────────────────────────────────

@router.post("", response_model=SubscriptionOut, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    body: SubscriptionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Subscription:
    subscription = Subscription(
        user_id=current_user.id,
        source_url=str(body.source_url),
        origin_iata=body.origin_iata,
        destination_iata=body.destination_iata,
        departure_date=body.departure_date,
        departure_time=body.departure_time,
        flight_number=body.flight_number,
        airline=body.airline,
        airline_iata=body.airline_iata,
        airline_domain=body.airline_domain,
        baggage_info=body.baggage_info,
        check_frequency=body.check_frequency,
        status="active",
        expires_at=datetime.utcnow() + timedelta(days=SUBSCRIPTION_LIFETIME_DAYS),
    )
    db.add(subscription)
    await db.commit()
    await db.refresh(subscription)
    logger.info(
        "subscription created",
        extra={
            "subscription_id": subscription.id,
            "user_id": current_user.id,
            "route": f"{body.origin_iata}->{body.destination_iata}",
            "flight": body.flight_number,
        },
    )
    return subscription


# ── API-06: GET /subscriptions ────────────────────────────────────────────────

@router.get("", response_model=list[SubscriptionOut])
async def list_subscriptions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Subscription]:
    result = await db.execute(
        select(Subscription)
        .where(Subscription.user_id == current_user.id)
        .where(Subscription.is_active == True)  # noqa: E712
        .order_by(Subscription.id.desc())
    )
    subscriptions = result.scalars().all()
    logger.debug(
        "subscriptions listed",
        extra={"user_id": current_user.id, "count": len(subscriptions)},
    )
    return subscriptions


# ── API-07: GET /subscriptions/{id} ──────────────────────────────────────────

@router.get("/{subscription_id:int}", response_model=SubscriptionOut)
async def get_subscription(
    subscription_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Subscription:
    return await _get_own_subscription(subscription_id, current_user, db)


# ── API-08: DELETE /subscriptions/{id} ───────────────────────────────────────

@router.delete("/{subscription_id:int}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subscription(
    subscription_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    subscription = await _get_own_subscription(subscription_id, current_user, db)
    subscription.is_active = False  # soft delete — keep data for price history
    await db.commit()
    logger.info(
        "subscription soft-deleted",
        extra={"subscription_id": subscription_id, "user_id": current_user.id},
    )


# ── API-09: GET /subscriptions/{id}/prices ────────────────────────────────────

@router.get("/{subscription_id:int}/prices", response_model=list[PriceHistoryOut])
async def get_price_history(
    subscription_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[PriceHistory]:
    await _get_own_subscription(subscription_id, current_user, db)
    result = await db.execute(
        select(PriceHistory)
        .where(PriceHistory.subscription_id == subscription_id)
        .order_by(PriceHistory.checked_at.desc())
        .limit(100)
    )
    records = result.scalars().all()
    logger.debug(
        "price history fetched",
        extra={"subscription_id": subscription_id, "records": len(records)},
    )
    return records


# ── API-10: GET /subscriptions/{id}/screenshots ───────────────────────────────

@router.get("/{subscription_id:int}/screenshots", response_model=list[str])
async def get_screenshots(
    subscription_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[str]:
    await _get_own_subscription(subscription_id, current_user, db)

    result = await db.execute(
        select(PriceHistory)
        .where(PriceHistory.subscription_id == subscription_id)
        .where(PriceHistory.s3_key.isnot(None))
        .order_by(PriceHistory.checked_at.desc())
        .limit(20)
    )
    records = result.scalars().all()

    import boto3
    s3 = boto3.client("s3", region_name=settings.aws_region)
    urls = [
        s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.screenshots_bucket, "Key": r.s3_key},
            ExpiresIn=3600,
        )
        for r in records
    ]
    logger.debug(
        "screenshots presigned urls generated",
        extra={"subscription_id": subscription_id, "count": len(urls)},
    )
    return urls


# ── POST /subscriptions/{id}/check ────────────────────────────────────────────
# Manual price check trigger. Runs browser-use agent, saves result to DB,
# returns price + screenshot (base64) to the frontend.

@router.post("/{subscription_id:int}/check", response_model=CheckResult)
async def check_subscription_price(
    subscription_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CheckResult:
    from app.price_checker import run_price_check

    sub = await _get_own_subscription(subscription_id, current_user, db)

    # Resolve airline domain: stored → IATA map → name map
    airline_domain = sub.airline_domain
    if not airline_domain and sub.airline_iata:
        airline_domain = AIRLINE_DOMAIN_MAP.get(sub.airline_iata.upper())
        if airline_domain:
            logger.info(
                "airline_domain resolved from IATA mapping",
                extra={"airline_iata": sub.airline_iata, "airline_domain": airline_domain},
            )
    if not airline_domain and sub.airline:
        airline_domain = AIRLINE_NAME_DOMAIN_MAP.get(sub.airline.lower())
        if airline_domain:
            logger.info(
                "airline_domain resolved from name mapping",
                extra={"airline": sub.airline, "airline_domain": airline_domain},
            )

    if not airline_domain:
        logger.error(
            "cannot run price check: airline_domain unknown",
            extra={
                "subscription_id": subscription_id,
                "airline_iata": sub.airline_iata,
                "airline": sub.airline,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Cannot determine airline website for '{sub.airline}' ({sub.airline_iata}). "
                "Please contact support."
            ),
        )

    logger.info(
        "manual price check started",
        extra={"subscription_id": subscription_id, "user_id": current_user.id},
    )

    with_baggage = sub.baggage_info not in (None, "", "no_baggage")

    result = await run_price_check(
        airline_domain=airline_domain,
        origin_iata=sub.origin_iata,
        destination_iata=sub.destination_iata,
        departure_date=str(sub.departure_date),
        flight_number=sub.flight_number or "",
        with_baggage=with_baggage,
    )

    now = datetime.utcnow()

    # Determine record status
    from app.price_checker import _is_agent_failure
    if result.price > 0:
        check_status = "ok"
    elif _is_agent_failure(result.raw_output):
        check_status = "agent_error"
    else:
        check_status = "no_price"

    # Save to price_history (s3_key populated by Lambda; None for manual checks)
    record = PriceHistory(
        subscription_id=sub.id,
        price=Decimal(str(result.price)),
        currency=result.currency,
        s3_key=None,
        status=check_status,
        checked_at=now,
    )
    db.add(record)

    # Update last_checked_at on subscription
    sub.last_checked_at = now
    await db.commit()

    logger.info(
        "manual price check done",
        extra={
            "subscription_id": subscription_id,
            "price": result.price,
            "currency": result.currency,
        },
    )

    return CheckResult(
        price=result.price,
        currency=result.currency,
        flight_number=result.flight_number,
        checked_at=now,
        screenshot_b64=result.screenshot_b64,
    )
