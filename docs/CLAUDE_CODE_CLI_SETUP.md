# Claude Code CLI Setup - Multi-Agent Build Guide

## ✅ Claude Code CLI Installed!

```bash
$ claude --version
2.1.39 (Claude Code)
```

You're currently using Claude Code CLI in this session. Perfect for the multi-agent build strategy!

---

## 🚀 Environment Setup

### 1. Install Python 3.11+ (Required)

Your current Python is 3.9.6. We need 3.11+ for this project.

```bash
# Install Python 3.11 via Homebrew
brew install python@3.11

# Verify installation
python3.11 --version

# Make it accessible
echo 'export PATH="/opt/homebrew/opt/python@3.11/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### 2. Install Poetry (Required)

```bash
# Install Poetry using Python 3.11
curl -sSL https://install.python-poetry.org | python3.11 -

# Add to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Verify
poetry --version
```

### 3. Install Docker Desktop (Required)

```bash
# Install via Homebrew
brew install --cask docker

# Start Docker Desktop
open /Applications/Docker.app

# Wait for Docker to start, then verify
docker --version
docker ps
```

### 4. Start Database Services

```bash
cd /Users/amit/Coding-Projects/Project-Suggester

# Start PostgreSQL and Redis
docker-compose up -d

# Verify they're running
docker ps
```

**Or run the automated setup script:**
```bash
./setup.sh
```

---

## 🎯 Multi-Agent Strategy with Claude Code CLI

### Why Multiple Terminal Windows?

Claude Code CLI allows you to run **independent agents in separate terminal windows**, each with its own context and task. This enables true parallel execution.

**Benefits:**
- ✅ True parallelization (4-6 agents working simultaneously)
- ✅ Independent contexts (no interference)
- ✅ Easy monitoring (one agent per terminal)
- ✅ Better than Cursor Composer for complex builds

---

## 🖥️ Terminal Setup (7 Windows)

### Window Layout

```
┌─────────────────┬─────────────────┐
│   Terminal 1    │   Terminal 2    │
│   Main/Phase 1  │   Agent 2A      │
├─────────────────┼─────────────────┤
│   Terminal 3    │   Terminal 4    │
│   Agent 2B      │   Agent 2C      │
├─────────────────┼─────────────────┤
│   Terminal 5    │   Terminal 6    │
│   Agent 2D      │   Agent 3A      │
├─────────────────┼─────────────────┤
│   Terminal 7    │                 │
│   Agent 3B      │                 │
└─────────────────┴─────────────────┘
```

### Using iTerm2 (Recommended) or Terminal.app

**iTerm2 (Better for Multiple Windows):**
```bash
# Install iTerm2
brew install --cask iterm2

# Create window arrangement:
# Cmd+D: Split vertically
# Cmd+Shift+D: Split horizontally
# Cmd+T: New tab
```

**Terminal.app (Built-in):**
- Cmd+N: New window
- Cmd+T: New tab
- Arrange windows manually

---

## 📝 Build Execution Plan

### Phase 0: Pre-Flight (5 minutes)

**In any terminal:**
```bash
cd /Users/amit/Coding-Projects/Project-Suggester

# Run setup
./setup.sh

# Verify everything
python3.11 --version   # 3.11.x
poetry --version
docker ps              # postgres + redis
claude --version       # 2.1.39
```

### Phase 1: Foundation (10 minutes)

**Terminal 1 - Main Orchestrator:**
```bash
cd /Users/amit/Coding-Projects/Project-Suggester
claude
```

**Instruction for Terminal 1:**
```
You are starting Phase 1 of the Research Pivot Advisor System build.

ENVIRONMENT:
- Python: 3.11+ (use python3.11 command)
- Working directory: /Users/amit/Coding-Projects/Project-Suggester
- Using Claude Code CLI
- Add Poetry to PATH: export PATH="$HOME/.local/bin:$PATH"

START PHASE 1: Foundation

Read docs/IMPLEMENTATION_PRIORITIES.md Phase 1 section.

Tasks:
1. Create complete directory structure (backend and frontend)
2. Create app/models/schemas.py with ALL Pydantic models
   (from research_pivot_advisor_system.plan.md lines 227-281)
3. Create app/models/gap_map_models.py with SQLAlchemy models
   (from plan lines 318-339)
4. Create pyproject.toml using Poetry (python = "^3.11")
5. Create app/config.py with Pydantic settings for env vars
6. Verify docker-compose.yml is correct
7. Create tests/ directory with __init__.py
8. Create tests/conftest.py with test fixtures (already exists)
9. Create pytest.ini with test configuration (already exists)

VALIDATION:
After completing all tasks, run:
  ./validate_phase1.sh

This checks:
- All directories exist
- All Python files have valid syntax
- Poetry config is valid

IMPORTANT:
- Use python3.11 in all scripts and commands
- Use poetry for Python package management
- Update docs/BUILD_STATUS.md after completing each task

When ./validate_phase1.sh passes, tell me "PHASE 1 COMPLETE - VALIDATION PASSED" and summarize what was created.
```

**Wait for "PHASE 1 COMPLETE" before proceeding to Phase 2.**

---

### Phase 2 & 3: Parallel Backend + Frontend (20-30 minutes)

Launch all 6 agents **simultaneously** in separate terminals.

#### Terminal 2 - Agent 2A: Info Collection Service

```bash
cd /Users/amit/Coding-Projects/Project-Suggester
claude
```

**Instruction:**
```
You are Agent 2A: Information Collection Service.

⚠️ TESTING IS MANDATORY ⚠️

ENVIRONMENT:
- Python: 3.11+ (use python3.11 or /opt/homebrew/bin/python3.11)
- Working directory: /Users/amit/Coding-Projects/Project-Suggester/research-advisor-backend
- Testing: pytest with fixtures in tests/conftest.py
- Add Poetry to PATH: export PATH="$HOME/.local/bin:$PATH"

TESTING REQUIREMENTS:
1. Create tests BEFORE implementation (TDD approach)
2. Mock all external APIs (use fixtures from conftest.py)
3. Achieve >80% code coverage
4. Run ./validate_agent.sh 2A before marking COMPLETE

Read docs/TESTING_STRATEGY.md for detailed requirements.
Read docs/IMPLEMENTATION_PRIORITIES.md "Agent 2A" section.

TASKS:
1. Create tests/test_document_parser.py
   - Test PDF parsing (mock file I/O)
   - Test DOCX parsing (mock file I/O)
   - Test TXT parsing
   - Test error handling (empty files, invalid formats)

2. Create tests/test_info_collector.py
   - Test LLM extraction returns valid ResearchProfile
   - Mock OpenAI API (use mock_openai_response fixture)
   - Test with various input types
   - Test error handling

3. Create app/services/document_parser.py
   - Implement PDF, DOCX, TXT parsing
   - Use pypdf, python-docx libraries

4. Create app/services/info_collector.py
   - Implement LLM-based extraction
   - Use OpenAI structured output with ResearchProfile schema
   - Handle errors gracefully

5. RUN VALIDATION:
   cd /Users/amit/Coding-Projects/Project-Suggester
   ./validate_agent.sh 2A

6. Fix any test failures

7. Update docs/BUILD_STATUS.md with:
   - Timestamp
   - Files created
   - Test results (X/Y tests passing)

✅ Say "AGENT 2A COMPLETE - ALL TESTS PASSING (X/Y)" only when ./validate_agent.sh 2A succeeds.
❌ DO NOT mark COMPLETE if validation fails.
```

#### Terminal 3 - Agent 2B: Novelty Analyzer

```bash
cd /Users/amit/Coding-Projects/Project-Suggester
claude
```

**Instruction:**
```
You are Agent 2B: Novelty & Impact Analyzer.

⚠️ TESTING IS MANDATORY ⚠️

ENVIRONMENT:
- Python: 3.11+ (use python3.11 or /opt/homebrew/bin/python3.11)
- Working directory: /Users/amit/Coding-Projects/Project-Suggester/research-advisor-backend
- Testing: pytest with fixtures in tests/conftest.py
- Add Poetry to PATH: export PATH="$HOME/.local/bin:$PATH"

TESTING REQUIREMENTS:
1. Create tests BEFORE implementation (TDD approach)
2. Mock OpenAlex API (use mock_openalex_response fixture)
3. Achieve >80% code coverage
4. Run ./validate_agent.sh 2B before marking COMPLETE

Read docs/TESTING_STRATEGY.md for detailed requirements.
Read docs/IMPLEMENTATION_PRIORITIES.md "Agent 2B" section.

TASKS:
1. Create tests/test_openalex_client.py
   - Test OpenAlex API query
   - Test FWCI extraction (handle None values)
   - Mock OpenAlex responses
   - Test error handling (API failures)

2. Create tests/test_novelty_analyzer.py
   - Test novelty verdict logic (SOLVED/MARGINAL/NOVEL/UNCERTAIN)
   - Test impact assessment (HIGH/MEDIUM/LOW based on FWCI)
   - Test with various FWCI values
   - Test error handling

3. Create app/services/openalex_client.py
   - OpenAlex API wrapper
   - Extract: fwci, citation_normalized_percentile, cited_by_percentile_year
   - Use OPENALEX_API_KEY from .env (higher tier account)
   - Handle None values gracefully

4. Create app/services/novelty_analyzer.py
   - Implement novelty + impact analysis
   - Use LLM to interpret OpenAlex results
   - Calculate FWCI statistics
   - Return NoveltyAssessment with evidence

5. RUN VALIDATION:
   cd /Users/amit/Coding-Projects/Project-Suggester
   ./validate_agent.sh 2B

6. Fix any test failures

7. Update docs/BUILD_STATUS.md with:
   - Timestamp
   - Files created
   - Test results (X/Y tests passing)

✅ Say "AGENT 2B COMPLETE - ALL TESTS PASSING (X/Y)" only when ./validate_agent.sh 2B succeeds.
❌ DO NOT mark COMPLETE if validation fails.
```

#### Terminal 4 - Agent 2C: Gap Map System

```bash
cd /Users/amit/Coding-Projects/Project-Suggester
claude
```

**Instruction:**
```
You are Agent 2C: Gap Map Database & Scrapers.

⚠️ TESTING IS MANDATORY ⚠️

ENVIRONMENT:
- Python: 3.11+ (use python3.11 or /opt/homebrew/bin/python3.11)
- Working directory: /Users/amit/Coding-Projects/Project-Suggester/research-advisor-backend
- Testing: pytest with test database (see conftest.py)
- Add Poetry to PATH: export PATH="$HOME/.local/bin:$PATH"

TESTING REQUIREMENTS:
1. Create tests BEFORE implementation (TDD approach)
2. Use test database (test_db_session fixture)
3. Mock Oxylabs API or use sample data
4. Achieve >80% code coverage
5. Run ./validate_agent.sh 2C before marking COMPLETE

Read docs/TESTING_STRATEGY.md for detailed requirements.
Read docs/IMPLEMENTATION_PRIORITIES.md "Agent 2C" section.
Read docs/OXYLABS_INTEGRATION.md for Oxylabs usage (optional for MVP).

TASKS:
1. Create tests/test_gap_map_repository.py
   - Test database upsert (update existing, insert new)
   - Test query methods (get_all, get_by_category, get_by_source)
   - Use test_db_session fixture
   - Test with sample GapMapEntry objects

2. Create tests/test_scrapers.py
   - Test each scraper returns valid GapMapEntry objects
   - Test sample data has correct structure
   - Mock Oxylabs or use hardcoded data

3. Create app/services/gap_map_repository.py
   - GapMapRepository class (async SQLAlchemy)
   - upsert, get_all, get_by_category, get_by_source methods

4. Create app/services/scrapers/base_scraper.py
   - BaseScraper abstract class

5. Create 5 scrapers (use sample data for MVP):
   - convergent_scraper.py (3-5 hardcoded entries)
   - homeworld_scraper.py (3-5 hardcoded entries)
   - wikenigma_scraper.py (3-5 hardcoded entries)
   - threeie_scraper.py (3-5 hardcoded entries)
   - encyclopedia_scraper.py (3-5 hardcoded entries)

6. Create app/services/gap_map_scraper.py
   - GapMapScraperOrchestrator class

7. Create app/jobs/gap_map_scraper_job.py
   - APScheduler setup for background job

8. RUN VALIDATION:
   cd /Users/amit/Coding-Projects/Project-Suggester
   ./validate_agent.sh 2C

9. Fix any test failures

10. Update docs/BUILD_STATUS.md with:
    - Timestamp
    - Files created
    - Test results (X/Y tests passing)

FOR MVP: Use hardcoded sample data (3-5 entries per source).
Skip full Oxylabs web scraping for speed.

✅ Say "AGENT 2C COMPLETE - ALL TESTS PASSING (X/Y)" only when ./validate_agent.sh 2C succeeds.
❌ DO NOT mark COMPLETE if validation fails.
```

#### Terminal 5 - Agent 2D: Pivot Matcher & Report Generator

```bash
cd /Users/amit/Coding-Projects/Project-Suggester
claude
```

**Instruction:**
```
You are Agent 2D: Pivot Matcher & Report Generator.

⚠️ TESTING IS MANDATORY ⚠️

ENVIRONMENT:
- Python: 3.11+ (use python3.11 or /opt/homebrew/bin/python3.11)
- Working directory: /Users/amit/Coding-Projects/Project-Suggester/research-advisor-backend
- Testing: pytest with fixtures in tests/conftest.py
- Add Poetry to PATH: export PATH="$HOME/.local/bin:$PATH"

TESTING REQUIREMENTS:
1. Create tests BEFORE implementation (TDD approach)
2. Mock LLM API calls
3. Use sample fixtures (sample_research_profile, sample_gap_map_entries, sample_novelty_assessment)
4. Achieve >80% code coverage
5. Run ./validate_agent.sh 2D before marking COMPLETE

Read docs/TESTING_STRATEGY.md for detailed requirements.
Read docs/IMPLEMENTATION_PRIORITIES.md "Agent 2D" section.

TASKS:
1. Create tests/test_pivot_matcher.py
   - Test matching algorithm
   - Test ranking by relevance × impact
   - Mock LLM responses
   - Use sample_research_profile and sample_gap_map_entries fixtures
   - Test returns top N suggestions

2. Create tests/test_report_generator.py
   - Test report generation includes all sections
   - Test recommendation logic (CONTINUE/PIVOT/UNCERTAIN)
   - Test with various NoveltyAssessment values
   - Test citations are properly formatted
   - Mock LLM responses

3. Create app/services/pivot_matcher.py
   - PivotMatcher class
   - match_pivots method: profile + novelty + gap_entries → list[PivotSuggestion]
   - Use LLM to match skills/motivations to gaps
   - Rank by relevance × impact potential
   - Return top 5 suggestions

4. Create app/services/report_generator.py
   - ReportGenerator class
   - generate_report method: profile + novelty + pivots → ResearchRecommendation
   - Decision logic:
     * If novelty=SOLVED/MARGINAL OR impact=LOW → PIVOT
     * If novelty=NOVEL AND impact=HIGH/MEDIUM → CONTINUE
     * Otherwise → UNCERTAIN
   - Generate narrative report with LLM

5. RUN VALIDATION:
   cd /Users/amit/Coding-Projects/Project-Suggester
   ./validate_agent.sh 2D

6. Fix any test failures

7. Update docs/BUILD_STATUS.md with:
   - Timestamp
   - Files created
   - Test results (X/Y tests passing)

✅ Say "AGENT 2D COMPLETE - ALL TESTS PASSING (X/Y)" only when ./validate_agent.sh 2D succeeds.
❌ DO NOT mark COMPLETE if validation fails.
```

#### Terminal 6 - Agent 3A: Frontend Chat Interface

```bash
cd /Users/amit/Coding-Projects/Project-Suggester
claude
```

**Instruction:**
```
You are Agent 3A: Frontend Chat Interface.

⚠️ TESTING IS MANDATORY ⚠️

ENVIRONMENT:
- Node.js 18+, Vite, React, TypeScript
- Working directory: /Users/amit/Coding-Projects/Project-Suggester/research-advisor-frontend
- Testing: Vitest + React Testing Library

TESTING REQUIREMENTS:
1. Create tests for each component
2. Use Vitest and @testing-library/react
3. Achieve >70% code coverage
4. Run ./validate_agent.sh 3A before marking COMPLETE

Read docs/TESTING_STRATEGY.md for detailed requirements.
Read docs/IMPLEMENTATION_PRIORITIES.md "Agent 3A" section.

TASKS:
1. Initialize Vite + React + TypeScript project
   npm create vite@latest research-advisor-frontend -- --template react-ts
   cd research-advisor-frontend
   npm install

2. Install testing dependencies:
   npm install --save-dev vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom

3. Create vitest.config.ts (see docs/TESTING_STRATEGY.md)

4. Install Shadcn UI:
   npx shadcn-ui@latest init
   npx shadcn-ui@latest add button card input textarea progress alert

5. Install other dependencies:
   npm install react-dropzone tailwind-merge clsx

6. Create src/lib/utils.ts (cn function for Tailwind)

7. Create src/components/chat-interface.test.tsx
   - Test component renders
   - Test user can type message
   - Test send button works
   - Test loading state displays

8. Create src/components/chat-interface.tsx
   - Message list display
   - Message input textarea
   - Send button
   - Loading indicator

9. Create src/components/file-upload.test.tsx
   - Test file upload accepts valid files
   - Test file upload rejects invalid files
   - Test drag and drop works

10. Create src/components/file-upload.tsx
    - Use react-dropzone
    - Drag-and-drop area
    - File type validation (PDF, DOCX, TXT)
    - File list with remove option

11. RUN VALIDATION:
    cd /Users/amit/Coding-Projects/Project-Suggester
    ./validate_agent.sh 3A

12. Fix any test failures

13. Update docs/BUILD_STATUS.md with:
    - Timestamp
    - Files created
    - Test results (X/Y tests passing)

Use Tailwind for all styling. Follow Shadcn patterns.

✅ Say "AGENT 3A COMPLETE - ALL TESTS PASSING (X/Y)" only when ./validate_agent.sh 3A succeeds.
❌ DO NOT mark COMPLETE if validation fails.
```

#### Terminal 7 - Agent 3B: Frontend Results View

```bash
cd /Users/amit/Coding-Projects/Project-Suggester
claude
```

**Instruction:**
```
You are Agent 3B: Frontend Results View & API Client.

⚠️ TESTING IS MANDATORY ⚠️

ENVIRONMENT:
- Node.js 18+, React, TypeScript
- Working directory: /Users/amit/Coding-Projects/Project-Suggester/research-advisor-frontend
- Testing: Vitest + React Testing Library

TESTING REQUIREMENTS:
1. Create tests for components and API client
2. Mock axios calls
3. Achieve >70% code coverage
4. Run ./validate_agent.sh 3B before marking COMPLETE

Read docs/TESTING_STRATEGY.md for detailed requirements.
Read docs/IMPLEMENTATION_PRIORITIES.md "Agent 3B" section.

TASKS:
1. Install dependencies:
   npm install @tanstack/react-query axios
   npm install --save-dev vitest-mock-extended

2. Create src/types/index.ts
   - TypeScript interfaces matching backend Pydantic models
   - ResearchProfile, NoveltyAssessment, GapMapEntry, PivotSuggestion, ResearchRecommendation
   - Copy from research-advisor-backend/app/models/schemas.py

3. Create src/api/client.test.ts
   - Test API methods call correct endpoints
   - Mock axios responses
   - Test error handling

4. Create src/api/client.ts
   - Axios instance with baseURL (http://localhost:8000/api/v1)
   - analyzeResearch(messages, files)
   - getAnalysis(sessionId)
   - sendChatMessage(sessionId, message)
   - deleteSession(sessionId)

5. Create src/hooks/useAnalysis.ts
   - TanStack Query hooks:
     * useAnalyzeResearch() - useMutation
     * useGetAnalysis(sessionId) - useQuery
     * useSendMessage() - useMutation
   - Handle loading, error states

6. Create src/components/results-view.test.tsx
   - Test results display correctly
   - Test recommendation badge shows
   - Test pivot suggestions render
   - Mock data from fixtures

7. Create src/components/results-view.tsx
   - Display ResearchRecommendation
   - Show recommendation badge (CONTINUE/PIVOT/UNCERTAIN)
   - Render narrative_report (markdown)
   - Show NoveltyAssessment with FWCI metrics
   - List PivotSuggestions as cards
   - Display citations with links

8. RUN VALIDATION:
   cd /Users/amit/Coding-Projects/Project-Suggester
   ./validate_agent.sh 3B

9. Fix any test failures

10. Update docs/BUILD_STATUS.md with:
    - Timestamp
    - Files created
    - Test results (X/Y tests passing)

Use TanStack Query for ALL API calls (never useEffect for fetching).
Use Shadcn UI components (Alert, Card, Badge).

✅ Say "AGENT 3B COMPLETE - ALL TESTS PASSING (X/Y)" only when ./validate_agent.sh 3B succeeds.
❌ DO NOT mark COMPLETE if validation fails.
```

---

### Monitoring Progress

**In Terminal 1 or a spare terminal:**
```bash
# Watch BUILD_STATUS.md for updates
watch -n 5 cat docs/BUILD_STATUS.md

# Or manually check
cat docs/BUILD_STATUS.md

# Count completed tasks
grep "✅" docs/BUILD_STATUS.md | wc -l
```

---

### Phase 4: Integration (10 minutes)

**Back to Terminal 1 (after all agents report COMPLETE):**

```
All Phase 2 and 3 agents have completed. Now integrate everything.

⚠️ INTEGRATION TESTING REQUIRED ⚠️

ENVIRONMENT:
- Python: 3.11+ (use python3.11 or /opt/homebrew/bin/python3.11)
- Working directory: /Users/amit/Coding-Projects/Project-Suggester/research-advisor-backend
- Add Poetry to PATH: export PATH="$HOME/.local/bin:$PATH"

Read docs/IMPLEMENTATION_PRIORITIES.md Phase 4 section.

Tasks:
1. Create app/api/routes.py with all endpoints:
   - POST /api/v1/analyze
   - GET /api/v1/analysis/{session_id}
   - POST /api/v1/chat
   - DELETE /api/v1/session/{session_id}

2. Create app/main.py with FastAPI app:
   - FastAPI app initialization
   - CORS middleware (allow http://localhost:5173)
   - Lifespan context manager for Redis/DB connections
   - Global exception handler
   - Include routes from app/api/routes.py

3. Wire up all services from Agents 2A-2D:
   - Import and use InfoCollectionService
   - Import and use NoveltyAnalyzer
   - Import and use GapMapRepository
   - Import and use PivotMatcher
   - Import and use ReportGenerator

4. Implement Redis session management:
   - Use redis-py with async support
   - Store user data with TTL (SESSION_TTL_SECONDS from config)
   - Session ID generation (UUID)
   - Session retrieval and deletion

5. Create integration tests:
   - tests/integration/__init__.py
   - tests/integration/test_api_endpoints.py
     * Test POST /api/v1/analyze returns session_id
     * Test GET /api/v1/analysis/{session_id} returns results
     * Test session expiration (TTL)
   - tests/integration/test_full_flow.py
     * Test complete flow: submit → analyze → retrieve results

6. Initialize Alembic:
   alembic init alembic
   - Configure alembic.ini with DATABASE_URL
   - Update alembic/env.py for async engine
   - Import Base from app.models.gap_map_models

7. Create database migration:
   alembic revision --autogenerate -m "Initial migration: gap_map_entries table"

8. Run migration:
   alembic upgrade head

9. RUN VALIDATION:
   cd /Users/amit/Coding-Projects/Project-Suggester
   ./run_all_tests.sh

10. Verify all services integrate correctly:
    - Start backend: poetry run uvicorn app.main:app --reload
    - Test API endpoints with curl or HTTP client
    - Check logs for errors

11. Update docs/BUILD_STATUS.md with:
    - Timestamp
    - Files created
    - Integration test results
    - Any issues encountered

Use python3.11 for all commands.

✅ Say "PHASE 4 COMPLETE - ALL TESTS PASSING" only when ./run_all_tests.sh succeeds.
❌ DO NOT mark COMPLETE if integration tests fail.
```

---

### Phase 5: Testing (5-10 minutes)

**Terminal 1:**

```
Phase 4 is complete. Now test end-to-end.

⚠️ MANUAL TESTING REQUIRED ⚠️

ENVIRONMENT:
- Two terminals needed (backend + frontend)
- Browser for testing

Tasks:
1. Start backend (Terminal 1):
   cd research-advisor-backend
   export PATH="$HOME/.local/bin:$PATH"
   poetry install
   poetry run alembic upgrade head
   poetry run uvicorn app.main:app --reload

   Verify:
   - Server starts on http://localhost:8000
   - No errors in logs
   - API docs at http://localhost:8000/docs

2. Start frontend (Terminal 2):
   cd research-advisor-frontend
   npm install
   npm run dev

   Verify:
   - Frontend starts on http://localhost:5173
   - No compilation errors
   - Assets load correctly

3. Manual E2E Testing Checklist:
   Open browser to http://localhost:5173

   [ ] Chat interface renders
   [ ] User can type research question
   [ ] Send button works
   [ ] File upload accepts PDF/DOCX/TXT
   [ ] File upload rejects invalid files
   [ ] Loading indicator shows during analysis
   [ ] OpenAlex API is called (check backend logs)
   [ ] Novelty assessment displays
   [ ] FWCI metrics show correctly
   [ ] Impact assessment (HIGH/MEDIUM/LOW) displays
   [ ] Recommendation badge shows (CONTINUE/PIVOT/UNCERTAIN)
   [ ] Pivot suggestions display (if applicable)
   [ ] Citations render with links
   [ ] No console errors in browser
   [ ] No backend errors in logs

4. Test with sample research question:
   "Can quantum computing solve NP-complete problems efficiently?"

   Expected:
   - OpenAlex returns papers
   - FWCI metrics extracted
   - Novelty verdict: NOVEL or UNCERTAIN
   - Impact assessment based on FWCI
   - Recommendation generated
   - Results display properly

5. Run final test suite:
   cd /Users/amit/Coding-Projects/Project-Suggester
   ./run_all_tests.sh

   Verify:
   - All backend unit tests pass
   - All frontend tests pass
   - Integration tests pass
   - Coverage reports generated

6. Document results in docs/BUILD_STATUS.md:
   - Timestamp
   - Manual testing results
   - Test coverage metrics
   - Known issues or limitations
   - Next steps for production

7. Create comprehensive README.md:
   - Project overview
   - Setup instructions
   - How to run (backend, frontend, tests)
   - Environment variables
   - API documentation link
   - Known limitations

✅ Say "PHASE 5 COMPLETE - BUILD SUCCESSFUL" when:
   - All manual tests pass
   - ./run_all_tests.sh passes
   - README.md created
   - BUILD_STATUS.md updated

✅ Mark the entire build as COMPLETE!
```

---

## 🎛️ Managing Multiple Claude Sessions

### Starting All Agents Quickly

**Create a script to open all terminals (optional):**

```bash
# start_agents.sh
#!/bin/bash

osascript <<EOF
tell application "iTerm"
    # Main window (already open)

    # Agent 2A
    tell current window
        create tab with default profile
        tell current session
            write text "cd /Users/amit/Coding-Projects/Project-Suggester && claude"
        end tell
    end tell

    # Agent 2B
    tell current window
        create tab with default profile
        tell current session
            write text "cd /Users/amit/Coding-Projects/Project-Suggester && claude"
        end tell
    end tell

    # Agent 2C
    tell current window
        create tab with default profile
        tell current session
            write text "cd /Users/amit/Coding-Projects/Project-Suggester && claude"
        end tell
    end tell

    # Agent 2D
    tell current window
        create tab with default profile
        tell current session
            write text "cd /Users/amit/Coding-Projects/Project-Suggester && claude"
        end tell
    end tell

    # Agent 3A
    tell current window
        create tab with default profile
        tell current session
            write text "cd /Users/amit/Coding-Projects/Project-Suggester && claude"
        end tell
    end tell

    # Agent 3B
    tell current window
        create tab with default profile
        tell current session
            write text "cd /Users/amit/Coding-Projects/Project-Suggester && claude"
        end tell
    end tell
end tell
EOF
```

### Manual Approach (Simpler)

1. Open iTerm2 or Terminal
2. Create 7 tabs (Cmd+T)
3. In each tab: `cd /Users/amit/Coding-Projects/Project-Suggester && claude`
4. Paste agent instruction into each tab
5. Let them work in parallel

---

## 📊 Expected Timeline

| Phase | Time | Terminals | Activity |
|-------|------|-----------|----------|
| **Setup** | 5 min | 1 | Run ./setup.sh |
| **Phase 1** | 10 min | 1 | Foundation |
| **Phase 2 & 3** | 20 min | 6 parallel | Backend + Frontend |
| **Phase 4** | 10 min | 1 | Integration |
| **Phase 5** | 10 min | 1 | Testing |

**Total:** ~55 minutes (with perfect parallelization)

---

## 💡 Tips for Claude Code CLI

### Best Practices
1. **One task per agent** - Keep instructions focused
2. **Reference docs with @** - Use `@docs/filename.md`
3. **Monitor BUILD_STATUS.md** - Track progress across agents
4. **Use copy-paste** - Copy instructions from this doc
5. **Wait for "COMPLETE"** - Ensure each phase finishes

### Keyboard Shortcuts
- **Cmd+T**: New terminal tab
- **Cmd+W**: Close terminal tab
- **Cmd+1/2/3**: Switch between tabs
- **Ctrl+C**: Stop current command
- **Ctrl+D**: Exit Claude session

### If an Agent Gets Stuck
```bash
# Stop the agent
Ctrl+C

# Restart with simpler instructions
claude

# Use mocks or sample data to unblock
```

---

## ✅ Verification Checklist

Before starting build:
```bash
# Python 3.11+
python3.11 --version

# Poetry
poetry --version

# Docker
docker ps | grep postgres
docker ps | grep redis

# Claude Code
claude --version

# API Keys
cat .env | grep OPENAI_API_KEY
cat .env | grep ANTHROPIC_API_KEY
```

---

## 🚀 Quick Start Summary

```bash
# 1. Setup environment
./setup.sh

# 2. Open 7 terminal tabs
# In each tab:
cd /Users/amit/Coding-Projects/Project-Suggester
claude

# 3. Terminal 1: Phase 1
[Paste Phase 1 instruction]

# 4. Terminals 2-7: Phase 2 & 3 (after Phase 1 completes)
[Paste agent instructions]

# 5. Terminal 1: Phase 4 (after all agents complete)
[Paste Phase 4 instruction]

# 6. Terminal 1: Phase 5 (testing)
[Paste Phase 5 instruction]
```

**You're ready to build!** 🎯
