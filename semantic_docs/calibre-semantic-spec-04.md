# Calibre Semantic Search Plugin - Calibre Integration Guide

## Document Information
- **Version**: 1.0
- **Status**: Draft
- **Audience**: Developers implementing the plugin
- **Purpose**: Comprehensive guide to integrating with Calibre's codebase

## Calibre Architecture Overview

### Core Components Relevant to Our Plugin

```
calibre/
├── src/
│   ├── calibre/
│   │   ├── customize/          # Plugin system base classes
│   │   │   ├── __init__.py    # InterfaceActionBase, Plugin
│   │   │   └── ui.py          # InterfaceAction
│   │   ├── gui2/              # GUI components
│   │   │   ├── actions/       # Built-in actions
│   │   │   ├── viewer/        # E-book viewer
│   │   │   ├── library/       # Library view
│   │   │   └── preferences/   # Preferences system
│   │   ├── db/                # Database layer
│   │   │   ├── backend.py     # DB backend
│   │   │   └── cache.py       # Metadata cache
│   │   └── utils/             # Utilities
│   │       ├── config.py      # Configuration
│   │       └── date.py        # Date handling
│   └── pyj/                   # RapydScript sources
│       └── read_book/         # Viewer JavaScript
│           ├── read_book.pyj  # Main viewer code
│           └── search.pyj     # Search implementation
├── resources/                 # Icons, themes, etc.
└── translations/             # I18n files
```

### Key Integration Points

1. **Plugin System** - Our primary interface
2. **Viewer Hooks** - Limited but crucial
3. **Database Access** - Read-only to metadata.db
4. **Job System** - For background processing
5. **Configuration** - JSONConfig system
6. **UI Integration** - Menus, toolbars, dialogs

---

## Plugin System Integration

### 1. Plugin Base Class Structure

```python
# PSEUDOCODE: Plugin class hierarchy

class Plugin(Calibre.customize.Plugin):
    """Base plugin class - DO NOT use directly"""
    
    # Required metadata
    name = None                  # Display name
    version = None              # (major, minor, patch)
    minimum_calibre_version = None
    
    # Optional metadata
    supported_platforms = ['windows', 'osx', 'linux']
    author = None
    description = None
    
class InterfaceActionBase(Plugin):
    """Base class for UI plugins - THIS IS WHAT WE USE"""
    
    # Additional UI-specific attributes
    actual_plugin = None        # 'module:ClassName'
    
    def load_actual_plugin(self, gui):
        """Load the actual UI plugin"""
        # Calibre handles this
        
class InterfaceAction(QObject):
    """Actual UI plugin implementation"""
    
    # Core lifecycle methods
    def genesis(self):
        """Called once when plugin loads"""
        
    def initialization_complete(self):
        """Called after all plugins loaded"""
        
    def library_changed(self, db):
        """Called when library switches"""
        
    def location_selected(self, loc):
        """Called when book location selected"""
        
    def shutting_down(self):
        """Called before Calibre shuts down"""
```

### 2. Plugin Initialization Flow

```
PSEUDOCODE: Plugin initialization sequence

1. Calibre starts
2. Loads plugin metadata from __init__.py
3. Calls load_actual_plugin(gui)
4. Creates InterfaceAction instance
5. Calls genesis() on instance
6. Adds to GUI (menus, toolbars)
7. Calls initialization_complete()
8. Plugin ready for use

SEQUENCE:
Calibre → Plugin.__init__.py → InterfaceActionBase → InterfaceAction → genesis()
```

### 3. Critical Plugin Files

#### `__init__.py` - Plugin Metadata
```python
# STRUCTURE: Plugin metadata definition

from calibre.customize import InterfaceActionBase

class SemanticSearchPlugin(InterfaceActionBase):
    name = 'Semantic Search'
    description = 'AI-powered semantic search for philosophical texts'
    supported_platforms = ['windows', 'osx', 'linux']
    author = 'Your Name'
    version = (1, 0, 0)
    minimum_calibre_version = (5, 0, 0)
    
    # Point to actual implementation
    actual_plugin = 'calibre_plugins.semantic_search.ui:SemanticSearchAction'
    
    def is_customizable(self):
        """Allow configuration"""
        return True
        
    def config_widget(self):
        """Return configuration widget"""
        # Import here to avoid loading Qt at startup
        from calibre_plugins.semantic_search.config import ConfigWidget
        return ConfigWidget()
        
    def save_settings(self, config_widget):
        """Save configuration"""
        config_widget.save_settings()
```

#### `plugin-import-name-semantic_search.txt`
```
CONTENT: Just the import name
semantic_search
```

This file is REQUIRED and must match the plugin folder name.

---

## Viewer Integration

### 1. Viewer Architecture Overview

```
┌─────────────────────────────────────────┐
│          Qt Application (Python)         │
│  ┌────────────────────────────────────┐ │
│  │         EbookViewer class          │ │
│  │  - Manages viewer window           │ │
│  │  - Controls navigation             │ │
│  └──────────────┬─────────────────────┘ │
│                 │                        │
│  ┌──────────────▼─────────────────────┐ │
│  │       WebView (QWebEngineView)     │ │
│  │  - Renders book content            │ │
│  │  - Executes viewer JavaScript      │ │
│  └──────────────┬─────────────────────┘ │
└─────────────────┼───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│      JavaScript Layer (Restricted)      │
│  - RapydScript compiled code            │
│  - No arbitrary JS execution            │
│  - Communicates via Qt Bridge           │
└─────────────────────────────────────────┘
```

### 2. Viewer Hook Points

#### Show Viewer Hook
```python
# PSEUDOCODE: Viewer integration hook

def show_viewer(self, *args):
    """
    Called when viewer opens
    Args vary based on how viewer was opened
    
    Typical args:
    - args[0]: EbookViewer instance
    - args[1]: Book path or pathtoebook
    """
    
    # Extract viewer instance
    viewer = args[0] if args else None
    
    if viewer:
        # Store reference for later use
        self.current_viewer = viewer
        
        # Inject our customizations
        self.inject_viewer_features(viewer)
```

#### Viewer Customization Options
```python
# WHAT WE CAN DO:

1. Add toolbar actions:
   viewer.tool_bar.addAction(our_action)

2. Add menu items:
   viewer.menuBar().addMenu(our_menu)

3. Connect to existing signals:
   viewer.view.document.chapter_rendered.connect(handler)

4. Add context menu items (via Qt):
   viewer.view.page().customContextMenuRequested.connect(handler)

# WHAT WE CANNOT DO:

1. ❌ Modify viewer's internal JavaScript
2. ❌ Change search.pyj behavior directly  
3. ❌ Inject arbitrary JavaScript
4. ❌ Access DOM directly
```

### 3. Working with ViewerBridge

```python
# PSEUDOCODE: ViewerBridge communication

class ViewerBridge(QObject):
    """Bridge between Python and JavaScript"""
    
    # Signals from JavaScript to Python
    search_requested = pyqtSignal(str)
    selection_changed = pyqtSignal(str)
    
    # Methods callable from JavaScript
    @pyqtSlot(str, result=str)
    def process_search(self, query):
        """JavaScript can call this"""
        return self.do_python_search(query)

# How to use:
1. Get viewer's bridge: viewer.view.bridge
2. Connect to signals: bridge.search_requested.connect(handler)
3. Call JS functions: viewer.view.page().runJavaScript("code")
```

### 4. Context Menu Integration Strategy

```python
# PSEUDOCODE: Adding context menu items

def inject_context_menu(self, viewer):
    """Add semantic search to context menu"""
    
    web_view = viewer.view
    
    def show_context_menu(point):
        # Get selected text via JavaScript
        web_view.page().runJavaScript(
            "window.getSelection().toString()",
            lambda text: self.handle_selection(text, point)
        )
    
    # Connect to context menu signal
    web_view.customContextMenuRequested.connect(show_context_menu)
    
def handle_selection(self, selected_text, point):
    """Add menu items for selected text"""
    
    if selected_text:
        menu = QMenu()
        
        # Add our actions
        search_action = menu.addAction(
            f"Semantic Search: '{selected_text[:30]}...'"
        )
        search_action.triggered.connect(
            lambda: self.search_selected(selected_text)
        )
        
        # Show menu
        menu.exec_(point)
```

---

## Database Integration

### 1. Calibre Database Structure

```sql
-- Main tables we interact with (READ ONLY!)

-- Books table
CREATE TABLE books (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    sort TEXT,
    author_sort TEXT,
    timestamp TIMESTAMP,
    pubdate TIMESTAMP,
    series_index REAL,
    path TEXT,
    has_cover BOOL DEFAULT 0,
    last_modified TIMESTAMP NOT NULL
);

-- Authors table  
CREATE TABLE authors (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    sort TEXT
);

-- Many-to-many relationship
CREATE TABLE books_authors_link (
    id INTEGER PRIMARY KEY,
    book INTEGER NOT NULL,
    author INTEGER NOT NULL
);

-- Tags
CREATE TABLE tags (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

-- Custom columns (dynamic)
CREATE TABLE custom_column_N (
    id INTEGER PRIMARY KEY,
    value TEXT
);
```

### 2. Safe Database Access Patterns

```python
# PSEUDOCODE: Safe database access

# ALWAYS use new_api for thread safety
def get_book_metadata(self, book_id):
    """Safe way to get book metadata"""
    
    db = self.gui.current_db.new_api
    
    # Get metadata
    mi = db.get_metadata(book_id)
    
    # Extract what we need
    return {
        'title': mi.title,
        'authors': mi.authors,
        'tags': mi.tags,
        'pubdate': mi.pubdate,
        'series': mi.series,
        'language': mi.language,
        'format_metadata': mi.format_metadata
    }

# NEVER modify metadata.db directly!
# Create our own database instead:
def init_semantic_db(self):
    """Initialize our separate database"""
    
    library_path = self.gui.library_path
    semantic_path = os.path.join(library_path, 'semantic_search')
    os.makedirs(semantic_path, exist_ok=True)
    
    self.db_path = os.path.join(semantic_path, 'embeddings.db')
    # Initialize with our schema
```

### 3. Working with Book Formats

```python
# PSEUDOCODE: Extracting text from books

def extract_book_text(self, book_id):
    """Extract text from book for indexing"""
    
    db = self.gui.current_db.new_api
    
    # Get available formats
    formats = db.formats(book_id)
    
    # Prefer certain formats
    for fmt in ['EPUB', 'AZW3', 'MOBI', 'PDF', 'TXT']:
        if fmt in formats:
            path = db.format_abspath(book_id, fmt)
            return self.extract_text_from_format(path, fmt)
    
    return None

def extract_text_from_format(self, path, fmt):
    """Format-specific text extraction"""
    
    if fmt == 'EPUB':
        # Use calibre's epub library
        from calibre.ebooks.epub.input import EPUBInput
        epub = EPUBInput()
        # Extract text...
        
    elif fmt == 'PDF':
        # Use calibre's PDF library
        from calibre.ebooks.pdf.pdftohtml import pdftohtml
        # Extract text...
```

---

## Job System Integration

### 1. Background Job Architecture

```python
# PSEUDOCODE: Job system for long operations

from calibre.gui2.threaded_jobs import ThreadedJob

class IndexingJob(ThreadedJob):
    """Background job for indexing books"""
    
    def __init__(self, gui, book_ids, db_path):
        ThreadedJob.__init__(self, 'Indexing books for semantic search')
        self.gui = gui
        self.book_ids = book_ids
        self.db_path = db_path
        self.results = []
        self.errors = []
        
    def run(self):
        """Executed in background thread"""
        
        total = len(self.book_ids)
        
        for i, book_id in enumerate(self.book_ids):
            # Check if cancelled
            if self.abort_requested():
                break
                
            # Update progress
            self.set_progress(i / total, 
                f'Processing book {i+1} of {total}')
            
            try:
                # Process book
                self.index_book(book_id)
                self.results.append(book_id)
                
            except Exception as e:
                self.errors.append((book_id, str(e)))
                
            # Commit periodically
            if i % 10 == 0:
                self.commit_progress()
```

### 2. Progress Dialog Integration

```python
# PSEUDOCODE: Showing progress dialog

def start_indexing(self, book_ids):
    """Start indexing with progress dialog"""
    
    # Create job
    job = IndexingJob(self.gui, book_ids, self.db_path)
    
    # Configure callback
    job.callback = self.indexing_complete
    
    # Create progress dialog
    from calibre.gui2.dialogs.progress import ProgressDialog
    
    dialog = ProgressDialog(
        title='Semantic Search Indexing',
        msg='Starting indexing process...',
        max=len(book_ids),
        parent=self.gui,
        job=job
    )
    
    # Show dialog (blocks until complete)
    dialog.exec_()
    
def indexing_complete(self, job):
    """Called when job completes"""
    
    if job.errors:
        # Show error summary
        self.show_indexing_errors(job.errors)
    else:
        # Show success
        info_dialog(self.gui, 'Success',
            f'Indexed {len(job.results)} books')
```

---

## Configuration System

### 1. JSONConfig Usage

```python
# PSEUDOCODE: Configuration management

from calibre.utils.config import JSONConfig

class SemanticSearchConfig:
    """Configuration management"""
    
    # Default configuration
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
            'batch_size': 100
        }
    }
    
    def __init__(self):
        # Create config with defaults
        self.config = JSONConfig('plugins/semantic_search')
        self.config.defaults = self.DEFAULTS
        
    def get(self, key, default=None):
        """Get configuration value"""
        # Handle nested keys
        if '.' in key:
            parts = key.split('.')
            value = self.config
            for part in parts:
                value = value.get(part, {})
            return value or default
        return self.config.get(key, default)
```

### 2. Secure API Key Storage

```python
# PSEUDOCODE: Secure API key management

def store_api_key(self, provider, key):
    """Store API key securely"""
    
    # Use Calibre's password storage
    from calibre.utils.config import password_key
    
    # Encrypt the key
    encrypted = password_key(key)
    
    # Store in config
    api_keys = self.config.get('api_keys', {})
    api_keys[provider] = {
        'encrypted': True,
        'value': encrypted
    }
    self.config.set('api_keys', api_keys)

def get_api_key(self, provider):
    """Retrieve API key"""
    
    api_keys = self.config.get('api_keys', {})
    key_data = api_keys.get(provider, {})
    
    if key_data.get('encrypted'):
        # Decrypt
        from calibre.utils.config import password_key
        return password_key(key_data['value'], decrypt=True)
    
    return key_data.get('value')
```

---

## UI Integration Patterns

### 1. Menu and Toolbar Integration

```python
# PSEUDOCODE: Adding menus and toolbars

def genesis(self):
    """Initialize UI elements"""
    
    # Create menu
    self.menu = QMenu(self.gui)
    self.create_menu_items()
    
    # Add to menu bar
    self.qaction.setMenu(self.menu)
    self.qaction.setIcon(get_icons('semantic_search.png'))
    self.qaction.triggered.connect(self.show_dialog)
    
    # Add toolbar button
    self.toolbar_action = QAction(
        get_icons('search.png'),
        'Semantic Search',
        self.gui
    )
    self.toolbar_action.triggered.connect(self.toolbar_clicked)
    
    # Find calibre's toolbar and add our action
    for toolbar in self.gui.findChildren(QToolBar):
        if toolbar.objectName() == 'main_toolbar':
            toolbar.addAction(self.toolbar_action)
            break

def create_menu_items(self):
    """Create menu structure"""
    
    # Main search action
    self.search_action = QAction('Search Library...', self.gui)
    self.search_action.triggered.connect(self.show_search_dialog)
    self.menu.addAction(self.search_action)
    
    # Separator
    self.menu.addSeparator()
    
    # Indexing submenu
    index_menu = self.menu.addMenu('Indexing')
    
    index_selected = QAction('Index Selected Books', self.gui)
    index_selected.triggered.connect(self.index_selected_books)
    index_menu.addAction(index_selected)
    
    index_all = QAction('Index All Books', self.gui)
    index_all.triggered.connect(self.index_all_books)
    index_menu.addAction(index_all)
```

### 2. Dialog Integration

```python
# PSEUDOCODE: Creating plugin dialogs

class SemanticSearchDialog(QDialog):
    """Main search dialog"""
    
    def __init__(self, gui, plugin):
        QDialog.__init__(self, gui)
        self.gui = gui
        self.plugin = plugin
        
        # Window properties
        self.setWindowTitle('Semantic Search')
        self.setWindowFlags(
            Qt.Window |
            Qt.WindowMinimizeButtonHint |
            Qt.WindowMaximizeButtonHint |
            Qt.WindowCloseButtonHint
        )
        
        # Remember geometry
        self.restore_geometry()
        
    def restore_geometry(self):
        """Restore window size/position"""
        geometry = gprefs.get(
            'semantic_search_dialog_geometry',
            None
        )
        if geometry:
            self.restoreGeometry(geometry)
            
    def save_geometry(self):
        """Save window size/position"""
        gprefs.set(
            'semantic_search_dialog_geometry',
            self.saveGeometry()
        )
```

### 3. Library View Integration

```python
# PSEUDOCODE: Integrating with library view

def connect_to_library_view(self):
    """Connect to library view events"""
    
    library_view = self.gui.library_view
    
    # Selection changes
    library_view.selection_changed.connect(
        self.on_library_selection_changed
    )
    
    # Context menu
    library_view.context_menu.connect(
        self.add_library_context_menu
    )
    
def add_library_context_menu(self, menu):
    """Add items to library context menu"""
    
    selected = self.gui.library_view.get_selected_ids()
    
    if selected:
        menu.addSeparator()
        
        # Single book selected
        if len(selected) == 1:
            search_action = menu.addAction(
                'Semantic Search in This Book'
            )
            search_action.triggered.connect(
                lambda: self.search_in_book(selected[0])
            )
            
        # Multiple books
        index_action = menu.addAction(
            f'Index {len(selected)} Books for Semantic Search'
        )
        index_action.triggered.connect(
            lambda: self.index_books(selected)
        )
```

---

## Platform-Specific Considerations

### 1. File System Differences

```python
# PSEUDOCODE: Cross-platform file handling

import os
from pathlib import Path

def get_plugin_data_path(self):
    """Get platform-appropriate data path"""
    
    # Use library path as base
    library_path = Path(self.gui.library_path)
    
    # Create semantic search directory
    data_path = library_path / 'semantic_search'
    data_path.mkdir(exist_ok=True)
    
    # Platform-specific adjustments
    if iswindows:
        # Handle long paths on Windows
        data_path = Path(f'\\\\?\\{data_path}')
        
    return data_path

def normalize_path(self, path):
    """Normalize path for platform"""
    
    path = Path(path)
    
    if iswindows:
        # Convert to Windows style
        return str(path).replace('/', '\\')
    else:
        # POSIX style
        return str(path)
```

### 2. Qt Platform Differences

```python
# PSEUDOCODE: Handling Qt differences

def create_platform_ui(self):
    """Platform-specific UI adjustments"""
    
    if ismacos:
        # macOS specific
        self.setWindowFlags(
            self.windowFlags() | 
            Qt.WindowStaysOnTopHint
        )
        # Unified toolbar
        self.setUnifiedTitleAndToolBarOnMac(True)
        
    elif iswindows:
        # Windows specific
        # Handle high DPI
        if hasattr(Qt, 'AA_EnableHighDpiScaling'):
            QApplication.setAttribute(
                Qt.AA_EnableHighDpiScaling
            )
            
    elif islinux:
        # Linux specific
        # GTK theme integration
        self.setStyleSheet(
            self.get_gtk_compatible_stylesheet()
        )
```

### 3. Performance Tuning by Platform

```python
# PSEUDOCODE: Platform-specific optimizations

def get_platform_settings(self):
    """Platform-specific performance settings"""
    
    if iswindows:
        return {
            'max_threads': os.cpu_count() - 1,
            'chunk_size': 1024,  # Larger chunks on Windows
            'use_mmap': False    # mmap issues on Windows
        }
        
    elif ismacos:
        return {
            'max_threads': os.cpu_count() // 2,  # macOS scheduling
            'chunk_size': 512,
            'use_mmap': True
        }
        
    else:  # Linux
        return {
            'max_threads': os.cpu_count(),
            'chunk_size': 512,
            'use_mmap': True
        }
```

---

## Common Integration Pitfalls

### 1. Threading Issues

```python
# WRONG: Modifying GUI from thread
def run(self):
    # This will crash!
    self.gui.status_bar.showMessage('Processing...')

# CORRECT: Use signals or callbacks
def run(self):
    # Emit signal instead
    self.update_status.emit('Processing...')
    
# Or use Calibre's callback system
def run(self):
    self.callback = lambda: self.gui.status_bar.showMessage('Done')
```

### 2. Database Lock Issues

```python
# WRONG: Keeping database connection open
self.db_conn = sqlite3.connect(self.db_path)
# ... use connection throughout

# CORRECT: Open and close as needed
def execute_query(self, query, params=None):
    with sqlite3.connect(self.db_path) as conn:
        cursor = conn.execute(query, params or [])
        return cursor.fetchall()
```

### 3. Memory Management

```python
# WRONG: Loading all embeddings at once
embeddings = load_all_embeddings()  # Could be GBs!

# CORRECT: Load on demand
def get_embedding(self, chunk_id):
    # Load single embedding
    return self.load_embedding(chunk_id)
    
# Or use memory mapping
def setup_mmap_embeddings(self):
    self.embeddings = np.memmap(
        self.embedding_file,
        dtype='float32',
        mode='r',
        shape=(self.num_embeddings, self.dimensions)
    )
```

### 4. Update Compatibility

```python
# WRONG: Assuming API stability
viewer = self.gui.viewers[0]  # May not exist in future

# CORRECT: Defensive programming
viewers = getattr(self.gui, 'viewers', [])
if viewers:
    viewer = viewers[0]
else:
    # Handle missing viewer
    pass
```

---

## Testing Integration Points

### 1. Plugin Loading Test

```python
# TEST: Verify plugin loads correctly

def test_plugin_loads():
    """Test plugin can be loaded by Calibre"""
    
    # Simulate Calibre's loading process
    from calibre.customize import Plugin
    from calibre_plugins.semantic_search import SemanticSearchPlugin
    
    # Instantiate plugin
    plugin = SemanticSearchPlugin()
    
    # Verify metadata
    assert plugin.name == 'Semantic Search'
    assert plugin.version >= (1, 0, 0)
    assert plugin.minimum_calibre_version <= current_calibre_version()
```

### 2. Integration Test Harness

```python
# PSEUDOCODE: Integration test setup

class CalibreIntegrationTest:
    """Base class for integration tests"""
    
    def setup_method(self):
        """Setup test environment"""
        
        # Create temporary library
        self.temp_lib = create_temp_library()
        
        # Mock GUI
        self.gui = MockCalibreGUI(self.temp_lib)
        
        # Load plugin
        self.plugin = SemanticSearchPlugin()
        self.plugin.gui = self.gui
        self.plugin.genesis()
        
    def teardown_method(self):
        """Cleanup test environment"""
        
        # Shutdown plugin
        self.plugin.shutting_down()
        
        # Remove temp library
        shutil.rmtree(self.temp_lib)
```

### 3. Viewer Integration Test

```python
# TEST: Viewer integration

def test_viewer_integration():
    """Test viewer hooks work correctly"""
    
    # Create mock viewer
    viewer = MockEbookViewer()
    
    # Simulate show_viewer call
    plugin.show_viewer(viewer)
    
    # Verify our customizations
    assert hasattr(viewer, 'semantic_search_injected')
    assert 'Semantic Search' in viewer.get_context_menu_items()
```

---

## Best Practices Summary

### Do's
1. ✅ Use Calibre's APIs whenever possible
2. ✅ Handle errors gracefully
3. ✅ Test across platforms
4. ✅ Use background jobs for long operations
5. ✅ Store data in library folder
6. ✅ Use JSONConfig for settings
7. ✅ Clean up resources properly

### Don'ts
1. ❌ Modify Calibre's source files
2. ❌ Access private methods (_method)
3. ❌ Keep database connections open
4. ❌ Block the UI thread
5. ❌ Assume viewer structure
6. ❌ Hard-code paths
7. ❌ Ignore platform differences

This comprehensive integration guide provides all the necessary information to successfully integrate the semantic search plugin with Calibre's architecture while avoiding common pitfalls.