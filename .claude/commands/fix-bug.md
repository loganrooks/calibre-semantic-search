Fix the bug: "$ARGUMENTS" using bug-first TDD methodology.

## Phase 0: Bug Tracking Setup
**Initialize Bug Tracking**:
- Generate bug ID: `/project:generate-requirement-id "Fix: $ARGUMENTS"`
- Create bug fix branch: `git checkout -b fix/[ID]-short-description`
- Ensure clean working directory or run `/project:git-debt` first
- Document bug details in requirement system for tracking

1. **Reproduce the Bug**:
   - Understand exact conditions causing the bug
   - Find the error message or incorrect behavior
   - Identify the file and method where it occurs
   - Create minimal steps to reproduce

2. **Write Failing Test FIRST**:
   ```python
   def test_$ARGUMENTS_bug(self):
       """
       BUG: $ARGUMENTS
       This test should FAIL until bug is fixed.
       """
       # Reproduce exact conditions causing the bug
       # Assert expected behavior
   ```

3. **Verify Test Fails**:
   - Run test and confirm it fails with same error
   - If test passes, the bug isn't properly captured
   - Show me the failing test output

4. **Fix Minimal Code**:
   - Make smallest change to fix the bug
   - Don't refactor or improve unrelated code
   - Run test to verify fix works

5. **Verify in Real Environment**:
   - Build plugin: python scripts/build_plugin.py
   - Install: calibre-customize -a calibre-semantic-search.zip
   - Test manually in Calibre
   - Check for side effects

6. **Document Fix**:
   - Add comment explaining why fix was needed
   - Update CHANGELOG.md with bug fix entry
   - Keep test for regression prevention

## Phase 1: Git Integration & Tracking

7. **Commit Bug Fix**:
   - Stage all related changes: `git add [test files] [fix files]`
   - Commit with conventional format and bug ID:
     ```
     git commit -m "fix(component): resolve $ARGUMENTS
     
     Bug Details:
     - Issue: [Brief description of the problem]
     - Root Cause: [What was causing the bug]
     - Solution: [How it was fixed]
     
     Fixes: [BUG-ID]
     
     Testing:
     - Added regression test: test_[bug_name]
     - Verified fix in real environment
     - No side effects detected"
     ```

8. **Update Bug Tracking**:
   - Update `.requirements/[ID].md` status to "Fixed"
   - Link commit hash to bug report
   - Document root cause and solution in requirement document
   - Add to CHANGELOG.md under "Fixed" section

9. **Clean Up**:
   - Run `/project:git-debt` to handle any remaining changes
   - Ensure all bug fix artifacts are committed
   - Prepare for testing and PR creation

10. **Next Steps**:
    - Create pull request: `/project:create-pr`
    - Ensure fix is tested in integration environment
    - Monitor for any regression after deployment

Show the test and fix with explanations, including the requirement ID for tracking.