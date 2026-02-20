"""Batch embedding pipeline for gap map entries."""

import logging

from app.models.gap_map_models import GapMapEntry as GapMapEntryDB
from app.services.embedding_service import EmbeddingService
from app.services.gap_map_repository import GapMapRepository

logger = logging.getLogger(__name__)

BATCH_SIZE = 100  # Embed in batches to avoid rate limits


def _text_for_embedding(entry: GapMapEntryDB) -> str:
    """Build concatenated text for embedding from title, description, tags."""
    parts = [entry.title or "", entry.description or ""]
    if entry.tags:
        parts.append(" ".join(entry.tags))
    return " ".join(parts).strip() or entry.title or ""


class GapMapEmbedder:
    """Embeds gap map entries and stores vectors in the database."""

    def __init__(
        self,
        embedding_service: EmbeddingService,
        repository: GapMapRepository,
    ):
        self._embedding_service = embedding_service
        self._repository = repository

    async def embed_pending(self, limit: int = 500) -> int:
        """
        Embed entries that have no embedding yet.

        Returns the number of entries embedded.
        """
        entries = await self._repository.get_entries_without_embedding(limit=limit)
        if not entries:
            logger.debug("No entries without embedding")
            return 0
        return await self._embed_entries(entries)

    async def _embed_entries(self, entries: list[GapMapEntryDB]) -> int:
        """Embed a list of entries and update the database."""
        count = 0
        for i in range(0, len(entries), BATCH_SIZE):
            batch = entries[i : i + BATCH_SIZE]
            texts = [_text_for_embedding(e) for e in batch]
            try:
                embeddings = await self._embedding_service.embed_batch(texts)
            except Exception:
                logger.exception("Failed to embed batch of %d entries", len(batch))
                continue
            for entry, emb in zip(batch, embeddings, strict=True):
                await self._repository.update_embedding(entry.id, emb)
                count += 1
            await self._repository.session.commit()
            logger.info("Embedded batch of %d entries (%d total)", len(batch), count)
        return count
