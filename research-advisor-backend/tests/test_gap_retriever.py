"""Tests for GapRetriever vector search + taxonomy-aware boosting."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.gap_retriever import GapRetriever, _taxonomy_boost
from app.models.schemas import (
    GapMapEntry,
    NoveltyAssessment,
    ResearcherClassification,
    ResearchProfile,
)


def _make_gap_entry(**kwargs) -> GapMapEntry:
    """Helper to build a GapMapEntry with defaults."""
    defaults = {
        "title": "Test Gap",
        "description": "desc",
        "source": "convergent",
        "source_url": "https://example.com/gap",
        "category": "Biotech",
        "tags": [],
        "openalex_topic": None,
        "openalex_subfield": None,
        "openalex_field": None,
        "openalex_domain": None,
    }
    defaults.update(kwargs)
    return GapMapEntry(**defaults)


def _make_novelty(**kwargs) -> NoveltyAssessment:
    """Helper to build a NoveltyAssessment with defaults."""
    defaults = {
        "score": 0.5,
        "verdict": "UNCERTAIN",
        "evidence": [],
        "reasoning": "test",
        "related_papers_count": 0,
        "impact_assessment": "UNCERTAIN",
        "impact_reasoning": "test",
        "expected_impact_assessment": "UNCERTAIN",
        "expected_impact_reasoning": "test",
        "researcher_classification": None,
    }
    defaults.update(kwargs)
    return NoveltyAssessment(**defaults)


class TestTaxonomyBoost:
    """Tests for _taxonomy_boost scoring."""

    def test_subfield_match_highest(self):
        entry = _make_gap_entry(openalex_subfield="Genetics", openalex_field="Bio", openalex_domain="Life Sciences")
        boost = _taxonomy_boost(entry, "Life Sciences", "Bio", "Genetics")
        assert boost == pytest.approx(0.15)

    def test_field_match_medium(self):
        entry = _make_gap_entry(openalex_subfield="Ecology", openalex_field="Bio", openalex_domain="Life Sciences")
        boost = _taxonomy_boost(entry, "Life Sciences", "Bio", "Genetics")
        assert boost == pytest.approx(0.10)

    def test_domain_match_lowest(self):
        entry = _make_gap_entry(openalex_subfield="Ecology", openalex_field="Env Sci", openalex_domain="Life Sciences")
        boost = _taxonomy_boost(entry, "Life Sciences", "Bio", "Genetics")
        assert boost == pytest.approx(0.05)

    def test_no_match_zero(self):
        entry = _make_gap_entry(openalex_subfield="Particle Physics", openalex_field="Physics", openalex_domain="Physical Sciences")
        boost = _taxonomy_boost(entry, "Life Sciences", "Bio", "Genetics")
        assert boost == 0.0

    def test_no_researcher_taxonomy(self):
        entry = _make_gap_entry(openalex_field="Bio")
        boost = _taxonomy_boost(entry, None, None, None)
        assert boost == 0.0


class TestGapRetrieverTaxonomyBoosting:
    """Tests for taxonomy-aware boosting in GapRetriever.retrieve()."""

    @pytest.mark.asyncio
    async def test_taxonomy_boost_reorders_entries(self):
        """Entries in researcher's field should be ranked higher."""
        mock_repo = AsyncMock()
        mock_embedding = AsyncMock()

        db_entry_cross = MagicMock()
        db_entry_cross.to_pydantic.return_value = _make_gap_entry(
            title="Cross-field gap",
            source_url="https://example.com/1",
            openalex_field="Physics",
            openalex_domain="Physical Sciences",
        )
        db_entry_same = MagicMock()
        db_entry_same.to_pydantic.return_value = _make_gap_entry(
            title="Same-field gap",
            source_url="https://example.com/2",
            openalex_field="Biology",
            openalex_domain="Life Sciences",
        )

        mock_repo.get_similar_to_embedding = AsyncMock(return_value=[db_entry_cross, db_entry_same])
        mock_repo.get_by_taxonomy = AsyncMock(return_value=[])
        mock_embedding.embed_text = AsyncMock(return_value=[0.0] * 1536)

        retriever = GapRetriever(repository=mock_repo, embedding_service=mock_embedding)

        profile = ResearchProfile(research_question="test biology question")
        novelty = _make_novelty(
            researcher_classification=ResearcherClassification(
                primary_domain="Life Sciences",
                primary_field="Biology",
                primary_subfield="Genetics",
            )
        )

        with patch("app.services.gap_retriever.get_settings") as mock_settings:
            mock_settings.return_value.gap_use_vector_search = True
            mock_settings.return_value.gap_retrieval_top_k = 50
            mock_settings.return_value.openai_api_key = "test-key"
            entries = await retriever.retrieve(profile, novelty)

        assert entries[0].title == "Same-field gap"
        assert entries[1].title == "Cross-field gap"

    @pytest.mark.asyncio
    async def test_no_classification_preserves_order(self):
        """Without researcher classification, original order is preserved."""
        mock_repo = AsyncMock()
        mock_embedding = AsyncMock()

        db_entries = []
        for i in range(3):
            mock_entry = MagicMock()
            mock_entry.to_pydantic.return_value = _make_gap_entry(
                title=f"Gap {i}",
                source_url=f"https://example.com/{i}",
            )
            db_entries.append(mock_entry)

        mock_repo.get_similar_to_embedding = AsyncMock(return_value=db_entries)
        mock_embedding.embed_text = AsyncMock(return_value=[0.0] * 1536)

        retriever = GapRetriever(repository=mock_repo, embedding_service=mock_embedding)

        profile = ResearchProfile(research_question="test question")
        novelty = _make_novelty(researcher_classification=None)

        with patch("app.services.gap_retriever.get_settings") as mock_settings:
            mock_settings.return_value.gap_use_vector_search = True
            mock_settings.return_value.gap_retrieval_top_k = 50
            mock_settings.return_value.openai_api_key = "test-key"
            entries = await retriever.retrieve(profile, novelty)

        assert [e.title for e in entries] == ["Gap 0", "Gap 1", "Gap 2"]

    @pytest.mark.asyncio
    async def test_supplements_with_taxonomy_entries(self):
        """When classification exists, taxonomy entries are supplemented."""
        mock_repo = AsyncMock()
        mock_embedding = AsyncMock()

        db_entry_vec = MagicMock()
        db_entry_vec.to_pydantic.return_value = _make_gap_entry(
            title="Vector match",
            source_url="https://example.com/vec",
        )

        db_entry_tax = MagicMock()
        db_entry_tax.to_pydantic.return_value = _make_gap_entry(
            title="Taxonomy match",
            source_url="https://example.com/tax",
            openalex_field="Biology",
            openalex_domain="Life Sciences",
        )

        mock_repo.get_similar_to_embedding = AsyncMock(return_value=[db_entry_vec])
        mock_repo.get_by_taxonomy = AsyncMock(return_value=[db_entry_tax])
        mock_embedding.embed_text = AsyncMock(return_value=[0.0] * 1536)

        retriever = GapRetriever(repository=mock_repo, embedding_service=mock_embedding)

        profile = ResearchProfile(research_question="biology question")
        novelty = _make_novelty(
            researcher_classification=ResearcherClassification(
                primary_domain="Life Sciences",
                primary_field="Biology",
            )
        )

        with patch("app.services.gap_retriever.get_settings") as mock_settings:
            mock_settings.return_value.gap_use_vector_search = True
            mock_settings.return_value.gap_retrieval_top_k = 50
            mock_settings.return_value.openai_api_key = "test-key"
            entries = await retriever.retrieve(profile, novelty)

        titles = [e.title for e in entries]
        assert "Vector match" in titles
        assert "Taxonomy match" in titles
