# Expected File Structure After Build

This document shows the complete file structure you should have after completing the 1-hour build.

## Root Directory

```
Project-Suggester/
├── BUILD_GUIDE_README.md              ← Start here
├── .cursorrules                       ← Claude behavioral rules
├── .env.example                       ← Environment variables template
├── .env                               ← Your actual env vars (not in git)
├── docker-compose.yml                 ← PostgreSQL + Redis
├── .gitignore                         ← Git ignore file
├── research_pivot_advisor_system.plan.md  ← Original specification
│
├── docs/                              ← All documentation
│   ├── QUICK_START.md                 ← Execution guide
│   ├── ACTION_PLAN.md                 ← Strategy overview
│   ├── IMPLEMENTATION_PRIORITIES.md   ← Task breakdown
│   ├── PARALLELIZATION_GUIDE.md       ← Multi-agent guide
│   ├── TECH_STACK.md                  ← Technology choices
│   ├── BUILD_STATUS.md                ← Progress tracking (live)
│   └── EXPECTED_FILE_STRUCTURE.md     ← This file
│
├── research-advisor-backend/          ← Python/FastAPI backend
│   ├── pyproject.toml                 ← Poetry dependencies
│   ├── poetry.lock                    ← Locked dependencies
│   ├── alembic.ini                    ← Alembic config
│   ├── README.md                      ← Backend setup instructions
│   │
│   ├── app/                           ← Main application code
│   │   ├── __init__.py
│   │   ├── main.py                    ← FastAPI app entry point
│   │   ├── config.py                  ← Environment configuration
│   │   │
│   │   ├── models/                    ← Data models
│   │   │   ├── __init__.py
│   │   │   ├── schemas.py             ← Pydantic models (Phase 1)
│   │   │   └── gap_map_models.py      ← SQLAlchemy models (Phase 1)
│   │   │
│   │   ├── services/                  ← Business logic
│   │   │   ├── __init__.py
│   │   │   ├── document_parser.py     ← Agent 2A
│   │   │   ├── info_collector.py      ← Agent 2A
│   │   │   ├── openalex_client.py     ← Agent 2B
│   │   │   ├── novelty_analyzer.py    ← Agent 2B
│   │   │   ├── gap_map_repository.py  ← Agent 2C
│   │   │   ├── gap_map_scraper.py     ← Agent 2C (orchestrator)
│   │   │   ├── pivot_matcher.py       ← Agent 2D
│   │   │   ├── report_generator.py    ← Agent 2D
│   │   │   │
│   │   │   └── scrapers/              ← Web scrapers (Agent 2C)
│   │   │       ├── __init__.py
│   │   │       ├── base_scraper.py
│   │   │       ├── convergent_scraper.py
│   │   │       ├── homeworld_scraper.py
│   │   │       ├── wikenigma_scraper.py
│   │   │       ├── threeie_scraper.py
│   │   │       └── encyclopedia_scraper.py
│   │   │
│   │   ├── api/                       ← API endpoints
│   │   │   ├── __init__.py
│   │   │   └── routes.py              ← Phase 4
│   │   │
│   │   └── jobs/                      ← Background jobs
│   │       ├── __init__.py
│   │       └── gap_map_scraper_job.py ← Agent 2C
│   │
│   ├── alembic/                       ← Database migrations
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   │       └── [timestamp]_initial_migration.py  ← Phase 4
│   │
│   └── tests/                         ← Test suite
│       ├── __init__.py
│       ├── conftest.py                ← Pytest fixtures
│       ├── test_info_collector.py     ← Agent 2A
│       ├── test_novelty_analyzer.py   ← Agent 2B
│       ├── test_gap_map_repository.py ← Agent 2C
│       └── test_pivot_matcher.py      ← Agent 2D
│
└── research-advisor-frontend/         ← React/TypeScript frontend
    ├── package.json                   ← npm dependencies
    ├── package-lock.json              ← Locked dependencies
    ├── tsconfig.json                  ← TypeScript config
    ├── vite.config.ts                 ← Vite config
    ├── tailwind.config.js             ← Tailwind config
    ├── postcss.config.js              ← PostCSS config
    ├── index.html                     ← HTML entry point
    ├── README.md                      ← Frontend setup instructions
    │
    ├── public/                        ← Static assets
    │   └── vite.svg
    │
    └── src/                           ← Source code
        ├── main.tsx                   ← React entry point
        ├── App.tsx                    ← Main app component
        ├── index.css                  ← Global styles
        ├── vite-env.d.ts              ← Vite types
        │
        ├── components/                ← React components
        │   ├── chat-interface.tsx     ← Agent 3A
        │   ├── file-upload.tsx        ← Agent 3A
        │   ├── results-view.tsx       ← Agent 3B
        │   │
        │   └── ui/                    ← Shadcn UI components
        │       ├── button.tsx
        │       ├── card.tsx
        │       ├── input.tsx
        │       ├── textarea.tsx
        │       ├── progress.tsx
        │       ├── alert.tsx
        │       └── [other shadcn components]
        │
        ├── api/                       ← API client
        │   └── client.ts              ← Agent 3B (axios setup)
        │
        ├── hooks/                     ← Custom React hooks
        │   └── useAnalysis.ts         ← Agent 3B (TanStack Query)
        │
        ├── types/                     ← TypeScript types
        │   └── index.ts               ← Agent 3B (mirrors backend schemas)
        │
        └── lib/                       ← Utilities
            └── utils.ts               ← Agent 3A (cn function)
```

---

## File Count Summary

| Component | Files | Created By |
|-----------|-------|------------|
| **Documentation** | 8 files | Pre-built |
| **Backend Core** | 6 files | Phase 1 & 4 |
| **Backend Services** | 13 files | Agents 2A-2D |
| **Backend Tests** | 5 files | Agents 2A-2D |
| **Frontend Core** | 9 files | Agent 3A |
| **Frontend Components** | 4+ files | Agents 3A & 3B |
| **Frontend API/Hooks** | 3 files | Agent 3B |
| **Shadcn UI** | 7+ files | Agent 3A |
| **Database** | 1 migration | Phase 4 |

**Total:** ~55-65 files (depending on Shadcn components installed)

---

## Verification Checklist

After completing the build, verify these files exist:

### Phase 1: Foundation
- [ ] `research-advisor-backend/app/models/schemas.py`
- [ ] `research-advisor-backend/app/models/gap_map_models.py`
- [ ] `research-advisor-backend/pyproject.toml`
- [ ] `research-advisor-backend/app/config.py`
- [ ] `.env` (with your API keys)
- [ ] `docker-compose.yml`

### Agent 2A: Info Collection
- [ ] `research-advisor-backend/app/services/document_parser.py`
- [ ] `research-advisor-backend/app/services/info_collector.py`
- [ ] `research-advisor-backend/tests/test_info_collector.py`

### Agent 2B: Novelty Analyzer
- [ ] `research-advisor-backend/app/services/openalex_client.py`
- [ ] `research-advisor-backend/app/services/novelty_analyzer.py`
- [ ] `research-advisor-backend/tests/test_novelty_analyzer.py`

### Agent 2C: Gap Map System
- [ ] `research-advisor-backend/app/services/gap_map_repository.py`
- [ ] `research-advisor-backend/app/services/gap_map_scraper.py`
- [ ] `research-advisor-backend/app/services/scrapers/base_scraper.py`
- [ ] `research-advisor-backend/app/services/scrapers/convergent_scraper.py`
- [ ] `research-advisor-backend/app/services/scrapers/homeworld_scraper.py`
- [ ] `research-advisor-backend/app/services/scrapers/wikenigma_scraper.py`
- [ ] `research-advisor-backend/app/services/scrapers/threeie_scraper.py`
- [ ] `research-advisor-backend/app/services/scrapers/encyclopedia_scraper.py`
- [ ] `research-advisor-backend/app/jobs/gap_map_scraper_job.py`
- [ ] `research-advisor-backend/tests/test_gap_map_repository.py`

### Agent 2D: Pivot Matcher
- [ ] `research-advisor-backend/app/services/pivot_matcher.py`
- [ ] `research-advisor-backend/app/services/report_generator.py`
- [ ] `research-advisor-backend/tests/test_pivot_matcher.py`

### Agent 3A: Chat Interface
- [ ] `research-advisor-frontend/package.json`
- [ ] `research-advisor-frontend/src/components/chat-interface.tsx`
- [ ] `research-advisor-frontend/src/components/file-upload.tsx`
- [ ] `research-advisor-frontend/src/lib/utils.ts`
- [ ] `research-advisor-frontend/src/components/ui/` (directory with Shadcn components)

### Agent 3B: Results View
- [ ] `research-advisor-frontend/src/types/index.ts`
- [ ] `research-advisor-frontend/src/api/client.ts`
- [ ] `research-advisor-frontend/src/hooks/useAnalysis.ts`
- [ ] `research-advisor-frontend/src/components/results-view.tsx`

### Phase 4: Integration
- [ ] `research-advisor-backend/app/api/routes.py`
- [ ] `research-advisor-backend/app/main.py`
- [ ] `research-advisor-backend/alembic/versions/[timestamp]_initial_migration.py`

### Phase 5: Documentation
- [ ] `research-advisor-backend/README.md`
- [ ] `research-advisor-frontend/README.md`
- [ ] Root `README.md` (optional, created in Phase 5)

---

## Quick Verification Commands

### Check Backend Files
```bash
# Navigate to backend
cd research-advisor-backend

# Count Python files in app/
find app/ -name "*.py" | wc -l
# Expected: ~20-25 files

# Verify all services exist
ls -1 app/services/
# Should see: 9+ files

# Verify all scrapers exist
ls -1 app/services/scrapers/
# Should see: 6 files (base + 5 scrapers)

# Check tests
ls -1 tests/
# Should see: 4+ test files
```

### Check Frontend Files
```bash
# Navigate to frontend
cd research-advisor-frontend

# Count TypeScript/TSX files
find src/ -name "*.tsx" -o -name "*.ts" | wc -l
# Expected: ~15-25 files (depends on Shadcn components)

# Verify components exist
ls -1 src/components/
# Should see: chat-interface.tsx, file-upload.tsx, results-view.tsx, ui/

# Check Shadcn UI components
ls -1 src/components/ui/
# Should see: button.tsx, card.tsx, input.tsx, etc.
```

### Check Database Migration
```bash
cd research-advisor-backend

# List migrations
poetry run alembic history
# Should show: 1 migration (initial)

# Check migration file exists
ls -1 alembic/versions/
# Should see: [timestamp]_initial_migration.py
```

---

## File Size Expectations

### Backend
| Directory | Approx Size | File Count |
|-----------|-------------|------------|
| `app/models/` | ~5-10 KB | 2 files |
| `app/services/` | ~50-80 KB | 9+ files |
| `app/services/scrapers/` | ~30-50 KB | 6 files |
| `app/api/` | ~10-15 KB | 1 file |
| `app/jobs/` | ~5-10 KB | 1 file |
| `tests/` | ~20-30 KB | 4+ files |
| `alembic/versions/` | ~2-5 KB | 1 file |

**Total Backend Code:** ~130-200 KB (~30-35 files)

### Frontend
| Directory | Approx Size | File Count |
|-----------|-------------|------------|
| `src/components/` | ~30-50 KB | 3-4 files |
| `src/components/ui/` | ~20-40 KB | 7+ files |
| `src/api/` | ~5-10 KB | 1 file |
| `src/hooks/` | ~5-10 KB | 1 file |
| `src/types/` | ~5-10 KB | 1 file |
| `src/lib/` | ~1-2 KB | 1 file |

**Total Frontend Code:** ~70-120 KB (~15-25 files)

---

## Missing Files = Incomplete Agents

If files are missing, identify which agent didn't complete:

| Missing File | Agent | Action |
|--------------|-------|--------|
| `schemas.py` | Phase 1 | CRITICAL - restart Phase 1 |
| `info_collector.py` | Agent 2A | Rerun Agent 2A |
| `novelty_analyzer.py` | Agent 2B | Rerun Agent 2B |
| `gap_map_repository.py` | Agent 2C | Rerun Agent 2C |
| `pivot_matcher.py` | Agent 2D | Rerun Agent 2D |
| `chat-interface.tsx` | Agent 3A | Rerun Agent 3A |
| `results-view.tsx` | Agent 3B | Rerun Agent 3B |
| `routes.py` | Phase 4 | Rerun Phase 4 |

---

## File Content Verification

### Critical Files to Review

#### 1. `app/models/schemas.py` (Phase 1)
Should contain:
- [ ] `ResearchProfile` class
- [ ] `NoveltyAssessment` class with FWCI fields
- [ ] `GapMapEntry` class
- [ ] `PivotSuggestion` class
- [ ] `ResearchRecommendation` class
- [ ] `ChatMessage` class
- [ ] `Citation` class
- [ ] Enums: `NoveltyVerdict`, `ImpactLevel`, `RecommendationType`

#### 2. `app/main.py` (Phase 4)
Should contain:
- [ ] FastAPI app initialization
- [ ] CORS middleware configuration
- [ ] Lifespan context manager (Redis, DB setup)
- [ ] Router inclusion (`app.include_router(routes.router)`)
- [ ] Global exception handler

#### 3. `app/api/routes.py` (Phase 4)
Should contain:
- [ ] `POST /api/v1/analyze` endpoint
- [ ] `GET /api/v1/analysis/{session_id}` endpoint
- [ ] `POST /api/v1/chat` endpoint
- [ ] `DELETE /api/v1/session/{session_id}` endpoint
- [ ] Redis session management
- [ ] Service integrations (info_collector, novelty_analyzer, etc.)

#### 4. `src/components/chat-interface.tsx` (Agent 3A)
Should contain:
- [ ] Message list rendering
- [ ] Input textarea
- [ ] Send button
- [ ] File upload integration
- [ ] Loading states

#### 5. `src/components/results-view.tsx` (Agent 3B)
Should contain:
- [ ] Recommendation display (CONTINUE/PIVOT badge)
- [ ] Novelty assessment section
- [ ] FWCI metrics display
- [ ] Pivot suggestions list
- [ ] Citations section

---

## Directory Permissions

Ensure correct permissions:

```bash
# Backend should have these permissions
chmod +x research-advisor-backend/app/main.py

# Frontend should have these permissions
chmod +x research-advisor-frontend/node_modules/.bin/*

# Scripts should be executable
find . -name "*.sh" -exec chmod +x {} \;
```

---

## Git Ignore

Ensure these are in `.gitignore`:

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
.venv/
venv/
*.egg-info/
.pytest_cache/

# Node
node_modules/
dist/
build/
.vite/

# Environment
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Database
*.db
*.sqlite3

# Logs
*.log
logs/
```

---

## Verification Script

Create this script to auto-verify file structure:

```bash
#!/bin/bash
# verify_structure.sh

echo "Verifying file structure..."

ERRORS=0

# Check critical backend files
BACKEND_FILES=(
    "research-advisor-backend/app/models/schemas.py"
    "research-advisor-backend/app/models/gap_map_models.py"
    "research-advisor-backend/app/services/info_collector.py"
    "research-advisor-backend/app/services/novelty_analyzer.py"
    "research-advisor-backend/app/services/pivot_matcher.py"
    "research-advisor-backend/app/api/routes.py"
    "research-advisor-backend/app/main.py"
)

for file in "${BACKEND_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Missing: $file"
        ERRORS=$((ERRORS + 1))
    else
        echo "✅ Found: $file"
    fi
done

# Check critical frontend files
FRONTEND_FILES=(
    "research-advisor-frontend/src/components/chat-interface.tsx"
    "research-advisor-frontend/src/components/results-view.tsx"
    "research-advisor-frontend/src/api/client.ts"
    "research-advisor-frontend/src/types/index.ts"
)

for file in "${FRONTEND_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Missing: $file"
        ERRORS=$((ERRORS + 1))
    else
        echo "✅ Found: $file"
    fi
done

if [ $ERRORS -eq 0 ]; then
    echo "✅ All critical files present!"
    exit 0
else
    echo "❌ $ERRORS files missing!"
    exit 1
fi
```

Run with: `bash verify_structure.sh`

---

## Summary

After completing the 1-hour build, you should have:
- **~55-65 files** total
- **8 documentation files** (pre-created)
- **~30-35 backend files** (Python)
- **~15-25 frontend files** (TypeScript/React)
- **1 database migration**
- **4+ test files**

If any critical files are missing, check `docs/BUILD_STATUS.md` to see which agent didn't complete, then rerun that specific agent.
