"""core tables: users, analyses, feedback

Blueprint 09 §2.1, §2.4, §2.5, as amended by doc 15 §4 (four tables, not ten)
and doc 10 D-007 (three now; `skill_taxonomy_overrides` deferred with a reason).

Types are chosen so this revision applies unchanged to PostgreSQL and SQLite:
JSON renders as JSONB on PostgreSQL, and primary keys are VARCHAR(36) rather
than native UUID — see `app/db/models.py` for why.

Revision ID: 0001
Revises:
Create Date: 2026-08-01
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

JSONVariant = sa.JSON().with_variant(JSONB, "postgresql")
ID = sa.String(36)


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", ID, primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("first_name", sa.String(100), nullable=True),
        sa.Column("last_name", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
    )
    op.create_index("idx_users_email", "users", ["email"])

    op.create_table(
        "analyses",
        sa.Column("id", ID, primary_key=True),
        sa.Column("user_id", ID, sa.ForeignKey("users.id", ondelete="SET NULL"),
                  nullable=True),
        sa.Column("resume_text", sa.Text(), nullable=False),
        sa.Column("jd_text", sa.Text(), nullable=False),
        sa.Column("recommendation", sa.String(50), nullable=False),
        sa.Column("fit_level", sa.String(50), nullable=False),
        sa.Column("overall_score", sa.Float(), nullable=False),
        sa.Column("shortlist_probability", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("reasoning", sa.Text(), nullable=False, server_default=""),
        sa.Column("semantic_score", sa.Float(), nullable=True),
        sa.Column("skill_overlap_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("gap_penalty", sa.Float(), nullable=False, server_default="0"),
        sa.Column("scoring_explanation", sa.Text(), nullable=False, server_default=""),
        sa.Column("payload", JSONVariant, nullable=False),
        sa.Column("processing_time_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
    )
    op.create_index("idx_analyses_user", "analyses", ["user_id"])
    op.create_index("idx_analyses_score", "analyses", ["overall_score"])
    op.create_index("idx_analyses_user_created", "analyses", ["user_id", "created_at"])

    op.create_table(
        "feedback",
        sa.Column("id", ID, primary_key=True),
        # Nullable + UNIQUE: at most one outcome per analysis, and any number of
        # orphan reports whose analysis is unknown (doc 08 §3.2
        # `decision_found: false`). SQL UNIQUE permits repeated NULLs.
        sa.Column("analysis_id", ID, sa.ForeignKey("analyses.id", ondelete="CASCADE"),
                  nullable=True, unique=True),
        sa.Column("outcome", sa.String(50), nullable=False),
        sa.Column("user_notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("shortlist_probability", sa.Float(), nullable=False, server_default="0"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("recommendation", sa.String(50), nullable=False, server_default=""),
        sa.Column("fit_level", sa.String(50), nullable=False, server_default=""),
        sa.Column("is_processed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
    )
    op.create_index("idx_feedback_outcome", "feedback", ["outcome"])
    op.create_index("idx_feedback_unprocessed", "feedback", ["is_processed"])


def downgrade() -> None:
    op.drop_table("feedback")
    op.drop_table("analyses")
    op.drop_table("users")
