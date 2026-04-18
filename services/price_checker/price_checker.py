import logging

from common.database import SessionLocal
from common.exceptions import SubscriptionNotFoundError
from common.queries import get_subscription

logger = logging.getLogger(__name__)


def check_price(subscription_id: int) -> None:
    """
    Trigger a price re-check for the given subscription.

    Stub for now: fetches the subscription from the DB and logs it.
    Real implementation will re-fetch the ticket via link_parser and
    compare against the previous price.

    Raises:
        SubscriptionNotFoundError: if no subscription exists with this id.
    """
    with SessionLocal() as db:
        sub = get_subscription(db, subscription_id)
        if sub is None:
            logger.warning(f"[price_checker] subscription id={subscription_id} not found")
            raise SubscriptionNotFoundError(subscription_id)

        airline_name = sub.airline

        logger.info(
            f"[price_checker] triggered | id={sub.id} "
            f"| {sub.departure_airport}→{sub.arrival_airport} "
            f"| {airline_name} | {sub.departure_date} {sub.departure_time} "
            f"| need_baggage={sub.need_baggage} | source_url={sub.source_url}"
        )
