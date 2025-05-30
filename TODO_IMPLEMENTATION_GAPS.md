# Calibre Semantic Search - Implementation & Deployment TODO

**Created:** 2025-05-29  
**Current Branch:** `develop`  
**Purpose:** Precise action items to close specification gaps and prepare for production deployment

---

## 🔴 Priority 1: Critical UI-Backend Integration (1-2 days)

These are placeholder implementations that need to be connected to existing services.

### 1.1 Connect Search Dialog to Search Engine
**File:** `/calibre_plugins/semantic_search/ui/search_dialog.py`  
**Line:** 401-404

```python
# CURRENT (placeholder):
def _initialize_search_engine(self):
    """Initialize search engine (placeholder)"""
    self.status_bar.setText("Search engine not yet implemented")

# TODO: Replace with:
def _initialize_search_engine(self):
    """Initialize search engine with dependencies"""
    from calibre_plugins.semantic_search.core.search_engine import SearchEngine
    from calibre_plugins.semantic_search.core.embedding_service import create_embedding_service
    from calibre_plugins.semantic_search.data.repositories import (
        EmbeddingRepository, CalibreRepository
    )
    
    # Get library path
    library_path = self.gui.library_path
    db_path = os.path.join(library_path, 'semantic_search', 'embeddings.db')
    
    # Create repositories
    embedding_repo = EmbeddingRepository(db_path)
    calibre_repo = CalibreRepository(self.gui.current_db.new_api)
    
    # Create embedding service
    embedding_service = create_embedding_service(self.config.as_dict())
    
    # Create search engine
    self.search_engine = SearchEngine(embedding_repo, embedding_service)
    
    # Run event loop in thread
    import threading
    self.loop_thread = threading.Thread(target=self.loop.run_forever)
    self.loop_thread.daemon = True
    self.loop_thread.start()
```

### 1.2 Implement View in Book Navigation
**File:** `/calibre_plugins/semantic_search/ui/search_dialog.py`  
**Line:** 405-412

```python
# CURRENT (placeholder):
def _view_in_book(self, book_id: int):
    """View result in book viewer"""
    info_dialog(self.gui, "View in Book",
               f"Opening book {book_id} in viewer...\n\n"
               "This feature will be implemented with viewer integration.",
               show=True)

# TODO: Replace with:
def _view_in_book(self, book_id: int):
    """View result in book viewer"""
    # Get the result that was clicked
    sender = self.sender()
    if hasattr(sender, 'parent') and hasattr(sender.parent(), 'result'):
        result = sender.parent().result
        
        # Open book in viewer
        self.gui.iactions['View'].view_book_at_position(
            book_id, 
            result.chunk_index,  # or use character position
            highlight_text=result.chunk_text[:100]  # First 100 chars to highlight
        )
```

### 1.3 Implement Find Similar Passages
**File:** `/calibre_plugins/semantic_search/ui/search_dialog.py`  
**Line:** 413-420

```python
# CURRENT (placeholder):
def _find_similar(self, chunk_id: int):
    """Find similar passages"""
    info_dialog(self.gui, "Find Similar",
               f"Finding passages similar to chunk {chunk_id}...\n\n"
               "This feature will be implemented soon.",
               show=True)

# TODO: Replace with:
def _find_similar(self, chunk_id: int):
    """Find similar passages"""
    if not self.search_engine:
        self._initialize_search_engine()
    
    # Clear current results
    self.results_list.clear()
    self.status_bar.setText("Finding similar passages...")
    
    # Run similarity search
    future = asyncio.run_coroutine_threadsafe(
        self.search_engine.find_similar(chunk_id, limit=20),
        self.loop
    )
    
    # Schedule result handling
    QTimer.singleShot(100, lambda: self._check_search_complete(future))
```

### 1.4 Connect Indexing UI to Indexing Service
**File:** `/calibre_plugins/semantic_search/ui.py`  
**Line:** 140-146

```python
# CURRENT (placeholder):
def _start_indexing(self, book_ids):
    """Start the indexing process for given books"""
    info_dialog(self.gui, 'Indexing',
                f'Indexing {len(book_ids)} books...\n\n'
                'This feature will be implemented with the indexing service.',
                show=True)

# TODO: Replace with:
def _start_indexing(self, book_ids):
    """Start the indexing process for given books"""
    from calibre_plugins.semantic_search.core.indexing_service import IndexingService
    from calibre.gui2.dialogs.progress import ProgressDialog
    from calibre.gui2.threaded_jobs import ThreadedJob
    
    # Create indexing job
    class IndexingJob(ThreadedJob):
        def __init__(self, gui, book_ids):
            ThreadedJob.__init__(self, 'Indexing books for semantic search')
            self.gui = gui
            self.book_ids = book_ids
            
        def run(self):
            # Initialize services
            library_path = self.gui.library_path
            # ... (initialize repositories and services)
            
            indexing_service = IndexingService(
                text_processor, embedding_service, 
                embedding_repo, calibre_repo
            )
            
            # Index books with progress
            return indexing_service.index_books(
                self.book_ids,
                progress_callback=self.set_progress
            )
    
    # Create and run job with progress dialog
    job = IndexingJob(self.gui, book_ids)
    ProgressDialog('Semantic Search Indexing', 
                   'Indexing books...', 
                   max=len(book_ids), 
                   parent=self.gui, 
                   job=job).exec_()
```

### 1.5 Implement Viewer Context Menu Integration
**File:** `/calibre_plugins/semantic_search/ui.py`  
**Line:** 185-188

```python
# CURRENT (placeholder):
def _inject_viewer_menu(self, viewer):
    """Add semantic search to viewer context menu"""
    pass

# TODO: Replace with:
def _inject_viewer_menu(self, viewer):
    """Add semantic search to viewer context menu"""
    from calibre_plugins.semantic_search.ui.viewer_integration import ViewerIntegration
    
    if not hasattr(self, 'viewer_integration'):
        self.viewer_integration = ViewerIntegration(self)
    
    self.viewer_integration.inject_into_viewer(viewer)
```

---

## 🟡 Priority 2: Local Embedding Provider (3-5 days)

### 2.1 Implement Ollama Provider
**Create File:** `/calibre_plugins/semantic_search/core/embedding_providers/ollama_provider.py`

```python
"""
Ollama local embedding provider for offline functionality
"""

import aiohttp
import numpy as np
from typing import List
import logging

from calibre_plugins.semantic_search.core.embedding_service import BaseEmbeddingProvider

logger = logging.getLogger(__name__)


class OllamaProvider(BaseEmbeddingProvider):
    """Local embedding provider using Ollama"""
    
    def __init__(self, 
                 model: str = "all-minilm-l6-v2",
                 base_url: str = "http://localhost:11434"):
        super().__init__(None, model)
        self.base_url = base_url
        self._dimensions = {
            "all-minilm-l6-v2": 384,
            "nomic-embed-text": 768,
            "mxbai-embed-large": 1024
        }.get(model, 384)
        
    async def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding using Ollama"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/embeddings",
                    json={
                        "model": self.model,
                        "prompt": self._truncate_text(text)
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        embedding = np.array(data['embedding'], dtype=np.float32)
                        return embedding
                    else:
                        raise Exception(f"Ollama API error: {response.status}")
                        
        except aiohttp.ClientError as e:
            logger.error(f"Ollama connection error: {e}")
            raise Exception("Ollama not running. Please start Ollama service.")
            
    async def generate_batch(self, texts: List[str]) -> List[np.ndarray]:
        """Batch generation for Ollama"""
        # Ollama doesn't support batch, so process sequentially
        embeddings = []
        for text in texts:
            embedding = await self.generate_embedding(text)
            embeddings.append(embedding)
        return embeddings
        
    def get_dimensions(self) -> int:
        return self._dimensions
        
    def get_model_name(self) -> str:
        return f"ollama/{self.model}"
```

### 2.2 Update Embedding Service Factory
**File:** `/calibre_plugins/semantic_search/core/embedding_service.py`  
**Line:** 406-450 (in `create_embedding_service` function)

```python
# ADD after line 436:
elif provider_name == 'local' or provider_name == 'ollama':
    # Check if Ollama is running
    try:
        import requests
        response = requests.get('http://localhost:11434/api/tags')
        if response.status_code == 200:
            from .embedding_providers.ollama_provider import OllamaProvider
            provider = OllamaProvider(
                model=config.get('embedding_model', 'all-minilm-l6-v2')
            )
            providers.append(provider)
    except:
        logger.warning("Ollama not available, will use mock provider")
```

### 2.3 Add Ollama Configuration UI
**File:** `/calibre_plugins/semantic_search/config.py`  
**Update:** `_create_api_tab` method to include Ollama settings

```python
# ADD in provider_combo items:
self.provider_combo.addItems([
    'vertex_ai',
    'openai', 
    'cohere',
    'ollama',  # ADD THIS
    'local'    # RENAME from 'local' to 'mock' for clarity
])

# ADD Ollama-specific settings that show/hide based on provider selection
```

---

## 🟢 Priority 3: Minor UI Enhancements (1-2 days)

### 3.1 Add Real Icons
**Create Directory:** `/calibre_plugins/semantic_search/resources/icons/`

**Required Icons:**
- `search.png` - Main plugin icon (32x32)
- `semantic_search.png` - Toolbar icon (24x24)
- `index.png` - Indexing icon (16x16)
- `settings.png` - Settings icon (16x16)

**Update:** `/calibre_plugins/semantic_search/ui.py`  
**Line:** 206-212

```python
# CURRENT:
def get_icons(name):
    """Get icon from resources"""
    return QIcon()

# TODO: Replace with:
def get_icons(name):
    """Get icon from resources"""
    from calibre.utils.resources import get_image_path
    import os
    
    # Try to get icon from our resources
    icon_path = os.path.join(
        os.path.dirname(__file__), 
        'resources', 'icons', name
    )
    
    if os.path.exists(icon_path):
        return QIcon(icon_path)
    
    # Fallback to Calibre's icons
    return QIcon(I(name))
```

### 3.2 Implement Floating Window Mode
**File:** `/calibre_plugins/semantic_search/ui/search_dialog.py`  
**Add after line 113:**

```python
# Check if floating window mode is enabled
if self.config.get('ui_options.floating_window', False):
    self.setWindowFlags(
        Qt.Window | 
        Qt.WindowStaysOnTopHint |
        Qt.FramelessWindowHint  # Optional
    )
    
    # Set opacity
    opacity = self.config.get('ui_options.window_opacity', 0.95)
    self.setWindowOpacity(opacity)
    
    # Make draggable if frameless
    self.draggable = True
    self.drag_position = None
```

### 3.3 Add Test Connection Feature
**File:** `/calibre_plugins/semantic_search/config.py`  
**Line:** 362-367

```python
# CURRENT (placeholder):
def _test_connection(self):
    """Test API connection"""
    from PyQt5.Qt import QMessageBox
    QMessageBox.information(self, "Test Connection", 
                            "Connection testing will be implemented with the embedding service.")

# TODO: Replace with:
def _test_connection(self):
    """Test API connection"""
    from PyQt5.Qt import QMessageBox, QProgressDialog
    import asyncio
    
    provider = self.provider_combo.currentText()
    
    # Show progress
    progress = QProgressDialog("Testing connection...", None, 0, 0, self)
    progress.setWindowModality(Qt.WindowModal)
    progress.show()
    
    try:
        # Create test provider
        config = {
            'embedding_provider': provider,
            'api_keys': {provider: self.api_key_edit.text()},
            'embedding_model': self.model_edit.text()
        }
        
        from calibre_plugins.semantic_search.core.embedding_service import create_embedding_service
        service = create_embedding_service(config)
        
        # Test embedding generation
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        embedding = loop.run_until_complete(
            service.generate_embedding("Test connection")
        )
        
        progress.close()
        QMessageBox.information(self, "Success", 
                               f"Successfully connected to {provider}!\n"
                               f"Embedding dimensions: {len(embedding)}")
        
    except Exception as e:
        progress.close()
        QMessageBox.critical(self, "Connection Failed",
                            f"Failed to connect to {provider}:\n\n{str(e)}")
```

---

## 🚀 Deployment Preparation Checklist

### 4.1 Code Quality & Testing

```bash
# 1. Run all tests
pytest tests/ -v

# 2. Check code coverage
pytest --cov=calibre_plugins.semantic_search --cov-report=html

# 3. Run linting
black calibre_plugins/
isort calibre_plugins/
mypy calibre_plugins/

# 4. Run performance benchmarks
pytest tests/performance/ -v -m benchmark
```

### 4.2 Build Process

```bash
# 1. Update version number
# Edit: calibre_plugins/semantic_search/__init__.py
# Change: version = (0, 1, 0) to version = (1, 0, 0)

# 2. Build plugin ZIP
python scripts/build_plugin.py

# 3. Test installation
calibre-customize -r "Semantic Search"  # Remove if exists
calibre-customize -a calibre-semantic-search.zip

# 4. Test in Calibre
calibre-debug -g
```

### 4.3 Documentation Updates

**Create/Update these files:**

1. **`CHANGELOG.md`**
```markdown
# Changelog

## [1.0.0] - 2025-05-30

### Added
- Initial release of Calibre Semantic Search Plugin
- Multi-provider embedding support (Vertex AI, OpenAI, Cohere, Local)
- Philosophy-aware text chunking with argument preservation
- Advanced search modes (Semantic, Dialectical, Genealogical, Hybrid)
- Viewer integration with context menu
- Comprehensive configuration interface
- Performance optimizations and caching

### Features
- Sub-100ms search performance for 10,000 books
- Batch indexing with progress tracking
- Cross-platform support (Windows, macOS, Linux)
- Calibre 5.0+ compatibility
```

2. **`README.md`** - Update installation instructions

3. **`docs/user_manual.md`** - Complete user documentation

### 4.4 Git Workflow

```bash
# 1. Ensure all changes are committed
git add .
git commit -m "feat: connect UI to backend services and prepare for v1.0.0 release"

# 2. Create pull request to develop (if not already on develop)
git push origin develop

# 3. Run final tests on develop
# ... (all tests pass)

# 4. Create release branch
git checkout -b release/v1.0.0

# 5. Final version bumps and changelog
# ... make final adjustments ...
git commit -m "chore: prepare v1.0.0 release"

# 6. Merge to master
git checkout master
git merge --no-ff release/v1.0.0
git tag -a v1.0.0 -m "Release version 1.0.0"

# 7. Push everything
git push origin master --tags
git push origin develop

# 8. Create GitHub release
# - Upload calibre-semantic-search.zip
# - Add changelog contents
# - Mark as stable release
```

---

## 📋 Task Summary & Time Estimates

### Immediate Tasks (Total: 2-3 days)
1. **UI-Backend Integration** (1 day)
   - [ ] Connect search dialog to search engine
   - [ ] Implement view in book navigation  
   - [ ] Implement find similar passages
   - [ ] Connect indexing UI to service
   - [ ] Complete viewer integration

2. **Minor UI Polish** (0.5 days)
   - [ ] Add real icons
   - [ ] Test connection implementation
   - [ ] Final UI testing

3. **Build & Test** (0.5 days)
   - [ ] Run full test suite
   - [ ] Build plugin ZIP
   - [ ] Test installation
   - [ ] Performance verification

### Medium-term Tasks (Total: 3-5 days)
1. **Local Provider** (3-4 days)
   - [ ] Implement Ollama provider
   - [ ] Add configuration UI
   - [ ] Test offline functionality
   - [ ] Documentation

2. **Floating Window** (1 day)
   - [ ] Implement floating mode
   - [ ] Test across platforms
   - [ ] Add keyboard shortcuts

### Pre-release Checklist
- [ ] All tests passing (>80% coverage)
- [ ] Performance benchmarks meet targets
- [ ] Documentation complete
- [ ] Changelog updated
- [ ] Version bumped to 1.0.0
- [ ] Plugin ZIP builds successfully
- [ ] Manual testing on all platforms
- [ ] GitHub release prepared

---

**Estimated Total Time to Production: 5-8 days**

**Recommended Approach:**
1. Focus on Priority 1 tasks first (critical integrations)
2. Build and test frequently
3. Consider releasing v1.0.0 without local provider, add in v1.1.0
4. Floating window can be v1.2.0 feature

This will get you to production fastest while maintaining quality!