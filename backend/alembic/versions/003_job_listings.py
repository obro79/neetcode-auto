"""job listings and digest logs

Revision ID: 003
Revises: 002
Create Date: 2026-06-09
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "003"
down_revision: str | Sequence[str] | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "job_listings",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("company_name", sa.String(length=256), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("locations", sa.JSON(), nullable=False),
        sa.Column("terms", sa.JSON(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=128), nullable=False),
        sa.Column("date_posted", sa.Integer(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("sponsorship", sa.String(length=64), nullable=True),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_job_listings_company_name", "job_listings", ["company_name"])
    op.create_index("ix_job_listings_category", "job_listings", ["category"])
    op.create_index("ix_job_listings_active", "job_listings", ["active"])

    op.create_table(
        "job_digest_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("digest_date", sa.Date(), nullable=False),
        sa.Column("slot", sa.Integer(), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("resend_id", sa.String(length=64), nullable=True),
        sa.Column("listing_ids", sa.JSON(), nullable=False),
        sa.Column("new_listing_ids", sa.JSON(), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("digest_date", "slot", name="uq_job_digest_date_slot"),
    )
    op.create_index("ix_job_digest_logs_digest_date", "job_digest_logs", ["digest_date"])


def downgrade() -> None:
    op.drop_index("ix_job_digest_logs_digest_date", table_name="job_digest_logs")
    op.drop_table("job_digest_logs")
    op.drop_index("ix_job_listings_active", table_name="job_listings")
    op.drop_index("ix_job_listings_category", table_name="job_listings")
    op.drop_index("ix_job_listings_company_name", table_name="job_listings")
    op.drop_table("job_listings")
