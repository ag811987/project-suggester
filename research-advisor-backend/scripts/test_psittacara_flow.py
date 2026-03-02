#!/usr/bin/env python3
"""
One-off test: run novelty analysis for the Psittacara query and print
(1) the query(ies) sent to OpenAlex and (2) the results shown in the app.

Usage (from repo root, with .env containing OPENALEX_API_KEY, OPENAI_API_KEY):
  cd research-advisor-backend && poetry run python scripts/test_psittacara_flow.py
"""
import asyncio
import os
import sys

# Load .env from project root if present
def _load_env():
    for path in [
        os.path.join(os.path.dirname(__file__), "..", ".env"),
        os.path.join(os.path.dirname(__file__), "..", "..", ".env"),
        ".env",
    ]:
        if os.path.isfile(path):
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k and k not in os.environ:
                            os.environ[k] = v
            break

_load_env()

from app.config import get_settings
from app.services.novelty_analyzer import NoveltyAnalyzer


RESEARCH_QUESTION = "Incorporating modes of phenotypic evolution into species delimitation of Psittacara parakeets."


async def main():
    settings = get_settings()
    openalex_key = getattr(settings, "openalex_api_key", None) or os.environ.get("OPENALEX_API_KEY")
    if not openalex_key:
        print("OPENALEX_API_KEY not set; semantic search will not run.", file=sys.stderr)

    queries_sent = []

    analyzer = NoveltyAnalyzer(
        openalex_email=settings.openalex_email,
        openai_api_key=settings.openai_api_key,
        openalex_api_key=openalex_key,
        openai_model=settings.openai_model,
        use_semantic_search=getattr(settings, "openalex_use_semantic_search", True),
        semantic_budget_threshold=getattr(settings, "openalex_semantic_budget_threshold", 0.05),
        semantic_only=getattr(settings, "openalex_semantic_only", True),
        condense_query_threshold=getattr(settings, "openalex_condense_query_threshold", 0),
        search_limit=settings.openalex_search_limit,
    )
    original_semantic = analyzer._openalex_client.search_papers_semantic

    async def captured_semantic(query: str, limit=None):
        queries_sent.append(("search_papers_semantic", query, limit))
        return await original_semantic(query, limit)

    analyzer._openalex_client.search_papers_semantic = captured_semantic

    print("=" * 72)
    print("Research proposal:", RESEARCH_QUESTION)
    print("=" * 72)

    result = await analyzer.analyze(RESEARCH_QUESTION, profile=None)

    print("\n--- 1) Query(ies) sent to OpenAlex ---")
    if not queries_sent:
        print("(None – semantic path may have been skipped or fallback used.)")
    for i, (method, query, limit) in enumerate(queries_sent, 1):
        print(f"  {i}. Method: {method}")
        print(f"     Query: {query!r}")
        print(f"     Limit: {limit}")

    print("\n--- 2) Results shown in the application ---")
    print(f"  Verdict: {result.verdict}")
    print(f"  Score: {result.score:.2f}")
    print(f"  Related papers count: {result.related_papers_count}")
    print(f"  Evidence (citations) shown to user ({len(result.evidence)}):")
    for j, c in enumerate(result.evidence[:15], 1):
        title = (c.title or "")[:70]
        print(f"    {j}. {title}" + ("..." if len(c.title or "") > 70 else ""))
    if len(result.evidence) > 15:
        print(f"    ... and {len(result.evidence) - 15} more")

    print("\n" + "=" * 72)
    await analyzer.close()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
