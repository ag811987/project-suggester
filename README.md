# Research Pivot Advisor System

An AI-powered research advisor that analyzes academic research questions for novelty, assesses impact using bibliometric data, identifies knowledge gaps, and suggests strategic research pivots.

## Key Features

- **Research Profile Extraction** — Parse research questions from chat or uploaded documents (PDF, DOCX, TXT)
- **Novelty Assessment** — LLM-based analysis with verdicts: NOVEL, SOLVED, MARGINAL, UNCERTAIN
- **Bibliometric Impact Analysis** — FWCI (Field-Weighted Citation Impact) metrics via OpenAlex
- **Gap Map Discovery** — Aggregated knowledge gaps from 5 curated sources (Convergent Research, Homeworld Bio, Wikenigma, 3ie, Encyclopedia of World Problems)
- **Pivot Suggestions** — AI-matched research pivots ranked by relevance and impact
- **Narrative Reports** — Comprehensive recommendations with citations and evidence
- **Privacy-First Design** — User research data stored only in ephemeral Redis sessions (auto-expire); only public gap map data persists in PostgreSQL

## Architecture

```
┌─────────────────────┐     ┌─────────────────────────────────┐
│   React Frontend    │     │       FastAPI Backend            │
│   (Vite + TS)       │────▶│                                 │
│   Port 5173         │     │  ┌───────────┐  ┌────────────┐  │
└─────────────────────┘     │  │  Info      │  │  Novelty   │  │
                            │  │ Collector  │  │  Analyzer  │  │
                            │  └───────────┘  └────────────┘  │
                            │  ┌───────────┐  ┌────────────┐  │
                            │  │  Pivot     │  │  Report    │  │
                            │  │  Matcher   │  │ Generator  │  │
                            │  └───────────┘  └────────────┘  │
                            │       Port 8000                 │
                            └──────┬──────────────┬───────────┘
                                   │              │
                            ┌──────▼──────┐ ┌─────▼──────┐
                            │ PostgreSQL  │ │   Redis    │
                            │ (Gap Maps)  │ │ (Sessions) │
                            │ Port 5432   │ │ Port 6379  │
                            └─────────────┘ └────────────┘
```

## Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **Docker & Docker Compose** (for PostgreSQL and Redis)
- **Poetry** (Python dependency manager)

## Quick Start

### 1. Clone and Configure

```bash
git clone <repository-url>
cd Project-Suggester
cp .env.example .env
```

Edit `.env` and set your API keys:
```bash
OPENAI_API_KEY=sk-your-key-here
OPENALEX_EMAIL=your.email@example.com
```

### 2. Start Infrastructure Services

```bash
docker-compose up -d
```

This starts PostgreSQL 15 and Redis 7 with health checks.

### 3. Install & Start Backend

```bash
cd research-advisor-backend
poetry install
poetry run uvicorn app.main:app --reload
```

The API is available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### 4. Install & Start Frontend

```bash
cd research-advisor-frontend
npm install
npm run dev
```

The UI is available at `http://localhost:5173`.

## Running Tests

Run the full test suite from the project root:

```bash
./run_all_tests.sh
```

This runs:
- **Backend**: 138 unit + integration tests with coverage report
- **Frontend**: 49 component + API client tests

### Backend Tests Only

```bash
cd research-advisor-backend
poetry run pytest tests/ -v --cov=app --cov-report=term-missing
```

### Frontend Tests Only

```bash
cd research-advisor-frontend
npm test -- --run
```

### Coverage Reports

After running tests:
- Backend HTML report: `research-advisor-backend/htmlcov/index.html`
- Frontend coverage: run `npx vitest --run --coverage`

## API Endpoints

All endpoints are prefixed with `/api/v1`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/analyze` | Submit research question + files for analysis |
| `GET` | `/api/v1/analysis/{session_id}` | Retrieve analysis results |
| `POST` | `/api/v1/chat` | Follow-up chat within a session |
| `DELETE` | `/api/v1/session/{session_id}` | Delete session data |

Full interactive API docs available at `http://localhost:8000/docs` when the backend is running.

## Environment Variables

See [.env.example](.env.example) for all configuration options.

**Required:**
| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key for LLM operations |
| `OPENALEX_EMAIL` | Email for OpenAlex polite pool access |

**Optional:**
| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/research_advisor` | PostgreSQL connection |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |
| `SESSION_TTL_SECONDS` | `3600` | Session expiry (seconds) |
| `OPENALEX_API_KEY` | — | OpenAlex API key (improves rate limits) |
| `OXYLABS_USERNAME` | — | Oxylabs proxy username |
| `OXYLABS_PASSWORD` | — | Oxylabs proxy password |

## Privacy & Data Handling

- **User research data** (questions, uploaded documents, analysis results) is stored **only in Redis** with automatic TTL expiration (default: 1 hour)
- **No user data is persisted to disk** — Redis is configured with `appendonly no`
- **PostgreSQL stores only public gap map data** scraped from open sources
- Sessions can be explicitly deleted via `DELETE /api/v1/session/{session_id}`

## Tech Stack

**Backend:** FastAPI, SQLAlchemy (async), Pydantic V2, OpenAI, PyAlex, APScheduler
**Frontend:** React 18, TypeScript, Vite, TanStack Query, Tailwind CSS, Axios
**Infrastructure:** PostgreSQL 15, Redis 7, Docker Compose

## Project Structure

```
Project-Suggester/
├── research-advisor-backend/
│   ├── app/
│   │   ├── api/routes.py          # API endpoints
│   │   ├── config.py              # Settings management
│   │   ├── main.py                # FastAPI app entry point
│   │   ├── models/                # Pydantic + SQLAlchemy models
│   │   ├── services/              # Business logic
│   │   └── jobs/                  # Background scraper jobs
│   └── tests/                     # Backend tests (138 tests)
├── research-advisor-frontend/
│   └── src/
│       ├── api/                   # API client
│       ├── components/            # React components
│       ├── hooks/                 # React Query hooks
│       └── types/                 # TypeScript interfaces
├── docker-compose.yml             # PostgreSQL + Redis
├── run_all_tests.sh               # Full test suite runner
├── .env.example                   # Environment template
└── docs/                          # Documentation
```
