"""Add embedding column for vector search

Revision ID: 7b2c1d3e4f5a
Revises: 6a30bcac59c9
Create Date: 2026-02-11

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "7b2c1d3e4f5a"
down_revision: Union[str, Sequence[str], None] = "6a30bcac59c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add pgvector extension and embedding column with ivfflat index."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute(
        "ALTER TABLE gap_map_entries ADD COLUMN IF NOT EXISTS embedding vector(1536)"
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_gap_map_entries_embedding
        ON gap_map_entries USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
        """
    )


def downgrade() -> None:
    """Remove embedding column and extension."""
    op.execute("DROP INDEX IF EXISTS idx_gap_map_entries_embedding")
    op.execute("ALTER TABLE gap_map_entries DROP COLUMN IF EXISTS embedding")
    op.execute("DROP EXTENSION IF EXISTS vector")
