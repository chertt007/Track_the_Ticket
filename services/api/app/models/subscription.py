from datetime import date, datetime, time

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    strategy_id: Mapped[int | None] = mapped_column(ForeignKey("search_strategies.id"), nullable=True)

    flight_number: Mapped[str | None] = mapped_column(String(16), nullable=True)
    airline: Mapped[str | None] = mapped_column(String(128), nullable=True)
    origin_iata: Mapped[str] = mapped_column(String(3), nullable=False)
    destination_iata: Mapped[str] = mapped_column(String(3), nullable=False)
    departure_date: Mapped[date] = mapped_column(Date, nullable=False)
    departure_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    baggage_info: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)

    # pending → agent is processing the URL
    # active  → flight found, strategy ready, price checks running
    # failed  → link-parser or strategy-agent could not process the URL
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    check_frequency: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    last_checked_at: Mapped[datetime | None] = mapped_column(nullable=True)
    last_notified_at: Mapped[datetime | None] = mapped_column(nullable=True)

    user: Mapped["User"] = relationship(back_populates="subscriptions")
    strategy: Mapped["SearchStrategy | None"] = relationship(back_populates="subscriptions")
    price_history: Mapped[list["PriceHistory"]] = relationship(back_populates="subscription")
