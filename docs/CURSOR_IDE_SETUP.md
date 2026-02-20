# Cursor IDE Setup for Research Pivot Advisor Build

## Environment Detected
- **IDE**: Cursor (VS Code fork)
- **Python**: 3.9.6 → **Needs upgrade to 3.11+**
- **Claude**: Using Cursor's built-in AI (not CLI)

---

## 🔧 Required Setup

### 1. Upgrade Python to 3.11+

Python 3.9.6 is too old for this project. We need 3.11+ for modern type hints and async features.

#### Option A: Using Homebrew (Recommended)
```bash
# Install Homebrew if not installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.11
brew install python@3.11

# Verify installation
python3.11 --version  # Should show Python 3.11.x

# Make it default (optional)
echo 'alias python3=python3.11' >> ~/.zshrc
source ~/.zshrc
```

#### Option B: Using pyenv (Alternative)
```bash
# Install pyenv
brew install pyenv

# Install Python 3.11
pyenv install 3.11.7

# Set as global default
pyenv global 3.11.7

# Add to shell
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init --path)"' >> ~/.zshrc
source ~/.zshrc

# Verify
python3 --version  # Should show Python 3.11.7
```

### 2. Install Poetry (Python Package Manager)
```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3.11 -

# Add to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Verify
poetry --version
```

### 3. Install Docker Desktop
```bash
# Download and install from:
# https://www.docker.com/products/docker-desktop/

# Or using Homebrew:
brew install --cask docker

# Start Docker Desktop app
open /Applications/Docker.app

# Verify
docker --version
docker ps
```

### 4. Install Node.js 18+ (for frontend)
```bash
# Install Node.js 18 LTS
brew install node@18

# Verify
node --version  # Should be 18.x or higher
npm --version
```

---

## 🎯 Cursor IDE Usage (NOT CLI)

Since you're using Cursor IDE, you **don't need the Claude CLI**. Instead, use Cursor's built-in AI chat.

### How to Use Multiple Claude "Agents" in Cursor

#### Method 1: Multiple Chat Tabs (Recommended)
1. **Open Cursor IDE**
2. **Open multiple Composer windows** (Cmd+I or Cmd+Shift+I)
3. Each Composer acts as an independent "agent"
4. Give each one its specific instructions

**Example:**
- **Composer Tab 1**: Phase 1 (Foundation)
- **Composer Tab 2**: Agent 2A (Info Collection)
- **Composer Tab 3**: Agent 2B (Novelty Analyzer)
- **Composer Tab 4**: Agent 2C (Gap Map Scrapers)
- **Composer Tab 5**: Agent 2D (Pivot Matcher)
- **Composer Tab 6**: Frontend Agent

#### Method 2: Sequential Execution
If multiple tabs are confusing, do phases sequentially:
1. Complete Phase 1 in one chat
2. Start new chat for Phase 2 (backend services)
3. Start new chat for Phase 3 (frontend)
4. Integrate in Phase 4

**Trade-off:** Slower (no parallelization), but simpler.

---

## 📝 Updated Build Instructions for Cursor IDE

### Pre-Flight Checklist
```bash
# 1. Verify Python 3.11+
python3 --version
# Expected: Python 3.11.x or higher

# 2. Verify Poetry
poetry --version

# 3. Verify Docker
docker --version
docker ps

# 4. Verify Node.js
node --version  # Should be 18.x+

# 5. Start Docker services
cd /Users/amit/Coding-Projects/Project-Suggester
docker-compose up -d

# 6. Verify databases are running
docker ps | grep postgres
docker ps | grep redis
```

---

## 🚀 Build Execution in Cursor IDE

### Step 1: Phase 1 - Foundation (10 minutes)

**Open Cursor Composer (Cmd+I)** and give this instruction:

```
You are building the Research Pivot Advisor System using Cursor IDE.

ENVIRONMENT:
- Python: 3.11+ (use python3.11 command)
- IDE: Cursor
- Working directory: /Users/amit/Coding-Projects/Project-Suggester

START PHASE 1: Foundation

Read docs/IMPLEMENTATION_PRIORITIES.md and complete Phase 1 tasks:

1. Create directory structure for backend and frontend
2. Create app/models/schemas.py with ALL Pydantic models
3. Create app/models/gap_map_models.py with SQLAlchemy models
4. Create pyproject.toml using Poetry (specify python = "^3.11")
5. Create app/config.py with Pydantic settings
6. Create docker-compose.yml (already exists, verify it's correct)

IMPORTANT:
- Use python3.11 in all scripts
- Use poetry for Python dependency management
- Update docs/BUILD_STATUS.md after each task

When Phase 1 is complete, tell me "PHASE 1 COMPLETE".
```

### Step 2: Phase 2 - Backend Services (20 minutes)

**Option A: Multiple Composer Tabs (Parallel)**

Open 4 new Composer tabs and give each one its agent instruction:

**Tab 2 - Agent 2A:**
```
You are Agent 2A: Information Collection Service.

ENVIRONMENT: Python 3.11+, use python3.11 command

Read docs/IMPLEMENTATION_PRIORITIES.md "Agent 2A" section.

Create:
- app/services/document_parser.py
- app/services/info_collector.py
- tests/test_info_collector.py

Update docs/BUILD_STATUS.md when done.
Say "AGENT 2A COMPLETE" when finished.
```

**Tab 3 - Agent 2B:**
```
You are Agent 2B: Novelty & Impact Analyzer.

ENVIRONMENT: Python 3.11+, use python3.11 command

Read docs/IMPLEMENTATION_PRIORITIES.md "Agent 2B" section.

Create:
- app/services/openalex_client.py
- app/services/novelty_analyzer.py
- tests/test_novelty_analyzer.py

Update docs/BUILD_STATUS.md when done.
Say "AGENT 2B COMPLETE" when finished.
```

**Tab 4 - Agent 2C:**
```
You are Agent 2C: Gap Map Database & Scrapers.

ENVIRONMENT: Python 3.11+, use python3.11 command

Read docs/IMPLEMENTATION_PRIORITIES.md "Agent 2C" section.
Read docs/OXYLABS_INTEGRATION.md for Oxylabs usage.

Create all scraper files and database repository.

For MVP: Use hardcoded sample data in scrapers (3-5 entries per source).

Update docs/BUILD_STATUS.md when done.
Say "AGENT 2C COMPLETE" when finished.
```

**Tab 5 - Agent 2D:**
```
You are Agent 2D: Pivot Matcher & Report Generator.

ENVIRONMENT: Python 3.11+, use python3.11 command

Read docs/IMPLEMENTATION_PRIORITIES.md "Agent 2D" section.

Create:
- app/services/pivot_matcher.py
- app/services/report_generator.py
- tests/test_pivot_matcher.py

Update docs/BUILD_STATUS.md when done.
Say "AGENT 2D COMPLETE" when finished.
```

**Option B: Sequential (Simpler)**

Do them one at a time in the same Composer tab. Slower but less context switching.

### Step 3: Phase 3 - Frontend (15 minutes)

**Open new Composer tab for frontend:**

```
You are building the React frontend for Research Pivot Advisor.

ENVIRONMENT: Node.js 18+, Vite, React, TypeScript

Read docs/IMPLEMENTATION_PRIORITIES.md Phase 3 section.

Tasks:
1. Initialize Vite + React + TypeScript project
2. Install Shadcn UI
3. Create chat-interface.tsx and file-upload.tsx
4. Create results-view.tsx and API client
5. Create TypeScript types from backend schemas

Update docs/BUILD_STATUS.md when done.
```

### Step 4: Phase 4 - Integration (10 minutes)

```
All Phase 2 and 3 work is complete. Now integrate everything.

Read docs/IMPLEMENTATION_PRIORITIES.md Phase 4 section.

Tasks:
1. Create app/api/routes.py with all endpoints
2. Create app/main.py with FastAPI app
3. Initialize Alembic and create migration
4. Wire up all services

Use python3.11 for all Python commands.

Update docs/BUILD_STATUS.md when done.
```

### Step 5: Phase 5 - Testing (5 minutes)

```
Test the complete application end-to-end.

Start backend:
cd research-advisor-backend
poetry install
poetry run alembic upgrade head
poetry run uvicorn app.main:app --reload

Start frontend (in another terminal):
cd research-advisor-frontend
npm install
npm run dev

Test the flow manually in browser.
Update docs/BUILD_STATUS.md with final status.
```

---

## 💡 Tips for Cursor IDE

### Using Composer Effectively
1. **Cmd+I**: Open Composer (inline editing)
2. **Cmd+Shift+I**: Open Composer sidebar
3. **@-mentions**: Reference files with `@filename`
4. **Agent context**: Each Composer maintains its own context

### Managing Multiple Tasks
- **Use Composer tabs** for parallel work
- **Pin important files** in sidebar for quick access
- **Use split view** to see multiple files
- **Terminal tabs** for running services

### Keeping Context
Each Composer can:
- Read files with `@filename`
- Remember previous messages in that tab
- Execute terminal commands
- Create/edit files

---

## 🔍 Verification Commands

### Check Python Setup
```bash
which python3.11
python3.11 --version
python3.11 -m pip --version
```

### Check Poetry Setup
```bash
poetry --version
poetry env info  # After poetry install
```

### Check Docker
```bash
docker --version
docker-compose --version
docker ps
```

### Check Node.js
```bash
node --version
npm --version
```

---

## 🆘 Troubleshooting

### Python 3.11 Not Found
```bash
# Install via Homebrew
brew install python@3.11

# Add to PATH
export PATH="/opt/homebrew/opt/python@3.11/bin:$PATH"

# Or create symlink
ln -s /opt/homebrew/bin/python3.11 /usr/local/bin/python3.11
```

### Poetry Not Found
```bash
# Reinstall Poetry
curl -sSL https://install.python-poetry.org | python3.11 -

# Add to PATH
export PATH="$HOME/.local/bin:$PATH"
```

### Docker Not Running
```bash
# Start Docker Desktop
open /Applications/Docker.app

# Wait for Docker to start
sleep 10

# Verify
docker ps
```

### Port Already in Use
```bash
# Check what's using port 8000 (backend)
lsof -i :8000
kill -9 <PID>

# Check what's using port 5173 (frontend)
lsof -i :5173
kill -9 <PID>
```

---

## 📊 Expected Timeline (Cursor IDE)

| Phase | Time | Method | Notes |
|-------|------|--------|-------|
| Setup | 15 min | Manual | Install Python 3.11, Poetry, Docker |
| Phase 1 | 10 min | 1 Composer | Foundation (schemas, config) |
| Phase 2 | 30 min | 4 Composers or 1 sequential | Backend services |
| Phase 3 | 20 min | 1 Composer | Frontend |
| Phase 4 | 10 min | 1 Composer | Integration |
| Phase 5 | 10 min | 1 Composer | Testing |

**Total:** ~95 minutes (including setup)

Without parallelization: ~120 minutes

---

## ✅ Ready to Start

After running the setup commands above, you'll have:
- ✅ Python 3.11+
- ✅ Poetry for Python packages
- ✅ Docker Desktop running
- ✅ Node.js 18+ for frontend
- ✅ PostgreSQL and Redis containers running

Then follow the build instructions in this document!
