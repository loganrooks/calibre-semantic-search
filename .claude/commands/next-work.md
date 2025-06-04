Identify the next suite of work items by scanning TODOs, analyzing project status, and preparing comprehensive context for the next development cycle

## NEXT WORK IDENTIFICATION WORKFLOW

### 1. Scan for Explicit TODOs
**Find All TODO/FIXME Comments**:
- Search codebase for TODO, FIXME, XXX, HACK, NOTE comments using `grep -r`
- Categorize by file type: source code, tests, documentation, configuration
- Extract context around each TODO (5 lines before/after)
- Check if TODOs have dates, priority markers, or assignee information
- Identify which TODOs are in active vs deprecated code paths

### 2. Analyze Project Documentation
**Cross-Reference Multiple Sources**:
- Read PROJECT_STATUS.md for stated current priorities and completion status
- Read CHANGELOG.md to understand recent work patterns and upcoming features
- Check CLAUDE.md for current active tasks and next steps
- Scan README.md for any roadmap or planned features
- Look for any specification documents in docs/ or semantic_docs/
- Check for any IMPLEMENTATION_PLAN files

### 3. Verify Documentation vs Reality
**Cross-Reference Stated Status with Code**:
- For each "completed" item in PROJECT_STATUS.md, verify actual implementation exists
- For each "in progress" item, check if code changes match the description
- For each "planned" item, see if any preliminary work has started
- Identify discrepancies between documented status and actual code state
- Flag items marked as complete but missing tests or integration

### 4. Infer Next Work from Patterns
**Intelligent Priority Analysis**:
- Analyze git commit history for development momentum and focus areas
- Look at test coverage gaps using `pytest --cov` if available
- Identify incomplete feature implementations (half-built UI, missing backend)
- Find integration points that need wiring (based on import analysis)
- Detect architectural inconsistencies or missing abstractions
- Check for performance bottlenecks or optimization opportunities

### 5. Categorize and Prioritize Work Items
**Organize by Type and Urgency**:
- **Critical Bugs**: Issues that break core functionality
- **Integration Gaps**: Implemented components not wired together
- **Missing Features**: Planned features not yet started
- **Technical Debt**: Code quality issues, refactoring needs
- **Testing Gaps**: Missing tests for implemented features
- **Documentation**: Outdated docs, missing specifications
- **Performance**: Optimization opportunities
- **User Experience**: UI/UX improvements needed

### 6. Update Outdated TODOs
**TODO Maintenance**:
- Flag TODOs that reference completed work
- Update TODOs with new context or changed priorities
- Add dates to undated TODOs for tracking
- Convert vague TODOs into specific, actionable items
- Link TODOs to requirement IDs if system exists
- Suggest removing TODOs that are no longer relevant

### 7. Assess Current Context
**Prepare Development Environment Context**:
- Check git branch status and any uncommitted changes
- Verify test suite is passing and build is clean
- Assess development environment health
- Check for any blocking dependencies or external factors
- Review recent development velocity and capacity

### 8. Generate Next Work Recommendations
**Comprehensive Work Planning**:
- Rank work items by: Impact, Effort, Dependencies, Risk
- Suggest optimal sequence for implementation
- Identify work that can be done in parallel
- Recommend appropriate development approach (SPARC+TDD, bug-first TDD, refactoring)
- Estimate complexity and time requirements
- Flag work that needs additional planning or research

### 9. Prepare SPARC+TDD Context
**Set Up for Next Development Cycle**:
- For highest priority item, gather all relevant context:
  - Related code files and their current state
  - Existing tests and coverage gaps
  - Design documents or specifications
  - Integration points and dependencies
  - User stories or acceptance criteria
- Suggest whether to use `/project:launch-task`, `/project:fix-bug`, or other workflow
- Pre-generate requirement ID if needed: `/project:generate-requirement-id`
- Identify any prerequisites that need completion first

### 10. Create Action Plan
**Immediate Next Steps**:
- List the top 3-5 work items with clear descriptions
- For #1 priority item, provide:
  - Specific files to examine
  - Relevant context to gather
  - Suggested approach (feature, fix, refactor, etc.)
  - Command to run to start the work
- For remaining items, provide brief action summary
- Flag any blockers or dependencies that need resolution first

## Output Format:

```
🎯 NEXT WORK ANALYSIS - [Date]

📋 TODO SCAN RESULTS:
- [X] TODOs found in codebase
- [X] Documentation analysis complete  
- [X] Status verification complete

🚨 CRITICAL ISSUES:
1. [Issue description] - [File/location] - [Priority: High/Medium/Low]

🔗 INTEGRATION GAPS:
1. [Gap description] - [Files involved] - [Effort estimate]

📝 DOCUMENTATION DISCREPANCIES:
1. [Status vs Reality mismatch] - [Correction needed]

⭐ TOP PRIORITY RECOMMENDATIONS:

#1: [Work Item Title]
Type: [Feature/Fix/Refactor/Test/Docs]
Files: [List of relevant files]
Effort: [Time estimate]
Command: `/project:[suggested-command] "[description]"`
Context: [Key information needed]

#2: [Work Item Title]
[Similar format]

🧪 SUGGESTED APPROACH:
- Branch: feature/[type]-[description] or fix/[bug-description]
- Methodology: [SPARC+TDD/Bug-first TDD/Refactoring]
- Prerequisites: [Any blockers to resolve first]

🔄 NEXT COMMAND TO RUN:
[Specific command with arguments to start the work]
```

Remember: This command provides a comprehensive foundation for informed development decisions and ensures no important work is overlooked.