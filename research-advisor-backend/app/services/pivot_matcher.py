"""
Pivot Matcher service for matching researchers to research gaps.

Uses LLM to match a researcher's skills and motivations to gap map entries,
ranking by relevance × impact potential.
"""

import json
import logging

from openai import AsyncOpenAI

from app.config import get_settings
from app.debug_log import debug_log
from app.models.schemas import (
    GapMapEntry,
    ImpactLevel,
    NoveltyAssessment,
    PivotSuggestion,
    ResearcherClassification,
    ResearchProfile,
)

logger = logging.getLogger(__name__)

# Impact weights for composite scoring
IMPACT_WEIGHTS: dict[str, float] = {
    "HIGH": 3.0,
    "MEDIUM": 2.0,
    "LOW": 1.0,
    "UNCERTAIN": 1.5,
}


class PivotMatcher:
    """Matches researchers to potential research pivots using LLM analysis."""

    def __init__(self, openai_client: AsyncOpenAI | None = None):
        self._client = openai_client

    async def _call_llm(self, prompt: str) -> str:
        """Call the LLM with structured JSON output and a single retry on parse failure."""
        if self._client is None:
            self._client = AsyncOpenAI(api_key=get_settings().openai_api_key)

        settings = get_settings()
        for attempt in range(2):
            response = await self._client.chat.completions.create(
                model=settings.openai_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_tokens=2000,
                response_format={"type": "json_object"},
                timeout=60,
            )
            content = response.choices[0].message.content or ""
            try:
                json.loads(content)
                return content
            except json.JSONDecodeError:
                if attempt == 0:
                    logger.warning("LLM returned invalid JSON, retrying with strict prompt")
                    prompt = (
                        "Your previous response was not valid JSON. "
                        "Return ONLY a valid JSON array. No markdown, no explanation.\n\n"
                        + prompt
                    )
                    continue
                return "[]"
        return "[]"

    async def match_pivots(
        self,
        profile: ResearchProfile,
        novelty: NoveltyAssessment,
        gap_entries: list[GapMapEntry],
        top_n: int = 5,
    ) -> list[PivotSuggestion]:
        """
        Match a researcher's profile to gap map entries.

        Uses LLM to understand the researcher's skills and motivations,
        then matches to gap entries and ranks by relevance × impact weight.

        Args:
            profile: The researcher's profile
            novelty: The novelty assessment of their current research
            gap_entries: Available research gaps to match against
            top_n: Maximum number of suggestions to return (default 5)

        Returns:
            List of PivotSuggestion sorted by composite score (descending)
        """
        if not gap_entries:
            return []

        try:
            prompt = self._build_prompt(profile, novelty, gap_entries)
            llm_response = await self._call_llm(prompt)
            suggestions = self._parse_response(llm_response, gap_entries, top_n)
            return suggestions
        except Exception:
            debug_log(
                location="app/services/pivot_matcher.py:PivotMatcher:match_pivots:exception",
                message="Pivot matcher failed (exception only)",
                data={"client_initialized": self._client is not None},
                run_id="post-fix",
                hypothesis_id="H2_OPENAI_KEY_NOT_WIRED",
            )
            logger.exception("Error in pivot matching")
            return []

    def _build_prompt(
        self,
        profile: ResearchProfile,
        novelty: NoveltyAssessment,
        gap_entries: list[GapMapEntry],
    ) -> str:
        """Build the LLM prompt for pivot matching.

        Includes the researcher's OpenAlex field classification and each gap's
        taxonomy so the LLM can reason about pivot distance.
        """
        # Format each gap with its OpenAlex taxonomy when available
        gap_lines = []
        for i, g in enumerate(gap_entries):
            taxonomy_line = ""
            if g.openalex_domain or g.openalex_field:
                parts = [
                    g.openalex_domain or "?",
                    g.openalex_field or "?",
                    g.openalex_subfield or "?",
                    g.openalex_topic or "?",
                ]
                taxonomy_line = f"\n      OpenAlex: {' > '.join(parts)}"

            gap_lines.append(
                f"  [{i}] Title: {g.title}\n"
                f"      Description: {g.description}\n"
                f"      Category: {g.category or 'N/A'}\n"
                f"      Tags: {', '.join(g.tags) if g.tags else 'N/A'}"
                f"{taxonomy_line}"
            )
        gaps_text = "\n".join(gap_lines)

        # Build researcher's field position from classification
        classification = novelty.researcher_classification
        field_position = ""
        if classification and (classification.primary_domain or classification.primary_field):
            field_position = f"""
RESEARCHER'S FIELD POSITION (from OpenAlex topic taxonomy):
- Domain: {classification.primary_domain or 'Unknown'}
- Field: {classification.primary_field or 'Unknown'}
- Subfield: {classification.primary_subfield or 'Unknown'}
- Topic: {classification.primary_topic or 'Unknown'}

Use this to assess pivot distance: gaps in the same field are near pivots (lower risk, more skill transfer), while gaps in different domains are bold pivots (higher risk, more novel)."""

        return f"""You are a research strategist. Analyze the researcher's profile and match them to research gap opportunities. Prioritize gaps where the researcher's skills would be put to BETTER use—not just higher impact score, but problems that justify their expertise and have meaningful beneficiaries. Avoid recommending niche/low-significance pivots (e.g., speciating a particular species) unless the researcher explicitly seeks that.

RESEARCHER PROFILE:
- Research Question: {profile.research_question}
- Skills: {', '.join(profile.skills) if profile.skills else 'Not specified'}
- Expertise Areas: {', '.join(profile.expertise_areas) if profile.expertise_areas else 'Not specified'}
- Motivations: {', '.join(profile.motivations) if profile.motivations else 'Not specified'}
- Interests: {', '.join(profile.interests) if profile.interests else 'Not specified'}
{field_position}

CURRENT RESEARCH NOVELTY:
- Verdict: {novelty.verdict}
- Impact: {novelty.impact_assessment}
- Reasoning: {novelty.reasoning}

AVAILABLE RESEARCH GAPS:
{gaps_text}

For each gap that could be a good match, return a JSON array of objects with:
- "gap_index": integer index from the list above
- "relevance_score": float 0.0-1.0 (how well researcher's skills match this gap)
- "impact_potential": "HIGH", "MEDIUM", or "LOW" — be skeptical: avoid over-scoring niche problems. HIGH = meaningful beneficiaries, justifies expertise.
- "match_reasoning": why this gap matches the researcher's skills and motivations. Note the pivot distance (near/adjacent/bold) based on the OpenAlex taxonomy.
- "feasibility_for_researcher": CONCRETE guidance on how the researcher can leverage their specific skills ({', '.join(profile.skills) if profile.skills else 'their expertise'}) in this pivot. Be actionable: e.g. "Your X skills would allow you to..." or "Apply your background in Y to..."
- "impact_rationale": why this problem is a BETTER use of the researcher's skills than their current direction. Who benefits? Why is this worth their time? Avoid generic praise—be specific.

Return ONLY valid JSON array. No other text."""

    def _parse_response(
        self,
        llm_response: str,
        gap_entries: list[GapMapEntry],
        top_n: int,
    ) -> list[PivotSuggestion]:
        """Parse LLM response into ranked PivotSuggestion list."""
        try:
            raw = json.loads(llm_response)
        except json.JSONDecodeError:
            logger.warning("LLM returned invalid JSON for pivot matching")
            return []

        if not isinstance(raw, list):
            logger.warning("LLM response is not a JSON array")
            return []

        suggestions: list[tuple[float, PivotSuggestion]] = []

        for item in raw:
            try:
                gap_index = item.get("gap_index")
                if gap_index is None or gap_index < 0 or gap_index >= len(gap_entries):
                    continue

                relevance = float(item.get("relevance_score", 0.0))
                relevance = max(0.0, min(1.0, relevance))  # Clamp to [0, 1]

                impact = item.get("impact_potential", "MEDIUM")
                if impact not in IMPACT_WEIGHTS:
                    impact = "MEDIUM"

                suggestion = PivotSuggestion(
                    gap_entry=gap_entries[gap_index],
                    relevance_score=relevance,
                    impact_potential=impact,
                    match_reasoning=item.get("match_reasoning", ""),
                    feasibility_for_researcher=item.get("feasibility_for_researcher", ""),
                    impact_rationale=item.get("impact_rationale", ""),
                )

                composite_score = relevance * IMPACT_WEIGHTS[impact]
                suggestions.append((composite_score, suggestion))
            except (ValueError, KeyError, TypeError):
                logger.warning("Skipping malformed pivot match item: %s", item)
                continue

        # Sort by composite score descending
        suggestions.sort(key=lambda x: x[0], reverse=True)

        return [s for _, s in suggestions[:top_n]]
