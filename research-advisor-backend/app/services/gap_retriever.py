"""Vector search retrieval for gap map entries with taxonomy-aware boosting."""

import logging

from app.config import get_settings
from app.models.schemas import GapMapEntry, NoveltyAssessment, ResearchProfile
from app.services.embedding_service import EmbeddingService
from app.services.gap_map_repository import GapMapRepository

logger = logging.getLogger(__name__)

_TAXONOMY_BOOST_SAME_SUBFIELD = 0.15
_TAXONOMY_BOOST_SAME_FIELD = 0.10
_TAXONOMY_BOOST_SAME_DOMAIN = 0.05


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


def _taxonomy_boost(
    entry: GapMapEntry,
    researcher_domain: str | None,
    researcher_field: str | None,
    researcher_subfield: str | None,
) -> float:
    """Return a boost score (0.0–0.15) based on taxonomy overlap."""
    if researcher_subfield and entry.openalex_subfield == researcher_subfield:
        return _TAXONOMY_BOOST_SAME_SUBFIELD
    if researcher_field and entry.openalex_field == researcher_field:
        return _TAXONOMY_BOOST_SAME_FIELD
    if researcher_domain and entry.openalex_domain == researcher_domain:
        return _TAXONOMY_BOOST_SAME_DOMAIN
    return 0.0


class GapRetriever:
    """Retrieves relevant gap map entries via vector similarity + taxonomy boosting."""

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
        """Retrieve top-k gap map entries by semantic similarity to the research profile.

        Applies taxonomy-aware boosting when researcher classification is available:
        entries in the same subfield/field/domain are ranked higher while still
        allowing cross-domain pivots.

        Falls back to get_all when vector search is disabled or no embeddings exist.
        """
        settings = get_settings()
        top_k = limit or settings.gap_retrieval_top_k

        if not settings.gap_use_vector_search:
            db_entries = await self._repository.get_all()
            entries = [e.to_pydantic() for e in db_entries[:top_k]]
            return self._apply_taxonomy_boost(entries, novelty, top_k)

        query_text = _query_text_from_profile(profile)
        if not query_text.strip():
            db_entries = await self._repository.get_all()
            entries = [e.to_pydantic() for e in db_entries[:top_k]]
            return self._apply_taxonomy_boost(entries, novelty, top_k)

        try:
            query_embedding = await self._embedding_service.embed_text(query_text)
        except Exception:
            logger.warning("Embedding failed, falling back to get_all")
            db_entries = await self._repository.get_all()
            entries = [e.to_pydantic() for e in db_entries[:top_k]]
            return self._apply_taxonomy_boost(entries, novelty, top_k)

        db_entries = await self._repository.get_similar_to_embedding(
            query_embedding, limit=top_k
        )

        if not db_entries:
            db_entries = await self._repository.get_all()

        entries = [e.to_pydantic() for e in db_entries[:top_k]]

        classification = novelty.researcher_classification
        if classification and (classification.primary_field or classification.primary_domain):
            entries = await self._supplement_with_taxonomy(
                entries, classification, top_k
            )

        return self._apply_taxonomy_boost(entries, novelty, top_k)

    async def _supplement_with_taxonomy(
        self,
        entries: list[GapMapEntry],
        classification,
        top_k: int,
    ) -> list[GapMapEntry]:
        """Supplement vector results with taxonomy-matched entries if underrepresented."""
        existing_urls = {e.source_url for e in entries}
        taxonomy_entries = await self._repository.get_by_taxonomy(
            domain=classification.primary_domain,
            field=classification.primary_field,
            subfield=classification.primary_subfield,
            limit=top_k,
        )
        added = 0
        for db_entry in taxonomy_entries:
            pydantic_entry = db_entry.to_pydantic()
            if pydantic_entry.source_url not in existing_urls:
                entries.append(pydantic_entry)
                existing_urls.add(pydantic_entry.source_url)
                added += 1
        if added:
            logger.debug("Supplemented %d taxonomy-matched gap entries", added)
        return entries

    @staticmethod
    def _apply_taxonomy_boost(
        entries: list[GapMapEntry],
        novelty: NoveltyAssessment,
        top_k: int,
    ) -> list[GapMapEntry]:
        """Reorder entries by taxonomy boost (preserving original relative order as tiebreaker)."""
        classification = novelty.researcher_classification
        if not classification or not (classification.primary_field or classification.primary_domain):
            return entries[:top_k]

        scored = []
        for idx, entry in enumerate(entries):
            boost = _taxonomy_boost(
                entry,
                classification.primary_domain,
                classification.primary_field,
                classification.primary_subfield,
            )
            scored.append((-boost, idx, entry))

        scored.sort(key=lambda x: (x[0], x[1]))
        return [e for _, _, e in scored[:top_k]]
