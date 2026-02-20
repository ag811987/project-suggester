# 🚀 START HERE - Cursor IDE Build Guide

## Your Environment
- **IDE**: Cursor (VS Code fork with built-in AI)
- **Python**: Currently 3.9.6 → **Needs upgrade to 3.11+**
- **Setup Status**: ⚠️ Requires initial setup

---

## ⚡ Quick Start (3 Steps)

### Step 1: Run Setup Script (5 minutes)
```bash
cd /Users/amit/Coding-Projects/Project-Suggester
./setup.sh
```

This will automatically install:
- ✅ Python 3.11
- ✅ Poetry (Python package manager)
- ✅ Docker Desktop
- ✅ Node.js 18+
- ✅ Start PostgreSQL and Redis containers

**If setup script fails**, follow manual instructions in [docs/CURSOR_IDE_SETUP.md](docs/CURSOR_IDE_SETUP.md).

### Step 2: Verify Setup
```bash
# Check all tools are installed
python3.11 --version   # Should be 3.11.x
poetry --version       # Should show poetry version
docker ps              # Should show postgres and redis running
node --version         # Should be 18.x or higher
```

### Step 3: Start Building in Cursor
1. Open Cursor IDE (you're already here!)
2. Open Composer: **Cmd+I** (or Cmd+Shift+I for sidebar)
3. Follow instructions in [docs/CURSOR_IDE_SETUP.md](docs/CURSOR_IDE_SETUP.md)

---

## 📚 Documentation for Cursor IDE

### Primary Guide
**[docs/CURSOR_IDE_SETUP.md](docs/CURSOR_IDE_SETUP.md)** ⭐ **START HERE**
- Environment setup for Cursor IDE
- How to use multiple Composer tabs as "agents"
- Step-by-step build instructions
- Python 3.11 setup
- Troubleshooting

### Supporting Docs
- [docs/IMPLEMENTATION_PRIORITIES.md](docs/IMPLEMENTATION_PRIORITIES.md) - Task breakdown for each agent
- [docs/TECH_STACK.md](docs/TECH_STACK.md) - Technology choices
- [docs/OXYLABS_INTEGRATION.md](docs/OXYLABS_INTEGRATION.md) - Web scraping guide
- [docs/BUILD_STATUS.md](docs/BUILD_STATUS.md) - Track your progress here
- [docs/EXPECTED_FILE_STRUCTURE.md](docs/EXPECTED_FILE_STRUCTURE.md) - Verify completeness

### Original Planning (Reference)
- [BUILD_GUIDE_README.md](BUILD_GUIDE_README.md) - Original overview (written for CLI)
- [research_pivot_advisor_system.plan.md](research_pivot_advisor_system.plan.md) - Complete specification

---

## 🎯 Build Phases (Cursor IDE)

### Phase 1: Foundation (10 min) - 1 Composer Tab
Create schemas, config, and directory structure.

### Phase 2: Backend Services (30 min) - 4 Composer Tabs (or sequential)
Build 4 independent services in parallel:
- Agent 2A: Info Collection
- Agent 2B: Novelty Analyzer
- Agent 2C: Gap Map Scrapers
- Agent 2D: Pivot Matcher

### Phase 3: Frontend (20 min) - 1 Composer Tab
Build React UI with chat interface and results view.

### Phase 4: Integration (10 min) - 1 Composer Tab
Wire everything together and create API endpoints.

### Phase 5: Testing (10 min) - Manual + 1 Composer Tab
Test end-to-end flow and verify functionality.

**Total Time: ~95 minutes** (including setup)

---

## 💡 Using Cursor Composer as "Multiple Agents"

### Option A: Multiple Tabs (Parallel - Faster)
1. Open 4+ Composer tabs (**Cmd+I** multiple times)
2. Give each tab its agent instruction
3. Let them work simultaneously
4. Each maintains independent context

**Pros:** Parallel execution, faster build
**Cons:** Need to manage multiple tabs

### Option B: Sequential (Simple - Slower)
1. Use one Composer tab
2. Complete phases one at a time
3. Start new chat for each major phase

**Pros:** Simpler, less context switching
**Cons:** Slower (no parallelization)

---

## 🔧 What the Setup Script Does

```bash
./setup.sh
```

1. **Checks** current environment
2. **Installs** Homebrew (if needed)
3. **Installs** Python 3.11
4. **Installs** Poetry for Python package management
5. **Installs** Docker Desktop
6. **Installs** Node.js 18+
7. **Starts** PostgreSQL and Redis containers via Docker Compose
8. **Verifies** everything is working

**Time:** ~5-10 minutes (depending on what's already installed)

---

## ✅ Environment Checklist

After running `./setup.sh`, verify:

```bash
# Python 3.11+
python3.11 --version
# Expected: Python 3.11.x

# Poetry
poetry --version
# Expected: Poetry (version 1.x.x)

# Docker
docker --version
docker ps
# Expected: postgres and redis containers running

# Node.js
node --version
# Expected: v18.x.x or higher

# Environment variables
cat .env | grep OPENAI_API_KEY
# Expected: Your actual API key (not empty)
```

---

## 🚀 First Composer Instruction (Phase 1)

After setup is complete, open Composer (**Cmd+I**) and paste this:

```
You are building the Research Pivot Advisor System using Cursor IDE.

ENVIRONMENT:
- Python: 3.11+ (use python3.11 command)
- IDE: Cursor
- Working directory: /Users/amit/Coding-Projects/Project-Suggester

START PHASE 1: Foundation

Read docs/IMPLEMENTATION_PRIORITIES.md and complete Phase 1 tasks:

1. Create directory structure for backend and frontend
2. Create app/models/schemas.py with ALL Pydantic models (from research_pivot_advisor_system.plan.md lines 227-281)
3. Create app/models/gap_map_models.py with SQLAlchemy models (from plan lines 318-339)
4. Create pyproject.toml using Poetry (specify python = "^3.11")
5. Create app/config.py with Pydantic settings
6. Verify docker-compose.yml is correct

IMPORTANT:
- Use python3.11 in all scripts
- Use poetry for Python dependency management
- Update docs/BUILD_STATUS.md after each task with timestamp

When Phase 1 is complete, tell me "PHASE 1 COMPLETE" and show me what you created.
```

---

## 🆘 Troubleshooting

### Issue: Setup script fails
**Solution:** Follow manual instructions in [docs/CURSOR_IDE_SETUP.md](docs/CURSOR_IDE_SETUP.md)

### Issue: Python 3.11 not found after setup
```bash
# Check where it was installed
which python3.11

# Add to PATH if needed
echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Try again
python3.11 --version
```

### Issue: Poetry not found
```bash
# Add to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Verify
poetry --version
```

### Issue: Docker containers not starting
```bash
# Make sure Docker Desktop is running
open /Applications/Docker.app

# Wait 30 seconds, then try
docker-compose up -d
docker ps
```

### Issue: Port already in use
```bash
# Find what's using port 5432 (PostgreSQL)
lsof -i :5432

# Kill it if needed
kill -9 <PID>

# Restart containers
docker-compose restart
```

---

## 📊 Expected Timeline

| Phase | Time | Composer Tabs | Activity |
|-------|------|---------------|----------|
| **Setup** | 5-10 min | N/A | Run ./setup.sh |
| **Phase 1** | 10 min | 1 | Foundation (schemas, config) |
| **Phase 2** | 30 min | 4 or 1 | Backend services |
| **Phase 3** | 20 min | 1 | Frontend (React) |
| **Phase 4** | 10 min | 1 | API integration |
| **Phase 5** | 10 min | 1 | Testing |
| **Buffer** | 10 min | 1 | Fixes, polish |

**Total:** ~95-105 minutes

---

## 🎯 Success Criteria

By the end, you'll have:
- ✅ Full-stack application running locally
- ✅ Backend: FastAPI + PostgreSQL + Redis
- ✅ Frontend: React + TypeScript + Vite
- ✅ Core flow: Input → Analysis → Recommendation
- ✅ OpenAlex integration with FWCI metrics
- ✅ Gap map database with sample data
- ✅ LLM-powered matching and reports

**Not production-ready, but fully functional MVP.**

---

## 📞 Next Steps

1. **Run setup:** `./setup.sh`
2. **Verify environment:** Check all tools work
3. **Read Cursor guide:** [docs/CURSOR_IDE_SETUP.md](docs/CURSOR_IDE_SETUP.md)
4. **Start building:** Open Composer and begin Phase 1
5. **Track progress:** Update [docs/BUILD_STATUS.md](docs/BUILD_STATUS.md)

---

## 🎉 You're Ready!

Everything is configured:
- ✅ API keys in `.env`
- ✅ Docker Compose ready
- ✅ Documentation prepared
- ✅ Setup script ready to run

**Run `./setup.sh` to begin!**
