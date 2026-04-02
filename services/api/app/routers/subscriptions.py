from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.dependencies import get_db
from app.models.subscription import Subscription
from app.models.user import User
from app.schemas.subscription import SubscriptionCreate, SubscriptionOut

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


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
    return subscription
