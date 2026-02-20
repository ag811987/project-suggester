"""Regression tests for novelty analysis using benchmark dataset."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from app.models.schemas import ResearchDecomposition
from app.services.novelty_analyzer import NoveltyAnalyzer

BENCHMARK_PATH = Path(__file__).parent / "benchmarks" / "novelty_benchmark.json"

# Allow fuzzy match for borderline cases (e.g., MARGINAL vs UNCERTAIN)
FUZZY_VERDICT_MAP = {
    "MARGINAL": {"MARGINAL", "UNCERTAIN"},
    "UNCERTAIN": {"UNCERTAIN", "MARGINAL"},
}


def _load_benchmark():
    """Load novelty benchmark from JSON."""
    import json
    with open(BENCHMARK_PATH) as f:
        return json.load(f)


def _mock_decomposition():
    """Standard mock for research decomposition."""
    return ResearchDecomposition(
        core_questions=["What is the research question?"],
        core_motivations=["Understanding"],
        potential_impact_domains=["Science"],
        key_concepts=["research"],
    )


@pytest.fixture
def analyzer():
    """Create NoveltyAnalyzer for testing."""
    return NoveltyAnalyzer(
        openalex_email="eval@example.com",
        openai_api_key="test-key",
    )


@pytest.fixture
def default_papers():
    """Default papers for mocked OpenAlex."""
    return [
        {
            "id": "https://openalex.org/W1001",
            "title": "Related Paper 1",
            "doi": "10.1234/rel1",
            "fwci": 1.2,
            "citation_normalized_percentile": 0.65,
            "cited_by_percentile_year_min": 55,
            "cited_by_percentile_year_max": 70,
            "authors": ["Author A"],
            "publication_year": 2023,
            "cited_by_count": 60,
        },
        {
            "id": "https://openalex.org/W1002",
            "title": "Related Paper 2",
            "doi": "10.1234/rel2",
            "fwci": 1.0,
            "citation_normalized_percentile": 0.55,
            "cited_by_percentile_year_min": 45,
            "cited_by_percentile_year_max": 60,
            "authors": ["Author B"],
            "publication_year": 2022,
            "cited_by_count": 40,
        },
    ]


def _verdict_to_score(verdict: str) -> float:
    """Map verdict to typical novelty score."""
    return {"SOLVED": 0.1, "MARGINAL": 0.4, "NOVEL": 0.8, "UNCERTAIN": 0.5}[verdict]


def _verdict_to_impact(verdict: str) -> str:
    """Map verdict to typical impact for mock."""
    if verdict in ("SOLVED", "NOVEL"):
        return "HIGH"
    if verdict == "MARGINAL":
        return "LOW"
    return "MEDIUM"


@pytest.mark.evaluation
@pytest.mark.slow
@pytest.mark.asyncio
async def test_novelty_benchmark_regression(analyzer, default_papers):
    """Run all benchmark cases with mocked OpenAlex and LLM."""
    benchmark = _load_benchmark()
    failed = []

    for case in benchmark:
        case_id = case["id"]
        research_question = case["research_question"]
        expected_verdict = case["expected_verdict"]
        expected_impact = case.get("expected_impact")
        mock_papers = case.get("mock_papers", default_papers)

        llm_verdict = {
            "verdict": expected_verdict,
            "score": _verdict_to_score(expected_verdict),
            "reasoning": f"Benchmark case {case_id}",
        }
        impact_level = expected_impact or _verdict_to_impact(expected_verdict)
        impact_reasoning = f"Impact for {case_id}"

        with (
            patch.object(
                analyzer, "_decompose_research", new_callable=AsyncMock
            ) as mock_decompose,
            patch.object(
                analyzer, "_search_papers", new_callable=AsyncMock
            ) as mock_search,
            patch.object(
                analyzer, "_get_llm_verdict", new_callable=AsyncMock
            ) as mock_llm,
            patch.object(
                analyzer, "_assess_impact_llm", new_callable=AsyncMock
            ) as mock_impact_llm,
            patch.object(
                analyzer, "_assess_expected_impact", new_callable=AsyncMock
            ) as mock_impact,
        ):
            mock_decompose.return_value = _mock_decomposition()
            mock_search.return_value = mock_papers
            mock_llm.return_value = llm_verdict
            mock_impact_llm.return_value = (impact_level, impact_reasoning)
            mock_impact.return_value = (impact_level, impact_reasoning)

            result = await analyzer.analyze(research_question)

            # Strict verdict check (or fuzzy for MARGINAL/UNCERTAIN)
            allowed = FUZZY_VERDICT_MAP.get(
                expected_verdict, {expected_verdict}
            )
            if result.verdict not in allowed:
                failed.append(
                    f"{case_id}: expected {expected_verdict}, got {result.verdict}"
                )
                continue

            if expected_impact and result.impact_assessment != expected_impact:
                failed.append(
                    f"{case_id}: expected impact {expected_impact}, "
                    f"got {result.impact_assessment}"
                )

    assert not failed, "Benchmark failures:\n" + "\n".join(failed)


@pytest.mark.evaluation
@pytest.mark.slow
@pytest.mark.asyncio
async def test_novelty_benchmark_case_by_case(analyzer, default_papers):
    """Run each benchmark case as a separate test for clearer reporting."""
    benchmark = _load_benchmark()

    for case in benchmark:
        case_id = case["id"]
        research_question = case["research_question"]
        expected_verdict = case["expected_verdict"]
        expected_impact = case.get("expected_impact")
        mock_papers = case.get("mock_papers", default_papers)

        llm_verdict = {
            "verdict": expected_verdict,
            "score": _verdict_to_score(expected_verdict),
            "reasoning": f"Benchmark case {case_id}",
        }
        impact_level = expected_impact or _verdict_to_impact(expected_verdict)
        impact_reasoning = f"Impact for {case_id}"

        with (
            patch.object(
                analyzer, "_decompose_research", new_callable=AsyncMock
            ) as mock_decompose,
            patch.object(
                analyzer, "_search_papers", new_callable=AsyncMock
            ) as mock_search,
            patch.object(
                analyzer, "_get_llm_verdict", new_callable=AsyncMock
            ) as mock_llm,
            patch.object(
                analyzer, "_assess_impact_llm", new_callable=AsyncMock
            ) as mock_impact_llm,
            patch.object(
                analyzer, "_assess_expected_impact", new_callable=AsyncMock
            ) as mock_impact,
        ):
            mock_decompose.return_value = _mock_decomposition()
            mock_search.return_value = mock_papers
            mock_llm.return_value = llm_verdict
            mock_impact_llm.return_value = (impact_level, impact_reasoning)
            mock_impact.return_value = (impact_level, impact_reasoning)

            result = await analyzer.analyze(research_question)

            allowed = FUZZY_VERDICT_MAP.get(
                expected_verdict, {expected_verdict}
            )
            assert result.verdict in allowed, (
                f"{case_id}: expected verdict in {allowed}, got {result.verdict}"
            )
            if expected_impact:
                assert result.impact_assessment == expected_impact, (
                    f"{case_id}: expected impact {expected_impact}, "
                    f"got {result.impact_assessment}"
                )
