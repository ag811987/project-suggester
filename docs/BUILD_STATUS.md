# Build Status - Research Pivot Advisor System

## Current Status: PHASE 5 COMPLETE ✅ — ALL PHASES DONE

**Last Updated:** 2026-02-20

---

## Recent Updates (Multi-Query Search)

**2026-02-20: Additive Multi-Query Search Improvements**
- **Multi-query keyword:** Run 3-5 query variants (key_concepts OR, core_questions[0], shortened, phrase) in parallel, merge and rank by query_count + relevance_score.
- **Preserved:** Semantic + keyword hybrid when budget allows; budget fallback to keyword-only.
- **Fallback when empty:** Full research_question, then ultra-broad (3 concepts OR 3 words).
- **Optional embedding rerank:** `OPENALEX_USE_EMBEDDING_RERANK` reranks merged papers by cosine similarity.
- **Config:** `OPENALEX_MULTI_QUERY` (default true), `OPENALEX_QUERIES_PER_VARIANT` (5), `OPENALEX_USE_EMBEDDING_RERANK` (false).
- **OpenAlexClient:** Added `relevance_score` to normalized papers.

---

## Recent Updates (Relevance Quality Fix)

**2026-02-20: Tighten OpenAlex retrieval to reduce unrelated classics/tools**
- **Tighter matching:** Multi-query keyword search now uses OpenAlex `title_and_abstract.search` instead of broad `/works?search=...` to reduce famous-but-irrelevant results.
- **Heuristic rerank:** Added lightweight local relevance filter/rerank (term overlap with specific key concepts) to down-rank generic methods/guidelines when they only match broad terms.
- **Stability:** Sanitized `title_and_abstract.search` filter query strings to avoid intermittent OpenAlex 400s on punctuation/long titles.

---

## Recent Updates (Hybrid Semantic + Keyword Search)

**2026-02-20: Hybrid Semantic + Keyword Search with Budget Fallback**
- **Hybrid search:** When budget allows, runs semantic + keyword search in parallel, merges and dedupes by paper ID (semantic results first).
- **Budget fallback:** When remaining daily API budget < threshold (default $0.05), falls back to keyword-only flow to avoid 429s.
- **OpenAlexClient:** Added `get_remaining_budget_usd()` using `/rate-limit` endpoint; fixed semantic cost docstring ($0.01/query).
- **Config:** `OPENALEX_SEMANTIC_BUDGET_THRESHOLD` (default 0.05).
- **Tests:** `get_remaining_budget_usd`, `_merge_papers`, hybrid vs keyword-only paths.

---

## Recent Updates (Real-World Impact & FWCI Calibration)

**2026-02-20: Real-World Impact Assessment & FWCI Calibration**
- **Real-World Impact Section:** New report section assessing how the world changes if the question is answered—downstream consequences, future knowledge production, problem solving. Explicit comparison vs. gap map entries (curated high-impact problems). Prompt asks: Is this research justified vis-a-vis our gap maps? Would their skills be better used elsewhere?
- **FWCI Calibration:** OpenAlex FWCI tends to inflate (~1.5x vs SciVal). Added configurable thresholds: `FWCI_HIGH_THRESHOLD` (default 2.2), `FWCI_LOW_THRESHOLD` (default 1.2). Stricter than raw Snowball (1.5, 0.8) to reduce false HIGH scores. See `docs/FWCI_CALIBRATION.md`.
- **ReportSections:** Added `real_world_impact_section`. Frontend displays new section when present.

---

## Recent Updates (Scalable Retrieval & Evaluation)

**2026-02-11: Scalable Retrieval and Evaluation Framework**
- **Phase A – Retrieval:** pgvector setup (Docker image `pgvector/pgvector:pg15`), Alembic migration for `embedding` column (vector 1536) and ivfflat index; `EmbeddingService` (OpenAI text-embedding-3-small); `GapMapEmbedder` (batch embed after scrape); `GapRetriever` (vector similarity search); routes wired to use `GapRetriever` with fallback to `get_all` when embeddings missing or vector search disabled
- **Phase B – Evaluation:** `tests/evaluation/benchmarks/novelty_benchmark.json` (8 cases); `test_novelty_regression.py` (mocked OpenAlex/LLM); `run_evaluation.py` CLI with `--live` and `--json`; pytest markers `evaluation`, `slow`
- Config: `GAP_RETRIEVAL_TOP_K` (default 50), `GAP_USE_VECTOR_SEARCH` (default true)

---

## Recent Updates (Novelty & Impact Analysis)

**2026-02-11: Novelty and Impact Analysis Improvements**
- Added `ResearchDecomposition` schema and decomposition step before OpenAlex query
- Enriched OpenAlex `_normalize_paper` with abstract (decoded from inverted index), concepts, keywords
- Redesigned prompts with expert research advisor role; LLM-based impact assessment (not just FWCI thresholds)
- Added optional semantic search (`OPENALEX_USE_SEMANTIC_SEARCH`, `/find/works`)
- Added multi-query search using decomposition core questions
- Config: `OPENALEX_USE_SEMANTIC_SEARCH`, `OPENALEX_API_KEY`

---

## Phase Progress

### Phase 1: Foundation ✅ COMPLETE
- [x] Task 1.1: Project Structure Setup
  - Created `research-advisor-backend/` directory structure
  - Created `research-advisor-frontend/` directory structure
  - Created all required `__init__.py` files for Python packages
- [x] Task 1.2: Backend Schemas
  - Created `app/models/schemas.py` with ALL Pydantic models:
    - Citation, ChatMessage, ResearchProfile
    - NoveltyAssessment, GapMapEntry
    - PivotSuggestion, ResearchRecommendation
    - API request/response models
  - Created `app/models/gap_map_models.py` with SQLAlchemy GapMapEntry model
- [x] Task 1.3: Backend Config & Dependencies
  - Created `pyproject.toml` with Poetry configuration (Python ^3.11)
  - Created `app/config.py` with Pydantic Settings for env vars
  - Created `.env.example` with all required configuration keys
  - Verified `docker-compose.yml` (PostgreSQL 15 + Redis 7) ✅

### Phase 2: Parallel Backend Development ✅ COMPLETE
- [x] Agent 2A: Information Collection Service ✅ COMPLETE
- [x] Agent 2B: Novelty & Impact Analyzer ✅ COMPLETE
- [x] Agent 2C: Gap Map Database & Scrapers ✅ COMPLETE
- [x] Agent 2D: Pivot Matcher & Report Generator ✅ COMPLETE

### Phase 3: Parallel Frontend Development ✅ COMPLETE
- [x] Agent 3A: Chat Interface & File Upload ✅ COMPLETE
- [x] Agent 3B: Results View & API Client ✅ COMPLETE

### Phase 4: Backend API Integration ✅ COMPLETE
- [x] Task 4.1: FastAPI Endpoints (routes.py with /analyze, /analysis/{id}, /chat, /session/{id})
- [x] Task 4.2: App entry point with lifespan (main.py with DB + Redis init)
- [x] Task 4.3: Integration tests (13 tests covering all endpoints)

### Phase 5: End-to-End Testing & Validation ✅ COMPLETE
- [x] Task 5.1: Docker services verified (PostgreSQL + Redis healthy)
- [x] Task 5.2: Complete test suite validation — 187/187 tests passing
  - Backend: 138 tests passed, 87% coverage
  - Frontend: 49 tests passed, 88% coverage
- [x] Task 5.3: Documentation & deploy prep
  - Root README.md created with setup instructions
  - .env.example verified (all required keys present)
  - Docker Compose verified (services healthy)

---

## Active Agents

*All phases complete — no agents running*

---

## Agent 3A: Chat Interface & File Upload ✅ COMPLETE

**Completed:** 2026-02-10 19:21:00
**Validation:** `./validate_agent.sh 3A` PASSED
**Test Results:** 19/19 tests passing

### Files Created:
- `research-advisor-frontend/package.json` - Project config with all dependencies
- `research-advisor-frontend/index.html` - Entry HTML
- `research-advisor-frontend/vite.config.ts` - Vite configuration
- `research-advisor-frontend/vitest.config.ts` - Vitest test configuration (jsdom, globals)
- `research-advisor-frontend/tsconfig.json` - TypeScript configuration
- `research-advisor-frontend/tailwind.config.js` - Tailwind CSS configuration
- `research-advisor-frontend/postcss.config.js` - PostCSS configuration
- `research-advisor-frontend/src/main.tsx` - App entry point
- `research-advisor-frontend/src/App.tsx` - Root component
- `research-advisor-frontend/src/index.css` - Tailwind base styles
- `research-advisor-frontend/src/vite-env.d.ts` - Vite type declarations
- `research-advisor-frontend/src/lib/utils.ts` - cn() utility for Tailwind class merging
- `research-advisor-frontend/src/test/setup.ts` - Test setup (jest-dom matchers)
- `research-advisor-frontend/src/components/chat-interface.tsx` - Chat interface component
- `research-advisor-frontend/src/components/chat-interface.test.tsx` - Chat interface tests (10 tests)
- `research-advisor-frontend/src/components/file-upload.tsx` - File upload component
- `research-advisor-frontend/src/components/file-upload.test.tsx` - File upload tests (9 tests)

---

## Agent 3B: Results View & API Client ✅ COMPLETE

**Completed:** 2026-02-10 19:23:30
**Validation:** `./validate_agent.sh 3B` PASSED
**Test Results:** 30/30 tests passing (11 API client + 19 results view)

### Files Created:
- `research-advisor-frontend/src/types/index.ts` - TypeScript interfaces matching backend Pydantic models
- `research-advisor-frontend/src/api/client.ts` - Axios API client (analyzeResearch, getAnalysis, sendChatMessage, deleteSession)
- `research-advisor-frontend/src/api/client.test.ts` - API client tests (11 tests)
- `research-advisor-frontend/src/hooks/useAnalysis.ts` - TanStack Query hooks (useAnalyzeResearch, useGetAnalysis, useSendMessage)
- `research-advisor-frontend/src/components/results-view.tsx` - Results display component with recommendation badge, novelty assessment, pivot cards, citations
- `research-advisor-frontend/src/components/results-view.test.tsx` - Results view tests (19 tests)

### Dependencies Added:
- `@tanstack/react-query` - Data fetching with React Query
- `axios` - HTTP client

### Configuration Updated:
- `vite.config.ts` - Added Vitest test configuration (globals, jsdom, setup file)

---

## Agent 2B: Novelty & Impact Analyzer ✅ COMPLETE

**Completed:** 2026-02-10
**Validation:** `./validate_agent.sh 2B` PASSED
**Test Results:** 39/39 tests passing (18 openalex client + 21 novelty analyzer)

### Files Created:
- `research-advisor-backend/app/services/openalex_client.py` - OpenAlexClient class: async search_papers(), FWCI extraction with None handling, calculate_fwci_stats(), polite pool email header, API key support
- `research-advisor-backend/app/services/novelty_analyzer.py` - NoveltyAnalyzer class: LLM-based verdict (SOLVED/MARGINAL/NOVEL/UNCERTAIN), FWCI-based impact (HIGH/MEDIUM/LOW), citation building, error handling with UNCERTAIN fallback
- `research-advisor-backend/tests/test_openalex_client.py` - 18 tests: client init, search_papers field extraction, limit param, empty results, None FWCI handling, missing keys, API timeout/connection/HTTP/rate-limit errors, FWCI stats calculation with None/empty/mixed data
- `research-advisor-backend/tests/test_novelty_analyzer.py` - 21 tests: impact thresholds (HIGH/MEDIUM/LOW/UNCERTAIN + boundaries), verdict logic (NOVEL/SOLVED/MARGINAL/UNCERTAIN), FWCI integration (high/medium/low/none/mixed), citations from papers, error handling (OpenAlex failure, LLM failure)

### Coverage (Agent 2B files):
- `openalex_client.py`: 89% coverage
- `novelty_analyzer.py`: 94% coverage

### Impact Assessment Thresholds:
- HIGH: avg FWCI > 1.5
- MEDIUM: 0.8 <= avg FWCI <= 1.5
- LOW: avg FWCI < 0.8
- UNCERTAIN: no FWCI data available

### 2026-02-11 Enhancements:
- Research problem decomposition (core questions, motivations, impact domains) before literature search
- Abstract, concepts, keywords passed to LLM for similarity and core-question overlap judgment
- LLM-based impact assessment using FWCI as evidence; expert role prompts
- Optional semantic search; multi-query using decomposition

---

## Agent 2C: Gap Map Database & Scrapers ✅ COMPLETE

**Completed:** 2026-02-10
**Validation:** `./validate_agent.sh 2C` PASSED
**Test Results:** 28/28 tests passing (11 repository + 17 scrapers/orchestrator)

### Files Created:
- `research-advisor-backend/app/services/gap_map_repository.py` - GapMapRepository class with async SQLAlchemy upsert, get_all, get_by_category, get_by_source
- `research-advisor-backend/app/services/scrapers/__init__.py` - Scrapers package
- `research-advisor-backend/app/services/scrapers/base_scraper.py` - BaseScraper abstract class
- `research-advisor-backend/app/services/scrapers/convergent_scraper.py` - Convergent Research scraper (4 hardcoded entries)
- `research-advisor-backend/app/services/scrapers/homeworld_scraper.py` - Homeworld Bio scraper (4 hardcoded entries)
- `research-advisor-backend/app/services/scrapers/wikenigma_scraper.py` - Wikenigma scraper (3 hardcoded entries)
- `research-advisor-backend/app/services/scrapers/threeie_scraper.py` - 3ie Impact scraper (3 hardcoded entries)
- `research-advisor-backend/app/services/scrapers/encyclopedia_scraper.py` - Encyclopedia of World Problems scraper (3 hardcoded entries)
- `research-advisor-backend/app/services/gap_map_scraper.py` - GapMapScraperOrchestrator (scrape_all + scrape_and_store)
- `research-advisor-backend/app/jobs/gap_map_scraper_job.py` - APScheduler job setup (daily at 2 AM)
- `research-advisor-backend/tests/test_gap_map_repository.py` - 11 tests: upsert insert/update/no-duplicate, get_all, get_by_category, get_by_source, scraped_at timestamp
- `research-advisor-backend/tests/test_scrapers.py` - 17 tests: base scraper abstract, 5 scraper validations, orchestrator all-sources/valid-entries/scraper-count

### Coverage (Agent 2C files):
- `gap_map_repository.py`: 100% coverage
- `gap_map_scraper.py`: 74% coverage
- `base_scraper.py`: 100% coverage
- All 5 scrapers: 100% coverage each

### Dependencies Added:
- `greenlet` - Required for async SQLAlchemy operations

---

## Agent 2D: Pivot Matcher & Report Generator ✅ COMPLETE

**Completed:** 2026-02-10
**Validation:** `./validate_agent.sh 2D` PASSED
**Test Results:** 26/26 tests passing (11 pivot matcher + 15 report generator)

### Files Created:
- `research-advisor-backend/app/services/pivot_matcher.py` - PivotMatcher class with LLM-based matching, relevance×impact ranking, top-N selection
- `research-advisor-backend/app/services/report_generator.py` - ReportGenerator class with CONTINUE/PIVOT/UNCERTAIN decision logic, LLM narrative generation, fallback report
- `research-advisor-backend/tests/test_pivot_matcher.py` - 11 tests: matching algorithm, ranking, top-N, empty inputs, invalid JSON, LLM errors, gap index validation, score clamping
- `research-advisor-backend/tests/test_report_generator.py` - 15 tests: decision logic (SOLVED→PIVOT, MARGINAL→PIVOT, LOW→PIVOT, NOVEL+HIGH→CONTINUE, NOVEL+MEDIUM→CONTINUE, UNCERTAIN→UNCERTAIN), report output, citations, LLM failure handling

### Coverage (Agent 2D files):
- `pivot_matcher.py`: 82% coverage
- `report_generator.py`: 94% coverage

### Dependencies Updated:
- Fixed `pyproject.toml`: `httpx-mock` → `pytest-httpx`, updated `httpx`, `pytest`, `pytest-asyncio` versions for compatibility
- Added `pytest-cov` for coverage reporting

---

## Agent 2A: Information Collection Service ✅ COMPLETE

**Completed:** 2026-02-10 19:35:00
**Validation:** `./validate_agent.sh 2A` PASSED
**Test Results:** 32/32 tests passing (17 document parser + 15 info collector)

### Files Created:
- `research-advisor-backend/app/services/document_parser.py` - DocumentParser class: parse_pdf (pypdf), parse_docx (python-docx), parse_txt, generic parse_file with extension routing, error handling with ValueError
- `research-advisor-backend/app/services/info_collector.py` - InfoCollectionService class: async extract_from_chat (multi-turn conversation), async extract_from_text (with source_filename), merge_profiles (deduplication), OpenAI structured JSON extraction, _parse_profile validation
- `research-advisor-backend/tests/test_document_parser.py` - 17 tests: TXT content/multiline/utf8/empty, PDF single-page/multi-page/empty-pages/error, DOCX paragraphs/empty/skip-empty/error, parse_file routing for pdf/docx/txt, unsupported format, case-insensitive extensions
- `research-advisor-backend/tests/test_info_collector.py` - 15 tests: chat extraction valid/multi-message/empty/llm-error/invalid-json/incomplete-json, text extraction valid/empty/file-context, merge profiles combine/single/empty/deduplicate, OpenAI payload, fixture validation

### Coverage (Agent 2A files):
- `document_parser.py`: 97% coverage
- `info_collector.py`: 92% coverage

---

## Completed Tasks

### Phase 1 - Foundation (Completed: 2026-02-10 18:51:18)
1. ✅ Complete directory structure created
2. ✅ `app/models/schemas.py` - All Pydantic V2 models with detailed docstrings
3. ✅ `app/models/gap_map_models.py` - SQLAlchemy async model with indexes
4. ✅ `pyproject.toml` - Poetry configuration with all dependencies
5. ✅ `app/config.py` - Pydantic Settings for environment management
6. ✅ `.env.example` - Template for environment variables
7. ✅ Verified `docker-compose.yml` configuration

---

## Blockers

*No blockers — project complete*

---

## Notes

### Phase 1 Completion Notes:
- **Python 3.11**: Confirmed installed (Python 3.11.14)
- **Poetry**: Not installed yet (user can install if needed: `curl -sSL https://install.python-poetry.org | python3.11 -`)
- **Directory Structure**: Both backend and frontend directories created
- **Models**: All Pydantic models follow V2 syntax with comprehensive field documentation
- **Configuration**: Settings support development, production, and test environments
- **Database**: SQLAlchemy model ready for async operations with proper indexes

### Project Completion Notes:
All 5 phases completed successfully. The system is fully functional with:
- Full backend API integration with all services wired together
- Complete frontend with chat, file upload, and results display
- 187 tests passing across backend and frontend
- Backend coverage: 87% | Frontend coverage: 88%
- Docker infrastructure running (PostgreSQL + Redis)
- Comprehensive README.md with setup instructions

---

## Time Tracking

- **Start Time:** 2026-02-10 18:51:18
- **Phase 1 Completion:** 2026-02-10 18:51:18
- **Phase 5 Completion:** 2026-02-10 20:45:00
- **Status:** ALL PHASES COMPLETE
