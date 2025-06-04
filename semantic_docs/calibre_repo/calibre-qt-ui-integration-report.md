# Agent 4: Qt/UI Integration Expert Report
## Complete Guide to Qt and UI Integration in Calibre Plugins

### Executive Summary

Qt integration in Calibre plugins requires understanding the custom import system, widget hierarchy, signal/slot mechanisms, and Calibre-specific UI patterns. This report provides comprehensive guidance on creating professional, integrated user interfaces that seamlessly blend with Calibre's native UI while avoiding common pitfalls.

### 1. Understanding Calibre's Qt Import System

#### The Golden Rule of Qt Imports

```python
# ✅ CORRECT - Always use this pattern
from qt.core import (
    Qt, QWidget, QDialog, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTableWidget,
    QMenu, QAction, pyqtSignal, QTimer, QThread
)

# ❌ WRONG - Never use direct imports
from PyQt5.QtWidgets import QWidget  # Will fail!
from PyQt6.QtCore import Qt  # Will fail!
import PyQt5  # Will fail!
```

#### Why qt.core?

```python
# Calibre's qt.core module provides:
# 1. Version abstraction (PyQt5/PyQt6)
# 2. Platform-specific patches
# 3. Calibre customizations
# 4. Consistent API across versions

# Behind the scenes (simplified):
# calibre/src/calibre/qt/__init__.py
try:
    from PyQt6 import *
    qt_version = 6
except ImportError:
    from PyQt5 import *
    qt_version = 5

# This abstraction ensures plugins work across Qt versions
```

### 2. Complete Qt Import Reference

#### Available Qt Modules Through qt.core

```python
# Complete list of available imports
from qt.core import (
    # Core
    Qt, QObject, QEvent, QTimer, QThread, QRunnable,
    QThreadPool, QMutex, QWaitCondition,
    pyqtSignal, pyqtSlot, QUrl, QByteArray,
    QPoint, QPointF, QRect, QRectF, QSize, QSizeF,
    QDate, QDateTime, QTime,
    
    # Widgets
    QApplication, QWidget, QMainWindow, QDialog,
    QLabel, QPushButton, QLineEdit, QTextEdit,
    QPlainTextEdit, QComboBox, QCheckBox, QRadioButton,
    QSpinBox, QDoubleSpinBox, QSlider, QDial,
    QProgressBar, QCalendarWidget, QDateEdit,
    QTimeEdit, QDateTimeEdit,
    
    # Containers
    QGroupBox, QTabWidget, QToolBox, QStackedWidget,
    QSplitter, QScrollArea, QMdiArea, QDockWidget,
    
    # Item Views
    QListView, QTreeView, QTableView, QColumnView,
    QListWidget, QTreeWidget, QTableWidget,
    QListWidgetItem, QTreeWidgetItem, QTableWidgetItem,
    
    # Layouts
    QLayout, QBoxLayout, QHBoxLayout, QVBoxLayout,
    QGridLayout, QFormLayout, QStackedLayout,
    
    # Dialogs
    QMessageBox, QInputDialog, QColorDialog,
    QFontDialog, QFileDialog, QProgressDialog,
    
    # Models
    QAbstractItemModel, QStandardItemModel,
    QStringListModel, QSortFilterProxyModel,
    
    # Graphics
    QPixmap, QImage, QIcon, QPainter, QPen, QBrush,
    QFont, QFontMetrics, QPalette, QColor,
    
    # Actions and Menus
    QAction, QMenu, QMenuBar, QToolBar, QStatusBar,
    QSystemTrayIcon,
    
    # Advanced
    QWebEngineView,  # If available
    QGraphicsScene, QGraphicsView, QGraphicsItem,
)
```

### 3. InterfaceAction Plugin Architecture

#### Complete InterfaceAction Implementation

```python
# __init__.py - Plugin wrapper
from calibre.customize import InterfaceActionBase

class SemanticSearchPlugin(InterfaceActionBase):
    """
    This wrapper class is loaded by Calibre's plugin system.
    It provides metadata and points to the actual implementation.
    """
    name = 'Semantic Search'
    description = 'Advanced semantic search for ebooks'
    supported_platforms = ['windows', 'osx', 'linux']
    author = 'Your Name'
    version = (1, 0, 0)
    minimum_calibre_version = (5, 0, 0)
    
    # Points to the actual GUI plugin implementation
    actual_plugin = 'calibre_plugins.semantic_search.ui:SemanticSearchAction'
    
    def is_customizable(self):
        """Allow users to customize the plugin"""
        return True
    
    def config_widget(self):
        """Return the configuration widget"""
        from calibre_plugins.semantic_search.config import ConfigWidget
        return ConfigWidget()
    
    def save_settings(self, config_widget):
        """Save the configuration"""
        config_widget.save_settings()
        
        # Apply settings to running plugin
        ac = self.actual_plugin_
        if ac is not None:
            ac.apply_settings()
```

#### Main UI Implementation

```python
# ui.py - Actual GUI implementation
from calibre.gui2.actions import InterfaceAction
from calibre.gui2 import error_dialog, info_dialog
from qt.core import QMenu, QToolButton, QAction

class SemanticSearchAction(InterfaceAction):
    """
    The actual GUI plugin implementation.
    This class handles all UI interactions.
    """
    
    name = 'Semantic Search'
    
    # Action specification: (text, icon, tooltip, keyboard shortcut)
    action_spec = ('Semantic Search', 'search.png', 
                   'Search books using semantic similarity', 'Ctrl+Shift+S')
    
    # Where to place the action
    dont_add_to = frozenset(['context-menu-device'])
    
    # Toolbar button behavior
    popup_type = QToolButton.ToolButtonPopupMode.MenuButtonPopup
    action_type = 'current'
    
    def genesis(self):
        """
        Called once when the plugin is first loaded.
        Set up the plugin's UI elements here.
        """
        # Create menu
        self.menu = QMenu(self.gui)
        self.qaction.setMenu(self.menu)
        
        # Add menu items
        self.search_action = self.create_menu_action(
            self.menu, 'search-library',
            'Search Library', icon='search.png',
            triggered=self.search_library,
            shortcut='Ctrl+Shift+S'
        )
        
        self.index_action = self.create_menu_action(
            self.menu, 'index-books',
            'Index Books', icon='exec.png',
            triggered=self.index_books
        )
        
        self.menu.addSeparator()
        
        self.config_action = self.create_menu_action(
            self.menu, 'configure',
            'Configure...', icon='config.png',
            triggered=self.show_configuration
        )
        
        # Connect main action
        self.qaction.triggered.connect(self.main_action)
    
    def initialization_complete(self):
        """
        Called after the main GUI is completely initialized.
        Safe to access all GUI elements here.
        """
        # Set initial state based on library
        self.update_state()
    
    def library_changed(self, db):
        """
        Called whenever a new library is opened.
        Update plugin state for the new library.
        """
        self.update_state()
    
    def update_state(self):
        """Update UI state based on current library"""
        # Check if index exists
        from calibre_plugins.semantic_search.index import IndexManager
        
        index_mgr = IndexManager(self.gui.current_db)
        has_index = index_mgr.index_exists()
        
        # Update action states
        self.search_action.setEnabled(has_index)
        self.qaction.setEnabled(True)
        
        # Update tooltip
        if not has_index:
            self.qaction.setToolTip(
                'Semantic Search (index required - click to create)'
            )
```

### 4. Creating Dialogs

#### Base Dialog Pattern

```python
from calibre.gui2.widgets2 import Dialog
from qt.core import (
    QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QDialogButtonBox
)

class SemanticSearchDialog(Dialog):
    """
    Base pattern for Calibre dialogs.
    Inherits from calibre.gui2.widgets2.Dialog for consistency.
    """
    
    def __init__(self, parent, icon):
        # Dialog name used for saving geometry
        Dialog.__init__(self, 'Semantic Search', 'semantic_search_dialog', parent)
        
        self.gui = parent
        self.setWindowIcon(icon)
        
        self.setup_ui()
        
        # Restore saved geometry
        self.restore_geometry()
    
    def setup_ui(self):
        """Create the dialog UI"""
        layout = QVBoxLayout(self)
        
        # Add widgets
        self.create_search_area(layout)
        self.create_results_area(layout)
        self.create_button_box(layout)
    
    def create_search_area(self, parent_layout):
        """Create search input area"""
        search_layout = QHBoxLayout()
        
        search_layout.addWidget(QLabel('Search:'))
        
        from qt.core import QLineEdit, QCompleter
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('Enter search terms...')
        
        # Add auto-completion
        completer = QCompleter(self.get_search_history())
        self.search_input.setCompleter(completer)
        
        search_layout.addWidget(self.search_input)
        
        self.search_button = QPushButton('Search')
        self.search_button.clicked.connect(self.perform_search)
        search_layout.addWidget(self.search_button)
        
        parent_layout.addLayout(search_layout)
    
    def create_button_box(self, parent_layout):
        """Create standard button box"""
        self.bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        self.bb.rejected.connect(self.reject)
        parent_layout.addWidget(self.bb)
```

#### Advanced Dialog Features

```python
from qt.core import (
    QSplitter, QTableWidget, QTableWidgetItem,
    QHeaderView, Qt, QMenu, QAbstractItemView
)

class AdvancedSearchDialog(Dialog):
    """Advanced dialog with splitter and table"""
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Create splitter for resizable panes
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Top pane - search options
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        self.create_search_options(top_layout)
        splitter.addWidget(top_widget)
        
        # Bottom pane - results table
        self.results_table = self.create_results_table()
        splitter.addWidget(self.results_table)
        
        # Set initial splitter sizes (60% top, 40% bottom)
        splitter.setSizes([600, 400])
        
        layout.addWidget(splitter)
        
        # Status bar
        from qt.core import QStatusBar
        self.status_bar = QStatusBar()
        layout.addWidget(self.status_bar)
    
    def create_results_table(self):
        """Create a results table with context menu"""
        table = QTableWidget()
        
        # Set columns
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels([
            'Title', 'Author', 'Score', 'Tags'
        ])
        
        # Configure behavior
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        table.setSortingEnabled(True)
        
        # Resize columns
        header = table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        
        # Context menu
        table.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        table.customContextMenuRequested.connect(
            self.show_context_menu
        )
        
        return table
    
    def show_context_menu(self, pos):
        """Show context menu for table"""
        table = self.sender()
        item = table.itemAt(pos)
        
        if item is None:
            return
        
        menu = QMenu(self)
        
        # Add actions
        view_action = menu.addAction('View Book')
        view_action.triggered.connect(
            lambda: self.view_book(item.row())
        )
        
        edit_action = menu.addAction('Edit Metadata')
        edit_action.triggered.connect(
            lambda: self.edit_metadata(item.row())
        )
        
        menu.addSeparator()
        
        copy_action = menu.addAction('Copy Title')
        copy_action.triggered.connect(
            lambda: self.copy_to_clipboard(item.row(), 0)
        )
        
        # Show menu
        menu.exec(table.mapToGlobal(pos))
```

### 5. Background Tasks and Threading

#### Using ThreadedJob for Long Operations

```python
from calibre.gui2.threaded_jobs import ThreadedJob
from qt.core import QTimer

class IndexingJob:
    """Background job for indexing books"""
    
    def __init__(self, gui, books_to_index):
        self.gui = gui
        self.books_to_index = books_to_index
        self.current_book = 0
        self.total_books = len(books_to_index)
    
    def start(self):
        """Start the background job"""
        job = ThreadedJob(
            'semantic_search_indexing',  # Job name
            'Indexing books for semantic search',  # Description
            self.run,  # Function to run in background
            self.done,  # Function to call when complete
            max_concurrent_count=1,  # Only one at a time
        )
        
        self.gui.job_manager.run_threaded_job(job)
        self.gui.status_bar.show_message(
            'Indexing books...', 0
        )
    
    def run(self):
        """
        Run in background thread.
        Cannot access GUI elements here!
        """
        results = []
        
        for i, book_id in enumerate(self.books_to_index):
            # Report progress
            self.set_progress(i, self.total_books)
            
            # Process book
            try:
                embedding = self.generate_embedding(book_id)
                results.append((book_id, embedding))
            except Exception as e:
                self.set_exception(e)
                return None
            
            # Check if cancelled
            if self.is_aborted():
                return None
        
        return results
    
    def done(self, job):
        """
        Called in main thread when job completes.
        Safe to access GUI here.
        """
        if job.failed:
            error_dialog(
                self.gui, 
                'Indexing Failed',
                'Failed to index books.',
                det_msg=str(job.exception),
                show=True
            )
            return
        
        if job.result is None:
            # Cancelled
            self.gui.status_bar.show_message('Indexing cancelled', 5000)
            return
        
        # Success - update UI
        results = job.result
        self.gui.status_bar.show_message(
            f'Indexed {len(results)} books', 5000
        )
        
        # Trigger UI update
        self.gui.tags_view.recount()
    
    def set_progress(self, current, total):
        """Update progress (called from background thread)"""
        percent = int((current / total) * 100)
        self.set_percent(percent)
```

#### Progress Dialog Integration

```python
from qt.core import QProgressDialog, Qt

class ProgressJob:
    """Job with progress dialog"""
    
    def __init__(self, gui):
        self.gui = gui
        self.pd = None
    
    def start_with_progress(self):
        """Start job with progress dialog"""
        self.pd = QProgressDialog(
            'Processing books...',
            'Cancel',
            0, 100,
            self.gui
        )
        self.pd.setWindowTitle('Semantic Search')
        self.pd.setWindowModality(Qt.WindowModality.WindowModal)
        self.pd.setAutoClose(True)
        self.pd.setMinimumDuration(0)
        
        # Connect cancel
        self.pd.canceled.connect(self.cancel_job)
        
        # Start job
        self.job = ThreadedJob(
            'progress_job',
            'Processing',
            self.run_with_progress,
            self.progress_done
        )
        
        # Update progress periodically
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(100)  # Update every 100ms
        
        self.gui.job_manager.run_threaded_job(self.job)
    
    def update_progress(self):
        """Update progress dialog"""
        if hasattr(self.job, 'percent'):
            self.pd.setValue(self.job.percent)
```

### 6. Calibre-Specific UI Components

#### Using Calibre's Custom Widgets

```python
from calibre.gui2.widgets import BusyCursor
from calibre.gui2.complete2 import EditWithComplete
from calibre.gui2.widgets2 import ColorButton

class CalibreWidgetsExample(QWidget):
    """Examples of Calibre-specific widgets"""
    
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        
        # 1. EditWithComplete - Input with completion
        self.author_input = EditWithComplete(self)
        self.author_input.set_separator('&')
        self.author_input.update_items_cache(
            self.get_all_authors()
        )
        layout.addWidget(self.author_input)
        
        # 2. ColorButton - Color picker button
        self.color_button = ColorButton(self)
        self.color_button.color = '#ff0000'
        self.color_button.color_changed.connect(
            self.on_color_changed
        )
        layout.addWidget(self.color_button)
        
        # 3. BusyCursor - Context manager for busy cursor
        self.process_button = QPushButton('Process')
        self.process_button.clicked.connect(self.process)
        layout.addWidget(self.process_button)
    
    def process(self):
        """Show busy cursor during processing"""
        with BusyCursor():
            # Long operation
            import time
            time.sleep(2)
```

#### Tag Browser Integration

```python
class TagBrowserIntegration:
    """Integrate with Calibre's tag browser"""
    
    def add_to_tag_browser_context_menu(self):
        """Add items to tag browser context menu"""
        
        def create_menu(self, menu, index):
            """Called when creating context menu"""
            if not index.isValid():
                return
            
            # Get the tag item
            item = index.data(Qt.ItemDataRole.UserRole)
            if item.type != TagTreeItem.TAG:
                return
            
            # Add our action
            action = menu.addAction(
                'Search Similar Books',
                lambda: self.search_similar_tag(item.name)
            )
        
        # In genesis():
        self.gui.tags_view.context_menu_handler = create_menu
```

### 7. Event Handling and Signals

#### Custom Signals and Events

```python
from qt.core import pyqtSignal, QObject

class SearchEngine(QObject):
    """Search engine with custom signals"""
    
    # Custom signals
    search_started = pyqtSignal()
    search_progress = pyqtSignal(int, int)  # current, total
    search_completed = pyqtSignal(list)  # results
    search_error = pyqtSignal(str)  # error message
    
    def __init__(self):
        super().__init__()
        self.cancelled = False
    
    def search(self, query):
        """Perform search and emit signals"""
        self.cancelled = False
        self.search_started.emit()
        
        try:
            results = []
            total = self.estimate_work(query)
            
            for i in range(total):
                if self.cancelled:
                    break
                
                # Do work
                result = self.search_one(i)
                if result:
                    results.append(result)
                
                # Report progress
                self.search_progress.emit(i + 1, total)
            
            self.search_completed.emit(results)
            
        except Exception as e:
            self.search_error.emit(str(e))
    
    def cancel(self):
        """Cancel the search"""
        self.cancelled = True

# Using the search engine
class SearchWidget(QWidget):
    def __init__(self):
        super().__init__()
        
        self.engine = SearchEngine()
        
        # Connect signals
        self.engine.search_started.connect(
            self.on_search_started
        )
        self.engine.search_progress.connect(
            self.on_search_progress
        )
        self.engine.search_completed.connect(
            self.on_search_completed
        )
        self.engine.search_error.connect(
            self.on_search_error
        )
```

### 8. Keyboard Shortcuts and Actions

#### Managing Keyboard Shortcuts

```python
class ShortcutManager:
    """Manage plugin keyboard shortcuts"""
    
    def register_shortcuts(self):
        """Register all shortcuts during genesis()"""
        
        # Register shortcut with Calibre
        self.register_shortcut(
            self.search_action,  # QAction
            'semantic-search',   # Unique name
            default_keys=('Ctrl+Shift+S',),  # Default
            description='Open semantic search dialog'
        )
        
        # Multiple shortcuts for one action
        self.register_shortcut(
            self.index_action,
            'semantic-index',
            default_keys=('Ctrl+Shift+I', 'F7'),
            description='Index books for semantic search'
        )
    
    def create_action_with_shortcut(self, parent, unique_name, 
                                   text, icon, triggered,
                                   default_keys=None):
        """Create action with registered shortcut"""
        action = QAction(icon, text, parent)
        
        if default_keys:
            self.register_shortcut(
                action, unique_name, 
                default_keys=default_keys
            )
        
        action.triggered.connect(triggered)
        return action
```

### 9. Styling and Theming

#### Respecting Calibre's Theme

```python
from calibre.gui2 import gprefs

class ThemedWidget(QWidget):
    """Widget that respects Calibre's theme"""
    
    def __init__(self):
        super().__init__()
        self.setup_theme()
    
    def setup_theme(self):
        """Apply theme-aware styling"""
        # Check if dark theme
        is_dark = gprefs.get('ui_style') == 'dark'
        
        if is_dark:
            # Dark theme colors
            self.setStyleSheet('''
                QWidget {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QPushButton {
                    background-color: #3c3c3c;
                    border: 1px solid #555;
                    padding: 5px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #484848;
                }
            ''')
        else:
            # Light theme colors
            self.setStyleSheet('''
                QWidget {
                    background-color: #ffffff;
                    color: #000000;
                }
                QPushButton {
                    background-color: #f0f0f0;
                    border: 1px solid #ccc;
                    padding: 5px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
            ''')
```

### 10. Common Pitfalls and Solutions

#### Pitfall Prevention Guide

```python
class UIBestPractices:
    """Common pitfalls and their solutions"""
    
    # PITFALL 1: Wrong imports
    @staticmethod
    def correct_imports():
        """Always use qt.core imports"""
        # ❌ WRONG
        # from PyQt5.QtWidgets import QWidget
        
        # ✅ CORRECT
        from qt.core import QWidget
    
    # PITFALL 2: Accessing GUI from background thread
    @staticmethod
    def thread_safe_gui_update(self):
        """Update GUI safely from threads"""
        # ❌ WRONG - Direct GUI access from thread
        # def run(self):
        #     self.label.setText('Done')  # Will crash!
        
        # ✅ CORRECT - Use signals or callback
        def run(self):
            return "Done"  # Return result
        
        def done(self, job):
            self.label.setText(job.result)  # Safe in main thread
    
    # PITFALL 3: Not saving dialog geometry
    @staticmethod
    def save_dialog_state(self):
        """Save and restore dialog state"""
        # In dialog __init__:
        self.restore_geometry(gprefs.get(
            'semantic_search_dialog_geometry', None
        ))
        
        # Override accept/reject:
        def accept(self):
            gprefs['semantic_search_dialog_geometry'] = \
                bytearray(self.saveGeometry())
            super().accept()
    
    # PITFALL 4: Memory leaks with connections
    @staticmethod
    def prevent_memory_leaks(self):
        """Prevent memory leaks"""
        # Disconnect signals when done
        def cleanup(self):
            try:
                self.signal.disconnect()
            except:
                pass  # Already disconnected
    
    # PITFALL 5: Not handling library changes
    @staticmethod
    def handle_library_changes(self):
        """Update plugin for library changes"""
        def library_changed(self, db):
            # Clear caches
            self.cache.clear()
            
            # Update UI state
            self.update_actions()
            
            # Reload configuration
            self.load_library_config()
```

### 11. Advanced UI Patterns

#### Dockable Widget

```python
from qt.core import QDockWidget, Qt

class SearchDock(QDockWidget):
    """Dockable search panel"""
    
    def __init__(self, gui):
        super().__init__('Semantic Search', gui)
        self.gui = gui
        
        # Configure dock
        self.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea |
            Qt.DockWidgetArea.RightDockWidgetArea
        )
        
        # Create content
        self.widget = SearchPanel(gui)
        self.setWidget(self.widget)
        
        # Add to main window
        gui.addDockWidget(
            Qt.DockWidgetArea.RightDockWidgetArea, 
            self
        )
        
        # Save state
        self.visibilityChanged.connect(
            self.save_dock_state
        )
```

#### Custom Book Details Tab

```python
class BookDetailsTab:
    """Add tab to book details panel"""
    
    def add_to_book_details(self):
        """Add semantic search tab"""
        from calibre.gui2.book_details import BookDetails
        
        # Create widget for tab
        class SemanticTab(QWidget):
            def __init__(self, parent):
                super().__init__(parent)
                layout = QVBoxLayout(self)
                
                self.similar_books = QListWidget()
                layout.addWidget(QLabel('Similar Books:'))
                layout.addWidget(self.similar_books)
            
            def update_for_book(self, book_id):
                """Update tab for selected book"""
                # Find similar books
                similar = self.find_similar(book_id)
                
                self.similar_books.clear()
                for book in similar:
                    self.similar_books.addItem(
                        f"{book['title']} by {book['author']}"
                    )
        
        # Register tab
        BookDetails.add_plugin_tab(
            'Semantic Search',
            SemanticTab
        )
```

### 12. Testing UI Plugins

#### UI Testing Strategies

```python
class UITester:
    """Testing strategies for UI plugins"""
    
    @staticmethod
    def create_test_gui():
        """Create minimal GUI for testing"""
        from calibre.gui2.main import FakeMainWindow
        
        app = QApplication([])
        gui = FakeMainWindow()
        
        # Add minimal components
        gui.library_view = QTableView()
        gui.tags_view = QTreeView()
        gui.status_bar = QStatusBar()
        
        return app, gui
    
    @staticmethod
    def test_dialog():
        """Test dialog in isolation"""
        app = QApplication([])
        
        dialog = SemanticSearchDialog(None, QIcon())
        dialog.show()
        
        # Simulate user input
        QTest.keyClicks(
            dialog.search_input, 
            "test query"
        )
        QTest.mouseClick(
            dialog.search_button,
            Qt.MouseButton.LeftButton
        )
        
        app.exec()
```

### Conclusions and Best Practices

1. **Always use qt.core imports** - Never import PyQt directly
2. **Respect the thread boundary** - GUI updates only in main thread
3. **Save UI state** - Remember window positions and sizes
4. **Handle library changes** - Plugins must adapt to library switches
5. **Use Calibre's widgets** - Leverage built-in components for consistency
6. **Follow Calibre patterns** - Study built-in plugins for examples
7. **Test thoroughly** - Test with different themes and window sizes
8. **Provide keyboard shortcuts** - Make plugin keyboard-friendly
9. **Show progress** - Use ThreadedJob for long operations
10. **Handle errors gracefully** - Always show meaningful error messages

The key to successful UI integration is understanding that Calibre provides a rich set of UI components and patterns - use them rather than reinventing the wheel.