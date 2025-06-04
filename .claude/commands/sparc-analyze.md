Perform SPARC analysis for the problem/feature: "$ARGUMENTS"

## Verification First (ANTI-HALLUCINATION)
1. **Gather Evidence**:
   ```bash
   # Find relevant files
   find . -type f -name "*.py" | xargs grep -l "$ARGUMENTS" | head -20
   
   # Check current implementation
   grep -rn "$ARGUMENTS" --include="*.py" . | head -20
   
   # Look for related tests
   find tests -name "*.py" | xargs grep -l "$ARGUMENTS"
   ```

## SPARC Analysis Framework

### S - Situation (Current State)
2. **Document What EXISTS** (with evidence):
   - Current implementation: [Show actual code]
   - Current tests: [Show actual test files]
   - Current behavior: [Demonstrate with commands]
   - Dependencies: [List with verification]
   
   VERIFY each claim with actual file content or command output.

### P - Problem (What's Wrong/Missing)
3. **Define the Gap**:
   - Expected behavior: [Clear description]
   - Actual behavior: [With evidence]
   - Root cause: [Traced through code]
   - Impact: [Who/what is affected]
   
   For bugs: Include stack trace or error message
   For features: Show where integration points are needed

### A - Alternatives (Possible Solutions)
4. **Generate Options** (minimum 3):
   
   **Option 1: [Name]**
   - Approach: [Description]
   - Pros: [List benefits]
   - Cons: [List drawbacks]
   - Effort: [Low/Medium/High]
   - Risk: [Low/Medium/High]
   
   **Option 2: [Name]**
   - Approach: [Description]
   - Pros: [List benefits]
   - Cons: [List drawbacks]
   - Effort: [Low/Medium/High]
   - Risk: [Low/Medium/High]
   
   **Option 3: [Name]**
   - Approach: [Description]
   - Pros: [List benefits]
   - Cons: [List drawbacks]
   - Effort: [Low/Medium/High]
   - Risk: [Low/Medium/High]

### R - Recommendation (Best Choice)
5. **Select with Rationale**:
   - Chosen: Option [X]
   - Why: [Compelling reasons]
   - Trade-offs accepted: [What we're giving up]
   - Success criteria: [How we'll know it works]

### C - Consequences (What Happens Next)
6. **Predict Outcomes**:
   - **Immediate changes**:
     - Files to modify: [List with reasons]
     - New files needed: [List with purposes]
     - Tests to add/update: [List scenarios]
   
   - **Side effects**:
     - Performance impact: [Faster/Slower/Same]
     - Breaking changes: [None/List them]
     - Migration needs: [None/Describe]
   
   - **Future implications**:
     - Maintenance burden: [Lower/Same/Higher]
     - Extensibility: [How this enables future work]
     - Technical debt: [Reduced/Unchanged/Increased]

## Verification Checklist
- [ ] All current state claims backed by actual code/output
- [ ] Problem demonstrated with concrete examples
- [ ] Alternatives are genuinely different approaches
- [ ] Recommendation based on objective criteria
- [ ] Consequences are specific and measurable

## Next Steps
1. Review analysis with stakeholders
2. Create detailed specification: `/project:create-spec`
3. Plan implementation: `/project:architect`
4. Begin TDD cycle: `/project:tdd-cycle`

Remember: SPARC is about thinking before coding. Better analysis = fewer surprises.