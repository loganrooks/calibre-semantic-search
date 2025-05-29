# Calibre Semantic Search Plugin - Development Guide

## Project Overview
This is a Calibre plugin that adds AI-powered semantic search capabilities specifically optimized for philosophical and academic texts. It uses vector embeddings to enable conceptual similarity search beyond traditional keyword matching.

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
1. **Feature Development**:
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/semantic-chunking
   # Make changes
   git add -p  # Review changes piece by piece
   git commit -m "feat(core): implement semantic chunking algorithm"
   git push origin feature/semantic-chunking
   # Create PR to develop branch
   ```

2. **Before Committing**:
   - Run tests: `pytest`
   - Run linting: `black . && isort .`
   - Review changes: `git diff --staged`

3. **Pull Request Guidelines**:
   - Must pass all CI checks
   - Must have test coverage for new code
   - Must update documentation if needed
   - Requires at least one review

### Version Tagging
Use semantic versioning: `MAJOR.MINOR.PATCH`
```bash
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

## Important Architectural Decisions

1. **Plugin-Based Architecture**: All functionality via Calibre's plugin system, no core modifications
2. **SQLite with sqlite-vec**: For vector storage instead of external vector DB
3. **Multi-Provider Embeddings**: Fallback chain for reliability
4. **Hybrid Chunking**: Smart text chunking that preserves philosophical arguments
5. **Philosophy-Aware Search**: Special modes for dialectical and genealogical search

## Performance Targets
- Search latency: <100ms for 10,000 books
- Indexing speed: ≥50 books/hour
- Memory usage: <500MB during operation
- Storage: ~4.4GB per 1,000 books (768-dim embeddings)

## Key Requirements
- **FR-001**: Basic semantic search with >0.7 similarity
- **FR-010**: Multi-provider embedding generation
- **FR-020**: Viewer context menu integration
- **NFR-001**: Search response time targets
- **PRR-001**: Complex philosophical concept support

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

## Contact and Resources
- Calibre Plugin Development: https://manual.calibre-ebook.com/creating_plugins.html
- SQLite-vec Documentation: https://github.com/asg017/sqlite-vec
- Project Issues: GitHub Issues (when repository is created)