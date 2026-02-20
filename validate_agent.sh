#!/bin/bash
# Validate agent completion with tests

AGENT=$1

if [ -z "$AGENT" ]; then
    echo "Usage: ./validate_agent.sh <agent_name>"
    echo "Example: ./validate_agent.sh 2A"
    echo ""
    echo "Available agents:"
    echo "  2A - Info Collection Service"
    echo "  2B - Novelty Analyzer"
    echo "  2C - Gap Map System"
    echo "  2D - Pivot Matcher & Report Generator"
    echo "  3A - Frontend Chat Interface"
    echo "  3B - Frontend Results View"
    exit 1
fi

echo "🧪 Validating Agent $AGENT"
echo ""

case $AGENT in
    2A)
        echo "Testing Info Collection Service..."
        cd research-advisor-backend
        poetry run pytest tests/test_info_collector.py tests/test_document_parser.py -v --tb=short
        ;;
    2B)
        echo "Testing Novelty Analyzer..."
        cd research-advisor-backend
        poetry run pytest tests/test_openalex_client.py tests/test_novelty_analyzer.py -v --tb=short
        ;;
    2C)
        echo "Testing Gap Map System..."
        cd research-advisor-backend
        poetry run pytest tests/test_gap_map_repository.py tests/test_scrapers.py -v --tb=short
        ;;
    2D)
        echo "Testing Pivot Matcher & Report Generator..."
        cd research-advisor-backend
        poetry run pytest tests/test_pivot_matcher.py tests/test_report_generator.py -v --tb=short
        ;;
    3A)
        echo "Testing Frontend Chat Interface..."
        cd research-advisor-frontend
        npm test -- --run src/components/chat-interface.test.tsx src/components/file-upload.test.tsx
        ;;
    3B)
        echo "Testing Frontend Results View..."
        cd research-advisor-frontend
        npm test -- --run src/components/results-view.test.tsx src/api/client.test.ts
        ;;
    *)
        echo "❌ Unknown agent: $AGENT"
        echo "Valid agents: 2A, 2B, 2C, 2D, 3A, 3B"
        exit 1
        ;;
esac

EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Agent $AGENT validation PASSED"
    echo "Agent $AGENT can be marked as COMPLETE"
else
    echo "❌ Agent $AGENT validation FAILED"
    echo "Fix test failures before marking Agent $AGENT as COMPLETE"
fi

exit $EXIT_CODE
