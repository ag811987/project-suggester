# 🚀 START HERE - Claude Code CLI Build Guide

## ✅ Claude Code CLI Installed and Ready!

```bash
$ claude --version
2.1.39 (Claude Code)
```

You're currently in a Claude Code session. Perfect for the multi-agent build!

---

## ⚡ Quick Start (3 Steps)

### Step 1: Run Setup Script (5 minutes)
```bash
cd /Users/amit/Coding-Projects/Project-Suggester
./setup.sh
```

This installs:
- ✅ Python 3.11 (upgrade from 3.9.6)
- ✅ Poetry (Python package manager)
- ✅ Docker Desktop
- ✅ Node.js 18+
- ✅ PostgreSQL & Redis containers

### Step 2: Verify Setup
```bash
python3.11 --version   # Should be 3.11.x
poetry --version
docker ps              # Should show postgres and redis
claude --version       # Should be 2.1.39
```

### Step 3: Start Multi-Agent Build
1. Open **7 terminal windows** (or tabs)
2. In each: `cd /Users/amit/Coding-Projects/Project-Suggester && claude`
3. Follow instructions in **[docs/CLAUDE_CODE_CLI_SETUP.md](docs/CLAUDE_CODE_CLI_SETUP.md)**

---

## 📚 Documentation

### Main Guide (Start Here!)
**[docs/CLAUDE_CODE_CLI_SETUP.md](docs/CLAUDE_CODE_CLI_SETUP.md)** ⭐
- Complete setup instructions
- Multi-terminal agent strategy
- Step-by-step build phases
- All agent instructions ready to copy-paste

### Supporting Docs
- [docs/IMPLEMENTATION_PRIORITIES.md](docs/IMPLEMENTATION_PRIORITIES.md) - Detailed task breakdown
- [docs/TECH_STACK.md](docs/TECH_STACK.md) - Technology choices
- [docs/OXYLABS_INTEGRATION.md](docs/OXYLABS_INTEGRATION.md) - Web scraping guide
- [docs/BUILD_STATUS.md](docs/BUILD_STATUS.md) - Track progress here
- [docs/EXPECTED_FILE_STRUCTURE.md](docs/EXPECTED_FILE_STRUCTURE.md) - Verify completion

### Reference (Original Planning)
- [research_pivot_advisor_system.plan.md](research_pivot_advisor_system.plan.md) - Complete specification
- [BUILD_GUIDE_README.md](BUILD_GUIDE_README.md) - Original overview

---

## 🎯 Multi-Agent Strategy

### Why 7 Terminal Windows?

Claude Code CLI in multiple terminals = **true parallelization**

**Layout:**
```
Terminal 1: Main/Phase 1 (Foundation)
Terminal 2: Agent 2A (Info Collection)
Terminal 3: Agent 2B (Novelty Analyzer)
Terminal 4: Agent 2C (Gap Map Scrapers)
Terminal 5: Agent 2D (Pivot Matcher)
Terminal 6: Agent 3A (Frontend Chat)
Terminal 7: Agent 3B (Frontend Results)
```

**Benefits:**
- ✅ 6 agents work simultaneously (Phase 2 & 3)
- ✅ Each agent has independent context
- ✅ 80 minutes of work → 20 minutes wall time
- ✅ Easy monitoring (one terminal per agent)

---

## 📊 Timeline (With Parallelization)

| Phase | Time | Terminals | Activity |
|-------|------|-----------|----------|
| Setup | 5 min | 1 | Run ./setup.sh |
| Phase 1 | 10 min | 1 | Foundation (schemas, config) |
| Phase 2 & 3 | 20 min | **6 parallel** | Backend + Frontend |
| Phase 4 | 10 min | 1 | API integration |
| Phase 5 | 10 min | 1 | Testing |

**Total: ~55 minutes** (with perfect parallelization)

---

## 🚀 Quick Command Reference

### Setup (First Time Only)
```bash
# Run automated setup
./setup.sh

# Or manual setup:
brew install python@3.11
curl -sSL https://install.python-poetry.org | python3.11 -
brew install --cask docker
open /Applications/Docker.app
docker-compose up -d
```

### Verify Environment
```bash
# Check all tools
python3.11 --version
poetry --version
docker ps
claude --version
node --version

# Check API keys
cat .env | grep OPENAI_API_KEY
cat .env | grep ANTHROPIC_API_KEY
```

### Start Building
```bash
# In each of 7 terminal windows:
cd /Users/amit/Coding-Projects/Project-Suggester
claude

# Then paste agent instructions from docs/CLAUDE_CODE_CLI_SETUP.md
```

---

## ✅ Pre-Flight Checklist

Before starting the build:

- [ ] Run `./setup.sh` successfully
- [ ] Python 3.11+ installed and working
- [ ] Poetry installed
- [ ] Docker running (verify with `docker ps`)
- [ ] PostgreSQL container running on port 5432
- [ ] Redis container running on port 6379
- [ ] Claude Code CLI working (`claude --version`)
- [ ] API keys in `.env` file
- [ ] 7 terminal windows ready

---

## 🎯 Success Criteria

After ~55 minutes, you'll have:

- ✅ Full-stack application running
- ✅ Backend: FastAPI + PostgreSQL + Redis
- ✅ Frontend: React + TypeScript + Vite
- ✅ OpenAlex integration with FWCI metrics
- ✅ LLM-powered analysis and matching
- ✅ Gap map database with sample data
- ✅ Core flow: Input → Analysis → Recommendation

**Functional MVP, ready for iteration and polish.**

---

## 📞 Troubleshooting

### Python 3.11 not found
```bash
brew install python@3.11
export PATH="/opt/homebrew/opt/python@3.11/bin:$PATH"
```

### Poetry not found
```bash
curl -sSL https://install.python-poetry.org | python3.11 -
export PATH="$HOME/.local/bin:$PATH"
```

### Docker not running
```bash
open /Applications/Docker.app
# Wait 30 seconds
docker ps
```

### Port conflicts
```bash
# Kill process on port 8000 (backend)
lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill -9

# Kill process on port 5173 (frontend)
lsof -i :5173 | grep LISTEN | awk '{print $2}' | xargs kill -9
```

**Full troubleshooting guide:** [docs/CLAUDE_CODE_CLI_SETUP.md](docs/CLAUDE_CODE_CLI_SETUP.md)

---

## 💡 Pro Tips

1. **Copy-paste instructions** - All agent instructions ready in docs/
2. **Watch BUILD_STATUS.md** - Monitor progress across agents
3. **Use @mentions** - Reference docs with `@docs/filename.md`
4. **One task per agent** - Keep instructions focused
5. **Wait for "COMPLETE"** - Ensure phases finish before proceeding

---

## 🎉 You're Ready!

Everything is configured:
- ✅ Claude Code CLI installed (2.1.39)
- ✅ API keys in `.env` (OpenAI, Anthropic, OpenAlex, Oxylabs)
- ✅ Documentation prepared
- ✅ Setup script ready

**Next step:**
```bash
./setup.sh
```

Then follow **[docs/CLAUDE_CODE_CLI_SETUP.md](docs/CLAUDE_CODE_CLI_SETUP.md)** to start building! 🚀
