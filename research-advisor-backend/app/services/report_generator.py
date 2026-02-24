"""
Report Generator service for producing research recommendations.

Determines CONTINUE/PIVOT/UNCERTAIN recommendation based on novelty and
expected impact, then generates a structured report using LLM.
"""

import json
import logging

from openai import AsyncOpenAI

from app.config import get_settings
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
        """Call the LLM with structured JSON output and a single retry on parse failure."""
        if self._client is None:
            self._client = AsyncOpenAI(api_key=get_settings().openai_api_key)

        settings = get_settings()
        for attempt in range(2):
            response = await self._client.chat.completions.create(
                model=settings.openai_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,
                max_tokens=3500,
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
                        "Return ONLY a valid JSON object. No markdown, no explanation.\n\n"
                        + prompt
                    )
                    continue
                return "{}"
        return "{}"

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
            # Pivot section is always built from template or short fallback, never LLM
            report_sections = report_sections.model_copy(
                update={"pivot_section": self._build_pivot_section(pivot_suggestions, recommendation)}
            )
            narrative = self._sections_to_narrative(report_sections, recommendation)
        except Exception:
            debug_log(
                location="app/services/report_generator.py:ReportGenerator:generate_report:exception",
                message="Report generator failed (exception only)",
                data={"client_initialized": self._client is not None},
                run_id="post-fix",
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

    def _build_pivot_section(
        self,
        pivot_suggestions: list[PivotSuggestion],
        recommendation: RecommendationType,
    ) -> str:
        """Build pivot section from structured suggestions or short fallback.

        When suggestions exist: template-driven blocks (title, link, match_reasoning,
        impact_rationale). When none: short static fallback with repo links.
        """
        if pivot_suggestions:
            intro = "We matched you to the following gap map projects."
            blocks = []
            for p in pivot_suggestions[:5 if recommendation == "PIVOT" else 2]:
                title = p.gap_entry.title
                url = p.gap_entry.source_url or ""
                link = f"[{title}]({url})" if url else title
                block = f"### {link}\n\n"
                block += f"**Why you're a good match:** {p.match_reasoning}\n\n"
                block += f"**Why this is higher impact:** {p.impact_rationale}\n\n"
                if p.feasibility_for_researcher:
                    block += f"**How to use your skills:** {p.feasibility_for_researcher}\n\n"
                blocks.append(block)
            return f"{intro}\n\n" + "\n".join(blocks)
        # Short fallback when no suggestions
        return (
            "No specific gap map projects matched your profile. "
            "You can browse [Convergent Research Gap Map](https://www.gap-map.org/), "
            "[3ie Evidence Gap Maps](https://gapmaps.3ieimpact.org/), or "
            "[Homeworld Bio](https://homeworld.bio/) for ideas."
        )

    def _build_structured_prompt(
        self,
        profile: ResearchProfile,
        novelty: NoveltyAssessment,
        pivot_suggestions: list[PivotSuggestion],
        recommendation: RecommendationType,
    ) -> str:
        """Build the LLM prompt to produce five structured sections."""
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

        # Pivot section is built from template/fallback, not LLM — always set to ""
        pivot_instruction = """
4. "pivot_section": Set to empty string "". (Pivot content is generated from structured data.)"""

        gap_map_context = ""
        if pivot_suggestions:
            gap_map_context = "\n\nHIGH-IMPACT GAP MAP PROBLEMS (for comparison—these are curated, high-impact research gaps):\n" + "\n".join(
                f"  - {p.gap_entry.title}: {p.gap_entry.description[:150]}..."
                if len(p.gap_entry.description or "") > 150
                else f"  - {p.gap_entry.title}: {p.gap_entry.description or 'N/A'}"
                for p in pivot_suggestions[:5]
            )

        confidence = self._calculate_confidence(novelty, recommendation)

        verdict_instruction = f"""5. "verdict_section": A concise (2-4 sentence) FINAL VERDICT. This appears at the top of the report.
   - State clearly: "We recommend you **{recommendation.lower()}** your current research direction."
   - Summarize the key reason in one sentence.
   - State the confidence level: {confidence * 100:.0f}%.
   - If CONTINUE: acknowledge what could be improved or what the alternative direction offers.
   - If PIVOT: be encouraging about the pivot and specific about next steps.
   - If UNCERTAIN: state what additional information would resolve the uncertainty."""

        return f"""Generate a structured research advisory report as JSON with five sections. Write as a research strategist—consider both scholarly and practical impact, not just publication metrics. Be appropriately critical: method-to-new-population research is usually incremental (MARGINAL), not novel. Avoid over-scoring niche problems; ask whether the research justifies the researcher's skills and who actually benefits.

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

IMPACT ON THE FIELD (discipline, methods, tools):
- Impact on the field: {novelty.expected_impact_assessment}
- Reasoning: {novelty.expected_impact_reasoning}

GLOBAL IMPACT (society, policy, population):
- Global impact: {novelty.real_world_impact_assessment}
- Reasoning: {novelty.real_world_impact_reasoning}

RECOMMENDATION: {recommendation}

PIVOT SUGGESTIONS:
{pivots_text or 'None available.'}
{gap_map_context}

KEY CITATIONS:
{citations_text or 'No specific citations available.'}

Respond with ONLY valid JSON (no markdown code fences) containing these five keys:

1. "novelty_section": Markdown text analyzing whether the question is novel, marginal, or solved.
   - Include the verdict and score
   - When MARGINAL/SOLVED: reference specific papers/literature that have addressed this question
   - Include FWCI context as secondary information

2. "impact_section": Markdown text for IMPACT ON THE FIELD — how this research affects the discipline, methods, or tools.
   - This is NOT the literature impact — it is the predicted impact of the researcher's own work
   - Include the impact level ({novelty.expected_impact_assessment}) and reasoning
   - Reference the researcher's skills and how they contribute to potential impact

3. "real_world_impact_section": Markdown text for GLOBAL IMPACT — effect on society, policy, and population. Apply HARSH criteria.
   - The structured assessment says: {novelty.real_world_impact_assessment} — {novelty.real_world_impact_reasoning}
   - Apply these tests:
     * SCALE: What fraction of 8 billion people are affected? Thousands = LOW, Millions = MEDIUM, Billions = HIGH.
     * TOOLING: Does this create a new method/tool/framework others outside the subfield can use? If not, it cannot be HIGH.
     * NEWS TEST: Would a non-specialist journalist write about this? If only specialist journals care, it is LOW.
     * COMPARE: Is this comparable to curing a disease, discovering a new material, or preventing famine? If not, do not call it HIGH.
   - Be specific about who benefits, how many people, and to what degree.
   - If real-world impact is LOW, say so clearly. Do not inflate.
   - Compare to gap map problems if available — are those more impactful?

{pivot_instruction}

{verdict_instruction}

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
            verdict_section=data.get("verdict_section", ""),
        )

    def _sections_to_narrative(
        self, sections: ReportSections, recommendation: RecommendationType
    ) -> str:
        """Combine structured sections into a single narrative for backwards compatibility."""
        parts = []
        if sections.verdict_section:
            parts.append(f"## Final Verdict\n\n{sections.verdict_section}")
        parts.extend([
            f"## Novelty Analysis\n\n{sections.novelty_section}",
            f"## Impact on the field\n\n{sections.impact_section}",
        ])
        if sections.real_world_impact_section:
            parts.append(f"## Global impact\n\n{sections.real_world_impact_section}")
        if sections.pivot_section:
            heading = "Pivot Suggestions" if recommendation == "PIVOT" else "Alternative Direction"
            parts.append(f"## {heading}\n\n{sections.pivot_section}")
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

        impact_section = f"""**Impact on the field: {novelty.expected_impact_assessment}**

{novelty.expected_impact_reasoning}"""

        # Build substantive real-world impact from structured assessment
        rw_level = novelty.real_world_impact_assessment
        rw_reasoning = novelty.real_world_impact_reasoning
        if rw_reasoning:
            real_world_impact_section = (
                f"**Global impact: {rw_level}**\n\n"
                f"{rw_reasoning}"
            )
        else:
            impact_domains = []
            if novelty.research_decomposition:
                impact_domains = novelty.research_decomposition.potential_impact_domains
            if impact_domains:
                real_world_impact_section = (
                    f"**Global impact: {rw_level}**\n\n"
                    f"Potential impact domains: {', '.join(impact_domains)}.\n\n"
                    f"Impact on the field: {novelty.expected_impact_assessment} — "
                    f"{novelty.expected_impact_reasoning}"
                )
            else:
                real_world_impact_section = (
                    f"**Global impact: {rw_level}**\n\n"
                    f"Based on the impact on the field ({novelty.expected_impact_assessment}): "
                    f"{novelty.expected_impact_reasoning}"
                )

        pivot_section = self._build_pivot_section(pivot_suggestions, recommendation)

        # Build verdict section from available assessments
        if recommendation == "CONTINUE":
            verdict_section = (
                f"**We recommend you continue** your current research direction. "
                f"The novelty verdict is {novelty.verdict} with a score of {novelty.score:.0%}, "
                f"and expected impact is {novelty.expected_impact_assessment}. "
                f"Real-world impact: {rw_level}."
            )
        elif recommendation == "PIVOT":
            verdict_section = (
                f"**We recommend you consider pivoting** from your current research direction. "
                f"The novelty verdict is {novelty.verdict}, suggesting this area is already well-explored. "
                f"Expected impact: {novelty.expected_impact_assessment}. "
                f"Your skills could have greater impact in an alternative direction."
            )
        else:
            verdict_section = (
                f"**We are uncertain** about the best path forward. "
                f"Novelty: {novelty.verdict} (score: {novelty.score:.0%}). "
                f"Expected impact: {novelty.expected_impact_assessment}. "
                f"Consider gathering more data or consulting domain experts."
            )

        return ReportSections(
            novelty_section=novelty_section,
            impact_section=impact_section,
            real_world_impact_section=real_world_impact_section,
            pivot_section=pivot_section,
            verdict_section=verdict_section,
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
