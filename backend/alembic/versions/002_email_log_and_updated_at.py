"""email log success fields and user_progress updated_at

Revision ID: 002
Revises: 001
Create Date: 2026-06-07
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "002"
down_revision: str | Sequence[str] | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "email_log",
        sa.Column("success", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "email_log",
        sa.Column("resend_id", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "user_progress",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("user_progress", "updated_at")
    op.drop_column("email_log", "resend_id")
    op.drop_column("email_log", "success")
