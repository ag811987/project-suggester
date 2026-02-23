"""Repository for gap map database operations."""

from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.gap_map_models import GapMapEntry as GapMapEntryDB
from app.models.schemas import GapMapEntry as GapMapEntrySchema


class GapMapRepository:
    """Async repository for GapMapEntry CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert(self, entries: list[GapMapEntrySchema]) -> int:
        """Insert new entries or update existing ones (matched by source_url).

        Returns the number of entries processed.
        """
        now = datetime.utcnow()
        count = 0

        for entry in entries:
            # Check if entry already exists by source_url
            stmt = select(GapMapEntryDB).where(
                GapMapEntryDB.source_url == entry.source_url
            )
            result = await self.session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                existing.title = entry.title
                existing.description = entry.description
                existing.source = entry.source
                existing.category = entry.category
                existing.tags = entry.tags
                existing.scraped_at = now
                existing.embedding = None  # Re-embed after content change
            else:
                db_entry = GapMapEntryDB(
                    title=entry.title,
                    description=entry.description,
                    source=entry.source,
                    source_url=entry.source_url,
                    category=entry.category,
                    tags=entry.tags,
                    scraped_at=now,
                    created_at=now,
                )
                self.session.add(db_entry)

            count += 1

        await self.session.commit()
        return count

    async def get_all(self) -> list[GapMapEntryDB]:
        """Return all gap map entries."""
        stmt = select(GapMapEntryDB)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_entries_without_embedding(self, limit: int = 500) -> list[GapMapEntryDB]:
        """Return gap map entries that have no embedding yet."""
        stmt = (
            select(GapMapEntryDB)
            .where(GapMapEntryDB.embedding.is_(None))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_embedding(self, entry_id: int, embedding: list[float]) -> None:
        """Update a single entry's embedding."""
        stmt = (
            update(GapMapEntryDB)
            .where(GapMapEntryDB.id == entry_id)
            .values(embedding=embedding)
        )
        await self.session.execute(stmt)

    async def get_by_category(self, category: str) -> list[GapMapEntryDB]:
        """Return gap map entries filtered by category."""
        stmt = select(GapMapEntryDB).where(GapMapEntryDB.category == category)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_source(self, source: str) -> list[GapMapEntryDB]:
        """Return gap map entries filtered by source."""
        stmt = select(GapMapEntryDB).where(GapMapEntryDB.source == source)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_similar_to_embedding(
        self, query_embedding: list[float], limit: int = 50
    ) -> list[GapMapEntryDB]:
        """Return gap map entries ordered by cosine similarity to query embedding."""
        stmt = (
            select(GapMapEntryDB)
            .where(GapMapEntryDB.embedding.isnot(None))
            .order_by(GapMapEntryDB.embedding.cosine_distance(query_embedding))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_entries_without_taxonomy(self, limit: int = 500) -> list[GapMapEntryDB]:
        """Return gap map entries that have no OpenAlex taxonomy yet."""
        stmt = (
            select(GapMapEntryDB)
            .where(GapMapEntryDB.openalex_topic.is_(None))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_taxonomy(
        self,
        entry_id: int,
        taxonomy: dict,
    ) -> None:
        """Update a single entry's OpenAlex taxonomy fields."""
        stmt = (
            update(GapMapEntryDB)
            .where(GapMapEntryDB.id == entry_id)
            .values(
                openalex_topic=taxonomy.get("topic"),
                openalex_subfield=taxonomy.get("subfield"),
                openalex_field=taxonomy.get("field"),
                openalex_domain=taxonomy.get("domain"),
            )
        )
        await self.session.execute(stmt)
