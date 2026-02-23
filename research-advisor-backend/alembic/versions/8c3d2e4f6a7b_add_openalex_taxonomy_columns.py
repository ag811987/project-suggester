"""Add OpenAlex taxonomy columns for topic hierarchy

Revision ID: 8c3d2e4f6a7b
Revises: 7b2c1d3e4f5a
Create Date: 2026-02-20

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "8c3d2e4f6a7b"
down_revision: Union[str, Sequence[str], None] = "7b2c1d3e4f5a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add OpenAlex topic taxonomy columns (topic, subfield, field, domain)."""
    op.execute(
        "ALTER TABLE gap_map_entries ADD COLUMN IF NOT EXISTS openalex_topic VARCHAR"
    )
    op.execute(
        "ALTER TABLE gap_map_entries ADD COLUMN IF NOT EXISTS openalex_subfield VARCHAR"
    )
    op.execute(
        "ALTER TABLE gap_map_entries ADD COLUMN IF NOT EXISTS openalex_field VARCHAR"
    )
    op.execute(
        "ALTER TABLE gap_map_entries ADD COLUMN IF NOT EXISTS openalex_domain VARCHAR"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_openalex_field ON gap_map_entries (openalex_field)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_openalex_domain ON gap_map_entries (openalex_domain)"
    )


def downgrade() -> None:
    """Remove OpenAlex taxonomy columns."""
    op.execute("DROP INDEX IF EXISTS idx_openalex_domain")
    op.execute("DROP INDEX IF EXISTS idx_openalex_field")
    op.execute("ALTER TABLE gap_map_entries DROP COLUMN IF EXISTS openalex_domain")
    op.execute("ALTER TABLE gap_map_entries DROP COLUMN IF EXISTS openalex_field")
    op.execute("ALTER TABLE gap_map_entries DROP COLUMN IF EXISTS openalex_subfield")
    op.execute("ALTER TABLE gap_map_entries DROP COLUMN IF EXISTS openalex_topic")
