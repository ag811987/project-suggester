"""FastAPI application entry point for the Research Pivot Advisor System."""

import logging
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.config import get_settings
from app.api.routes import router
from app.services.gap_map_repository import GapMapRepository
from app.services.gap_map_scraper import GapMapScraperOrchestrator

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan: startup and shutdown."""
    settings = get_settings()

    # Create async database engine
    engine = create_async_engine(settings.database_url, echo=settings.debug)
    app.state.db_engine = engine
    app.state.db_session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    # Create Redis connection
    app.state.redis = aioredis.from_url(
        settings.redis_url, decode_responses=True
    )

    # Seed gap map database if empty (ensures pivot suggestions are available)
    try:
        async with app.state.db_session_factory() as session:
            result = await session.execute(
                text("SELECT COUNT(*) FROM gap_map_entries")
            )
            count = result.scalar() or 0
        if count == 0:
            logger.info("Gap map database empty, seeding with sample data...")
            async with app.state.db_session_factory() as session:
                repo = GapMapRepository(session)
                orchestrator = GapMapScraperOrchestrator(repository=repo)
                n = await orchestrator.scrape_and_store()
            logger.info("Gap map database seeded with %d entries", n)
    except Exception as e:
        logger.warning("Could not seed gap map database (table may not exist yet): %s", e)

    logger.info("Application started")
    yield

    # Shutdown
    await app.state.redis.aclose()
    await engine.dispose()
    logger.info("Application shut down")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    # Include API routes
    app.include_router(router, prefix=settings.api_v1_prefix)

    return app


app = create_app()
