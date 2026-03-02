# Research Pivot Advisor - Backend

FastAPI backend for the Research Pivot Advisor System.

## Prerequisites

- **PostgreSQL** and **Redis** must be running (use `docker-compose up -d` from the project root)
- **`.env`** file in the project root with `OPENAI_API_KEY` and `OPENALEX_EMAIL` set

See the [root README](../README.md) for full setup instructions.

## Setup

From the project root, after starting Docker:

```bash
cd research-advisor-backend
poetry install
poetry run alembic upgrade head   # Required on first run — creates gap_map_entries table
poetry run uvicorn app.main:app --reload
```

The API runs at `http://localhost:8000`. Interactive docs: `http://localhost:8000/docs`.

## Testing

```bash
poetry run pytest tests/ -v
poetry run pytest tests/ --cov=app --cov-report=html   # With coverage
```

Backend tests require PostgreSQL and Redis. Use the same `docker-compose` services; tests use `research_advisor_test` database (created automatically by test fixtures).

## Environment Variables

See `.env.example` in the project root. The backend loads `.env` from the project root or `research-advisor-backend/`.
