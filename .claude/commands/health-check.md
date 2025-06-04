Perform a comprehensive health check of the entire workspace.

## WORKSPACE HEALTH ASSESSMENT

### 1. Build Health
**Check Build System**:
```bash
# Can we build successfully?
[build_command]
echo "Build status: $?"

# Check for build warnings
[build_command] 2>&1 | grep -i "warning\|deprecated"

# Build artifacts present?
ls -la build/ dist/ *.zip 2>/dev/null
```

Health Score: [0-10]

### 2. Test Health
**Test Suite Analysis**:
```bash
# Run all tests
pytest tests/ --tb=short -q

# Test statistics
echo "Total tests: $(find tests -name "test_*.py" | wc -l) files"
echo "Test functions: $(grep -r "def test_" tests | wc -l)"

# Test execution time
time pytest tests/ -q

# Flaky tests check
pytest tests/ --count=3 -x
```

**Coverage Analysis**:
```bash
pytest --cov=. --cov-report=term-missing --cov-report=html
echo "Overall coverage: [X]%"
```

Health Score: [0-10]

### 3. Code Quality Health
**Static Analysis**:
```bash
# Find code smells
echo "=== Code Complexity ==="
find . -name "*.py" -path "./src/*" | xargs radon cc -s -n B

echo "=== Duplicate Code ==="
pylint --disable=all --enable=duplicate-code src/

echo "=== TODO/FIXME Count ==="
grep -rn "TODO\|FIXME\|HACK\|XXX" --include="*.py" . | wc -l
```

**Style Consistency**:
```bash
# Check formatting
black . --check --diff | wc -l
isort . --check-only | wc -l

# Type hints coverage
mypy . --ignore-missing-imports | grep "Success:" || echo "Type errors found"
```

Health Score: [0-10]

### 4. Dependency Health
**Dependency Analysis**:
```bash
# Check for outdated packages
pip list --outdated

# Security vulnerabilities
pip-audit

# Unused dependencies
pipreqs . --print | diff requirements.txt -

# Dependency conflicts
pip check
```

Health Score: [0-10]

### 5. Documentation Health
**Documentation Coverage**:
```bash
# Find undocumented modules
echo "=== Modules without docstrings ==="
find . -name "*.py" -exec grep -L '"""' {} \;

# Check README completeness
echo "=== README sections ==="
grep "^#" README.md

# Stale documentation check
echo "=== Docs older than code ==="
find docs -name "*.md" -mtime +30 | wc -l
```

**API Documentation**:
```python
# Check docstring coverage
import ast
import os

def check_docstrings(filepath):
    with open(filepath) as f:
        tree = ast.parse(f.read())
    
    functions = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    documented = [f for f in functions if ast.get_docstring(f)]
    
    return len(documented), len(functions)

# Calculate percentage
```

Health Score: [0-10]

### 6. Performance Health
**Performance Metrics**:
```bash
# Benchmark critical operations
pytest tests/performance/ --benchmark-only --benchmark-json=benchmark.json

# Check for performance regression
# Compare with previous benchmark.json

# Memory leaks check
pytest tests/ --memray
```

Health Score: [0-10]

### 7. Security Health
**Security Scan**:
```bash
# Check for common vulnerabilities
bandit -r . -ll

# Secrets detection
detect-secrets scan --all-files

# Check file permissions
find . -type f -perm /go+w -ls

# Review authentication code
grep -rn "password\|auth\|token\|secret" --include="*.py" .
```

Health Score: [0-10]

### 8. Architecture Health
**Architectural Metrics**:
```python
# Coupling analysis
import ast
import os
from collections import defaultdict

def analyze_imports(directory):
    coupling = defaultdict(set)
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                # Parse and analyze imports
                pass
    return coupling

# High coupling indicators
```

**Circular Dependencies**:
```bash
# Check for circular imports
pydeps . --max-bacon=2 --pylib=False

# Module hierarchy violations
# [Custom script to check layering]
```

Health Score: [0-10]

### 9. Technical Debt Assessment
**Debt Indicators**:
```bash
# Code age analysis
git log --format="%ad" --date=short -- "*.py" | sort | uniq -c

# Frequently changed files (potential hotspots)
git log --format=format: --name-only | grep ".py$" | sort | uniq -c | sort -rn | head -20

# Large files (potential for splitting)
find . -name "*.py" -exec wc -l {} \; | sort -rn | head -20

# Complex files
radon cc . -s -n D | wc -l
```

Health Score: [0-10]

### 10. Development Workflow Health
**Git Health**:
```bash
# Uncommitted changes
git status --porcelain | wc -l

# Stale branches
git for-each-ref --format='%(refname:short) %(committerdate)' refs/heads/ | awk '$2 < "'$(date -d '30 days ago' '+%Y-%m-%d')'"'

# Large commits (potential for breaking down)
git log --oneline --shortstat | grep -E "[0-9]{3,} insertion"
```

Health Score: [0-10]

## HEALTH REPORT GENERATION

### Overall Health Score
```
Category               Score   Status
-----------------     ------  --------
Build Health           X/10   [🟢/🟡/🔴]
Test Health            X/10   [🟢/🟡/🔴]
Code Quality           X/10   [🟢/🟡/🔴]
Dependencies           X/10   [🟢/🟡/🔴]
Documentation          X/10   [🟢/🟡/🔴]
Performance            X/10   [🟢/🟡/🔴]
Security               X/10   [🟢/🟡/🔴]
Architecture           X/10   [🟢/🟡/🔴]
Technical Debt         X/10   [🟢/🟡/🔴]
Workflow               X/10   [🟢/🟡/🔴]
-----------------     ------  --------
OVERALL HEALTH:        XX/100 [GRADE]
```

### Critical Issues Found
1. [Issue 1]: [Description] - Severity: [High/Medium/Low]
2. [Issue 2]: [Description] - Severity: [High/Medium/Low]
3. [Issue 3]: [Description] - Severity: [High/Medium/Low]

### Recommended Actions
**Immediate** (Health < 5):
- [ ] Action 1
- [ ] Action 2

**Short-term** (Health 5-7):
- [ ] Action 3
- [ ] Action 4

**Long-term** (Health 7-8):
- [ ] Action 5
- [ ] Action 6

### Improvement Tracking
Compare with previous health check:
- Previous score: XX/100
- Current score: YY/100
- Trend: [↑ Improving / → Stable / ↓ Declining]

## Next Steps
1. Address critical issues first
2. Run `/project:tech-debt` for detailed debt analysis
3. Run `/project:optimize-performance` for performance improvements
4. Schedule regular health checks (weekly/monthly)

Remember: A healthy codebase is a productive codebase.