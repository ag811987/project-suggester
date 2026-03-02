"""Add shared_analyses table for permanent shared links

Revision ID: 9d4e5f6a7b8c
Revises: 8c3d2e4f6a7b
Create Date: 2026-03-02

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9d4e5f6a7b8c"
down_revision: str | Sequence[str] | None = "8c3d2e4f6a7b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create shared_analyses table for persisting completed analysis results."""
    op.create_table(
        "shared_analyses",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            comment="Session ID - same as session_id for seamless lookup",
        ),
        sa.Column(
            "recommendation",
            JSONB,
            nullable=False,
            comment="Full ResearchRecommendation as JSON",
        ),
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.now(),
            comment="When analysis completed",
        ),
    )


def downgrade() -> None:
    """Drop shared_analyses table."""
    op.drop_table("shared_analyses")
