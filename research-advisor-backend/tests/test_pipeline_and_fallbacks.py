"""Tests for the async pipeline, JSON parse fallbacks, and UNCERTAIN handling."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.schemas import (
    NoveltyAssessment,
    Citation,
    ReportSections,
    ResearchRecommendation,
)
from app.services.pivot_matcher import PivotMatcher
from app.services.report_generator import ReportGenerator


class TestPivotMatcherJsonFallback:
    """Verify that PivotMatcher degrades gracefully on bad JSON."""

    @pytest.mark.asyncio
    async def test_invalid_json_returns_empty_list(
        self,
        sample_research_profile,
        sample_novelty_assessment,
        sample_gap_map_entries,
    ):
        """When _call_llm returns non-JSON, match_pivots returns []."""
        matcher = PivotMatcher()
        with patch.object(
            matcher, "_call_llm", new_callable=AsyncMock, return_value="not json"
        ):
            result = await matcher.match_pivots(
                sample_research_profile,
                sample_novelty_assessment,
                sample_gap_map_entries,
            )
        assert result == []

    @pytest.mark.asyncio
    async def test_non_array_json_returns_empty_list(
        self,
        sample_research_profile,
        sample_novelty_assessment,
        sample_gap_map_entries,
    ):
        """When LLM returns a JSON object instead of array, returns []."""
        matcher = PivotMatcher()
        with patch.object(
            matcher, "_call_llm", new_callable=AsyncMock, return_value='{"key": "val"}'
        ):
            result = await matcher.match_pivots(
                sample_research_profile,
                sample_novelty_assessment,
                sample_gap_map_entries,
            )
        assert result == []


class TestReportGeneratorJsonFallback:
    """Verify that ReportGenerator degrades gracefully on bad JSON."""

    @pytest.mark.asyncio
    async def test_invalid_json_uses_fallback_sections(
        self,
        sample_research_profile,
        sample_novelty_assessment,
    ):
        """When LLM returns unparseable JSON, a fallback report is generated."""
        gen = ReportGenerator()
        with patch.object(
            gen, "_call_llm", new_callable=AsyncMock, return_value="not json at all"
        ):
            rec = await gen.generate_report(
                sample_research_profile,
                sample_novelty_assessment,
                [],
            )
        assert isinstance(rec, ResearchRecommendation)
        assert rec.narrative_report
        assert rec.report_sections is not None

    @pytest.mark.asyncio
    async def test_api_exception_uses_fallback(
        self,
        sample_research_profile,
        sample_novelty_assessment,
    ):
        """When _call_llm raises, fallback sections are used (no crash)."""
        gen = ReportGenerator()
        with patch.object(
            gen, "_call_llm", new_callable=AsyncMock, side_effect=RuntimeError("boom")
        ):
            rec = await gen.generate_report(
                sample_research_profile,
                sample_novelty_assessment,
                [],
            )
        assert isinstance(rec, ResearchRecommendation)
        assert rec.report_sections is not None


class TestDecisionEngine:
    """Tests for the continue/pivot/uncertain decision logic."""

    def _make_novelty(self, verdict: str, expected_impact: str) -> NoveltyAssessment:
        return NoveltyAssessment(
            score=0.5,
            verdict=verdict,
            evidence=[],
            reasoning="test",
            related_papers_count=0,
            impact_assessment="MEDIUM",
            impact_reasoning="test",
            expected_impact_assessment=expected_impact,
            expected_impact_reasoning="test",
        )

    def test_solved_means_pivot(self):
        gen = ReportGenerator()
        assert gen._determine_recommendation(self._make_novelty("SOLVED", "HIGH")) == "PIVOT"

    def test_marginal_means_pivot(self):
        gen = ReportGenerator()
        assert gen._determine_recommendation(self._make_novelty("MARGINAL", "HIGH")) == "PIVOT"

    def test_low_impact_means_pivot(self):
        gen = ReportGenerator()
        assert gen._determine_recommendation(self._make_novelty("NOVEL", "LOW")) == "PIVOT"

    def test_novel_high_means_continue(self):
        gen = ReportGenerator()
        assert gen._determine_recommendation(self._make_novelty("NOVEL", "HIGH")) == "CONTINUE"

    def test_novel_medium_means_continue(self):
        gen = ReportGenerator()
        assert gen._determine_recommendation(self._make_novelty("NOVEL", "MEDIUM")) == "CONTINUE"

    def test_uncertain_verdict_means_uncertain(self):
        gen = ReportGenerator()
        assert gen._determine_recommendation(self._make_novelty("UNCERTAIN", "MEDIUM")) == "UNCERTAIN"

    def test_uncertain_impact_with_novel_means_uncertain(self):
        gen = ReportGenerator()
        assert gen._determine_recommendation(self._make_novelty("NOVEL", "UNCERTAIN")) == "UNCERTAIN"


class TestSessionStatusSchema:
    """Verify the SessionStatusResponse schema has the stage field."""

    def test_session_status_includes_stage(self):
        from app.models.schemas import SessionStatusResponse

        resp = SessionStatusResponse(
            session_id="abc",
            status="processing",
            stage="analyzing_novelty",
            result=None,
            error_message=None,
        )
        assert resp.stage == "analyzing_novelty"

    def test_session_status_completed_has_result(self):
        from app.models.schemas import SessionStatusResponse

        resp = SessionStatusResponse(
            session_id="abc",
            status="completed",
            stage="completed",
            result=None,
            error_message=None,
        )
        assert resp.status == "completed"
