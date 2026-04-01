from sqlalchemy import Float, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SearchStrategy(Base):
    __tablename__ = "search_strategies"

    id: Mapped[int] = mapped_column(primary_key=True)
    airline_name: Mapped[str] = mapped_column(String(128), nullable=False)
    airline_domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    strategy_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    success_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="strategy")
