# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 2025-06-10

### Added
- SPARC-V-L³ development protocol for systematic development
- Triple-log system (ACTIVITY_LOG, FEEDBACK_LOG, SELF_ANALYSIS_LOG)
- Comprehensive ARCHITECTURE.md documenting MVP pattern
- DEVELOPMENT_GUIDE.md with mandatory workflows
- Destructive Operations Protocol to prevent data loss
- Context initialization protocol in CLAUDE.md for consistent decision-making
- Git workflow decision matrix for context-appropriate merge strategies
- SimpleLocationCombo widget for Calibre Qt compatibility

### Changed
- Reorganized project structure with proper archive system
- Moved scattered test files to appropriate test directories
- Established single source of truth for documentation
- Refactored ConfigWidget to MVP pattern (824→685 lines, 17% reduction)
- Updated location dropdown implementation for Qt enum compatibility

### Fixed
- Location dropdown focus-stealing bug preventing continuous typing
- Qt enum access issues with QCompleter.PopupCompletion → QCompleter.CompletionMode.PopupCompletion
- Circular import issues in config module
- ThreadedJob integration with Calibre job system
- AsyncMock errors in EPUB integration tests
- Missing IndexDetector module for UI components

### Security
- N/A

## [0.9.0] - 2025-06-07

### Added
- Focus-stealing fix for location dropdown
- Enhanced location dropdown UX with smart typing patterns
- Comprehensive test failure documentation

### Fixed
- Dropdown focus-stealing preventing continuous typing
- Circular import in config module
- Missing parser methods preventing location dropdown UI

### Known Issues
- EPUB indexing returns 0 books
- ThreadedJob import breaking Calibre integration
- Missing index_detector module
- Async mocking errors in tests
- Config UI features not yet implemented

## [0.8.0] - Previous releases
See archive/pre_refactor_20250609/CHANGELOG.md for historical entries