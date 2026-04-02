from datetime import datetime

from pydantic import BaseModel


class PriceHistoryOut(BaseModel):
    id: int
    price: float
    currency: str
    status: str
    s3_key: str | None
    checked_at: datetime

    model_config = {"from_attributes": True}
