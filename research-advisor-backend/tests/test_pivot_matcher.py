"""Tests for PivotMatcher service."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.schemas import (
    GapMapEntry,
    NoveltyAssessment,
    PivotSuggestion,
    ResearchProfile,
)
from app.services.pivot_matcher import PivotMatcher


@pytest.fixture
def pivot_matcher():
    """Create a PivotMatcher instance with mocked OpenAI client."""
    return PivotMatcher()


@pytest.fixture
def mock_llm_pivot_response():
    """Mock LLM response for pivot matching."""
    return json.dumps([
        {
            "gap_index": 0,
            "relevance_score": 0.85,
            "impact_potential": "HIGH",
            "match_reasoning": "Researcher's Python and Algorithm Design skills directly apply to scalable cell therapy production optimization.",
            "feasibility_for_researcher": "High feasibility - computational skills transfer well to biotech optimization problems.",
            "impact_rationale": "Cell therapy manufacturing is a critical bottleneck with massive clinical impact."
        },
        {
            "gap_index": 2,
            "relevance_score": 0.65,
            "impact_potential": "MEDIUM",
            "match_reasoning": "Algorithm Design skills could be applied to carbon capture optimization.",
            "feasibility_for_researcher": "Moderate feasibility - would require domain knowledge acquisition in climate science.",
            "impact_rationale": "Climate change mitigation is globally significant but requires domain expertise."
        },
        {
            "gap_index": 1,
            "relevance_score": 0.75,
            "impact_potential": "HIGH",
            "match_reasoning": "Quantum computing expertise enables novel approaches to protein design computational problems.",
            "feasibility_for_researcher": "Good feasibility - quantum algorithms for molecular simulation are an active research area.",
            "impact_rationale": "Protein design has transformative potential in medicine and biotechnology."
        },
    ])


class TestPivotMatcher:
    """Test suite for PivotMatcher."""

    @pytest.mark.asyncio
    async def test_match_pivots_returns_list_of_pivot_suggestions(
        self,
        pivot_matcher,
        sample_research_profile,
        sample_novelty_assessment,
        sample_gap_map_entries,
        mock_llm_pivot_response,
    ):
        """Test that match_pivots returns a list of PivotSuggestion objects."""
        with patch.object(
            pivot_matcher, "_call_llm", new_callable=AsyncMock, return_value=mock_llm_pivot_response
        ):
            result = await pivot_matcher.match_pivots(
                profile=sample_research_profile,
                novelty=sample_novelty_assessment,
                gap_entries=sample_gap_map_entries,
            )

        assert isinstance(result, list)
        assert all(isinstance(s, PivotSuggestion) for s in result)

    @pytest.mark.asyncio
    async def test_match_pivots_ranked_by_relevance_times_impact(
        self,
        pivot_matcher,
        sample_research_profile,
        sample_novelty_assessment,
        sample_gap_map_entries,
        mock_llm_pivot_response,
    ):
        """Test that suggestions are ranked by relevance × impact weight."""
        with patch.object(
            pivot_matcher, "_call_llm", new_callable=AsyncMock, return_value=mock_llm_pivot_response
        ):
            result = await pivot_matcher.match_pivots(
                profile=sample_research_profile,
                novelty=sample_novelty_assessment,
                gap_entries=sample_gap_map_entries,
            )

        # Results should be sorted by composite score (relevance × impact_weight) descending
        # gap_index=0: 0.85 * 3.0(HIGH) = 2.55
        # gap_index=1: 0.75 * 3.0(HIGH) = 2.25
        # gap_index=2: 0.65 * 2.0(MEDIUM) = 1.30
        assert len(result) == 3
        assert result[0].relevance_score == 0.85  # Highest composite score
        assert result[0].impact_potential == "HIGH"
        assert result[1].relevance_score == 0.75
        assert result[1].impact_potential == "HIGH"
        assert result[2].relevance_score == 0.65
        assert result[2].impact_potential == "MEDIUM"

    @pytest.mark.asyncio
    async def test_match_pivots_returns_top_n(
        self,
        pivot_matcher,
        sample_research_profile,
        sample_novelty_assessment,
        sample_gap_map_entries,
        mock_llm_pivot_response,
    ):
        """Test that match_pivots returns at most top_n suggestions."""
        with patch.object(
            pivot_matcher, "_call_llm", new_callable=AsyncMock, return_value=mock_llm_pivot_response
        ):
            result = await pivot_matcher.match_pivots(
                profile=sample_research_profile,
                novelty=sample_novelty_assessment,
                gap_entries=sample_gap_map_entries,
                top_n=2,
            )

        assert len(result) <= 2

    @pytest.mark.asyncio
    async def test_match_pivots_default_top_5(
        self,
        pivot_matcher,
        sample_research_profile,
        sample_novelty_assessment,
        sample_gap_map_entries,
        mock_llm_pivot_response,
    ):
        """Test that default top_n is 5."""
        with patch.object(
            pivot_matcher, "_call_llm", new_callable=AsyncMock, return_value=mock_llm_pivot_response
        ):
            result = await pivot_matcher.match_pivots(
                profile=sample_research_profile,
                novelty=sample_novelty_assessment,
                gap_entries=sample_gap_map_entries,
            )

        # We only have 3 gap entries, so result should be 3 (< default 5)
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_match_pivots_gap_entry_correctly_linked(
        self,
        pivot_matcher,
        sample_research_profile,
        sample_novelty_assessment,
        sample_gap_map_entries,
        mock_llm_pivot_response,
    ):
        """Test that each PivotSuggestion references the correct GapMapEntry."""
        with patch.object(
            pivot_matcher, "_call_llm", new_callable=AsyncMock, return_value=mock_llm_pivot_response
        ):
            result = await pivot_matcher.match_pivots(
                profile=sample_research_profile,
                novelty=sample_novelty_assessment,
                gap_entries=sample_gap_map_entries,
            )

        # First result should reference gap_index 0 (highest composite score)
        assert result[0].gap_entry.title == "Scalable Production of Cell Therapies"
        # Second result should reference gap_index 1
        assert result[1].gap_entry.title == "Protein Design for Novel Functions"
        # Third result should reference gap_index 2
        assert result[2].gap_entry.title == "Climate Change Mitigation Technologies"

    @pytest.mark.asyncio
    async def test_match_pivots_includes_reasoning_fields(
        self,
        pivot_matcher,
        sample_research_profile,
        sample_novelty_assessment,
        sample_gap_map_entries,
        mock_llm_pivot_response,
    ):
        """Test that each suggestion includes non-empty reasoning fields."""
        with patch.object(
            pivot_matcher, "_call_llm", new_callable=AsyncMock, return_value=mock_llm_pivot_response
        ):
            result = await pivot_matcher.match_pivots(
                profile=sample_research_profile,
                novelty=sample_novelty_assessment,
                gap_entries=sample_gap_map_entries,
            )

        for suggestion in result:
            assert suggestion.match_reasoning
            assert suggestion.feasibility_for_researcher
            assert suggestion.impact_rationale

    @pytest.mark.asyncio
    async def test_match_pivots_empty_gap_entries(
        self,
        pivot_matcher,
        sample_research_profile,
        sample_novelty_assessment,
    ):
        """Test that match_pivots returns empty list when no gap entries provided."""
        result = await pivot_matcher.match_pivots(
            profile=sample_research_profile,
            novelty=sample_novelty_assessment,
            gap_entries=[],
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_match_pivots_handles_llm_invalid_json(
        self,
        pivot_matcher,
        sample_research_profile,
        sample_novelty_assessment,
        sample_gap_map_entries,
    ):
        """Test graceful handling when LLM returns invalid JSON."""
        with patch.object(
            pivot_matcher, "_call_llm", new_callable=AsyncMock, return_value="not valid json"
        ):
            result = await pivot_matcher.match_pivots(
                profile=sample_research_profile,
                novelty=sample_novelty_assessment,
                gap_entries=sample_gap_map_entries,
            )

        assert result == []

    @pytest.mark.asyncio
    async def test_match_pivots_handles_llm_exception(
        self,
        pivot_matcher,
        sample_research_profile,
        sample_novelty_assessment,
        sample_gap_map_entries,
    ):
        """Test graceful handling when LLM call raises an exception."""
        with patch.object(
            pivot_matcher, "_call_llm", new_callable=AsyncMock, side_effect=Exception("API error")
        ):
            result = await pivot_matcher.match_pivots(
                profile=sample_research_profile,
                novelty=sample_novelty_assessment,
                gap_entries=sample_gap_map_entries,
            )

        assert result == []

    @pytest.mark.asyncio
    async def test_match_pivots_filters_invalid_gap_index(
        self,
        pivot_matcher,
        sample_research_profile,
        sample_novelty_assessment,
        sample_gap_map_entries,
    ):
        """Test that invalid gap_index values in LLM response are filtered out."""
        bad_response = json.dumps([
            {
                "gap_index": 99,  # Out of range
                "relevance_score": 0.9,
                "impact_potential": "HIGH",
                "match_reasoning": "Test",
                "feasibility_for_researcher": "Test",
                "impact_rationale": "Test"
            },
            {
                "gap_index": 0,
                "relevance_score": 0.8,
                "impact_potential": "MEDIUM",
                "match_reasoning": "Valid match",
                "feasibility_for_researcher": "Feasible",
                "impact_rationale": "Good impact"
            },
        ])
        with patch.object(
            pivot_matcher, "_call_llm", new_callable=AsyncMock, return_value=bad_response
        ):
            result = await pivot_matcher.match_pivots(
                profile=sample_research_profile,
                novelty=sample_novelty_assessment,
                gap_entries=sample_gap_map_entries,
            )

        assert len(result) == 1
        assert result[0].gap_entry.title == "Scalable Production of Cell Therapies"

    @pytest.mark.asyncio
    async def test_match_pivots_relevance_score_clamped(
        self,
        pivot_matcher,
        sample_research_profile,
        sample_novelty_assessment,
        sample_gap_map_entries,
    ):
        """Test that relevance scores are clamped to [0.0, 1.0]."""
        response = json.dumps([
            {
                "gap_index": 0,
                "relevance_score": 1.5,  # Over 1.0
                "impact_potential": "HIGH",
                "match_reasoning": "Test",
                "feasibility_for_researcher": "Test",
                "impact_rationale": "Test"
            },
        ])
        with patch.object(
            pivot_matcher, "_call_llm", new_callable=AsyncMock, return_value=response
        ):
            result = await pivot_matcher.match_pivots(
                profile=sample_research_profile,
                novelty=sample_novelty_assessment,
                gap_entries=sample_gap_map_entries,
            )

        assert len(result) == 1
        assert result[0].relevance_score <= 1.0
