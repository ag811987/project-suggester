"""Tests for ReportGenerator service."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from app.models.schemas import (
    Citation,
    GapMapEntry,
    NoveltyAssessment,
    PivotSuggestion,
    ResearchRecommendation,
    ResearchProfile,
)
from app.services.report_generator import ReportGenerator


@pytest.fixture
def report_generator():
    """Create a ReportGenerator instance."""
    return ReportGenerator()


@pytest.fixture
def sample_pivot_suggestions(sample_gap_map_entries):
    """Sample pivot suggestions for testing."""
    return [
        PivotSuggestion(
            gap_entry=sample_gap_map_entries[0],
            relevance_score=0.85,
            impact_potential="HIGH",
            match_reasoning="Strong alignment with computational skills.",
            feasibility_for_researcher="High feasibility.",
            impact_rationale="Critical bottleneck in biotech.",
        ),
        PivotSuggestion(
            gap_entry=sample_gap_map_entries[1],
            relevance_score=0.75,
            impact_potential="HIGH",
            match_reasoning="Quantum computing enables novel protein design approaches.",
            feasibility_for_researcher="Good feasibility.",
            impact_rationale="Transformative potential in medicine.",
        ),
    ]


@pytest.fixture
def mock_llm_report_response():
    """Mock LLM response for report generation (structured JSON)."""
    return json.dumps({
        "novelty_section": "**Verdict: NOVEL** (Score: 0.7/1.0)\n\nThe research explores a fundamental open problem in quantum computing.\n\n**Literature Context:**\n- Related Papers: 3\n- Average FWCI: 1.7",
        "impact_section": "**Expected Impact: MEDIUM**\n\nThe research has moderate expected impact given the novelty of the approach.",
        "pivot_section": ""
    })


@pytest.fixture
def novelty_solved():
    """NoveltyAssessment with SOLVED verdict."""
    return NoveltyAssessment(
        score=0.1,
        verdict="SOLVED",
        evidence=[],
        reasoning="This problem has been thoroughly solved in existing literature.",
        related_papers_count=50,
        average_fwci=3.5,
        fwci_percentile=0.95,
        citation_percentile_min=85,
        citation_percentile_max=99,
        impact_assessment="HIGH",
        impact_reasoning="Well-established area with high citations.",
        expected_impact_assessment="LOW",
        expected_impact_reasoning="Problem already solved; new work unlikely to have significant impact.",
    )


@pytest.fixture
def novelty_marginal():
    """NoveltyAssessment with MARGINAL verdict."""
    return NoveltyAssessment(
        score=0.3,
        verdict="MARGINAL",
        evidence=[],
        reasoning="Only marginal novelty remains in this area.",
        related_papers_count=30,
        average_fwci=1.2,
        fwci_percentile=0.55,
        citation_percentile_min=40,
        citation_percentile_max=65,
        impact_assessment="MEDIUM",
        impact_reasoning="Moderate impact area.",
        expected_impact_assessment="LOW",
        expected_impact_reasoning="Marginal novelty limits expected impact.",
    )


@pytest.fixture
def novelty_novel_high():
    """NoveltyAssessment with NOVEL verdict and HIGH impact."""
    return NoveltyAssessment(
        score=0.9,
        verdict="NOVEL",
        evidence=[],
        reasoning="Highly novel research direction.",
        related_papers_count=5,
        average_fwci=2.0,
        fwci_percentile=0.80,
        citation_percentile_min=70,
        citation_percentile_max=90,
        impact_assessment="HIGH",
        impact_reasoning="High impact area with strong citations.",
        expected_impact_assessment="HIGH",
        expected_impact_reasoning="Highly novel direction with strong expected impact.",
    )


@pytest.fixture
def novelty_novel_medium():
    """NoveltyAssessment with NOVEL verdict and MEDIUM impact."""
    return NoveltyAssessment(
        score=0.8,
        verdict="NOVEL",
        evidence=[],
        reasoning="Novel research direction with moderate impact.",
        related_papers_count=8,
        average_fwci=1.3,
        fwci_percentile=0.60,
        citation_percentile_min=50,
        citation_percentile_max=70,
        impact_assessment="MEDIUM",
        impact_reasoning="Moderate impact area.",
        expected_impact_assessment="MEDIUM",
        expected_impact_reasoning="Moderate expected impact given novelty and field context.",
    )


@pytest.fixture
def novelty_novel_low():
    """NoveltyAssessment with NOVEL verdict and LOW expected impact."""
    return NoveltyAssessment(
        score=0.8,
        verdict="NOVEL",
        evidence=[],
        reasoning="Novel but low impact area.",
        related_papers_count=2,
        average_fwci=0.5,
        fwci_percentile=0.20,
        citation_percentile_min=10,
        citation_percentile_max=30,
        impact_assessment="LOW",
        impact_reasoning="Low citation impact area.",
        expected_impact_assessment="LOW",
        expected_impact_reasoning="Low expected impact due to niche field with limited audience.",
    )


@pytest.fixture
def novelty_uncertain():
    """NoveltyAssessment with UNCERTAIN verdict."""
    return NoveltyAssessment(
        score=0.5,
        verdict="UNCERTAIN",
        evidence=[],
        reasoning="Insufficient data to determine novelty.",
        related_papers_count=1,
        average_fwci=None,
        fwci_percentile=None,
        citation_percentile_min=None,
        citation_percentile_max=None,
        impact_assessment="UNCERTAIN",
        impact_reasoning="Cannot determine impact.",
        expected_impact_assessment="UNCERTAIN",
        expected_impact_reasoning="Cannot predict expected impact due to insufficient data.",
    )


class TestReportGeneratorDecisionLogic:
    """Test the recommendation decision logic."""

    @pytest.mark.asyncio
    async def test_solved_verdict_produces_pivot(
        self,
        report_generator,
        sample_research_profile,
        novelty_solved,
        sample_pivot_suggestions,
        mock_llm_report_response,
    ):
        """If novelty=SOLVED → PIVOT."""
        with patch.object(
            report_generator, "_call_llm", new_callable=AsyncMock,
            return_value=mock_llm_report_response,
        ):
            result = await report_generator.generate_report(
                profile=sample_research_profile,
                novelty=novelty_solved,
                pivot_suggestions=sample_pivot_suggestions,
            )

        assert result.recommendation == "PIVOT"

    @pytest.mark.asyncio
    async def test_marginal_verdict_produces_pivot(
        self,
        report_generator,
        sample_research_profile,
        novelty_marginal,
        sample_pivot_suggestions,
        mock_llm_report_response,
    ):
        """If novelty=MARGINAL → PIVOT."""
        with patch.object(
            report_generator, "_call_llm", new_callable=AsyncMock,
            return_value=mock_llm_report_response,
        ):
            result = await report_generator.generate_report(
                profile=sample_research_profile,
                novelty=novelty_marginal,
                pivot_suggestions=sample_pivot_suggestions,
            )

        assert result.recommendation == "PIVOT"

    @pytest.mark.asyncio
    async def test_novel_low_impact_produces_pivot(
        self,
        report_generator,
        sample_research_profile,
        novelty_novel_low,
        sample_pivot_suggestions,
        mock_llm_report_response,
    ):
        """If novelty=NOVEL AND impact=LOW → PIVOT."""
        with patch.object(
            report_generator, "_call_llm", new_callable=AsyncMock,
            return_value=mock_llm_report_response,
        ):
            result = await report_generator.generate_report(
                profile=sample_research_profile,
                novelty=novelty_novel_low,
                pivot_suggestions=sample_pivot_suggestions,
            )

        assert result.recommendation == "PIVOT"

    @pytest.mark.asyncio
    async def test_novel_high_impact_produces_continue(
        self,
        report_generator,
        sample_research_profile,
        novelty_novel_high,
        sample_pivot_suggestions,
        mock_llm_report_response,
    ):
        """If novelty=NOVEL AND impact=HIGH → CONTINUE."""
        with patch.object(
            report_generator, "_call_llm", new_callable=AsyncMock,
            return_value=mock_llm_report_response,
        ):
            result = await report_generator.generate_report(
                profile=sample_research_profile,
                novelty=novelty_novel_high,
                pivot_suggestions=sample_pivot_suggestions,
            )

        assert result.recommendation == "CONTINUE"

    @pytest.mark.asyncio
    async def test_novel_medium_impact_produces_continue(
        self,
        report_generator,
        sample_research_profile,
        novelty_novel_medium,
        sample_pivot_suggestions,
        mock_llm_report_response,
    ):
        """If novelty=NOVEL AND impact=MEDIUM → CONTINUE."""
        with patch.object(
            report_generator, "_call_llm", new_callable=AsyncMock,
            return_value=mock_llm_report_response,
        ):
            result = await report_generator.generate_report(
                profile=sample_research_profile,
                novelty=novelty_novel_medium,
                pivot_suggestions=sample_pivot_suggestions,
            )

        assert result.recommendation == "CONTINUE"

    @pytest.mark.asyncio
    async def test_uncertain_verdict_produces_uncertain(
        self,
        report_generator,
        sample_research_profile,
        novelty_uncertain,
        sample_pivot_suggestions,
        mock_llm_report_response,
    ):
        """If verdict=UNCERTAIN → UNCERTAIN."""
        with patch.object(
            report_generator, "_call_llm", new_callable=AsyncMock,
            return_value=mock_llm_report_response,
        ):
            result = await report_generator.generate_report(
                profile=sample_research_profile,
                novelty=novelty_uncertain,
                pivot_suggestions=sample_pivot_suggestions,
            )

        assert result.recommendation == "UNCERTAIN"


class TestReportGeneratorOutput:
    """Test report generation output."""

    @pytest.mark.asyncio
    async def test_generate_report_returns_research_recommendation(
        self,
        report_generator,
        sample_research_profile,
        sample_novelty_assessment,
        sample_pivot_suggestions,
        mock_llm_report_response,
    ):
        """Test that generate_report returns a ResearchRecommendation."""
        with patch.object(
            report_generator, "_call_llm", new_callable=AsyncMock,
            return_value=mock_llm_report_response,
        ):
            result = await report_generator.generate_report(
                profile=sample_research_profile,
                novelty=sample_novelty_assessment,
                pivot_suggestions=sample_pivot_suggestions,
            )

        assert isinstance(result, ResearchRecommendation)

    @pytest.mark.asyncio
    async def test_report_includes_narrative(
        self,
        report_generator,
        sample_research_profile,
        sample_novelty_assessment,
        sample_pivot_suggestions,
        mock_llm_report_response,
    ):
        """Test that report includes a narrative report."""
        with patch.object(
            report_generator, "_call_llm", new_callable=AsyncMock,
            return_value=mock_llm_report_response,
        ):
            result = await report_generator.generate_report(
                profile=sample_research_profile,
                novelty=sample_novelty_assessment,
                pivot_suggestions=sample_pivot_suggestions,
            )

        assert result.narrative_report
        assert len(result.narrative_report) > 0

    @pytest.mark.asyncio
    async def test_report_includes_novelty_assessment(
        self,
        report_generator,
        sample_research_profile,
        sample_novelty_assessment,
        sample_pivot_suggestions,
        mock_llm_report_response,
    ):
        """Test that report includes the novelty assessment."""
        with patch.object(
            report_generator, "_call_llm", new_callable=AsyncMock,
            return_value=mock_llm_report_response,
        ):
            result = await report_generator.generate_report(
                profile=sample_research_profile,
                novelty=sample_novelty_assessment,
                pivot_suggestions=sample_pivot_suggestions,
            )

        assert result.novelty_assessment == sample_novelty_assessment

    @pytest.mark.asyncio
    async def test_report_includes_pivot_suggestions(
        self,
        report_generator,
        sample_research_profile,
        sample_novelty_assessment,
        sample_pivot_suggestions,
        mock_llm_report_response,
    ):
        """Test that report includes pivot suggestions."""
        with patch.object(
            report_generator, "_call_llm", new_callable=AsyncMock,
            return_value=mock_llm_report_response,
        ):
            result = await report_generator.generate_report(
                profile=sample_research_profile,
                novelty=sample_novelty_assessment,
                pivot_suggestions=sample_pivot_suggestions,
            )

        assert result.pivot_suggestions == sample_pivot_suggestions

    @pytest.mark.asyncio
    async def test_report_includes_evidence_citations(
        self,
        report_generator,
        sample_research_profile,
        sample_novelty_assessment,
        sample_pivot_suggestions,
        mock_llm_report_response,
    ):
        """Test that report includes evidence citations from novelty assessment."""
        with patch.object(
            report_generator, "_call_llm", new_callable=AsyncMock,
            return_value=mock_llm_report_response,
        ):
            result = await report_generator.generate_report(
                profile=sample_research_profile,
                novelty=sample_novelty_assessment,
                pivot_suggestions=sample_pivot_suggestions,
            )

        assert len(result.evidence_citations) > 0
        # Should include citations from the novelty assessment evidence
        assert any(
            c.doi == "10.1234/quantum.2024"
            for c in result.evidence_citations
        )

    @pytest.mark.asyncio
    async def test_report_confidence_between_0_and_1(
        self,
        report_generator,
        sample_research_profile,
        sample_novelty_assessment,
        sample_pivot_suggestions,
        mock_llm_report_response,
    ):
        """Test that confidence is between 0.0 and 1.0."""
        with patch.object(
            report_generator, "_call_llm", new_callable=AsyncMock,
            return_value=mock_llm_report_response,
        ):
            result = await report_generator.generate_report(
                profile=sample_research_profile,
                novelty=sample_novelty_assessment,
                pivot_suggestions=sample_pivot_suggestions,
            )

        assert 0.0 <= result.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_report_with_empty_pivot_suggestions(
        self,
        report_generator,
        sample_research_profile,
        novelty_novel_high,
        mock_llm_report_response,
    ):
        """Test report generation with no pivot suggestions (CONTINUE case)."""
        with patch.object(
            report_generator, "_call_llm", new_callable=AsyncMock,
            return_value=mock_llm_report_response,
        ):
            result = await report_generator.generate_report(
                profile=sample_research_profile,
                novelty=novelty_novel_high,
                pivot_suggestions=[],
            )

        assert result.recommendation == "CONTINUE"
        assert result.pivot_suggestions == []

    @pytest.mark.asyncio
    async def test_citations_properly_formatted(
        self,
        report_generator,
        sample_research_profile,
        sample_novelty_assessment,
        sample_pivot_suggestions,
        mock_llm_report_response,
    ):
        """Test that citations have required fields."""
        with patch.object(
            report_generator, "_call_llm", new_callable=AsyncMock,
            return_value=mock_llm_report_response,
        ):
            result = await report_generator.generate_report(
                profile=sample_research_profile,
                novelty=sample_novelty_assessment,
                pivot_suggestions=sample_pivot_suggestions,
            )

        for citation in result.evidence_citations:
            assert isinstance(citation, Citation)
            assert citation.title  # Must have a title

    @pytest.mark.asyncio
    async def test_report_handles_llm_failure(
        self,
        report_generator,
        sample_research_profile,
        sample_novelty_assessment,
        sample_pivot_suggestions,
    ):
        """Test that report generator handles LLM failure gracefully."""
        with patch.object(
            report_generator, "_call_llm", new_callable=AsyncMock,
            side_effect=Exception("LLM API error"),
        ):
            result = await report_generator.generate_report(
                profile=sample_research_profile,
                novelty=sample_novelty_assessment,
                pivot_suggestions=sample_pivot_suggestions,
            )

        # Should still return a valid report with fallback narrative
        assert isinstance(result, ResearchRecommendation)
        assert result.narrative_report  # Has some content even on error
