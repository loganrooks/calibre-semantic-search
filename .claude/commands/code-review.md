Perform automated code review for: "$ARGUMENTS" (or recent changes if not specified)

## AUTOMATED CODE REVIEW CHECKLIST

### 1. Change Identification
**Find What Changed**:
```bash
# If reviewing specific component
find . -name "*$ARGUMENTS*" -type f -name "*.py" | head -20

# If reviewing recent changes
git diff --name-only HEAD~1
git diff HEAD~1 -- "*.py" | head -50
```

### 2. Code Quality Review

#### 2.1 Complexity Analysis
```bash
# Cyclomatic complexity
radon cc $FILES -s -n B

# Cognitive complexity
# Functions with CC > 10 need refactoring
```

**Issues Found**:
- [ ] Function X has complexity Y (threshold: 10)
- [ ] Class Z has too many methods (>20)
- [ ] File A is too long (>500 lines)

#### 2.2 Code Smells Detection
```python
# Long method detection
def check_method_length(filename):
    with open(filename) as f:
        lines = f.readlines()
    # Methods > 50 lines are suspect
    
# Duplicate code detection
# Parameters lists > 5 arguments
# Deeply nested code (>4 levels)
```

**Common Smells to Check**:
- [ ] Long methods (>50 lines)
- [ ] Long parameter lists (>5 params)
- [ ] Deep nesting (>4 levels)
- [ ] Duplicate code blocks
- [ ] Dead code (unreachable)
- [ ] God classes (doing too much)
- [ ] Feature envy (using other class's data)

### 3. Style & Conventions

#### 3.1 Naming Conventions
```bash
# Check naming patterns
grep -n "class [a-z]" $FILES  # Classes should be CamelCase
grep -n "def [A-Z]" $FILES     # Functions should be snake_case
grep -n "^[a-z].*=" $FILES     # Constants should be UPPER_CASE
```

**Naming Issues**:
- [ ] Non-PEP8 names found
- [ ] Unclear variable names (a, b, tmp)
- [ ] Inconsistent naming style

#### 3.2 Formatting Check
```bash
# PEP8 compliance
flake8 $FILES --statistics

# Black formatting
black $FILES --check --diff

# Import ordering
isort $FILES --check-only --diff
```

### 4. Documentation Review

#### 4.1 Docstring Coverage
```python
# Check all public methods have docstrings
ast.parse(code)
# Walk tree and verify docstrings exist
```

**Documentation Checklist**:
- [ ] Module docstring present
- [ ] All public classes documented
- [ ] All public methods documented
- [ ] Parameters documented with types
- [ ] Return values documented
- [ ] Exceptions documented
- [ ] Examples provided for complex functions

#### 4.2 Comment Quality
```bash
# Check for bad comments
grep -n "TODO\|FIXME\|HACK\|XXX" $FILES

# Check for obvious comments
grep -n "# increment\|# add 1\|# return" $FILES
```

### 5. Type Safety Review

#### 5.1 Type Hints Coverage
```bash
# Run mypy
mypy $FILES --ignore-missing-imports

# Check for Any types (should be specific)
grep -n ": Any" $FILES
```

**Type Issues**:
- [ ] Missing type hints on public methods
- [ ] Using Any instead of specific types
- [ ] Type errors found by mypy

### 6. Security Review

#### 6.1 Common Vulnerabilities
```bash
# Security scan
bandit -r $FILES -ll

# Check for hardcoded secrets
grep -n "password\|secret\|key\|token" $FILES | grep -v "test"

# SQL injection risks
grep -n "execute.*%s\|execute.*format" $FILES

# Command injection risks
grep -n "subprocess\|os.system\|eval\|exec" $FILES
```

**Security Checklist**:
- [ ] No hardcoded credentials
- [ ] Input validation present
- [ ] No SQL string concatenation
- [ ] No shell=True in subprocess
- [ ] No eval/exec with user input
- [ ] Proper error handling (no stack traces to users)

### 7. Testing Review

#### 7.1 Test Coverage
```bash
# Check if tests exist
test_files=$(find tests -name "*$ARGUMENTS*test*.py")
echo "Test files found: $test_files"

# Run coverage
pytest $test_files --cov=$MODULE --cov-report=term-missing
```

**Testing Checklist**:
- [ ] Tests exist for new code
- [ ] Edge cases covered
- [ ] Error cases tested
- [ ] Mocks used appropriately
- [ ] Tests are deterministic
- [ ] Tests run quickly (<1s each)

### 8. Design & Architecture Review

#### 8.1 SOLID Principles
**Single Responsibility**:
- [ ] Each class has one clear purpose
- [ ] Methods do one thing

**Open/Closed**:
- [ ] Extensible without modification
- [ ] Uses inheritance/composition properly

**Liskov Substitution**:
- [ ] Subclasses truly substitute base class
- [ ] No surprising behavior changes

**Interface Segregation**:
- [ ] No fat interfaces
- [ ] Clients not forced to depend on unused methods

**Dependency Inversion**:
- [ ] Depends on abstractions, not concretions
- [ ] High-level modules independent of low-level

#### 8.2 Design Pattern Usage
```bash
# Check for common patterns
grep -n "Factory\|Singleton\|Observer\|Strategy" $FILES

# Check for anti-patterns
grep -n "global\|singleton" $FILES
```

### 9. Performance Review

#### 9.1 Common Performance Issues
```python
# Check for performance anti-patterns
# - Nested loops with database queries
# - Loading entire file into memory
# - Inefficient string concatenation in loops
# - Not using generators for large datasets
```

**Performance Checklist**:
- [ ] No N+1 query problems
- [ ] Efficient data structures used
- [ ] No premature optimization
- [ ] Async/await used appropriately
- [ ] Caching implemented where beneficial

### 10. Error Handling Review

```bash
# Check exception handling
grep -n "except:" $FILES  # Bare excepts are bad
grep -n "except Exception" $FILES  # Too broad
grep -n "raise$" $FILES  # Re-raising without context
```

**Error Handling Checklist**:
- [ ] Specific exceptions caught
- [ ] Errors logged appropriately
- [ ] User-friendly error messages
- [ ] Resources cleaned up (finally/context managers)
- [ ] No silent failures

## REVIEW SUMMARY

### Severity Classification
**🔴 Critical** (Must fix):
1. [Issue description] - File:Line
2. [Issue description] - File:Line

**🟡 Major** (Should fix):
1. [Issue description] - File:Line
2. [Issue description] - File:Line

**🟢 Minor** (Nice to fix):
1. [Issue description] - File:Line
2. [Issue description] - File:Line

### Code Metrics
```
Metric                Current   Threshold   Status
-----------------    --------  ----------  --------
Complexity (avg)        X.X        10.0      [✓/✗]
Test Coverage           XX%        80%       [✓/✗]
Documentation           XX%        100%      [✓/✗]
Type Hint Coverage      XX%        90%       [✓/✗]
Security Issues          X          0        [✓/✗]
```

### Review Decision
- [ ] **APPROVED** - Ready to merge
- [ ] **APPROVED WITH COMMENTS** - Fix minor issues
- [ ] **NEEDS CHANGES** - Fix major issues
- [ ] **REJECTED** - Significant rework needed

### Actionable Feedback
1. **Must Do**:
   - Fix: [Specific issue with line number]
   - Add: [What's missing]

2. **Should Do**:
   - Refactor: [What and why]
   - Improve: [Specific improvement]

3. **Consider**:
   - Enhancement: [Future improvement]
   - Alternative: [Different approach]

## Next Steps
1. Address critical issues
2. Run tests after fixes
3. Request human review for design decisions
4. Update documentation if needed

Remember: Code review is about improving quality, not finding fault.