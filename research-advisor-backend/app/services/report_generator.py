"""
Report Generator service for producing research recommendations.

Determines CONTINUE/PIVOT/UNCERTAIN recommendation based on novelty and
expected impact, then generates a structured report using LLM.
"""

import json
import logging
import os

from openai import AsyncOpenAI

from app.debug_log import debug_log
from app.models.schemas import (
    Citation,
    NoveltyAssessment,
    PivotSuggestion,
    ReportSections,
    ResearchProfile,
    ResearchRecommendation,
    RecommendationType,
)

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates research recommendation reports."""

    def __init__(self, openai_client: AsyncOpenAI | None = None):
        self._client = openai_client

    async def _call_llm(self, prompt: str) -> str:
        """Call the LLM with a prompt and return the response content."""
        if self._client is None:
            debug_log(
                location="app/services/report_generator.py:ReportGenerator:_call_llm:init_client",
                message="Initializing OpenAI client for report generator",
                data={"has_openai_api_key_env": bool(os.getenv("OPENAI_API_KEY"))},
                run_id="pre-fix",
                hypothesis_id="H2_OPENAI_KEY_NOT_WIRED",
            )
            self._client = AsyncOpenAI()

        response = await self._client.chat.completions.create(
            model="gpt-4-0125-preview",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=3000,
        )
        return response.choices[0].message.content or ""

    async def generate_report(
        self,
        profile: ResearchProfile,
        novelty: NoveltyAssessment,
        pivot_suggestions: list[PivotSuggestion],
    ) -> ResearchRecommendation:
        """
        Generate a complete research recommendation report.

        Decision logic:
        - If novelty in [SOLVED, MARGINAL] OR expected_impact == LOW → PIVOT
        - If novelty == NOVEL AND expected_impact in [HIGH, MEDIUM] → CONTINUE
        - Otherwise → UNCERTAIN

        Args:
            profile: The researcher's profile
            novelty: The novelty assessment
            pivot_suggestions: Matched pivot suggestions

        Returns:
            Complete ResearchRecommendation with narrative report and structured sections
        """
        recommendation = self._determine_recommendation(novelty)
        confidence = self._calculate_confidence(novelty, recommendation)
        citations = self._collect_citations(novelty)

        report_sections = None
        try:
            prompt = self._build_structured_prompt(
                profile, novelty, pivot_suggestions, recommendation
            )
            raw = await self._call_llm(prompt)
            report_sections = self._parse_sections(raw)
            narrative = self._sections_to_narrative(report_sections, recommendation)
        except Exception:
            debug_log(
                location="app/services/report_generator.py:ReportGenerator:generate_report:exception",
                message="Report generator failed (exception only)",
                data={"has_openai_api_key_env": bool(os.getenv("OPENAI_API_KEY"))},
                run_id="pre-fix",
                hypothesis_id="H2_OPENAI_KEY_NOT_WIRED",
            )
            logger.exception("Error generating structured report via LLM")
            narrative = self._build_fallback_narrative(
                profile, novelty, pivot_suggestions, recommendation
            )
            report_sections = self._fallback_sections(
                profile, novelty, pivot_suggestions, recommendation
            )

        return ResearchRecommendation(
            recommendation=recommendation,
            confidence=confidence,
            narrative_report=narrative,
            report_sections=report_sections,
            novelty_assessment=novelty,
            pivot_suggestions=pivot_suggestions,
            evidence_citations=citations,
        )

    def _determine_recommendation(
        self, novelty: NoveltyAssessment
    ) -> RecommendationType:
        """
        Determine the recommendation based on novelty verdict and expected impact.

        Rules:
        - SOLVED or MARGINAL verdict → PIVOT
        - LOW expected impact → PIVOT
        - NOVEL + HIGH/MEDIUM expected impact → CONTINUE
        - Everything else → UNCERTAIN
        """
        if novelty.verdict in ("SOLVED", "MARGINAL"):
            return "PIVOT"

        if novelty.expected_impact_assessment == "LOW":
            return "PIVOT"

        if novelty.verdict == "NOVEL" and novelty.expected_impact_assessment in ("HIGH", "MEDIUM"):
            return "CONTINUE"

        return "UNCERTAIN"

    def _calculate_confidence(
        self,
        novelty: NoveltyAssessment,
        recommendation: RecommendationType,
    ) -> float:
        """Calculate confidence score for the recommendation."""
        base_confidence = novelty.score

        if recommendation == "CONTINUE" and novelty.verdict == "NOVEL":
            confidence = min(1.0, base_confidence + 0.1)
        elif recommendation == "PIVOT" and novelty.verdict in ("SOLVED", "MARGINAL"):
            confidence = min(1.0, (1.0 - base_confidence) + 0.1)
        elif recommendation == "UNCERTAIN":
            confidence = 0.5
        else:
            confidence = base_confidence

        return round(max(0.0, min(1.0, confidence)), 2)

    def _collect_citations(self, novelty: NoveltyAssessment) -> list[Citation]:
        """Collect all citations from the novelty assessment."""
        return list(novelty.evidence)

    def _build_structured_prompt(
        self,
        profile: ResearchProfile,
        novelty: NoveltyAssessment,
        pivot_suggestions: list[PivotSuggestion],
        recommendation: RecommendationType,
    ) -> str:
        """Build the LLM prompt to produce three structured sections."""
        pivots_text = ""
        if pivot_suggestions:
            pivots_text = "\n".join(
                f"  {i+1}. {p.gap_entry.title}\n"
                f"     Source: {p.gap_entry.source_url}\n"
                f"     Relevance: {float(p.relevance_score):.2f}, Impact: {p.impact_potential}\n"
                f"     Why this matches: {p.match_reasoning}\n"
                f"     How to use your skills: {p.feasibility_for_researcher}\n"
                f"     Impact rationale: {p.impact_rationale}"
                for i, p in enumerate(pivot_suggestions)
            )

        citations_text = ""
        if novelty.evidence:
            citations_text = "\n".join(
                f"  - {c.title} ({c.year or 'N/A'}). DOI: {c.doi or 'N/A'}"
                for c in novelty.evidence
            )

        fwci_text = f"Average FWCI: {novelty.average_fwci}" if novelty.average_fwci else "FWCI: Not available"

        include_pivot = recommendation == "PIVOT" and (pivot_suggestions or True)

        pivot_instruction = ""
        if include_pivot:
            if pivot_suggestions:
                pivot_instruction = f"""4. "pivot_section": Markdown text for pivot suggestions. For EACH pivot:
   (a) What to pivot to
   (b) How to leverage skills: {', '.join(profile.skills) if profile.skills else 'their expertise'}
   (c) Next steps or links
   If recommendation is not PIVOT, set this to empty string ""."""
            else:
                pivot_instruction = """
4. "pivot_section": Since no specific pivots are available, suggest general directions to explore and repositories to check (Convergent Research, Homeworld Bio, 3ie Gap Maps)."""
        else:
            pivot_instruction = """
4. "pivot_section": Set to empty string "" since recommendation is not PIVOT."""

        gap_map_context = ""
        if pivot_suggestions:
            gap_map_context = "\n\nHIGH-IMPACT GAP MAP PROBLEMS (for comparison—these are curated, high-impact research gaps):\n" + "\n".join(
                f"  - {p.gap_entry.title}: {p.gap_entry.description[:150]}..."
                if len(p.gap_entry.description or "") > 150
                else f"  - {p.gap_entry.title}: {p.gap_entry.description or 'N/A'}"
                for p in pivot_suggestions[:5]
            )

        return f"""Generate a structured research advisory report as JSON with four sections. Write as a research strategist—consider both scholarly and practical impact, not just publication metrics. Be appropriately critical: method-to-new-population research is usually incremental (MARGINAL), not novel. Avoid over-scoring niche problems; ask whether the research justifies the researcher's skills and who actually benefits.

RESEARCHER:
- Research Question: {profile.research_question}
- Problem: {profile.problem_description or 'Not specified'}
- Skills: {', '.join(profile.skills) if profile.skills else 'Not specified'}
- Expertise: {', '.join(profile.expertise_areas) if profile.expertise_areas else 'Not specified'}
- Motivations: {', '.join(profile.motivations) if profile.motivations else 'Not specified'}

NOVELTY ANALYSIS:
- Score: {novelty.score}/1.0
- Verdict: {novelty.verdict}
- {fwci_text}
- Related Papers: {novelty.related_papers_count}
- Literature Impact (FWCI-based): {novelty.impact_assessment} — {novelty.impact_reasoning}
- Novelty Reasoning: {novelty.reasoning}

EXPECTED IMPACT OF THIS RESEARCH:
- Expected Impact: {novelty.expected_impact_assessment}
- Expected Impact Reasoning: {novelty.expected_impact_reasoning}

RECOMMENDATION: {recommendation}

PIVOT SUGGESTIONS:
{pivots_text or 'None available.'}
{gap_map_context}

KEY CITATIONS:
{citations_text or 'No specific citations available.'}

Respond with ONLY valid JSON (no markdown code fences) containing these four keys:

1. "novelty_section": Markdown text analyzing whether the question is novel, marginal, or solved.
   - Include the verdict and score
   - When MARGINAL/SOLVED: reference specific papers/literature that have addressed this question
   - Include FWCI context as secondary information

2. "impact_section": Markdown text analyzing the EXPECTED IMPACT of this specific research if completed.
   - This is NOT the literature impact — it is the predicted impact of the researcher's own work
   - Include the expected impact level ({novelty.expected_impact_assessment}) and reasoning
   - Reference the researcher's skills and how they contribute to potential impact

3. "real_world_impact_section": Markdown text assessing REAL-WORLD IMPACT. This is critical.
   - How does the world change if they answer this question? What are the downstream consequences?
   - Future knowledge production: what becomes possible? Problem solving: who can act on this?
   - Is this research justified vis-a-vis the gap map problems above? Our gap maps are curated HIGH-IMPACT problems. If the researcher's question has lower real-world impact than typical gap map entries, say so clearly. Would their skills be better used on a gap map problem?
   - Be specific: who benefits, how, and to what degree? Avoid generic praise.

{pivot_instruction}

Use markdown formatting within each section. Be specific and actionable.
Each section should be self-contained and readable on its own."""

    def _parse_sections(self, raw: str) -> ReportSections:
        """Parse LLM response into structured sections."""
        # Strip potential markdown code fences
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        data = json.loads(cleaned)
        return ReportSections(
            novelty_section=data.get("novelty_section", ""),
            impact_section=data.get("impact_section", ""),
            real_world_impact_section=data.get("real_world_impact_section", ""),
            pivot_section=data.get("pivot_section", ""),
        )

    def _sections_to_narrative(
        self, sections: ReportSections, recommendation: RecommendationType
    ) -> str:
        """Combine structured sections into a single narrative for backwards compatibility."""
        parts = [
            f"## Novelty Analysis\n\n{sections.novelty_section}",
            f"## Expected Impact\n\n{sections.impact_section}",
        ]
        if sections.real_world_impact_section:
            parts.append(f"## Real-World Impact\n\n{sections.real_world_impact_section}")
        if sections.pivot_section:
            parts.append(f"## Pivot Suggestions\n\n{sections.pivot_section}")
        return "\n\n---\n\n".join(parts)

    def _fallback_sections(
        self,
        profile: ResearchProfile,
        novelty: NoveltyAssessment,
        pivot_suggestions: list[PivotSuggestion],
        recommendation: RecommendationType,
    ) -> ReportSections:
        """Build fallback structured sections when LLM is unavailable."""
        fwci_info = (
            f"Average FWCI: {novelty.average_fwci:.2f}"
            if novelty.average_fwci is not None
            else "FWCI data unavailable"
        )

        novelty_section = f"""**Verdict: {novelty.verdict}** (Score: {novelty.score}/1.0)

{novelty.reasoning}

**Literature Context:**
- Related Papers Found: {novelty.related_papers_count}
- {fwci_info}
- Literature Impact: {novelty.impact_assessment} — {novelty.impact_reasoning}"""

        impact_section = f"""**Expected Impact: {novelty.expected_impact_assessment}**

{novelty.expected_impact_reasoning}"""

        real_world_impact_section = (
            "Real-world impact assessment requires LLM analysis. "
            "Consider: How does the world change if this question is answered? "
            "Is this justified vs. high-impact gap map problems?"
        )

        pivot_section = ""
        if recommendation == "PIVOT":
            if pivot_suggestions:
                lines = []
                for p in pivot_suggestions:
                    lines.append(f"- **{p.gap_entry.title}** (Relevance: {float(p.relevance_score):.2f}, Impact: {p.impact_potential})")
                    lines.append(f"  - Why this matches: {p.match_reasoning}")
                    lines.append(f"  - How to use your skills: {p.feasibility_for_researcher}")
                    lines.append(f"  - [View source]({p.gap_entry.source_url})")
                pivot_section = chr(10).join(lines)
            else:
                pivot_section = (
                    "Specific pivot suggestions could not be generated. "
                    "Consider exploring Convergent Research, Homeworld Bio, or "
                    "3ie Impact Evidence Gap Maps for opportunities aligned with your skills."
                )

        return ReportSections(
            novelty_section=novelty_section,
            impact_section=impact_section,
            real_world_impact_section=real_world_impact_section,
            pivot_section=pivot_section,
        )

    def _build_fallback_narrative(
        self,
        profile: ResearchProfile,
        novelty: NoveltyAssessment,
        pivot_suggestions: list[PivotSuggestion],
        recommendation: RecommendationType,
    ) -> str:
        """Build a basic narrative report when LLM is unavailable."""
        sections = self._fallback_sections(
            profile, novelty, pivot_suggestions, recommendation
        )
        return self._sections_to_narrative(sections, recommendation)
