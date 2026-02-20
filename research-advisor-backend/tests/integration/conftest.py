"""Integration test configuration - set env vars before any app imports."""

import os

# Set required environment variables BEFORE any app module is imported.
# This prevents pydantic Settings validation from failing.
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("OPENALEX_EMAIL", "test@example.com")
