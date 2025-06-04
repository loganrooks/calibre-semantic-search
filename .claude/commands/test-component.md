Run tests for the component "$ARGUMENTS" and analyze results.

1. **Find Relevant Tests**:
   - Search for test files related to $ARGUMENTS
   - Look in tests/unit/, tests/integration/, tests/ui/
   - Show me the test files found

2. **Run Focused Tests**:
   ```bash
   # Run specific test file
   python -m pytest tests/unit/test_$ARGUMENTS.py -v
   
   # Run with coverage
   python -m pytest tests/unit/test_$ARGUMENTS.py --cov=calibre_plugins.semantic_search.$ARGUMENTS
   
   # Run matching test names
   python -m pytest -k "$ARGUMENTS" -v
   ```

3. **Analyze Results**:
   - Show number of tests passed/failed
   - Display any error messages or tracebacks
   - Check test coverage percentage
   - Identify untested code paths

4. **Check Integration**:
   - Are there integration tests for this component?
   - Does it have UI tests if it's a UI component?
   - Are edge cases covered?

5. **Fix Failing Tests**:
   - If tests fail, show the specific failures
   - Determine if it's a test issue or implementation issue
   - Suggest fixes for failing tests

6. **Run Full Suite** (if all pass):
   ```bash
   python -m pytest tests/ -x --tb=short
   ```

Show me test results and any issues found.