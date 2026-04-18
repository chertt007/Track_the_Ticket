import logging

logger = logging.getLogger(__name__)


def check_price(subscription_id: int) -> None:
    """
    Trigger a price re-check for the given subscription.

    Stub for now: just logs that it was called. Real implementation will
    re-fetch the ticket via link_parser and compare against the previous price.
    """
    logger.info(f"[price_checker] triggered for subscription id={subscription_id}")
