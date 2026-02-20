#!/bin/bash
# Run all tests for the entire project

echo "🧪 Running all tests for Research Pivot Advisor System"
echo ""

ERRORS=0

# Backend unit tests
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Backend Unit Tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ -d "research-advisor-backend/tests" ]; then
    cd research-advisor-backend
    poetry run pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=html
    BACKEND_EXIT=$?

    if [ $BACKEND_EXIT -ne 0 ]; then
        echo ""
        echo "❌ Backend tests failed"
        ERRORS=$((ERRORS + 1))
    else
        echo ""
        echo "✅ Backend tests passed"
        echo "Coverage report: research-advisor-backend/htmlcov/index.html"
    fi

    cd ..
else
    echo "⚠️  Backend tests directory not found (skip for Phase 1)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Frontend Tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ -d "research-advisor-frontend/src" ]; then
    cd research-advisor-frontend

    # Check if package.json has test script
    if [ -f "package.json" ] && grep -q '"test"' package.json; then
        npm test -- --run
        FRONTEND_EXIT=$?

        if [ $FRONTEND_EXIT -ne 0 ]; then
            echo ""
            echo "❌ Frontend tests failed"
            ERRORS=$((ERRORS + 1))
        else
            echo ""
            echo "✅ Frontend tests passed"
        fi
    else
        echo "⚠️  Frontend tests not configured yet (skip for Phase 2)"
    fi

    cd ..
else
    echo "⚠️  Frontend directory not found (skip for Phase 2)"
fi

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Test Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $ERRORS -eq 0 ]; then
    echo "✅ All tests PASSED"
    echo ""
    echo "Coverage reports:"
    echo "  Backend:  research-advisor-backend/htmlcov/index.html"
    echo "  Frontend: research-advisor-frontend/coverage/index.html"
    exit 0
else
    echo "❌ $ERRORS test suite(s) FAILED"
    echo ""
    echo "Review failures above and fix before proceeding"
    exit 1
fi
