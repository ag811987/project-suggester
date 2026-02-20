"""Background job for periodic gap map scraping."""

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.services.gap_map_repository import GapMapRepository
from app.services.gap_map_scraper import GapMapScraperOrchestrator

logger = logging.getLogger(__name__)


async def run_scraper_job(database_url: str) -> int:
    """Execute a single scraping run.

    Creates its own database session and runs the orchestrator.
    Returns the number of entries upserted.
    """
    engine = create_async_engine(database_url, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with session_factory() as session:
            repository = GapMapRepository(session)
            orchestrator = GapMapScraperOrchestrator(repository=repository)
            count = await orchestrator.scrape_and_store()
            logger.info("Scraper job completed: %d entries upserted", count)
            return count
    finally:
        await engine.dispose()


def setup_scraper_scheduler(
    database_url: str,
    cron_expression: str = "0 2 * * *",
    enabled: bool = True,
) -> AsyncIOScheduler | None:
    """Set up APScheduler for periodic gap map scraping.

    Args:
        database_url: PostgreSQL connection string.
        cron_expression: Cron schedule (default: daily at 2 AM).
        enabled: Whether to start the scheduler.

    Returns:
        The scheduler instance, or None if disabled.
    """
    if not enabled:
        logger.info("Scraper scheduler disabled")
        return None

    scheduler = AsyncIOScheduler()

    # Parse cron expression: "minute hour day month day_of_week"
    parts = cron_expression.split()
    trigger = CronTrigger(
        minute=parts[0],
        hour=parts[1],
        day=parts[2],
        month=parts[3],
        day_of_week=parts[4],
    )

    scheduler.add_job(
        run_scraper_job,
        trigger=trigger,
        args=[database_url],
        id="gap_map_scraper",
        name="Gap Map Scraper Job",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scraper scheduler started with cron: %s", cron_expression)
    return scheduler
