import asyncio
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
from app.schemas.price_history import PriceHistoryOut, ScreenshotOut
from app.schemas.subscription import SubscriptionCreate, SubscriptionOut

SUBSCRIPTION_LIFETIME_DAYS = 14

# Screenshots retention: keep last N days and at most N records per subscription
SCREENSHOT_RETENTION_DAYS = 7
SCREENSHOT_MAX_PER_SUB    = 24


def _send_sqs_message(queue_url: str, message_body: str) -> None:
    """Put a message on SQS. Called via asyncio.to_thread (boto3 is sync)."""
    import boto3
    sqs = boto3.client("sqs", region_name=settings.aws_region)
    sqs.send_message(QueueUrl=queue_url, MessageBody=message_body)


def _upload_screenshot_to_s3(screenshot_b64: str, subscription_id: int, timestamp: str) -> str | None:
    """
    Decode base64 PNG and upload to S3.
    Returns the s3_key on success, or None if upload fails (e.g. no credentials in local dev).
    Called via asyncio.to_thread so it does not block the event loop.
    """
    import base64
    import boto3
    try:
        img_bytes = base64.b64decode(screenshot_b64)
        key = f"screenshots/{subscription_id}/{timestamp}.png"
        boto3.client("s3", region_name=settings.aws_region).put_object(
            Bucket=settings.screenshots_bucket,
            Key=key,
            Body=img_bytes,
            ContentType="image/png",
        )
        return key
    except Exception as exc:
        logger.warning(
            "screenshot S3 upload failed — skipping (local dev or missing credentials)",
            extra={"subscription_id": subscription_id, "error": str(exc)},
        )
        return None


class CheckResult(BaseModel):
    """Returned by POST /subscriptions/{id}/check."""
    queued: bool = False           # True when check was dispatched to SQS (production)
    price: float | None = None     # Populated only in local-dev synchronous mode
    currency: str | None = None
    flight_number: str | None = None
    checked_at: datetime | None = None
    screenshot_b64: str | None = None
    message: str = ""

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
# Returns the last SCREENSHOT_RETENTION_DAYS days worth of screenshots,
# capped at SCREENSHOT_MAX_PER_SUB, newest first.
# Each item includes a presigned S3 URL (valid 1 hour) plus price metadata.

@router.get("/{subscription_id:int}/screenshots", response_model=list[ScreenshotOut])
async def get_screenshots(
    subscription_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ScreenshotOut]:
    await _get_own_subscription(subscription_id, current_user, db)

    cutoff = datetime.utcnow() - timedelta(days=SCREENSHOT_RETENTION_DAYS)
    result = await db.execute(
        select(PriceHistory)
        .where(PriceHistory.subscription_id == subscription_id)
        .where(PriceHistory.s3_key.isnot(None))
        .where(PriceHistory.checked_at >= cutoff)
        .order_by(PriceHistory.checked_at.desc())
        .limit(SCREENSHOT_MAX_PER_SUB)
    )
    records = result.scalars().all()

    if not records:
        logger.debug("screenshots: no records", extra={"subscription_id": subscription_id})
        return []

    try:
        import boto3
        s3 = boto3.client("s3", region_name=settings.aws_region)
        items: list[ScreenshotOut] = []
        for r in records:
            try:
                url = s3.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": settings.screenshots_bucket, "Key": r.s3_key},
                    ExpiresIn=3600,
                )
                items.append(ScreenshotOut(
                    url=url,
                    checked_at=r.checked_at,
                    price=float(r.price),
                    currency=r.currency,
                    status=r.status,
                ))
            except Exception as exc:
                logger.warning(
                    "screenshots: presigned URL failed for record",
                    extra={"record_id": r.id, "s3_key": r.s3_key, "error": str(exc)},
                )
        logger.debug(
            "screenshots: presigned urls generated",
            extra={"subscription_id": subscription_id, "count": len(items)},
        )
        return items
    except Exception as exc:
        logger.warning(
            "screenshots: S3 client init failed — returning empty list",
            extra={"subscription_id": subscription_id, "error": str(exc)},
        )
        return []


# ── POST /subscriptions/{id}/check ────────────────────────────────────────────
# Manual price check trigger.
#
# Production mode (PRICE_CHECKER_QUEUE_URL is set):
#   Puts a message {"subscription_id": N} onto the SQS queue and immediately
#   returns 202. The price-checker Lambda picks it up and saves the result.
#   API Gateway has a hard 29s timeout — the agent takes 60-90s, so we MUST
#   be asynchronous in production.
#
# Local dev mode (PRICE_CHECKER_QUEUE_URL is not set):
#   Runs the browser-use agent synchronously, saves result to DB, and returns
#   the full result including screenshot_b64. Useful for testing without AWS.

@router.post("/{subscription_id:int}/check", response_model=CheckResult)
async def check_subscription_price(
    subscription_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CheckResult:
    sub = await _get_own_subscription(subscription_id, current_user, db)

    if not sub.airline:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Subscription is missing airline name — cannot run price check.",
        )

    queue_url = settings.price_checker_queue_url

    # ── Production: dispatch to SQS ─────────────────────────────────────────
    if queue_url:
        import json
        sqs_message = json.dumps({"subscription_id": subscription_id})
        await asyncio.to_thread(
            _send_sqs_message,
            queue_url,
            sqs_message,
        )
        logger.info(
            "manual price check queued",
            extra={
                "subscription_id": subscription_id,
                "user_id": current_user.id,
                "queue_url": queue_url,
            },
        )
        return CheckResult(
            queued=True,
            message="Price check started. Results will appear in price history within 2 minutes.",
        )

    # ── Local dev: run agent synchronously ──────────────────────────────────
    logger.info(
        "manual price check started (local dev mode — synchronous)",
        extra={
            "subscription_id": subscription_id,
            "user_id": current_user.id,
            "airline": sub.airline,
        },
    )

    with_baggage = sub.baggage_info not in (None, "", "no_baggage")

    from app.price_checker import run_price_check, _is_agent_failure
    result = await run_price_check(
        airline_name=sub.airline,
        airline_iata=sub.airline_iata or "",
        origin_iata=sub.origin_iata,
        destination_iata=sub.destination_iata,
        departure_date=str(sub.departure_date),
        flight_number=sub.flight_number or "",
        with_baggage=with_baggage,
    )

    now = datetime.utcnow()

    if result.price > 0:
        check_status = "ok"
    elif _is_agent_failure(result.raw_output):
        check_status = "agent_error"
    else:
        check_status = "no_price"

    if result.domain_used and not sub.airline_domain:
        sub.airline_domain = result.domain_used

    s3_key: str | None = None
    if result.screenshot_b64:
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        s3_key = await asyncio.to_thread(
            _upload_screenshot_to_s3,
            result.screenshot_b64,
            sub.id,
            timestamp,
        )

    record = PriceHistory(
        subscription_id=sub.id,
        price=Decimal(str(result.price)),
        currency=result.currency,
        s3_key=s3_key,
        status=check_status,
        checked_at=now,
    )
    db.add(record)
    sub.last_checked_at = now
    await db.commit()

    logger.info(
        "manual price check done (local dev)",
        extra={
            "subscription_id": subscription_id,
            "price": result.price,
            "currency": result.currency,
            "check_status": check_status,
        },
    )

    return CheckResult(
        queued=False,
        price=result.price,
        currency=result.currency,
        flight_number=result.flight_number,
        checked_at=now,
        screenshot_b64=result.screenshot_b64,
        message="",
    )
