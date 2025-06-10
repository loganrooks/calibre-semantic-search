# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 2025-06-09

### Added
- SPARC-V-L³ development protocol for systematic development
- Triple-log system (ACTIVITY_LOG, FEEDBACK_LOG, SELF_ANALYSIS_LOG)
- Comprehensive ARCHITECTURE.md documenting MVP pattern
- DEVELOPMENT_GUIDE.md with mandatory workflows
- Destructive Operations Protocol to prevent data loss

### Changed
- Reorganized project structure with proper archive system
- Moved scattered test files to appropriate test directories
- Established single source of truth for documentation

### Fixed
- N/A (fixes pending in Phase 2)

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