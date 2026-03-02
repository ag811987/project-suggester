"""Repository for shared analysis persistence."""

import json
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shared_models import SharedAnalysis


class SharedAnalysisRepository:
    """Async repository for SharedAnalysis CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert(self, session_id: str, recommendation_json: str) -> None:
        """Insert or replace a shared analysis by session_id."""
        try:
            uid = UUID(session_id)
        except (ValueError, TypeError):
            return
        recommendation_dict = json.loads(recommendation_json)
        stmt = insert(SharedAnalysis).values(
            id=uid,
            recommendation=recommendation_dict,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["id"],
            set_={"recommendation": stmt.excluded.recommendation},
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def get(self, session_id: str) -> str | None:
        """Return recommendation JSON string for session_id, or None if not found."""
        try:
            uid = UUID(session_id)
        except (ValueError, TypeError):
            return None
        stmt = select(SharedAnalysis.recommendation).where(SharedAnalysis.id == uid)
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return json.dumps(row)

    async def delete(self, session_id: str) -> bool:
        """Delete shared analysis by session_id. Returns True if deleted."""
        try:
            uid = UUID(session_id)
        except (ValueError, TypeError):
            return False
        stmt = select(SharedAnalysis).where(SharedAnalysis.id == uid)
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return False
        await self.session.delete(row)
        await self.session.commit()
        return True
