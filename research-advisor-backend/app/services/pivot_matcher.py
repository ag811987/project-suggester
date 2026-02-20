"""
Pivot Matcher service for matching researchers to research gaps.

Uses LLM to match a researcher's skills and motivations to gap map entries,
ranking by relevance × impact potential.
"""

import json
import logging

from openai import AsyncOpenAI

from app.models.schemas import (
    GapMapEntry,
    ImpactLevel,
    NoveltyAssessment,
    PivotSuggestion,
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
        """Call the LLM with a prompt and return the response content."""
        if self._client is None:
            self._client = AsyncOpenAI()

        response = await self._client.chat.completions.create(
            model="gpt-4-0125-preview",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=2000,
        )
        return response.choices[0].message.content or ""

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
            return self._parse_response(llm_response, gap_entries, top_n)
        except Exception:
            logger.exception("Error in pivot matching")
            return []

    def _build_prompt(
        self,
        profile: ResearchProfile,
        novelty: NoveltyAssessment,
        gap_entries: list[GapMapEntry],
    ) -> str:
        """Build the LLM prompt for pivot matching."""
        gaps_text = "\n".join(
            f"  [{i}] Title: {g.title}\n"
            f"      Description: {g.description}\n"
            f"      Category: {g.category or 'N/A'}\n"
            f"      Tags: {', '.join(g.tags) if g.tags else 'N/A'}"
            for i, g in enumerate(gap_entries)
        )

        return f"""You are a research strategist. Analyze the researcher's profile and match them to research gap opportunities, considering both scholarly and practical impact potential.

RESEARCHER PROFILE:
- Research Question: {profile.research_question}
- Skills: {', '.join(profile.skills) if profile.skills else 'Not specified'}
- Expertise Areas: {', '.join(profile.expertise_areas) if profile.expertise_areas else 'Not specified'}
- Motivations: {', '.join(profile.motivations) if profile.motivations else 'Not specified'}
- Interests: {', '.join(profile.interests) if profile.interests else 'Not specified'}

CURRENT RESEARCH NOVELTY:
- Verdict: {novelty.verdict}
- Impact: {novelty.impact_assessment}
- Reasoning: {novelty.reasoning}

AVAILABLE RESEARCH GAPS:
{gaps_text}

For each gap that could be a good match, return a JSON array of objects with:
- "gap_index": integer index from the list above
- "relevance_score": float 0.0-1.0 (how well researcher's skills match this gap)
- "impact_potential": "HIGH", "MEDIUM", or "LOW"
- "match_reasoning": why this gap matches the researcher's skills and motivations
- "feasibility_for_researcher": CONCRETE guidance on how the researcher can leverage their specific skills ({', '.join(profile.skills) if profile.skills else 'their expertise'}) in this pivot. Be actionable: e.g. "Your X skills would allow you to..." or "Apply your background in Y to..."
- "impact_rationale": why this problem has higher impact potential than the researcher's current direction

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
