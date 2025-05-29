# Changelog

All notable changes to the Calibre Semantic Search Plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial plugin architecture with Calibre integration
- Philosophy-aware text chunking with multiple strategies
  - Paragraph-based chunking with intelligent merging
  - Sliding window chunking with configurable overlap
  - Philosophical chunking that preserves arguments and concepts
- Multi-provider embedding service
  - Support for Vertex AI, OpenAI, and Cohere
  - Automatic fallback between providers
  - Embedding caching for performance
- Advanced search modes
  - Semantic search for conceptual similarity
  - Dialectical search for finding oppositions
  - Genealogical search for tracing concept evolution
- Comprehensive search UI
  - Query input with real-time validation
  - Search scope selection (library, book, author, tag)
  - Similarity threshold adjustment
  - Result cards with book metadata and actions
- Viewer integration
  - Context menu for searching selected text
  - Quick search from highlighted passages
- Data layer implementation
  - SQLite database with sqlite-vec extension support
  - Repository pattern for clean data access
  - Multi-level caching (TTL and LRU)
- Configuration system
  - API key management
  - Search preferences
  - Performance tuning options
  - UI customization
- Indexing service
  - Batch processing for efficiency
  - Progress tracking
  - Error handling and recovery

### Technical Details
- Python 3.8+ compatibility
- Qt 5.12+ for UI components
- Async/await support for non-blocking operations
- Comprehensive error handling and logging
- Test-driven development approach

## [0.1.0] - TBD

### Notes
- First alpha release for testing
- Requires Calibre 5.0 or higher
- SQLite-vec extension recommended for optimal performance