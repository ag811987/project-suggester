"""Tests for Novelty & Impact Analyzer."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.novelty_analyzer import (
    NoveltyAnalyzer,
    _merge_papers,
    _merge_multiquery_results,
)
from app.models.schemas import NoveltyAssessment, ResearchDecomposition


@pytest.fixture
def analyzer():
    """Create a NoveltyAnalyzer instance for testing.

    Uses legacy FWCI thresholds (1.5, 0.8) to match test expectations.
    Production defaults are stricter (2.2, 1.2); see docs/FWCI_CALIBRATION.md.
    """
    return NoveltyAnalyzer(
        openalex_email="test@example.com",
        openai_api_key="test-key",
        fwci_high_threshold=1.5,
        fwci_low_threshold=0.8,
        search_limit=25,  # tests expect 25 papers from mock
    )


@pytest.fixture
def high_fwci_papers():
    """Papers with high FWCI (avg > 1.5) — indicates HIGH impact."""
    return [
        {
            "id": "https://openalex.org/W1001",
            "title": "High Impact Paper 1",
            "doi": "10.1234/high1",
            "fwci": 3.0,
            "citation_normalized_percentile": 0.95,
            "cited_by_percentile_year_min": 90,
            "cited_by_percentile_year_max": 99,
            "authors": ["Author A"],
            "publication_year": 2023,
            "cited_by_count": 200,
        },
        {
            "id": "https://openalex.org/W1002",
            "title": "High Impact Paper 2",
            "doi": "10.1234/high2",
            "fwci": 2.0,
            "citation_normalized_percentile": 0.88,
            "cited_by_percentile_year_min": 85,
            "cited_by_percentile_year_max": 92,
            "authors": ["Author B"],
            "publication_year": 2023,
            "cited_by_count": 150,
        },
    ]


@pytest.fixture
def medium_fwci_papers():
    """Papers with medium FWCI (0.8–1.5) — indicates MEDIUM impact."""
    return [
        {
            "title": "Medium Impact Paper 1",
            "doi": "10.1234/med1",
            "fwci": 1.2,
            "citation_normalized_percentile": 0.65,
            "cited_by_percentile_year_min": 55,
            "cited_by_percentile_year_max": 70,
            "authors": ["Author C"],
            "publication_year": 2023,
            "cited_by_count": 60,
        },
        {
            "title": "Medium Impact Paper 2",
            "doi": "10.1234/med2",
            "fwci": 1.0,
            "citation_normalized_percentile": 0.55,
            "cited_by_percentile_year_min": 45,
            "cited_by_percentile_year_max": 60,
            "authors": ["Author D"],
            "publication_year": 2022,
            "cited_by_count": 40,
        },
    ]


@pytest.fixture
def low_fwci_papers():
    """Papers with low FWCI (< 0.8) — indicates LOW impact."""
    return [
        {
            "title": "Low Impact Paper 1",
            "doi": "10.1234/low1",
            "fwci": 0.3,
            "citation_normalized_percentile": 0.2,
            "cited_by_percentile_year_min": 10,
            "cited_by_percentile_year_max": 25,
            "authors": ["Author E"],
            "publication_year": 2023,
            "cited_by_count": 5,
        },
        {
            "title": "Low Impact Paper 2",
            "doi": "10.1234/low2",
            "fwci": 0.5,
            "citation_normalized_percentile": 0.3,
            "cited_by_percentile_year_min": 20,
            "cited_by_percentile_year_max": 35,
            "authors": ["Author F"],
            "publication_year": 2022,
            "cited_by_count": 10,
        },
    ]


@pytest.fixture
def none_fwci_papers():
    """Papers with None FWCI values."""
    return [
        {
            "title": "No FWCI Paper",
            "doi": "10.1234/none",
            "fwci": None,
            "citation_normalized_percentile": None,
            "cited_by_percentile_year_min": None,
            "cited_by_percentile_year_max": None,
            "authors": [],
            "publication_year": 2024,
            "cited_by_count": 0,
        },
    ]


def _mock_llm_response(verdict: str, score: float, reasoning: str):
    """Helper to create a mock LLM response for novelty analysis."""
    return {
        "verdict": verdict,
        "score": score,
        "reasoning": reasoning,
    }


def _mock_expected_impact(level: str = "MEDIUM", reasoning: str = "Moderate expected impact."):
    """Helper to create a mock expected impact response."""
    return (level, reasoning)


def _mock_decomposition():
    """Helper to create a mock ResearchDecomposition."""
    return ResearchDecomposition(
        core_questions=["What is the research question?"],
        core_motivations=["Understanding"],
        potential_impact_domains=["Science"],
        key_concepts=["research"],
    )


class TestImpactAssessment:
    """Tests for impact assessment based on FWCI thresholds."""

    def test_high_impact_from_high_fwci(self, analyzer):
        avg_fwci = 2.5  # > 1.5
        impact = analyzer._determine_impact_level(avg_fwci)
        assert impact == "HIGH"

    def test_medium_impact_from_medium_fwci(self, analyzer):
        avg_fwci = 1.1  # 0.8–1.5
        impact = analyzer._determine_impact_level(avg_fwci)
        assert impact == "MEDIUM"

    def test_low_impact_from_low_fwci(self, analyzer):
        avg_fwci = 0.4  # < 0.8
        impact = analyzer._determine_impact_level(avg_fwci)
        assert impact == "LOW"

    def test_uncertain_impact_when_none_fwci(self, analyzer):
        impact = analyzer._determine_impact_level(None)
        assert impact == "UNCERTAIN"

    def test_boundary_high_medium(self, analyzer):
        # 1.5 is the threshold — exactly 1.5 should be MEDIUM
        impact = analyzer._determine_impact_level(1.5)
        assert impact == "MEDIUM"

    def test_boundary_medium_low(self, analyzer):
        # 0.8 is the threshold — exactly 0.8 should be MEDIUM
        impact = analyzer._determine_impact_level(0.8)
        assert impact == "MEDIUM"

    def test_just_above_high_threshold(self, analyzer):
        impact = analyzer._determine_impact_level(1.51)
        assert impact == "HIGH"

    def test_just_below_low_threshold(self, analyzer):
        impact = analyzer._determine_impact_level(0.79)
        assert impact == "LOW"


class TestNoveltyVerdict:
    """Tests for novelty verdict determination logic."""

    @pytest.mark.asyncio
    async def test_novel_verdict(self, analyzer, high_fwci_papers):
        llm_response = _mock_llm_response(
            "NOVEL", 0.8, "This is a genuinely novel research direction."
        )

        with patch.object(
            analyzer, "_decompose_research", new_callable=AsyncMock
        ) as mock_decompose, patch.object(
            analyzer, "_search_papers", new_callable=AsyncMock
        ) as mock_search, patch.object(
            analyzer, "_get_llm_verdict", new_callable=AsyncMock
        ) as mock_llm, patch.object(
            analyzer, "_assess_impact_llm", new_callable=AsyncMock
        ) as mock_impact_llm, patch.object(
            analyzer, "_assess_expected_impact", new_callable=AsyncMock
        ) as mock_impact:
            mock_decompose.return_value = _mock_decomposition()
            mock_search.return_value = high_fwci_papers
            mock_llm.return_value = llm_response
            mock_impact_llm.return_value = ("HIGH", "High impact field.")
            mock_impact.return_value = _mock_expected_impact("HIGH")

            result = await analyzer.analyze("novel quantum computing approach")

        assert isinstance(result, NoveltyAssessment)
        assert result.verdict == "NOVEL"
        assert result.score == 0.8

    @pytest.mark.asyncio
    async def test_solved_verdict(self, analyzer, high_fwci_papers):
        llm_response = _mock_llm_response(
            "SOLVED", 0.1, "This problem has been extensively studied and solved."
        )

        with patch.object(
            analyzer, "_decompose_research", new_callable=AsyncMock
        ) as mock_decompose, patch.object(
            analyzer, "_search_papers", new_callable=AsyncMock
        ) as mock_search, patch.object(
            analyzer, "_get_llm_verdict", new_callable=AsyncMock
        ) as mock_llm, patch.object(
            analyzer, "_assess_impact_llm", new_callable=AsyncMock
        ) as mock_impact_llm, patch.object(
            analyzer, "_assess_expected_impact", new_callable=AsyncMock
        ) as mock_impact:
            mock_decompose.return_value = _mock_decomposition()
            mock_search.return_value = high_fwci_papers
            mock_llm.return_value = llm_response
            mock_impact_llm.return_value = ("HIGH", "High impact.")
            mock_impact.return_value = _mock_expected_impact("LOW")

            result = await analyzer.analyze("well known solved problem")

        assert result.verdict == "SOLVED"
        assert result.score == 0.1

    @pytest.mark.asyncio
    async def test_marginal_verdict(self, analyzer, medium_fwci_papers):
        llm_response = _mock_llm_response(
            "MARGINAL", 0.4, "Some novelty but largely explored territory."
        )

        with patch.object(
            analyzer, "_decompose_research", new_callable=AsyncMock
        ) as mock_decompose, patch.object(
            analyzer, "_search_papers", new_callable=AsyncMock
        ) as mock_search, patch.object(
            analyzer, "_get_llm_verdict", new_callable=AsyncMock
        ) as mock_llm, patch.object(
            analyzer, "_assess_impact_llm", new_callable=AsyncMock
        ) as mock_impact_llm, patch.object(
            analyzer, "_assess_expected_impact", new_callable=AsyncMock
        ) as mock_impact:
            mock_decompose.return_value = _mock_decomposition()
            mock_search.return_value = medium_fwci_papers
            mock_llm.return_value = llm_response
            mock_impact_llm.return_value = ("MEDIUM", "Medium impact.")
            mock_impact.return_value = _mock_expected_impact("LOW")

            result = await analyzer.analyze("incremental improvement")

        assert result.verdict == "MARGINAL"
        assert result.score == 0.4

    @pytest.mark.asyncio
    async def test_uncertain_verdict_on_api_failure(self, analyzer):
        """When OpenAlex fails, verdict should be UNCERTAIN."""
        with patch.object(
            analyzer, "_decompose_research", new_callable=AsyncMock
        ) as mock_decompose, patch.object(
            analyzer, "_search_papers", new_callable=AsyncMock
        ) as mock_search:
            mock_decompose.return_value = _mock_decomposition()
            mock_search.return_value = []

            result = await analyzer.analyze("some research question")

        assert result.verdict == "UNCERTAIN"
        assert result.impact_assessment == "UNCERTAIN"
        assert result.expected_impact_assessment == "UNCERTAIN"


class TestFWCIIntegration:
    """Tests that FWCI values flow correctly into NoveltyAssessment."""

    @pytest.mark.asyncio
    async def test_high_fwci_papers_stats(self, analyzer, high_fwci_papers):
        llm_response = _mock_llm_response("NOVEL", 0.8, "Novel research area.")

        with patch.object(
            analyzer, "_decompose_research", new_callable=AsyncMock
        ) as mock_decompose, patch.object(
            analyzer, "_search_papers", new_callable=AsyncMock
        ) as mock_search, patch.object(
            analyzer, "_get_llm_verdict", new_callable=AsyncMock
        ) as mock_llm, patch.object(
            analyzer, "_assess_impact_llm", new_callable=AsyncMock
        ) as mock_impact_llm, patch.object(
            analyzer, "_assess_expected_impact", new_callable=AsyncMock
        ) as mock_impact:
            mock_decompose.return_value = _mock_decomposition()
            mock_search.return_value = high_fwci_papers
            mock_llm.return_value = llm_response
            mock_impact_llm.return_value = ("HIGH", "High impact.")
            mock_impact.return_value = _mock_expected_impact("HIGH")

            result = await analyzer.analyze("quantum computing")

        assert result.average_fwci == pytest.approx(2.5, abs=0.01)
        assert result.impact_assessment == "HIGH"
        assert result.related_papers_count == 2

    @pytest.mark.asyncio
    async def test_medium_fwci_papers_stats(self, analyzer, medium_fwci_papers):
        llm_response = _mock_llm_response("MARGINAL", 0.4, "Moderate area.")

        with patch.object(
            analyzer, "_decompose_research", new_callable=AsyncMock
        ) as mock_decompose, patch.object(
            analyzer, "_search_papers", new_callable=AsyncMock
        ) as mock_search, patch.object(
            analyzer, "_get_llm_verdict", new_callable=AsyncMock
        ) as mock_llm, patch.object(
            analyzer, "_assess_impact_llm", new_callable=AsyncMock
        ) as mock_impact_llm, patch.object(
            analyzer, "_assess_expected_impact", new_callable=AsyncMock
        ) as mock_impact:
            mock_decompose.return_value = _mock_decomposition()
            mock_search.return_value = medium_fwci_papers
            mock_llm.return_value = llm_response
            mock_impact_llm.return_value = ("MEDIUM", "Medium impact.")
            mock_impact.return_value = _mock_expected_impact("MEDIUM")

            result = await analyzer.analyze("some topic")

        assert result.average_fwci == pytest.approx(1.1, abs=0.01)
        assert result.impact_assessment == "MEDIUM"

    @pytest.mark.asyncio
    async def test_low_fwci_papers_stats(self, analyzer, low_fwci_papers):
        llm_response = _mock_llm_response("MARGINAL", 0.3, "Low impact area.")

        with patch.object(
            analyzer, "_decompose_research", new_callable=AsyncMock
        ) as mock_decompose, patch.object(
            analyzer, "_search_papers", new_callable=AsyncMock
        ) as mock_search, patch.object(
            analyzer, "_get_llm_verdict", new_callable=AsyncMock
        ) as mock_llm, patch.object(
            analyzer, "_assess_impact_llm", new_callable=AsyncMock
        ) as mock_impact_llm, patch.object(
            analyzer, "_assess_expected_impact", new_callable=AsyncMock
        ) as mock_impact:
            mock_decompose.return_value = _mock_decomposition()
            mock_search.return_value = low_fwci_papers
            mock_llm.return_value = llm_response
            mock_impact_llm.return_value = ("LOW", "Low impact.")
            mock_impact.return_value = _mock_expected_impact("LOW")

            result = await analyzer.analyze("obscure topic")

        assert result.average_fwci == pytest.approx(0.4, abs=0.01)
        assert result.impact_assessment == "LOW"

    @pytest.mark.asyncio
    async def test_none_fwci_papers_stats(self, analyzer, none_fwci_papers):
        """Papers with all None FWCI should give UNCERTAIN impact."""
        with patch.object(
            analyzer, "_decompose_research", new_callable=AsyncMock
        ) as mock_decompose, patch.object(
            analyzer, "_search_papers", new_callable=AsyncMock
        ) as mock_search, patch.object(
            analyzer, "_get_llm_verdict", new_callable=AsyncMock
        ) as mock_llm, patch.object(
            analyzer, "_assess_impact_llm", new_callable=AsyncMock
        ) as mock_impact_llm, patch.object(
            analyzer, "_assess_expected_impact", new_callable=AsyncMock
        ) as mock_impact:
            mock_decompose.return_value = _mock_decomposition()
            mock_search.return_value = none_fwci_papers
            mock_llm.return_value = _mock_llm_response("UNCERTAIN", 0.5, "Insufficient data.")
            mock_impact_llm.return_value = ("UNCERTAIN", "No FWCI data.")
            mock_impact.return_value = _mock_expected_impact("UNCERTAIN", "Cannot assess.")

            result = await analyzer.analyze("topic with no metrics")

        assert result.average_fwci is None
        assert result.impact_assessment == "UNCERTAIN"

    @pytest.mark.asyncio
    async def test_mixed_fwci_papers(self, analyzer):
        """Mix of papers with and without FWCI — should only average valid ones."""
        papers = [
            {
                "id": "https://openalex.org/W2001",
                "title": "Good Paper",
                "doi": "10.1234/good",
                "fwci": 2.0,
                "citation_normalized_percentile": 0.9,
                "cited_by_percentile_year_min": 85,
                "cited_by_percentile_year_max": 95,
                "authors": ["A"],
                "publication_year": 2023,
                "cited_by_count": 100,
            },
            {
                "id": "https://openalex.org/W2002",
                "title": "No FWCI Paper",
                "doi": "10.1234/none",
                "fwci": None,
                "citation_normalized_percentile": None,
                "cited_by_percentile_year_min": None,
                "cited_by_percentile_year_max": None,
                "authors": [],
                "publication_year": 2024,
                "cited_by_count": 0,
            },
        ]
        llm_response = _mock_llm_response("NOVEL", 0.7, "Interesting area.")

        with patch.object(
            analyzer, "_decompose_research", new_callable=AsyncMock
        ) as mock_decompose, patch.object(
            analyzer, "_search_papers", new_callable=AsyncMock
        ) as mock_search, patch.object(
            analyzer, "_get_llm_verdict", new_callable=AsyncMock
        ) as mock_llm, patch.object(
            analyzer, "_assess_impact_llm", new_callable=AsyncMock
        ) as mock_impact_llm, patch.object(
            analyzer, "_assess_expected_impact", new_callable=AsyncMock
        ) as mock_impact:
            mock_decompose.return_value = _mock_decomposition()
            mock_search.return_value = papers
            mock_llm.return_value = llm_response
            mock_impact_llm.return_value = ("HIGH", "High impact.")
            mock_impact.return_value = _mock_expected_impact("HIGH")

            result = await analyzer.analyze("mixed fwci topic")

        # Only the paper with FWCI=2.0 should be averaged
        assert result.average_fwci == pytest.approx(2.0)
        assert result.impact_assessment == "HIGH"
        assert result.related_papers_count == 2


class TestEvidenceCitations:
    """Tests that citations are correctly built from papers."""

    @pytest.mark.asyncio
    async def test_citations_from_papers(self, analyzer, high_fwci_papers):
        llm_response = _mock_llm_response("NOVEL", 0.8, "Novel.")

        with patch.object(
            analyzer, "_decompose_research", new_callable=AsyncMock
        ) as mock_decompose, patch.object(
            analyzer, "_search_papers", new_callable=AsyncMock
        ) as mock_search, patch.object(
            analyzer, "_get_llm_verdict", new_callable=AsyncMock
        ) as mock_llm, patch.object(
            analyzer, "_assess_impact_llm", new_callable=AsyncMock
        ) as mock_impact_llm, patch.object(
            analyzer, "_assess_expected_impact", new_callable=AsyncMock
        ) as mock_impact:
            mock_decompose.return_value = _mock_decomposition()
            mock_search.return_value = high_fwci_papers
            mock_llm.return_value = llm_response
            mock_impact_llm.return_value = ("HIGH", "High impact.")
            mock_impact.return_value = _mock_expected_impact("HIGH")

            result = await analyzer.analyze("test")

        assert len(result.evidence) == 2
        assert result.evidence[0].title == "High Impact Paper 1"
        assert result.evidence[0].doi == "10.1234/high1"
        assert result.evidence[0].fwci == 3.0

    @pytest.mark.asyncio
    async def test_no_citations_when_no_papers(self, analyzer):
        with patch.object(
            analyzer, "_decompose_research", new_callable=AsyncMock
        ) as mock_decompose, patch.object(
            analyzer, "_search_papers", new_callable=AsyncMock
        ) as mock_search:
            mock_decompose.return_value = _mock_decomposition()
            mock_search.return_value = []

            result = await analyzer.analyze("nothing")

        assert result.evidence == []


class TestAnalyzerErrorHandling:
    """Tests for error scenarios in the analyzer."""

    @pytest.mark.asyncio
    async def test_openalex_failure_returns_uncertain(self, analyzer):
        with patch.object(
            analyzer, "_decompose_research", new_callable=AsyncMock
        ) as mock_decompose, patch.object(
            analyzer, "_search_papers", new_callable=AsyncMock
        ) as mock_search:
            mock_decompose.return_value = _mock_decomposition()
            mock_search.side_effect = Exception("API failure")

            result = await analyzer.analyze("test")

        assert result.verdict == "UNCERTAIN"
        assert result.impact_assessment == "UNCERTAIN"
        assert result.expected_impact_assessment == "UNCERTAIN"

    @pytest.mark.asyncio
    async def test_llm_failure_returns_uncertain(self, analyzer, high_fwci_papers):
        with patch.object(
            analyzer, "_decompose_research", new_callable=AsyncMock
        ) as mock_decompose, patch.object(
            analyzer, "_search_papers", new_callable=AsyncMock
        ) as mock_search, patch.object(
            analyzer, "_get_llm_verdict", new_callable=AsyncMock
        ) as mock_llm, patch.object(
            analyzer, "_assess_impact_llm", new_callable=AsyncMock
        ) as mock_impact_llm, patch.object(
            analyzer, "_assess_expected_impact", new_callable=AsyncMock
        ) as mock_impact:
            mock_decompose.return_value = _mock_decomposition()
            mock_search.return_value = high_fwci_papers
            mock_llm.side_effect = Exception("LLM failure")
            mock_impact_llm.return_value = ("HIGH", "High impact.")
            mock_impact.return_value = _mock_expected_impact("UNCERTAIN", "Cannot assess.")

            result = await analyzer.analyze("test")

        assert result.verdict == "UNCERTAIN"
        # FWCI stats should still be computed even if LLM fails
        assert result.average_fwci is not None


class TestExpectedImpact:
    """Tests for the expected impact assessment."""

    @pytest.mark.asyncio
    async def test_expected_impact_flows_into_assessment(self, analyzer, high_fwci_papers):
        llm_response = _mock_llm_response("NOVEL", 0.8, "Novel direction.")

        with patch.object(
            analyzer, "_decompose_research", new_callable=AsyncMock
        ) as mock_decompose, patch.object(
            analyzer, "_search_papers", new_callable=AsyncMock
        ) as mock_search, patch.object(
            analyzer, "_get_llm_verdict", new_callable=AsyncMock
        ) as mock_llm, patch.object(
            analyzer, "_assess_impact_llm", new_callable=AsyncMock
        ) as mock_impact_llm, patch.object(
            analyzer, "_assess_expected_impact", new_callable=AsyncMock
        ) as mock_impact:
            mock_decompose.return_value = _mock_decomposition()
            mock_search.return_value = high_fwci_papers
            mock_llm.return_value = llm_response
            mock_impact_llm.return_value = ("HIGH", "High impact.")
            mock_impact.return_value = ("HIGH", "Strong expected impact due to novel approach.")

            result = await analyzer.analyze("quantum research")

        assert result.expected_impact_assessment == "HIGH"
        assert result.expected_impact_reasoning == "Strong expected impact due to novel approach."


class TestMergeMultiqueryResults:
    """Tests for _merge_multiquery_results helper."""

    def test_merges_and_ranks_by_query_count(self):
        r1 = [{"id": "W1", "title": "A", "relevance_score": 0.5}]
        r2 = [{"id": "W1", "title": "A", "relevance_score": 0.6}, {"id": "W2", "title": "B"}]
        result = _merge_multiquery_results([r1, r2], limit=5)
        assert len(result) == 2
        assert result[0]["id"] == "W1"
        assert result[1]["id"] == "W2"

    def test_dedupes_by_id(self):
        r1 = [{"id": "W1", "title": "A"}]
        r2 = [{"id": "W1", "title": "A again"}]
        result = _merge_multiquery_results([r1, r2], limit=5)
        assert len(result) == 1
        assert result[0]["id"] == "W1"

    def test_caps_at_limit(self):
        r1 = [{"id": f"W{i}", "title": str(i)} for i in range(5)]
        r2 = [{"id": f"K{i}", "title": str(i)} for i in range(5)]
        result = _merge_multiquery_results([r1, r2], limit=4)
        assert len(result) == 4


class TestBuildSearchQueries:
    """Tests for _build_search_queries."""

    def test_returns_key_concepts_or_when_two_plus(self):
        analyzer = NoveltyAnalyzer(
            openalex_email="t@t.com",
            openai_api_key="k",
            multi_query=True,
        )
        d = ResearchDecomposition(
            core_questions=[],
            core_motivations=[],
            potential_impact_domains=[],
            key_concepts=["Psittacula", "parakeet", "speciation"],
        )
        qs = analyzer._build_search_queries("What drives parakeet speciation?", d)
        assert " OR " in qs[0]
        assert "Psittacula" in qs[0] and "parakeet" in qs[0]

    def test_includes_core_question_and_shortened(self):
        analyzer = NoveltyAnalyzer(
            openalex_email="t@t.com",
            openai_api_key="k",
            multi_query=True,
        )
        d = ResearchDecomposition(
            core_questions=["What drives morphological change in parakeet speciation?"],
            core_motivations=[],
            potential_impact_domains=[],
            key_concepts=["parakeet", "speciation"],
        )
        qs = analyzer._build_search_queries("What drives parakeet speciation?", d)
        assert len(qs) >= 2
        assert any("morphological" in q for q in qs)
        assert any("parakeet" in q for q in qs)

    def test_phrase_query_when_2_to_3_concepts(self):
        analyzer = NoveltyAnalyzer(
            openalex_email="t@t.com",
            openai_api_key="k",
            multi_query=True,
        )
        d = ResearchDecomposition(
            core_questions=[],
            core_motivations=[],
            potential_impact_domains=[],
            key_concepts=["parakeet", "speciation"],
        )
        qs = analyzer._build_search_queries("question", d)
        assert any(q.startswith('"') and q.endswith('"') for q in qs)


class TestMergePapers:
    """Tests for _merge_papers helper."""

    def test_merges_semantic_first_then_keyword(self):
        semantic = [{"id": "W1", "title": "A"}, {"id": "W2", "title": "B"}]
        keyword = [{"id": "W3", "title": "C"}, {"id": "W1", "title": "A dup"}]
        result = _merge_papers(semantic, keyword, limit=5)
        assert len(result) == 3
        assert [p["id"] for p in result] == ["W1", "W2", "W3"]
        assert result[0]["title"] == "A"

    def test_dedupes_by_id(self):
        semantic = [{"id": "W1", "title": "A"}]
        keyword = [{"id": "W1", "title": "A again"}]
        result = _merge_papers(semantic, keyword, limit=5)
        assert len(result) == 1
        assert result[0]["id"] == "W1"

    def test_caps_at_limit(self):
        semantic = [{"id": f"W{i}", "title": str(i)} for i in range(5)]
        keyword = [{"id": f"K{i}", "title": str(i)} for i in range(5)]
        result = _merge_papers(semantic, keyword, limit=4)
        assert len(result) == 4


class TestSearchPapersHybrid:
    """Tests for hybrid semantic + keyword search with budget fallback."""

    @pytest.fixture
    def hybrid_analyzer(self):
        """Analyzer with semantic search enabled and API key."""
        return NoveltyAnalyzer(
            openalex_email="test@example.com",
            openai_api_key="test-key",
            openalex_api_key="test-openalex-key",
            use_semantic_search=True,
            semantic_budget_threshold=0.05,
            fwci_high_threshold=1.5,
            fwci_low_threshold=0.8,
            search_limit=8,
        )

    @pytest.fixture
    def mock_decomposition(self):
        return ResearchDecomposition(
            core_questions=["What is X?"],
            core_motivations=[],
            potential_impact_domains=[],
            key_concepts=["specific_term", "another_concept"],
        )

    @pytest.mark.asyncio
    async def test_hybrid_path_when_budget_high(self, hybrid_analyzer, mock_decomposition):
        """When budget >= threshold, runs semantic + multi-query keyword in parallel."""
        semantic_papers = [{"id": "W1", "title": "Semantic Paper"}]
        keyword_papers = [{"id": "W2", "title": "Keyword Paper"}]

        with patch.object(
            hybrid_analyzer._openalex_client,
            "get_remaining_budget_usd",
            new_callable=AsyncMock,
            return_value=0.10,
        ), patch.object(
            hybrid_analyzer._openalex_client,
            "search_papers_semantic",
            new_callable=AsyncMock,
            return_value=semantic_papers,
        ) as mock_semantic, patch.object(
            hybrid_analyzer._openalex_client,
            "search_papers",
            new_callable=AsyncMock,
            return_value=keyword_papers,
        ) as mock_keyword:
            papers = await hybrid_analyzer._search_papers("question", mock_decomposition)

        mock_semantic.assert_called_once()
        mock_keyword.assert_called()
        assert len(papers) == 2
        ids = [p["id"] for p in papers]
        assert "W1" in ids and "W2" in ids

    @pytest.mark.asyncio
    async def test_keyword_only_when_budget_low(self, hybrid_analyzer, mock_decomposition):
        """When budget < threshold, uses keyword-only multi-query flow."""
        keyword_papers = [
            {"id": "W1", "title": "Keyword 1"},
            {"id": "W2", "title": "Keyword 2"},
            {"id": "W3", "title": "Keyword 3"},
        ]

        with patch.object(
            hybrid_analyzer._openalex_client,
            "get_remaining_budget_usd",
            new_callable=AsyncMock,
            return_value=0.02,
        ), patch.object(
            hybrid_analyzer._openalex_client,
            "search_papers_semantic",
            new_callable=AsyncMock,
        ) as mock_semantic, patch.object(
            hybrid_analyzer._openalex_client,
            "search_papers",
            new_callable=AsyncMock,
            return_value=keyword_papers,
        ) as mock_keyword:
            papers = await hybrid_analyzer._search_papers("question", mock_decomposition)

        mock_semantic.assert_not_called()
        mock_keyword.assert_called()
        assert len(papers) == 3
        assert [p["id"] for p in papers] == ["W1", "W2", "W3"]

    @pytest.mark.asyncio
    async def test_keyword_only_when_budget_none(self, hybrid_analyzer, mock_decomposition):
        """When get_remaining_budget_usd returns None, uses keyword-only multi-query."""
        keyword_papers = [
            {"id": "W1", "title": "K1"},
            {"id": "W2", "title": "K2"},
            {"id": "W3", "title": "K3"},
        ]

        with patch.object(
            hybrid_analyzer._openalex_client,
            "get_remaining_budget_usd",
            new_callable=AsyncMock,
            return_value=None,
        ), patch.object(
            hybrid_analyzer._openalex_client,
            "search_papers_semantic",
            new_callable=AsyncMock,
        ) as mock_semantic, patch.object(
            hybrid_analyzer._openalex_client,
            "search_papers",
            new_callable=AsyncMock,
            return_value=keyword_papers,
        ) as mock_keyword:
            papers = await hybrid_analyzer._search_papers("question", mock_decomposition)

        mock_semantic.assert_not_called()
        mock_keyword.assert_called()
        assert len(papers) == 3
