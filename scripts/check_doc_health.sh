#!/bin/bash
# Documentation Health Check Script
# Run this to verify documentation system compliance

echo "🔍 Checking Documentation Health..."
echo "=================================="

# Check root directory file count
ROOT_COUNT=$(find . -maxdepth 1 -name "*.md" | wc -l)
echo "📁 Root markdown files: $ROOT_COUNT/4"

if [ $ROOT_COUNT -gt 4 ]; then
    echo "❌ VIOLATION: Too many files in root directory!"
    echo "   Expected: 4 (CLAUDE.md, PROJECT_STATUS.md, CHANGELOG.md, README.md)"
    echo "   Found: $ROOT_COUNT files"
    echo "   Files in root:"
    ls -la *.md
    exit 1
elif [ $ROOT_COUNT -eq 4 ]; then
    echo "✅ Root directory file count: PERFECT"
else
    echo "⚠️  Root directory file count: $ROOT_COUNT (expected 4)"
fi

echo ""

# Check for stale documents
echo "📅 Checking for stale documents (>60 days)..."
STALE_COUNT=0
if [ -d "docs/" ]; then
    STALE_FILES=$(find docs/ -name "*.md" -mtime +60 2>/dev/null)
    if [ -n "$STALE_FILES" ]; then
        STALE_COUNT=$(echo "$STALE_FILES" | wc -l)
        echo "⚠️  Found $STALE_COUNT stale documents:"
        echo "$STALE_FILES"
    else
        echo "✅ No stale documents found"
    fi
fi

echo ""

# Check for required essential files
echo "📋 Checking essential files..."
ESSENTIAL_FILES=("CLAUDE.md" "PROJECT_STATUS.md" "CHANGELOG.md" "README.md")
MISSING_COUNT=0

for file in "${ESSENTIAL_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file exists"
    else
        echo "❌ MISSING: $file"
        ((MISSING_COUNT++))
    fi
done

echo ""

# Check directory structure
echo "📂 Checking directory structure..."
EXPECTED_DIRS=("docs" "archive" "docs/lessons" "docs/planning" "docs/terminology")
for dir in "${EXPECTED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "✅ $dir exists"
    else
        echo "⚠️  Missing directory: $dir"
    fi
done

echo ""

# Summary
echo "📊 SUMMARY"
echo "=========="
echo "Root files: $ROOT_COUNT/4"
echo "Stale documents: $STALE_COUNT"
echo "Missing essential: $MISSING_COUNT"

if [ $ROOT_COUNT -le 4 ] && [ $STALE_COUNT -eq 0 ] && [ $MISSING_COUNT -eq 0 ]; then
    echo "🎉 Documentation health: EXCELLENT"
    exit 0
elif [ $ROOT_COUNT -le 5 ] && [ $STALE_COUNT -le 2 ] && [ $MISSING_COUNT -eq 0 ]; then
    echo "✅ Documentation health: GOOD"
    exit 0
else
    echo "⚠️  Documentation health: NEEDS ATTENTION"
    exit 1
fi