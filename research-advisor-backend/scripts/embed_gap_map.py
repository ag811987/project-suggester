#!/usr/bin/env python3
"""Embed gap map entries that have no embedding yet (no scraping).

Run from research-advisor-backend:
  poetry run python scripts/embed_gap_map.py

Uses DATABASE_URL and OPENAI_API_KEY from .env.
"""

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.config import get_settings
from app.services.embedding_service import EmbeddingService
from app.services.gap_map_embedder import GapMapEmbedder
from app.services.gap_map_repository import GapMapRepository

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


async def main() -> int:
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    total = 0
    try:
        while True:
            async with session_factory() as session:
                repo = GapMapRepository(session)
                embedder = GapMapEmbedder(
                    embedding_service=EmbeddingService(api_key=settings.openai_api_key),
                    repository=repo,
                )
                n = await embedder.embed_pending(limit=500)
                total += n
                if n == 0:
                    break
        logger.info("Embedded %d gap map entries total", total)
        return total
    finally:
        await engine.dispose()


if __name__ == "__main__":
    count = asyncio.run(main())
    sys.exit(0 if count >= 0 else 1)
