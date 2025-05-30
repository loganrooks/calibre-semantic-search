# Calibre Semantic Search Plugin - Development Guide

## Project Overview
This is a Calibre plugin that adds AI-powered semantic search capabilities specifically optimized for philosophical and academic texts. It uses vector embeddings to enable conceptual similarity search beyond traditional keyword matching.

## Important: Specification Documents
This project is based on comprehensive specification documents located in `semantic_docs/`:
- **calibre-semantic-spec-01.md**: Executive Summary & Quick Start Guide
- **calibre-semantic-spec-02.md**: Core Requirements Specification (FR, NFR, PRR)
- **calibre-semantic-spec-03.md**: Architecture Design Document
- **calibre-semantic-spec-04.md**: Calibre Integration Guide
- **calibre-semantic-spec-05.md**: Testing & Verification Specification
- **calibre-semantic-spec-06.md**: Development Workflow Guide (SPARC methodology)

**⚠️ IMPORTANT**: Always refer to these specification documents for detailed requirements, architectural decisions, and implementation guidelines. This CLAUDE.md provides a quick reference, but the specs are the authoritative source.

## Key Technologies
- **Language**: Python 3.8+
- **UI Framework**: Qt 5.12+ (via Calibre)
- **Vector Database**: SQLite with sqlite-vec extension
- **Embedding Models**: Vertex AI (primary), OpenAI, Cohere, local models (fallbacks)
- **Plugin System**: Calibre's InterfaceAction framework

## Project Structure
```
calibre-semantic-search/
├── calibre_plugins/semantic_search/  # Main plugin code
│   ├── core/                        # Business logic (embedding, search, text processing)
│   ├── data/                        # Data access layer (database, repositories, cache)
│   ├── ui/                          # User interface (dialogs, widgets, viewer integration)
│   └── resources/                   # Icons, translations
├── tests/                           # Test suite
│   ├── unit/                        # Component tests
│   ├── integration/                 # Integration tests
│   ├── philosophical/               # Domain-specific tests
│   └── performance/                 # Performance benchmarks
├── docs/                            # Documentation
└── scripts/                         # Build and utility scripts
```

## Development Commands

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=calibre_plugins.semantic_search --cov-report=html

# Run specific test categories
pytest tests/unit -v
pytest tests/integration -v
pytest tests/philosophical -v
pytest tests/performance --benchmark-only

# Run linting and type checking
black calibre_plugins/
isort calibre_plugins/
mypy calibre_plugins/
```

### Building
```bash
# Build plugin ZIP file
python scripts/build_plugin.py

# Install to Calibre for testing
calibre-customize -a calibre-semantic-search.zip
```

### Running Calibre with plugin
```bash
# Run Calibre in debug mode
calibre-debug -g

# Run with console output
calibre-debug -g 2>&1 | tee calibre.log
```

## Version Control Best Practices

### Branch Strategy
- `main` - Stable releases only
- `develop` - Integration branch for features
- `feature/*` - Individual feature branches
- `bugfix/*` - Bug fix branches
- `release/*` - Release preparation branches

### Commit Message Convention
Follow conventional commits format:
```
type(scope): subject

body (optional)

footer (optional)
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc)
- `refactor`: Code refactoring
- `test`: Test additions or changes
- `chore`: Build process or auxiliary tool changes

Examples:
```
feat(search): add dialectical search mode
fix(ui): correct context menu positioning in viewer
docs(api): update embedding service documentation
test(philosophy): add Heidegger concept tests
```

### Git Workflow

#### Branch Structure
- **master**: Production-ready code only. Protected branch.
- **develop**: Integration branch for features. All feature branches merge here.
- **feature/\***: Feature branches for new functionality
- **bugfix/\***: Bug fix branches
- **hotfix/\***: Emergency fixes that go directly to master

#### Development Flow

1. **Starting New Work**:
   ```bash
   # Always start from updated develop
   git checkout develop
   git pull origin develop
   
   # Create feature branch with descriptive name
   git checkout -b feature/repository-tests
   # OR
   git checkout -b bugfix/search-performance
   ```

2. **During Development**:
   ```bash
   # Make atomic commits with clear messages
   git add -p  # Review changes piece by piece
   git commit -m "feat(core): implement repository pattern for data access"
   
   # Push regularly to backup work
   git push origin feature/repository-tests
   ```

3. **Before Creating PR**:
   - Run all tests: `pytest`
   - Run linting: `black . && isort .`
   - Review changes: `git diff develop...HEAD`
   - Update documentation if needed
   - Ensure commits follow conventional format

4. **Pull Request Guidelines**:
   - Create PR from feature branch to `develop` (never to master)
   - PR title should follow conventional commit format
   - PR description must include:
     - What changes were made and why
     - Which specs/requirements are addressed
     - Testing approach used
     - Any breaking changes
   - Must pass all CI checks
   - Must have test coverage for new code
   - Requires at least one review

5. **After PR Approval**:
   ```bash
   # Merge via GitHub PR interface (squash if many commits)
   # Delete feature branch after merge
   git checkout develop
   git pull origin develop
   git branch -d feature/repository-tests
   ```

6. **Release Process**:
   ```bash
   # Only when develop is stable and tested
   git checkout master
   git pull origin master
   git merge develop
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin master --tags
   ```

#### Branch Naming Conventions
- feature/descriptive-name (e.g., feature/dialectical-search)
- bugfix/issue-description (e.g., bugfix/embedding-memory-leak)
- hotfix/critical-issue (e.g., hotfix/search-crash)

#### Commit Message Examples
```
feat(search): add genealogical search mode for concept evolution
fix(ui): prevent dialog overflow on small screens
test(philosophy): add Hegel dialectical concept tests
docs(api): update embedding service API documentation
refactor(core): extract chunking strategies to separate classes
perf(search): optimize vector similarity calculations
chore(deps): update numpy to 1.24.0
```

#### IMPORTANT: Never commit directly to master or develop!

### Version Tagging
Use semantic versioning: `MAJOR.MINOR.PATCH`
```bash
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

## Important Architectural Decisions

These decisions are detailed in `semantic_docs/calibre-semantic-spec-03.md`:

1. **Plugin-Based Architecture**: All functionality via Calibre's plugin system, no core modifications (see ADR-001 in spec-03)
2. **SQLite with sqlite-vec**: For vector storage instead of external vector DB (see ADR-002 in spec-03)
3. **Multi-Provider Embeddings**: Fallback chain for reliability (see ADR-003 in spec-03)
4. **Hybrid Chunking**: Smart text chunking that preserves philosophical arguments (see FR-013 in spec-02)
5. **Philosophy-Aware Search**: Special modes for dialectical and genealogical search (see PRR-010/011 in spec-02)

## Performance Targets

From `semantic_docs/calibre-semantic-spec-02.md` (NFR section):
- Search latency: <100ms for 10,000 books (NFR-001)
- Indexing speed: ≥50 books/hour (NFR-002)
- Memory usage: <500MB during operation (NFR-003)
- Storage: ~4.4GB per 1,000 books with 768-dim embeddings (NFR-004)

## Key Requirements

Core requirements from the specifications:
- **FR-001**: Basic semantic search with >0.7 similarity (spec-02)
- **FR-010**: Multi-provider embedding generation (spec-02)
- **FR-020**: Viewer context menu integration (spec-02)
- **NFR-001**: Search response time targets (spec-02)
- **PRR-001**: Complex philosophical concept support (spec-02)

For complete requirements, see `semantic_docs/calibre-semantic-spec-02.md`

## Testing Philosophy
- Test-Driven Development (TDD)
- Write failing test first
- Implement minimal code to pass
- Refactor with confidence
- Maintain >80% code coverage

## Common Tasks

### Adding a New Embedding Provider
1. Create provider class in `core/embedding_providers/`
2. Implement `IEmbeddingProvider` interface
3. Add to provider chain in `EmbeddingService`
4. Write unit tests
5. Update configuration options

### Adding a New Search Mode
1. Define mode in `SearchMode` enum
2. Implement search logic in `SearchEngine`
3. Add UI option in `SearchDialog`
4. Write philosophical correctness tests
5. Document the mode's purpose

### Debugging Tips
- Enable Calibre debug mode: `calibre-debug -g`
- Check logs in: `~/.config/calibre/plugins/semantic_search.log`
- Use Qt Creator for UI debugging
- Profile with: `python -m cProfile -o profile.stats`

## Code Style Guidelines
- Follow PEP 8
- Use type hints for all functions
- Document with docstrings (Google style)
- Keep functions under 50 lines
- Prefer composition over inheritance

## Security Considerations
- API keys stored encrypted using Calibre's password storage
- No telemetry without explicit consent
- All network requests use HTTPS
- Input validation on all user data

## Platform-Specific Notes
- **Windows**: Handle long paths with `\\?\` prefix
- **macOS**: Test on both Intel and Apple Silicon
- **Linux**: Ensure sqlite-vec loads correctly

## Release Checklist
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Version bumped in `__init__.py`
- [ ] CHANGELOG.md updated
- [ ] Git tag created
- [ ] Plugin ZIP built and tested
- [ ] GitHub release created

## Specification Quick Reference

When working on specific features, consult:
- **Requirements**: See spec-02 for all FR (Functional), NFR (Non-Functional), and PRR (Philosophical Research) requirements
- **Architecture**: See spec-03 for component design, data flow, and architectural decisions
- **Calibre Integration**: See spec-04 for plugin hooks, viewer integration, and platform considerations
- **Testing**: See spec-05 for test categories, philosophical test cases, and acceptance criteria
- **Development Process**: See spec-06 for SPARC methodology and workflow guidelines

## Contact and Resources
- Calibre Plugin Development: https://manual.calibre-ebook.com/creating_plugins.html
- SQLite-vec Documentation: https://github.com/asg017/sqlite-vec
- Project Specifications: `semantic_docs/` directory
- Project Issues: GitHub Issues (when repository is created)