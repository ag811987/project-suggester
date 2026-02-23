"""
SQLAlchemy database models for the Research Pivot Advisor System.

This module contains the database schema definitions for storing gap map entries.
Uses async SQLAlchemy 2.0+ syntax.
"""

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import ARRAY, Column, DateTime, Index, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class GapMapEntry(Base):
    """
    Database model for storing research gap map entries.

    This table stores gap map data scraped from various sources
    (Convergent, Homeworld, Wikenigma, 3ie, Encyclopedia of World Problems).
    Data is periodically refreshed via background scraping jobs.
    """
    __tablename__ = "gap_map_entries"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Unique identifier for the gap map entry"
    )
    title = Column(
        String,
        nullable=False,
        comment="Title of the research gap or problem"
    )
    description = Column(
        Text,
        nullable=True,
        comment="Detailed description of the gap"
    )
    source = Column(
        String,
        nullable=False,
        comment="Source database: convergent, homeworld, wikenigma, 3ie, encyclopedia"
    )
    source_url = Column(
        String,
        nullable=False,
        comment="URL to the original entry in the source database"
    )
    category = Column(
        String,
        nullable=True,
        comment="Category or domain of the research gap"
    )
    tags = Column(
        ARRAY(String),
        nullable=True,
        comment="Tags or keywords associated with this gap (PostgreSQL array)"
    )
    scraped_at = Column(
        DateTime,
        nullable=False,
        comment="When this entry was last scraped from the source"
    )
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="When this record was first created in our database"
    )
    updated_at = Column(
        DateTime,
        nullable=True,
        onupdate=datetime.utcnow,
        comment="When this record was last updated"
    )
    embedding = Column(
        Vector(1536),
        nullable=True,
        comment="OpenAI text-embedding-3-small vector for semantic search"
    )

    # OpenAlex topic taxonomy (Topic → Subfield → Field → Domain)
    openalex_topic = Column(
        String,
        nullable=True,
        comment="OpenAlex topic classification (most specific, ~4,500 topics)"
    )
    openalex_subfield = Column(
        String,
        nullable=True,
        comment="OpenAlex subfield classification (~250 subfields)"
    )
    openalex_field = Column(
        String,
        nullable=True,
        comment="OpenAlex field classification (~20 fields)"
    )
    openalex_domain = Column(
        String,
        nullable=True,
        comment="OpenAlex domain classification (4 domains)"
    )

    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_source', 'source'),
        Index('idx_category', 'category'),
        Index('idx_scraped_at', 'scraped_at'),
        # Composite index for common query patterns
        Index('idx_source_category', 'source', 'category'),
        # OpenAlex taxonomy indexes
        Index('idx_openalex_field', 'openalex_field'),
        Index('idx_openalex_domain', 'openalex_domain'),
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<GapMapEntry(id={self.id}, title='{self.title[:50]}...', source='{self.source}')>"

    def to_pydantic(self):
        """
        Convert SQLAlchemy model to Pydantic GapMapEntry schema.

        Returns:
            GapMapEntry: Pydantic model instance
        """
        from app.models.schemas import GapMapEntry as GapMapEntrySchema

        return GapMapEntrySchema(
            title=self.title,
            description=self.description or "",
            source=self.source,  # type: ignore
            source_url=self.source_url,
            category=self.category,
            tags=self.tags or [],
            openalex_topic=self.openalex_topic,
            openalex_subfield=self.openalex_subfield,
            openalex_field=self.openalex_field,
            openalex_domain=self.openalex_domain,
        )
