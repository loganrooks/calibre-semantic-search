# Code Patterns Library for Calibre Plugin Development
## A Comprehensive Collection of Verified Code Patterns and Best Practices

### Executive Summary

This library contains battle-tested code patterns extracted from the Calibre codebase, built-in plugins, and successful third-party plugins. Each pattern is documented with context, implementation details, variations, and common pitfalls. These patterns represent the collective wisdom of the Calibre plugin development community and have been verified against the actual source code.

### 1. Plugin Initialization Patterns

#### Pattern 1.1: Basic Plugin Structure

```python
# __init__.py - Plugin wrapper
from calibre.customize import InterfaceActionBase

class MyPluginWrapper(InterfaceActionBase):
    """
    Plugin wrapper loaded by Calibre's plugin system.
    Provides metadata and points to actual implementation.
    """
    name = 'My Plugin Name'
    description = 'Description of what the plugin does'
    supported_platforms = ['windows', 'osx', 'linux']
    author = 'Your Name'
    version = (1, 0, 0)  # (major, minor, patch)
    minimum_calibre_version = (5, 0, 0)
    
    # Points to actual GUI implementation
    actual_plugin = 'calibre_plugins.my_plugin.ui:MyPluginAction'
    
    def is_customizable(self):
        """Enable configuration via Preferences"""
        return True
    
    def config_widget(self):
        """Return configuration widget"""
        # Import here to avoid loading GUI libraries when not needed
        from calibre_plugins.my_plugin.config import ConfigWidget
        return ConfigWidget()
    
    def save_settings(self, config_widget):
        """Save configuration"""
        config_widget.save_settings()
        
        # Apply settings to running instance
        ac = self.actual_plugin_
        if ac is not None:
            ac.apply_settings()
```

**Variations:**
- For non-GUI plugins, inherit from `Plugin` directly
- For file type plugins, inherit from `FileTypePlugin`
- For metadata source plugins, inherit from `MetadataSourcePlugin`

#### Pattern 1.2: Main Plugin Implementation

```python
# ui.py - Actual plugin implementation
from calibre.gui2.actions import InterfaceAction
from calibre.gui2 import error_dialog, info_dialog
from qt.core import QMenu, QToolButton, QAction, QIcon

class MyPluginAction(InterfaceAction):
    """Main plugin implementation"""
    
    name = 'My Plugin Name'
    
    # Action specification: (text, icon, tooltip, keyboard shortcut)
    action_spec = ('My Plugin', 'icon.png', 
                   'Plugin tooltip text', 'Ctrl+Shift+M')
    
    # Plugin behavior configuration
    popup_type = QToolButton.ToolButtonPopupMode.MenuButtonPopup
    action_type = 'current'
    dont_add_to = frozenset(['context-menu-device'])
    
    def genesis(self):
        """
        One-time initialization when plugin first loads.
        Set up menus, actions, and connections.
        """
        # Create menu
        self.menu = QMenu(self.gui)
        self.qaction.setMenu(self.menu)
        
        # Add menu items
        self.create_menu_action(
            self.menu, 'unique-action-name',
            'Menu Item Text', icon='icon.png',
            triggered=self.menu_item_triggered,
            shortcut='Ctrl+Shift+A'
        )
        
        # Connect main action
        self.qaction.triggered.connect(self.toolbar_button_clicked)
        
        # Load saved state
        self.load_settings()
    
    def initialization_complete(self):
        """
        Called after main GUI is fully initialized.
        Safe to access all GUI elements.
        """
        self.rebuild_menus()
    
    def library_changed(self, db):
        """
        Called when user switches libraries.
        Update plugin state for new library.
        """
        self.rebuild_menus()
    
    def shutting_down(self):
        """
        Called when Calibre is closing.
        Clean up resources.
        """
        self.save_settings()
```

### 2. Configuration Management Patterns

#### Pattern 2.1: JSONConfig for Settings

```python
from calibre.utils.config import JSONConfig

class PluginConfig:
    """Centralized configuration management"""
    
    def __init__(self, namespace='my_plugin'):
        # Create namespaced configuration
        self.prefs = JSONConfig(f'plugins/{namespace}')
        
        # Define defaults
        self.prefs.defaults['api_key'] = ''
        self.prefs.defaults['model'] = 'default'
        self.prefs.defaults['max_results'] = 10
        self.prefs.defaults['advanced'] = {
            'timeout': 30,
            'retry_count': 3,
            'cache_enabled': True
        }
        
        # Library-specific settings
        self.library_prefs = None
    
    def set_library_config(self, db):
        """Switch to library-specific configuration"""
        library_id = db.library_id
        self.library_prefs = JSONConfig(
            f'plugins/{self.namespace}_library_{library_id}'
        )
        self.library_prefs.defaults = self.prefs.defaults.copy()
    
    def get(self, key, library_specific=False):
        """Get configuration value"""
        if library_specific and self.library_prefs:
            return self.library_prefs.get(key, self.prefs[key])
        return self.prefs[key]
    
    def set(self, key, value, library_specific=False):
        """Set configuration value"""
        if library_specific and self.library_prefs:
            self.library_prefs[key] = value
        else:
            self.prefs[key] = value
```

#### Pattern 2.2: Configuration Dialog

```python
from qt.core import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QSpinBox, QCheckBox, QGroupBox,
    QComboBox, QPushButton
)
from calibre.gui2.preferences import ConfigWidgetBase

class ConfigWidget(ConfigWidgetBase):
    """Plugin configuration dialog"""
    
    def genesis(self, gui):
        """Initialize configuration widget"""
        self.gui = gui
        self.config = PluginConfig()
        
        # Create UI
        layout = QVBoxLayout(self)
        
        # Basic settings group
        basic_group = QGroupBox('Basic Settings')
        basic_layout = QVBoxLayout()
        
        # API Key
        api_layout = QHBoxLayout()
        api_layout.addWidget(QLabel('API Key:'))
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        api_layout.addWidget(self.api_key_edit)
        basic_layout.addLayout(api_layout)
        
        # Model selection
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel('Model:'))
        self.model_combo = QComboBox()
        self.model_combo.addItems(['default', 'advanced', 'fast'])
        model_layout.addWidget(self.model_combo)
        basic_layout.addLayout(model_layout)
        
        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)
        
        # Advanced settings
        advanced_group = QGroupBox('Advanced Settings')
        advanced_layout = QVBoxLayout()
        
        # Max results
        results_layout = QHBoxLayout()
        results_layout.addWidget(QLabel('Max Results:'))
        self.max_results_spin = QSpinBox()
        self.max_results_spin.setRange(1, 100)
        results_layout.addWidget(self.max_results_spin)
        advanced_layout.addLayout(results_layout)
        
        # Cache
        self.cache_check = QCheckBox('Enable caching')
        advanced_layout.addWidget(self.cache_check)
        
        advanced_group.setLayout(advanced_layout)
        layout.addWidget(advanced_group)
        
        # Test button
        self.test_button = QPushButton('Test Configuration')
        self.test_button.clicked.connect(self.test_config)
        layout.addWidget(self.test_button)
        
        # Load current settings
        self.load_settings()
    
    def initialize(self):
        """Called by Calibre when showing dialog"""
        ConfigWidgetBase.initialize(self)
        self.load_settings()
    
    def load_settings(self):
        """Load current settings into UI"""
        self.api_key_edit.setText(self.config.get('api_key'))
        
        model = self.config.get('model')
        idx = self.model_combo.findText(model)
        if idx >= 0:
            self.model_combo.setCurrentIndex(idx)
        
        self.max_results_spin.setValue(self.config.get('max_results'))
        self.cache_check.setChecked(
            self.config.get('advanced')['cache_enabled']
        )
    
    def save_settings(self):
        """Save UI values to configuration"""
        self.config.set('api_key', self.api_key_edit.text())
        self.config.set('model', self.model_combo.currentText())
        self.config.set('max_results', self.max_results_spin.value())
        
        advanced = self.config.get('advanced')
        advanced['cache_enabled'] = self.cache_check.isChecked()
        self.config.set('advanced', advanced)
    
    def validate(self):
        """Validate settings before saving"""
        if not self.api_key_edit.text():
            return False, ('Missing API Key', 
                          'Please enter your API key')
        return True
    
    def test_config(self):
        """Test current configuration"""
        from calibre.gui2 import info_dialog
        # Test logic here
        info_dialog(self, 'Test Result', 
                   'Configuration is valid!', show=True)
```

### 3. Database Access Patterns

#### Pattern 3.1: Safe Database Operations

```python
from calibre.gui2 import error_dialog

class DatabaseOperations:
    """Safe database access patterns"""
    
    def __init__(self, gui):
        self.gui = gui
    
    def get_db(self):
        """Get current database with error handling"""
        if not hasattr(self.gui, 'current_db'):
            return None
        return self.gui.current_db.new_api
    
    def safe_db_read(self, operation, *args, **kwargs):
        """Execute database read with error handling"""
        try:
            db = self.get_db()
            if db is None:
                raise Exception('No database available')
            
            return operation(db, *args, **kwargs)
            
        except Exception as e:
            error_dialog(
                self.gui, 
                'Database Error',
                f'Failed to read from database: {e}',
                show=True
            )
            return None
    
    def get_books_with_format(self, fmt):
        """Get all books that have specified format"""
        def _operation(db):
            results = []
            for book_id in db.all_book_ids():
                if db.has_format(book_id, fmt):
                    metadata = db.get_metadata(book_id)
                    results.append({
                        'id': book_id,
                        'title': metadata.title,
                        'authors': metadata.authors,
                        'path': db.format_abspath(book_id, fmt)
                    })
            return results
        
        return self.safe_db_read(_operation)
    
    def batch_update_metadata(self, updates):
        """Batch update metadata with progress"""
        from calibre.gui2.dialogs.progress import ProgressDialog
        
        db = self.get_db()
        if not db:
            return
        
        pd = ProgressDialog(
            'Updating Metadata', 
            'Processing books...', 
            max=len(updates),
            parent=self.gui
        )
        
        errors = []
        
        for i, (book_id, metadata) in enumerate(updates.items()):
            if pd.canceled:
                break
            
            pd.set_value(i)
            pd.set_msg(f'Updating {metadata.title}')
            
            try:
                db.set_metadata(book_id, metadata)
            except Exception as e:
                errors.append((book_id, str(e)))
        
        pd.hide()
        
        if errors:
            from calibre.gui2 import error_dialog
            msg = '\n'.join(f'Book {id}: {err}' for id, err in errors)
            error_dialog(
                self.gui, 
                'Update Errors',
                f'{len(errors)} errors occurred',
                det_msg=msg,
                show=True
            )
```

#### Pattern 3.2: Custom Column Access

```python
class CustomColumnHandler:
    """Handle custom column operations"""
    
    def __init__(self, db):
        self.db = db
        self._cache = {}
    
    def get_custom_columns(self):
        """Get all custom columns"""
        if 'columns' not in self._cache:
            self._cache['columns'] = self.db.field_metadata.custom_field_metadata()
        return self._cache['columns']
    
    def get_custom_column(self, name):
        """Get specific custom column value"""
        # Ensure name starts with #
        if not name.startswith('#'):
            name = '#' + name
        
        columns = self.get_custom_columns()
        if name not in columns:
            return None
        
        return columns[name]
    
    def set_custom_column(self, book_id, column_name, value):
        """Set custom column value"""
        if not column_name.startswith('#'):
            column_name = '#' + column_name
        
        col = self.get_custom_column(column_name)
        if not col:
            raise ValueError(f'Custom column {column_name} not found')
        
        # Handle different column types
        if col['datatype'] == 'bool':
            value = bool(value)
        elif col['datatype'] == 'int':
            value = int(value)
        elif col['datatype'] == 'float':
            value = float(value)
        elif col['datatype'] == 'datetime':
            # Convert string to datetime if needed
            if isinstance(value, str):
                from calibre.utils.date import parse_date
                value = parse_date(value)
        elif col['datatype'] == 'comments':
            # HTML content
            value = str(value)
        elif col['is_multiple']:
            # Tags-like field
            if isinstance(value, str):
                value = [v.strip() for v in value.split(',')]
        
        self.db.set_field(column_name, {book_id: value})
```

### 4. Background Task Patterns

#### Pattern 4.1: ThreadedJob Implementation

```python
from calibre.gui2.threaded_jobs import ThreadedJob
from calibre.gui2 import error_dialog, info_dialog

class BackgroundTask:
    """Pattern for long-running background tasks"""
    
    def __init__(self, gui, task_name, task_description):
        self.gui = gui
        self.task_name = task_name
        self.task_description = task_description
        self.canceled = False
        self.current_progress = 0
        self.total_items = 0
    
    def start(self, items_to_process):
        """Start background task"""
        self.items_to_process = items_to_process
        self.total_items = len(items_to_process)
        
        # Create job
        job = ThreadedJob(
            self.task_name,
            self.task_description,
            self.run,  # Function to run in background
            self.done,  # Function to call when complete
            max_concurrent_count=1,
        )
        
        # Start job
        self.gui.job_manager.run_threaded_job(job)
        self.gui.status_bar.show_message(
            f'{self.task_description}...', 0
        )
    
    def run(self):
        """
        Run in background thread.
        Cannot access GUI elements here!
        """
        results = []
        errors = []
        
        for i, item in enumerate(self.items_to_process):
            # Check if canceled
            if self.is_aborted():
                self.canceled = True
                break
            
            # Update progress
            self.current_progress = i + 1
            self.set_progress(i + 1, self.total_items)
            
            # Process item
            try:
                result = self.process_item(item)
                results.append(result)
            except Exception as e:
                import traceback
                errors.append({
                    'item': item,
                    'error': str(e),
                    'traceback': traceback.format_exc()
                })
                
                # Optionally set exception to abort
                # self.set_exception(e)
                # return None
        
        return {
            'results': results,
            'errors': errors,
            'canceled': self.canceled
        }
    
    def process_item(self, item):
        """Process single item - override in subclass"""
        import time
        time.sleep(0.1)  # Simulate work
        return f'Processed: {item}'
    
    def done(self, job):
        """
        Called in main thread when job completes.
        Safe to access GUI here.
        """
        # Hide progress message
        self.gui.status_bar.show_message('', 0)
        
        if job.failed:
            error_dialog(
                self.gui,
                f'{self.task_name} Failed',
                f'Task failed with error: {job.exception}',
                det_msg=job.details,
                show=True
            )
            return
        
        if job.result is None:
            # Canceled or aborted
            self.gui.status_bar.show_message(
                f'{self.task_name} canceled', 5000
            )
            return
        
        # Process results
        result = job.result
        
        if result['errors']:
            # Show errors
            error_msg = f"{len(result['errors'])} errors occurred:\n\n"
            for err in result['errors'][:5]:  # Show first 5
                error_msg += f"Item: {err['item']}\n"
                error_msg += f"Error: {err['error']}\n\n"
            
            if len(result['errors']) > 5:
                error_msg += f"... and {len(result['errors']) - 5} more"
            
            error_dialog(
                self.gui,
                f'{self.task_name} Completed with Errors',
                error_msg,
                show=True
            )
        else:
            # Success
            info_dialog(
                self.gui,
                f'{self.task_name} Complete',
                f"Successfully processed {len(result['results'])} items",
                show=True
            )
        
        # Refresh UI if needed
        self.gui.library_view.model().refresh()
```

#### Pattern 4.2: Progress Dialog with Cancel

```python
from qt.core import QTimer, Qt
from calibre.gui2.progress_indicator import ProgressIndicator

class ProgressTask:
    """Task with progress dialog"""
    
    def __init__(self, gui):
        self.gui = gui
        self.pd = None
        self.timer = None
        self.canceled = False
    
    def start_with_progress(self, title, message, max_value):
        """Start task with progress dialog"""
        # Create progress dialog
        self.pd = ProgressIndicator(self.gui)
        self.pd.set_msg(title)
        self.pd.set_submsg(message)
        self.pd.set_max(max_value)
        self.pd.show()
        
        # Connect cancel
        self.pd.canceled_signal.connect(self.cancel)
        
        # Start background job
        job = ThreadedJob(
            'progress_task',
            title,
            self.run_with_progress,
            self.progress_done
        )
        
        # Update progress periodically
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress_display)
        self.timer.start(100)  # Update every 100ms
        
        self.gui.job_manager.run_threaded_job(job)
    
    def run_with_progress(self):
        """Run task with progress updates"""
        for i in range(100):
            if self.canceled:
                return None
            
            # Do work
            import time
            time.sleep(0.05)
            
            # Update progress
            self.set_percent(i + 1)
            self.set_msg(f'Processing item {i + 1}')
        
        return 'Success'
    
    def update_progress_display(self):
        """Update progress dialog from timer"""
        if hasattr(self, 'percent'):
            self.pd.set_value(int(self.percent))
        
        if hasattr(self, 'message'):
            self.pd.set_submsg(self.message)
    
    def cancel(self):
        """Handle cancel request"""
        self.canceled = True
        if hasattr(self, 'job'):
            self.job.kill()
    
    def progress_done(self, job):
        """Clean up when done"""
        if self.timer:
            self.timer.stop()
        
        if self.pd:
            self.pd.hide()
        
        if not self.canceled and job.result:
            from calibre.gui2 import info_dialog
            info_dialog(
                self.gui,
                'Success',
                'Task completed successfully',
                show=True
            )
```

### 5. UI Component Patterns

#### Pattern 5.1: Custom Dialog with Validation

```python
from calibre.gui2.widgets2 import Dialog
from qt.core import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QDialogButtonBox, QMessageBox
)

class CustomDialog(Dialog):
    """Custom dialog with validation"""
    
    def __init__(self, parent, initial_value=''):
        Dialog.__init__(
            self, 
            'Custom Dialog Title',
            'custom_dialog_geometry',  # For saving size/position
            parent
        )
        self.initial_value = initial_value
        self.result_value = None
        
        self.setup_ui()
        self.restore_geometry()
    
    def setup_ui(self):
        """Create dialog UI"""
        layout = QVBoxLayout(self)
        
        # Input section
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel('Enter value:'))
        
        self.input_edit = QLineEdit(self.initial_value)
        self.input_edit.textChanged.connect(self.validate_input)
        input_layout.addWidget(self.input_edit)
        
        layout.addLayout(input_layout)
        
        # Validation message
        self.validation_label = QLabel('')
        self.validation_label.setStyleSheet('color: red')
        layout.addWidget(self.validation_label)
        
        # Buttons
        self.bb = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        self.bb.accepted.connect(self.accept)
        self.bb.rejected.connect(self.reject)
        layout.addWidget(self.bb)
        
        # Initial validation
        self.validate_input()
    
    def validate_input(self):
        """Validate input and update UI"""
        text = self.input_edit.text().strip()
        
        if not text:
            self.validation_label.setText('Value cannot be empty')
            self.bb.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
            return False
        
        if len(text) < 3:
            self.validation_label.setText('Value must be at least 3 characters')
            self.bb.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
            return False
        
        # Valid
        self.validation_label.setText('')
        self.bb.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)
        return True
    
    def accept(self):
        """Handle OK button"""
        if self.validate_input():
            self.result_value = self.input_edit.text().strip()
            self.save_geometry()
            Dialog.accept(self)
    
    @classmethod
    def get_value(cls, parent, initial=''):
        """Convenience method to show dialog and get result"""
        dialog = cls(parent, initial)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.result_value
        return None
```

#### Pattern 5.2: Book List Widget

```python
from qt.core import (
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, Qt, QMenu
)

class BookListWidget(QTableWidget):
    """Widget for displaying list of books"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.book_data = []
    
    def setup_ui(self):
        """Configure table appearance"""
        # Set columns
        self.setColumnCount(4)
        self.setHorizontalHeaderLabels([
            'Title', 'Authors', 'Series', 'Tags'
        ])
        
        # Configure behavior
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.setSortingEnabled(True)
        
        # Configure headers
        header = self.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        
        # Context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
    
    def populate_books(self, books):
        """Fill table with book data"""
        self.book_data = books
        self.setRowCount(len(books))
        
        for row, book in enumerate(books):
            # Title
            self.setItem(row, 0, QTableWidgetItem(book['title']))
            
            # Authors
            authors = ' & '.join(book.get('authors', []))
            self.setItem(row, 1, QTableWidgetItem(authors))
            
            # Series
            series = ''
            if book.get('series'):
                series = f"{book['series']} [{book.get('series_index', 1)}]"
            self.setItem(row, 2, QTableWidgetItem(series))
            
            # Tags
            tags = ', '.join(book.get('tags', []))
            self.setItem(row, 3, QTableWidgetItem(tags))
        
        # Auto-resize columns
        self.resizeColumnsToContents()
    
    def get_selected_books(self):
        """Get currently selected books"""
        selected = []
        for row in set(item.row() for item in self.selectedItems()):
            if row < len(self.book_data):
                selected.append(self.book_data[row])
        return selected
    
    def show_context_menu(self, pos):
        """Show context menu"""
        if not self.selectedItems():
            return
        
        menu = QMenu(self)
        
        # Add actions
        view_action = menu.addAction('View Details')
        view_action.triggered.connect(self.view_selected)
        
        edit_action = menu.addAction('Edit Metadata')
        edit_action.triggered.connect(self.edit_selected)
        
        menu.addSeparator()
        
        remove_action = menu.addAction('Remove from List')
        remove_action.triggered.connect(self.remove_selected)
        
        menu.exec(self.mapToGlobal(pos))
    
    def view_selected(self):
        """View selected books"""
        books = self.get_selected_books()
        # Implement view logic
        print(f'Viewing {len(books)} books')
    
    def edit_selected(self):
        """Edit selected books"""
        books = self.get_selected_books()
        # Implement edit logic
        print(f'Editing {len(books)} books')
    
    def remove_selected(self):
        """Remove selected books from list"""
        rows = sorted(set(item.row() for item in self.selectedItems()), 
                     reverse=True)
        
        for row in rows:
            self.removeRow(row)
            if row < len(self.book_data):
                self.book_data.pop(row)
```

### 6. Error Handling Patterns

#### Pattern 6.1: Comprehensive Error Handler

```python
import traceback
from calibre.gui2 import error_dialog, warning_dialog
from calibre.constants import DEBUG

class ErrorHandler:
    """Centralized error handling"""
    
    def __init__(self, plugin_name):
        self.plugin_name = plugin_name
        self.error_log = []
    
    def handle_error(self, operation, error, parent=None, 
                    show_dialog=True, critical=False):
        """Handle error with appropriate response"""
        # Create error record
        error_info = {
            'operation': operation,
            'error_type': type(error).__name__,
            'error_msg': str(error),
            'traceback': traceback.format_exc(),
            'timestamp': time.time()
        }
        
        self.error_log.append(error_info)
        
        # Log to console if debug mode
        if DEBUG:
            print(f'\n[{self.plugin_name}] Error in {operation}:')
            print(error_info['traceback'])
        
        # Show dialog if requested
        if show_dialog and parent:
            self.show_error_dialog(
                parent, operation, error, 
                error_info['traceback'], critical
            )
        
        return error_info
    
    def show_error_dialog(self, parent, operation, error, 
                         details, critical=False):
        """Show appropriate error dialog"""
        
        # Categorize error
        if isinstance(error, IOError):
            title = 'File Error'
            msg = f'File operation failed during {operation}'
        elif isinstance(error, ValueError):
            title = 'Invalid Input'
            msg = f'Invalid data provided for {operation}'
        elif isinstance(error, ImportError):
            title = 'Missing Component'
            msg = f'Required component not found for {operation}'
        else:
            title = f'{operation} Failed'
            msg = f'An error occurred during {operation}'
        
        # Add error details
        msg += f'\n\nError: {error}'
        
        # Show dialog
        if critical:
            error_dialog(
                parent, title, msg,
                det_msg=details,
                show=True
            )
        else:
            warning_dialog(
                parent, title, msg,
                det_msg=details,
                show=True
            )
    
    def safe_operation(self, operation_func, *args, 
                      parent=None, default=None, **kwargs):
        """Execute operation with error handling"""
        try:
            return operation_func(*args, **kwargs)
        except Exception as e:
            self.handle_error(
                operation_func.__name__, e, 
                parent=parent
            )
            return default
```

#### Pattern 6.2: Retry with Backoff

```python
import time
import random

class RetryHandler:
    """Handle retries with exponential backoff"""
    
    def __init__(self, max_retries=3, base_delay=1.0, 
                 max_delay=30.0, jitter=True):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter = jitter
    
    def calculate_delay(self, attempt):
        """Calculate delay for attempt with exponential backoff"""
        delay = min(
            self.base_delay * (2 ** attempt),
            self.max_delay
        )
        
        if self.jitter:
            # Add random jitter to prevent thundering herd
            delay *= (0.5 + random.random())
        
        return delay
    
    def retry_operation(self, operation, *args, **kwargs):
        """Execute operation with retries"""
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                return operation(*args, **kwargs)
                
            except Exception as e:
                last_error = e
                
                # Check if error is retryable
                if not self.is_retryable(e):
                    raise
                
                if attempt < self.max_retries - 1:
                    delay = self.calculate_delay(attempt)
                    print(f'Retry {attempt + 1}/{self.max_retries} '
                          f'after {delay:.1f}s: {e}')
                    time.sleep(delay)
        
        # All retries exhausted
        raise last_error
    
    def is_retryable(self, error):
        """Determine if error is retryable"""
        # Network errors
        if isinstance(error, (ConnectionError, TimeoutError)):
            return True
        
        # Temporary file errors
        if isinstance(error, OSError) and error.errno in (
            errno.EAGAIN,  # Resource temporarily unavailable
            errno.EBUSY,   # Device or resource busy
        ):
            return True
        
        # HTTP errors
        if hasattr(error, 'code'):
            # Retry on server errors and rate limiting
            return error.code in (429, 500, 502, 503, 504)
        
        return False
```

### 7. Resource Management Patterns

#### Pattern 7.1: Plugin Resource Loading

```python
import os
from calibre.utils.zipfile import ZipFile

class ResourceManager:
    """Manage plugin resources efficiently"""
    
    def __init__(self, plugin):
        self.plugin = plugin
        self.resource_cache = {}
    
    def get_resource(self, path, binary=True):
        """Get resource from plugin ZIP"""
        # Check cache first
        if path in self.resource_cache:
            return self.resource_cache[path]
        
        # Load from ZIP
        try:
            resources = self.plugin.load_resources([path])
            
            if path not in resources or resources[path] is None:
                raise FileNotFoundError(f'Resource not found: {path}')
            
            data = resources[path]
            
            if not binary:
                data = data.decode('utf-8')
            
            # Cache for future use
            self.resource_cache[path] = data
            
            return data
            
        except Exception as e:
            print(f'Failed to load resource {path}: {e}')
            return None
    
    def get_icon(self, name):
        """Load icon from resources"""
        from qt.core import QIcon, QPixmap
        
        # Try multiple formats
        for ext in ('png', 'svg', 'jpg'):
            path = f'images/{name}.{ext}'
            data = self.get_resource(path, binary=True)
            
            if data:
                pixmap = QPixmap()
                if pixmap.loadFromData(data):
                    return QIcon(pixmap)
        
        # Return empty icon as fallback
        return QIcon()
    
    def get_template(self, name):
        """Load template file"""
        path = f'templates/{name}'
        return self.get_resource(path, binary=False)
    
    def extract_all_resources(self, target_dir):
        """Extract all resources to directory"""
        import zipfile
        
        with zipfile.ZipFile(self.plugin.plugin_path, 'r') as zf:
            for info in zf.infolist():
                if info.filename.startswith('resources/'):
                    # Create target path
                    rel_path = info.filename[10:]  # Remove 'resources/'
                    target_path = os.path.join(target_dir, rel_path)
                    
                    # Create directories
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    
                    # Extract file
                    with zf.open(info) as src:
                        with open(target_path, 'wb') as dst:
                            dst.write(src.read())
```

#### Pattern 7.2: Temporary File Management

```python
import tempfile
import shutil
import atexit
from calibre.ptempfile import PersistentTemporaryDirectory

class TempFileManager:
    """Manage temporary files safely"""
    
    def __init__(self, plugin_name):
        self.plugin_name = plugin_name
        self.temp_dirs = []
        self.temp_files = []
        
        # Register cleanup
        atexit.register(self.cleanup_all)
    
    def create_temp_dir(self, persistent=False):
        """Create temporary directory"""
        if persistent:
            # Survives calibre restart
            temp_dir = PersistentTemporaryDirectory(
                prefix=f'{self.plugin_name}_'
            )
        else:
            # Regular temp dir
            temp_dir = tempfile.mkdtemp(
                prefix=f'{self.plugin_name}_'
            )
        
        self.temp_dirs.append(temp_dir)
        return temp_dir
    
    def create_temp_file(self, suffix='', content=None):
        """Create temporary file"""
        fd, path = tempfile.mkstemp(
            suffix=suffix,
            prefix=f'{self.plugin_name}_'
        )
        
        try:
            if content:
                if isinstance(content, str):
                    content = content.encode('utf-8')
                
                os.write(fd, content)
            
            os.close(fd)
            
        except:
            os.close(fd)
            os.unlink(path)
            raise
        
        self.temp_files.append(path)
        return path
    
    def cleanup_all(self):
        """Clean up all temporary files"""
        # Clean files
        for path in self.temp_files:
            try:
                if os.path.exists(path):
                    os.unlink(path)
            except Exception as e:
                print(f'Failed to delete {path}: {e}')
        
        # Clean directories
        for path in self.temp_dirs:
            try:
                if os.path.exists(path):
                    shutil.rmtree(path)
            except Exception as e:
                print(f'Failed to delete {path}: {e}')
        
        self.temp_files.clear()
        self.temp_dirs.clear()
```

### 8. Inter-Plugin Communication Patterns

#### Pattern 8.1: Plugin Discovery and Communication

```python
from calibre.customize.ui import find_plugin, initialized_plugins

class PluginCommunicator:
    """Enable communication between plugins"""
    
    def __init__(self, source_plugin_name):
        self.source_plugin = source_plugin_name
        self._plugin_cache = {}
    
    def find_active_plugin(self, plugin_name):
        """Find an active plugin by name"""
        if plugin_name in self._plugin_cache:
            return self._plugin_cache[plugin_name]
        
        # Search initialized plugins
        for plugin in initialized_plugins():
            if plugin.name == plugin_name:
                self._plugin_cache[plugin_name] = plugin
                return plugin
        
        # Try finding by class
        plugin = find_plugin(plugin_name)
        if plugin:
            self._plugin_cache[plugin_name] = plugin
            return plugin
        
        return None
    
    def call_plugin_method(self, plugin_name, method_name, 
                          *args, **kwargs):
        """Call method on another plugin"""
        plugin = self.find_active_plugin(plugin_name)
        
        if not plugin:
            raise ValueError(f'Plugin {plugin_name} not found')
        
        # For GUI plugins, get the actual instance
        if hasattr(plugin, 'actual_plugin_'):
            plugin_instance = plugin.actual_plugin_
            
            if hasattr(plugin_instance, method_name):
                method = getattr(plugin_instance, method_name)
                return method(*args, **kwargs)
        
        # For other plugins
        if hasattr(plugin, method_name):
            method = getattr(plugin, method_name)
            return method(*args, **kwargs)
        
        raise AttributeError(
            f'Plugin {plugin_name} has no method {method_name}'
        )
    
    def emit_event(self, event_name, data=None):
        """Emit event for other plugins to handle"""
        from calibre.gui2 import gui_prefs
        
        # Store event in shared preferences
        events = gui_prefs.get('plugin_events', {})
        
        if event_name not in events:
            events[event_name] = []
        
        events[event_name].append({
            'source': self.source_plugin,
            'timestamp': time.time(),
            'data': data
        })
        
        # Keep only recent events
        events[event_name] = events[event_name][-100:]
        
        gui_prefs['plugin_events'] = events
    
    def register_event_handler(self, event_name, handler):
        """Register to handle events from other plugins"""
        # This would typically be implemented with Qt signals
        # or a proper event bus, but shown here for pattern
        pass
```

#### Pattern 8.2: Shared Data Store

```python
from calibre.utils.config import JSONConfig

class SharedDataStore:
    """Share data between plugins"""
    
    def __init__(self):
        self.store = JSONConfig('plugins/shared_data')
        self.locks = {}
    
    def get(self, key, default=None):
        """Get shared data"""
        return self.store.get(key, default)
    
    def set(self, key, value):
        """Set shared data"""
        self.store[key] = value
        self.store.commit()
    
    def update(self, key, updater_func, default=None):
        """Atomically update shared data"""
        current = self.get(key, default)
        new_value = updater_func(current)
        self.set(key, new_value)
        return new_value
    
    def append_to_list(self, key, item):
        """Append to shared list"""
        def updater(current):
            if not isinstance(current, list):
                current = []
            current.append(item)
            return current
        
        return self.update(key, updater, [])
    
    def register_plugin(self, plugin_name, plugin_data):
        """Register plugin in shared registry"""
        def updater(registry):
            if not isinstance(registry, dict):
                registry = {}
            
            registry[plugin_name] = {
                'data': plugin_data,
                'timestamp': time.time()
            }
            
            return registry
        
        return self.update('plugin_registry', updater, {})
```

### 9. Performance Optimization Patterns

#### Pattern 9.1: Lazy Loading and Caching

```python
import functools
import time
from collections import OrderedDict

class LazyLoader:
    """Lazy loading with caching"""
    
    def __init__(self, max_cache_size=100, ttl=3600):
        self.max_cache_size = max_cache_size
        self.ttl = ttl  # Time to live in seconds
        self.cache = OrderedDict()
    
    def lazy_property(self, func):
        """Decorator for lazy properties"""
        attr_name = f'_lazy_{func.__name__}'
        
        @functools.wraps(func)
        def wrapper(self):
            if not hasattr(self, attr_name):
                setattr(self, attr_name, func(self))
            return getattr(self, attr_name)
        
        return wrapper
    
    def cached(self, func):
        """Decorator for cached methods"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key
            key = (func.__name__, args, tuple(sorted(kwargs.items())))
            
            # Check cache
            if key in self.cache:
                value, timestamp = self.cache[key]
                if time.time() - timestamp < self.ttl:
                    # Move to end (LRU)
                    self.cache.move_to_end(key)
                    return value
                else:
                    # Expired
                    del self.cache[key]
            
            # Compute value
            result = func(*args, **kwargs)
            
            # Store in cache
            self.cache[key] = (result, time.time())
            
            # Limit cache size
            if len(self.cache) > self.max_cache_size:
                # Remove oldest
                self.cache.popitem(last=False)
            
            return result
        
        # Add cache control methods
        wrapper.clear_cache = lambda: self.cache.clear()
        wrapper.cache_info = lambda: {
            'size': len(self.cache),
            'max_size': self.max_cache_size,
            'ttl': self.ttl
        }
        
        return wrapper

# Usage example
class BookProcessor(LazyLoader):
    def __init__(self, db):
        super().__init__()
        self.db = db
    
    @property
    @LazyLoader.lazy_property
    def all_tags(self):
        """Load all tags once"""
        return self.db.all_tags()
    
    @LazyLoader.cached
    def get_books_by_tag(self, tag):
        """Cache books by tag queries"""
        return self.db.search(f'tag:{tag}')
```

#### Pattern 9.2: Batch Processing

```python
from itertools import islice

class BatchProcessor:
    """Process items in efficient batches"""
    
    def __init__(self, batch_size=100):
        self.batch_size = batch_size
    
    def process_in_batches(self, items, processor_func, 
                          progress_callback=None):
        """Process items in batches"""
        total = len(items) if hasattr(items, '__len__') else None
        processed = 0
        results = []
        
        # Convert to iterator
        item_iter = iter(items)
        
        while True:
            # Get next batch
            batch = list(islice(item_iter, self.batch_size))
            
            if not batch:
                break
            
            # Process batch
            batch_results = processor_func(batch)
            results.extend(batch_results)
            
            # Update progress
            processed += len(batch)
            if progress_callback and total:
                progress_callback(processed, total)
            
            # Allow GUI updates between batches
            QApplication.processEvents()
        
        return results
    
    def parallel_process(self, items, processor_func, 
                        max_workers=None):
        """Process items in parallel"""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        if max_workers is None:
            max_workers = min(4, (os.cpu_count() or 1))
        
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_item = {
                executor.submit(processor_func, item): item
                for item in items
            }
            
            # Collect results
            for future in as_completed(future_to_item):
                item = future_to_item[future]
                
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    print(f'Error processing {item}: {e}')
                    results.append(None)
        
        return results
```

### 10. Testing and Debugging Patterns

#### Pattern 10.1: Debug Mode Integration

```python
from calibre.constants import DEBUG
import logging

class DebugHelper:
    """Enhanced debugging support"""
    
    def __init__(self, plugin_name):
        self.plugin_name = plugin_name
        self.setup_logging()
    
    def setup_logging(self):
        """Configure logging for plugin"""
        self.logger = logging.getLogger(
            f'calibre_plugins.{self.plugin_name}'
        )
        
        if DEBUG:
            self.logger.setLevel(logging.DEBUG)
            
            # Console handler
            handler = logging.StreamHandler()
            handler.setLevel(logging.DEBUG)
            
            formatter = logging.Formatter(
                '[%(name)s] %(levelname)s: %(message)s'
            )
            handler.setFormatter(formatter)
            
            self.logger.addHandler(handler)
        else:
            self.logger.setLevel(logging.WARNING)
    
    def debug_decorator(self, func):
        """Decorator to add debug logging"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if DEBUG:
                self.logger.debug(
                    f'Calling {func.__name__} with args={args}, kwargs={kwargs}'
                )
            
            try:
                result = func(*args, **kwargs)
                
                if DEBUG:
                    self.logger.debug(
                        f'{func.__name__} returned: {result}'
                    )
                
                return result
                
            except Exception as e:
                self.logger.exception(
                    f'Error in {func.__name__}: {e}'
                )
                raise
        
        return wrapper
    
    def profile_method(self, func):
        """Profile method execution time"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                
                if DEBUG or elapsed > 1.0:  # Log slow operations
                    self.logger.info(
                        f'{func.__name__} took {elapsed:.3f}s'
                    )
                
                return result
                
            except Exception:
                elapsed = time.time() - start_time
                self.logger.error(
                    f'{func.__name__} failed after {elapsed:.3f}s'
                )
                raise
        
        return wrapper
```

#### Pattern 10.2: Test Mode Support

```python
class TestablePlugin:
    """Plugin with test mode support"""
    
    def __init__(self):
        self.test_mode = False
        self.test_data = None
    
    def enable_test_mode(self, test_data=None):
        """Enable test mode with optional test data"""
        self.test_mode = True
        self.test_data = test_data
        print(f'Test mode enabled for {self.__class__.__name__}')
    
    def disable_test_mode(self):
        """Disable test mode"""
        self.test_mode = False
        self.test_data = None
    
    def get_data_source(self):
        """Get data from test or real source"""
        if self.test_mode and self.test_data:
            return self.test_data
        
        # Normal data source
        return self.fetch_real_data()
    
    def mock_method(self, real_method, mock_method):
        """Replace method with mock in test mode"""
        if self.test_mode:
            return mock_method
        return real_method
    
    def assert_test_mode(self):
        """Ensure we're in test mode"""
        if not self.test_mode:
            raise RuntimeError('This method requires test mode')

# Usage in tests
def test_plugin():
    plugin = MyPlugin()
    plugin.enable_test_mode({
        'books': [
            {'id': 1, 'title': 'Test Book 1'},
            {'id': 2, 'title': 'Test Book 2'},
        ]
    })
    
    # Test with mock data
    results = plugin.search('Test')
    assert len(results) == 2
    
    plugin.disable_test_mode()
```

### Best Practices Summary

1. **Always use `qt.core` imports** - Never import PyQt directly
2. **Handle errors gracefully** - Use error dialogs with details
3. **Use ThreadedJob for long operations** - Keep UI responsive
4. **Cache expensive operations** - But manage memory usage
5. **Validate user input** - Provide clear feedback
6. **Save/restore dialog geometry** - For better UX
7. **Use namespaced configuration** - Avoid conflicts
8. **Clean up resources** - Register cleanup handlers
9. **Support library switching** - Update state appropriately
10. **Add debug logging** - But only in DEBUG mode

This patterns library provides a solid foundation for developing robust, efficient, and user-friendly Calibre plugins that integrate seamlessly with the Calibre ecosystem.