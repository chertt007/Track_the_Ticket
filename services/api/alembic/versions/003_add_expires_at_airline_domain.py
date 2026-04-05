"""add expires_at and airline_domain to subscriptions

Revision ID: 003
Revises: 002
Create Date: 2026-04-05
"""

from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "subscriptions",
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "subscriptions",
        sa.Column("airline_domain", sa.String(255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("subscriptions", "expires_at")
    op.drop_column("subscriptions", "airline_domain")
