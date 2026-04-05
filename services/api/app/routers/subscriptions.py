from fastapi import APIRouter, Depends, HTTPException, status
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
    # Create subscription in pending state.
    # Link-parser + strategy-agent will fill in flight details asynchronously.
    subscription = Subscription(
        user_id=current_user.id,
        source_url=str(body.source_url),
        check_frequency=body.check_frequency,
        status="pending",
    )
    db.add(subscription)
    await db.commit()
    await db.refresh(subscription)
    logger.info(
        "subscription created",
        extra={
            "subscription_id": subscription.id,
            "user_id": current_user.id,
            "source_url": str(body.source_url),
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
