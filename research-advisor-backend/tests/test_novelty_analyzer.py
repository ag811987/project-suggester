"""Tests for Novelty & Impact Analyzer."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.novelty_analyzer import NoveltyAnalyzer
from app.models.schemas import NoveltyAssessment, ResearchDecomposition


@pytest.fixture
def analyzer():
    """Create a NoveltyAnalyzer instance for testing."""
    return NoveltyAnalyzer(
        openalex_email="test@example.com",
        openai_api_key="test-key",
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
