# Testing Quick Reference

## Quick Commands

### Validate Phase 1
```bash
./validate_phase1.sh
```

### Validate Individual Agent
```bash
./validate_agent.sh 2A  # Info Collection
./validate_agent.sh 2B  # Novelty Analyzer
./validate_agent.sh 2C  # Gap Map System
./validate_agent.sh 2D  # Pivot Matcher
./validate_agent.sh 3A  # Frontend Chat
./validate_agent.sh 3B  # Frontend Results
```

### Run All Tests
```bash
./run_all_tests.sh
```

### Backend Tests Only
```bash
cd research-advisor-backend
poetry run pytest tests/ -v
```

### Frontend Tests Only
```bash
cd research-advisor-frontend
npm test
```

### With Coverage
```bash
# Backend
cd research-advisor-backend
poetry run pytest --cov=app --cov-report=html
open htmlcov/index.html

# Frontend
cd research-advisor-frontend
npm test -- --coverage
```

---

## Testing Checklist by Phase

### ✅ Phase 1: Foundation
- [ ] Run `./validate_phase1.sh`
- [ ] All directories exist
- [ ] All Python files have valid syntax
- [ ] Poetry config is valid
- [ ] No import errors

### ✅ Phase 2: Backend Services

**Agent 2A:**
- [ ] Create `tests/test_info_collector.py`
- [ ] Create `tests/test_document_parser.py`
- [ ] Run `./validate_agent.sh 2A`
- [ ] All tests pass
- [ ] Coverage >80%

**Agent 2B:**
- [ ] Create `tests/test_openalex_client.py`
- [ ] Create `tests/test_novelty_analyzer.py`
- [ ] Run `./validate_agent.sh 2B`
- [ ] All tests pass
- [ ] Coverage >80%

**Agent 2C:**
- [ ] Create `tests/test_gap_map_repository.py`
- [ ] Create `tests/test_scrapers.py`
- [ ] Run `./validate_agent.sh 2C`
- [ ] All tests pass
- [ ] Coverage >80%

**Agent 2D:**
- [ ] Create `tests/test_pivot_matcher.py`
- [ ] Create `tests/test_report_generator.py`
- [ ] Run `./validate_agent.sh 2D`
- [ ] All tests pass
- [ ] Coverage >80%

### ✅ Phase 3: Frontend

**Agent 3A:**
- [ ] Create `src/components/chat-interface.test.tsx`
- [ ] Create `src/components/file-upload.test.tsx`
- [ ] Run `./validate_agent.sh 3A`
- [ ] All tests pass
- [ ] Coverage >70%

**Agent 3B:**
- [ ] Create `src/components/results-view.test.tsx`
- [ ] Create `src/api/client.test.ts`
- [ ] Run `./validate_agent.sh 3B`
- [ ] All tests pass
- [ ] Coverage >70%

### ✅ Phase 4: Integration
- [ ] Create `tests/integration/test_api_endpoints.py`
- [ ] Create `tests/integration/test_full_flow.py`
- [ ] All API endpoints respond correctly
- [ ] Full flow works: input → analysis → results

### ✅ Phase 5: End-to-End
- [ ] Manual testing checklist complete
- [ ] Run `./run_all_tests.sh`
- [ ] All tests pass
- [ ] Application runs without errors

---

## Test Failure Protocol

If any test fails:

1. **❌ DO NOT mark agent as COMPLETE**
2. **📝 Document failure in docs/BUILD_STATUS.md**
3. **🔧 Fix the issue**
4. **🔄 Re-run tests: `./validate_agent.sh <agent>`**
5. **✅ Only mark COMPLETE when tests pass**

---

## Coverage Goals

| Component | Target | Command |
|-----------|--------|---------|
| Backend Unit Tests | >80% | `cd research-advisor-backend && poetry run pytest --cov=app` |
| Frontend Components | >70% | `cd research-advisor-frontend && npm test -- --coverage` |
| Integration Tests | 100% of endpoints | `poetry run pytest tests/integration/` |
| Critical Paths | 100% | Focus: auth, sessions, API calls |

---

## Quick Test Writing Templates

### Backend Unit Test Template

```python
# tests/test_example.py
import pytest
from app.services.example import ExampleService

@pytest.mark.asyncio
async def test_example_service():
    """Test example service functionality."""
    service = ExampleService()
    result = await service.do_something()

    assert result is not None
    assert result.status == "success"

@pytest.mark.asyncio
async def test_example_service_error_handling():
    """Test error handling."""
    service = ExampleService()

    with pytest.raises(ValueError):
        await service.do_something_invalid()
```

### Frontend Component Test Template

```typescript
// src/components/example.test.tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import ExampleComponent from './example'

describe('ExampleComponent', () => {
  it('renders without crashing', () => {
    render(<ExampleComponent />)
    expect(screen.getByText('Example')).toBeInTheDocument()
  })

  it('handles user interaction', () => {
    render(<ExampleComponent />)
    const button = screen.getByRole('button')

    fireEvent.click(button)

    expect(screen.getByText('Clicked')).toBeInTheDocument()
  })
})
```

---

## Continuous Validation

### After Each Agent Completes:
```bash
# Validate specific agent
./validate_agent.sh 2A

# Run all tests to ensure no regressions
./run_all_tests.sh
```

### Before Phase Transition:
```bash
# Phase 1 → Phase 2
./validate_phase1.sh

# Phase 2 → Phase 4
./run_all_tests.sh  # Ensure all backend tests pass

# Phase 4 → Phase 5
./run_all_tests.sh  # Full suite
```

---

## Debugging Failed Tests

### Backend Test Failures
```bash
# Run with verbose output
cd research-advisor-backend
poetry run pytest tests/test_failing.py -vv

# Run with print statements visible
poetry run pytest tests/test_failing.py -s

# Run specific test function
poetry run pytest tests/test_failing.py::test_specific_function -vv

# Debug with pdb
poetry run pytest tests/test_failing.py --pdb
```

### Frontend Test Failures
```bash
# Run with verbose output
cd research-advisor-frontend
npm test -- --run --reporter=verbose

# Run specific test file
npm test -- --run src/components/failing.test.tsx

# Run in watch mode
npm test
```

---

## Test Data & Mocking

### Mock OpenAI Responses
```python
# tests/conftest.py
@pytest.fixture
def mock_openai(mocker):
    return mocker.patch('openai.ChatCompletion.create', return_value={
        'choices': [{'message': {'content': 'mocked response'}}]
    })
```

### Mock OpenAlex Responses
```python
@pytest.fixture
def mock_openalex(mocker):
    return mocker.patch('pyalex.Works.search', return_value={
        'results': [{
            'id': 'W123',
            'fwci': 2.5,
            'title': 'Test Paper'
        }]
    })
```

### Mock File Uploads (Frontend)
```typescript
const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' })
const input = screen.getByLabelText('Upload File')
fireEvent.change(input, { target: { files: [file] } })
```

---

## CI/CD Integration (Future)

```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run backend tests
        run: |
          cd research-advisor-backend
          poetry install
          poetry run pytest --cov=app

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run frontend tests
        run: |
          cd research-advisor-frontend
          npm install
          npm test
```

---

## Summary

**Key Principle:** No agent marks work as COMPLETE until tests pass.

**Validation Flow:**
1. Agent creates tests
2. Agent implements code
3. Agent runs `./validate_agent.sh <agent>`
4. If pass → Mark COMPLETE
5. If fail → Fix and repeat step 3

**Use these scripts religiously to ensure quality!** 🧪✅
