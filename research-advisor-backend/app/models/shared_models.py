"""
SQLAlchemy models for shared analysis storage.

Stores completed ResearchRecommendation results for permanent shared links.
"""

from datetime import datetime

from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.models.gap_map_models import Base


class SharedAnalysis(Base):
    """
    Persisted analysis result for permanent shared links.

    When an analysis completes, the recommendation is stored here so that
    shared URLs (e.g. ?session=xyz) continue to work after Redis TTL expires.
    """

    __tablename__ = "shared_analyses"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        comment="Session ID - same as session_id for seamless lookup",
    )
    recommendation = Column(
        JSONB,
        nullable=False,
        comment="Full ResearchRecommendation as JSON",
    )
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="When analysis completed",
    )
