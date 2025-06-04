Run a complete TDD cycle for implementing: "$ARGUMENTS"

## PRE-CYCLE VERIFICATION
1. **Git & Requirements Check**:
   - Check if feature has requirement ID, if not run `/project:generate-requirement-id "$ARGUMENTS"`
   - Ensure on feature branch: `git checkout feature/[ID]-description` 
   - Check git status is clean or run `/project:git-debt` first
   - Store requirement ID for commit linking

2. **Prerequisites Check**:
   - [ ] SPARC analysis complete?
   - [ ] Architecture designed?
   - [ ] Specifications clear?
   - [ ] Test environment working?
   
   ```bash
   # Verify test environment
   python -m pytest --version
   python -m pytest tests/ -k "test_simple" --tb=short
   ```

## TDD CYCLE ORCHESTRATION

### CYCLE 1: Core Functionality

#### RED PHASE (Write Failing Test)
2. **Create Test File** (if needed):
   ```bash
   touch tests/unit/test_$ARGUMENTS.py
   ```

3. **Write FIRST Test** (Simplest Case):
   ```python
   def test_$ARGUMENTS_exists():
       """Component should exist and be importable"""
       from module import Component
       assert Component is not None
   ```

4. **VERIFY RED** (MANDATORY):
   ```bash
   pytest tests/unit/test_$ARGUMENTS.py::test_$ARGUMENTS_exists -v
   ```
   EXPECTED: ImportError or AttributeError
   ACTUAL: [Show actual error]
   
   ⚠️ STOP if test passes - means misunderstanding

#### GREEN PHASE (Minimal Implementation)
5. **Create Minimal Code**:
   ```python
   # Just enough to pass
   class Component:
       pass
   ```

6. **VERIFY GREEN** (MANDATORY):
   ```bash
   pytest tests/unit/test_$ARGUMENTS.py::test_$ARGUMENTS_exists -v
   ```
   EXPECTED: 1 passed
   ACTUAL: [Show actual output]

#### REFACTOR PHASE
7. **Clean Up** (if needed):
   - Add docstring
   - Fix naming
   - Extract constants

8. **VERIFY STILL GREEN**:
   ```bash
   pytest tests/unit/test_$ARGUMENTS.py -v
   ```

### CYCLE 2: First Real Behavior

#### RED PHASE
9. **Write Behavior Test**:
   ```python
   def test_$ARGUMENTS_core_behavior():
       """Should do its main job"""
       component = Component()
       result = component.do_something(input_data)
       assert result == expected_output
   ```

10. **VERIFY RED**:
    ```bash
    pytest tests/unit/test_$ARGUMENTS.py::test_$ARGUMENTS_core_behavior -v
    ```
    EXPECTED: AttributeError: 'Component' has no attribute 'do_something'
    ACTUAL: [Show actual error]

#### GREEN PHASE
11. **Implement Behavior**:
    ```python
    def do_something(self, input_data):
        return expected_output  # Simplest thing
    ```

12. **VERIFY GREEN**:
    ```bash
    pytest tests/unit/test_$ARGUMENTS.py -v
    ```
    ALL tests should pass

### CYCLE 3: Edge Cases

#### Systematic Edge Case Testing
13. **Identify Edge Cases**:
    - [ ] Empty input
    - [ ] None/null input
    - [ ] Invalid types
    - [ ] Boundary values
    - [ ] Concurrent access
    - [ ] Resource exhaustion

14. **Write Edge Case Tests** (One at a time):
    ```python
    def test_$ARGUMENTS_handles_empty_input():
        """Should handle empty input gracefully"""
        component = Component()
        result = component.do_something([])
        assert result == default_value
    ```

15. **RED-GREEN-REFACTOR** for each edge case

### CYCLE 4: Error Handling

16. **Write Error Tests**:
    ```python
    def test_$ARGUMENTS_raises_on_invalid_input():
        """Should raise specific error for invalid input"""
        component = Component()
        with pytest.raises(ValueError, match="Invalid input"):
            component.do_something(invalid_data)
    ```

17. **Implement Error Handling**:
    - Specific exceptions
    - Clear error messages
    - Recovery strategies

### CYCLE 5: Integration

18. **Write Integration Tests**:
    ```python
    def test_$ARGUMENTS_integrates_with_system():
        """Should work with real dependencies"""
        # Use real collaborators, not mocks
        component = Component(real_dependency)
        result = component.do_something(real_data)
        assert result in real_dependency.get_results()
    ```

## VERIFICATION CHECKPOINTS

### Coverage Check
19. **Measure Coverage**:
    ```bash
    pytest tests/unit/test_$ARGUMENTS.py --cov=module.$ARGUMENTS --cov-report=term-missing
    ```
    Target: >80% coverage
    Missing lines: [List them]

### Performance Check
20. **Basic Performance Test**:
    ```python
    def test_$ARGUMENTS_performance():
        """Should complete in reasonable time"""
        import time
        component = Component()
        start = time.time()
        component.do_something(large_dataset)
        duration = time.time() - start
        assert duration < 1.0  # seconds
    ```

### Full Suite Check
21. **Run ALL Tests**:
    ```bash
    pytest tests/ -x --tb=short
    ```
    MUST: All pass before proceeding

## POST-CYCLE VERIFICATION

22. **Manual Testing** (if UI/interactive):
    - Build/install: `[build command]`
    - Run application
    - Test feature manually
    - Screenshot/record results

23. **Code Quality Check**:
    ```bash
    # Linting
    pylint module/$ARGUMENTS.py
    
    # Type checking
    mypy module/$ARGUMENTS.py
    
    # Formatting
    black module/$ARGUMENTS.py --check
    ```

24. **Documentation Check**:
    - [ ] All public methods documented
    - [ ] Examples in docstrings
    - [ ] Type hints complete
    - [ ] README updated if needed

## POST-CYCLE GIT INTEGRATION

25. **Commit TDD Implementation**:
    - Stage all test and implementation files
    - Create comprehensive commit with requirement ID:
      ```
      git commit -m "test/feat(component): implement $ARGUMENTS with TDD
      
      Complete TDD implementation with comprehensive test coverage:
      - Added [X] unit tests covering all scenarios
      - Implemented core functionality with [Y] methods
      - Added edge case handling and error management
      - Achieved >80% test coverage
      
      Implements: [REQUIREMENT-ID]
      
      Tests:
      - test_component_exists: ✅
      - test_core_behavior: ✅ 
      - test_edge_cases: ✅
      - test_error_handling: ✅"
      ```

26. **Update Requirement Tracking**:
    - Update `.requirements/[ID].md` progress log
    - Mark acceptance criteria as completed
    - Link commit hash to requirement document
    - Update status to "Implementation Complete" or "Ready for Review"

27. **Clean Up**:
    - Run `/project:git-debt` to handle any remaining changes
    - Ensure all TDD artifacts are committed and tracked
    - Prepare for next phase (integration testing, code review, etc.)

## Anti-Hallucination Rules
1. NEVER claim test passes without running
2. ALWAYS show actual command output
3. STOP at first failure to investigate
4. NO implementation without failing test
5. VERIFY each phase independently
6. ALWAYS commit with requirement ID linking
7. NEVER leave uncommitted TDD work

## Next Steps
- Run `/project:code-review` for quality check
- Run `/project:integration-verify` for system check
- Update documentation with `/project:update-docs`
- Consider `/project:git-debt` if any loose ends remain

Remember: TDD is about confidence through verification and complete traceability.