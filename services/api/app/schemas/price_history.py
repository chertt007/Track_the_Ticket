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


class ScreenshotOut(BaseModel):
    """One screenshot entry returned to the frontend, with presigned S3 URL and metadata."""
    url: str
    checked_at: datetime
    price: float
    currency: str
    status: str
