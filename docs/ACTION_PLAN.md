# Action Plan: Building Research Pivot Advisor System in 1 Hour

## Executive Summary

**Goal:** Build a full-stack research advisor application in 60 minutes using Claude Code with parallel agent execution.

**Strategy:** Break work into 5 phases with aggressive parallelization. Use 6 simultaneous Claude agents in Phase 2-3 to compress 80 minutes of work into 20 minutes.

**Expected Outcome:** Functional MVP with core flow working (input → analysis → recommendation).

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────┐
│                  User (Researcher)                  │
└─────────────────┬───────────────────────────────────┘
                  │
         ┌────────▼────────┐
         │  React Frontend │
         │  (Vite + TS)    │
         └────────┬────────┘
                  │ HTTP/REST
         ┌────────▼────────┐
         │ FastAPI Backend │
         │   (Python 3.11) │
         └─────┬─────┬─────┘
               │     │
       ┌───────┘     └───────┐
       │                     │
┌──────▼──────┐      ┌───────▼───────┐
│ PostgreSQL  │      │     Redis     │
│ (Gap Maps)  │      │  (Sessions)   │
└─────────────┘      └───────────────┘
       │
       │ Periodic Scraping
       │
┌──────▼───────────────────────────────┐
│  External Data Sources (Gap Maps)   │
│  - Convergent Research               │
│  - Homeworld Bio                     │
│  - Wikenigma                         │
│  - 3ie Impact                        │
│  - Encyclopedia UIA                  │
└──────────────────────────────────────┘

External APIs:
- OpenAI GPT-4 (LLM reasoning)
- OpenAlex (Research papers + FWCI metrics)
- Oxylabs (Web scraping proxy - optional)
```

---

## Key Design Decisions

### 1. Privacy-First Architecture
- **User data** → Redis only (1-hour TTL, no disk persistence)
- **Public data** → PostgreSQL (gap map entries)
- **Principle:** No user research ideas ever persist beyond session

### 2. Background Scraping (Not On-Demand)
- Gap maps scraped daily by background job
- Stored in database for fast retrieval
- Users query pre-scraped data (no live scraping delays)

### 3. Dual Analysis: Novelty + Impact
- **Novelty:** Is it already solved? (via OpenAlex)
- **Impact:** Does it matter? (via FWCI metrics)
- **Decision:** Pivot if low novelty OR low impact

### 4. Tech Stack Choices
| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Backend | FastAPI | Async, auto-docs, Pydantic |
| Frontend | Vite + React | Fast dev, modern |
| Database | PostgreSQL | Structured data, ACID |
| Cache | Redis | Ephemeral sessions, TTL |
| LLM | OpenAI GPT-4 | Structured outputs, reliable |
| Research | OpenAlex | Free, FWCI metrics |

---

## Implementation Phases

### Phase 1: Foundation (10 min) - Sequential
**1 Agent: Main Orchestrator**

**Goal:** Create schemas and config that unblock all parallel work.

**Deliverables:**
- ✅ Directory structure (backend + frontend)
- ✅ All Pydantic schemas (`ResearchProfile`, `NoveltyAssessment`, etc.)
- ✅ SQLAlchemy models for gap map entries
- ✅ `pyproject.toml` with dependencies
- ✅ `app/config.py` for environment variables
- ✅ `.env` file with API keys
- ✅ `docker-compose.yml` for PostgreSQL + Redis

**Blocker Risk:** Low (mostly file creation, no complex logic)

---

### Phase 2: Backend Services (20 min) - Parallel
**4 Agents: 2A, 2B, 2C, 2D**

#### Agent 2A: Information Collection (20 min)
**Goal:** Extract research profile from chat/files using LLM.

**Files:**
- `app/services/document_parser.py` - Parse PDF, DOCX, TXT
- `app/services/info_collector.py` - LLM extraction → `ResearchProfile`
- `tests/test_info_collector.py` - Unit tests with mocked OpenAI

**Dependencies:** Phase 1 schemas

#### Agent 2B: Novelty & Impact Analyzer (20 min)
**Goal:** Determine if research is novel and high-impact using OpenAlex + FWCI.

**Files:**
- `app/services/openalex_client.py` - OpenAlex API wrapper
- `app/services/novelty_analyzer.py` - Novelty + impact analysis
- `tests/test_novelty_analyzer.py` - Unit tests with mocked OpenAlex

**Key Logic:**
- Query OpenAlex for related papers
- Extract FWCI (Field Weighted Citation Impact) metrics
- Use LLM to interpret: SOLVED / MARGINAL / NOVEL
- Assess impact: HIGH / MEDIUM / LOW (based on FWCI thresholds)

**Dependencies:** Phase 1 schemas

#### Agent 2C: Gap Map Database & Scrapers (20 min)
**Goal:** Build database layer and scrapers for gap map sources.

**Files:**
- `app/services/gap_map_repository.py` - Database CRUD operations
- `app/services/scrapers/base_scraper.py` - Abstract base class
- `app/services/scrapers/[5 scrapers].py` - One per source
- `app/services/gap_map_scraper.py` - Orchestrator for all scrapers
- `app/jobs/gap_map_scraper_job.py` - Background job (APScheduler)
- `tests/test_gap_map_repository.py` - Database tests

**MVP Shortcut:** Use hardcoded sample data (3-5 entries per source) to save time.

**Dependencies:** Phase 1 schemas + DB models

#### Agent 2D: Pivot Matcher & Report Generator (20 min)
**Goal:** Match researcher to pivots and generate recommendation report.

**Files:**
- `app/services/pivot_matcher.py` - LLM-based matching + ranking
- `app/services/report_generator.py` - Narrative report generation
- `tests/test_pivot_matcher.py` - Unit tests with mocked LLM

**Key Logic:**
- Match researcher skills/motivations to gap map entries
- Rank by: relevance × impact potential
- Prioritize HIGH impact problems
- Generate narrative report with recommendations

**Dependencies:** Phase 1 schemas

---

### Phase 3: Frontend (15 min) - Parallel with Phase 2
**2 Agents: 3A, 3B**

#### Agent 3A: Chat Interface & File Upload (15 min)
**Goal:** Build input components for user interaction.

**Setup:**
- Initialize Vite + React + TypeScript project
- Install Shadcn UI and components (Button, Card, Input, etc.)

**Files:**
- `src/components/chat-interface.tsx` - Message list + input
- `src/components/file-upload.tsx` - Drag-and-drop upload
- `src/lib/utils.ts` - Tailwind class merging utility

**Dependencies:** None (independent)

#### Agent 3B: Results View & API Client (15 min)
**Goal:** Build output components and API integration layer.

**Files:**
- `src/types/index.ts` - TypeScript types (mirror backend schemas)
- `src/api/client.ts` - Axios client with endpoints
- `src/hooks/useAnalysis.ts` - TanStack Query hooks
- `src/components/results-view.tsx` - Display recommendations

**Dependencies:** Phase 1 schemas (for TypeScript types)

---

### Phase 4: Backend API Integration (10 min) - Sequential
**1 Agent: Main Orchestrator**

**Goal:** Wire up all services and create API endpoints.

**Tasks:**
- Create `app/api/routes.py` with endpoints:
  - `POST /api/v1/analyze` - Submit research for analysis
  - `GET /api/v1/analysis/{session_id}` - Get results
  - `POST /api/v1/chat` - Continue conversation
  - `DELETE /api/v1/session/{session_id}` - Delete session
- Create `app/main.py` - FastAPI app with CORS, error handling
- Wire up services from Phase 2 (Agents 2A-2D)
- Implement Redis session management
- Initialize Alembic and create database migration
- Run migration: `alembic upgrade head`

**Dependencies:** ALL Phase 2 agents must complete

---

### Phase 5: End-to-End Testing (5 min) - Sequential
**1 Agent: Main Orchestrator**

**Goal:** Verify core flow works end-to-end.

**Tasks:**
- Start backend: `uvicorn app.main:app --reload`
- Start frontend: `npm run dev`
- Manual testing:
  - Input research question via chat
  - Verify OpenAlex novelty analysis
  - Check pivot recommendations display
  - Verify FWCI metrics shown
- Document critical bugs in `BUILD_STATUS.md`
- Create README.md with setup instructions

**Success Criteria:** User can complete one full flow without errors.

---

## Parallelization Strategy

### Dependency Graph
```
Phase 1 (Foundation)
    ↓
    ├─────────┬─────────┬─────────┬─────────┬─────────┐
    ↓         ↓         ↓         ↓         ↓         ↓
  Agent 2A  Agent 2B  Agent 2C  Agent 2D  Agent 3A  Agent 3B
    ↓         ↓         ↓         ↓         ↓         ↓
    └─────────┴─────────┴─────────┴─────────┴─────────┘
                        ↓
                    Phase 4 (API Integration)
                        ↓
                    Phase 5 (Testing)
```

### Agent Independence
- **Phase 2 Agents (2A-2D):** Fully independent (no file conflicts)
- **Phase 3 Agents (3A-3B):** Fully independent
- **Phase 2 + 3 can overlap:** Frontend agents can start immediately

### Critical Path
Longest sequential path = minimum time:
1. Phase 1: 10 min (required)
2. Phase 2C: 20 min (longest agent task)
3. Phase 4: 10 min (integration)
4. Phase 5: 5 min (testing)

**Minimum Time:** 45 minutes with perfect execution

---

## Risk Mitigation

### High-Risk Areas
| Risk | Impact | Mitigation |
|------|--------|------------|
| Agent 2C slow (scraping) | High | Use hardcoded sample data |
| OpenAlex rate limits | Medium | Mock responses for dev |
| Frontend-backend type mismatch | Medium | Generate TS types from Pydantic |
| Docker setup issues | Low | Pre-test Docker before starting |
| OpenAI API errors | High | Check credits before starting |

### Fallback Strategy
If running out of time:
1. **Skip:** Full scraper implementation (use static JSON)
2. **Skip:** Comprehensive tests (critical path only)
3. **Skip:** UI polish (functional > pretty)
4. **Keep:** Core flow working end-to-end

---

## Required Resources

### Hardware/Software
- **Machine:** Modern laptop (8GB+ RAM)
- **Docker Desktop:** Running
- **Terminals:** 6-7 windows/tabs
- **Internet:** Stable (multiple API calls)

### API Keys & Services
| Service | Required? | Cost | Usage |
|---------|-----------|------|-------|
| OpenAI API | ✅ Yes | ~$2-5 | LLM operations |
| OpenAlex | ⚠️ Optional | Free | Better rate limits |
| Oxylabs | ❌ No (MVP) | Pay-as-you-go | Web scraping |

### Time Investment
| Activity | Time |
|----------|------|
| Pre-reading docs | 10 min |
| Environment setup | 5 min |
| Getting API keys | 5 min |
| **Build execution** | **60 min** |
| Post-build cleanup | 10 min |
| **Total** | **90 min** |

---

## Success Metrics

### Minimum Viable Product (MVP)
By minute 60, must have:
- ✅ Chat interface accepts research question
- ✅ Backend calls OpenAlex for novelty analysis
- ✅ Backend returns CONTINUE/PIVOT recommendation
- ✅ Frontend displays results with FWCI metrics
- ✅ End-to-end flow works (even with mocked data)

### Nice-to-Have (Stretch Goals)
- ✅ File upload working
- ✅ Full gap map scraping (not just sample data)
- ✅ Comprehensive error handling
- ✅ Test coverage >70%
- ✅ UI polish and animations

### Done = Deployable?
**No.** After 1 hour, you have:
- ✅ Proof of concept
- ✅ Core functionality
- ⚠️ Basic error handling
- ❌ Production-ready deployment
- ❌ Security hardening
- ❌ Performance optimization

**Next Steps for Production:**
1. Implement real web scraping (replace sample data)
2. Add comprehensive error handling and validation
3. Increase test coverage to 80%+
4. Add authentication and rate limiting
5. Set up monitoring and logging
6. Deploy with CI/CD pipeline

---

## File Inventory

### Documentation Files (Created)
- ✅ `.cursorrules` - Behavioral rules for Claude agents
- ✅ `docs/TECH_STACK.md` - Technology choices and rationale
- ✅ `docs/IMPLEMENTATION_PRIORITIES.md` - Task breakdown and dependencies
- ✅ `docs/PARALLELIZATION_GUIDE.md` - How to run multiple agents
- ✅ `docs/BUILD_STATUS.md` - Progress tracking (live document)
- ✅ `docs/QUICK_START.md` - Engineer execution guide
- ✅ `docs/ACTION_PLAN.md` - This file (high-level overview)
- ✅ `.env.example` - Environment variables template
- ✅ `docker-compose.yml` - PostgreSQL + Redis setup

### Original Planning Files
- ✅ `research_pivot_advisor_system.plan.md` - Complete system specification

---

## Operational Instructions

### For the Engineer

1. **Pre-Flight (Before Timer Starts):**
   - Read `docs/QUICK_START.md` (5 minutes)
   - Skim `docs/IMPLEMENTATION_PRIORITIES.md` (3 minutes)
   - Get OpenAI API key ($5+ credits)
   - Open 7 terminal windows
   - Start Docker Desktop

2. **Start Timer - Execute:**
   - Follow `docs/QUICK_START.md` step-by-step
   - Launch agents at specified times
   - Monitor `docs/BUILD_STATUS.md` for progress
   - Don't micromanage - trust the agents

3. **Post-Build:**
   - Test core flow manually
   - Document incomplete work in `BUILD_STATUS.md`
   - Create git commit with summary
   - Write handoff document (see QUICK_START.md)

### For Claude Agents

All agents should:
- Read assigned section in `docs/IMPLEMENTATION_PRIORITIES.md`
- Follow patterns in `.cursorrules`
- Update `docs/BUILD_STATUS.md` after each task
- Use technologies from `docs/TECH_STACK.md`
- When blocked, document and continue with mocks

---

## Contact & Support

**If you get stuck:**
1. Check `docs/QUICK_START.md` troubleshooting section
2. Review `.cursorrules` for guidance
3. Simplify the task (use mocks, hardcode data)
4. Document the blocker and move on

**After completion:**
- Share results: [Your contact info]
- Feedback on process: [GitHub issues / email]
- Questions: [Support channel]

---

## Appendix: Command Reference

### Docker Commands
```bash
# Start databases
docker-compose up -d

# Check status
docker ps

# View logs
docker-compose logs -f postgres
docker-compose logs -f redis

# Stop and remove
docker-compose down

# Nuclear option (reset everything)
docker-compose down -v
```

### Backend Commands
```bash
cd research-advisor-backend

# Install dependencies
poetry install

# Run migrations
poetry run alembic upgrade head

# Start server
poetry run uvicorn app.main:app --reload

# Run tests
poetry run pytest

# Lint
poetry run ruff check app/
```

### Frontend Commands
```bash
cd research-advisor-frontend

# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build

# Type check
npm run type-check
```

### Monitoring Commands
```bash
# Watch BUILD_STATUS.md
watch -n 5 cat docs/BUILD_STATUS.md

# Count completed tasks
grep -c "✅" docs/BUILD_STATUS.md

# Check running processes
ps aux | grep uvicorn
ps aux | grep npm
```

---

**Ready to build? Start with `docs/QUICK_START.md`!** 🚀
