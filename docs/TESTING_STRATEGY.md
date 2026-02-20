# Testing Strategy - Research Pivot Advisor System

## Overview

Every component must be tested as it's built. No agent marks their work "COMPLETE" until tests pass.

---

## Testing Requirements by Phase

### Phase 1: Foundation
**Validation (Not Unit Tests):**
- ✅ All directories exist
- ✅ All schema files have valid Python syntax
- ✅ Pydantic models validate correctly
- ✅ SQLAlchemy models have correct relationships
- ✅ pyproject.toml is valid Poetry format
- ✅ config.py loads environment variables

**Validation Script:**
```bash
# Run after Phase 1
python3.11 -m py_compile research-advisor-backend/app/models/schemas.py
python3.11 -m py_compile research-advisor-backend/app/models/gap_map_models.py
python3.11 -m py_compile research-advisor-backend/app/config.py
cd research-advisor-backend && poetry check
```

### Phase 2: Backend Services

Each agent must create:
1. **Implementation files** (service code)
2. **Unit tests** (pytest files)
3. **Run tests** before marking complete

#### Agent 2A: Info Collection Service

**Files:**
- `app/services/document_parser.py`
- `app/services/info_collector.py`
- `tests/test_info_collector.py` ← **Required**
- `tests/test_document_parser.py` ← **Required**

**Test Coverage:**
- ✅ PDF parsing works
- ✅ DOCX parsing works
- ✅ TXT parsing works
- ✅ LLM extraction returns valid ResearchProfile
- ✅ Handles empty files gracefully
- ✅ Handles invalid formats gracefully

**Mock External APIs:**
- Mock OpenAI responses
- Use sample PDFs/DOCX for testing

**Run Tests:**
```bash
cd research-advisor-backend
poetry run pytest tests/test_info_collector.py -v
poetry run pytest tests/test_document_parser.py -v
```

#### Agent 2B: Novelty Analyzer

**Files:**
- `app/services/openalex_client.py`
- `app/services/novelty_analyzer.py`
- `tests/test_openalex_client.py` ← **Required**
- `tests/test_novelty_analyzer.py` ← **Required**

**Test Coverage:**
- ✅ OpenAlex API query works
- ✅ FWCI extraction is correct
- ✅ Handles None values for FWCI
- ✅ Novelty verdict logic is correct (SOLVED/MARGINAL/NOVEL)
- ✅ Impact assessment based on FWCI thresholds
- ✅ Returns UNCERTAIN on API failures

**Mock External APIs:**
- Mock OpenAlex responses with sample papers
- Test with various FWCI values (high, medium, low, None)

**Run Tests:**
```bash
cd research-advisor-backend
poetry run pytest tests/test_openalex_client.py -v
poetry run pytest tests/test_novelty_analyzer.py -v
```

#### Agent 2C: Gap Map System

**Files:**
- `app/services/gap_map_repository.py`
- `app/services/scrapers/*.py`
- `app/services/gap_map_scraper.py`
- `app/jobs/gap_map_scraper_job.py`
- `tests/test_gap_map_repository.py` ← **Required**
- `tests/test_scrapers.py` ← **Required**

**Test Coverage:**
- ✅ Database upsert works (update existing, insert new)
- ✅ Query methods work (get_all, get_by_category, get_by_source)
- ✅ Scrapers return valid GapMapEntry objects
- ✅ Sample data has correct structure
- ✅ Background job scheduler initializes

**Use Test Database:**
```python
# tests/conftest.py
@pytest.fixture
def test_db():
    """Use separate test database."""
    engine = create_async_engine(
        "postgresql+asyncpg://postgres:postgres@localhost:5432/research_advisor_test"
    )
    # Setup and teardown
```

**Run Tests:**
```bash
cd research-advisor-backend
poetry run pytest tests/test_gap_map_repository.py -v
poetry run pytest tests/test_scrapers.py -v
```

#### Agent 2D: Pivot Matcher & Report Generator

**Files:**
- `app/services/pivot_matcher.py`
- `app/services/report_generator.py`
- `tests/test_pivot_matcher.py` ← **Required**
- `tests/test_report_generator.py` ← **Required**

**Test Coverage:**
- ✅ Matching algorithm works
- ✅ Ranking by relevance × impact
- ✅ Returns top N suggestions
- ✅ Report generation includes all sections
- ✅ Recommendation logic (CONTINUE/PIVOT/UNCERTAIN) is correct
- ✅ Citations are properly formatted

**Mock External APIs:**
- Mock LLM responses for matching
- Use sample gap map entries

**Run Tests:**
```bash
cd research-advisor-backend
poetry run pytest tests/test_pivot_matcher.py -v
poetry run pytest tests/test_report_generator.py -v
```

### Phase 3: Frontend

#### Agent 3A: Chat Interface

**Files:**
- `src/components/chat-interface.tsx`
- `src/components/file-upload.tsx`
- `src/components/chat-interface.test.tsx` ← **Required**
- `src/components/file-upload.test.tsx` ← **Required**

**Test Coverage:**
- ✅ Component renders without crashing
- ✅ User can type message
- ✅ Send button works
- ✅ File upload accepts valid files
- ✅ File upload rejects invalid files
- ✅ Loading state displays

**Testing Library:**
```bash
npm install --save-dev @testing-library/react @testing-library/jest-dom vitest
```

**Run Tests:**
```bash
cd research-advisor-frontend
npm test
```

#### Agent 3B: Results View

**Files:**
- `src/components/results-view.tsx`
- `src/api/client.ts`
- `src/hooks/useAnalysis.ts`
- `src/components/results-view.test.tsx` ← **Required**
- `src/api/client.test.ts` ← **Required**

**Test Coverage:**
- ✅ Results display correctly
- ✅ API client calls correct endpoints
- ✅ TanStack Query hooks work
- ✅ Error states display properly
- ✅ Loading states display properly

**Run Tests:**
```bash
cd research-advisor-frontend
npm test
```

### Phase 4: Integration

**Integration Tests:**
- `tests/integration/test_api_endpoints.py` ← **Required**
- `tests/integration/test_full_flow.py` ← **Required**

**Test Coverage:**
- ✅ All API endpoints respond correctly
- ✅ POST /api/v1/analyze works
- ✅ GET /api/v1/analysis/{session_id} works
- ✅ Redis session storage works
- ✅ Database queries work
- ✅ Full flow: input → analysis → results

**Run Tests:**
```bash
cd research-advisor-backend
poetry run pytest tests/integration/ -v
```

### Phase 5: End-to-End

**Manual Testing Checklist:**
- [ ] Backend starts without errors
- [ ] Frontend starts without errors
- [ ] User can input research question via chat
- [ ] User can upload PDF file
- [ ] System calls OpenAlex API
- [ ] System displays novelty assessment
- [ ] System displays FWCI metrics
- [ ] System shows CONTINUE or PIVOT recommendation
- [ ] System displays pivot suggestions (if applicable)
- [ ] Citations are properly formatted
- [ ] Session expires after TTL

---

## Test Configuration Files

### Backend: pytest.ini

```ini
# research-advisor-backend/pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --strict-markers
    --tb=short
    --cov=app
    --cov-report=term-missing
    --cov-report=html

markers =
    unit: Unit tests (mock external dependencies)
    integration: Integration tests (use test database)
    slow: Slow tests (skip with -m "not slow")

asyncio_mode = auto
```

### Backend: conftest.py

```python
# research-advisor-backend/tests/conftest.py
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.gap_map_models import Base

# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/research_advisor_test"

@pytest_asyncio.fixture
async def test_db_engine():
    """Create test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables after tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()

@pytest_asyncio.fixture
async def test_db_session(test_db_engine):
    """Create test database session."""
    async_session = sessionmaker(
        test_db_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session

@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response."""
    return {
        "choices": [{
            "message": {
                "content": '{"research_question": "Test question", "skills": ["Python"], "motivations": ["Impact"]}'
            }
        }]
    }

@pytest.fixture
def mock_openalex_response():
    """Mock OpenAlex API response."""
    return {
        "results": [{
            "id": "W123",
            "title": "Test Paper",
            "doi": "10.1234/test",
            "fwci": 2.5,
            "citation_normalized_percentile": {"value": 0.85},
            "cited_by_percentile_year": {"min": 80, "max": 95}
        }]
    }
```

### Frontend: vitest.config.ts

```typescript
// research-advisor-frontend/vitest.config.ts
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],
      exclude: [
        'node_modules/',
        'src/test/',
      ]
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
```

---

## Validation Scripts

### validate_phase1.sh

```bash
#!/bin/bash
# Validate Phase 1 completion

echo "🧪 Validating Phase 1: Foundation"
echo ""

ERRORS=0

# Check directory structure
echo "📁 Checking directory structure..."
DIRS=(
    "research-advisor-backend/app"
    "research-advisor-backend/app/models"
    "research-advisor-backend/app/services"
    "research-advisor-backend/app/api"
    "research-advisor-backend/app/jobs"
    "research-advisor-backend/tests"
    "research-advisor-frontend/src"
)

for dir in "${DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "  ✅ $dir"
    else
        echo "  ❌ Missing: $dir"
        ERRORS=$((ERRORS + 1))
    fi
done

# Check critical files
echo ""
echo "📄 Checking critical files..."
FILES=(
    "research-advisor-backend/app/models/schemas.py"
    "research-advisor-backend/app/models/gap_map_models.py"
    "research-advisor-backend/app/config.py"
    "research-advisor-backend/pyproject.toml"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ Missing: $file"
        ERRORS=$((ERRORS + 1))
    fi
done

# Validate Python syntax
echo ""
echo "🐍 Validating Python syntax..."
cd research-advisor-backend
python3.11 -m py_compile app/models/schemas.py && echo "  ✅ schemas.py syntax valid" || { echo "  ❌ schemas.py syntax error"; ERRORS=$((ERRORS + 1)); }
python3.11 -m py_compile app/models/gap_map_models.py && echo "  ✅ gap_map_models.py syntax valid" || { echo "  ❌ gap_map_models.py syntax error"; ERRORS=$((ERRORS + 1)); }
python3.11 -m py_compile app/config.py && echo "  ✅ config.py syntax valid" || { echo "  ❌ config.py syntax error"; ERRORS=$((ERRORS + 1)); }

# Validate Poetry config
echo ""
echo "📦 Validating Poetry configuration..."
poetry check && echo "  ✅ pyproject.toml valid" || { echo "  ❌ pyproject.toml invalid"; ERRORS=$((ERRORS + 1)); }

cd ..

# Summary
echo ""
echo "================================"
if [ $ERRORS -eq 0 ]; then
    echo "✅ Phase 1 validation PASSED"
    exit 0
else
    echo "❌ Phase 1 validation FAILED ($ERRORS errors)"
    exit 1
fi
```

### validate_agent.sh

```bash
#!/bin/bash
# Validate agent completion with tests

AGENT=$1

if [ -z "$AGENT" ]; then
    echo "Usage: ./validate_agent.sh <agent_name>"
    echo "Example: ./validate_agent.sh 2A"
    exit 1
fi

echo "🧪 Validating Agent $AGENT"
echo ""

cd research-advisor-backend

case $AGENT in
    2A)
        echo "Testing Info Collection Service..."
        poetry run pytest tests/test_info_collector.py tests/test_document_parser.py -v
        ;;
    2B)
        echo "Testing Novelty Analyzer..."
        poetry run pytest tests/test_openalex_client.py tests/test_novelty_analyzer.py -v
        ;;
    2C)
        echo "Testing Gap Map System..."
        poetry run pytest tests/test_gap_map_repository.py tests/test_scrapers.py -v
        ;;
    2D)
        echo "Testing Pivot Matcher & Report Generator..."
        poetry run pytest tests/test_pivot_matcher.py tests/test_report_generator.py -v
        ;;
    3A|3B)
        echo "Testing Frontend..."
        cd ../research-advisor-frontend
        npm test
        ;;
    *)
        echo "Unknown agent: $AGENT"
        exit 1
        ;;
esac

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "✅ Agent $AGENT validation PASSED"
else
    echo ""
    echo "❌ Agent $AGENT validation FAILED"
fi

exit $EXIT_CODE
```

### run_all_tests.sh

```bash
#!/bin/bash
# Run all tests

echo "🧪 Running all tests..."
echo ""

ERRORS=0

# Backend unit tests
echo "📊 Backend unit tests..."
cd research-advisor-backend
poetry run pytest tests/ -v --cov=app --cov-report=term-missing
if [ $? -ne 0 ]; then
    ERRORS=$((ERRORS + 1))
fi

cd ..

# Frontend tests
echo ""
echo "📊 Frontend tests..."
cd research-advisor-frontend
npm test
if [ $? -ne 0 ]; then
    ERRORS=$((ERRORS + 1))
fi

cd ..

# Summary
echo ""
echo "================================"
if [ $ERRORS -eq 0 ]; then
    echo "✅ All tests PASSED"
    exit 0
else
    echo "❌ Some tests FAILED"
    exit 1
fi
```

---

## Agent Instructions Update

### Each Agent Must:

1. **Write tests FIRST** (TDD approach)
2. **Implement code** to pass tests
3. **Run tests** before marking complete
4. **Update BUILD_STATUS.md** with test results

### Example Agent Instruction Template:

```
You are Agent 2A: Information Collection Service.

TESTING REQUIREMENTS:
- Create tests BEFORE implementation
- Mock all external APIs (OpenAI, file I/O)
- Achieve >80% code coverage
- All tests must pass before marking COMPLETE

Tasks:
1. Create tests/test_document_parser.py (mock file reading)
2. Create tests/test_info_collector.py (mock OpenAI)
3. Create app/services/document_parser.py
4. Create app/services/info_collector.py
5. Run: poetry run pytest tests/test_info_collector.py -v
6. Fix any failures
7. Update docs/BUILD_STATUS.md with test results

Say "AGENT 2A COMPLETE - ALL TESTS PASSING" when done.
```

---

## Coverage Goals

### Backend
- **Unit Tests:** >80% coverage
- **Integration Tests:** All API endpoints
- **Critical Paths:** 100% coverage (auth, session management)

### Frontend
- **Component Tests:** >70% coverage
- **Integration Tests:** All user flows
- **Critical Paths:** 100% coverage (API calls, error handling)

---

## Continuous Validation

### After Each Agent Completes:

```bash
# Validate agent work
./validate_agent.sh 2A

# Run all tests so far
cd research-advisor-backend
poetry run pytest tests/ -v
```

### Before Marking Phase Complete:

```bash
# Run full test suite
./run_all_tests.sh

# Check coverage
cd research-advisor-backend
poetry run pytest --cov=app --cov-report=html
open htmlcov/index.html
```

---

## Test Failure Protocol

If tests fail:
1. **Don't mark agent as COMPLETE**
2. **Document failure in BUILD_STATUS.md**
3. **Fix the issue**
4. **Re-run tests**
5. **Only then mark COMPLETE**

**No exceptions.** Tests must pass before proceeding.
