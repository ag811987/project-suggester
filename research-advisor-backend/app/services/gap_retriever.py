"""Vector search retrieval for gap map entries."""

import logging

from app.config import get_settings
from app.models.schemas import GapMapEntry, NoveltyAssessment, ResearchProfile
from app.services.embedding_service import EmbeddingService
from app.services.gap_map_repository import GapMapRepository

logger = logging.getLogger(__name__)


def _query_text_from_profile(profile: ResearchProfile) -> str:
    """Build query text from research profile for embedding."""
    parts = [profile.research_question or ""]
    if profile.skills:
        parts.append(" ".join(profile.skills))
    if profile.expertise_areas:
        parts.append(" ".join(profile.expertise_areas))
    if profile.motivations:
        parts.append(" ".join(profile.motivations))
    return " ".join(parts).strip() or profile.research_question or ""


class GapRetriever:
    """Retrieves relevant gap map entries via vector similarity search."""

    def __init__(
        self,
        repository: GapMapRepository,
        embedding_service: EmbeddingService | None = None,
    ):
        self._repository = repository
        self._embedding_service = embedding_service or EmbeddingService(
            api_key=get_settings().openai_api_key
        )

    async def retrieve(
        self,
        profile: ResearchProfile,
        novelty: NoveltyAssessment,
        limit: int | None = None,
    ) -> list[GapMapEntry]:
        """
        Retrieve top-k gap map entries by semantic similarity to the research profile.

        Falls back to get_all when vector search is disabled or no embeddings exist.
        """
        settings = get_settings()
        top_k = limit or settings.gap_retrieval_top_k

        if not settings.gap_use_vector_search:
            db_entries = await self._repository.get_all()
            return [e.to_pydantic() for e in db_entries[:top_k]]

        query_text = _query_text_from_profile(profile)
        if not query_text.strip():
            db_entries = await self._repository.get_all()
            return [e.to_pydantic() for e in db_entries[:top_k]]

        try:
            query_embedding = await self._embedding_service.embed_text(query_text)
        except Exception:
            logger.warning("Embedding failed, falling back to get_all")
            db_entries = await self._repository.get_all()
            return [e.to_pydantic() for e in db_entries[:top_k]]

        db_entries = await self._repository.get_similar_to_embedding(
            query_embedding, limit=top_k
        )
        if not db_entries:
            db_entries = await self._repository.get_all()
            return [e.to_pydantic() for e in db_entries[:top_k]]

        return [e.to_pydantic() for e in db_entries]
