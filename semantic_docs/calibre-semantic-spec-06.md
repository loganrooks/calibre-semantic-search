# Calibre Semantic Search Plugin - Development Workflow Guide

## Document Information
- **Version**: 1.0
- **Status**: Draft
- **Audience**: Developers, Technical Leads, AI Agents implementing the plugin
- **Purpose**: Step-by-step implementation guide following SPARC methodology

## SPARC Methodology Overview

### What is SPARC?
```
S - Specification: Define what to build (completed documents 1-5)
P - Pseudocode: Design algorithms and logic (this document)
A - Architecture: Implement components (this document)
R - Refinement: Optimize and polish (this document)
C - Completion: Verify and release (this document)
```

### Development Principles
1. **Test-First**: Write failing test before implementation
2. **Incremental**: Small, verifiable steps
3. **Iterative**: Refine based on feedback
4. **Measurable**: Track progress objectively

---

## Phase 1: Project Setup and Foundation

### Step 1.1: Development Environment Setup

```bash
# PSEUDOCODE: Environment setup script

FUNCTION setup_development_environment():
    # 1. Verify Python version
    IF python_version < 3.8:
        ERROR "Python 3.8+ required"
    
    # 2. Create virtual environment
    CREATE virtual_env AT ./venv
    ACTIVATE virtual_env
    
    # 3. Install Calibre development dependencies
    INSTALL calibre[dev]
    INSTALL pytest pytest-qt pytest-cov pytest-benchmark
    INSTALL black isort mypy
    
    # 4. Install plugin dependencies
    INSTALL numpy
    INSTALL litellm
    INSTALL msgpack
    
    # 5. Download sqlite-vec
    DOWNLOAD sqlite-vec FOR current_platform
    EXTRACT TO ./lib/
    
    # 6. Setup pre-commit hooks
    INSTALL pre-commit
    CONFIGURE .pre-commit-config.yaml
    RUN pre-commit install
```

### Step 1.2: Project Structure Creation

```bash
# SPECIFICATION: Directory structure

calibre-semantic-search/
├── .github/
│   └── workflows/
│       ├── test.yml
│       └── release.yml
├── calibre_plugins/
│   └── semantic_search/
│       ├── __init__.py
│       ├── plugin-import-name-semantic_search.txt
│       ├── config.py
│       ├── ui.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── embedding_service.py
│       │   ├── search_engine.py
│       │   └── text_processor.py
│       ├── data/
│       │   ├── __init__.py
│       │   ├── database.py
│       │   ├── repositories.py
│       │   └── cache.py
│       ├── ui/
│       │   ├── __init__.py
│       │   ├── search_dialog.py
│       │   ├── widgets.py
│       │   └── viewer_integration.py
│       └── resources/
│           ├── icons/
│           └── translations/
├── tests/
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── docs/
│   ├── user_manual.md
│   └── api_reference.md
├── scripts/
│   ├── build_plugin.py
│   └── run_tests.py
├── requirements.txt
├── requirements-dev.txt
├── setup.cfg
├── pyproject.toml
└── README.md
```

### Step 1.3: Initial Plugin Skeleton

```python
# IMPLEMENTATION: Create base plugin structure

# File: calibre_plugins/semantic_search/__init__.py
"""
Semantic Search Plugin for Calibre
Enables AI-powered similarity search for philosophical texts
"""

from calibre.customize import InterfaceActionBase

class SemanticSearchPlugin(InterfaceActionBase):
    """
    Main plugin class that Calibre loads
    """
    name = 'Semantic Search'
    description = 'AI-powered semantic search for philosophical texts'
    supported_platforms = ['windows', 'osx', 'linux']
    author = 'Your Name'
    version = (0, 1, 0)  # Start at 0.1.0
    minimum_calibre_version = (5, 0, 0)
    
    # This points to our actual implementation
    actual_plugin = 'calibre_plugins.semantic_search.ui:SemanticSearchInterface'
    
    def is_customizable(self):
        """Allow user configuration"""
        return True
```

### Step 1.4: Version Control Initialization

```bash
# COMMANDS: Initialize git repository

git init
git add .gitignore README.md

# .gitignore contents:
*.pyc
__pycache__/
*.egg-info/
.coverage
.pytest_cache/
venv/
*.db
*.log
.DS_Store
build/
dist/
```

---

## Phase 2: Core Implementation (TDD Approach)

### Step 2.1: Configuration System

#### Write Test First
```python
# TEST: tests/unit/test_config.py

class TestConfiguration:
    def test_default_configuration(self):
        """Test default config values"""
        config = SemanticSearchConfig()
        
        assert config.get('embedding_provider') == 'vertex_ai'
        assert config.get('chunk_size') == 512
        assert config.get('search_options.similarity_threshold') == 0.7
        
    def test_save_and_load_config(self, tmp_path):
        """Test config persistence"""
        config = SemanticSearchConfig(tmp_path)
        config.set('api_keys.vertex_ai', 'test_key')
        config.save()
        
        # Load in new instance
        config2 = SemanticSearchConfig(tmp_path)
        assert config2.get('api_keys.vertex_ai') == 'test_key'
```

#### Implement Configuration
```python
# IMPLEMENTATION: calibre_plugins/semantic_search/config.py

from calibre.utils.config import JSONConfig
from typing import Any, Dict, Optional
import os

class SemanticSearchConfig:
    """Configuration management for semantic search"""
    
    DEFAULTS = {
        'embedding_provider': 'vertex_ai',
        'embedding_model': 'text-embedding-preview-0815',
        'embedding_dimensions': 768,
        'chunk_size': 512,
        'chunk_overlap': 50,
        'api_keys': {},
        'search_options': {
            'default_limit': 20,
            'similarity_threshold': 0.7,
            'scope': 'library'
        },
        'ui_options': {
            'floating_window': False,
            'window_opacity': 0.95,
            'remember_position': True
        },
        'performance': {
            'cache_enabled': True,
            'cache_size_mb': 100,
            'batch_size': 100,
            'max_concurrent_requests': 3
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        if config_path:
            # For testing
            self._config = JSONConfig(os.path.join(config_path, 'semantic_search'))
        else:
            # Production
            self._config = JSONConfig('plugins/semantic_search')
        
        self._config.defaults = self.DEFAULTS
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get config value with dot notation support"""
        # Implementation here...
```

### Step 2.2: Text Processing Implementation

#### Write Test First
```python
# TEST: tests/unit/test_text_processor.py

class TestTextProcessor:
    def test_chunk_by_paragraph(self):
        """Test paragraph-based chunking"""
        text = """First paragraph here.
        
        Second paragraph here.
        
        Third paragraph here."""
        
        processor = TextProcessor()
        chunks = processor.chunk_text(text, strategy='paragraph')
        
        assert len(chunks) == 3
        assert chunks[0].text == "First paragraph here."
        assert chunks[0].metadata['index'] == 0
```

#### Implement Text Processor
```python
# PSEUDOCODE: Text processing implementation

class TextProcessor:
    def chunk_text(self, text: str, strategy: str = 'hybrid') -> List[Chunk]:
        """
        Split text into chunks based on strategy
        
        Strategies:
        - paragraph: Split by paragraphs
        - sliding: Fixed-size sliding window
        - semantic: Topic-based splitting
        - hybrid: Smart combination
        """
        
        IF strategy == 'paragraph':
            RETURN self._chunk_by_paragraph(text)
        ELIF strategy == 'sliding':
            RETURN self._chunk_sliding_window(text)
        ELIF strategy == 'semantic':
            RETURN self._chunk_by_semantics(text)
        ELSE:  # hybrid
            RETURN self._chunk_hybrid(text)
            
    def _chunk_hybrid(self, text: str) -> List[Chunk]:
        """
        ALGORITHM: Hybrid chunking
        
        1. Split into paragraphs
        2. FOR each paragraph:
           IF length > MAX_CHUNK_SIZE:
               Split paragraph into sentences
               Group sentences into chunks
           ELIF length < MIN_CHUNK_SIZE:
               Merge with adjacent paragraphs
           ELSE:
               Keep as single chunk
        3. Add overlap between chunks
        4. Return chunk list
        """
```

### Step 2.3: Embedding Service Implementation

#### Write Test First
```python
# TEST: tests/unit/test_embedding_service.py

class TestEmbeddingService:
    @pytest.mark.asyncio
    async def test_generate_embedding(self):
        """Test embedding generation"""
        service = EmbeddingService(mock_provider)
        embedding = await service.generate_embedding("test text")
        
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (768,)
        assert -1 <= embedding.min() <= embedding.max() <= 1
        
    @pytest.mark.asyncio
    async def test_provider_fallback(self):
        """Test fallback on provider failure"""
        primary = MockProvider(fail=True)
        fallback = MockProvider(fail=False)
        
        service = EmbeddingService([primary, fallback])
        embedding = await service.generate_embedding("test")
        
        assert embedding is not None
        assert service.last_provider == fallback
```

#### Implement Embedding Service
```python
# PSEUDOCODE: Embedding service with fallback

class EmbeddingService:
    def __init__(self, providers: List[EmbeddingProvider]):
        self.providers = providers
        self.cache = EmbeddingCache()
        
    async def generate_embedding(self, text: str) -> np.ndarray:
        """
        ALGORITHM: Generate embedding with fallback
        
        1. Check cache for existing embedding
        2. IF cached: RETURN cached embedding
        3. FOR each provider in order:
           TRY:
               embedding = await provider.embed(text)
               cache.store(text, embedding)
               RETURN embedding
           CATCH ProviderError:
               LOG error
               CONTINUE to next provider
        4. RAISE NoProvidersAvailable
        """
        
    async def generate_batch(self, texts: List[str]) -> List[np.ndarray]:
        """
        ALGORITHM: Efficient batch generation
        
        1. Separate cached and uncached texts
        2. Retrieve cached embeddings
        3. FOR uncached texts:
           Batch into groups of BATCH_SIZE
           Generate embeddings for each batch
        4. Combine and return all embeddings
        """
```

### Step 2.4: Database Layer Implementation

#### Write Test First
```python
# TEST: tests/unit/test_database.py

class TestDatabase:
    def test_initialize_schema(self, tmp_path):
        """Test database initialization"""
        db = SemanticSearchDB(tmp_path / "test.db")
        
        # Verify tables exist
        tables = db.get_tables()
        assert 'embeddings' in tables
        assert 'chunks' in tables
        assert 'books' in tables
        
    def test_store_and_retrieve_embedding(self, tmp_path):
        """Test embedding storage"""
        db = SemanticSearchDB(tmp_path / "test.db")
        
        # Store embedding
        embedding = np.random.rand(768).astype(np.float32)
        chunk_id = db.store_embedding(
            book_id=1,
            chunk_text="test chunk",
            embedding=embedding
        )
        
        # Retrieve
        retrieved = db.get_embedding(chunk_id)
        np.testing.assert_array_almost_equal(embedding, retrieved)
```

#### Implement Database Layer
```python
# PSEUDOCODE: Database implementation

class SemanticSearchDB:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_database()
        
    def _init_database(self):
        """
        ALGORITHM: Initialize database schema
        
        1. Connect to SQLite database
        2. Load sqlite-vec extension
        3. CREATE tables if not exist:
           - embeddings (vector table)
           - chunks (metadata)
           - books (tracking)
           - cache (query cache)
        4. Create indexes for performance
        5. Run migrations if needed
        """
        
    def vector_search(self, query_embedding: np.ndarray, 
                     limit: int = 20,
                     filters: Dict = None) -> List[SearchResult]:
        """
        ALGORITHM: Perform vector similarity search
        
        1. Build SQL query with filters
        2. Execute vector search:
           SELECT * FROM embeddings
           WHERE embedding MATCH ?
           AND [filter conditions]
           ORDER BY distance
           LIMIT ?
        3. Join with metadata tables
        4. Convert to SearchResult objects
        5. RETURN results
        """
```

---

## Phase 3: User Interface Implementation

### Step 3.1: Main Search Dialog

#### Write Test First
```python
# TEST: tests/integration/test_search_dialog.py

class TestSearchDialog:
    def test_dialog_creation(self, qtbot, mock_gui):
        """Test dialog can be created"""
        dialog = SemanticSearchDialog(mock_gui)
        qtbot.addWidget(dialog)
        
        assert dialog.windowTitle() == "Semantic Search"
        assert dialog.search_input is not None
        assert dialog.results_list is not None
        
    def test_search_execution(self, qtbot, mock_gui):
        """Test search from dialog"""
        dialog = SemanticSearchDialog(mock_gui)
        qtbot.addWidget(dialog)
        
        # Enter search query
        qtbot.keyClicks(dialog.search_input, "consciousness")
        
        # Click search button
        qtbot.mouseClick(dialog.search_button, Qt.LeftButton)
        
        # Verify results appear
        qtbot.waitUntil(lambda: dialog.results_list.count() > 0)
```

#### Implement Search Dialog
```python
# PSEUDOCODE: Search dialog implementation

class SemanticSearchDialog(QDialog):
    def __init__(self, gui_instance, plugin_instance):
        super().__init__(gui_instance)
        self.gui = gui_instance
        self.plugin = plugin_instance
        self.search_service = SearchService()
        
        self._setup_ui()
        self._connect_signals()
        
    def _setup_ui(self):
        """
        ALGORITHM: Create dialog UI
        
        1. Set window properties (title, size, flags)
        2. Create main layout
        3. Add search input section:
           - Query text box
           - Search button
           - Options panel
        4. Add results section:
           - Results list
           - Details panel
        5. Add status bar
        6. Apply styling
        """
        
    def perform_search(self):
        """
        ALGORITHM: Execute search
        
        1. Get query from input
        2. Validate query
        3. Show progress indicator
        4. ASYNC:
           results = await search_service.search(query, options)
        5. Display results
        6. Hide progress indicator
        7. Update status bar
        """
```

### Step 3.2: Viewer Integration

#### Write Test First
```python
# TEST: tests/integration/test_viewer_integration.py

class TestViewerIntegration:
    def test_context_menu_injection(self, mock_viewer):
        """Test context menu appears in viewer"""
        integration = ViewerIntegration()
        integration.inject_into_viewer(mock_viewer)
        
        # Simulate text selection
        mock_viewer.select_text("Dasein")
        
        # Get context menu
        menu = mock_viewer.get_context_menu()
        
        # Verify our action exists
        actions = [a.text() for a in menu.actions()]
        assert "Semantic Search" in actions
```

#### Implement Viewer Integration
```python
# PSEUDOCODE: Viewer integration

class ViewerIntegration:
    def inject_into_viewer(self, viewer):
        """
        ALGORITHM: Add semantic search to viewer
        
        1. Get viewer's web view widget
        2. Connect to context menu signal
        3. Add toolbar button
        4. Setup JavaScript bridge communication
        """
        
    def handle_context_menu(self, point: QPoint):
        """
        ALGORITHM: Add menu items
        
        1. Get selected text via JavaScript:
           text = viewer.execute_js("window.getSelection().toString()")
        2. IF text is selected:
           Create menu action "Semantic Search: [text]"
           Connect to search handler
        3. Show menu at point
        """
        
    def search_from_selection(self, selected_text: str):
        """
        ALGORITHM: Search selected text
        
        1. Get current book context
        2. Open search dialog
        3. Populate with selected text
        4. Set scope to current book
        5. Execute search
        """
```

---

## Phase 4: Integration and Testing

### Step 4.1: Plugin Integration

```python
# PSEUDOCODE: Main plugin integration

class SemanticSearchInterface(InterfaceAction):
    def genesis(self):
        """
        ALGORITHM: Initialize plugin
        
        1. Create menu structure
        2. Add toolbar buttons
        3. Initialize services:
           - Config service
           - Database service
           - Search service
           - UI components
        4. Connect to Calibre signals
        5. Check for updates
        """
        
    def show_search_dialog(self):
        """Show main search interface"""
        IF not hasattr(self, 'search_dialog'):
            self.search_dialog = SemanticSearchDialog(self.gui, self)
        
        self.search_dialog.show()
        self.search_dialog.raise_()
        self.search_dialog.activateWindow()
        
    def library_changed(self, db):
        """Handle library switch"""
        # Reinitialize database connection
        # Clear caches
        # Update UI state
```

### Step 4.2: End-to-End Testing

```bash
# SCRIPT: Run comprehensive tests

#!/bin/bash
# scripts/run_tests.py

# Unit tests with coverage
pytest tests/unit -v --cov=calibre_plugins.semantic_search --cov-report=html

# Integration tests
pytest tests/integration -v

# Performance benchmarks
pytest tests/performance -v --benchmark-only

# Philosophical correctness
pytest tests/philosophical -v

# Generate report
python scripts/generate_test_report.py
```

---

## Phase 5: Optimization and Refinement

### Step 5.1: Performance Optimization

```python
# PSEUDOCODE: Performance optimizations

class PerformanceOptimizer:
    def optimize_search_performance(self):
        """
        OPTIMIZATIONS:
        
        1. Query result caching:
           - LRU cache for recent queries
           - TTL-based expiration
           
        2. Embedding pre-loading:
           - Memory-map frequently accessed
           - Predictive loading
           
        3. Database query optimization:
           - Prepared statements
           - Connection pooling
           - Index optimization
           
        4. Parallel processing:
           - Concurrent embedding generation
           - Parallel chunk processing
        """
        
    def profile_and_optimize(self):
        """
        ALGORITHM: Profile-guided optimization
        
        1. Run profiler on common operations
        2. Identify bottlenecks
        3. Apply targeted optimizations:
           IF CPU bound: Parallelize
           IF I/O bound: Async/caching
           IF Memory bound: Streaming
        4. Measure improvement
        5. Repeat until targets met
        """
```

### Step 5.2: User Experience Refinement

```python
# PSEUDOCODE: UX improvements

class UXRefinements:
    def improve_search_feedback(self):
        """
        IMPROVEMENTS:
        
        1. Real-time search suggestions
        2. Search history with favorites
        3. Keyboard shortcuts
        4. Contextual help tooltips
        5. Progress animations
        6. Error recovery suggestions
        """
        
    def add_advanced_features(self):
        """
        FEATURES:
        
        1. Search query builder
        2. Visual similarity graph
        3. Export to research tools
        4. Batch operations
        5. Search templates
        """
```

---

## Phase 6: Release Preparation

### Step 6.1: Documentation

```markdown
# TEMPLATE: User documentation structure

1. Getting Started
   - Installation
   - Configuration
   - First search
   
2. Search Features
   - Basic search
   - Advanced search
   - Philosophical modes
   
3. Research Workflows
   - Concept genealogy
   - Comparative analysis
   - Citation export
   
4. Troubleshooting
   - Common issues
   - Performance tuning
   - FAQ
```

### Step 6.2: Build and Package

```python
# SCRIPT: Build plugin package

def build_plugin():
    """
    ALGORITHM: Create plugin ZIP
    
    1. Clean build directory
    2. Copy source files
    3. Copy resources (icons, translations)
    4. Generate metadata
    5. Create ZIP archive
    6. Verify plugin structure
    7. Test installation
    """
    
    # Implementation in scripts/build_plugin.py
```

### Step 6.3: Release Checklist

```yaml
# CHECKLIST: Pre-release verification

code_quality:
  - [ ] All tests passing
  - [ ] Coverage > 80%
  - [ ] No linting errors
  - [ ] Type checking passes

functionality:
  - [ ] Basic search works
  - [ ] Viewer integration works
  - [ ] All UI elements functional
  - [ ] Performance targets met

compatibility:
  - [ ] Tested on Windows
  - [ ] Tested on macOS
  - [ ] Tested on Linux
  - [ ] Calibre 5.x, 6.x, 7.x

documentation:
  - [ ] User manual complete
  - [ ] API docs generated
  - [ ] README updated
  - [ ] CHANGELOG updated

release:
  - [ ] Version bumped
  - [ ] Git tagged
  - [ ] Package built
  - [ ] Upload to releases
```

---

## Development Best Practices

### 1. Code Organization
```python
# PATTERN: Clear module structure

# Good: Clear separation of concerns
calibre_plugins/semantic_search/
├── core/           # Business logic
├── data/           # Data access
├── ui/             # User interface
└── utils/          # Utilities

# Bad: Everything in one file
calibre_plugins/semantic_search/
└── plugin.py      # 5000 lines!
```

### 2. Error Handling
```python
# PATTERN: Graceful error handling

def safe_operation():
    try:
        # Risky operation
        result = perform_operation()
    except SpecificError as e:
        # Handle known error
        logger.warning(f"Expected error: {e}")
        return fallback_value()
    except Exception as e:
        # Log unexpected error
        logger.error(f"Unexpected error: {e}")
        # Show user-friendly message
        show_error_dialog("Operation failed. Please try again.")
        # Don't crash
        return None
```

### 3. Testing Discipline
```python
# PATTERN: Test-first development

# 1. Write test that fails
def test_new_feature():
    result = new_feature()
    assert result == expected

# 2. Implement minimal code
def new_feature():
    return expected  # Just make test pass

# 3. Refactor with confidence
def new_feature():
    # Proper implementation
    # Tests ensure correctness
```

### 4. Performance Awareness
```python
# PATTERN: Measure before optimizing

def potentially_slow_operation():
    with timer("operation_name"):
        # Code to measure
        result = do_work()
    
    # Log if too slow
    if timer.elapsed > THRESHOLD:
        logger.warning(f"Slow operation: {timer.elapsed}s")
    
    return result
```

---

## Troubleshooting Guide

### Common Issues and Solutions

1. **Plugin Won't Load**
   ```
   DIAGNOSIS:
   - Check Calibre version compatibility
   - Verify __init__.py structure
   - Check for import errors
   
   SOLUTION:
   - Update minimum_calibre_version
   - Fix import paths
   - Check dependencies
   ```

2. **Search Too Slow**
   ```
   DIAGNOSIS:
   - Profile search operation
   - Check database indexes
   - Monitor API latency
   
   SOLUTION:
   - Add caching layer
   - Optimize queries
   - Use local embeddings
   ```

3. **Memory Usage High**
   ```
   DIAGNOSIS:
   - Profile memory allocation
   - Check for leaks
   - Monitor cache size
   
   SOLUTION:
   - Implement streaming
   - Add cache limits
   - Use memory mapping
   ```

---

## Continuous Improvement

### Metrics to Track
1. **Performance Metrics**
   - Search latency (p50, p95, p99)
   - Indexing speed (books/hour)
   - Memory usage (peak, average)

2. **Quality Metrics**
   - Test coverage
   - Bug reports/week
   - User satisfaction

3. **Usage Metrics**
   - Daily active users
   - Searches/day
   - Popular queries

### Iteration Process
```
WHILE not perfect:
    1. Collect feedback
    2. Analyze metrics
    3. Identify improvements
    4. Implement changes
    5. Test thoroughly
    6. Release update
    7. GOTO 1
```

This comprehensive workflow guide provides the roadmap for implementing the semantic search plugin using SPARC methodology, ensuring a systematic and quality-focused development process.