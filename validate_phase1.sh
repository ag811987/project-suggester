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
if [ -f "research-advisor-backend/app/models/schemas.py" ]; then
    cd research-advisor-backend
    python3.11 -m py_compile app/models/schemas.py && echo "  ✅ schemas.py syntax valid" || { echo "  ❌ schemas.py syntax error"; ERRORS=$((ERRORS + 1)); }
    python3.11 -m py_compile app/models/gap_map_models.py && echo "  ✅ gap_map_models.py syntax valid" || { echo "  ❌ gap_map_models.py syntax error"; ERRORS=$((ERRORS + 1)); }
    python3.11 -m py_compile app/config.py && echo "  ✅ config.py syntax valid" || { echo "  ❌ config.py syntax error"; ERRORS=$((ERRORS + 1)); }

    # Validate Poetry config
    echo ""
    echo "📦 Validating Poetry configuration..."
    # Try poetry in PATH first, then try full path
    if command -v poetry &> /dev/null; then
        if poetry check 2>&1 | grep -q "^Error:"; then
            echo "  ❌ pyproject.toml has errors"
            ERRORS=$((ERRORS + 1))
        else
            echo "  ✅ pyproject.toml valid (warnings OK)"
        fi
    elif [ -f "$HOME/.local/bin/poetry" ]; then
        if $HOME/.local/bin/poetry check 2>&1 | grep -q "^Error:"; then
            echo "  ❌ pyproject.toml has errors"
            ERRORS=$((ERRORS + 1))
        else
            echo "  ✅ pyproject.toml valid (warnings OK)"
        fi
    else
        echo "  ⚠️  Poetry not found, skipping validation"
    fi

    cd ..
fi

# Summary
echo ""
echo "================================"
if [ $ERRORS -eq 0 ]; then
    echo "✅ Phase 1 validation PASSED"
    echo ""
    echo "Next step: Run Phase 2 with parallel agents"
    exit 0
else
    echo "❌ Phase 1 validation FAILED ($ERRORS errors)"
    echo ""
    echo "Please fix errors before proceeding to Phase 2"
    exit 1
fi
