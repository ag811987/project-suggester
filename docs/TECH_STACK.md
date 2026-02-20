# Research Pivot Advisor System - Technology Stack

## Overview
This document defines the exact technologies, libraries, and versions to use. **Follow this precisely** to avoid decision paralysis.

## Backend Stack

### Core Framework
- **FastAPI**: `^0.109.0` - Modern async web framework
- **Python**: `3.11+` - Required for modern type hints
- **Uvicorn**: `^0.27.0` - ASGI server with auto-reload

### Database & Storage
- **PostgreSQL**: `15+` - For gap map entries (public data only)
  - Use via Docker: `postgres:15-alpine`
- **Redis**: `7+` - For session storage (ephemeral user data)
  - Use via Docker: `redis:7-alpine`
- **SQLAlchemy**: `^2.0` - Async ORM
  - Driver: `asyncpg` for PostgreSQL
- **Alembic**: `^1.13.0` - Database migrations
- **redis-py**: `^5.0` - Redis client with async support

### AI & NLP
- **OpenAI**: `^1.10.0` - GPT-4 for LLM operations
  - Use: `gpt-4-0125-preview` model
  - Enable structured outputs with Pydantic
- **LangChain**: `^0.1.0` - LLM orchestration (optional, use if needed)
  - Packages: `langchain-openai`, `langchain-core`

### Research & Literature APIs
- **pyalex**: `^0.13` - OpenAlex API client
  - For novelty analysis and FWCI metrics
  - Use polite pool with email header

### Web Scraping
- **httpx**: `^0.26.0` - Async HTTP client
  - Use for Oxylabs proxy requests
- **beautifulsoup4**: `^4.12.0` - HTML parsing
  - Parser: `lxml`
- **lxml**: `^5.1.0` - Fast XML/HTML parser

### Document Processing
- **pypdf**: `^4.0.0` - PDF parsing (prefer over PyPDF2)
- **python-docx**: `^1.1.0` - DOCX parsing
- **python-multipart**: `^0.0.6` - File upload handling in FastAPI

### Background Jobs
- **APScheduler**: `^3.10.0` - Simple job scheduler
  - Use: `AsyncIOScheduler` for async jobs
  - Alternative: Celery (heavier, use if needed for scale)

### Utilities
- **pydantic**: `^2.6.0` - Data validation (comes with FastAPI)
- **pydantic-settings**: `^2.1.0` - Settings management from .env
- **python-dotenv**: `^1.0.0` - Load environment variables
- **loguru**: `^0.7.0` - Structured logging (better than logging module)

### Development Tools
- **pytest**: `^8.0.0` - Testing framework
- **pytest-asyncio**: `^0.23.0` - Async test support
- **pytest-mock**: `^3.12.0` - Mocking utilities
- **httpx-mock**: `^0.15.0` - Mock HTTP requests
- **ruff**: `^0.2.0` - Fast linter and formatter
- **mypy**: `^1.8.0` - Type checking

### Backend Dependencies Summary
```toml
[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.109.0"
uvicorn = {extras = ["standard"], version = "^0.27.0"}
sqlalchemy = {extras = ["asyncio"], version = "^2.0"}
asyncpg = "^0.29.0"
alembic = "^1.13.0"
redis = "^5.0"
openai = "^1.10.0"
pyalex = "^0.13"
httpx = "^0.26.0"
beautifulsoup4 = "^4.12.0"
lxml = "^5.1.0"
pypdf = "^4.0.0"
python-docx = "^1.1.0"
python-multipart = "^0.0.6"
apscheduler = "^3.10.0"
pydantic-settings = "^2.1.0"
python-dotenv = "^1.0.0"
loguru = "^0.7.0"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0.0"
pytest-asyncio = "^0.23.0"
pytest-mock = "^3.12.0"
httpx-mock = "^0.15.0"
ruff = "^0.2.0"
mypy = "^1.8.0"
```

## Frontend Stack

### Core Framework
- **React**: `^18.2.0` - UI library
- **TypeScript**: `^5.3.0` - Type safety
- **Vite**: `^5.0.0` - Build tool (fast HMR)

### UI Components & Styling
- **Shadcn UI**: Latest - Pre-built accessible components
  - Install via CLI: `npx shadcn-ui@latest init`
  - Components needed: Button, Card, Input, Textarea, Progress, Alert, Dialog
- **Tailwind CSS**: `^3.4.0` - Utility-first CSS
- **Tailwind Merge**: `^2.2.0` - Merge Tailwind classes
- **clsx**: `^2.1.0` - Conditional class names
- **Lucide React**: `^0.309.0` - Icon library (used by Shadcn)

### State Management & Data Fetching
- **TanStack Query (React Query)**: `^5.17.0` - Server state management
  - Use for all API calls, never useEffect for fetching
- **Zustand**: `^4.5.0` (optional) - Client state (if needed beyond React Context)

### Form Handling
- **React Hook Form**: `^7.49.0` - Form state management
- **Zod**: `^3.22.0` - Schema validation (works with React Hook Form)

### Routing
- **React Router**: `^6.21.0` - Client-side routing
  - Use loader pattern for data fetching with TanStack Query

### HTTP Client
- **axios**: `^1.6.0` - HTTP client
  - Configure base URL and interceptors for session handling

### File Upload
- **react-dropzone**: `^14.2.0` - Drag-and-drop file upload

### Development Tools
- **ESLint**: `^8.56.0` - Linting
- **Prettier**: `^3.2.0` - Code formatting
- **TypeScript ESLint**: `^6.19.0` - TypeScript linting rules

### Frontend Dependencies Summary
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.21.0",
    "@tanstack/react-query": "^5.17.0",
    "axios": "^1.6.0",
    "react-hook-form": "^7.49.0",
    "zod": "^3.22.0",
    "react-dropzone": "^14.2.0",
    "tailwindcss": "^3.4.0",
    "tailwind-merge": "^2.2.0",
    "clsx": "^2.1.0",
    "lucide-react": "^0.309.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.48",
    "@types/react-dom": "^18.2.18",
    "@vitejs/plugin-react": "^4.2.1",
    "typescript": "^5.3.0",
    "vite": "^5.0.0",
    "eslint": "^8.56.0",
    "prettier": "^3.2.0"
  }
}
```

## External Services

### Required API Keys (in .env)
1. **OpenAI API** - For GPT-4 LLM operations
   - Key: `OPENAI_API_KEY`
   - Model: `gpt-4-0125-preview` or latest

2. **OpenAlex** - For research paper analysis
   - Key: Not required, but provide email for polite pool
   - Config: `OPENALEX_EMAIL`

3. **Oxylabs** - For web scraping gap maps
   - Keys: `OXYLABS_USERNAME`, `OXYLABS_PASSWORD`
   - Plan: Pay-as-you-go or trial

### Optional Services
- **Sentry** - Error tracking (production)
- **Posthog** - Analytics (if needed)

## Development Environment

### Docker Compose Setup
```yaml
version: '3.8'
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: research_advisor
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru

volumes:
  postgres_data:
```

### Environment Variables Template
See `.env.example` for complete list.

## Architecture Decisions

### Why These Choices?

1. **FastAPI over Flask/Django**
   - Native async support (required for parallel API calls)
   - Built-in Pydantic validation
   - Auto-generated OpenAPI docs

2. **PostgreSQL over NoSQL**
   - Gap map data is structured and relational
   - Need ACID guarantees for scrapers (upsert pattern)
   - Supports full-text search for matching

3. **Redis over Database Sessions**
   - Privacy: User data auto-expires (TTL)
   - Performance: Faster than database queries
   - Simplicity: No need for session cleanup jobs

4. **APScheduler over Celery**
   - Simpler setup (no message broker)
   - Sufficient for periodic scraping jobs
   - Can upgrade to Celery later if needed

5. **Shadcn UI over Material-UI**
   - Accessible by default (WCAG compliant)
   - Copy-paste components (no bloated package)
   - Tailwind-first (consistent styling)

6. **TanStack Query over Redux**
   - Server state is different from client state
   - Built-in caching and refetching
   - Less boilerplate

## Performance Targets

- API Response Time: < 5s for novelty analysis
- Background Scraping: Complete all sources in < 10 minutes
- Frontend Initial Load: < 2s
- Redis TTL: 1 hour (configurable)

## Security Considerations

- All API keys in environment variables
- HTTPS required in production
- CORS configured for frontend domain only
- Rate limiting on all public endpoints
- SQL injection prevented by SQLAlchemy parameterization
- XSS prevented by React's escaping
