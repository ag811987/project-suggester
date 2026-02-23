"""Orchestrator for running all gap map scrapers."""

import logging

from openai import AsyncOpenAI

from app.config import get_settings
from app.models.schemas import GapMapEntry
from app.services.embedding_service import EmbeddingService
from app.services.gap_map_embedder import GapMapEmbedder
from app.services.gap_map_repository import GapMapRepository
from app.services.gap_map_topic_enricher import GapMapTopicEnricher
from app.services.openalex_client import OpenAlexClient
from app.services.scrapers.convergent_scraper import ConvergentScraper
from app.services.scrapers.homeworld_scraper import HomeworldScraper
from app.services.scrapers.wikenigma_scraper import WikienigmaScraper
from app.services.scrapers.threeie_scraper import ThreeIEScraper
from app.services.scrapers.encyclopedia_scraper import EncyclopediaScraper

logger = logging.getLogger(__name__)


class GapMapScraperOrchestrator:
    """Orchestrates all gap map scrapers and stores results."""

    def __init__(self, repository: GapMapRepository | None = None):
        settings = get_settings()
        scraper_kwargs = {
            "use_oxylabs": settings.scraping_use_oxylabs,
            "oxylabs_username": settings.oxylabs_username,
            "oxylabs_password": settings.oxylabs_password,
        }
        self.scrapers = [
            ConvergentScraper(**scraper_kwargs),
            HomeworldScraper(**scraper_kwargs),
            WikienigmaScraper(**scraper_kwargs),
            ThreeIEScraper(**scraper_kwargs),
            EncyclopediaScraper(**scraper_kwargs),
        ]
        self.repository = repository

    async def scrape_all(self) -> list[GapMapEntry]:
        """Run all scrapers and return combined entries."""
        all_entries: list[GapMapEntry] = []

        for scraper in self.scrapers:
            try:
                entries = await scraper.scrape()
                all_entries.extend(entries)
                logger.info(
                    "Scraped %d entries from %s", len(entries), scraper.source_name
                )
            except Exception:
                logger.exception("Failed to scrape %s", scraper.source_name)
            finally:
                await scraper.close()

        logger.info("Total entries scraped: %d", len(all_entries))
        return all_entries

    async def scrape_and_store(self) -> int:
        """Run all scrapers and store results in the database.

        After upserting, runs the gap map embedder to compute embeddings
        for entries that need them.

        Returns the number of entries upserted.
        """
        entries = await self.scrape_all()
        if self.repository and entries:
            count = await self.repository.upsert(entries)
            logger.info("Upserted %d entries to database", count)
            settings = get_settings()
            embedder = GapMapEmbedder(
                embedding_service=EmbeddingService(api_key=settings.openai_api_key),
                repository=self.repository,
            )
            embedded = await embedder.embed_pending()
            if embedded:
                logger.info("Embedded %d gap map entries", embedded)

            # Step 3: Enrich entries missing OpenAlex taxonomy
            openalex_client = OpenAlexClient(
                email=settings.openalex_email,
                api_key=settings.openalex_api_key,
            )
            try:
                enricher = GapMapTopicEnricher(
                    openalex_client=openalex_client,
                    openai_client=AsyncOpenAI(api_key=settings.openai_api_key),
                    repository=self.repository,
                    openai_model=settings.openai_model,
                )
                enriched = await enricher.enrich_pending()
                if enriched:
                    logger.info("Enriched %d gap map entries with taxonomy", enriched)
            finally:
                await openalex_client.close()

            return count
        return 0
