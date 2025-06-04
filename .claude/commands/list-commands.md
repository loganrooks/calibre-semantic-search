List all available custom commands with brief descriptions.

## Available Custom Commands

### 📋 Project Management & Status
- `/project:status` - Check current project status and priorities
- `/project:next-work` - **COMPREHENSIVE**: Identify next TODOs, verify project state, prepare context for next cycle
- `/project:resume-work` - Resume work with context check
- `/project:update-docs <work>` - Update documentation after changes

### 🔧 Development Workflow Orchestration
- `/project:launch-task <description>` - **MAIN ORCHESTRATOR**: Full SPARC+TDD workflow with git integration and requirement tracking
- `/project:sparc-analyze <problem>` - Perform SPARC analysis (Situation, Problem, Alternatives, Result, Consequences)
- `/project:architect <feature>` - Design architecture following SOLID principles
- `/project:create-spec <feature>` - Create detailed functional and technical specifications with requirement tracking

### 🧪 Test-Driven Development
- `/project:tdd-cycle <feature>` - Complete TDD cycle with verification and git integration
- `/project:tdd-implement <feature>` - Implement using strict TDD (simplified)
- `/project:test-component <name>` - Run tests for specific component
- `/project:verify-implementation <feature>` - Verify implementation matches specifications

### 🐛 Debugging & Bug Fixes
- `/project:debug-integration <component>` - Debug Calibre integration issues
- `/project:fix-bug <description>` - Fix bugs using bug-first TDD with requirement tracking
- `/project:find-placeholders [area]` - Find unimplemented functionality
- `/project:quick-check [component]` - Quick health check of specific area

### 📊 Code Quality & Analysis
- `/project:code-review [component]` - Automated code review with metrics
- `/project:health-check` - Comprehensive workspace health assessment
- `/project:tech-debt [area]` - Analyze technical debt and create remediation plan

### 🔌 Integration & Wiring (Project-Specific)
- `/project:wire-component <name>` - Wire component into Calibre interface
- `/project:check-knowledge <issue>` - Search knowledge base for known solutions

### 🗂️ Git & Requirement Management ⭐ NEW
- `/project:git-debt` - Organize uncommitted changes into logical conventional commits
- `/project:generate-requirement-id <description>` - Generate unique trackable requirement ID
- `/project:create-pr` - Create pull request with proper requirement linking and conventional format

## Quick Start Examples

**Identifying next work:**
```
/project:next-work
```

**Starting a new feature:**
```
/project:launch-task "Add export functionality for search results"
```

**Managing git debt:**
```
/project:git-debt
```

**Creating requirement tracking:**
```
/project:generate-requirement-id "Add user authentication"
```

**Creating pull request:**
```
/project:create-pr
```

**Debugging an issue:**
```
/project:debug-integration SearchDialog
```

**Checking project health:**
```
/project:health-check
```

**Resuming work:**
```
/project:resume-work
```

## Command Categories by Use Case

### "I want to build something new"
1. `/project:launch-task` - Start here for full workflow
2. `/project:sparc-analyze` - Or start with analysis only
3. `/project:create-spec` - Or jump to specifications

### "I need to fix something"
1. `/project:fix-bug` - For known bugs
2. `/project:debug-integration` - For integration issues
3. `/project:find-placeholders` - To find what's not implemented

### "I want to improve code quality"
1. `/project:code-review` - Get automated review
2. `/project:health-check` - Check overall health
3. `/project:tech-debt` - Find and plan debt reduction

### "I'm continuing work"
1. `/project:next-work` - **BEST START**: Comprehensive analysis of what to do next
2. `/project:resume-work` - Get oriented with existing work
3. `/project:status` - Check project status
4. `/project:quick-check` - Verify specific components

### "I need to manage git and requirements" ⭐ NEW
1. `/project:git-debt` - Clean up uncommitted changes
2. `/project:generate-requirement-id` - Create trackable requirements
3. `/project:create-pr` - Submit properly formatted pull request

## New Git Integration Features ⭐

All workflow commands now include:
- **Automatic requirement ID generation** for full traceability
- **Git debt management** to prevent accumulation of uncommitted changes
- **Conventional commit formatting** with requirement linking
- **Branch management** following feature/[ID]-description pattern
- **Pull request integration** with proper documentation

Total Commands: **26** (4 new commands: 3 git management + 1 comprehensive work analysis)

Remember: Commands are designed to enforce best practices, prevent common AI coding pitfalls through verification checkpoints, and maintain clean git history with full requirement traceability.