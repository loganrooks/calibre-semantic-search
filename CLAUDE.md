# Calibre Semantic Search Plugin - Development Guide

## 📚 Custom Commands Available

This project includes Claude Code custom commands for both project-specific and general development workflows with **integrated git management and requirement tracking**:

### Project-Specific Commands
- `/project:status` - Check current status and priorities
- `/project:wire-component <name>` - Wire component into Calibre
- `/project:debug-integration <component>` - Debug integration issues
- `/project:find-placeholders [area]` - Find unimplemented functionality
- `/project:resume-work` - Resume with context check

### General Development Workflow Commands
- `/project:launch-task <description>` - Full SPARC+TDD orchestration with git integration
- `/project:sparc-analyze <problem>` - Thorough SPARC analysis
- `/project:architect <feature>` - Design architecture
- `/project:create-spec <feature>` - Create detailed specifications with requirement tracking
- `/project:tdd-cycle <feature>` - Complete TDD implementation with git integration
- `/project:verify-implementation <feature>` - Verify against specs
- `/project:code-review [component]` - Automated code review
- `/project:health-check` - Workspace health assessment
- `/project:tech-debt [area]` - Technical debt analysis

### Git & Requirement Management (NEW)
- `/project:git-debt` - Organize uncommitted changes into logical conventional commits
- `/project:generate-requirement-id <description>` - Generate unique trackable requirement ID
- `/project:create-pr` - Create pull request with proper requirement linking

**Example**: `/project:launch-task "Add search filters"` runs complete workflow from analysis to implementation with automatic requirement ID generation and git management.

**Tip**: Use `/project:list-commands` to see all 26 available commands with descriptions.

## Project Overview
This is a Calibre plugin that adds AI-powered semantic search capabilities specifically optimized for philosophical and academic texts. It uses vector embeddings to enable conceptual similarity search beyond traditional keyword matching.

**Current Status:** Critical Integration Phase - Components built but not connected (v0.9.0)  
**Target Release:** v1.0.0 (4-6 hours of integration work remaining)

## 🔧 CURRENT ACTIVE TASK

**Task**: Wire implemented components into live Calibre interface

**Recent Work (2025-06-03)**:
- ✅ Enhanced Index Manager with multi-index display
- ✅ Added embedding configuration UI (model selection, dimensions)
- ✅ Fixed database initialization issues
- ✅ Created comprehensive TDD plan for chunking strategies
- ❌ Search engine still not wired to UI
- ❌ Theme manager not applied to dialogs

**Next Steps**:
1. Wire SearchEngine to search_dialog.py:perform_search()
2. Apply ThemeManager stylesheet to search dialog
3. Add menu item for IndexManagerDialog
4. Connect ViewerIntegration to context menu

## Important: Specification Documents
This project is based on comprehensive specification documents located in `semantic_docs/`:
- **calibre-semantic-spec-01.md**: Executive Summary & Quick Start Guide
- **calibre-semantic-spec-02.md**: Core Requirements Specification
- **calibre-semantic-spec-03.md**: Architecture Design Document
- **calibre-semantic-spec-04.md**: Calibre Integration Guide
- **calibre-semantic-spec-05.md**: Testing & Verification Specification
- **calibre-semantic-spec-06.md**: Development Workflow Guide
- **calibre-semantic-spec-07.md**: Risk Analysis & Mitigation Strategy

## Implementation Status

### ✅ Completed Components (Built & Tested)
- **Core Services** (98% spec compliance)
  - Multi-provider embedding service with LiteLLM
  - Philosophy-optimized search engine
  - Intelligent text processing
  - Multi-index support per book
  
- **User Interface** (95% spec compliance)
  - Professional search dialog
  - Complete IndexManagerDialog with CRUD
  - Dynamic ThemeManager
  - ViewerIntegration with navigation
  
- **Data Layer** (100% spec compliance)
  - SQLite with sqlite-vec
  - Repository pattern
  - Multi-level caching

- **Testing Suite** (275+ tests passing)
  - Unit, integration, performance tests
  - Complete test isolation

### 🔧 Critical Integration Gaps
See `/critical-issues` for detailed list. Main issues:
1. SearchEngine not wired to search dialog
2. ThemeManager not applied to UI
3. IndexManagerDialog not accessible
4. ViewerIntegration not called
5. Plugin system not integrated

## Key Technologies
- **Language**: Python 3.8+
- **UI Framework**: Qt 5.12+ (via Calibre)
- **Vector Database**: SQLite with sqlite-vec extension
- **Embedding Models**: Multiple providers via LiteLLM
- **Plugin System**: Calibre's InterfaceAction framework

## Development Commands

### Testing
```bash
pytest                          # Run all tests
pytest --cov=calibre_plugins    # With coverage
pytest tests/unit -v            # Specific category
```

### Building
```bash
python scripts/build_plugin.py  # Build plugin ZIP
calibre-customize -a calibre-semantic-search.zip  # Install
```

### Running
```bash
calibre-debug -g               # Run with debug output
calibre-debug -g 2>&1 | tee calibre.log  # Capture output
```

## Development Guidelines

### Critical Rules
1. **NO ASSUMPTIONS**: Always verify with `calibre-debug -c` before claiming something doesn't work
2. **READ FIRST**: Use Read tool to examine files before modifying
3. **TDD DISCIPLINE**: Red-Green-Refactor with actual test execution
4. **VERIFY INTEGRATION**: Test in live Calibre, not just unit tests

### Common Pitfalls
- NumPy not available → Use VectorOps pure Python implementation
- Use `qt.core` imports, not PyQt5 directly
- Use print() for debugging, not logger.info() (for Calibre visibility)
- Check if services are initialized before use

### Documentation Updates
After each work session, update:
- PROJECT_STATUS.md - Current status and completion
- CHANGELOG.md - What was added/fixed/changed
- Run `/project:update-docs` for guided updates

### Important Lessons Learned

#### Implementation vs Integration (2025-06-02)
- **Discovery**: Components can be fully built and tested but not visible to users
- **Lesson**: Always verify user-facing functionality, not just unit tests
- **Prevention**: Test in live Calibre after implementing

#### File Naming Conflicts
- **Problem**: `ui.py` conflicts with Calibre internals
- **Solution**: Renamed to `interface.py`
- **Prevention**: Check Calibre namespace before naming

#### Pure Python Dependencies
- **Problem**: NumPy not available in Calibre
- **Solution**: Created VectorOps pure Python implementation
- **Prevention**: Only use pure Python libraries

## Performance Targets
- Search latency: <100ms for 10,000 books ✅
- Indexing speed: ≥50 books/hour ✅
- Memory usage: <500MB during operation ✅
- UI responsiveness: <33ms for result display ✅

## Testing Philosophy
- Test-Driven Development (TDD) - see `/tdd-requirements`
- Bug-first methodology for fixes
- >80% code coverage maintained
- 275+ comprehensive tests passing

## Security Considerations
- API keys stored encrypted using Calibre's password storage
- No telemetry without explicit consent
- All network requests use HTTPS
- Input validation on all user data

## Platform Notes
- **Windows**: Handle long paths with `\\?\` prefix
- **macOS**: Test on both Intel and Apple Silicon
- **Linux**: Ensure sqlite-vec loads correctly

## Quick Reference

### Current Git Status
- Branch: `feature/ui-backend-integration`
- Version: 0.9.0 → 1.0.0
- Next Release: v1.0.0

### Critical Files
- `interface.py` - Main plugin entry (has integration gaps)
- `search_dialog.py` - Search UI (needs SearchEngine wiring)
- `index_manager_dialog.py` - Index management (needs menu access)
- `theme_manager.py` - UI theming (needs application to dialogs)

### Next Actions
1. **Wire SearchEngine** (2-3 hours) - `/critical-issues`
2. **Apply ThemeManager** (1-2 hours)
3. **Add Index Manager menu** (1 hour)
4. **Connect Viewer Integration** (1-2 hours)

## Contact and Resources
- Calibre Plugin Development: https://manual.calibre-ebook.com/creating_plugins.html
- SQLite-vec Documentation: https://github.com/asg017/sqlite-vec
- Project Specifications: `semantic_docs/` directory
- Claude Code Issues: https://github.com/anthropics/claude-code/issues

---
*Use PROJECT_STATUS.md as the single source of truth for detailed status. Update after each work session.*