# Research Pivot Advisor System - Build Guide

## 🎯 Goal
Build a complete full-stack application in **1 hour** using Claude Code with parallel agent execution.

## 📋 What You're Building

A research advisor system that helps PhD/Post-Doc researchers decide whether to:
- **CONTINUE** their current research (if novel and high-impact)
- **PIVOT** to more promising directions (if already solved or low-impact)

### How It Works
1. Researcher inputs their research question + skills + motivations (chat or file upload)
2. System analyzes novelty using OpenAlex (is it already solved?)
3. System assesses impact using FWCI metrics (does it matter?)
4. System matches researcher to alternative high-impact problems (if needed)
5. System generates a narrative report with recommendations

---

## 🗂️ Documentation Structure

**Start here** → **Execution guide** → **Reference docs**

```
├── BUILD_GUIDE_README.md              ← YOU ARE HERE (start)
│
├── docs/
│   ├── QUICK_START.md                 ← Step-by-step execution (read this next!)
│   ├── ACTION_PLAN.md                 ← High-level overview and strategy
│   ├── IMPLEMENTATION_PRIORITIES.md   ← Detailed task breakdown
│   ├── PARALLELIZATION_GUIDE.md       ← How to run multiple Claude agents
│   ├── TECH_STACK.md                  ← Technology choices and versions
│   └── BUILD_STATUS.md                ← Live progress tracking (Claude updates this)
│
├── .cursorrules                       ← Behavioral rules for Claude agents
├── .env.example                       ← Environment variables template
├── docker-compose.yml                 ← PostgreSQL + Redis setup
└── research_pivot_advisor_system.plan.md  ← Original detailed specification
```

### Which File to Read When?

| When | Read | Why |
|------|------|-----|
| **Before starting** | `QUICK_START.md` | Step-by-step execution instructions |
| Understand strategy | `ACTION_PLAN.md` | High-level architecture and phases |
| During execution | `IMPLEMENTATION_PRIORITIES.md` | Task details for each agent |
| Setting up parallelization | `PARALLELIZATION_GUIDE.md` | How to run multiple Claude instances |
| Technology questions | `TECH_STACK.md` | What libraries to use and why |
| Tracking progress | `BUILD_STATUS.md` | See what's done and what's blocked |
| Detailed architecture | `research_pivot_advisor_system.plan.md` | Complete system specification |

---

## ⚡ Quick Start (60 Second Version)

### Prerequisites
- Claude Code installed
- Docker running
- OpenAI API key ($5+ credits)
- 7 terminal windows ready

### Execution
1. **Minutes 0-10:** Phase 1 in Terminal 1 (Foundation)
2. **Minutes 10-30:** Phase 2 & 3 in Terminals 2-7 (Parallel backend + frontend)
3. **Minutes 30-40:** Phase 4 in Terminal 1 (API integration)
4. **Minutes 40-45:** Phase 5 in Terminal 1 (Testing)
5. **Minutes 45-60:** Buffer for fixes

### Instructions for Claude
Each terminal gets a specific agent instruction from `docs/IMPLEMENTATION_PRIORITIES.md`.

**Example (Terminal 1, Phase 1):**
```
You are starting Phase 1 of the Research Pivot Advisor System build.

Read docs/IMPLEMENTATION_PRIORITIES.md and complete Phase 1 tasks:
1. Create project directory structure
2. Create all Pydantic schemas
3. Create SQLAlchemy models
4. Set up pyproject.toml and config

Update docs/BUILD_STATUS.md after each task.
Tell me when Phase 1 is complete.
```

**For detailed instructions, see `docs/QUICK_START.md`.**

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        User (Researcher)                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    ┌────────▼─────────┐
                    │  React Frontend  │
                    │  (Chat + Upload) │
                    └────────┬─────────┘
                             │ REST API
                    ┌────────▼─────────┐
                    │ FastAPI Backend  │
                    │  ┌─────────────┐ │
                    │  │ Info Collector (2A) │
                    │  │ Novelty Analyzer (2B) │
                    │  │ Gap Map DB (2C) │
                    │  │ Pivot Matcher (2D) │
                    │  │ Report Generator (2D) │
                    │  └─────────────┘ │
                    └────┬─────────┬───┘
                         │         │
                ┌────────▼──┐  ┌──▼─────────┐
                │PostgreSQL │  │   Redis    │
                │(Gap Maps) │  │ (Sessions) │
                └─────┬─────┘  └────────────┘
                      │
              ┌───────▼────────┐
              │  Background    │
              │  Scraper Job   │
              └────────────────┘

External APIs: OpenAI GPT-4, OpenAlex, Oxylabs (optional)
```

---

## 📊 Build Phases

| Phase | Time | Agents | Parallel? | Purpose |
|-------|------|--------|-----------|---------|
| **1. Foundation** | 10 min | 1 | No | Create schemas, config |
| **2. Backend Services** | 20 min | 4 | Yes | Build 4 independent services |
| **3. Frontend** | 15 min | 2 | Yes | Build UI (overlaps with Phase 2) |
| **4. Integration** | 10 min | 1 | No | Wire everything together |
| **5. Testing** | 5 min | 1 | No | Verify core flow |
| **Buffer** | 15 min | 1 | No | Fixes and polish |

**Total:** 60 minutes (45 min minimum + 15 min buffer)

---

## 🎯 Success Criteria

### Must Have (MVP)
By minute 60, these MUST work:
- ✅ User can input research question via chat
- ✅ System calls OpenAlex and analyzes novelty
- ✅ System calculates FWCI metrics for impact assessment
- ✅ System displays CONTINUE or PIVOT recommendation
- ✅ Frontend and backend communicate correctly

### Nice to Have (Stretch Goals)
- ✅ File upload (PDF, DOCX)
- ✅ Pivot suggestions with reasoning
- ✅ Real web scraping (not sample data)
- ✅ Comprehensive error handling
- ✅ Test coverage >70%

### Won't Have (Out of Scope)
- ❌ User authentication
- ❌ Production deployment
- ❌ UI polish and animations
- ❌ Performance optimization
- ❌ Security hardening

---

## 🚀 Next Steps

### 1. Pre-Flight Checklist (10 minutes)
- [ ] Read `docs/QUICK_START.md` (5 min)
- [ ] Skim `docs/ACTION_PLAN.md` (3 min)
- [ ] Get OpenAI API key with $5+ credits
- [ ] Verify Docker is running: `docker ps`
- [ ] Open 7 terminal windows in project directory
- [ ] Copy `.env.example` to `.env` and add API keys

### 2. Start Build (60 minutes)
- [ ] Follow `docs/QUICK_START.md` step-by-step
- [ ] Launch agents at specified times
- [ ] Monitor `docs/BUILD_STATUS.md` for progress
- [ ] Trust the agents - don't micromanage

### 3. Post-Build (10 minutes)
- [ ] Test core flow manually
- [ ] Document incomplete work
- [ ] Create git commit
- [ ] Write handoff notes

---

## 🆘 Troubleshooting

### Common Issues

**Issue:** "Claude is too slow"
- **Solution:** Use mocks instead of real API calls, simplify instructions

**Issue:** "File conflicts between agents"
- **Solution:** Phase 1 must complete first. Agents 2A-2D are independent.

**Issue:** "OpenAI API errors"
- **Solution:** Check API key, verify credits, use mocks if needed

**Issue:** "Running out of time"
- **Solution:** Focus on core flow only. Use hardcoded data. Skip tests.

**Full troubleshooting guide:** See `docs/QUICK_START.md` section "Troubleshooting"

---

## 📞 Support

**Getting Started:**
- Read: `docs/QUICK_START.md`
- Questions about architecture: `docs/ACTION_PLAN.md`
- Questions about tasks: `docs/IMPLEMENTATION_PRIORITIES.md`

**During Execution:**
- Check progress: `cat docs/BUILD_STATUS.md`
- Stuck on a task: Simplify and use mocks
- Agent blocked: Document in BUILD_STATUS.md and move on

---

## 📚 Additional Resources

### Original Planning
- `research_pivot_advisor_system.plan.md` - Complete system specification with:
  - Detailed architecture diagrams
  - All Pydantic schemas
  - FWCI analysis logic
  - Privacy and security requirements
  - Testing strategy

### Reference Documentation
- `.cursorrules` - Behavioral rules for Claude (read once, reference as needed)
- `docs/TECH_STACK.md` - Library choices and rationale
- `.env.example` - All environment variables with descriptions

---

## 🎓 Key Insights

### Why This Works
1. **Aggressive Parallelization:** 6 agents compress 80 min → 20 min
2. **Clear Contracts:** Schemas defined in Phase 1 unblock all parallel work
3. **Independence:** Agents don't conflict (separate files/services)
4. **Mock-First:** Use fake data to unblock dependencies
5. **Focus:** Core flow only, defer nice-to-haves

### What Makes 1-Hour Build Possible
- ✅ Detailed planning upfront (already done)
- ✅ Clear task breakdown with dependencies
- ✅ Parallel execution strategy
- ✅ Mock data to unblock work
- ✅ Focused MVP scope
- ✅ Claude Code's code generation speed

### What This Is NOT
- ❌ Production-ready deployment
- ❌ Fully tested (70%+ coverage)
- ❌ Polished UI/UX
- ❌ Optimized performance
- ❌ Comprehensive error handling

**This is a proof-of-concept with core functionality working.**

---

## 📈 Expected Outcomes

### After 1 Hour
- ✅ Core user flow works end-to-end
- ⚠️ Basic error handling (not comprehensive)
- ⚠️ Sample gap map data (not full scraping)
- ⚠️ Functional UI (not polished)
- ❌ Not production-ready

### Next Steps (Post-1-Hour)
1. Implement real web scraping (replace sample data) - 2 hours
2. Add comprehensive error handling - 1 hour
3. Increase test coverage to 80%+ - 2 hours
4. Polish UI/UX - 2 hours
5. Set up CI/CD and deploy to staging - 2 hours

**Total to production-ready:** +9 hours (10 hours total)

---

## 🏁 Ready to Start?

### Final Checklist
- ✅ OpenAI API key ready ($5+ credits)
- ✅ Docker Desktop running
- ✅ 7 terminal windows open in project directory
- ✅ Read `docs/QUICK_START.md`
- ✅ Understand the parallelization strategy
- ✅ Timer ready

### Let's Go!

**Navigate to:** `docs/QUICK_START.md`

**Start with:** Phase 1 instructions in Terminal 1

**Estimated completion:** 60 minutes from now

---

## 📄 License & Credits

**Built with:**
- Claude Code (Anthropic)
- FastAPI + React + PostgreSQL + Redis
- OpenAI GPT-4 + OpenAlex

**Architecture by:** [Your name]
**Date:** [Today's date]
**Build time:** 1 hour (target)

---

**Good luck! 🚀**
