Generate a unique requirement ID for tracking: "$ARGUMENTS". Follow these steps:

1. **Check Existing ID System**:
   - Look for `.requirements/id_registry.md` to see existing ID tracking
   - Scan recent git commits for ID patterns: FEAT-XXX, FIX-XXX, TASK-XXX, DOC-XXX, TEST-XXX, PERF-XXX, REFACTOR-XXX, CHORE-XXX
   - Find the highest number used for each ID type

2. **Classify the Requirement Type**:
   Based on keywords in "$ARGUMENTS", determine the appropriate type:
   - **FEAT**: New features (keywords: add, new, create, implement, feature, enhance)
   - **FIX**: Bug fixes (keywords: fix, bug, error, issue, broken, crash, fail)
   - **DOC**: Documentation (keywords: doc, document, readme, guide, manual, explain)
   - **TEST**: Testing (keywords: test, testing, coverage, spec, verify)
   - **PERF**: Performance (keywords: performance, optimize, speed, memory, cpu)
   - **REFACTOR**: Code refactoring (keywords: refactor, clean, reorganize, restructure)
   - **CHORE**: Maintenance (keywords: build, deploy, config, setup, dependencies, maintenance)
   - **TASK**: General tasks (keywords: task, story, work, complete, do)

3. **Generate Next ID Number**:
   - Find all existing IDs of the determined type in git history and documentation
   - Calculate the next sequential number (formatted as 3 digits: 001, 002, etc.)
   - Create the full ID: TYPE-XXX (e.g., FEAT-005)

4. **Create ID Registry System** (if it doesn't exist):
   - Create `.requirements/` directory
   - Create `id_registry.md` with table format tracking all IDs
   - Include columns: ID, Type, Description, Status, Created, Assignee, Related

5. **Register the New ID**:
   - Add entry to the ID registry table
   - Mark status as "Draft"
   - Include today's date and the requirement description

6. **Create Detailed Requirement Document**:
   - Create `.requirements/[ID].md` with full specification template
   - Include sections: Description, Acceptance Criteria, Technical Requirements, Dependencies, Testing Strategy, Definition of Done, Progress Log
   - Leave template fields for future completion during planning

7. **Update Project Tracking**:
   - Add to `.requirements/backlog.md` if it exists (create if not)
   - Add to PROJECT_STATUS.md if it has a requirements tracking section

8. **Provide Integration Instructions**:
   - Show how to use the ID in commit messages: "type(scope): description\n\nImplements: [ID]"
   - Explain branch naming: "feature/[ID]-short-description"
   - List which other commands should reference this ID

Output the generated ID clearly and explain how it should be used throughout the development workflow for full requirement traceability.