from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    cognito_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    telegram_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="user")
