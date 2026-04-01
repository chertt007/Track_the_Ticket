"""initial

Revision ID: 001
Revises:
Create Date: 2026-04-01
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cognito_id", sa.String(128), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("telegram_id", sa.String(64), nullable=True),
    )
    op.create_index("ix_users_cognito_id", "users", ["cognito_id"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "search_strategies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("airline_name", sa.String(128), nullable=False),
        sa.Column("airline_domain", sa.String(255), nullable=False),
        sa.Column("strategy_json", JSONB(), nullable=False),
        sa.Column("success_rate", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_search_strategies_airline_domain", "search_strategies", ["airline_domain"])

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("strategy_id", sa.Integer(), sa.ForeignKey("search_strategies.id"), nullable=True),
        sa.Column("flight_number", sa.String(16), nullable=True),
        sa.Column("airline", sa.String(128), nullable=True),
        sa.Column("origin_iata", sa.String(3), nullable=False),
        sa.Column("destination_iata", sa.String(3), nullable=False),
        sa.Column("departure_date", sa.Date(), nullable=False),
        sa.Column("departure_time", sa.Time(), nullable=True),
        sa.Column("baggage_info", sa.Text(), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("check_frequency", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_notified_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_subscriptions_user_id", "subscriptions", ["user_id"])

    op.create_table(
        "price_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("subscription_id", sa.Integer(), sa.ForeignKey("subscriptions.id"), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="RUB"),
        sa.Column("s3_key", sa.String(512), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="ok"),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_price_history_subscription_id", "price_history", ["subscription_id"])


def downgrade() -> None:
    op.drop_table("price_history")
    op.drop_table("subscriptions")
    op.drop_table("search_strategies")
    op.drop_table("users")
