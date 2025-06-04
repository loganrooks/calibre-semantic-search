Analyze the current git repository for uncommitted changes and help me organize them into logical commits following conventional commit patterns. Follow these steps:

1. **Git Debt Assessment**:
   - Run `git status --porcelain` to see all uncommitted changes
   - Categorize changes by type: staged, unstaged, untracked
   - Check how long files have been uncommitted using `git log -1 --format="%cr" -- filename`

2. **Group Changes by Intent**:
   - **Documentation**: .md, .rst, .txt files and docs/ folder
   - **Tests**: files with test_ prefix or in tests/ folder  
   - **Configuration**: config, setup, build, requirements, pyproject files
   - **Bug Fixes**: files with 'fix' or 'bug' in recent commit messages
   - **Features**: new .py files or files with significant additions
   - **Refactoring**: existing .py files with modifications

3. **Check Changelog Integration**:
   - Read CHANGELOG.md to see if today's changes are documented
   - Look for any existing entries for today's date
   - Identify changes that aren't documented yet

4. **Find Related Requirement IDs**:
   - Scan recent git commits for ID patterns: FEAT-XXX, FIX-XXX, TASK-XXX, DOC-XXX, TEST-XXX
   - Check if any files contain requirement IDs in their content
   - Match changes to existing requirement IDs if possible

5. **Create Commit Plan**:
   - Group files by conventional commit types: feat, fix, docs, test, chore, refactor, perf
   - Propose commit messages in format: "type(scope): description"
   - Link to requirement IDs where found
   - Prioritize safest commits first (docs, tests, config, then implementation)

6. **Execute Commits**:
   - Start with documentation changes (safest)
   - Then test changes
   - Then configuration/build changes  
   - Finally implementation changes (may need manual review)
   - Use conventional commit format with requirement ID linking

7. **Update Changelog**:
   - Add today's section if it doesn't exist
   - Include all commits made during git debt resolution
   - Note that timing may be approximate due to debt cleanup

8. **Verification**:
   - Check that repository is clean after commits
   - Show recent commit history
   - List any remaining uncommitted changes that need manual attention

Remember: Group related changes logically, use conventional commit format, link to requirement IDs, and update changelog automatically.