# Research Pivot Advisor - Backend

FastAPI backend for the Research Pivot Advisor System.

## Setup

```bash
# Install dependencies
poetry install

# Run migrations
poetry run alembic upgrade head

# Start server
poetry run uvicorn app.main:app --reload
```

## Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app --cov-report=html
```

## Environment Variables

See `.env.example` in project root for required configuration.
