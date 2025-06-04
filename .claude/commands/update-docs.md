Update project documentation after completing work on "$ARGUMENTS". Follow this checklist:

1. **Update PROJECT_STATUS.md**:
   - Change "Last Updated" date to today
   - Update version number if significant progress
   - Adjust completion percentage
   - Add new work to "RECENTLY IMPLEMENTED" section
   - Move completed items from "Critical Issues" to implemented
   - Update time estimates for remaining work

2. **Update CHANGELOG.md**:
   - Add entry under [Unreleased] with today's date
   - Group changes by category (Added, Fixed, Changed)
   - Include specific file:line references for changes
   - Note any breaking changes or integration gaps

3. **Update CLAUDE.md if needed**:
   - Update "CURRENT ACTIVE TASK" section
   - Revise version and status in overview
   - Add any new lessons learned
   - Update "Recent Work" with checkbox status

4. **Check for new issues to document**:
   - Any new integration gaps discovered?
   - New dependencies or requirements?
   - Lessons that should be captured?

5. **Commit documentation updates**:
   ```bash
   git add PROJECT_STATUS.md CHANGELOG.md CLAUDE.md
   git commit -m "docs: update status after $ARGUMENTS implementation"
   ```

Show me the key changes made to each file.