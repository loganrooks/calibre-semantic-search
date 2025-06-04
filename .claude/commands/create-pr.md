Create a pull request for the current feature branch with proper requirement linking and conventional format

## PULL REQUEST CREATION WORKFLOW

### 1. Pre-PR Verification
**Check Feature Readiness**:
- Verify you're on a feature branch: `git branch --show-current`
- Ensure all work is committed: `git status` should be clean
- If uncommitted changes exist, run `/project:git-debt` first
- Check that feature branch is up to date with latest main/master

### 2. Identify Requirement Information
**Extract Requirement Details**:
- Find requirement ID from branch name (feature/FEAT-005-description) or recent commits
- Look for requirement document in `.requirements/[ID].md`
- Read requirement details: description, acceptance criteria, testing strategy
- Check if requirement status is "Implementation Complete" or similar

### 3. Analyze Implementation
**Review What Was Built**:
- Run `git diff main...HEAD --name-only` to see all changed files
- Run `git log main...HEAD --oneline` to see all commits
- Categorize changes: new features, bug fixes, tests, documentation, configuration
- Verify all acceptance criteria from requirement are met
- Check test coverage and ensure quality standards met

### 4. Generate PR Description
**Create Comprehensive PR Description**:
```markdown
## Summary
Brief description of what this PR implements.

**Implements**: [REQUIREMENT-ID] - [Requirement Description]

## Changes Made
- ✅ [Acceptance Criterion 1]: Implementation details
- ✅ [Acceptance Criterion 2]: Implementation details  
- ✅ [Acceptance Criterion 3]: Implementation details

## Technical Details
### Files Changed
- `path/to/file.py`: Description of changes
- `tests/test_file.py`: Added comprehensive test coverage
- `docs/file.md`: Updated documentation

### Architecture
- Brief description of architectural decisions
- Any design patterns used
- Integration points affected

## Testing
- [ ] All existing tests pass
- [ ] New tests added with >80% coverage
- [ ] Manual testing completed
- [ ] Integration tests pass
- [ ] Performance requirements met

## Quality Checklist
- [ ] Code follows project conventions
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] No security vulnerabilities introduced
- [ ] Backward compatibility maintained

## Deployment Notes
Any special deployment considerations or migration steps.

## Related
- Requirement Document: `.requirements/[ID].md`
- Related Issues: #XXX
- Dependencies: None / Other PRs
```

### 5. Run Pre-PR Checks
**Quality Assurance**:
- Run full test suite: `pytest tests/ --tb=short`
- Run linting: `pylint` or configured linter
- Run type checking: `mypy` if configured
- Build project successfully
- Check for security issues
- Verify performance requirements

### 6. Create the Pull Request
**Submit PR with Proper Format**:
- Push feature branch: `git push -u origin feature/[ID]-description`
- Create PR using GitHub CLI or web interface:
  ```bash
  gh pr create \
    --title "[TYPE]: Brief description of changes" \
    --body "$(cat pr-description.md)" \
    --label "enhancement,ready-for-review" \
    --assignee @me
  ```
- Use conventional PR title format: "feat(scope): description" or "fix(scope): description"
- Include requirement ID in title if not obvious: "feat(search): add similarity scoring (FEAT-005)"

### 7. Link Documentation
**Ensure Full Traceability**:
- Add PR link to requirement document `.requirements/[ID].md`
- Update requirement status to "In Review" 
- Add to project tracking (PROJECT_STATUS.md if relevant)
- Notify relevant stakeholders/reviewers

### 8. Post-PR Actions
**Follow-up Tasks**:
- Monitor CI/CD pipeline results
- Address any review feedback promptly
- Update requirement document with any changes
- Prepare for merge: ensure CHANGELOG.md is updated
- Plan post-merge cleanup if needed

### 9. Merge Preparation
**Pre-Merge Checklist**:
- All CI checks passing
- Required approvals received
- No merge conflicts
- Requirement document updated to "Ready for Merge"
- CHANGELOG.md entry confirmed
- Documentation is complete

### 10. Post-Merge Cleanup
**After Successful Merge**:
- Update requirement status to "Completed"
- Add final commit hash to requirement document
- Archive feature branch (or delete if policy allows)
- Update PROJECT_STATUS.md completion percentage
- Run `/project:git-debt` to clean up any remaining items

## Best Practices
1. **Atomic PRs**: One requirement per PR for clear review
2. **Descriptive Titles**: Use conventional commit format
3. **Comprehensive Testing**: Don't rely on reviewers to catch bugs
4. **Documentation**: Update all relevant docs in the same PR
5. **Traceability**: Always link to requirement documents
6. **Clean History**: Squash commits if requested by team policy

## Quality Gates
- All tests passing (unit, integration, e2e)
- Code coverage >80%
- No security vulnerabilities
- Documentation complete
- Requirement acceptance criteria met
- Performance requirements satisfied

Remember: A good PR tells a complete story and makes reviewers' lives easier.