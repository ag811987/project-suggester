"""
Configuration management for the Research Pivot Advisor System.

Uses Pydantic Settings to load and validate environment variables from .env file.
All sensitive data (API keys, credentials) are loaded from environment variables
and never hardcoded.
"""

from functools import lru_cache
from typing import Literal, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All settings can be overridden via .env file or environment variables.
    See .env.example for a complete list of available settings.
    """

    # Application Settings
    app_name: str = Field(
        default="Research Pivot Advisor System",
        description="Name of the application"
    )
    app_version: str = Field(
        default="0.1.0",
        description="Application version"
    )
    environment: Literal["development", "production", "test"] = Field(
        default="development",
        description="Runtime environment"
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level"
    )

    # API Settings
    api_v1_prefix: str = Field(
        default="/api/v1",
        description="API version 1 URL prefix"
    )
    cors_origins: Union[str, list[str]] = Field(
        default="http://localhost:5173,http://localhost:3000",
        description="Allowed CORS origins (Vite dev server by default)"
    )

    # Database Settings
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/research_advisor",
        description="PostgreSQL database URL (async driver)"
    )

    # Redis Settings
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis URL for session storage"
    )
    session_ttl_seconds: int = Field(
        default=3600,
        ge=60,
        le=86400,
        description="Session TTL in seconds (1 hour default, min 1 min, max 24 hours)"
    )

    # OpenAI Settings
    openai_api_key: str = Field(
        ...,
        description="OpenAI API key for GPT-4 access (REQUIRED)"
    )
    openai_model: str = Field(
        default="gpt-4-0125-preview",
        description="OpenAI model to use for LLM operations"
    )
    openai_temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Temperature for OpenAI completions"
    )
    openai_max_tokens: int = Field(
        default=2000,
        ge=100,
        le=4000,
        description="Max tokens for OpenAI completions"
    )

    # OpenAlex Settings
    openalex_email: str = Field(
        ...,
        description="Email for OpenAlex polite pool (REQUIRED for better rate limits)"
    )
    openalex_api_key: str | None = Field(
        default=None,
        description="OpenAlex API key for semantic search (optional, costs $0.01/query)"
    )
    openalex_use_semantic_search: bool = Field(
        default=False,
        description="Use semantic search instead of keyword search (requires API key)"
    )
    openalex_semantic_budget_threshold: float = Field(
        default=0.05,
        ge=0.0,
        description="Skip semantic search when remaining daily budget (USD) is below this"
    )
    openalex_per_page: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Number of results per page from OpenAlex"
    )

    # Oxylabs Settings (Web Scraping)
    oxylabs_username: str | None = Field(
        default=None,
        description="Oxylabs username for proxy service (optional for MVP)"
    )
    oxylabs_password: str | None = Field(
        default=None,
        description="Oxylabs password for proxy service (optional for MVP)"
    )
    scraping_use_oxylabs: bool = Field(
        default=False,
        description="Whether to use Oxylabs for scraping (false = direct HTTP)"
    )

    # FWCI Calibration (OpenAlex FWCI tends to inflate vs SciVal; research suggests ~1.5x)
    # Stricter thresholds reduce false HIGH scores. See docs/FWCI_CALIBRATION.md
    fwci_high_threshold: float = Field(
        default=2.2,
        ge=0.5,
        le=5.0,
        description="FWCI above this = HIGH impact (default 2.2, stricter than OpenAlex raw 1.5)"
    )
    fwci_low_threshold: float = Field(
        default=1.2,
        ge=0.0,
        le=3.0,
        description="FWCI below this = LOW impact (default 1.2). Between low and high = MEDIUM"
    )
    openalex_search_limit: int = Field(
        default=8,
        ge=3,
        le=15,
        description="Number of papers to fetch for novelty analysis (3-10 recommended for tight, closely related results)"
    )
    openalex_multi_query: bool = Field(
        default=True,
        description="Use multi-query strategy for better keyword coverage"
    )
    openalex_queries_per_variant: int = Field(
        default=5,
        ge=2,
        le=10,
        description="Papers to fetch per query variant in multi-query mode"
    )
    openalex_use_embedding_rerank: bool = Field(
        default=False,
        description="Rerank merged papers by embedding similarity to research question"
    )

    # Gap Map Retrieval (Vector Search)
    gap_retrieval_top_k: int = Field(
        default=50,
        ge=10,
        le=200,
        description="Number of gap map entries to retrieve via vector search for pivot matching"
    )
    gap_use_vector_search: bool = Field(
        default=True,
        description="Use vector search for retrieval; fallback to get_all when false or no embeddings"
    )

    # Background Job Settings
    scraper_schedule_cron: str = Field(
        default="0 2 * * *",
        description="Cron expression for gap map scraper job (default: daily at 2 AM)"
    )
    scraper_enabled: bool = Field(
        default=True,
        description="Enable/disable background scraping jobs"
    )

    # Privacy & Security Settings
    delete_user_data_on_expiry: bool = Field(
        default=True,
        description="Automatically delete user session data when TTL expires"
    )
    max_file_size_mb: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum file upload size in MB"
    )
    allowed_file_types: list[str] = Field(
        default=["pdf", "docx", "txt"],
        description="Allowed file types for upload"
    )

    # Model configuration
    # Load .env from backend dir first, then project root (for monorepo layout)
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @field_validator("allowed_file_types", mode="before")
    @classmethod
    def parse_allowed_file_types(cls, v):
        """Parse allowed file types from comma-separated string or list."""
        if isinstance(v, str):
            return [ft.strip().lower() for ft in v.split(",")]
        return v

    @property
    def database_url_sync(self) -> str:
        """
        Get synchronous database URL for Alembic migrations.

        Replaces asyncpg driver with psycopg2 for compatibility.
        """
        return self.database_url.replace(
            "postgresql+asyncpg://",
            "postgresql+psycopg2://"
        )


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    This function is cached to avoid re-reading environment variables
    on every call. Use this function to access settings throughout
    the application.

    Returns:
        Settings: The application settings instance
    """
    return Settings()


# Convenience export
settings = get_settings()
