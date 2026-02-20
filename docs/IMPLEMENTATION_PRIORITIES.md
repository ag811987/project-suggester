# Implementation Priorities - Research Pivot Advisor System

## Build Strategy: Parallel Execution for 1-Hour Target

This document breaks down the build into phases with **explicit parallelization opportunities**. Use multiple Claude Code agents simultaneously.

---

## Phase 1: Foundation (Sequential) - 10 minutes
**MUST be completed before other phases. No parallelization here.**

### Task 1.1: Project Structure Setup (2 minutes)
- [x] Create directory structure:
  ```
  research-advisor-backend/
  ├── app/
  │   ├── __init__.py
  │   ├── main.py
  │   ├── config.py
  │   ├── models/
  │   │   ├── __init__.py
  │   │   ├── schemas.py
  │   │   └── gap_map_models.py
  │   ├── services/
  │   │   └── __init__.py
  │   ├── api/
  │   │   └── __init__.py
  │   └── jobs/
  │       └── __init__.py
  ├── tests/
  ├── alembic/
  ├── pyproject.toml
  └── .env.example

  research-advisor-frontend/
  ├── src/
  │   ├── components/
  │   ├── api/
  │   ├── hooks/
  │   └── lib/
  ├── public/
  └── package.json
  ```

**Claude Instruction:**
```
Create the complete directory structure for both backend and frontend projects.
Create placeholder __init__.py files for all Python packages.
```

### Task 1.2: Backend Schemas - ALL Models (5 minutes)
**CRITICAL: This unblocks all parallel work**

- [x] Create `app/models/schemas.py` with ALL Pydantic models:
  - `ResearchProfile`
  - `NoveltyAssessment`
  - `GapMapEntry`
  - `PivotSuggestion`
  - `ResearchRecommendation`
  - `ChatMessage`
  - `Citation`
  - Supporting enums: `NoveltyVerdict`, `ImpactLevel`, `RecommendationType`

- [x] Create `app/models/gap_map_models.py` with SQLAlchemy models:
  - `GapMapEntry` table definition
  - Indexes on `source`, `category`, `scraped_at`

**Claude Instruction:**
```
Read research_pivot_advisor_system.plan.md lines 227-281.
Create app/models/schemas.py with ALL Pydantic models matching the plan exactly.
Create app/models/gap_map_models.py with the SQLAlchemy GapMapEntry model from lines 318-339.
Use Pydantic V2 syntax. Add detailed docstrings.
```

### Task 1.3: Backend Config & Dependencies (3 minutes)
- [x] Create `pyproject.toml` with all dependencies from TECH_STACK.md
- [x] Create `app/config.py` with Pydantic Settings:
  - Load from .env
  - `OPENAI_API_KEY`
  - `OPENALEX_EMAIL`
  - `OXYLABS_USERNAME`, `OXYLABS_PASSWORD`
  - `DATABASE_URL`
  - `REDIS_URL`
  - `SESSION_TTL_SECONDS`
- [x] Create `.env.example`
- [x] Create `docker-compose.yml` for PostgreSQL + Redis

**Claude Instruction:**
```
Create pyproject.toml using Poetry with dependencies from docs/TECH_STACK.md.
Create app/config.py using pydantic-settings to load environment variables.
Create .env.example with all required keys.
Create docker-compose.yml for PostgreSQL 15 and Redis 7.
```

---

## Phase 2: Parallel Backend Development (20 minutes)
**Launch 4 separate Claude agents in PARALLEL. Each agent is independent.**

### Agent 2A: Information Collection Service (20 minutes)
**Files to create:**
- `app/services/info_collector.py`
- `app/services/document_parser.py`
- `tests/test_info_collector.py`

**Tasks:**
- [x] Implement `InfoCollectionService.extract_from_chat(messages)` → `ResearchProfile`
- [x] Implement `InfoCollectionService.extract_from_files(files)` → `ResearchProfile`
- [x] Use OpenAI structured output with ResearchProfile schema
- [x] Implement `DocumentParser.parse_pdf(file)` → text
- [x] Implement `DocumentParser.parse_docx(file)` → text
- [x] Write unit tests with mocked OpenAI responses

**Claude Instruction for Agent 2A:**
```
You are Agent 2A: Information Collection Service.
Goal: Build the service that extracts research profiles from chat and files.

Read:
- research_pivot_advisor_system.plan.md lines 136-148 (Info Collection spec)
- app/models/schemas.py (ResearchProfile model)
- docs/TECH_STACK.md (OpenAI library usage)

Create:
1. app/services/document_parser.py:
   - parse_pdf(file) using pypdf
   - parse_docx(file) using python-docx
   - parse_txt(file)

2. app/services/info_collector.py:
   - InfoCollectionService class
   - async extract_from_chat(messages: list[ChatMessage]) -> ResearchProfile
   - async extract_from_files(files: list[UploadFile]) -> ResearchProfile
   - Use OpenAI GPT-4 with structured output (Pydantic mode)
   - Prompt: "Extract research question, skills, expertise, motivations from this input"

3. tests/test_info_collector.py:
   - Mock OpenAI API
   - Test with sample chat messages
   - Test with sample file contents

Privacy reminder: No user data in logs.
```

### Agent 2B: Novelty & Impact Analyzer (20 minutes)
**Files to create:**
- `app/services/novelty_analyzer.py`
- `app/services/openalex_client.py`
- `tests/test_novelty_analyzer.py`

**Tasks:**
- [x] Implement `OpenAlexClient.search_papers(query)` → list of papers with FWCI
- [x] Extract FWCI metrics: `fwci`, `citation_normalized_percentile`, `cited_by_percentile_year`
- [x] Implement `NoveltyAnalyzer.analyze(research_question)` → `NoveltyAssessment`
- [x] Calculate average FWCI, percentiles
- [x] Use LLM to interpret: SOLVED/MARGINAL/NOVEL/UNCERTAIN
- [x] Determine impact: HIGH/MEDIUM/LOW based on FWCI thresholds
- [x] Write unit tests with mocked OpenAlex responses

**Claude Instruction for Agent 2B:**
```
You are Agent 2B: Novelty & Impact Analyzer.
Goal: Build the service that analyzes research novelty and impact using OpenAlex.

Read:
- research_pivot_advisor_system.plan.md lines 149-167 (Novelty Analyzer spec)
- research_pivot_advisor_system.plan.md lines 458-510 (FWCI logic)
- app/models/schemas.py (NoveltyAssessment model)
- docs/TECH_STACK.md (pyalex library)

Create:
1. app/services/openalex_client.py:
   - OpenAlexClient class (async)
   - async search_papers(query: str, limit: int = 20) -> list[dict]
   - Extract: title, doi, fwci, citation_normalized_percentile, cited_by_percentile_year
   - Handle None values for FWCI gracefully

2. app/services/novelty_analyzer.py:
   - NoveltyAnalyzer class
   - async analyze(research_question: str) -> NoveltyAssessment
   - Steps:
     a. Query OpenAlex for related papers
     b. Calculate FWCI statistics (mean, percentiles)
     c. Use LLM to determine verdict (SOLVED/MARGINAL/NOVEL/UNCERTAIN)
     d. Determine impact_assessment based on FWCI:
        - HIGH: avg_fwci > 1.5
        - MEDIUM: avg_fwci 0.8-1.5
        - LOW: avg_fwci < 0.8
     e. Return NoveltyAssessment with evidence

3. tests/test_novelty_analyzer.py:
   - Mock OpenAlex API responses
   - Test FWCI calculations
   - Test verdict determination

Use polite pool: set email header in OpenAlex requests.
```

### Agent 2C: Gap Map Database & Scrapers (20 minutes)
**Files to create:**
- `app/services/gap_map_repository.py`
- `app/services/scrapers/base_scraper.py`
- `app/services/scrapers/convergent_scraper.py`
- `app/services/scrapers/homeworld_scraper.py`
- `app/services/scrapers/wikenigma_scraper.py`
- `app/services/scrapers/threeie_scraper.py`
- `app/services/scrapers/encyclopedia_scraper.py`
- `app/services/gap_map_scraper.py` (orchestrator)
- `app/jobs/gap_map_scraper_job.py`
- `tests/test_gap_map_repository.py`

**Tasks:**
- [x] Implement `GapMapRepository` for database operations (upsert, query)
- [x] Create `BaseScraper` abstract class
- [x] Implement 5 scrapers (can use simple HTML parsing, full Oxylabs optional)
- [x] Implement `GapMapScraperOrchestrator.scrape_all()`
- [x] Create background job with APScheduler
- [x] Write tests with mock HTTP responses

**Claude Instruction for Agent 2C:**
```
You are Agent 2C: Gap Map Database & Scrapers.
Goal: Build the database layer and web scrapers for gap map data.

Read:
- research_pivot_advisor_system.plan.md lines 168-193 (Gap Map spec)
- research_pivot_advisor_system.plan.md lines 305-339 (Database schema)
- app/models/gap_map_models.py (SQLAlchemy model)
- app/models/schemas.py (GapMapEntry Pydantic model)
- docs/TECH_STACK.md (SQLAlchemy async, httpx, BeautifulSoup)

Create:
1. app/services/gap_map_repository.py:
   - GapMapRepository class (uses async SQLAlchemy)
   - async upsert(entries: list[GapMapEntry]) - update existing, insert new
   - async get_all() -> list[GapMapEntry]
   - async get_by_category(category: str) -> list[GapMapEntry]
   - async get_by_source(source: str) -> list[GapMapEntry]

2. app/services/scrapers/base_scraper.py:
   - BaseScraper abstract class
   - async scrape() -> list[GapMapEntry]

3. app/services/scrapers/[source]_scraper.py (5 files):
   - Inherit from BaseScraper
   - Implement scraping logic for each source
   - Use httpx for requests
   - Use BeautifulSoup for parsing
   - For MVP: Can scrape 3-5 entries per source (don't need full scraping)
   - Normalize to GapMapEntry schema

4. app/services/gap_map_scraper.py:
   - GapMapScraperOrchestrator class
   - async scrape_all_sources() -> int (returns count scraped)
   - Calls all 5 scrapers
   - Uses GapMapRepository to upsert results

5. app/jobs/gap_map_scraper_job.py:
   - setup_scheduler() - configure APScheduler
   - Job runs daily at 2 AM
   - Calls GapMapScraperOrchestrator.scrape_all_sources()

6. tests/test_gap_map_repository.py:
   - Use test database
   - Test upsert logic (update vs insert)
   - Test query methods

For MVP: Scrapers can return hardcoded sample data to unblock other work.
Privacy: Only public gap map data, no user data.
```

### Agent 2D: Pivot Matcher & Report Generator (20 minutes)
**Files to create:**
- `app/services/pivot_matcher.py`
- `app/services/report_generator.py`
- `tests/test_pivot_matcher.py`

**Tasks:**
- [x] Implement `PivotMatcher.match(profile, novelty, gap_entries)` → list of `PivotSuggestion`
- [x] Use LLM to match skills/motivations to gap entries
- [x] Rank by relevance × impact potential
- [x] Implement `ReportGenerator.generate(profile, novelty, pivots)` → `ResearchRecommendation`
- [x] Create narrative report with LLM
- [x] Include FWCI analysis and impact reasoning
- [x] Write unit tests with mocked LLM responses

**Claude Instruction for Agent 2D:**
```
You are Agent 2D: Pivot Matcher & Report Generator.
Goal: Build services that match researchers to pivots and generate reports.

Read:
- research_pivot_advisor_system.plan.md lines 194-212 (Pivot Matcher spec)
- research_pivot_advisor_system.plan.md lines 213-225 (Report Generator spec)
- app/models/schemas.py (PivotSuggestion, ResearchRecommendation models)
- docs/TECH_STACK.md (OpenAI library)

Create:
1. app/services/pivot_matcher.py:
   - PivotMatcher class
   - async match_pivots(
       profile: ResearchProfile,
       novelty: NoveltyAssessment,
       gap_entries: list[GapMapEntry]
     ) -> list[PivotSuggestion]
   - Use LLM to:
     - Understand researcher's skills and motivations
     - Match to gap map entries
     - Assess impact potential of each gap
     - Rank by (relevance_score × impact_weight)
   - Return top 5 suggestions
   - Prioritize HIGH impact entries

2. app/services/report_generator.py:
   - ReportGenerator class
   - async generate_report(
       profile: ResearchProfile,
       novelty: NoveltyAssessment,
       pivot_suggestions: list[PivotSuggestion]
     ) -> ResearchRecommendation
   - Determine recommendation:
     - If novelty.verdict in [SOLVED, MARGINAL] OR novelty.impact_assessment == LOW: PIVOT
     - If novelty.verdict == NOVEL AND novelty.impact_assessment in [HIGH, MEDIUM]: CONTINUE
     - Otherwise: UNCERTAIN
   - Use LLM to generate narrative_report (markdown):
     - Executive summary
     - Novelty findings (include FWCI metrics)
     - Impact assessment
     - Recommendation with reasoning
     - Pivot suggestions (if applicable)
     - Citations

3. tests/test_pivot_matcher.py:
   - Mock OpenAI API
   - Test matching logic
   - Test ranking

Decision logic critical: See plan lines 499-502.
```

---

## Phase 3: Parallel Frontend Development (15 minutes)
**Launch 2 separate Claude agents in PARALLEL while backend is building.**

### Agent 3A: Chat Interface & File Upload (15 minutes)
**Files to create:**
- `src/components/chat-interface.tsx`
- `src/components/file-upload.tsx`
- `src/components/ui/` (Shadcn components via CLI)
- `src/lib/utils.ts`

**Tasks:**
- [x] Set up Vite + React + TypeScript project
- [x] Install Shadcn UI: `npx shadcn-ui@latest init`
- [x] Install components: Button, Card, Input, Textarea, Progress
- [x] Create ChatInterface component with message list and input
- [x] Create FileUpload component with drag-and-drop
- [x] Use React Hook Form for input handling
- [x] Set up basic routing

**Claude Instruction for Agent 3A:**
```
You are Agent 3A: Frontend Chat Interface.
Goal: Build the chat interface and file upload components.

Read:
- research_pivot_advisor_system.plan.md lines 104-123 (Frontend spec)
- docs/TECH_STACK.md (Frontend stack)

Create:
1. Initialize Vite + React + TypeScript project in research-advisor-frontend/
   - Run: npm create vite@latest research-advisor-frontend -- --template react-ts
   - Install dependencies from TECH_STACK.md

2. Set up Shadcn UI:
   - Run: npx shadcn-ui@latest init
   - Install components: button, card, input, textarea, progress, alert

3. src/components/chat-interface.tsx:
   - Display message list (user and assistant messages)
   - Message input textarea
   - Send button
   - Show typing indicator when processing
   - Use Shadcn Card and Input components

4. src/components/file-upload.tsx:
   - Use react-dropzone
   - Drag-and-drop area
   - File type validation (PDF, DOCX, TXT)
   - File list with remove option
   - Shadcn Button for upload

5. src/lib/utils.ts:
   - cn() function for Tailwind class merging

Use Tailwind for all styling. Follow Shadcn patterns.
```

### Agent 3B: Results View & API Client (15 minutes)
**Files to create:**
- `src/components/results-view.tsx`
- `src/api/client.ts`
- `src/hooks/useAnalysis.ts`
- `src/types/index.ts`

**Tasks:**
- [x] Create TypeScript types matching backend schemas
- [x] Create axios client with base URL configuration
- [x] Create TanStack Query hooks for API calls
- [x] Create ResultsView component to display recommendations
- [x] Show narrative report, pivot suggestions, citations
- [x] Handle loading and error states

**Claude Instruction for Agent 3B:**
```
You are Agent 3B: Frontend Results View & API Integration.
Goal: Build the results display and API integration layer.

Read:
- research_pivot_advisor_system.plan.md lines 118-123 (Results View spec)
- research_pivot_advisor_system.plan.md lines 283-303 (API endpoints)
- app/models/schemas.py (Backend schemas)
- docs/TECH_STACK.md (TanStack Query, axios)

Create:
1. src/types/index.ts:
   - TypeScript interfaces matching backend Pydantic models:
     - ResearchProfile
     - NoveltyAssessment
     - GapMapEntry
     - PivotSuggestion
     - ResearchRecommendation
     - ChatMessage

2. src/api/client.ts:
   - Axios instance with baseURL (http://localhost:8000/api/v1)
   - Request/response interceptors
   - API methods:
     - analyzeResearch(messages, files)
     - getAnalysis(sessionId)
     - sendChatMessage(sessionId, message)
     - deleteSession(sessionId)

3. src/hooks/useAnalysis.ts:
   - TanStack Query hooks:
     - useAnalyzeResearch() - useMutation
     - useGetAnalysis(sessionId) - useQuery with polling
     - useSendMessage() - useMutation
   - Handle loading, error states

4. src/components/results-view.tsx:
   - Display ResearchRecommendation
   - Show recommendation badge (CONTINUE/PIVOT/UNCERTAIN)
   - Render narrative_report (markdown)
   - Show NoveltyAssessment with FWCI metrics
   - List PivotSuggestions as cards
   - Display citations with links
   - Use Shadcn Alert, Card, Badge components

Use TanStack Query for all data fetching. Never use useEffect for API calls.
```

---

## Phase 4: Backend API Integration (15 minutes)
**Sequential work. All agents must be done first.**

⚠️ **INTEGRATION TESTING REQUIRED** ⚠️

### Task 4.1: FastAPI Endpoints (7 minutes)
- [x] Create `app/api/routes.py` with endpoints:
  - `POST /api/v1/analyze`
  - `GET /api/v1/analysis/{session_id}`
  - `POST /api/v1/chat`
  - `DELETE /api/v1/session/{session_id}`
- [x] Implement session management with Redis
- [x] Wire up all services
- [x] Add CORS middleware
- [x] Add error handling middleware

**Claude Instruction:**
```
Read research_pivot_advisor_system.plan.md lines 283-303 for API spec.
Create app/api/routes.py with all endpoints.
Use Redis for session storage (TTL: 1 hour).
Wire up services created by Agents 2A-2D.
Add CORS for http://localhost:5173 (Vite dev server).
Add global exception handler for user-friendly errors.
```

### Task 4.2: Database Migrations (3 minutes)
- [x] Initialize Alembic: `alembic init alembic`
- [x] Configure Alembic for async SQLAlchemy
- [x] Create initial migration for gap_map_entries table
- [x] Run migration: `alembic upgrade head`

**Claude Instruction:**
```
Initialize Alembic in research-advisor-backend/.
Configure alembic.ini with async DATABASE_URL.
Create migration for GapMapEntry model.
Generate: alembic revision --autogenerate -m "Initial migration"
```

### Task 4.3: Integration Tests (5 minutes) - **MANDATORY**
- [x] Create `tests/integration/test_api_endpoints.py`
- [x] Test all 4 endpoints:
  - POST /analyze: Send research question → verify response
  - GET /analysis/{session_id}: Verify session retrieval
  - POST /chat: Send message → verify chat response
  - DELETE /session: Verify session deletion
- [x] Test error cases (invalid session, missing fields)
- [x] Test Redis session TTL behavior
- [x] **RUN VALIDATION:** `./run_all_tests.sh`

**Claude Instruction:**
```
⚠️ CRITICAL: Integration tests MUST pass before marking Phase 4 complete.

Create tests/integration/test_api_endpoints.py:

1. Test POST /api/v1/analyze:
   - Mock: OpenAI (InfoCollector), OpenAlex (NoveltyAnalyzer), GapMapRepository
   - Send: {"messages": [...], "files": []}
   - Assert: Returns session_id, status, ResearchRecommendation
   - Verify: Redis session created

2. Test GET /api/v1/analysis/{session_id}:
   - Create session with test data
   - Fetch via endpoint
   - Assert: Returns correct ResearchRecommendation

3. Test POST /api/v1/chat:
   - Mock: OpenAI responses
   - Send: {"session_id": "...", "message": "..."}
   - Assert: Returns chat response

4. Test DELETE /api/v1/session/{session_id}:
   - Create session
   - Delete via endpoint
   - Assert: Session removed from Redis

5. Error cases:
   - Invalid session_id → 404
   - Missing required fields → 422

RUN BEFORE MARKING COMPLETE:
./run_all_tests.sh

SUCCESS CRITERIA:
✅ All integration tests pass
✅ No regressions in unit tests
✅ Coverage >80% for new code
```

---

## Phase 5: End-to-End Testing & Validation (10 minutes)
**Final testing and polish.**

⚠️ **COMPLETE TEST SUITE VALIDATION REQUIRED** ⚠️

### Task 5.1: End-to-End Manual Testing (5 minutes)
- [x] Start Docker Compose (PostgreSQL + Redis)
- [x] Start backend: `uvicorn app.main:app --reload`
- [x] Start frontend: `npm run dev`
- [x] Test full flow:
  - Input research question via chat
  - Upload sample PDF
  - Verify profile extraction
  - Check novelty analysis (use OpenAlex)
  - Verify gap map retrieval
  - Check pivot suggestions
  - View narrative report with FWCI metrics
- [x] Test error handling:
  - Invalid file upload
  - Network errors
  - Session expiration
- [x] Test privacy: Verify no user data in PostgreSQL

**Claude Instruction:**
```
Perform complete end-to-end manual testing:

1. Start services:
   docker-compose up -d
   cd research-advisor-backend && poetry run uvicorn app.main:app --reload
   cd research-advisor-frontend && npm run dev

2. Test happy path:
   - Open http://localhost:5173
   - Input: "Can quantum computing solve NP-complete problems efficiently?"
   - Upload: Sample research proposal PDF
   - Wait for analysis
   - Verify: ResearchProfile extracted correctly
   - Verify: NoveltyAssessment shows FWCI metrics
   - Verify: PivotSuggestions appear with relevance scores
   - Verify: Narrative report is coherent and includes citations

3. Test edge cases:
   - Try uploading invalid file type → Should show error
   - Try submitting empty message → Should be disabled
   - Refresh page → Session should persist (Redis)
   - Wait 1 hour → Session should expire

4. Privacy check:
   - Connect to PostgreSQL: docker exec -it postgres psql -U postgres -d research_advisor
   - Query: SELECT * FROM gap_map_entries; (should have data)
   - Verify: NO user research data in database (only in Redis)

Document any issues in docs/BUILD_STATUS.md.
Fix critical bugs ONLY (defer nice-to-haves).
```

### Task 5.2: Complete Test Suite Validation (3 minutes) - **MANDATORY**
- [x] **RUN:** `./run_all_tests.sh`
- [x] Verify backend test coverage >80%
- [x] Verify frontend test coverage >70%
- [x] Verify all integration tests pass
- [x] Check coverage reports: `open htmlcov/index.html`

**Claude Instruction:**
```
⚠️ CRITICAL: ALL tests MUST pass before project is considered complete.

Run complete validation:

1. Execute full test suite:
   ./run_all_tests.sh

2. Review results:
   - Backend unit tests: MUST ALL PASS
   - Backend integration tests: MUST ALL PASS
   - Frontend component tests: MUST ALL PASS
   - Coverage backend: MUST BE >80%
   - Coverage frontend: MUST BE >70%

3. If ANY test fails:
   - Document failure in docs/BUILD_STATUS.md
   - Fix the issue
   - Re-run ./run_all_tests.sh
   - DO NOT proceed until all tests pass

4. Review coverage reports:
   cd research-advisor-backend
   open htmlcov/index.html

   cd research-advisor-frontend
   # Check coverage report in terminal output

SUCCESS CRITERIA:
✅ ./run_all_tests.sh completes with 0 errors
✅ Backend coverage >80%
✅ Frontend coverage >70%
✅ Manual E2E test checklist complete
✅ No critical bugs
```

### Task 5.3: Documentation & Deploy Prep (2 minutes)
- [x] Update README.md with setup instructions
- [x] Verify .env.example has all keys
- [x] Test Docker Compose setup from scratch
- [x] Create quick start guide

**Claude Instruction:**
```
Create comprehensive README.md with:
- Project overview and key features
- Architecture diagram (Backend + Frontend + Redis + PostgreSQL)
- Setup instructions:
  1. Prerequisites (Python 3.11+, Node.js 18+, Docker)
  2. Install dependencies (Poetry, npm)
  3. Configure .env (copy from .env.example)
  4. Start services (docker-compose, uvicorn, vite)
- How to run tests (./run_all_tests.sh)
- API documentation (link to /docs when running)
- Privacy & data handling notes

Verify .env.example includes:
- OPENAI_API_KEY
- OPENALEX_API_KEY
- OPENALEX_EMAIL
- OXYLABS_USERNAME
- OXYLABS_PASSWORD
- DATABASE_URL
- REDIS_URL
- SESSION_TTL_SECONDS

Test fresh setup:
1. Clone to new directory
2. Follow README instructions
3. Verify application runs
```

---

## Parallelization Summary

### Concurrent Agent Groups
1. **Phase 1:** Sequential (10 min) - 1 agent
2. **Phase 2:** Parallel (20 min) - 4 agents (2A, 2B, 2C, 2D)
3. **Phase 3:** Parallel (15 min) - 2 agents (3A, 3B) - can overlap with Phase 2
4. **Phase 4:** Sequential (15 min) - 1 agent - **INCLUDES INTEGRATION TESTING**
5. **Phase 5:** Sequential (10 min) - 1 agent - **INCLUDES FULL VALIDATION**

**Total Wall Time:** ~45-50 minutes with perfect parallelization
**Total Effort:** ~95 minutes of work (compressed via parallelization)
**Testing Time:** ~15 minutes (included in totals above)

---

## Dependency Graph

```
Phase 1 (Foundation)
  ├─ Schemas [REQUIRED FOR ALL]
  ├─ Config [REQUIRED FOR ALL]
  └─ Project Structure [REQUIRED FOR ALL]
      ↓
Phase 2 & 3 (Parallel Backend + Frontend)
  ├─ Agent 2A: Info Collector (depends on: schemas)
  ├─ Agent 2B: Novelty Analyzer (depends on: schemas)
  ├─ Agent 2C: Gap Map System (depends on: schemas, DB models)
  ├─ Agent 2D: Pivot Matcher (depends on: schemas)
  ├─ Agent 3A: Chat UI (independent)
  └─ Agent 3B: Results UI (depends on: schemas for types)
      ↓
Phase 4 (Integration)
  └─ API Endpoints (depends on: ALL Phase 2 agents)
      ↓
Phase 5 (Testing)
  └─ E2E Tests (depends on: ALL previous phases)
```

---

## Critical Path

The **longest sequential path** determines minimum time:
1. Phase 1: Foundation (10 min) → REQUIRED
2. Phase 2: Longest agent task (20 min) → Agent 2C (scrapers)
3. Phase 4: API Integration + Integration Testing (15 min)
4. Phase 5: E2E Testing + Validation (10 min)

**Minimum Total Time:** 55 minutes (with perfect execution and testing)
**Note:** Testing is non-negotiable and adds ~15 minutes to critical path

---

## Risk Mitigation

### High-Risk Tasks (Likely to Exceed Time)
1. **Agent 2C (Scrapers):** Web scraping is unpredictable
   - **Mitigation:** Use hardcoded sample gap map data initially
2. **OpenAlex Integration:** API rate limits or errors
   - **Mitigation:** Mock responses for development
3. **Frontend-Backend Integration:** CORS, type mismatches
   - **Mitigation:** Generate TypeScript types from Pydantic models

### Fallback Strategy
If behind schedule:
- **Skip:** Full scraper implementation (use static JSON files)
- **Skip:** Advanced UI polish (focus on functionality)
- **Skip:** Comprehensive tests (write critical path tests only)
- **Keep:** Core flow (chat → analysis → recommendation)
