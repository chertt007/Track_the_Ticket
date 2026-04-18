import logging

from agents.airline_url_finder import find_airline_url_online
from common.database import SessionLocal
from common.exceptions import SubscriptionNotFoundError
from common.queries import get_airline_url_by_name, get_subscription, save_airline

logger = logging.getLogger(__name__)


async def check_price(subscription_id: int) -> None:
    """
    Trigger a price re-check for the given subscription.

    Stub for now: fetches the subscription from the DB, ensures we know the
    airline's website URL (calling the url-finder agent if not), and logs.
    Real price re-fetching will be wired in later.

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
            logger.info(f"[price_checker] airline '{airline_name}' not in table — calling agent")
            airline_url = await find_airline_url_online(airline_name)
            if airline_url:
                save_airline(db, airline_name, airline_url)
                logger.info(f"[price_checker] saved '{airline_name}' → {airline_url}")
            else:
                logger.warning(f"[price_checker] agent did not return a URL for '{airline_name}'")
        else:
            logger.info(f"[price_checker] airline '{airline_name}' → url={airline_url}")

        
