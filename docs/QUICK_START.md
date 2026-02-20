# Quick Start Guide - Build in 1 Hour

## For the Engineer: How to Actually Build This

You're about to use Claude Code to build an entire application in ~1 hour. This guide tells you exactly what to do.

---

## ⏱️ Time Budget: 60 Minutes

| Phase | Time | Agents | Activity |
|-------|------|--------|----------|
| Phase 1 | 10 min | 1 | Foundation (schemas, config) |
| Phase 2 & 3 | 20 min | 6 | Parallel backend + frontend |
| Phase 4 | 10 min | 1 | API integration |
| Phase 5 | 5 min | 1 | Testing |
| Buffer | 15 min | 1 | Fixes, docs |

---

## 🚀 Pre-Flight Checklist (Before Starting Timer)

### 1. Environment Setup
```bash
# Install Claude Code (if not already installed)
# Verify installation
claude --version

# Install Docker Desktop
# Verify Docker is running
docker --version
docker ps

# Install Node.js 18+ and npm
node --version  # Should be 18+
npm --version

# Install Python 3.11+
python --version  # Should be 3.11+

# Install Poetry (Python package manager)
curl -sSL https://install.python-poetry.org | python3 -
poetry --version
```

### 2. Get API Keys

**Required:**
- **OpenAI API Key**: Get from https://platform.openai.com/api-keys
  - Need credits ($5+ recommended)
  - Test it works: `curl https://api.openai.com/v1/models -H "Authorization: Bearer YOUR_KEY"`

**Optional (but recommended):**
- **OpenAlex Email**: Just your email, no signup needed
- **Oxylabs** (skip for MVP): Can use sample data instead

### 3. Prepare Your Workspace
```bash
# Navigate to project directory
cd /Users/amit/Coding-Projects/Project-Suggester

# Verify all guide files exist
ls -la docs/
# Should see:
# - IMPLEMENTATION_PRIORITIES.md
# - PARALLELIZATION_GUIDE.md
# - BUILD_STATUS.md
# - TECH_STACK.md
# - QUICK_START.md (this file)

# Verify .cursorrules exists
ls -la .cursorrules

# Verify .env.example exists
ls -la .env.example

# Open 6-7 terminal windows/tabs (or use tmux)
```

### 4. Mental Preparation
- **Read** `docs/IMPLEMENTATION_PRIORITIES.md` (5 minutes)
- **Skim** `docs/PARALLELIZATION_GUIDE.md` (3 minutes)
- **Understand** the parallelization strategy
- **Trust** Claude - don't micromanage every line
- **Focus** on completion, not perfection

---

## 🎬 Execution Plan

### ⏰ Minute 0: START TIMER

**Open 7 terminal windows in this project directory.**

---

### ⏰ Minutes 0-10: Phase 1 (Foundation)

**Terminal 1 (Main):**

```bash
# Start Claude Code
claude

# Give Claude this instruction:
```

**Instruction to Claude:**
```
You are building the Research Pivot Advisor System. This is Phase 1: Foundation.

START TIME: [Current time - write it down]

Tasks:
1. Read docs/IMPLEMENTATION_PRIORITIES.md Phase 1 section
2. Create complete directory structure for backend and frontend
3. Create app/models/schemas.py with ALL Pydantic models (from plan lines 227-281)
4. Create app/models/gap_map_models.py with SQLAlchemy model (from plan lines 318-339)
5. Create pyproject.toml with dependencies from docs/TECH_STACK.md
6. Create app/config.py with Pydantic settings
7. Create .env file from .env.example (I'll fill in API keys)
8. Create docker-compose.yml

After each task, update docs/BUILD_STATUS.md with timestamp.
When Phase 1 is complete, tell me "PHASE 1 COMPLETE" and stop.

Work quickly. You have 10 minutes for this phase.
```

**Your Actions:**
- Let Claude work
- When it asks for API keys, fill in `.env` file manually:
  ```bash
  cp .env.example .env
  nano .env  # Add your OPENAI_API_KEY
  ```
- Start Docker:
  ```bash
  docker-compose up -d
  ```
- When Claude says "PHASE 1 COMPLETE", proceed to Phase 2

---

### ⏰ Minutes 10-30: Phase 2 & 3 (Parallel Development)

**Now launch 6 agents in parallel across terminals 2-7.**

#### Terminal 2: Agent 2A (Info Collector)
```bash
claude
```
**Instruction:**
```
You are Agent 2A: Information Collection Service.

Read docs/IMPLEMENTATION_PRIORITIES.md and find the "Claude Instruction for Agent 2A" section.
Execute all tasks for Agent 2A exactly as specified.

Files to create:
- app/services/document_parser.py
- app/services/info_collector.py
- tests/test_info_collector.py

Use OpenAI structured output with ResearchProfile schema.
When done, update docs/BUILD_STATUS.md and say "AGENT 2A COMPLETE".
```

#### Terminal 3: Agent 2B (Novelty Analyzer)
```bash
claude
```
**Instruction:**
```
You are Agent 2B: Novelty & Impact Analyzer.

Read docs/IMPLEMENTATION_PRIORITIES.md and find the "Claude Instruction for Agent 2B" section.
Execute all tasks for Agent 2B exactly as specified.

Files to create:
- app/services/openalex_client.py
- app/services/novelty_analyzer.py
- tests/test_novelty_analyzer.py

Extract FWCI metrics from OpenAlex. Use LLM to interpret results.
When done, update docs/BUILD_STATUS.md and say "AGENT 2B COMPLETE".
```

#### Terminal 4: Agent 2C (Gap Map System)
```bash
claude
```
**Instruction:**
```
You are Agent 2C: Gap Map Database & Scrapers.

Read docs/IMPLEMENTATION_PRIORITIES.md and find the "Claude Instruction for Agent 2C" section.
Execute all tasks for Agent 2C exactly as specified.

Files to create:
- app/services/gap_map_repository.py
- app/services/scrapers/base_scraper.py
- app/services/scrapers/[5 scraper files]
- app/services/gap_map_scraper.py
- app/jobs/gap_map_scraper_job.py
- tests/test_gap_map_repository.py

IMPORTANT: For MVP speed, use hardcoded sample gap map data in scrapers (3-5 entries per source).
Don't spend time on full web scraping implementation.

When done, update docs/BUILD_STATUS.md and say "AGENT 2C COMPLETE".
```

#### Terminal 5: Agent 2D (Pivot Matcher)
```bash
claude
```
**Instruction:**
```
You are Agent 2D: Pivot Matcher & Report Generator.

Read docs/IMPLEMENTATION_PRIORITIES.md and find the "Claude Instruction for Agent 2D" section.
Execute all tasks for Agent 2D exactly as specified.

Files to create:
- app/services/pivot_matcher.py
- app/services/report_generator.py
- tests/test_pivot_matcher.py

Use LLM to match researchers to pivots. Generate narrative reports.
When done, update docs/BUILD_STATUS.md and say "AGENT 2D COMPLETE".
```

#### Terminal 6: Agent 3A (Chat Interface)
```bash
cd research-advisor-frontend
claude
```
**Instruction:**
```
You are Agent 3A: Frontend Chat Interface.

Read docs/IMPLEMENTATION_PRIORITIES.md and find the "Claude Instruction for Agent 3A" section.
Execute all tasks for Agent 3A exactly as specified.

Tasks:
1. Initialize Vite + React + TypeScript project
2. Install Shadcn UI and required components
3. Create chat interface component
4. Create file upload component

When done, update docs/BUILD_STATUS.md and say "AGENT 3A COMPLETE".
```

#### Terminal 7: Agent 3B (Results View)
```bash
cd research-advisor-frontend
claude
```
**Instruction:**
```
You are Agent 3B: Frontend Results View & API Client.

Read docs/IMPLEMENTATION_PRIORITIES.md and find the "Claude Instruction for Agent 3B" section.
Execute all tasks for Agent 3B exactly as specified.

Tasks:
1. Create TypeScript types from backend schemas
2. Create axios API client
3. Create TanStack Query hooks
4. Create results view component

When done, update docs/BUILD_STATUS.md and say "AGENT 3B COMPLETE".
```

**Your Actions During Phase 2 & 3:**
- Monitor each terminal occasionally
- Check `docs/BUILD_STATUS.md` for progress:
  ```bash
  # In Terminal 1
  watch -n 10 cat docs/BUILD_STATUS.md
  ```
- If an agent gets stuck (>5 min no progress), check its terminal
- **Don't intervene unless blocked** - trust the agents

---

### ⏰ Minutes 30-40: Phase 4 (API Integration)

**Back to Terminal 1 (Main):**

```bash
# Ensure all Phase 2 & 3 agents reported "COMPLETE"
# Check BUILD_STATUS.md
cat docs/BUILD_STATUS.md
```

**Instruction to Claude:**
```
All Phase 2 and 3 agents have completed. Now run Phase 4: Backend API Integration.

Read docs/IMPLEMENTATION_PRIORITIES.md Phase 4 section.

Tasks:
1. Create app/api/routes.py with all endpoints:
   - POST /api/v1/analyze
   - GET /api/v1/analysis/{session_id}
   - POST /api/v1/chat
   - DELETE /api/v1/session/{session_id}
2. Create app/main.py with FastAPI app, CORS, error handling
3. Wire up all services from Phase 2 (Agents 2A-2D)
4. Implement Redis session management
5. Initialize Alembic and create migration for gap_map_entries
6. Run migration: alembic upgrade head

When done, update docs/BUILD_STATUS.md and say "PHASE 4 COMPLETE".
```

**Your Actions:**
- Verify backend starts:
  ```bash
  cd research-advisor-backend
  poetry install
  poetry run uvicorn app.main:app --reload
  ```
- Check http://localhost:8000/docs (FastAPI docs)
- If errors, work with Claude to fix quickly

---

### ⏰ Minutes 40-45: Phase 5 (Testing)

**Terminal 1 (Main):**

**Instruction to Claude:**
```
Phase 4 is complete. Now run Phase 5: End-to-End Integration Testing.

Read docs/IMPLEMENTATION_PRIORITIES.md Phase 5 section.

Tasks:
1. Verify backend is running: uvicorn app.main:app --reload
2. Start frontend in separate terminal: npm run dev
3. Test the complete user flow:
   a. Open browser to http://localhost:5173
   b. Input a research question: "Can we use quantum computing to solve NP-complete problems efficiently?"
   c. Verify it calls OpenAlex
   d. Verify it shows novelty assessment
   e. Verify it shows recommendations
4. Document any critical bugs in docs/BUILD_STATUS.md
5. Create README.md with setup instructions

When done, say "PHASE 5 COMPLETE" and mark build as done.
```

**Your Actions:**
- Open browser to http://localhost:5173
- Test the flow manually
- Note any issues
- Celebrate if it works! 🎉

---

### ⏰ Minutes 45-60: Buffer (Fixes & Polish)

**Use remaining time for:**
- **Critical bugs only** - fix anything that breaks the core flow
- **Documentation** - ensure README.md is complete
- **Deployment prep** - verify Docker Compose setup works
- **Cleanup** - remove debug code, fix lint errors

**Don't waste time on:**
- UI polish (colors, fonts, etc.)
- Comprehensive test coverage
- Performance optimization
- Advanced features

---

## 🎯 Success Criteria

By minute 60, you should have:
- ✅ User can input research question via chat
- ✅ System calls OpenAlex and analyzes novelty
- ✅ System displays CONTINUE/PIVOT recommendation
- ✅ Frontend and backend communicate correctly
- ✅ Core flow works end-to-end

**Anything beyond this is a bonus.**

---

## 🚨 Troubleshooting

### Issue: Claude is stuck or slow
**Solution:**
- Cancel current task (Ctrl+C)
- Simplify instructions: "Just create the file with basic implementation"
- Use mocks instead of real API calls

### Issue: File conflicts between agents
**Solution:**
- Check which agent wrote first
- Have second agent read the file and merge changes
- In Terminal 1: `git diff` to see conflicts

### Issue: OpenAI API errors (rate limits, auth)
**Solution:**
- Verify API key: `echo $OPENAI_API_KEY` or check `.env`
- Check credits: https://platform.openai.com/account/billing
- Use mocks: Set `MOCK_OPENAI=true` in `.env`

### Issue: OpenAlex not returning results
**Solution:**
- Check network: `curl https://api.openalex.org/works?search=quantum`
- Verify email header is set
- Use sample data: Create mock responses

### Issue: Frontend won't start
**Solution:**
- Check Node version: `node --version` (need 18+)
- Delete `node_modules`: `rm -rf node_modules && npm install`
- Check port 5173 isn't in use: `lsof -i :5173`

### Issue: Backend won't start
**Solution:**
- Check Python version: `python --version` (need 3.11+)
- Check .env file exists and has OPENAI_API_KEY
- Check PostgreSQL is running: `docker ps`
- Check dependencies: `poetry install`

### Issue: Database migration errors
**Solution:**
- Check DATABASE_URL in .env
- Reset database: `docker-compose down -v && docker-compose up -d`
- Recreate migration: `alembic revision --autogenerate`

### Issue: Running out of time
**Solution:**
- **Focus on core flow only**
- Skip tests, skip polish, skip error handling
- Use hardcoded data everywhere
- Document incomplete work in BUILD_STATUS.md

---

## 📋 Post-Build Checklist

After 1 hour (or when "done"):

### 1. Verify Core Functionality
```bash
# Backend health check
curl http://localhost:8000/health

# Frontend loads
open http://localhost:5173

# Test one complete flow manually
```

### 2. Documentation
- [ ] README.md exists with setup instructions
- [ ] .env.example is complete
- [ ] BUILD_STATUS.md shows all phases complete (or blockers documented)

### 3. Code Quality (Quick Pass)
```bash
# Backend lint check
cd research-advisor-backend
poetry run ruff check app/

# Frontend type check
cd research-advisor-frontend
npm run type-check
```

### 4. Git Commit
```bash
# Create initial commit
git init
git add .
git commit -m "Initial build: Research Pivot Advisor System

Built in 1 hour using Claude Code with parallel agents.

Core features working:
- Chat interface for research question input
- OpenAlex integration for novelty analysis
- Pivot recommendation engine
- Frontend-backend integration

Known limitations:
- Basic error handling
- Limited test coverage
- Scrapers use sample data
- UI needs polish

See docs/BUILD_STATUS.md for details."
```

### 5. Handoff Documentation
Create a quick handoff document:

```markdown
# Build Handoff

## What Works
- [x] Core user flow: input → analysis → recommendation
- [x] OpenAlex novelty checking with FWCI metrics
- [x] Pivot suggestion matching
- [x] Frontend-backend API integration

## What's Incomplete
- [ ] Full web scraping (using sample data)
- [ ] Comprehensive error handling
- [ ] Test coverage (basic tests only)
- [ ] UI polish and responsive design
- [ ] Production deployment config

## Next Steps (Priority Order)
1. Implement real web scraping for gap maps
2. Add comprehensive error handling
3. Increase test coverage to 80%+
4. Polish UI/UX
5. Set up CI/CD pipeline
6. Deploy to staging environment

## Technical Debt
- Hardcoded values in scrapers (replace with real scraping)
- Some error cases return generic messages
- Redis session cleanup job not implemented
- No rate limiting on API endpoints

## How to Run
See README.md for setup instructions.

## Contact
[Your name/email]
Built: [Date]
```

---

## 🎓 Lessons Learned (For Next Time)

**What Worked Well:**
- Parallel agent execution (saved 40+ minutes)
- Detailed .cursorrules guidance
- Mock data to unblock dependencies
- Phase-based approach with clear handoffs

**What to Improve:**
- Start Docker earlier (before Phase 1)
- Pre-generate Pydantic schemas as templates
- Use more mocks in tests (avoid real API calls)
- Simplify scraper implementation further

**Time Sinks to Avoid:**
- Perfect error messages
- Comprehensive test coverage
- UI polish and animations
- Over-engineering abstractions

---

## 🔗 Reference Links

- **Architecture Plan:** `research_pivot_advisor_system.plan.md`
- **Implementation Tasks:** `docs/IMPLEMENTATION_PRIORITIES.md`
- **Parallelization Strategy:** `docs/PARALLELIZATION_GUIDE.md`
- **Technology Stack:** `docs/TECH_STACK.md`
- **Build Status:** `docs/BUILD_STATUS.md`
- **Claude Rules:** `.cursorrules`

---

## 💡 Pro Tips

1. **Trust the Agents:** Don't micromanage every line of code. Review in Phase 5.
2. **Mock Everything:** Real API calls slow you down. Mock until integration testing.
3. **Document Blockers:** If stuck, write it down and move on. Fix in buffer time.
4. **Parallelize Aggressively:** 6 agents is optimal. More = overhead, fewer = slower.
5. **Keep Core Simple:** Get one flow working perfectly before adding features.
6. **Use Timestamps:** Track actual time spent per phase. Learn for next build.
7. **Celebrate Small Wins:** Each agent completion is progress!

---

## 🏁 Ready?

1. ✅ API keys ready
2. ✅ Docker running
3. ✅ 7 terminals open
4. ✅ Documentation read
5. ✅ Timer ready

**START TIMER AND GO TO PHASE 1!**

**Good luck! 🚀**
