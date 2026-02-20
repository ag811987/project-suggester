"""CLI to run evaluation benchmarks and report results."""

import argparse
import json
import sys
from pathlib import Path

# Add project root for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.models.schemas import ResearchDecomposition
from app.services.novelty_analyzer import NoveltyAnalyzer

BENCHMARK_PATH = Path(__file__).parent / "benchmarks" / "novelty_benchmark.json"


def _load_benchmark():
    """Load novelty benchmark from JSON."""
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


async def run_novelty_eval(live: bool = False) -> dict:
    """Run novelty benchmark and return results."""
    from unittest.mock import AsyncMock, patch

    benchmark = _load_benchmark()
    default_papers = [
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

    # Load settings for live mode
    if live:
        from app.config import get_settings
        settings = get_settings()
        analyzer = NoveltyAnalyzer(
            openalex_email=settings.openalex_email,
            openai_api_key=settings.openai_api_key,
            openalex_api_key=settings.openalex_api_key,
        )
    else:
        analyzer = NoveltyAnalyzer(
            openalex_email="eval@example.com",
            openai_api_key="test-key",
        )

    results = []
    passed = 0
    failed = 0

    for case in benchmark:
        case_id = case["id"]
        research_question = case["research_question"]
        expected_verdict = case["expected_verdict"]
        expected_impact = case.get("expected_impact")
        mock_papers = case.get("mock_papers", default_papers)

        if live:
            result = await analyzer.analyze(research_question)
        else:
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

        verdict_ok = result.verdict == expected_verdict
        impact_ok = (
            expected_impact is None or result.impact_assessment == expected_impact
        )
        case_ok = verdict_ok and impact_ok
        if case_ok:
            passed += 1
        else:
            failed += 1

        results.append({
            "id": case_id,
            "research_question": research_question[:60] + "..." if len(research_question) > 60 else research_question,
            "expected_verdict": expected_verdict,
            "actual_verdict": result.verdict,
            "expected_impact": expected_impact,
            "actual_impact": result.impact_assessment,
            "passed": case_ok,
        })

    return {
        "summary": {"passed": passed, "failed": failed, "total": len(benchmark)},
        "results": results,
    }


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Run novelty evaluation benchmark"
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Use real OpenAlex and OpenAI (slower, for periodic validation)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON report for CI artifact",
    )
    args = parser.parse_args()

    import asyncio
    report = asyncio.run(run_novelty_eval(live=args.live))

    if args.json:
        print(json.dumps(report, indent=2))
        return 0 if report["summary"]["failed"] == 0 else 1

    # Print summary table
    print("\n=== Novelty Evaluation Report ===\n")
    for r in report["results"]:
        status = "PASS" if r["passed"] else "FAIL"
        print(f"  [{status}] {r['id']}: {r['actual_verdict']} (expected {r['expected_verdict']})")
    print()
    s = report["summary"]
    print(f"  Passed: {s['passed']}  Failed: {s['failed']}  Total: {s['total']}")
    print()
    return 0 if s["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
