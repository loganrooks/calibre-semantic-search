Analyze technical debt in the codebase (or specific area: "$ARGUMENTS")

## TECHNICAL DEBT ASSESSMENT

### 1. Code Decay Analysis
**Identify Aging Code**:
```bash
# Find oldest unchanged files (potential legacy code)
for file in $(find . -name "*.py" -path "*/src/*"); do
    echo "$(git log -1 --format="%ai" -- "$file") $file"
done | sort | head -20

# Files changed most frequently (hotspots)
git log --format=format: --name-only | grep ".py$" | sort | uniq -c | sort -rn | head -20

# Large files that keep growing
for file in $(find . -name "*.py" -size +50k); do
    echo "$(wc -l $file) - $(git log --oneline $file | wc -l) changes"
done
```

### 2. Complexity Debt

#### 2.1 Cyclomatic Complexity
```bash
# Find most complex functions
radon cc . -s -n F | head -20

# Files with high average complexity
radon cc . -s -a | grep -E "Average complexity: [A-F] \(([1-9][0-9]|[7-9])"

# Count of complex functions by grade
echo "Complexity Distribution:"
echo "A (1-5): $(radon cc . -n A | grep -c "Function")"
echo "B (6-10): $(radon cc . -n B | grep -c "Function")"
echo "C (11-20): $(radon cc . -n C | grep -c "Function")"
echo "D (21-30): $(radon cc . -n D | grep -c "Function")"
echo "E (31-40): $(radon cc . -n E | grep -c "Function")"
echo "F (41+): $(radon cc . -n F | grep -c "Function")"
```

#### 2.2 Cognitive Complexity
```python
# Functions that are hard to understand
# - Deep nesting
# - Many branches
# - Complex conditionals
```

### 3. Design Debt

#### 3.1 Coupling Analysis
```bash
# High fan-out (depends on many modules)
for file in $(find . -name "*.py"); do
    imports=$(grep -E "^import |^from " "$file" | wc -l)
    if [ $imports -gt 15 ]; then
        echo "$imports imports: $file"
    fi
done | sort -rn

# Circular dependencies
pydeps . --max-bacon=0 --pylib=False 2>&1 | grep "circular"

# God classes (too many methods)
for file in $(find . -name "*.py"); do
    methods=$(grep -c "^    def " "$file")
    if [ $methods -gt 20 ]; then
        echo "$methods methods: $file"
    fi
done | sort -rn
```

#### 3.2 Inheritance Depth
```python
# Classes with deep inheritance
import ast

def check_inheritance_depth(filename):
    # Parse and find classes with >3 levels of inheritance
    pass
```

### 4. Documentation Debt

#### 4.1 Missing Documentation
```bash
# Functions without docstrings
for file in $(find . -name "*.py"); do
    total=$(grep -c "^def " "$file")
    with_docs=$(grep -A1 "^def " "$file" | grep -c '"""')
    if [ $total -gt 0 ]; then
        percent=$((with_docs * 100 / total))
        if [ $percent -lt 50 ]; then
            echo "$percent% documented: $file ($with_docs/$total)"
        fi
    fi
done | sort -n

# Outdated TODOs
echo "Old TODOs (>90 days):"
for file in $(grep -r "TODO" --include="*.py" -l .); do
    git blame "$file" | grep "TODO" | awk '{print $1}' | while read commit; do
        age=$(git show -s --format="%cr" $commit)
        echo "$age: $file"
    done
done | grep -E "months|year"
```

### 5. Test Debt

#### 5.1 Test Coverage Gaps
```bash
# Run coverage and find untested files
pytest --cov=. --cov-report=term-missing | grep -E "^[a-zA-Z].*\s+[0-9]+\s+[0-9]+\s+[0-6][0-9]%"

# Files with no tests
for source in $(find . -name "*.py" -path "*/src/*"); do
    test_file="tests/$(basename $source | sed 's/\.py/_test.py/')"
    if [ ! -f "$test_file" ]; then
        echo "No tests: $source"
    fi
done

# Test-to-code ratio
echo "Lines of code: $(find . -name "*.py" -path "*/src/*" -exec cat {} \; | wc -l)"
echo "Lines of tests: $(find . -name "*.py" -path "*/tests/*" -exec cat {} \; | wc -l)"
```

### 6. Dependency Debt

#### 6.1 Outdated Dependencies
```bash
# Check for outdated packages
pip list --outdated

# Dependencies with security issues
pip-audit

# Unused dependencies
# Compare imports with requirements.txt
```

#### 6.2 Version Pinning Issues
```bash
# Overly specific pins (blocks updates)
grep -E "==[0-9]+\.[0-9]+\.[0-9]+\b" requirements.txt

# Too loose pins (risks breaking changes)
grep -E ">=|>" requirements.txt
```

### 7. Performance Debt

#### 7.1 Inefficient Patterns
```bash
# String concatenation in loops
grep -n "for.*in.*:" -A5 . | grep -E "\+="

# Repeated database queries in loops
grep -n "for.*in.*:" -A5 . | grep -E "query|select|execute"

# Large memory allocations
grep -n "range(.*[0-9]{6,}" .
```

### 8. Security Debt

#### 8.1 Security Anti-patterns
```bash
# Hardcoded secrets
grep -rn "password.*=.*['\"]" --include="*.py" .

# SQL string formatting
grep -rn "execute.*%" --include="*.py" .

# Unsafe deserialization
grep -rn "pickle.loads\|eval\|exec" --include="*.py" .
```

### 9. Infrastructure Debt

#### 9.1 Build System Issues
```bash
# Build time analysis
time [build_command]

# Build complexity (number of steps)
grep -c "^[a-z]" Makefile

# CI/CD pipeline duration
# Check recent pipeline runs
```

### 10. Debt Quantification

#### 10.1 Calculate Debt Score
```python
def calculate_tech_debt_score():
    scores = {
        'complexity': 0,      # Based on CC metrics
        'documentation': 0,   # Based on coverage
        'testing': 0,         # Based on test coverage
        'dependencies': 0,    # Based on outdated count
        'security': 0,        # Based on vulnerabilities
        'design': 0,          # Based on coupling/cohesion
    }
    
    # Weight each category
    weights = {
        'complexity': 0.25,
        'documentation': 0.10,
        'testing': 0.25,
        'dependencies': 0.15,
        'security': 0.20,
        'design': 0.15,
    }
    
    # Calculate weighted score
    total_debt = sum(scores[k] * weights[k] for k in scores)
    return total_debt
```

## TECHNICAL DEBT REPORT

### Debt Summary
```
Category          Items    Severity    Est. Hours
--------------   -------  ----------  ------------
High Complexity     XX      HIGH           XXX
Missing Tests       XX      HIGH           XXX
Poor Docs          XX      MEDIUM          XX
Old Dependencies   XX      MEDIUM          XX
Security Issues    XX      CRITICAL        XX
Design Smells      XX      MEDIUM          XX
--------------   -------  ----------  ------------
TOTAL DEBT         XXX                     XXX hrs
```

### Critical Debt Items (Fix Immediately)
1. **Security Vulnerability**: [Description] - File:Line
2. **Performance Bottleneck**: [Description] - File:Line
3. **Blocking Issue**: [Description] - File:Line

### High Priority Debt (Fix This Sprint)
1. **Complex Function**: [Name] - CC=XX - File:Line
2. **Missing Tests**: [Module] - 0% coverage
3. **Circular Dependency**: [A→B→C→A]

### Medium Priority Debt (Fix This Quarter)
1. **Documentation**: XX% of functions undocumented
2. **Old TODOs**: XX items older than 6 months
3. **Code Duplication**: XX duplicate blocks found

### Debt Trends
```
Month     Total Items    Hours    Trend
-------   -----------   -------  -------
Month-3        XXX        XXX      ---
Month-2        XXX        XXX      ↑/↓
Month-1        XXX        XXX      ↑/↓
Current        XXX        XXX      ↑/↓
```

### Remediation Plan

#### Quick Wins (< 1 hour each)
- [ ] Update dependencies
- [ ] Fix simple security issues
- [ ] Add missing docstrings
- [ ] Remove dead code

#### Refactoring Targets (1-4 hours)
- [ ] Split god class: [ClassName]
- [ ] Reduce complexity: [FunctionName]
- [ ] Break circular dependency: [Module]

#### Major Initiatives (> 1 day)
- [ ] Redesign [Component]
- [ ] Add comprehensive tests for [Module]
- [ ] Performance optimization of [Feature]

### ROI Analysis
**Highest Impact Fixes**:
1. Fix [Issue] → Saves X hours/month
2. Refactor [Component] → Reduces bugs by Y%
3. Add tests to [Module] → Prevents regressions

### Debt Prevention
**New Policies to Implement**:
- [ ] Complexity limit in CI/CD
- [ ] Mandatory tests for new code
- [ ] Documentation required for PR
- [ ] Regular dependency updates
- [ ] Security scanning in pipeline

## Next Steps
1. Prioritize critical security issues
2. Schedule refactoring for high-complexity items
3. Add tech debt items to backlog
4. Set up monitoring for debt metrics
5. Regular debt review meetings

Remember: The best time to pay tech debt is before it compounds.