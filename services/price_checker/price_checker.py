import logging

from common.database import SessionLocal
from common.exceptions import SubscriptionNotFoundError
from common.queries import get_airline_url_by_name, get_subscription

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

        airline_url = get_airline_url_by_name(db, airline_name)
        if airline_url is None:
            logger.info(f"[price_checker] airline '{airline_name}' not in airlines table yet")
        else:
            logger.info(f"[price_checker] airline '{airline_name}' → url={airline_url}")

        
