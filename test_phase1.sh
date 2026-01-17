#!/bin/bash
# Phase 1 Testing Script
# Tests all Phase 1 changes to ensure they work correctly

set -e  # Exit on error

echo "🧪 Phase 1 Testing Script"
echo "========================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

pass() {
    echo -e "${GREEN}✓${NC} $1"
}

fail() {
    echo -e "${RED}✗${NC} $1"
}

warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Test 1: Check design tokens exist
echo "Test 1: Design Tokens"
echo "---------------------"
if [ -f "frontend/src/styles/tokens/colors.css" ] && \
   [ -f "frontend/src/styles/tokens/spacing.css" ] && \
   [ -f "frontend/src/styles/tokens/typography.css" ] && \
   [ -f "frontend/src/styles/tokens/breakpoints.css" ]; then
    pass "All token files exist"
else
    fail "Missing token files"
fi

# Check theme.css imports tokens
if grep -q "tokens/colors.css" frontend/src/styles/theme.css; then
    pass "theme.css imports tokens"
else
    fail "theme.css doesn't import tokens"
fi

# Check MainPage.css uses tokens
if grep -q "var(--space-" frontend/src/pages/MainPage.css; then
    pass "MainPage.css uses spacing tokens"
else
    warn "MainPage.css may not be using tokens"
fi

echo ""

# Test 2: Git hooks
echo "Test 2: Git Pre-commit Hooks"
echo "----------------------------"
if [ -f ".husky/pre-commit" ]; then
    pass ".husky/pre-commit exists"
else
    fail ".husky/pre-commit missing"
fi

if [ -x ".husky/pre-commit" ]; then
    pass "pre-commit hook is executable"
else
    fail "pre-commit hook is not executable"
fi

# Check package.json has lint-staged config
if grep -q "lint-staged" frontend/package.json; then
    pass "lint-staged configured in package.json"
else
    fail "lint-staged not configured"
fi

echo ""

# Test 3: ESLint rules
echo "Test 3: ESLint Rules"
echo "-------------------"
if grep -q "react-hooks/exhaustive-deps" frontend/eslint.config.js; then
    pass "react-hooks/exhaustive-deps rule added"
else
    fail "Missing react-hooks rule"
fi

if grep -q "no-console" frontend/eslint.config.js; then
    pass "no-console rule added"
else
    fail "Missing no-console rule"
fi

if grep -q "@typescript-eslint/no-explicit-any" frontend/eslint.config.js; then
    pass "TypeScript any rule added"
else
    fail "Missing TypeScript any rule"
fi

echo ""

# Test 4: MainPage optimization
echo "Test 4: MainPage Optimization"
echo "-----------------------------"
if grep -q "import { useEffect, useState, useMemo, memo }" frontend/src/pages/MainPage.tsx; then
    pass "memo imported in MainPage.tsx"
else
    fail "memo not imported in MainPage.tsx"
fi

memo_count=$(grep -c "= memo(" frontend/src/pages/MainPage.tsx || true)
if [ "$memo_count" -ge 5 ]; then
    pass "Found $memo_count memoized components (expected 5+)"
else
    warn "Found only $memo_count memoized components (expected 5+)"
fi

echo ""

# Test 5: Deploy automation
echo "Test 5: Deploy Automation"
echo "------------------------"
if grep -q "def task_deploy" scripts/run_task.py; then
    pass "Deploy task exists in run_task.py"
else
    fail "Deploy task missing"
fi

# Check if deploy task is registered
if python3 scripts/run_task.py list 2>/dev/null | grep -q "deploy"; then
    pass "Deploy task registered successfully"
else
    warn "Deploy task may not be registered (check Python dependencies)"
fi

echo ""

# Test 6: Build tests
echo "Test 6: Build Verification"
echo "--------------------------"
echo "Running frontend build (this may take a few seconds)..."

cd frontend
if npm run build > /tmp/build_output.txt 2>&1; then
    pass "Frontend build succeeded"

    # Check build output
    if [ -f "dist/index.html" ]; then
        pass "dist/index.html created"
    else
        fail "dist/index.html not found"
    fi

    # Check CSS bundle exists
    if ls dist/assets/*.css 1> /dev/null 2>&1; then
        pass "CSS bundle created"
    else
        fail "CSS bundle not found"
    fi

    # Check JS bundle exists
    if ls dist/assets/*.js 1> /dev/null 2>&1; then
        pass "JS bundle created"
    else
        fail "JS bundle not found"
    fi
else
    fail "Frontend build failed (check /tmp/build_output.txt)"
    cat /tmp/build_output.txt
fi

cd ..
echo ""

# Test 7: TypeScript check
echo "Test 7: TypeScript Compilation"
echo "------------------------------"
cd frontend
if npx tsc -b --noEmit > /tmp/tsc_output.txt 2>&1; then
    pass "TypeScript compilation passed"
else
    warn "TypeScript has errors (check /tmp/tsc_output.txt)"
fi
cd ..
echo ""

# Summary
echo ""
echo "========================="
echo "Test Summary"
echo "========================="
echo ""
echo "Review the results above. Common issues:"
echo "  - ESLint warnings are expected (new rules catching issues)"
echo "  - Deploy task may need Python dependencies"
echo "  - TypeScript errors should be investigated"
echo ""
echo "Next steps:"
echo "  1. Review PHASE1_SUMMARY.md for detailed changes"
echo "  2. Test the app locally: cd frontend && npm run dev"
echo "  3. Check for visual regressions in the browser"
echo "  4. Run ESLint: cd frontend && npm run lint"
echo ""
