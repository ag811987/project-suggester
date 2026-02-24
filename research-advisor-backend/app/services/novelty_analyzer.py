"""Novelty & Impact Analyzer service.

Determines whether a research question is novel, marginal, or already solved
by querying OpenAlex for related papers and using an LLM to interpret the results.
"""

import asyncio
import json

import hashlib
import time
import re

from openai import AsyncOpenAI

# Broad terms that match too many papers; prefer key_concepts that add specificity
_BROAD_SEARCH_TERMS = frozenset({
    "speciation", "ecology", "evolution", "adaptation", "biodiversity",
    "climate", "genetics", "molecular", "phylogeny", "morphology",
    "population", "species", "conservation", "behavior", "physiology",
})


def _looks_specific(term: str) -> bool:
    """True if term adds specificity (e.g. genus name, technique) vs broad field term."""
    lower = term.lower().strip()
    if not lower or len(lower) < 3:
        return False
    if term[0].isupper():
        return True
    return lower not in _BROAD_SEARCH_TERMS


def _shorten_query(text: str, max_words: int = 8) -> str:
    """Extract a short search query from a long research question."""
    words = text.split()
    if len(words) <= max_words:
        return text.strip()
    return " ".join(words[:max_words])


def _tokenize_terms(text: str) -> list[str]:
    """Tokenize into lowercase terms for lightweight relevance checks."""
    if not text:
        return []
    tokens = re.findall(r"[a-zA-Z0-9][a-zA-Z0-9\-]{2,}", text.lower())
    out: list[str] = []
    for t in tokens:
        if len(t) < 4:
            continue
        if t in _BROAD_SEARCH_TERMS:
            continue
        out.append(t)
    return out


def _bm25_rerank(
    papers: list[dict],
    *,
    query_terms: list[str],
    phrase_boosts: list[str],
    limit: int,
) -> list[dict]:
    """Rerank papers by BM25-style similarity over title+abstract.

    No citation-based signals are used.
    """
    if not papers or not query_terms:
        return papers[:limit]

    docs: list[list[str]] = []
    doc_texts: list[str] = []
    for p in papers:
        title = p.get("title") or ""
        abstract = p.get("abstract") or ""
        text = f"{title} {abstract}".lower()
        doc_texts.append(text)
        docs.append(_tokenize_terms(text))

    n_docs = len(docs)
    avgdl = (sum(len(d) for d in docs) / n_docs) if n_docs else 1.0
    if avgdl <= 0:
        avgdl = 1.0

    # Document frequencies for query terms
    qset = set(query_terms)
    df: dict[str, int] = {t: 0 for t in qset}
    for d in docs:
        dset = set(d)
        for t in qset:
            if t in dset:
                df[t] += 1

    # BM25 params
    k1 = 1.2
    b = 0.75

    def _idf(t: str) -> float:
        # BM25+ style idf smoothing
        n = df.get(t, 0)
        return max(0.0, ((n_docs - n + 0.5) / (n + 0.5)))

    scored: list[tuple[float, dict]] = []
    for paper, d_terms, d_text in zip(papers, docs, doc_texts, strict=True):
        dl = len(d_terms) or 1
        # term frequencies
        tf: dict[str, int] = {}
        for t in d_terms:
            if t in qset:
                tf[t] = tf.get(t, 0) + 1

        score = 0.0
        for t in qset:
            f = tf.get(t, 0)
            if f <= 0:
                continue
            idf = _idf(t)
            denom = f + k1 * (1 - b + b * (dl / avgdl))
            score += idf * ((f * (k1 + 1)) / denom)

        # Phrase boosts for multiword key concepts (exact substring match)
        for phrase in phrase_boosts:
            ph = phrase.lower().strip()
            if ph and len(ph) >= 6 and ph in d_text:
                score += 2.0

        paper["_bm25_score"] = score
        scored.append((score, paper))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in scored[:limit]]


def _merge_papers(semantic: list[dict], keyword: list[dict], limit: int) -> list[dict]:
    """Merge semantic and keyword results, dedupe by paper id, semantic first.

    Preserves _retrieval_source: papers from semantic list keep 'semantic',
    papers only found via keyword keep 'keyword'.
    """
    seen: set[str] = set()
    merged: list[dict] = []
    for p in semantic:
        p.setdefault("_retrieval_source", "semantic")
    for p in keyword:
        p.setdefault("_retrieval_source", "keyword")
    for p in semantic + keyword:
        pid = p.get("id")
        if pid and pid not in seen:
            seen.add(str(pid))
            merged.append(p)
            if len(merged) >= limit:
                break
    return merged


def _merge_multiquery_results(
    results_per_query: list[list[dict]], limit: int
) -> list[dict]:
    """Merge multi-query results: dedupe by paper id, rank by query_count then relevance_score."""
    # Count how many queries returned each paper
    paper_to_count: dict[str, dict] = {}
    for result_list in results_per_query:
        for p in result_list:
            pid = p.get("id")
            if not pid:
                continue
            pid_str = str(pid)
            if pid_str not in paper_to_count:
                paper_to_count[pid_str] = {**p, "_query_count": 0}
            paper_to_count[pid_str]["_query_count"] += 1
            # Keep highest relevance_score if paper appears in multiple lists
            rs = p.get("relevance_score")
            if rs is not None and (
                paper_to_count[pid_str].get("relevance_score") is None
                or rs > (paper_to_count[pid_str].get("relevance_score") or 0)
            ):
                paper_to_count[pid_str]["relevance_score"] = rs

    # Sort by query_count desc, then relevance_score desc
    papers_sorted = sorted(
        paper_to_count.values(),
        key=lambda p: (
            -p.get("_query_count", 0),
            -(p.get("relevance_score") or 0),
        ),
    )
    # Remove _query_count from output, take top limit
    out: list[dict] = []
    for p in papers_sorted[:limit]:
        d = {k: v for k, v in p.items() if k != "_query_count"}
        out.append(d)
    return out


from loguru import logger

from collections import Counter

from app.models.schemas import (
    NoveltyAssessment,
    Citation,
    ResearchDecomposition,
    ResearcherClassification,
    ResearchProfile,
)
from app.services.embedding_service import EmbeddingService
from app.services.openalex_client import OpenAlexClient

EXPERT_SYSTEM_PROMPT = """You are a research strategist who evaluates whether research directions are worth pursuing. You assess novelty, clarity of the question, and potential impact—considering both scholarly and non-academic outcomes (e.g., practical, policy, societal). You combine bibliometric data with domain judgment. You:
- Break down research problems to understand core questions and motivations.
- Judge whether related papers address the SAME core questions or only tangentially related ones.
- Assess significance: would answering this question advance knowledge or practice in a meaningful way?
- Make nuanced calls; do not over-weight citation metrics—consider emerging fields and practical impact.

Be appropriately skeptical:
- Method-to-new-population: Applying established methods to a slightly different species, population, or dataset is usually MARGINAL, not NOVEL. True novelty requires new conceptual questions, new methodology, or genuinely unexplored territory.
- Impact inflation: Avoid over-scoring niche research (e.g., speciating a particular bird species). Ask: Is this a good use of the researcher's skills? Would they have more impact elsewhere? Who actually benefits?
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

    def __init__(
        self,
        openalex_email: str,
        openai_api_key: str,
        openalex_api_key: str | None = None,
        openai_model: str = "gpt-4-0125-preview",
        use_semantic_search: bool = False,
        semantic_budget_threshold: float = 0.05,
        multi_query: bool = True,
        queries_per_variant: int = 5,
        use_embedding_rerank: bool = False,
        fwci_high_threshold: float = 2.2,
        fwci_low_threshold: float = 1.2,
        search_limit: int = 8,
    ):
        self._fwci_high = fwci_high_threshold
        self._fwci_low = fwci_low_threshold
        self._search_limit = search_limit
        self._openalex_client = OpenAlexClient(
            email=openalex_email,
            api_key=openalex_api_key,
        )
        self._openai_client = AsyncOpenAI(api_key=openai_api_key)
        self._openai_model = openai_model
        self._use_semantic_search = use_semantic_search
        self._semantic_budget_threshold = semantic_budget_threshold
        self._multi_query = multi_query
        self._queries_per_variant = queries_per_variant
        self._use_embedding_rerank = use_embedding_rerank
        self._embedding_service = (
            EmbeddingService(api_key=openai_api_key) if use_embedding_rerank else None
        )

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

        # Privacy: no user query text logged
        try:
            with open(
                "/Users/amit/Coding-Projects/Project-Suggester/.cursor/debug.log",
                "a",
                encoding="utf-8",
            ) as f:
                f.write(
                    json.dumps(
                        {
                            "id": f"log_{time.time_ns()}",
                            "timestamp": int(time.time() * 1000),
                            "location": "app/services/novelty_analyzer.py:analyze:papers_returned",
                            "message": "NoveltyAnalyzer papers returned from OpenAlex search",
                            "data": {"papers_count": len(papers)},
                            "runId": "post-fix",
                            "hypothesisId": "H_OA_RESULT_MISMATCH",
                        }
                    )
                    + "\n"
                )
        except Exception:
            pass

        # If no papers found, return UNCERTAIN
        if not papers:
            try:
                with open(
                    "/Users/amit/Coding-Projects/Project-Suggester/.cursor/debug.log",
                    "a",
                    encoding="utf-8",
                ) as f:
                    f.write(
                        json.dumps(
                            {
                                "id": f"log_{time.time_ns()}",
                                "timestamp": int(time.time() * 1000),
                                "location": "app/services/novelty_analyzer.py:analyze:no_papers",
                                "message": "NoveltyAnalyzer returning UNCERTAIN due to no papers",
                                "data": {},
                                "runId": "post-fix",
                                "hypothesisId": "H_OA_RESULT_MISMATCH",
                            }
                        )
                        + "\n"
                    )
            except Exception:
                pass
            return self._uncertain_assessment(
                reasoning="No related papers found in OpenAlex. Unable to assess novelty.",
                decomposition=decomposition,
            )

        # Step 3: Calculate FWCI statistics (median to avoid outlier inflation)
        stats = self._openalex_client.calculate_fwci_stats(papers)

        # Step 3b: Extract researcher's topic taxonomy classification
        researcher_classification = self._extract_researcher_taxonomy(papers)

        # Step 3c: Partition papers by topic proximity to researcher
        proximity_tiers = self._partition_by_proximity(papers, researcher_classification)
        tier_stats = {
            tier: self._openalex_client.calculate_fwci_stats(tier_papers)
            for tier, tier_papers in proximity_tiers.items()
            if tier_papers
        }

        # Step 4: Build citations
        citations = self._build_citations(papers)

        # Step 5: Use LLM to determine verdict (with topic proximity context)
        try:
            llm_result = await self._get_llm_verdict(
                research_question, decomposition, papers, stats,
                researcher_classification, proximity_tiers, tier_stats,
            )
            verdict = llm_result["verdict"]
            score = llm_result["score"]
            reasoning = llm_result["reasoning"]
        except Exception as e:
            logger.error(f"LLM verdict failed: {e}")
            verdict = "UNCERTAIN"
            score = 0.5
            reasoning = f"LLM analysis unavailable: {e}. Assessment based on bibliometric data only."

        # Step 6: LLM-based impact assessment (with field context)
        try:
            impact_level, impact_reasoning = await self._assess_impact_llm(
                research_question, decomposition, profile, papers, stats, verdict,
                researcher_classification, tier_stats,
            )
        except Exception as e:
            logger.error(f"Impact LLM assessment failed: {e}")
            impact_level = self._determine_impact_level(stats["average_fwci"])
            if stats["average_fwci"] is None:
                impact_level = "UNCERTAIN"
            impact_reasoning = self._build_impact_reasoning(stats, impact_level)

        # Step 7: Assess expected impact and real-world impact in parallel
        (expected_impact, expected_reasoning), (rw_impact, rw_reasoning) = (
            await asyncio.gather(
                self._assess_expected_impact(
                    research_question,
                    profile,
                    verdict,
                    score,
                    papers,
                    stats,
                    decomposition,
                    researcher_classification,
                    tier_stats,
                ),
                self._assess_real_world_impact(
                    research_question, profile, decomposition, verdict, papers
                ),
            )
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
            real_world_impact_assessment=rw_impact,
            real_world_impact_reasoning=rw_reasoning,
            research_decomposition=decomposition,
            researcher_classification=researcher_classification,
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
- key_concepts: SPECIFIC search terms—include genus/species names, model names, exact techniques (e.g., Psittacara, parakeet, morphological phylogeny). Include one primary topic (e.g., speciation, conservation). Avoid broad terms alone (speciation, ecology) that match unrelated highly-cited papers. Preserve niche specificity.

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

    @staticmethod
    def _extract_researcher_taxonomy(papers: list[dict]) -> ResearcherClassification:
        """Derive the researcher's position in the OpenAlex topic taxonomy.

        Aggregates primary_topic fields from returned papers using weighted voting.
        Computes topic_diversity as unique_subfields / total_papers.
        """
        domain_votes: Counter[str] = Counter()
        field_votes: Counter[str] = Counter()
        subfield_votes: Counter[str] = Counter()
        topic_votes: Counter[str] = Counter()
        subfields_seen: set[str] = set()
        papers_with_topics = 0

        for p in papers:
            pt = p.get("primary_topic")
            if not pt or not isinstance(pt, dict):
                continue
            papers_with_topics += 1
            weight = pt.get("score") or 1.0
            if pt.get("domain"):
                domain_votes[pt["domain"]] += weight
            if pt.get("field"):
                field_votes[pt["field"]] += weight
            if pt.get("subfield"):
                subfield_votes[pt["subfield"]] += weight
                subfields_seen.add(pt["subfield"])
            if pt.get("topic"):
                topic_votes[pt["topic"]] += weight

        primary_topic = topic_votes.most_common(1)[0][0] if topic_votes else None
        # Secondary topics: all topics beyond the primary
        secondary = [t for t, _ in topic_votes.most_common() if t != primary_topic]

        diversity = (
            len(subfields_seen) / papers_with_topics
            if papers_with_topics > 0
            else None
        )

        return ResearcherClassification(
            primary_domain=domain_votes.most_common(1)[0][0] if domain_votes else None,
            primary_field=field_votes.most_common(1)[0][0] if field_votes else None,
            primary_subfield=subfield_votes.most_common(1)[0][0] if subfield_votes else None,
            primary_topic=primary_topic,
            secondary_topics=secondary[:5],
            topic_diversity=round(diversity, 2) if diversity is not None else None,
        )

    @staticmethod
    def _partition_by_proximity(
        papers: list[dict],
        classification: ResearcherClassification,
    ) -> dict[str, list[dict]]:
        """Group papers by topic proximity to the researcher's classification.

        Returns a dict with keys: same_topic, same_subfield, same_field, cross_field.
        """
        tiers: dict[str, list[dict]] = {
            "same_topic": [],
            "same_subfield": [],
            "same_field": [],
            "cross_field": [],
        }
        for paper in papers:
            pt = paper.get("primary_topic") or {}
            if (
                classification.primary_topic
                and pt.get("topic") == classification.primary_topic
            ):
                tiers["same_topic"].append(paper)
            elif (
                classification.primary_subfield
                and pt.get("subfield") == classification.primary_subfield
            ):
                tiers["same_subfield"].append(paper)
            elif (
                classification.primary_field
                and pt.get("field") == classification.primary_field
            ):
                tiers["same_field"].append(paper)
            else:
                tiers["cross_field"].append(paper)
        return tiers

    def _build_search_queries(
        self, research_question: str, decomposition: ResearchDecomposition
    ) -> list[str]:
        """Build 3-6 query variants from decomposition for multi-query search.

        First query is a high-precision 'niche' phrase (Scholar-style) built from
        taxonomic/specific terms + primary topic, so narrow hits rank well.
        """
        queries: list[str] = []
        kc = [k for k in (decomposition.key_concepts or []) if k and len(k) > 2]
        cq = decomposition.core_questions or []

        # Q0 (niche): high-precision phrase from specific concepts + topic (Scholar-style)
        # e.g. "speciation Psittacara parakeets" or "Psittacara parakeet speciation"
        specific = [k for k in kc if _looks_specific(k)]
        if specific:
            # Build niche phrase: 2-3 specific terms + one topic-like term
            topic_candidates = ["speciation", "conservation", "phylogeny", "ecology", "evolution"]
            topic = None
            for t in topic_candidates:
                if any(t in (k or "").lower() for k in kc):
                    topic = t
                    break
            niche_parts = specific[:3]
            if topic and topic not in " ".join(niche_parts).lower():
                niche_parts.append(topic)
            niche = " ".join(niche_parts[:4])
            if niche and niche not in queries:
                queries.append(niche)

        # Q1: space-joined key concepts (avoid OR, which tends to pull famous unrelated tools)
        if kc:
            q1 = " ".join(kc[:6])
            if q1 and q1 not in queries:
                queries.append(q1)

        # Q2: first core question (10 words)
        if cq:
            q2 = " ".join(cq[0].split()[:10]).strip()
            if q2 and q2 not in queries:
                queries.append(q2)

        # Q3: shortened research question
        q3 = _shorten_query(research_question)
        if q3 and q3 not in queries:
            queries.append(q3)

        # Q4: phrase-ish variant (no quotes; OpenAlex filter parser can be sensitive)
        if len(kc) >= 2:
            phraseish = " ".join(kc[:3])
            if phraseish and phraseish not in queries:
                queries.append(phraseish)

        return queries[:6]

    async def _rerank_papers_by_embedding(
        self, research_question: str, papers: list[dict], limit: int
    ) -> list[dict]:
        """Rerank papers by cosine similarity of embeddings to research question."""
        if not papers or not self._embedding_service:
            return papers[:limit]
        texts = []
        for p in papers:
            t = (p.get("title") or "") + " " + ((p.get("abstract") or "")[:200])
            texts.append((t or " ").strip() or " ")
        try:
            query_embedding, *paper_embeddings = await self._embedding_service.embed_batch(
                [research_question] + texts
            )
        except Exception as e:
            logger.warning("Embedding rerank failed: %s", e)
            return papers[:limit]

        def _cosine_sim(a: list[float], b: list[float]) -> float:
            dot = sum(x * y for x, y in zip(a, b, strict=True))
            na = sum(x * x for x in a) ** 0.5
            nb = sum(x * x for x in b) ** 0.5
            return dot / (na * nb) if na and nb else 0.0

        scored = [
            (p, _cosine_sim(query_embedding, emb))
            for p, emb in zip(papers, paper_embeddings, strict=True)
        ]
        scored.sort(key=lambda x: -x[1])
        return [p for p, _ in scored[:limit]]

    async def _finalize_papers(
        self, research_question: str, papers: list[dict], limit: int
    ) -> list[dict]:
        """Apply optional embedding rerank, then cap to limit."""
        if self._use_embedding_rerank and papers:
            papers = await self._rerank_papers_by_embedding(
                research_question, papers, limit
            )
        return papers[:limit]

    async def _run_multiquery_keyword(
        self, queries: list[str], limit: int
    ) -> list[dict]:
        """Run multiple keyword queries; niche (first) query runs first, results prepended.

        Niche query results are placed at the top so high-precision hits (e.g.
        Psittacara parakeet speciation) are not pushed out by broad-query papers.
        """
        if not queries:
            return []
        per_query = self._queries_per_variant
        niche_limit = min(8, per_query * 2)

        # Run niche (first) query first
        niche_results = await self._openalex_client.search_papers_title_abstract(
            queries[0], limit=niche_limit
        )
        for p in niche_results:
            p.setdefault("_retrieval_source", "keyword")

        # Run remaining queries in parallel
        rest_results: list[list[dict]] = []
        if len(queries) > 1:
            rest_results = await asyncio.gather(
                *[
                    self._openalex_client.search_papers_title_abstract(q, limit=per_query)
                    for q in queries[1:]
                ]
            )
            for result_list in rest_results:
                for p in result_list:
                    p.setdefault("_retrieval_source", "keyword")

        # Merge: niche first, then rest (dedupe by paper id)
        seen: set[str] = set()
        merged: list[dict] = []
        for p in niche_results:
            pid = p.get("id")
            if pid and str(pid) not in seen:
                seen.add(str(pid))
                merged.append(p)
        if rest_results:
            rest_merged = _merge_multiquery_results(rest_results, limit)
            for p in rest_merged:
                pid = p.get("id")
                if pid and str(pid) not in seen:
                    seen.add(str(pid))
                    merged.append(p)

        if len(merged) < max(5, limit // 2) and queries:
            broad = await asyncio.gather(
                *[
                    self._openalex_client.search_papers(q, limit=per_query)
                    for q in queries
                ]
            )
            for result_list in broad:
                for p in result_list:
                    p.setdefault("_retrieval_source", "keyword")
            broad_merged = _merge_multiquery_results(broad, limit)
            for p in broad_merged:
                pid = p.get("id")
                if pid and str(pid) not in seen:
                    seen.add(str(pid))
                    merged.append(p)

        return merged[:limit]

    def _filter_and_rerank_by_local_relevance(
        self,
        papers: list[dict],
        decomposition: ResearchDecomposition,
        research_question: str,
        limit: int,
    ) -> list[dict]:
        """Rerank by similarity to the proposal (no citation-based preference)."""
        if not papers:
            return []

        # Build query terms and phrase boosts from specific key concepts; fall back to question tokens.
        raw_terms: list[str] = []
        phrase_boosts: list[str] = []
        for k in (decomposition.key_concepts or [])[:12]:
            if not k:
                continue
            if " " in k.strip():
                phrase_boosts.append(k.strip())
            if _looks_specific(k):
                raw_terms.extend(_tokenize_terms(k))
        if not raw_terms:
            raw_terms = _tokenize_terms(research_question)

        seen: set[str] = set()
        terms: list[str] = []
        for t in raw_terms:
            if t not in seen:
                seen.add(t)
                terms.append(t)
        terms = terms[:20]

        return _bm25_rerank(
            papers,
            query_terms=terms,
            phrase_boosts=phrase_boosts[:8],
            limit=limit,
        )

    async def _search_papers(
        self,
        research_question: str,
        decomposition: ResearchDecomposition,
    ) -> list[dict]:
        """Search OpenAlex for related papers.

        When budget allows: semantic + multi-query keyword in parallel.
        When budget low: multi-query keyword only.
        Fallback when empty: full research_question, then ultra-broad.
        """
        # Build keyword_query from key concepts (targeted for keyword search)
        specific_terms = [
            k for k in (decomposition.key_concepts or [])
            if k and len(k) > 2 and _looks_specific(k)
        ]
        all_concepts = [k for k in (decomposition.key_concepts or []) if k and len(k) > 2]
        if specific_terms:
            primary_query = " ".join(specific_terms[:5])
        elif all_concepts:
            primary_query = " ".join(all_concepts[:5])
        else:
            primary_query = _shorten_query(research_question)

        # For semantic search use a richer query closer to the user's proposal
        semantic_query = research_question.strip()
        if decomposition.core_questions:
            semantic_query = f"{research_question} {decomposition.core_questions[0]}"
        semantic_query = semantic_query[:2000]

        limit = self._search_limit
        use_semantic = (
            self._use_semantic_search
            and self._openalex_client.api_key
        )

        if self._multi_query:
            queries = self._build_search_queries(research_question, decomposition)
            if not queries:
                queries = [primary_query or research_question]

            # Privacy: Do NOT log raw queries or research_question.
            def _fp(s: str) -> str | None:
                sn = (s or "").strip()
                return hashlib.sha256(sn.encode("utf-8")).hexdigest()[:12] if sn else None

            t0 = time.perf_counter()
            try:
                with open(
                    "/Users/amit/Coding-Projects/Project-Suggester/.cursor/debug.log",
                    "a",
                    encoding="utf-8",
                ) as f:
                    f.write(
                        json.dumps(
                            {
                                "id": f"log_{time.time_ns()}",
                                "timestamp": int(time.time() * 1000),
                                "location": "app/services/novelty_analyzer.py:_search_papers:begin",
                                "message": "NoveltyAnalyzer OpenAlex search begin (multi-query)",
                                "data": {
                                    "multi_query": True,
                                    "use_semantic": bool(use_semantic),
                                    "queries_count": len(queries),
                                    "queries_sha256_12": [_fp(q) for q in queries],
                                    "primary_query_sha256_12": _fp(primary_query),
                                    "primary_query_len": len((primary_query or "").strip()),
                                    "search_limit": self._search_limit,
                                    "queries_per_variant": self._queries_per_variant,
                                },
                                "runId": "post-fix",
                                "hypothesisId": "H_OA_EMPTY",
                            }
                        )
                        + "\n"
                    )
            except Exception:
                pass

            if use_semantic:
                remaining = await self._openalex_client.get_remaining_budget_usd()
                if remaining is not None and remaining >= self._semantic_budget_threshold:
                    semantic, keyword = await asyncio.gather(
                        self._openalex_client.search_papers_semantic(
                            semantic_query, limit=limit
                        ),
                        self._run_multiquery_keyword(queries, limit),
                    )
                    papers = _merge_papers(semantic, keyword, limit)
                else:
                    papers = await self._run_multiquery_keyword(queries, limit)
            else:
                papers = await self._run_multiquery_keyword(queries, limit)

            if papers:
                papers = self._filter_and_rerank_by_local_relevance(
                    papers, decomposition, research_question, limit
                )
                try:
                    with open(
                        "/Users/amit/Coding-Projects/Project-Suggester/.cursor/debug.log",
                        "a",
                        encoding="utf-8",
                    ) as f:
                        f.write(
                            json.dumps(
                                {
                                    "id": f"log_{time.time_ns()}",
                                    "timestamp": int(time.time() * 1000),
                                    "location": "app/services/novelty_analyzer.py:_search_papers:end",
                                    "message": "NoveltyAnalyzer OpenAlex search end (multi-query)",
                                    "data": {
                                        "papers_count": len(papers),
                                        "elapsed_ms": int((time.perf_counter() - t0) * 1000),
                                    },
                                    "runId": "post-fix",
                                    "hypothesisId": "H_OA_EMPTY",
                                }
                            )
                            + "\n"
                        )
                except Exception:
                    pass
                return await self._finalize_papers(research_question, papers, limit)
            # Fallback when empty
            papers = await self._openalex_client.search_papers_title_abstract(
                research_question, limit=limit
            )
            if papers:
                papers = self._filter_and_rerank_by_local_relevance(
                    papers, decomposition, research_question, limit
                )
                return await self._finalize_papers(research_question, papers, limit)
            kc = [k for k in (decomposition.key_concepts or []) if k and len(k) > 2]
            ultra = (
                " OR ".join(kc[:3])
                if kc
                else " ".join(research_question.split()[:3])
            )
            if ultra:
                papers = await self._openalex_client.search_papers_title_abstract(
                    ultra, limit=limit
                )
                # Privacy: no raw query logging
                logger.warning(
                    "Multi-query returned 0; tried fallbacks (counts only): variants=%d",
                    len(queries) + 2,
                )
                papers = self._filter_and_rerank_by_local_relevance(
                    papers, decomposition, research_question, limit
                )
                return await self._finalize_papers(research_question, papers, limit)
            return []

        # Legacy single-query flow (multi_query=False)
        if use_semantic:
            remaining = await self._openalex_client.get_remaining_budget_usd()
            if remaining is not None and remaining >= self._semantic_budget_threshold:
                use_tight = specific_terms and len(primary_query) < 80
                keyword_search = (
                    self._openalex_client.search_papers_title_abstract
                    if use_tight
                    else self._openalex_client.search_papers
                )
                semantic, keyword = await asyncio.gather(
                    self._openalex_client.search_papers_semantic(
                        semantic_query, limit=limit
                    ),
                    keyword_search(primary_query, limit=limit),
                )
                papers = _merge_papers(semantic, keyword, limit)
                return await self._finalize_papers(
                    research_question, papers, limit
                )
        use_tight = specific_terms and len(primary_query) < 80
        if use_tight:
            papers = await self._openalex_client.search_papers_title_abstract(
                primary_query, limit=limit
            )
        else:
            papers = []
        if len(papers) < 3:
            papers = await self._openalex_client.search_papers(
                primary_query, limit=limit
            )
        if len(papers) < 3 and primary_query != research_question:
            papers = await self._openalex_client.search_papers(
                _shorten_query(research_question), limit=limit
            )
        return await self._finalize_papers(
            research_question, papers, limit
        )

    async def _assess_impact_llm(
        self,
        research_question: str,
        decomposition: ResearchDecomposition,
        profile: ResearchProfile | None,
        papers: list[dict],
        stats: dict,
        verdict: str,
        classification: ResearcherClassification | None = None,
        tier_stats: dict[str, dict] | None = None,
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

        # Build field context block from taxonomy classification
        field_context = ""
        if classification and tier_stats:
            same_topic_stats = tier_stats.get("same_topic", {})
            same_subfield_stats = tier_stats.get("same_subfield", {})
            field_context = f"""
FIELD CONTEXT:
- Researcher's field: {classification.primary_field or 'Unknown'} > {classification.primary_subfield or 'Unknown'}
- FWCI within their exact topic: {same_topic_stats.get('average_fwci', 'N/A')} (from {same_topic_stats.get('papers_with_fwci', 0)} papers)
- FWCI in adjacent subfields: {same_subfield_stats.get('average_fwci', 'N/A')} (from {same_subfield_stats.get('papers_with_fwci', 0)} papers)
- Topic diversity: {classification.topic_diversity or 'N/A'}

Papers from the researcher's exact topic are the most relevant for assessing field activity and competition."""

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
{field_context}

Consider:
1. Field interest: Is this area receiving attention (from FWCI/citations)?
2. Significance: Would answering the core question matter to the impact domains?
3. Researcher fit: Does their profile suggest they can execute and have impact?
4. Opportunity cost: Is this a good use of the researcher's skills? Would they have more impact elsewhere? Avoid over-scoring niche research (e.g., speciating a particular species)—ask who actually benefits and whether the problem justifies the researcher's expertise.

Use FWCI as evidence, not the sole rule. You may override when justified (e.g., new field with few citations but high potential). Be appropriately skeptical of impact inflation.

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

        Uses configurable thresholds (defaults stricter than raw OpenAlex due to
        known inflation; see docs/FWCI_CALIBRATION.md).
        """
        if avg_fwci is None:
            return "UNCERTAIN"
        if avg_fwci > self._fwci_high:
            return "HIGH"
        if avg_fwci < self._fwci_low:
            return "LOW"
        return "MEDIUM"

    _citation_cap = 10

    def _build_citations(
        self,
        papers: list[dict],
        min_bm25_score: float = 1.2,
    ) -> list[Citation]:
        """Convert paper dicts into Citation models, filtering low-relevance papers.

        Only considers the top N papers by BM25 (citation cap) to avoid citing
        marginal matches. Papers with _bm25_score below min_bm25_score are
        excluded. If all are filtered, the top 3 are kept as fallback.
        """
        def _to_citation(p: dict) -> Citation:
            doi = p.get("doi")
            url = f"https://doi.org/{doi}" if doi else None
            return Citation(
                title=p.get("title", "Unknown"),
                authors=p.get("authors", []),
                year=p.get("publication_year"),
                doi=doi,
                url=url,
                fwci=p.get("fwci"),
            )

        # Restrict to top N by BM25 so we don't cite marginal matches
        capped = papers[: self._citation_cap]

        filtered = []
        for p in capped:
            bm25 = p.get("_bm25_score")
            if bm25 is not None and bm25 < min_bm25_score:
                continue
            filtered.append(p)

        # Fallback: if all papers were filtered out, keep top 3 by BM25 score
        if not filtered and capped:
            sorted_by_bm25 = sorted(
                capped, key=lambda p: p.get("_bm25_score", 0), reverse=True
            )
            filtered = sorted_by_bm25[:3]

        return [_to_citation(p) for p in filtered]

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
            f"(HIGH > {self._fwci_high}, "
            f"MEDIUM {self._fwci_low}-{self._fwci_high}, "
            f"LOW < {self._fwci_low})."
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
            real_world_impact_assessment="UNCERTAIN",
            real_world_impact_reasoning="Unable to determine real-world impact due to insufficient data.",
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
        classification: ResearcherClassification | None = None,
        tier_stats: dict[str, dict] | None = None,
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

        # Build field positioning block
        field_positioning = ""
        if classification and tier_stats:
            same_topic_stats = tier_stats.get("same_topic", {})
            diversity = classification.topic_diversity
            if diversity is not None and diversity > 0.5:
                diversity_interp = "high cross-disciplinary potential — untapped transfer opportunities"
            elif diversity is not None and diversity > 0.25:
                diversity_interp = "moderate cross-disciplinarity"
            else:
                diversity_interp = "focused within one subfield"

            field_positioning = f"""
FIELD POSITIONING:
- Current position: {classification.primary_domain or 'Unknown'} > {classification.primary_field or 'Unknown'} > {classification.primary_subfield or 'Unknown'} > {classification.primary_topic or 'Unknown'}
- Papers in exact topic: {same_topic_stats.get('papers_with_fwci', 0)} found, median FWCI {same_topic_stats.get('average_fwci', 'N/A')}
- Topic diversity: {diversity_interp}

Higher diversity can mean untapped cross-field transfer opportunities."""

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
{field_positioning}

Based on:
1. The novelty of the research angle (method-to-new-population is usually incremental, not transformative)
2. The researcher's skills and expertise
3. The current state of the field (related papers and their impact)
4. The potential for this specific research to advance knowledge
5. Opportunity cost: Would the researcher's skills be better used elsewhere? Is this problem significant enough to justify their expertise?

Predict the expected impact if this research is completed:
- HIGH: Will likely produce highly-cited, field-advancing work that justifies the researcher's skills
- MEDIUM: Will contribute meaningfully but incrementally to the field
- LOW: Unlikely to have significant impact (e.g. saturated area, weak angle, niche problem that doesn't justify the researcher's expertise)

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

    async def _assess_real_world_impact(
        self,
        research_question: str,
        profile: ResearchProfile | None,
        decomposition: ResearchDecomposition,
        verdict: str,
        papers: list[dict],
    ) -> tuple[str, str]:
        """Assess real-world (non-academic) impact using deliberately harsh criteria.

        Separate from field impact: asks whether answering the question changes
        the lives of non-specialists, creates new tools/methods, or affects
        policy/practice at scale.

        Returns:
            Tuple of (impact_level, reasoning).
        """
        impact_domains = ", ".join(decomposition.potential_impact_domains) or "Not specified"
        skills_text = ""
        if profile:
            skills_text = f"Skills: {', '.join(profile.skills)}" if profile.skills else ""

        prompt = f"""Assess the REAL-WORLD impact of this research — NOT its academic/field impact.

Research Question: {research_question}
Potential Impact Domains: {impact_domains}
Researcher: {skills_text or 'Not specified'}
Novelty Verdict: {verdict}

Apply these HARSH criteria. Be a skeptic, not a cheerleader:

1. SCALE: What fraction of the world's 8 billion people are affected?
   - Billions (disease, food, energy) = HIGH
   - Millions (specific medical condition, regional policy) = MEDIUM
   - Thousands or fewer (niche species, narrow subfield) = LOW

2. TOOLING: Does this create a new method, tool, framework, or dataset that others OUTSIDE the subfield can use?
   - Yes, broadly applicable = boosts toward HIGH
   - No, only advances internal subfield knowledge = does not boost

3. NEWS TEST: Would a non-specialist journalist write about this result?
   - Front page of a major newspaper = HIGH
   - Science section of a newspaper = MEDIUM
   - Only in a specialist journal = LOW

4. COMPARE to these benchmarks:
   - HIGH: Curing a disease, discovering a new material, preventing famine, new energy source
   - MEDIUM: Improving crop yields 10%, better diagnostic for a common condition, new conservation strategy for an endangered ecosystem
   - LOW: Speciating a particular bird species, incremental taxonomy revision, method applied to new population with no broader consequence

5. HONESTY CHECK: If the researcher never did this work, would anyone outside their lab notice within 5 years?

Respond with ONLY valid JSON:
{{"real_world_impact": "HIGH|MEDIUM|LOW", "reasoning": "Be specific: who benefits, how many, and to what degree. Name concrete consequences or their absence."}}"""

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
            impact = result.get("real_world_impact", "LOW")
            reasoning = result.get("reasoning", "No reasoning provided.")
            if impact not in ("HIGH", "MEDIUM", "LOW"):
                impact = "LOW"  # Default to LOW when uncertain — harsh by design
            return impact, reasoning
        except Exception as e:
            logger.error(f"Real-world impact LLM call failed: {e}")
            return "UNCERTAIN", f"Could not assess real-world impact: {e}"

    def _format_paper_summary(self, paper: dict, include_topic: bool = False) -> str:
        """Format a single paper for LLM prompts."""
        abstract = (paper.get("abstract") or "")[:350]
        concepts = paper.get("concepts", [])[:3]
        keywords = paper.get("keywords", [])[:3]
        concepts_str = ", ".join(c[0] for c in concepts) if concepts else "N/A"
        keywords_str = ", ".join(k[0] for k in keywords) if keywords else "N/A"

        line = (
            f"- {paper['title']} (FWCI: {paper.get('fwci', 'N/A')}, "
            f"Year: {paper.get('publication_year', 'N/A')})\n"
            f"  Abstract: {abstract}...\n"
            f"  Concepts: {concepts_str}\n  Keywords: {keywords_str}"
        )

        if include_topic:
            pt = paper.get("primary_topic") or {}
            if pt.get("subfield"):
                line += f"\n  Topic: {pt.get('topic', 'N/A')} (Subfield: {pt['subfield']})"

        return line

    def _format_tier_section(
        self,
        tier_name: str,
        label: str,
        guidance: str,
        papers: list[dict],
        tier_stats: dict[str, dict],
    ) -> str:
        """Format a proximity tier section for LLM prompts."""
        if not papers:
            return ""
        summaries = [self._format_paper_summary(p, include_topic=True) for p in papers]
        stats = tier_stats.get(tier_name, {})
        fwci = stats.get("average_fwci", "N/A")
        n = stats.get("papers_with_fwci", 0)
        return (
            f"\n{label} ({guidance}):\n"
            f"{chr(10).join(summaries)}\n"
            f"  → Tier FWCI: median {fwci} across {n} papers"
        )

    def _format_classification_block(
        self, classification: ResearcherClassification
    ) -> str:
        """Format the researcher's field classification for LLM prompts."""
        diversity = classification.topic_diversity
        if diversity is not None:
            if diversity > 0.5:
                diversity_desc = f"{diversity:.2f} (papers span multiple subfields — high cross-disciplinarity)"
            elif diversity > 0.25:
                diversity_desc = f"{diversity:.2f} (moderate cross-disciplinarity)"
            else:
                diversity_desc = f"{diversity:.2f} (focused within one subfield)"
        else:
            diversity_desc = "N/A"

        return (
            f"RESEARCHER'S FIELD CLASSIFICATION:\n"
            f"- Domain: {classification.primary_domain or 'Unknown'}\n"
            f"- Field: {classification.primary_field or 'Unknown'}\n"
            f"- Subfield: {classification.primary_subfield or 'Unknown'}\n"
            f"- Primary Topic: {classification.primary_topic or 'Unknown'}\n"
            f"- Topic Diversity: {diversity_desc}"
        )

    async def _get_llm_verdict(
        self,
        research_question: str,
        decomposition: ResearchDecomposition,
        papers: list[dict],
        stats: dict,
        classification: ResearcherClassification | None = None,
        proximity_tiers: dict[str, list[dict]] | None = None,
        tier_stats: dict[str, dict] | None = None,
    ) -> dict:
        """Use an LLM to interpret OpenAlex results and determine novelty verdict.

        Papers are presented grouped by topic proximity to the researcher's field,
        giving the LLM structured context to weight prior work appropriately.

        Returns:
            Dict with 'verdict', 'score', and 'reasoning' keys.
        """
        core_questions = "\n".join(f"  - {q}" for q in decomposition.core_questions) or "  N/A"
        motivations = ", ".join(decomposition.core_motivations) or "Not specified"

        # Build classification and proximity sections if available
        classification_block = ""
        papers_block = ""
        proximity_guidance = ""

        if classification and proximity_tiers and tier_stats:
            classification_block = self._format_classification_block(classification)

            papers_block = ""
            papers_block += self._format_tier_section(
                "same_topic",
                "PAPERS IN YOUR EXACT TOPIC (strongest prior-work signal)",
                "direct competition — high weight for SOLVED/MARGINAL",
                proximity_tiers.get("same_topic", []),
                tier_stats,
            )
            papers_block += self._format_tier_section(
                "same_subfield",
                "PAPERS IN ADJACENT SUBFIELDS (related but different focus)",
                "adjacent exploration — reduces novelty but doesn't eliminate it",
                proximity_tiers.get("same_subfield", []),
                tier_stats,
            )
            papers_block += self._format_tier_section(
                "same_field",
                "PAPERS IN SAME FIELD (broader awareness)",
                "awareness-level overlap — weak novelty signal",
                proximity_tiers.get("same_field", []),
                tier_stats,
            )
            papers_block += self._format_tier_section(
                "cross_field",
                "CROSS-FIELD PAPERS (tangential — low weight for novelty)",
                "mention related terms but address different core questions",
                proximity_tiers.get("cross_field", []),
                tier_stats,
            )

            proximity_guidance = """
IMPORTANT: Weight papers by proximity tier when judging novelty:
- Same-topic papers are direct prior work. If 3+ exist with high FWCI, this is likely MARGINAL or SOLVED.
- Same-subfield papers indicate adjacent exploration. They reduce novelty but don't eliminate it.
- Cross-field papers should NOT drive MARGINAL/SOLVED verdicts — they indicate awareness, not competition.
- High topic diversity (>0.5) suggests cross-disciplinary synthesis — potentially NOVEL even with many papers."""
        else:
            # Fallback: flat list (when no topic data available)
            summaries = [self._format_paper_summary(p) for p in papers[:10]]
            papers_block = f"\nRelated Papers Found ({len(papers)} total):\n{chr(10).join(summaries)}"

        prompt = f"""You are evaluating whether a research direction is worth pursuing.

Research Question: {research_question}

Core Questions (what the research aims to answer):
{core_questions}

Core Motivations: {motivations}

{classification_block}
{papers_block}

Overall FWCI Statistics:
- Average FWCI: {stats.get('average_fwci', 'N/A')}
- Papers with FWCI data: {stats.get('papers_with_fwci', 0)}
- Citation percentile range: {stats.get('citation_percentile_min', 'N/A')}-{stats.get('citation_percentile_max', 'N/A')}

For each paper, consider:
1. Does it answer the SAME core question(s), or a related but different question?
2. Similarity: High = same core question; Medium = related subquestion; Low = tangential
3. What remains unanswered?
4. Method-to-new-population: If the research is essentially applying well-established methods to a different species, population, or dataset (e.g., same technique on parakeets instead of finches), that is typically MARGINAL—not NOVEL. True novelty requires new conceptual questions, new methodology, or genuinely unexplored territory.
{proximity_guidance}

Determine the novelty verdict:
- SOLVED: The core research question has been definitively answered in existing literature.
- MARGINAL: Some novelty exists but the area is heavily explored with diminishing returns. This includes "method applied to new population"—established techniques on a slightly different subject. Ask: Is this incremental rather than transformative?
- NOVEL: The research question explores genuinely new territory with significant potential. Not just a new application of old methods.
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
