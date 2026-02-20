"""Novelty & Impact Analyzer service.

Determines whether a research question is novel, marginal, or already solved
by querying OpenAlex for related papers and using an LLM to interpret the results.
"""

import json

from openai import AsyncOpenAI
from loguru import logger

from app.models.schemas import (
    NoveltyAssessment,
    Citation,
    ResearchDecomposition,
    ResearchProfile,
)
from app.services.openalex_client import OpenAlexClient

EXPERT_SYSTEM_PROMPT = """You are a research strategist who evaluates whether research directions are worth pursuing. You assess novelty, clarity of the question, and potential impact—considering both scholarly and non-academic outcomes (e.g., practical, policy, societal). You combine bibliometric data with domain judgment. You:
- Break down research problems to understand core questions and motivations.
- Judge whether related papers address the SAME core questions or only tangentially related ones.
- Assess significance: would answering this question advance knowledge or practice in a meaningful way?
- Make nuanced calls; do not over-weight citation metrics—consider emerging fields and practical impact.
Respond with valid JSON only, no markdown or code fences."""


class NoveltyAnalyzer:
    """Analyzes research novelty and impact using OpenAlex + LLM.

    Steps:
        1. Query OpenAlex for related papers.
        2. Calculate FWCI statistics.
        3. Ask an LLM to determine a verdict (SOLVED/MARGINAL/NOVEL/UNCERTAIN).
        4. Determine impact level from FWCI thresholds.
        5. Return a NoveltyAssessment with evidence.
    """

    # FWCI thresholds for impact assessment
    HIGH_FWCI_THRESHOLD = 1.5
    LOW_FWCI_THRESHOLD = 0.8

    def __init__(
        self,
        openalex_email: str,
        openai_api_key: str,
        openalex_api_key: str | None = None,
        openai_model: str = "gpt-4-0125-preview",
        use_semantic_search: bool = False,
    ):
        self._openalex_client = OpenAlexClient(
            email=openalex_email,
            api_key=openalex_api_key,
        )
        self._openai_client = AsyncOpenAI(api_key=openai_api_key)
        self._openai_model = openai_model
        self._use_semantic_search = use_semantic_search

    async def analyze(
        self,
        research_question: str,
        profile: ResearchProfile | None = None,
    ) -> NoveltyAssessment:
        """Analyze a research question for novelty and impact.

        Args:
            research_question: The research question to analyze.
            profile: Optional researcher profile for expected impact assessment.

        Returns:
            NoveltyAssessment with verdict, score, impact, evidence, and reasoning.
        """
        # Step 1: Decompose research problem
        decomposition = await self._decompose_research(research_question, profile)

        # Step 2: Query OpenAlex
        try:
            papers = await self._search_papers(research_question, decomposition)
        except Exception as e:
            logger.error(f"OpenAlex search failed: {e}")
            return self._uncertain_assessment(
                reasoning=f"Could not query literature database: {e}",
                decomposition=decomposition,
            )

        # If no papers found, return UNCERTAIN
        if not papers:
            return self._uncertain_assessment(
                reasoning="No related papers found in OpenAlex. Unable to assess novelty.",
                decomposition=decomposition,
            )

        # Step 3: Calculate FWCI statistics
        stats = self._openalex_client.calculate_fwci_stats(papers)

        # Step 4: Build citations
        citations = self._build_citations(papers)

        # Step 5: Use LLM to determine verdict
        try:
            llm_result = await self._get_llm_verdict(
                research_question, decomposition, papers, stats
            )
            verdict = llm_result["verdict"]
            score = llm_result["score"]
            reasoning = llm_result["reasoning"]
        except Exception as e:
            logger.error(f"LLM verdict failed: {e}")
            verdict = "UNCERTAIN"
            score = 0.5
            reasoning = f"LLM analysis unavailable: {e}. Assessment based on bibliometric data only."

        # Step 6: LLM-based impact assessment (or fallback to FWCI thresholds)
        try:
            impact_level, impact_reasoning = await self._assess_impact_llm(
                research_question, decomposition, profile, papers, stats, verdict
            )
        except Exception as e:
            logger.error(f"Impact LLM assessment failed: {e}")
            impact_level = self._determine_impact_level(stats["average_fwci"])
            if stats["average_fwci"] is None:
                impact_level = "UNCERTAIN"
            impact_reasoning = self._build_impact_reasoning(stats, impact_level)

        # Step 7: Assess expected impact of the researcher's work
        expected_impact, expected_reasoning = await self._assess_expected_impact(
            research_question,
            profile,
            verdict,
            score,
            papers,
            stats,
            decomposition,
        )

        return NoveltyAssessment(
            score=score,
            verdict=verdict,
            evidence=citations,
            reasoning=reasoning,
            related_papers_count=len(papers),
            average_fwci=stats["average_fwci"],
            fwci_percentile=stats["fwci_percentile"],
            citation_percentile_min=stats["citation_percentile_min"],
            citation_percentile_max=stats["citation_percentile_max"],
            impact_assessment=impact_level,
            impact_reasoning=impact_reasoning,
            expected_impact_assessment=expected_impact,
            expected_impact_reasoning=expected_reasoning,
            research_decomposition=decomposition,
        )

    async def _decompose_research(
        self,
        research_question: str,
        profile: ResearchProfile | None,
    ) -> ResearchDecomposition:
        """Decompose research problem into core questions, motivations, and impact domains."""
        profile_text = ""
        if profile:
            parts = []
            if profile.problem_description:
                parts.append(f"Problem description: {profile.problem_description}")
            if profile.motivations:
                parts.append(f"Motivations: {', '.join(profile.motivations)}")
            if profile.skills:
                parts.append(f"Skills: {', '.join(profile.skills)}")
            if profile.expertise_areas:
                parts.append(f"Expertise: {', '.join(profile.expertise_areas)}")
            profile_text = "\n".join(parts) if parts else ""

        context_block = f"Additional context:\n{profile_text}\n\n" if profile_text else ""
        prompt = f"""Decompose this research question for literature analysis.

Research Question: {research_question}
{context_block}
Extract structured JSON with:
- core_questions: 1-3 fundamental questions the research aims to answer
- core_motivations: What drives this research (e.g., fundamental understanding, practical impact, method innovation)
- potential_impact_domains: Who/what benefits if this succeeds (e.g., clinicians, policy, basic science)
- key_concepts: Key concepts/terms for search (e.g., CRISPR, gene editing)

Respond with ONLY valid JSON (no markdown, no code fences)."""

        try:
            response = await self._openai_client.chat.completions.create(
                model=self._openai_model,
                messages=[
                    {"role": "system", "content": "You are a research analyst. Extract structured JSON only."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=500,
            )
            content = response.choices[0].message.content.strip()
            result = json.loads(content)
            return ResearchDecomposition(
                core_questions=result.get("core_questions", [])[:3],
                core_motivations=result.get("core_motivations", []),
                potential_impact_domains=result.get("potential_impact_domains", []),
                key_concepts=result.get("key_concepts", []),
            )
        except Exception as e:
            logger.warning(f"Decomposition failed, using fallback: {e}")
            return ResearchDecomposition(
                core_questions=[research_question],
                core_motivations=[],
                potential_impact_domains=[],
                key_concepts=[],
            )

    async def _search_papers(
        self,
        research_question: str,
        decomposition: ResearchDecomposition,
    ) -> list[dict]:
        """Search OpenAlex for related papers (keyword or semantic, with optional multi-query)."""
        if self._use_semantic_search and self._openalex_client.api_key:
            papers = await self._openalex_client.search_papers_semantic(
                research_question, limit=25
            )
        else:
            papers = await self._openalex_client.search_papers(
                research_question, limit=25
            )

        # Multi-query: if decomposition has distinct core_questions, run additional searches
        if papers and decomposition.core_questions:
            rq_lower = research_question.lower()
            seen_ids = {p.get("id") for p in papers if p.get("id")}
            for q in decomposition.core_questions[:2]:
                q_lower = q.lower().strip()
                if len(q_lower) > 10 and q_lower not in rq_lower and rq_lower not in q_lower:
                    extra = await self._openalex_client.search_papers(q, limit=8)
                    for p in extra:
                        if p.get("id") and p["id"] not in seen_ids:
                            seen_ids.add(p["id"])
                            papers.append(p)
                    if len(papers) >= 35:
                        break

        return papers[:25]

    async def _assess_impact_llm(
        self,
        research_question: str,
        decomposition: ResearchDecomposition,
        profile: ResearchProfile | None,
        papers: list[dict],
        stats: dict,
        verdict: str,
    ) -> tuple[str, str]:
        """LLM-based impact assessment using FWCI as evidence, not sole rule."""
        fwci_level = self._determine_impact_level(stats["average_fwci"])
        if stats["average_fwci"] is None:
            fwci_level = "UNCERTAIN"

        paper_summaries = []
        for p in papers[:8]:
            abstract = (p.get("abstract") or "")[:300]
            concepts = p.get("concepts", [])[:3]
            concepts_str = ", ".join(c[0] for c in concepts) if concepts else "N/A"
            paper_summaries.append(
                f"- {p['title']} (FWCI: {p.get('fwci', 'N/A')}, Year: {p.get('publication_year', 'N/A')})\n"
                f"  Abstract: {abstract}...\n  Concepts: {concepts_str}"
            )

        impact_domains = ", ".join(decomposition.potential_impact_domains) or "Not specified"
        profile_text = ""
        if profile:
            profile_text = f"Skills: {', '.join(profile.skills)}, Expertise: {', '.join(profile.expertise_areas)}"

        prompt = f"""Assess the impact potential of this research area.

Research Question: {research_question}
Core Questions: {', '.join(decomposition.core_questions) or 'N/A'}
Potential Impact Domains: {impact_domains}
Researcher: {profile_text or 'Not specified'}

Novelty Verdict: {verdict}

Related Papers ({len(papers)} found):
{chr(10).join(paper_summaries)}

FWCI Statistics:
- Average FWCI: {stats.get('average_fwci', 'N/A')}
- Papers with FWCI data: {stats.get('papers_with_fwci', 0)}
- FWCI-based level: {fwci_level}

Consider:
1. Field interest: Is this area receiving attention (from FWCI/citations)?
2. Significance: Would answering the core question matter to the impact domains?
3. Researcher fit: Does their profile suggest they can execute and have impact?

Use FWCI as evidence, not the sole rule. You may override when justified (e.g., new field with few citations but high potential).

Respond with ONLY valid JSON:
{{"impact_assessment": "HIGH|MEDIUM|LOW|UNCERTAIN", "impact_reasoning": "explanation"}}"""

        try:
            response = await self._openai_client.chat.completions.create(
                model=self._openai_model,
                messages=[
                    {"role": "system", "content": EXPERT_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=400,
            )
            content = response.choices[0].message.content.strip()
            result = json.loads(content)
            impact = result.get("impact_assessment", fwci_level)
            reasoning = result.get("impact_reasoning", "")
            if impact not in ("HIGH", "MEDIUM", "LOW", "UNCERTAIN"):
                impact = fwci_level
            return impact, reasoning or self._build_impact_reasoning(stats, impact)
        except Exception as e:
            logger.warning(f"Impact LLM failed: {e}")
            return fwci_level, self._build_impact_reasoning(stats, fwci_level)

    def _determine_impact_level(self, avg_fwci: float | None) -> str:
        """Determine impact level from average FWCI.

        - HIGH: avg_fwci > 1.5
        - MEDIUM: 0.8 <= avg_fwci <= 1.5
        - LOW: avg_fwci < 0.8
        - UNCERTAIN: avg_fwci is None
        """
        if avg_fwci is None:
            return "UNCERTAIN"
        if avg_fwci > self.HIGH_FWCI_THRESHOLD:
            return "HIGH"
        if avg_fwci < self.LOW_FWCI_THRESHOLD:
            return "LOW"
        return "MEDIUM"

    def _build_citations(self, papers: list[dict]) -> list[Citation]:
        """Convert paper dicts into Citation models."""
        citations = []
        for p in papers:
            doi = p.get("doi")
            url = f"https://doi.org/{doi}" if doi else None
            citations.append(
                Citation(
                    title=p.get("title", "Unknown"),
                    authors=p.get("authors", []),
                    year=p.get("publication_year"),
                    doi=doi,
                    url=url,
                    fwci=p.get("fwci"),
                )
            )
        return citations

    def _build_impact_reasoning(self, stats: dict, impact_level: str) -> str:
        """Build a human-readable impact reasoning string."""
        avg = stats.get("average_fwci")
        count = stats.get("papers_with_fwci", 0)

        if avg is None:
            return "No FWCI data available for related papers. Impact cannot be determined."

        return (
            f"Based on {count} papers with FWCI data: "
            f"average FWCI = {avg:.2f}. "
            f"Impact level: {impact_level} "
            f"(HIGH > {self.HIGH_FWCI_THRESHOLD}, "
            f"MEDIUM {self.LOW_FWCI_THRESHOLD}-{self.HIGH_FWCI_THRESHOLD}, "
            f"LOW < {self.LOW_FWCI_THRESHOLD})."
        )

    def _uncertain_assessment(
        self,
        reasoning: str,
        decomposition: ResearchDecomposition | None = None,
    ) -> NoveltyAssessment:
        """Create a default UNCERTAIN assessment for error cases."""
        return NoveltyAssessment(
            score=0.5,
            verdict="UNCERTAIN",
            evidence=[],
            reasoning=reasoning,
            related_papers_count=0,
            average_fwci=None,
            fwci_percentile=None,
            citation_percentile_min=None,
            citation_percentile_max=None,
            impact_assessment="UNCERTAIN",
            impact_reasoning="Unable to determine impact due to insufficient data.",
            expected_impact_assessment="UNCERTAIN",
            expected_impact_reasoning="Unable to predict expected impact due to insufficient data.",
            research_decomposition=decomposition,
        )

    async def _assess_expected_impact(
        self,
        research_question: str,
        profile: ResearchProfile | None,
        verdict: str,
        novelty_score: float,
        papers: list[dict],
        stats: dict,
        decomposition: ResearchDecomposition,
    ) -> tuple[str, str]:
        """Assess the expected impact of the researcher's work using LLM.

        Returns:
            Tuple of (impact_level, reasoning).
        """
        skills_text = ""
        if profile:
            skills_text = f"""
Researcher Profile:
- Skills: {', '.join(profile.skills) if profile.skills else 'Not specified'}
- Expertise: {', '.join(profile.expertise_areas) if profile.expertise_areas else 'Not specified'}
- Motivations: {', '.join(profile.motivations) if profile.motivations else 'Not specified'}"""

        paper_summaries = []
        for p in papers[:8]:
            abstract = (p.get("abstract") or "")[:200]
            concepts = p.get("concepts", [])[:2]
            concepts_str = ", ".join(c[0] for c in concepts) if concepts else ""
            paper_summaries.append(
                f"- {p['title']} (FWCI: {p.get('fwci', 'N/A')}, Year: {p.get('publication_year', 'N/A')})\n"
                f"  Abstract: {abstract}...\n  Concepts: {concepts_str}"
            )

        core_questions = ", ".join(decomposition.core_questions) or "N/A"
        impact_domains = ", ".join(decomposition.potential_impact_domains) or "Not specified"

        prompt = f"""Predict the expected impact of a researcher's work if it goes through.

Research Question: {research_question}
Core Questions: {core_questions}
Potential Impact Domains: {impact_domains}
{skills_text}

Novelty Verdict: {verdict} (score: {novelty_score:.2f})

Related Literature ({len(papers)} papers found):
{chr(10).join(paper_summaries)}

FWCI Statistics:
- Average FWCI of related papers: {stats.get('average_fwci', 'N/A')}
- Papers with FWCI data: {stats.get('papers_with_fwci', 0)}

Based on:
1. The novelty of the research angle
2. The researcher's skills and expertise
3. The current state of the field (related papers and their impact)
4. The potential for this specific research to advance knowledge

Predict the expected impact if this research is completed:
- HIGH: Will likely produce highly-cited, field-advancing work
- MEDIUM: Will contribute meaningfully but incrementally to the field
- LOW: Unlikely to have significant impact (e.g. saturated area, weak angle)

Respond with ONLY valid JSON (no markdown, no code fences):
{{"expected_impact": "HIGH|MEDIUM|LOW", "reasoning": "explanation of predicted impact"}}"""

        try:
            response = await self._openai_client.chat.completions.create(
                model=self._openai_model,
                messages=[
                    {"role": "system", "content": EXPERT_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=500,
            )
            content = response.choices[0].message.content.strip()
            result = json.loads(content)
            impact = result.get("expected_impact", "UNCERTAIN")
            reasoning = result.get("reasoning", "No reasoning provided.")
            if impact not in ("HIGH", "MEDIUM", "LOW"):
                impact = "UNCERTAIN"
            return impact, reasoning
        except Exception as e:
            logger.error(f"Expected impact LLM call failed: {e}")
            return "UNCERTAIN", f"Could not predict expected impact: {e}"

    async def _get_llm_verdict(
        self,
        research_question: str,
        decomposition: ResearchDecomposition,
        papers: list[dict],
        stats: dict,
    ) -> dict:
        """Use an LLM to interpret OpenAlex results and determine novelty verdict.

        Returns:
            Dict with 'verdict', 'score', and 'reasoning' keys.
        """
        paper_summaries = []
        for p in papers[:10]:
            abstract = (p.get("abstract") or "")[:350]
            concepts = p.get("concepts", [])[:3]
            keywords = p.get("keywords", [])[:3]
            concepts_str = ", ".join(c[0] for c in concepts) if concepts else "N/A"
            keywords_str = ", ".join(k[0] for k in keywords) if keywords else "N/A"
            paper_summaries.append(
                f"- {p['title']} (FWCI: {p.get('fwci', 'N/A')}, Year: {p.get('publication_year', 'N/A')})\n"
                f"  Abstract: {abstract}...\n  Concepts: {concepts_str}\n  Keywords: {keywords_str}"
            )

        core_questions = "\n".join(f"  - {q}" for q in decomposition.core_questions) or "  N/A"
        motivations = ", ".join(decomposition.core_motivations) or "Not specified"

        prompt = f"""You are evaluating whether a research direction is worth pursuing.

Research Question: {research_question}

Core Questions (what the research aims to answer):
{core_questions}

Core Motivations: {motivations}

Related Papers Found ({len(papers)} total):
{chr(10).join(paper_summaries)}

FWCI Statistics:
- Average FWCI: {stats.get('average_fwci', 'N/A')}
- Papers with FWCI data: {stats.get('papers_with_fwci', 0)}
- Citation percentile range: {stats.get('citation_percentile_min', 'N/A')}-{stats.get('citation_percentile_max', 'N/A')}

For each paper, consider:
1. Does it answer the SAME core question(s), or a related but different question?
2. Similarity: High = same core question; Medium = related subquestion; Low = tangential
3. What remains unanswered?

Determine the novelty verdict:
- SOLVED: The core research question has been definitively answered in existing literature.
- MARGINAL: Some novelty exists but the area is heavily explored with diminishing returns.
- NOVEL: The research question explores genuinely new territory with significant potential.
- UNCERTAIN: Not enough information to determine novelty.

Respond with ONLY valid JSON (no markdown, no code fences):
{{"verdict": "SOLVED|MARGINAL|NOVEL|UNCERTAIN", "score": 0.0-1.0, "reasoning": "explanation"}}"""

        response = await self._openai_client.chat.completions.create(
            model=self._openai_model,
            messages=[
                {"role": "system", "content": EXPERT_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=600,
        )

        content = response.choices[0].message.content.strip()
        return json.loads(content)

    async def close(self):
        """Close underlying clients."""
        await self._openalex_client.close()
        await self._openai_client.close()
