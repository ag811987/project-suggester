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

# True research gaps (Convergent, Homeworld, 3ie) prioritized over open questions (Wikenigma)
_SOURCE_PRIORITY_BOOST = 0.15
_PRIORITY_SOURCES = frozenset({"convergent", "homeworld", "3ie"})


class PivotMatcher:
    """Matches researchers to potential research pivots using LLM analysis."""

    def __init__(self, openai_client: AsyncOpenAI | None = None):
        self._client = openai_client

    async def _call_llm(self, prompt: str) -> str:
        """Call the LLM with JSON array output and a single retry on parse failure.

        Does not use response_format=json_object so the model can return a top-level
        JSON array as required by the prompt.
        """
        if self._client is None:
            self._client = AsyncOpenAI(api_key=get_settings().openai_api_key)

        settings = get_settings()
        for attempt in range(2):
            response = await self._client.chat.completions.create(
                model=settings.openai_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_tokens=2000,
                timeout=60,
            )
            content = (response.choices[0].message.content or "").strip()
            # Strip markdown code block if present
            if content.startswith("```"):
                lines = content.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                content = "\n".join(lines)
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

CRITICAL - AVOID FORCED FIT:
Do NOT mechanically append the researcher's species, taxon, or study system to every gap.
Only suggest a gap if the specific project genuinely makes sense for their skills AND the topic.
If forcing their study system into a gap would be nonsensical (e.g., studying magnetoreception
in a species that doesn't exhibit it), SKIP that gap or propose a project that genuinely uses
their skills (e.g., comparative genomics of magnetoreception loss across bird lineages).
Match their SKILLS to the gap—not their taxon label.

CURRENT RESEARCH NOVELTY:
- Verdict: {novelty.verdict}
- Impact: {novelty.expected_impact_assessment}
- Reasoning: {novelty.reasoning}

AVAILABLE RESEARCH GAPS:
{gaps_text}

PRIORITY SOURCES: Gaps from Convergent Research, Homeworld Bio, and 3ie are curated research gaps (true R&D needs). Wikenigma entries are open questions. When relevance is similar, prefer gaps from Convergent, Homeworld, or 3ie.

For each gap that could be a good match, propose a SPECIFIC, CONCRETE PROJECT this researcher can work on within that topic. The output "specific_title" becomes the main heading—it should be the actionable project (e.g. "Developing low-cost soil moisture sensors for degraded grasslands"), NOT the broad gap title (e.g. "Challenges in Tracking and Restoring Resilient Ecosystems").

Return a JSON array of objects with:
- "gap_index": integer index from the list above
- "specific_title": concise title of the specific project (the actionable work the researcher can do within this gap)
- "specific_description": 2-3 sentences explaining the broader research gap this project addresses, and how this specific project contributes to it. Do not quote the gap map verbatim—explain in context.
- "relevance_score": float 0.0-1.0 (how well researcher's skills match this specific project)
- "impact_potential": "HIGH", "MEDIUM", or "LOW" — be skeptical: avoid over-scoring niche problems. HIGH = meaningful beneficiaries, justifies expertise.
- "match_reasoning": why this SPECIFIC PROJECT matches the researcher's skills and motivations. Note the pivot distance (near/adjacent/bold) based on the OpenAlex taxonomy.
- "feasibility_for_researcher": how they can execute this SPECIFIC PROJECT. Be actionable: e.g. "Your X skills would allow you to..." or "Apply your background in Y to..."
- "impact_rationale": impact of this SPECIFIC PROJECT and how it contributes to the broader gap topic. Who benefits? Why is this worth their time?

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

        # Unwrap: accept top-level array or object with a list under common keys
        items: list[dict] = []
        if isinstance(raw, list):
            items = raw
        elif isinstance(raw, dict):
            for key in ("suggestions", "items", "matches", "results", "pivots"):
                val = raw.get(key)
                if isinstance(val, list):
                    items = val
                    break
            if not items:
                logger.warning(
                    "LLM response is not a JSON array; got dict with keys: %s",
                    list(raw.keys()),
                )
                return []
        else:
            logger.warning(
                "LLM response is not a JSON array; got type: %s",
                type(raw).__name__,
            )
            return []

        top_n = max(1, top_n)
        suggestions: list[tuple[float, PivotSuggestion]] = []

        for item in items:
            try:
                if not isinstance(item, dict):
                    continue
                gap_index = item.get("gap_index")
                if gap_index is None:
                    continue
                try:
                    gap_index = int(gap_index)
                except (ValueError, TypeError):
                    continue
                if gap_index < 0 or gap_index >= len(gap_entries):
                    continue

                try:
                    relevance = float(item.get("relevance_score", 0.0))
                except (ValueError, TypeError):
                    relevance = 0.0
                relevance = max(0.0, min(1.0, relevance))  # Clamp to [0, 1]

                impact = item.get("impact_potential", "MEDIUM")
                if impact not in IMPACT_WEIGHTS:
                    impact = "MEDIUM"

                specific_title = item.get("specific_title")
                if isinstance(specific_title, str):
                    specific_title = specific_title.strip() or None
                else:
                    specific_title = None

                specific_description = item.get("specific_description")
                if isinstance(specific_description, str):
                    specific_description = specific_description.strip() or None
                else:
                    specific_description = None

                suggestion = PivotSuggestion(
                    gap_entry=gap_entries[gap_index],
                    specific_title=specific_title,
                    specific_description=specific_description,
                    relevance_score=relevance,
                    impact_potential=impact,
                    match_reasoning=item.get("match_reasoning", ""),
                    feasibility_for_researcher=item.get("feasibility_for_researcher", ""),
                    impact_rationale=item.get("impact_rationale", ""),
                )

                composite_score = relevance * IMPACT_WEIGHTS[impact]
                if gap_entries[gap_index].source in _PRIORITY_SOURCES:
                    composite_score += _SOURCE_PRIORITY_BOOST
                suggestions.append((composite_score, suggestion))
            except (ValueError, KeyError, TypeError):
                logger.warning("Skipping malformed pivot match item: %s", item)
                continue

        # Sort by composite score descending
        suggestions.sort(key=lambda x: x[0], reverse=True)

        return [s for _, s in suggestions[:top_n]]
