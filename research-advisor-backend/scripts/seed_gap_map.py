#!/usr/bin/env python3
"""Seed gap map database by scraping all sources and computing embeddings.

Run from project root or research-advisor-backend:
  cd research-advisor-backend && poetry run python scripts/seed_gap_map.py

Uses DATABASE_URL from .env. Requires OXYLABS_USERNAME and OXYLABS_PASSWORD
for scraping (sites block direct fetches). Requires OPENAI_API_KEY for embeddings.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Ensure app is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

# Load .env from project root
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.config import get_settings
from app.services.gap_map_repository import GapMapRepository
from app.services.gap_map_scraper import GapMapScraperOrchestrator

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


async def main() -> int:
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    try:
        async with session_factory() as session:
            repo = GapMapRepository(session)
            orchestrator = GapMapScraperOrchestrator(repository=repo)
            count = await orchestrator.scrape_and_store()
            logger.info("Seeded %d gap map entries (with embeddings)", count)
            return count
    finally:
        await engine.dispose()


if __name__ == "__main__":
    count = asyncio.run(main())
    sys.exit(0 if count >= 0 else 1)
