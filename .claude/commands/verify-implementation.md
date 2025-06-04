Verify that the implementation of "$ARGUMENTS" matches specifications and works correctly.

## VERIFICATION FRAMEWORK

### 1. Specification Compliance Check
**Gather Evidence of Requirements**:
```bash
# Find specifications
find . -name "*.md" | xargs grep -l "$ARGUMENTS" | grep -E "spec|requirement|design"

# Find acceptance criteria
grep -rn "acceptance criteria\|must\|should\|shall" --include="*.md" . | grep -i "$ARGUMENTS"
```

**Create Compliance Checklist**:
- [ ] Requirement 1: [Description] → Status: [✓/✗]
- [ ] Requirement 2: [Description] → Status: [✓/✗]
- [ ] Requirement 3: [Description] → Status: [✓/✗]

### 2. Implementation Verification
**Static Analysis**:
```bash
# Find implementation
find . -name "*.py" | xargs grep -l "class $ARGUMENTS\|def $ARGUMENTS"

# Check implementation completeness
grep -n "TODO\|FIXME\|NotImplemented\|pass$" [implementation_file]

# Verify no placeholder code
grep -n "placeholder\|mock\|stub\|dummy" [implementation_file]
```

### 3. Test Coverage Verification
**Comprehensive Test Check**:
```bash
# Run tests with coverage
pytest tests/ -k "$ARGUMENTS" --cov=[module] --cov-report=term-missing -v

# Check coverage percentage
# Expected: >80%
# Actual: [X]%
# Missing lines: [List them]
```

**Test Quality Assessment**:
- [ ] Tests are independent (no shared state)
- [ ] Tests have clear names (test_what_when_expect)
- [ ] Tests check behavior, not implementation
- [ ] Edge cases covered
- [ ] Error cases covered

### 4. Integration Verification
**Real Environment Testing**:
```bash
# Build if needed
[build_command]

# Run in real environment
[run_command]

# Check logs for errors
grep -i "error\|exception\|warning" [log_file] | grep -i "$ARGUMENTS"
```

**Integration Points Check**:
1. **Dependency Integration**:
   - Dependencies available? [✓/✗]
   - Versions compatible? [✓/✗]
   - Initialization correct? [✓/✗]

2. **API Contract Verification**:
   ```python
   # Verify public API matches design
   import inspect
   methods = inspect.getmembers(Component, predicate=inspect.ismethod)
   # Compare with specification
   ```

### 5. Behavioral Verification
**Scenario Testing** (for each main use case):

**Scenario 1: [Normal Flow]**
```python
# Setup
input_data = [...]
expected_output = [...]

# Execute
actual_output = component.operation(input_data)

# Verify
assert actual_output == expected_output
```
Result: [PASS/FAIL]

**Scenario 2: [Edge Case]**
[Similar structure]
Result: [PASS/FAIL]

**Scenario 3: [Error Case]**
[Similar structure]
Result: [PASS/FAIL]

### 6. Performance Verification
**Benchmark Key Operations**:
```python
import timeit

# Measure performance
execution_time = timeit.timeit(
    'component.operation(data)',
    setup='...',
    number=1000
)

# Compare with requirements
Required: <X seconds
Actual: Y seconds
Status: [PASS/FAIL]
```

**Resource Usage Check**:
```python
import tracemalloc
tracemalloc.start()

# Run operation
component.operation(large_data)

current, peak = tracemalloc.get_traced_memory()
print(f"Peak memory: {peak / 1024 / 1024:.1f} MB")

# Requirement: <X MB
# Actual: Y MB
# Status: [PASS/FAIL]
```

### 7. Security Verification
**Security Checklist**:
- [ ] No hardcoded secrets
- [ ] Input validation present
- [ ] SQL injection prevention (if applicable)
- [ ] XSS prevention (if UI)
- [ ] Proper authentication/authorization

```bash
# Check for security issues
grep -rn "password\|secret\|key\|token" [implementation_file] | grep -v "test"
```

### 8. Code Quality Verification
**Quality Metrics**:
```bash
# Complexity check
radon cc [implementation_file] -s

# Maintainability index
radon mi [implementation_file] -s

# Linting
pylint [implementation_file]

# Type checking
mypy [implementation_file]
```

**Quality Standards**:
- Cyclomatic complexity: <10 per method
- Maintainability index: >20
- Pylint score: >8.0
- No type errors

### 9. Documentation Verification
**Documentation Completeness**:
- [ ] All public methods have docstrings
- [ ] Parameters documented with types
- [ ] Return values documented
- [ ] Exceptions documented
- [ ] Examples provided
- [ ] Module docstring present

### 10. Regression Verification
**Ensure Nothing Broke**:
```bash
# Run full test suite
pytest tests/ -x --tb=short

# Check critical features still work
pytest tests/integration/ -v

# Verify no performance regression
pytest tests/performance/ --benchmark-only
```

## VERIFICATION SUMMARY

### Pass/Fail Criteria
**PASS Requirements** (All must be true):
- [ ] All specifications implemented
- [ ] Test coverage >80%
- [ ] All tests passing
- [ ] No critical issues in code quality
- [ ] Performance meets requirements
- [ ] No security vulnerabilities
- [ ] Documentation complete
- [ ] No regressions

### Evidence Collection
Create verification report:
```markdown
# Verification Report: $ARGUMENTS

Date: [Today]
Version: [X.Y.Z]

## Specification Compliance
[List each requirement and evidence of completion]

## Test Results
Coverage: X%
Tests Passed: Y/Z

## Performance Results
[Metrics and comparison with requirements]

## Issues Found
[Any problems discovered]

## Conclusion
Status: [VERIFIED/FAILED]
```

## Next Steps
- If VERIFIED: Ready for deployment
- If FAILED: Fix issues and re-verify
- Run `/project:code-review` for peer review
- Update documentation with results

Remember: Verification is about proving correctness with evidence.