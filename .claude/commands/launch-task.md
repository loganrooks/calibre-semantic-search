Launch a complete SPARC+TDD task orchestration workflow for: "$ARGUMENTS"

## PHASE 0: Requirement ID Generation & Git Hygiene
1. **Generate Requirement ID**:
   - Run `/project:generate-requirement-id "$ARGUMENTS"` to create trackable ID
   - Use the generated ID (e.g., FEAT-005) throughout this workflow
   - Create feature branch: `git checkout -b feature/[ID]-short-description`

2. **Git Debt Check**:
   - Run `git status` to check for uncommitted changes
   - If uncommitted changes exist, run `/project:git-debt` first
   - Start with clean working directory for proper change tracking

## PHASE 1: Task Understanding & Verification
1. **Parse Task Specification**:
   - Extract: What needs to be built/fixed/improved
   - Identify: Acceptance criteria (explicit or implicit)
   - Classify: Feature/Bug/Refactor/Performance/Documentation
   - Estimate: Complexity (Simple/Medium/Complex/Epic)

2. **Verify Understanding** (ANTI-HALLUCINATION):
   ```
   TASK: $ARGUMENTS
   TYPE: [Classified type]
   ACCEPTANCE CRITERIA:
   - [ ] Criterion 1
   - [ ] Criterion 2
   QUESTIONS TO CLARIFY:
   - Any ambiguities?
   ```
   STOP if understanding is unclear. Ask for clarification.

## PHASE 2: SPARC Analysis
3. **Situation Analysis**:
   - Current state of relevant code/features
   - Existing tests and coverage
   - Dependencies and constraints
   - VERIFY: Actually read the files, don't assume

4. **Problem Definition**:
   - Root cause (for bugs) or gap (for features)
   - Why current state is insufficient
   - Impact of not addressing this

5. **Alternatives Exploration**:
   - List 3+ implementation approaches
   - Pros/cons of each approach
   - Consider: Maintainability, performance, complexity

6. **Result Selection**:
   - Choose approach with rationale
   - Identify risks and mitigations
   - Define success metrics

7. **Consequences Prediction**:
   - What will change in the codebase
   - Potential side effects
   - Future maintenance implications

## PHASE 3: Specification & Design
8. **Create Detailed Specification**:
   - Behavioral specifications (Given/When/Then)
   - API contracts if applicable
   - UI/UX changes if applicable
   - Data model changes if needed

9. **Architecture Design**:
   - Component diagram if complex
   - Sequence diagram for interactions
   - Design patterns to apply
   
10. **Write Pseudocode** (VERIFICATION CHECKPOINT):
    ```
    # Main flow
    def feature():
        # Step 1: ...
        # Step 2: ...
        # Verify: Does this match spec?
    ```

## PHASE 4: TDD Implementation
11. **Test Planning**:
    - List all test scenarios
    - Prioritize by risk/importance
    - Identify: Unit/Integration/E2E tests needed

12. **RED Phase** (ANTI-HALLUCINATION):
    - Write first failing test
    - ACTUALLY RUN: `pytest test_file.py::test_name -v`
    - VERIFY: Test fails for the right reason
    - STOP if test passes (means misunderstanding)

13. **GREEN Phase**:
    - Implement minimal code
    - RUN: `pytest test_file.py::test_name -v`
    - VERIFY: Test now passes
    - NO extra features yet

14. **REFACTOR Phase**:
    - Improve code quality
    - Extract methods/constants
    - RUN ALL TESTS: `pytest tests/ -x`
    - VERIFY: Still green

15. **Repeat TDD Cycle**:
    - Next test from plan
    - Continue until all scenarios covered

## PHASE 5: Quality Assurance
16. **Coverage Analysis**:
    ```bash
    pytest --cov=module --cov-report=term-missing
    ```
    - Identify uncovered lines
    - Add tests for edge cases

17. **Integration Testing**:
    - Test with real dependencies
    - Verify in actual environment
    - Check performance metrics

18. **Code Review Checklist**:
    - [ ] Follows project conventions
    - [ ] Has appropriate documentation
    - [ ] No code smells
    - [ ] Security considerations addressed
    - [ ] Performance acceptable

## PHASE 6: Verification & Delivery
19. **Acceptance Testing**:
    - [ ] Each acceptance criterion met
    - [ ] Manual testing if UI involved
    - [ ] No regressions introduced

20. **Documentation Updates**:
    - Update relevant docs
    - Add/update code comments
    - Update changelog

21. **Final Verification** (ANTI-HALLUCINATION):
    - Build project: `[build command]`
    - Run full test suite
    - Test in real environment
    - SHOW ACTUAL OUTPUT, not assumed success

## PHASE 7: Git Integration & Documentation
22. **Commit Implementation**:
    - Stage all related changes: `git add [relevant files]`
    - Commit with conventional format and requirement ID:
      ```
      git commit -m "feat(scope): brief description
      
      Detailed description of what was implemented.
      
      Implements: [REQUIREMENT-ID]
      
      - Acceptance criterion 1 met
      - Acceptance criterion 2 met
      - Tests added with >80% coverage"
      ```

23. **Update Documentation**:
    - Update CHANGELOG.md with new feature entry
    - Update requirement document status to "Completed"
    - Update PROJECT_STATUS.md if relevant
    - Link commits to requirement ID in `.requirements/[ID].md`

24. **Branch Management**:
    - Push feature branch: `git push -u origin feature/[ID]-description`
    - Prepare for PR: Include requirement ID in PR description
    - Reference requirement document in PR for reviewers

25. **Clean Up Git Debt**:
    - Run `/project:git-debt` if any uncommitted changes remain
    - Ensure all work is properly committed and documented

## Orchestration Rules:
- STOP at any verification failure
- NEVER skip test execution
- ALWAYS show actual command output
- If unsure, ask for clarification
- Document decisions and rationale
- ALWAYS link to requirement ID in commits
- NEVER leave uncommitted changes

This orchestration ensures systematic, verifiable progress with multiple checkpoints to prevent hallucination, ensure quality, and maintain clean git history with full traceability.