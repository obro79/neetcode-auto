"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-06-07
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    difficulty = sa.Enum("easy", "medium", "hard", name="difficulty")
    review_stage = sa.Enum("new", "1d", "3d", "7d", "14d", "30d", "mastered", name="review_stage")
    confidence = sa.Enum("struggling", "getting_there", "solid", name="confidence")
    daily_slot = sa.Enum("review", "focused_new", "random_new", "done", name="daily_slot")
    daily_slot_item = sa.Enum("review", "focused_new", "random_new", "done", name="daily_slot_item")

    op.create_table(
        "problems",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(length=128), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("pattern", sa.String(length=128), nullable=False),
        sa.Column("difficulty", difficulty, nullable=False),
        sa.Column("leetcode_url", sa.Text(), nullable=False),
        sa.Column("neetcode_url", sa.Text(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.UniqueConstraint("slug", name="uq_problems_slug"),
    )
    op.create_index("ix_problems_slug", "problems", ["slug"])
    op.create_index("ix_problems_pattern", "problems", ["pattern"])
    op.create_index("ix_problems_sort_order", "problems", ["sort_order"])

    op.create_table(
        "user_progress",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("problem_id", sa.Integer(), sa.ForeignKey("problems.id"), nullable=False),
        sa.Column("solved", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("review_stage", review_stage, nullable=False, server_default="new"),
        sa.Column("next_review", sa.Date(), nullable=True),
        sa.Column("last_practiced", sa.Date(), nullable=True),
        sa.Column("confidence", confidence, nullable=True),
        sa.Column("daily_slot", daily_slot, nullable=True),
        sa.UniqueConstraint("problem_id", name="uq_user_progress_problem"),
    )
    op.create_index("ix_user_progress_problem_id", "user_progress", ["problem_id"])

    op.create_table(
        "daily_sets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("set_date", sa.Date(), nullable=False),
        sa.Column("focus_pattern", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("set_date", name="uq_daily_sets_set_date"),
    )
    op.create_index("ix_daily_sets_set_date", "daily_sets", ["set_date"])

    op.create_table(
        "daily_set_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("daily_set_id", sa.Integer(), sa.ForeignKey("daily_sets.id"), nullable=False),
        sa.Column("problem_id", sa.Integer(), sa.ForeignKey("problems.id"), nullable=False),
        sa.Column("slot", daily_slot_item, nullable=False),
        sa.UniqueConstraint("daily_set_id", "problem_id", name="uq_daily_set_problem"),
    )
    op.create_index("ix_daily_set_items_daily_set_id", "daily_set_items", ["daily_set_id"])
    op.create_index("ix_daily_set_items_problem_id", "daily_set_items", ["problem_id"])

    op.create_table(
        "email_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("set_date", sa.Date(), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempt", sa.Integer(), nullable=False),
        sa.UniqueConstraint("set_date", "attempt", name="uq_email_log_set_date_attempt"),
    )
    op.create_index("ix_email_log_set_date", "email_log", ["set_date"])


def downgrade() -> None:
    op.drop_table("email_log")
    op.drop_table("daily_set_items")
    op.drop_table("daily_sets")
    op.drop_table("user_progress")
    op.drop_table("problems")

    sa.Enum(name="daily_slot_item").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="daily_slot").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="confidence").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="review_stage").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="difficulty").drop(op.get_bind(), checkfirst=True)
