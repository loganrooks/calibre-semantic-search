# Claude Code Custom Commands for Calibre Semantic Search

This directory contains custom slash commands for Claude Code to help with development tasks. Commands are divided into project-specific and general development workflows.

## Project-Specific Commands

### Development Workflow
- `/project:status` - Check project status and show what needs to be done next
- `/project:wire-component <name>` - Wire a component into the live Calibre interface
- `/project:update-docs <work-done>` - Update documentation after completing work

### Debugging & Testing
- `/project:debug-integration <component>` - Debug why a component isn't working in Calibre
- `/project:find-placeholders [area]` - Find all placeholders and unimplemented functionality
- `/project:test-component <name>` - Run tests for a specific component
- `/project:fix-bug <description>` - Fix a bug using bug-first TDD methodology

### Knowledge & Continuity
- `/project:check-knowledge <issue>` - Search knowledge base for known solutions
- `/project:resume-work` - Check context and status when resuming development
- `/project:quick-check [component]` - Quick health check of specific area or general

## General Development Workflow Commands

### SPARC+TDD Orchestration
- `/project:launch-task <description>` - Launch complete SPARC+TDD workflow with anti-hallucination checks
- `/project:sparc-analyze <problem>` - Perform thorough SPARC analysis
- `/project:architect <feature>` - Design architecture following best practices
- `/project:create-spec <feature>` - Create detailed specifications

### Implementation & Verification
- `/project:tdd-cycle <feature>` - Run complete TDD cycle with verification checkpoints
- `/project:tdd-implement <feature>` - Implement using strict TDD (simplified version)
- `/project:verify-implementation <feature>` - Verify implementation matches specifications

### Code Quality & Review
- `/project:code-review [component]` - Automated code review with actionable feedback
- `/project:health-check` - Comprehensive workspace health assessment
- `/project:tech-debt [area]` - Analyze technical debt and create remediation plan

## Usage Examples

### Project-Specific Examples
```
/project:status
# Shows current version, completion %, critical issues, and next steps

/project:wire-component SearchEngine  
# Shows how to connect SearchEngine to the UI

/project:debug-integration IndexManager
# Helps debug why IndexManager isn't showing in menu

/project:fix-bug "Copy Citation throws error"
# Creates test first, then fixes the bug
```

### General Workflow Examples
```
/project:launch-task "Add user authentication to API endpoints"
# Runs complete SPARC analysis → specs → architecture → TDD implementation

/project:sparc-analyze "Performance bottleneck in search results"
# Analyzes situation, problems, alternatives, recommendations

/project:tdd-cycle "autocomplete widget"  
# Guides through systematic RED-GREEN-REFACTOR cycles

/project:code-review search_dialog.py
# Performs automated review with complexity, security, style checks

/project:health-check
# Assesses build, tests, dependencies, docs, security, tech debt

/project:tech-debt core/
# Analyzes technical debt in core module, creates remediation plan
```

## Command Structure

Commands follow this pattern:
1. Understand the current state
2. Find relevant code/issues
3. Show specific changes needed
4. Verify the solution
5. Update documentation if needed

## Adding New Commands

Create a new `.md` file in this directory:
- Filename becomes the command (e.g., `analyze.md` → `/project:analyze`)
- Content should be instructions to Claude, not documentation
- Use `$ARGUMENTS` to accept parameters
- Focus on actionable steps

## Tips

- Commands should be specific to this project's needs
- Include verification steps to ensure changes work
- Reference specific files and patterns used in this codebase
- Include commands for building and testing the plugin