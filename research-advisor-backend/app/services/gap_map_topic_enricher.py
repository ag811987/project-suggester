"""Batch enrichment pipeline for classifying gap map entries into OpenAlex topic taxonomy."""

import asyncio
import json
import logging
from collections import Counter

from openai import AsyncOpenAI

from app.models.gap_map_models import GapMapEntry as GapMapEntryDB
from app.services.gap_map_repository import GapMapRepository
from app.services.openalex_client import OpenAlexClient

logger = logging.getLogger(__name__)

# Delay between OpenAlex queries to stay within rate limits for large batches
_OPENALEX_DELAY_SECONDS = 0.25

# OpenAlex taxonomy reference for LLM fallback classification
_OPENALEX_TAXONOMY = """Domains and Fields:
- Life Sciences: Agricultural and Biological Sciences, Biochemistry Genetics and Molecular Biology, Immunology and Microbiology, Neuroscience, Pharmacology Toxicology and Pharmaceutics
- Health Sciences: Medicine, Dentistry, Health Professions, Nursing, Veterinary
- Physical Sciences: Chemistry, Chemical Engineering, Computer Science, Earth and Planetary Sciences, Energy, Engineering, Environmental Science, Materials Science, Mathematics, Physics and Astronomy
- Social Sciences: Arts and Humanities, Business Management and Accounting, Decision Sciences, Economics Econometrics and Finance, Psychology, Social Sciences"""


class GapMapTopicEnricher:
    """Classifies gap map entries into the OpenAlex topic taxonomy.

    For each entry:
    1. Search OpenAlex with the entry title to find related papers
    2. Extract primary_topic from results and use weighted majority voting
    3. If no papers found or no topics available, fall back to LLM classification
    """

    def __init__(
        self,
        openalex_client: OpenAlexClient,
        openai_client: AsyncOpenAI,
        repository: GapMapRepository,
        openai_model: str = "gpt-4-0125-preview",
    ):
        self._openalex = openalex_client
        self._openai = openai_client
        self._repository = repository
        self._openai_model = openai_model

    async def enrich_pending(self, limit: int = 500) -> int:
        """Enrich entries that have no OpenAlex taxonomy yet.

        Returns the number of entries enriched.
        """
        entries = await self._repository.get_entries_without_taxonomy(limit=limit)
        if not entries:
            logger.debug("No entries without taxonomy to enrich")
            return 0
        logger.info("Enriching %d entries with OpenAlex taxonomy", len(entries))
        return await self._enrich_entries(entries)

    async def _enrich_entries(self, entries: list[GapMapEntryDB]) -> int:
        """Classify each entry and update the database.

        Commits in batches of 50 to avoid losing progress on errors.
        Rolls back the session on DB errors to keep it usable.
        """
        count = 0
        batch_size = 50

        for i, entry in enumerate(entries):
            try:
                taxonomy = await self._classify_entry(entry)
                if taxonomy:
                    await self._repository.update_taxonomy(entry.id, taxonomy)
                    count += 1
                    logger.debug(
                        "Classified '%s' → %s > %s > %s > %s",
                        entry.title[:50],
                        taxonomy.get("domain"),
                        taxonomy.get("field"),
                        taxonomy.get("subfield"),
                        taxonomy.get("topic"),
                    )
            except Exception:
                logger.exception("Failed to classify entry %d: %s", entry.id, entry.title[:50])
                try:
                    await self._repository.session.rollback()
                except Exception:
                    logger.warning("Session rollback also failed")

            # Commit in batches to avoid losing progress
            if (i + 1) % batch_size == 0:
                try:
                    await self._repository.session.commit()
                    logger.info("Committed batch — %d / %d entries processed so far", i + 1, len(entries))
                except Exception:
                    logger.exception("Batch commit failed at entry %d", i + 1)
                    try:
                        await self._repository.session.rollback()
                    except Exception:
                        pass

            # Rate limiting for OpenAlex
            await asyncio.sleep(_OPENALEX_DELAY_SECONDS)

        # Final commit for remaining entries
        try:
            await self._repository.session.commit()
        except Exception:
            logger.exception("Final commit failed")
            try:
                await self._repository.session.rollback()
            except Exception:
                pass

        logger.info("Enriched %d / %d entries with taxonomy", count, len(entries))
        return count

    async def _classify_entry(
        self, entry: GapMapEntryDB, _retries: int = 2
    ) -> dict | None:
        """Classify a single gap entry into the OpenAlex taxonomy.

        Tries OpenAlex paper search first (with retry on empty results
        that may indicate rate limiting), falls back to LLM classification.
        """
        # Step 1: Search OpenAlex with entry title, retry with backoff
        papers: list[dict] = []
        for attempt in range(_retries + 1):
            papers = await self._openalex.search_papers_title_abstract(
                entry.title, limit=5
            )
            if papers:
                break
            if attempt < _retries:
                backoff = 2 ** (attempt + 1)  # 2s, 4s
                logger.debug("No results for '%s', retrying in %ds", entry.title[:40], backoff)
                await asyncio.sleep(backoff)

        # Step 2: If papers have primary_topic data, use majority voting
        topics = [p.get("primary_topic") for p in papers if p.get("primary_topic")]
        if topics:
            return self._vote_on_taxonomy(topics)

        # Step 3: LLM fallback for entries with no good OpenAlex matches
        return await self._llm_classify(entry)

    @staticmethod
    def _vote_on_taxonomy(topics: list[dict]) -> dict:
        """Pick the dominant taxonomy from paper primary_topics using weighted voting.

        Weights each paper's topic by its OpenAlex confidence score.
        Votes independently at each taxonomy level to handle cross-field papers.
        """
        domain_votes: Counter[str] = Counter()
        field_votes: Counter[str] = Counter()
        subfield_votes: Counter[str] = Counter()
        topic_votes: Counter[str] = Counter()

        for t in topics:
            weight = t.get("score") or 1.0
            if t.get("domain"):
                domain_votes[t["domain"]] += weight
            if t.get("field"):
                field_votes[t["field"]] += weight
            if t.get("subfield"):
                subfield_votes[t["subfield"]] += weight
            if t.get("topic"):
                topic_votes[t["topic"]] += weight

        return {
            "domain": domain_votes.most_common(1)[0][0] if domain_votes else None,
            "field": field_votes.most_common(1)[0][0] if field_votes else None,
            "subfield": subfield_votes.most_common(1)[0][0] if subfield_votes else None,
            "topic": topic_votes.most_common(1)[0][0] if topic_votes else None,
        }

    async def _llm_classify(self, entry: GapMapEntryDB) -> dict | None:
        """LLM fallback for entries with no good OpenAlex paper matches."""
        description = (entry.description or "")[:500]
        tags = ", ".join(entry.tags) if entry.tags else "None"

        prompt = f"""Classify this research gap into the OpenAlex academic taxonomy.

Research Gap:
- Title: {entry.title}
- Description: {description}
- Source category: {entry.category or 'None'}
- Tags: {tags}

{_OPENALEX_TAXONOMY}

Choose the BEST-FIT classification at each level. For "topic", provide a specific research topic name (e.g., "CRISPR Gene Editing", "Dark Matter Detection", "Machine Learning for Drug Discovery").

Respond with ONLY valid JSON (no markdown, no code fences):
{{"domain": "...", "field": "...", "subfield": "...", "topic": "..."}}"""

        try:
            response = await self._openai.chat.completions.create(
                model=self._openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an academic classification expert. Return ONLY valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=200,
            )
            content = response.choices[0].message.content.strip()
            result = json.loads(content)
            return {
                "domain": result.get("domain"),
                "field": result.get("field"),
                "subfield": result.get("subfield"),
                "topic": result.get("topic"),
            }
        except Exception as e:
            logger.warning("LLM classification failed for '%s': %s", entry.title[:50], e)
            return None
