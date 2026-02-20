# Parallelization Guide - Using Multiple Claude Agents

## Overview

To build this system in 1 hour, you **must** run multiple Claude Code agents in parallel. This guide explains how.

---

## Prerequisites

1. **Claude Code installed** (you're using it now)
2. **Cursor IDE or VS Code** with Claude extension
3. **Multiple terminal windows** or terminal multiplexer (tmux/screen)
4. **Good internet connection** (multiple API calls simultaneously)

---

## Method 1: Multiple Terminal Windows (Recommended)

### Setup
1. Open **5-6 terminal windows** (or tabs)
2. Navigate each to the project directory
3. Launch Claude Code in each terminal

### Execution Pattern

#### Window 1: Main Orchestrator
```bash
# Terminal 1: Main Claude instance
cd /Users/amit/Coding-Projects/Project-Suggester
# This is your current window - use for Phase 1 and coordination
```

**Role:** Runs Phase 1 (Foundation), then coordinates other agents

#### Windows 2-5: Parallel Backend Agents (Phase 2)
```bash
# Terminal 2: Agent 2A
cd /Users/amit/Coding-Projects/Project-Suggester
# Start Claude Code and give it Agent 2A instructions

# Terminal 3: Agent 2B
cd /Users/amit/Coding-Projects/Project-Suggester
# Start Claude Code and give it Agent 2B instructions

# Terminal 4: Agent 2C
cd /Users/amit/Coding-Projects/Project-Suggester
# Start Claude Code and give it Agent 2C instructions

# Terminal 5: Agent 2D
cd /Users/amit/Coding-Projects/Project-Suggester
# Start Claude Code and give it Agent 2D instructions
```

#### Windows 6-7: Parallel Frontend Agents (Phase 3)
```bash
# Terminal 6: Agent 3A
cd /Users/amit/Coding-Projects/Project-Suggester
# Start Claude Code and give it Agent 3A instructions

# Terminal 7: Agent 3B
cd /Users/amit/Coding-Projects/Project-Suggester
# Start Claude Code and give it Agent 3B instructions
```

---

## Method 2: Claude Code Task Tool (Alternative)

Use the Task tool to spawn background agents:

```bash
# In your main Claude instance, use the Task tool
```

Then invoke agents like this:

**For Agent 2A:**
```
Use the Task tool with:
- subagent_type: "general-purpose"
- prompt: "[Agent 2A instructions from IMPLEMENTATION_PRIORITIES.md]"
- run_in_background: true
```

**Advantages:**
- Simpler to manage (all in one terminal)
- Claude manages agent lifecycle

**Disadvantages:**
- Less visibility into each agent's progress
- Harder to debug individual agents

---

## Workflow: Step-by-Step

### Step 0: Preparation (Before Starting Timer)
1. Read this entire guide
2. Read `docs/IMPLEMENTATION_PRIORITIES.md`
3. Have all terminal windows open and ready
4. Ensure Docker is running (for PostgreSQL + Redis)
5. Have `.cursorrules` and documentation files ready

### Step 1: Phase 1 - Foundation (10 minutes)
**Use Window 1 (Main Orchestrator)**

```
Instruction to Claude:

You are starting Phase 1 of the Research Pivot Advisor System build.

Read docs/IMPLEMENTATION_PRIORITIES.md and complete Phase 1 tasks:
1. Create project directory structure
2. Create all Pydantic schemas in app/models/schemas.py
3. Create SQLAlchemy models in app/models/gap_map_models.py
4. Create pyproject.toml with dependencies
5. Create app/config.py with environment variable loading
6. Create .env.example
7. Create docker-compose.yml

Update docs/BUILD_STATUS.md after each task.
Mark Phase 1 as complete when done.
Tell me when you're finished so I can start Phase 2.
```

**Wait for completion before proceeding.**

### Step 2: Phase 2 & 3 - Parallel Development (20 minutes)
**Launch 6 agents simultaneously**

#### Window 1 (Main): Start Docker & Monitor
```bash
# Start databases
docker-compose up -d

# Monitor other agents' progress
# You can use Window 1 to check BUILD_STATUS.md periodically
```

#### Window 2: Launch Agent 2A
```
Instruction to Claude:

You are Agent 2A: Information Collection Service.

Read:
- docs/IMPLEMENTATION_PRIORITIES.md (Agent 2A section)
- The specific "Claude Instruction for Agent 2A"

Execute all tasks for Agent 2A:
- Create app/services/document_parser.py
- Create app/services/info_collector.py
- Create tests/test_info_collector.py

When done:
- Update docs/BUILD_STATUS.md (mark Agent 2A complete)
- Tell me you're finished
```

#### Window 3: Launch Agent 2B
```
Instruction to Claude:

You are Agent 2B: Novelty & Impact Analyzer.

Read:
- docs/IMPLEMENTATION_PRIORITIES.md (Agent 2B section)
- The specific "Claude Instruction for Agent 2B"

Execute all tasks for Agent 2B:
- Create app/services/openalex_client.py
- Create app/services/novelty_analyzer.py
- Create tests/test_novelty_analyzer.py

When done:
- Update docs/BUILD_STATUS.md (mark Agent 2B complete)
- Tell me you're finished
```

#### Window 4: Launch Agent 2C
```
Instruction to Claude:

You are Agent 2C: Gap Map Database & Scrapers.

Read:
- docs/IMPLEMENTATION_PRIORITIES.md (Agent 2C section)
- The specific "Claude Instruction for Agent 2C"

Execute all tasks for Agent 2C:
- Create app/services/gap_map_repository.py
- Create app/services/scrapers/ (all 5 scrapers)
- Create app/services/gap_map_scraper.py
- Create app/jobs/gap_map_scraper_job.py
- Create tests/test_gap_map_repository.py

For MVP: Use hardcoded sample data in scrapers to save time.

When done:
- Update docs/BUILD_STATUS.md (mark Agent 2C complete)
- Tell me you're finished
```

#### Window 5: Launch Agent 2D
```
Instruction to Claude:

You are Agent 2D: Pivot Matcher & Report Generator.

Read:
- docs/IMPLEMENTATION_PRIORITIES.md (Agent 2D section)
- The specific "Claude Instruction for Agent 2D"

Execute all tasks for Agent 2D:
- Create app/services/pivot_matcher.py
- Create app/services/report_generator.py
- Create tests/test_pivot_matcher.py

When done:
- Update docs/BUILD_STATUS.md (mark Agent 2D complete)
- Tell me you're finished
```

#### Window 6: Launch Agent 3A
```
Instruction to Claude:

You are Agent 3A: Frontend Chat Interface.

Read:
- docs/IMPLEMENTATION_PRIORITIES.md (Agent 3A section)
- The specific "Claude Instruction for Agent 3A"

Execute all tasks for Agent 3A:
- Initialize Vite + React + TypeScript project
- Set up Shadcn UI
- Create src/components/chat-interface.tsx
- Create src/components/file-upload.tsx
- Create src/lib/utils.ts

When done:
- Update docs/BUILD_STATUS.md (mark Agent 3A complete)
- Tell me you're finished
```

#### Window 7: Launch Agent 3B
```
Instruction to Claude:

You are Agent 3B: Frontend Results View & API Client.

Read:
- docs/IMPLEMENTATION_PRIORITIES.md (Agent 3B section)
- The specific "Claude Instruction for Agent 3B"

Execute all tasks for Agent 3B:
- Create src/types/index.ts (TypeScript types)
- Create src/api/client.ts (axios client)
- Create src/hooks/useAnalysis.ts (TanStack Query hooks)
- Create src/components/results-view.tsx

When done:
- Update docs/BUILD_STATUS.md (mark Agent 3B complete)
- Tell me you're finished
```

### Step 3: Monitor Progress
**In Window 1 or a spare terminal:**

```bash
# Watch BUILD_STATUS.md for updates
watch -n 5 cat docs/BUILD_STATUS.md

# Or manually check
cat docs/BUILD_STATUS.md
```

### Step 4: Phase 4 - Integration (10 minutes)
**Use Window 1 (Main Orchestrator) after all agents finish**

```
Instruction to Claude:

All Phase 2 and 3 agents are complete. Now run Phase 4: Backend API Integration.

Read docs/IMPLEMENTATION_PRIORITIES.md (Phase 4 section).

Tasks:
1. Create app/api/routes.py with all endpoints
2. Wire up services from Agents 2A-2D
3. Add CORS and error handling middleware
4. Initialize Alembic and create database migration
5. Run migration: alembic upgrade head

Update docs/BUILD_STATUS.md when Phase 4 is complete.
```

### Step 5: Phase 5 - Testing (5 minutes)
**Use Window 1 (Main Orchestrator)**

```
Instruction to Claude:

Run Phase 5: End-to-End Integration Testing.

Read docs/IMPLEMENTATION_PRIORITIES.md (Phase 5 section).

Tasks:
1. Start backend: uvicorn app.main:app --reload
2. Start frontend: npm run dev (in another terminal)
3. Test the complete user flow:
   - Input research question
   - Upload sample file
   - Verify analysis results
4. Document any critical issues in docs/BUILD_STATUS.md
5. Create README.md with setup instructions

Update docs/BUILD_STATUS.md when Phase 5 is complete.
Mark the entire build as COMPLETE.
```

---

## Communication Between Agents

### Shared State: BUILD_STATUS.md
All agents should:
1. **Read** `docs/BUILD_STATUS.md` before starting (to check dependencies)
2. **Update** `docs/BUILD_STATUS.md` after completing their tasks
3. **Document** any blockers immediately

### Conflict Resolution
If two agents need to edit the same file:
- **Phase 1 must complete first** (it creates all shared schemas)
- **Agents 2A-2D are independent** (no file conflicts)
- **Agents 3A-3B are independent** (no file conflicts)

If conflicts occur:
1. Agent that finishes first writes the file
2. Second agent reads the file and adds their code
3. Use git to merge if necessary

---

## Time Management Tips

### Staying on Track
- **Set a timer** for each phase
- **Don't wait** for perfect code - iterate later
- **Use mock data** liberally to unblock work
- **Skip tests** if running behind (add later)
- **Focus on core flow**: Chat → Analysis → Results

### If Running Behind
**Priority 1 (Must Have):**
- Chat interface (input)
- Novelty analysis (OpenAlex)
- Results display (output)

**Priority 2 (Should Have):**
- File upload
- Pivot suggestions
- Background scraper job

**Priority 3 (Nice to Have):**
- Full scraper implementation
- Comprehensive tests
- UI polish

### Speed Optimizations
1. **Copy-paste from plan file** - don't rewrite specs
2. **Use Claude's suggestions** - don't overthink
3. **Mock external APIs** - don't wait for real responses
4. **Hardcode sample data** - for gap maps initially
5. **Skip error handling** - add later if time permits

---

## Troubleshooting

### Agent Stuck or Slow
- **Check:** Is it waiting for API responses? Use mocks.
- **Check:** Is it over-engineering? Simplify the task.
- **Action:** Cancel and restart with simpler instructions.

### File Conflicts
- **Check:** Did Phase 1 complete successfully?
- **Action:** Have one agent wait, then merge changes.

### Integration Failures
- **Check:** Are all schemas consistent?
- **Check:** Is CORS configured correctly?
- **Action:** Test each service independently first.

### Out of Time
- **Action:** Deploy what works (core flow only)
- **Action:** Document incomplete features in BUILD_STATUS.md
- **Action:** Create GitHub issues for follow-up work

---

## Example Timeline (Target)

| Time      | Phase                | Activity                          |
|-----------|----------------------|-----------------------------------|
| 0:00-0:10 | Phase 1              | Foundation (1 agent)              |
| 0:10-0:30 | Phase 2 & 3          | Parallel development (6 agents)   |
| 0:30-0:40 | Phase 4              | API integration (1 agent)         |
| 0:40-0:45 | Phase 5              | Testing (1 agent)                 |
| 0:45-0:60 | Buffer               | Fixes, docs, polish               |

---

## Success Metrics

You've succeeded if by 1 hour:
- ✅ User can input research question (chat or file)
- ✅ System calls OpenAlex and shows novelty assessment
- ✅ System displays recommendations (CONTINUE/PIVOT)
- ✅ Frontend and backend communicate correctly
- ✅ Core flow works end-to-end (even with mocked data)

**Everything else is a bonus.**

---

## Post-Build: Cleanup & Handoff

After 1 hour:
1. **Merge all agent work** into main branch (if using git)
2. **Run tests** to verify nothing broke
3. **Update README.md** with what's complete vs TODO
4. **Create deployment guide** if time permits
5. **Document known issues** in GitHub issues

---

## FAQ

**Q: Can I use fewer agents?**
A: Yes, but you'll exceed 1 hour. Minimum 4 agents recommended (2A-2D).

**Q: What if I don't have multiple terminals?**
A: Use the Task tool with `run_in_background: true` to spawn agents.

**Q: Do agents share context?**
A: No. Each agent is independent. They communicate via files (BUILD_STATUS.md).

**Q: Can agents read each other's code?**
A: Yes, after files are written. Use Read tool to check other agents' work.

**Q: What if an agent fails?**
A: Document the blocker in BUILD_STATUS.md. Use mocks to continue other work.

**Q: How do I know when an agent is done?**
A: Check BUILD_STATUS.md or ask the agent "Are you finished?"

**Q: Should I review agent code before proceeding?**
A: Quick glance only. Trust the agents. Fix issues in Phase 4-5.

---

## Resources

- **IMPLEMENTATION_PRIORITIES.md**: Task definitions and dependencies
- **BUILD_STATUS.md**: Real-time progress tracking
- **.cursorrules**: Behavioral rules for all agents
- **TECH_STACK.md**: Library choices and versions
- **research_pivot_advisor_system.plan.md**: Complete system specification
