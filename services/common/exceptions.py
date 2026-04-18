"""Domain exceptions shared across services."""


class SubscriptionNotFoundError(Exception):
    """Raised when a subscription is not found in the database."""

    def __init__(self, subscription_id: int) -> None:
        self.subscription_id = subscription_id
        super().__init__(f"Subscription {subscription_id} not found")
