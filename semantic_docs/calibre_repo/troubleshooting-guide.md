# Comprehensive Troubleshooting Guide for Calibre Plugin Development
## Solutions to Common Problems and Debugging Strategies

### Executive Summary

This guide provides systematic approaches to diagnosing and resolving common issues in Calibre plugin development. Each problem includes symptoms, root causes, diagnostic steps, and verified solutions based on real-world plugin development experiences and analysis of the Calibre codebase.

### Table of Contents

1. [Import and Module Loading Errors](#1-import-and-module-loading-errors)
2. [GUI and Qt-Related Issues](#2-gui-and-qt-related-issues)
3. [Database Access Problems](#3-database-access-problems)
4. [Threading and Concurrency Issues](#4-threading-and-concurrency-issues)
5. [Plugin Installation and Loading](#5-plugin-installation-and-loading)
6. [Resource and File Handling](#6-resource-and-file-handling)
7. [Performance and Memory Issues](#7-performance-and-memory-issues)
8. [Platform-Specific Problems](#8-platform-specific-problems)
9. [Development and Testing Issues](#9-development-and-testing-issues)
10. [Advanced Debugging Techniques](#10-advanced-debugging-techniques)

---

### 1. Import and Module Loading Errors

#### Problem 1.1: ImportError: No module named 'numpy'

**Symptoms:**
```python
ImportError: No module named 'numpy'
# or
ModuleNotFoundError: No module named 'scipy'
```

**Root Cause:**
Calibre's embedded Python environment only includes standard library modules and specific Calibre dependencies. NumPy, SciPy, and other scientific computing libraries are not available.

**Solution:**
```python
# Option 1: Implement pure Python alternatives
import math
import array

class VectorOps:
    @staticmethod
    def dot_product(v1, v2):
        """Pure Python dot product"""
        return sum(a * b for a, b in zip(v1, v2))
    
    @staticmethod
    def cosine_similarity(v1, v2):
        """Pure Python cosine similarity"""
        dot = VectorOps.dot_product(v1, v2)
        norm1 = math.sqrt(sum(x * x for x in v1))
        norm2 = math.sqrt(sum(x * x for x in v2))
        return dot / (norm1 * norm2) if norm1 and norm2 else 0.0

# Option 2: Use array module for efficiency
def efficient_vector_ops():
    # Create typed arrays for better performance
    v1 = array.array('d', [1.0, 2.0, 3.0])  # 'd' for double
    v2 = array.array('d', [4.0, 5.0, 6.0])
    
    # Operations are still pure Python but more efficient
    dot = sum(a * b for a, b in zip(v1, v2))
    return dot
```

**Prevention:**
- Check available modules before development
- Design with Calibre's constraints in mind
- Use `calibre-debug -c "import sys; print(sys.modules.keys())"` to list available modules

#### Problem 1.2: ImportError with Qt modules

**Symptoms:**
```python
ImportError: cannot import name 'QWidget' from 'PyQt5.QtWidgets'
# or
ImportError: No module named 'PyQt5'
```

**Root Cause:**
Direct PyQt5/PyQt6 imports don't work in Calibre plugins. Must use Calibre's qt.core abstraction layer.

**Solution:**
```python
# ❌ WRONG - Never do this
from PyQt5.QtWidgets import QWidget, QDialog
from PyQt6.QtCore import Qt

# ✅ CORRECT - Always use qt.core
from qt.core import (
    QWidget, QDialog, Qt, QVBoxLayout,
    QPushButton, QLabel, pyqtSignal
)

# Complete list of common imports
from qt.core import (
    # Widgets
    QApplication, QMainWindow, QDialog, QWidget,
    QLabel, QPushButton, QLineEdit, QTextEdit,
    QComboBox, QCheckBox, QRadioButton,
    QListWidget, QTableWidget, QTreeWidget,
    
    # Layouts
    QVBoxLayout, QHBoxLayout, QGridLayout,
    QFormLayout, QStackedLayout,
    
    # Core
    Qt, QObject, QThread, QTimer,
    pyqtSignal, pyqtSlot,
    
    # Graphics
    QPixmap, QIcon, QPainter, QColor,
    
    # Dialogs
    QMessageBox, QFileDialog, QInputDialog
)
```

**Diagnostic Test:**
```python
# Test if imports are correct
def test_qt_imports():
    try:
        from qt.core import QWidget
        print("✓ Qt imports working correctly")
        return True
    except ImportError as e:
        print(f"✗ Qt import error: {e}")
        return False
```

#### Problem 1.3: Multi-file plugin import errors

**Symptoms:**
```python
ImportError: No module named 'calibre_plugins.my_plugin.utils'
# When trying to import from another file in your plugin
```

**Root Cause:**
Multi-file plugins require a special marker file for Calibre to set up imports correctly.

**Solution:**
```
# Plugin structure:
my_plugin.zip
├── __init__.py
├── plugin-import-name-my_plugin.txt  # ← REQUIRED (empty file)
├── ui.py
├── utils.py
└── config.py

# The marker file must be named exactly:
# plugin-import-name-[your_plugin_name].txt
```

**Verification:**
```python
# In __init__.py
print(f"Plugin loading from: {__file__}")

# In other files (e.g., ui.py)
from calibre_plugins.my_plugin.utils import helper_function
```

---

### 2. GUI and Qt-Related Issues

#### Problem 2.1: GUI freezes during operation

**Symptoms:**
- Calibre becomes unresponsive
- "Not Responding" in title bar
- Progress dialogs don't update

**Root Cause:**
Long-running operations blocking the main GUI thread.

**Solution:**
```python
from calibre.gui2.threaded_jobs import ThreadedJob

class NonBlockingOperation:
    def __init__(self, gui):
        self.gui = gui
    
    def start_long_operation(self):
        """Start operation in background"""
        job = ThreadedJob(
            'my_operation',
            'Processing books...',
            self.do_work,  # Runs in background thread
            self.work_done,  # Called in GUI thread when done
            max_concurrent_count=1
        )
        
        self.gui.job_manager.run_threaded_job(job)
        self.gui.status_bar.show_message('Processing...', 0)
    
    def do_work(self):
        """This runs in background thread - no GUI access!"""
        results = []
        
        for i in range(100):
            # Simulate work
            time.sleep(0.1)
            
            # Report progress
            self.set_progress(i + 1, 100)
            
            # Check if canceled
            if self.is_aborted():
                return None
            
            results.append(f"Item {i}")
        
        return results
    
    def work_done(self, job):
        """This runs in GUI thread - safe to update GUI"""
        self.gui.status_bar.show_message('', 0)  # Clear message
        
        if job.failed:
            error_dialog(self.gui, 'Error', str(job.exception), show=True)
        elif job.result is None:
            info_dialog(self.gui, 'Canceled', 'Operation was canceled', show=True)
        else:
            info_dialog(self.gui, 'Success', f'Processed {len(job.result)} items', show=True)
```

**Quick Fix for Existing Code:**
```python
# Add periodic GUI updates in loops
for i, item in enumerate(large_list):
    # Process item
    process(item)
    
    # Update GUI every 10 items
    if i % 10 == 0:
        QApplication.processEvents()
        # Optional: Update progress
        self.progress_label.setText(f'Processing {i}/{len(large_list)}')
```

#### Problem 2.2: Dialog doesn't appear or appears blank

**Symptoms:**
- Dialog window is empty
- Dialog appears but with no content
- Dialog flashes and disappears

**Root Cause:**
- Parent widget not set correctly
- Dialog going out of scope
- Modal/modeless confusion

**Solution:**
```python
from calibre.gui2.widgets2 import Dialog

class WorkingDialog(Dialog):
    """Properly implemented dialog"""
    
    def __init__(self, parent):
        # Must call parent __init__ with proper arguments
        Dialog.__init__(
            self, 
            'My Dialog Title',  # Window title
            'my_dialog_geometry',  # Name for saving geometry
            parent  # Parent widget (usually gui)
        )
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel('Dialog content here'))
        
        # Add buttons
        self.bb = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        self.bb.accepted.connect(self.accept)
        self.bb.rejected.connect(self.reject)
        layout.addWidget(self.bb)

# Correct usage:
def show_dialog(self):
    # Keep reference to prevent garbage collection
    self.dialog = WorkingDialog(self.gui)
    
    # Show modal dialog
    if self.dialog.exec() == QDialog.DialogCode.Accepted:
        print("User clicked OK")
    
    # For modeless dialog:
    # self.dialog.show()  # Returns immediately
```

#### Problem 2.3: Keyboard shortcuts not working

**Symptoms:**
- Defined shortcuts don't trigger actions
- Shortcuts conflict with Calibre's built-in ones
- Shortcuts work in menu but not globally

**Root Cause:**
- Shortcuts not registered with Calibre
- Conflicting shortcut definitions
- Wrong shortcut scope

**Solution:**
```python
class PluginWithShortcuts(InterfaceAction):
    def genesis(self):
        # Register shortcuts properly
        
        # Method 1: For toolbar action
        self.register_shortcut(
            self.qaction,  # The QAction
            'unique_shortcut_name',  # Unique identifier
            default_keys=('Ctrl+Shift+K',),  # Default keys
            description='Description for preferences'
        )
        
        # Method 2: For menu items
        menu_action = self.create_menu_action(
            self.menu,
            'another_unique_name',
            'Menu Item',
            triggered=self.menu_handler
        )
        
        self.register_shortcut(
            menu_action,
            'menu_shortcut_name',
            default_keys=('Ctrl+Alt+M', 'F9'),  # Multiple shortcuts
            description='Menu item shortcut'
        )

# Check for conflicts:
def check_shortcut_conflicts(self):
    """List all registered shortcuts"""
    from calibre.gui2 import shortcuts
    
    all_shortcuts = shortcuts.shortcuts
    for name, shortcut in all_shortcuts.items():
        print(f"{name}: {shortcut.keys()}")
```

---

### 3. Database Access Problems

#### Problem 3.1: Database locked errors

**Symptoms:**
```
apsw.BusyError: BusyError: database is locked
# or
DatabaseException: Database is locked, cannot write
```

**Root Cause:**
- Multiple simultaneous write attempts
- Long-running transactions
- Database accessed from background thread incorrectly

**Solution:**
```python
class SafeDatabaseAccess:
    def __init__(self, gui):
        self.gui = gui
    
    def read_with_retry(self, operation, max_retries=3):
        """Read from database with retry logic"""
        import time
        
        for attempt in range(max_retries):
            try:
                db = self.gui.current_db.new_api
                return operation(db)
                
            except apsw.BusyError:
                if attempt < max_retries - 1:
                    time.sleep(0.1 * (attempt + 1))  # Exponential backoff
                else:
                    raise
    
    def batch_write(self, updates, batch_size=50):
        """Write in batches to minimize lock time"""
        db = self.gui.current_db.new_api
        
        for i in range(0, len(updates), batch_size):
            batch = updates[i:i + batch_size]
            
            # Single transaction per batch
            with db.write_lock:
                for update in batch:
                    self._apply_update(db, update)
            
            # Allow other operations between batches
            QApplication.processEvents()
    
    def safe_update_metadata(self, book_id, metadata):
        """Update with proper error handling"""
        try:
            db = self.gui.current_db.new_api
            db.set_metadata(book_id, metadata)
            return True
        except apsw.BusyError:
            error_dialog(
                self.gui,
                'Database Busy',
                'The database is locked. Please try again.',
                show=True
            )
            return False
        except Exception as e:
            error_dialog(
                self.gui,
                'Update Failed',
                f'Failed to update metadata: {e}',
                show=True
            )
            return False
```

#### Problem 3.2: Book not found errors

**Symptoms:**
```python
ValueError: Book with id 123 not found
# or
NoSuchBook: Book does not exist
```

**Root Cause:**
- Book was deleted after plugin cached the ID
- Using IDs from different library
- Race condition with library refresh

**Solution:**
```python
class RobustBookAccess:
    def __init__(self, db):
        self.db = db
    
    def safe_get_metadata(self, book_id, default=None):
        """Get metadata with existence check"""
        try:
            if book_id in self.db.all_book_ids():
                return self.db.get_metadata(book_id)
        except:
            pass
        return default
    
    def verify_book_ids(self, book_ids):
        """Filter out non-existent books"""
        valid_ids = set(self.db.all_book_ids())
        return [bid for bid in book_ids if bid in valid_ids]
    
    def with_book_refresh(self, operation):
        """Execute operation with fresh book list"""
        # Force refresh
        self.db.refresh()
        
        # Get fresh IDs
        current_ids = self.db.all_book_ids()
        
        # Execute operation
        return operation(current_ids)
```

#### Problem 3.3: Custom column errors

**Symptoms:**
```python
KeyError: '#mycolumn'
# or
ValueError: Unknown field #mycolumn
```

**Root Cause:**
- Custom column doesn't exist
- Wrong column name format
- Column deleted after plugin loaded

**Solution:**
```python
class CustomColumnSafeAccess:
    def __init__(self, db):
        self.db = db
        self._column_cache = None
    
    def get_available_columns(self, refresh=False):
        """Get all custom columns with caching"""
        if self._column_cache is None or refresh:
            self._column_cache = self.db.field_metadata.custom_field_metadata()
        return self._column_cache
    
    def safe_get_custom(self, book_id, column_name, default=None):
        """Safely get custom column value"""
        # Ensure column name format
        if not column_name.startswith('#'):
            column_name = '#' + column_name
        
        # Check if column exists
        columns = self.get_available_columns()
        if column_name not in columns:
            print(f"Warning: Custom column {column_name} not found")
            return default
        
        try:
            # Get value
            value = self.db.get_field(book_id, column_name)
            
            # Handle empty values based on column type
            col_meta = columns[column_name]
            if value is None:
                if col_meta['datatype'] == 'bool':
                    return False
                elif col_meta['datatype'] in ('int', 'float'):
                    return 0
                elif col_meta['is_multiple']:
                    return []
            
            return value
            
        except Exception as e:
            print(f"Error accessing {column_name}: {e}")
            return default
    
    def create_custom_column_if_needed(self, spec):
        """Create custom column if it doesn't exist"""
        name = spec['label']
        if not name.startswith('#'):
            name = '#' + name
        
        columns = self.get_available_columns()
        if name not in columns:
            # Create column
            self.db.create_custom_column(
                label=name[1:],  # Remove #
                name=spec.get('name', name[1:]),
                datatype=spec.get('datatype', 'text'),
                is_multiple=spec.get('is_multiple', False),
                display=spec.get('display', {})
            )
            # Refresh cache
            self.get_available_columns(refresh=True)
```

---

### 4. Threading and Concurrency Issues

#### Problem 4.1: GUI updates from background thread

**Symptoms:**
- Random crashes with no error message
- "Cannot create children for a parent in a different thread"
- GUI elements not updating despite code running

**Root Cause:**
Qt GUI elements can only be accessed from the main thread.

**Solution:**
```python
from qt.core import pyqtSignal, QObject

class ThreadSafeWorker(QObject):
    """Worker with signals for thread-safe GUI updates"""
    
    # Define signals for GUI communication
    progress_update = pyqtSignal(int, int)  # current, total
    status_update = pyqtSignal(str)
    error_occurred = pyqtSignal(str, str)  # title, message
    result_ready = pyqtSignal(object)
    
    def __init__(self, gui):
        super().__init__()
        self.gui = gui
        
        # Connect signals to GUI updates (in main thread)
        self.progress_update.connect(self._update_progress)
        self.status_update.connect(self._update_status)
        self.error_occurred.connect(self._show_error)
    
    def _update_progress(self, current, total):
        """GUI update - runs in main thread"""
        self.gui.status_bar.show_message(
            f'Processing {current}/{total}...', 0
        )
    
    def _update_status(self, message):
        """GUI update - runs in main thread"""
        self.gui.status_bar.show_message(message, 5000)
    
    def _show_error(self, title, message):
        """GUI update - runs in main thread"""
        error_dialog(self.gui, title, message, show=True)
    
    def run_in_thread(self):
        """This runs in background thread"""
        try:
            # Emit signals instead of direct GUI access
            self.status_update.emit('Starting processing...')
            
            for i in range(100):
                # Do work
                time.sleep(0.1)
                
                # Update progress via signal
                self.progress_update.emit(i + 1, 100)
            
            # Send results via signal
            self.result_ready.emit({'success': True})
            
        except Exception as e:
            # Error handling via signal
            self.error_occurred.emit(
                'Processing Error',
                str(e)
            )
```

#### Problem 4.2: Race conditions with shared data

**Symptoms:**
- Inconsistent results
- Missing data intermittently
- Dictionary changed size during iteration

**Root Cause:**
Multiple threads accessing shared data without synchronization.

**Solution:**
```python
from qt.core import QMutex, QMutexLocker
import threading

class ThreadSafeData:
    """Thread-safe data container"""
    
    def __init__(self):
        # Qt approach
        self._data = {}
        self._mutex = QMutex()
        
        # Python approach
        self._lock = threading.RLock()
    
    def set(self, key, value):
        """Thread-safe write"""
        # Using Qt mutex
        with QMutexLocker(self._mutex):
            self._data[key] = value
        
        # Or using Python lock
        # with self._lock:
        #     self._data[key] = value
    
    def get(self, key, default=None):
        """Thread-safe read"""
        with QMutexLocker(self._mutex):
            return self._data.get(key, default)
    
    def update_atomic(self, key, updater_func):
        """Atomic read-modify-write"""
        with QMutexLocker(self._mutex):
            current = self._data.get(key)
            new_value = updater_func(current)
            self._data[key] = new_value
            return new_value
    
    def get_snapshot(self):
        """Get consistent snapshot of all data"""
        with QMutexLocker(self._mutex):
            return self._data.copy()
```

#### Problem 4.3: Deadlocks

**Symptoms:**
- Application hangs completely
- Operations never complete
- Must force-quit Calibre

**Root Cause:**
- Circular lock dependencies
- Waiting for GUI thread from background thread
- Database locks held too long

**Solution:**
```python
class DeadlockPrevention:
    """Patterns to prevent deadlocks"""
    
    def __init__(self):
        self.lock1 = threading.Lock()
        self.lock2 = threading.Lock()
    
    def correct_lock_ordering(self):
        """Always acquire locks in same order"""
        # ✓ CORRECT - consistent ordering
        with self.lock1:
            with self.lock2:
                # Do work
                pass
        
        # In another method - same order
        with self.lock1:
            with self.lock2:
                # Do other work
                pass
    
    def use_timeout(self):
        """Use timeouts to detect deadlocks"""
        acquired = self.lock1.acquire(timeout=5.0)
        if not acquired:
            raise TimeoutError("Could not acquire lock - possible deadlock")
        
        try:
            # Do work
            pass
        finally:
            self.lock1.release()
    
    def avoid_nested_locks(self):
        """Minimize lock scope"""
        # ✓ BETTER - prepare data outside lock
        data_to_write = prepare_data()
        
        with self.lock1:
            # Only hold lock for actual write
            write_data(data_to_write)
        
        # ✗ WORSE - doing preparation inside lock
        # with self.lock1:
        #     data = prepare_data()  # This could take time
        #     write_data(data)
```

---

### 5. Plugin Installation and Loading

#### Problem 5.1: InvalidPlugin: No __init__.py file

**Symptoms:**
```
InvalidPlugin: The plugin in '/path/to/plugin.zip' is invalid.
It does not contain a top-level __init__.py file
```

**Root Cause:**
- Plugin ZIP has wrong structure
- __init__.py in subdirectory instead of root
- File permissions issues

**Solution:**
```bash
# Correct ZIP structure:
plugin.zip
├── __init__.py          # ← Must be at root level
├── plugin-import-name-myplugin.txt
├── ui.py
└── resources/
    └── icon.png

# Create ZIP correctly:
cd /path/to/plugin/source
zip -r ../plugin.zip . -x "*.pyc" -x "__pycache__/*" -x ".git/*"

# Verify ZIP structure:
unzip -l plugin.zip | head
```

**Python script to create valid plugin ZIP:**
```python
import zipfile
import os
from pathlib import Path

def create_plugin_zip(source_dir, output_file):
    """Create properly structured plugin ZIP"""
    source_path = Path(source_dir)
    
    # Validate structure
    init_file = source_path / '__init__.py'
    if not init_file.exists():
        raise ValueError("No __init__.py found in source directory")
    
    # Create ZIP
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_path in source_path.rglob('*'):
            if file_path.is_file():
                # Skip unwanted files
                if '__pycache__' in str(file_path):
                    continue
                if file_path.suffix == '.pyc':
                    continue
                if '.git' in str(file_path):
                    continue
                
                # Add file with relative path
                arcname = file_path.relative_to(source_path)
                zf.write(file_path, arcname)
    
    print(f"Created plugin ZIP: {output_file}")
    
    # Verify
    with zipfile.ZipFile(output_file, 'r') as zf:
        if '__init__.py' not in zf.namelist():
            raise ValueError("Verification failed: no __init__.py at root")
```

#### Problem 5.2: Python 2 vs Python 3 syntax errors

**Symptoms:**
```
SyntaxError: Missing parentheses in call to 'print'
# or
SyntaxError: invalid syntax (Python 2 style)
```

**Root Cause:**
Plugin written for Python 2, but Calibre 5+ uses Python 3.

**Solution:**
```python
# Common Python 2 → 3 conversions:

# Print statements
# Python 2:
print "Hello"
print >> sys.stderr, "Error"

# Python 3:
print("Hello")
print("Error", file=sys.stderr)

# String types
# Python 2:
if isinstance(s, unicode):
    s = s.encode('utf-8')

# Python 3:
if isinstance(s, str):
    s = s.encode('utf-8')

# Division
# Python 2:
result = 5 / 2  # = 2

# Python 3:
result = 5 // 2  # = 2 (integer division)
result = 5 / 2   # = 2.5 (float division)

# Iterators
# Python 2:
for key in dict.iterkeys():
    pass

# Python 3:
for key in dict.keys():  # or just: for key in dict:
    pass

# Relative imports
# Python 2:
import utils

# Python 3 (in a package):
from . import utils
```

**2to3 compatibility helper:**
```python
# For code that must work in both Python 2 and 3:
import sys

if sys.version_info[0] >= 3:
    unicode = str
    basestring = str
else:
    bytes = str

# Use throughout code:
if isinstance(text, basestring):
    # Works in both Python 2 and 3
    pass
```

#### Problem 5.3: Plugin conflicts

**Symptoms:**
- Calibre crashes after installing plugin
- Other plugins stop working
- Menu items duplicated or missing

**Root Cause:**
- Name collisions between plugins
- Modifying global state
- Overriding built-in functionality

**Solution:**
```python
class ConflictFreePlugin:
    """Patterns to avoid conflicts"""
    
    # 1. Use unique names everywhere
    name = 'My Unique Plugin Name v1.0'  # Add version to ensure uniqueness
    
    # 2. Namespace all IDs
    def genesis(self):
        # Prefix all action names
        self.create_menu_action(
            self.menu,
            'my_unique_plugin_action_search',  # Namespaced ID
            'Search',
            triggered=self.search
        )
    
    # 3. Don't modify global state
    def safe_modification(self):
        # ✗ BAD - Modifies global
        # sys.path.insert(0, my_path)
        
        # ✓ GOOD - Local modification
        import sys
        old_path = sys.path[:]
        try:
            sys.path.insert(0, my_path)
            # Do work
        finally:
            sys.path[:] = old_path
    
    # 4. Check for conflicts
    def check_conflicts(self):
        from calibre.customize.ui import initialized_plugins
        
        for plugin in initialized_plugins():
            if plugin.name == self.name and plugin != self:
                raise Exception(f"Conflict: {self.name} already loaded")
```

---

### 6. Resource and File Handling

#### Problem 6.1: Resources not found in plugin ZIP

**Symptoms:**
```python
KeyError: 'images/icon.png'
# or
Resource 'template.html' not found in plugin
```

**Root Cause:**
- Resource path incorrect
- File not included in ZIP
- Case sensitivity issues

**Solution:**
```python
class ResourceHandler:
    """Robust resource handling"""
    
    def __init__(self, plugin):
        self.plugin = plugin
    
    def load_resource_safely(self, path, binary=True):
        """Load resource with fallback"""
        try:
            # Try primary path
            resources = self.plugin.load_resources([path])
            
            if path in resources and resources[path] is not None:
                data = resources[path]
                return data if binary else data.decode('utf-8')
            
        except Exception as e:
            print(f"Failed to load {path}: {e}")
        
        # Try alternative paths
        alternatives = [
            path.replace('/', '\\'),  # Windows path
            path.replace('\\', '/'),  # Unix path
            path.lower(),  # Lowercase
            path.upper(),  # Uppercase
        ]
        
        for alt_path in alternatives:
            try:
                resources = self.plugin.load_resources([alt_path])
                if alt_path in resources and resources[alt_path] is not None:
                    print(f"Found resource at alternative path: {alt_path}")
                    data = resources[alt_path]
                    return data if binary else data.decode('utf-8')
            except:
                continue
        
        # Final fallback
        return self.get_fallback_resource(path)
    
    def list_available_resources(self):
        """Debug helper to list all resources"""
        import zipfile
        
        try:
            with zipfile.ZipFile(self.plugin.plugin_path, 'r') as zf:
                print("Available resources in plugin:")
                for name in sorted(zf.namelist()):
                    print(f"  {name}")
        except Exception as e:
            print(f"Could not list resources: {e}")
```

#### Problem 6.2: Permission errors

**Symptoms:**
```
PermissionError: [Errno 13] Permission denied: '/path/to/file'
# or
OSError: [Errno 1] Operation not permitted
```

**Root Cause:**
- File locked by another process
- Insufficient permissions
- Antivirus interference

**Solution:**
```python
import os
import stat
import time

class FilePermissionHandler:
    """Handle file permission issues"""
    
    def make_writable(self, path):
        """Ensure file is writable"""
        try:
            # Get current permissions
            current = os.stat(path).st_mode
            
            # Add write permission
            os.chmod(path, current | stat.S_IWUSR)
            
        except Exception as e:
            print(f"Could not modify permissions: {e}")
    
    def safe_write_with_retry(self, path, content, max_retries=3):
        """Write with retry and permission handling"""
        
        for attempt in range(max_retries):
            try:
                # Ensure directory exists
                os.makedirs(os.path.dirname(path), exist_ok=True)
                
                # Try to write
                with open(path, 'wb' if isinstance(content, bytes) else 'w') as f:
                    f.write(content)
                
                return True
                
            except PermissionError as e:
                if attempt < max_retries - 1:
                    # Wait and retry (antivirus might be scanning)
                    time.sleep(1)
                    
                    # Try to fix permissions
                    self.make_writable(path)
                else:
                    # Final attempt failed
                    raise
            
            except OSError as e:
                if e.errno == 28:  # No space left
                    raise Exception("Disk full")
                raise
        
        return False
    
    def safe_temp_file(self, content, suffix=''):
        """Create temp file with proper cleanup"""
        import tempfile
        
        fd, path = tempfile.mkstemp(suffix=suffix)
        
        try:
            # Write content
            if isinstance(content, str):
                content = content.encode('utf-8')
            
            os.write(fd, content)
            os.close(fd)
            
            # Make readable
            os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
            
            return path
            
        except:
            # Clean up on error
            try:
                os.close(fd)
            except:
                pass
            try:
                os.unlink(path)
            except:
                pass
            raise
```

#### Problem 6.3: Path encoding issues

**Symptoms:**
- UnicodeDecodeError with file paths
- Files not found despite existing
- Different behavior on different platforms

**Root Cause:**
- Non-ASCII characters in paths
- Platform encoding differences
- Bytes vs string path confusion

**Solution:**
```python
import os
from calibre.constants import filesystem_encoding

class PathEncodingHandler:
    """Handle path encoding issues across platforms"""
    
    @staticmethod
    def safe_path(path):
        """Ensure path is properly encoded"""
        if isinstance(path, bytes):
            # Decode bytes path
            try:
                path = path.decode(filesystem_encoding)
            except UnicodeDecodeError:
                # Fallback decoding
                path = path.decode('utf-8', errors='replace')
        
        # Normalize path
        path = os.path.normpath(path)
        
        # Handle Windows UNC paths
        if os.name == 'nt' and path.startswith('\\\\'):
            # Preserve UNC prefix
            path = '\\\\' + path[2:].replace('/', '\\')
        
        return path
    
    @staticmethod
    def exists_with_encoding(base_path):
        """Check if path exists with encoding variations"""
        paths_to_try = [
            base_path,
            base_path.encode('utf-8').decode('latin-1', errors='ignore'),
            base_path.encode('latin-1', errors='ignore').decode('utf-8', errors='ignore'),
        ]
        
        for path in paths_to_try:
            try:
                if os.path.exists(path):
                    return True, path
            except:
                continue
        
        return False, None
    
    @staticmethod
    def list_dir_safe(directory):
        """List directory contents handling encoding"""
        items = []
        
        try:
            for item in os.listdir(directory):
                try:
                    # Ensure item is properly decoded
                    if isinstance(item, bytes):
                        item = item.decode(filesystem_encoding)
                    items.append(item)
                except UnicodeDecodeError:
                    # Skip items that can't be decoded
                    print(f"Skipping file with invalid encoding")
                    continue
        except Exception as e:
            print(f"Error listing directory: {e}")
        
        return items
```

---

### 7. Performance and Memory Issues

#### Problem 7.1: Plugin uses too much memory

**Symptoms:**
- Calibre becomes slow
- "Out of memory" errors
- System becomes unresponsive

**Root Cause:**
- Loading too much data at once
- Memory leaks from circular references
- Caching without limits

**Solution:**
```python
import gc
import sys
from collections import OrderedDict

class MemoryEfficientPlugin:
    """Memory-conscious plugin patterns"""
    
    def __init__(self):
        # Use bounded cache
        self.cache = BoundedCache(max_size=1000)
        
        # Track large objects
        self.large_objects = []
    
    def process_large_dataset(self, items):
        """Process data in chunks"""
        chunk_size = 100
        
        for i in range(0, len(items), chunk_size):
            chunk = items[i:i + chunk_size]
            
            # Process chunk
            results = self.process_chunk(chunk)
            
            # Yield results to avoid accumulation
            yield from results
            
            # Explicit garbage collection for large datasets
            if i % 1000 == 0:
                gc.collect()
    
    def load_embeddings_efficiently(self, count, dimension=768):
        """Load embeddings without memory explosion"""
        import mmap
        
        # Use memory-mapped file for large data
        bytes_per_embedding = dimension * 4  # float32
        total_size = count * bytes_per_embedding
        
        # Create memory-mapped file
        with open('embeddings.dat', 'r+b') as f:
            mm = mmap.mmap(f.fileno(), total_size)
            
            # Access embeddings on demand
            def get_embedding(index):
                offset = index * bytes_per_embedding
                data = mm[offset:offset + bytes_per_embedding]
                return struct.unpack(f'{dimension}f', data)
            
            return get_embedding
    
    def cleanup_memory(self):
        """Explicit memory cleanup"""
        # Clear caches
        self.cache.clear()
        
        # Delete large objects
        for obj in self.large_objects:
            del obj
        self.large_objects.clear()
        
        # Force garbage collection
        gc.collect()
    
    def get_memory_usage(self):
        """Monitor memory usage"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        return {
            'rss_mb': process.memory_info().rss / 1024 / 1024,
            'vms_mb': process.memory_info().vms / 1024 / 1024,
            'available_mb': psutil.virtual_memory().available / 1024 / 1024,
        }

class BoundedCache(OrderedDict):
    """LRU cache with size limit"""
    
    def __init__(self, max_size=1000):
        super().__init__()
        self.max_size = max_size
    
    def __setitem__(self, key, value):
        if key in self:
            # Move to end
            self.move_to_end(key)
        
        super().__setitem__(key, value)
        
        # Evict oldest if over limit
        if len(self) > self.max_size:
            self.popitem(last=False)
```

#### Problem 7.2: Slow plugin operations

**Symptoms:**
- Operations take minutes instead of seconds
- Progress bars move very slowly
- Users think plugin has frozen

**Root Cause:**
- Inefficient algorithms (O(n²) instead of O(n))
- Repeated database queries
- No caching of expensive operations

**Solution:**
```python
import time
import functools

class PerformanceOptimizedPlugin:
    """Performance optimization patterns"""
    
    def __init__(self):
        self.db_cache = {}
        self.timing_stats = {}
    
    def timed_operation(self, name):
        """Decorator to time operations"""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start = time.time()
                try:
                    result = func(*args, **kwargs)
                    elapsed = time.time() - start
                    
                    # Track timing
                    if name not in self.timing_stats:
                        self.timing_stats[name] = []
                    self.timing_stats[name].append(elapsed)
                    
                    if elapsed > 1.0:  # Log slow operations
                        print(f"{name} took {elapsed:.2f}s")
                    
                    return result
                except Exception:
                    elapsed = time.time() - start
                    print(f"{name} failed after {elapsed:.2f}s")
                    raise
            
            return wrapper
        return decorator
    
    @timed_operation("search_books")
    def efficient_search(self, db, criteria):
        """Optimized search with caching"""
        # Create cache key
        cache_key = ('search', tuple(sorted(criteria.items())))
        
        # Check cache
        if cache_key in self.db_cache:
            return self.db_cache[cache_key]
        
        # Optimize query
        results = []
        
        # Get all IDs once
        all_ids = set(db.all_book_ids())
        
        # Filter efficiently
        for criterion, value in criteria.items():
            if criterion == 'tag':
                # Use built-in tag search
                matching = set(db.search(f'tag:{value}'))
            elif criterion == 'author':
                # Use author index
                matching = set(db.search(f'author:{value}'))
            else:
                # Manual filter
                matching = set()
                for book_id in all_ids:
                    if self.matches_criterion(db, book_id, criterion, value):
                        matching.add(book_id)
            
            # Intersection for AND logic
            all_ids &= matching
        
        # Cache results
        self.db_cache[cache_key] = list(all_ids)
        
        return list(all_ids)
    
    def batch_database_reads(self, db, book_ids, fields):
        """Read multiple fields efficiently"""
        results = {}
        
        # Group by field to minimize DB calls
        for field in fields:
            if field == 'title':
                # Get all titles at once
                values = db.all_field_for('title', book_ids)
            elif field == 'authors':
                values = db.all_field_for('authors', book_ids)
            else:
                # Generic field
                values = {}
                for book_id in book_ids:
                    values[book_id] = db.get_field(book_id, field)
            
            # Store results
            for book_id, value in values.items():
                if book_id not in results:
                    results[book_id] = {}
                results[book_id][field] = value
        
        return results
    
    def optimize_similar_books(self, embeddings, query_embedding, top_k=10):
        """Optimized similarity search"""
        import heapq
        
        # Use heap for top-k instead of sorting all
        heap = []
        
        for book_id, embedding in embeddings.items():
            # Calculate similarity
            similarity = self.fast_cosine_similarity(query_embedding, embedding)
            
            # Maintain top-k heap
            if len(heap) < top_k:
                heapq.heappush(heap, (similarity, book_id))
            elif similarity > heap[0][0]:
                heapq.heapreplace(heap, (similarity, book_id))
        
        # Extract results
        results = []
        while heap:
            similarity, book_id = heapq.heappop(heap)
            results.append((book_id, similarity))
        
        return list(reversed(results))  # Highest similarity first
    
    def fast_cosine_similarity(self, v1, v2):
        """Optimized cosine similarity"""
        # Use generator expressions to avoid intermediate lists
        dot = sum(a * b for a, b in zip(v1, v2))
        
        # Calculate norms together
        sum_sq_1 = sum_sq_2 = 0.0
        for a, b in zip(v1, v2):
            sum_sq_1 += a * a
            sum_sq_2 += b * b
        
        # Final calculation
        denom = (sum_sq_1 * sum_sq_2) ** 0.5
        return dot / denom if denom else 0.0
```

---

### 8. Platform-Specific Problems

#### Problem 8.1: Plugin works on Windows but not Mac/Linux

**Symptoms:**
- File not found errors on certain platforms
- Case sensitivity issues
- Path separator problems

**Root Cause:**
- Windows is case-insensitive, Unix systems are case-sensitive
- Different path separators (\ vs /)
- Different file permissions models

**Solution:**
```python
import os
import sys
from calibre.constants import iswindows, ismacos, islinux

class CrossPlatformPlugin:
    """Handle platform differences correctly"""
    
    @staticmethod
    def get_platform_paths():
        """Get platform-specific paths"""
        if iswindows:
            return {
                'config': os.path.join(os.environ['APPDATA'], 'calibre'),
                'separator': '\\',
                'null_device': 'NUL',
            }
        elif ismacos:
            return {
                'config': os.path.expanduser('~/Library/Preferences/calibre'),
                'separator': '/',
                'null_device': '/dev/null',
            }
        else:  # Linux and others
            return {
                'config': os.path.expanduser('~/.config/calibre'),
                'separator': '/',
                'null_device': '/dev/null',
            }
    
    @staticmethod
    def safe_path_join(*parts):
        """Join paths safely across platforms"""
        # Remove empty parts
        parts = [p for p in parts if p]
        
        # Use os.path.join for platform-correct separators
        path = os.path.join(*parts)
        
        # Normalize the path
        path = os.path.normpath(path)
        
        return path
    
    @staticmethod
    def find_file_case_insensitive(directory, filename):
        """Find file regardless of case"""
        # First try exact match
        exact_path = os.path.join(directory, filename)
        if os.path.exists(exact_path):
            return exact_path
        
        # Try case-insensitive search
        filename_lower = filename.lower()
        
        try:
            for item in os.listdir(directory):
                if item.lower() == filename_lower:
                    return os.path.join(directory, item)
        except OSError:
            pass
        
        return None
    
    @staticmethod
    def handle_file_urls(url):
        """Convert file URLs correctly by platform"""
        if url.startswith('file://'):
            if iswindows:
                # Windows: file:///C:/path/to/file
                # or file://server/share/path
                if url.startswith('file:///'):
                    path = url[8:]  # Remove file:///
                else:
                    path = url[5:]  # Remove file://
                
                # Convert forward slashes
                path = path.replace('/', '\\')
                
            else:
                # Unix: file:///path/to/file
                path = url[7:]  # Remove file://
        
        else:
            path = url
        
        return path
    
    @staticmethod
    def execute_platform_command(base_command):
        """Execute command with platform-specific adjustments"""
        import subprocess
        
        if iswindows:
            # Windows: may need shell=True for some commands
            # Use full path for executables
            if not base_command[0].endswith('.exe'):
                base_command[0] = base_command[0] + '.exe'
            
            # Handle paths with spaces
            command = [f'"{arg}"' if ' ' in arg else arg 
                      for arg in base_command]
            
        else:
            # Unix: ensure executable permissions
            if os.path.exists(base_command[0]):
                os.chmod(base_command[0], 0o755)
            
            command = base_command
        
        # Execute with proper encoding
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        return result
```

#### Problem 8.2: High DPI display issues

**Symptoms:**
- UI elements too small or too large
- Blurry text or images
- Layout problems on 4K displays

**Root Cause:**
- DPI scaling differences
- Retina display handling
- Qt DPI awareness

**Solution:**
```python
from qt.core import QApplication, Qt

class DPIAwarePlugin:
    """Handle high DPI displays correctly"""
    
    @staticmethod
    def get_dpi_scale():
        """Get current DPI scale factor"""
        app = QApplication.instance()
        if app:
            # Get primary screen
            screen = app.primaryScreen()
            if screen:
                # Logical DPI
                logical_dpi = screen.logicalDotsPerInch()
                
                # Standard DPI is 96 on Windows, 72 on Mac
                standard_dpi = 96 if iswindows else 72
                
                return logical_dpi / standard_dpi
        
        return 1.0
    
    @staticmethod
    def scale_value(value):
        """Scale a value for current DPI"""
        return int(value * DPIAwarePlugin.get_dpi_scale())
    
    def create_dpi_aware_ui(self):
        """Create UI that scales properly"""
        from qt.core import QVBoxLayout, QPushButton, QFont
        
        layout = QVBoxLayout()
        
        # Scale fixed sizes
        button = QPushButton("Test")
        button.setMinimumHeight(self.scale_value(30))
        
        # Scale fonts
        font = QFont()
        base_size = 10
        font.setPointSize(self.scale_value(base_size))
        button.setFont(font)
        
        # Scale spacing
        layout.setSpacing(self.scale_value(5))
        layout.setContentsMargins(
            self.scale_value(10),
            self.scale_value(10),
            self.scale_value(10),
            self.scale_value(10)
        )
        
        layout.addWidget(button)
        
        return layout
    
    @staticmethod
    def load_high_dpi_icon(base_path):
        """Load appropriate icon for display DPI"""
        from qt.core import QIcon, QPixmap
        
        scale = DPIAwarePlugin.get_dpi_scale()
        
        # Try to load @2x or @3x versions for high DPI
        if scale >= 3.0:
            variations = ['@3x', '@2x', '']
        elif scale >= 2.0:
            variations = ['@2x', '']
        else:
            variations = ['']
        
        name, ext = os.path.splitext(base_path)
        
        for suffix in variations:
            path = f"{name}{suffix}{ext}"
            if os.path.exists(path):
                pixmap = QPixmap(path)
                if not pixmap.isNull():
                    return QIcon(pixmap)
        
        # Fallback to base path
        return QIcon(base_path)
```

---

### 9. Development and Testing Issues

#### Problem 9.1: Changes not reflected after reinstall

**Symptoms:**
- Code changes don't appear
- Old version still running
- Must restart Calibre multiple times

**Root Cause:**
- Plugin cached in memory
- Python module caching
- Calibre not fully shut down

**Solution:**
```python
# Development workflow script
import subprocess
import time
import os

class DevelopmentHelper:
    """Streamline development workflow"""
    
    @staticmethod
    def full_reload_cycle(plugin_dir):
        """Complete reload cycle for development"""
        
        print("1. Shutting down Calibre...")
        subprocess.run(['calibre-debug', '-s'])
        
        # Wait for shutdown
        time.sleep(2)
        
        print("2. Building plugin...")
        os.chdir(plugin_dir)
        subprocess.run([
            'zip', '-r', '../plugin.zip', '.',
            '-x', '*.pyc', '-x', '__pycache__/*'
        ])
        
        print("3. Installing plugin...")
        subprocess.run(['calibre-customize', '-b', plugin_dir])
        
        print("4. Launching Calibre in debug mode...")
        subprocess.run(['calibre-debug', '-g'])
    
    @staticmethod
    def clear_plugin_cache():
        """Clear all plugin caches"""
        import shutil
        from calibre.constants import config_dir
        
        # Clear plugin cache
        cache_dir = os.path.join(config_dir, 'plugins', 'cache')
        if os.path.exists(cache_dir):
            shutil.rmtree(cache_dir)
            print(f"Cleared plugin cache: {cache_dir}")
        
        # Clear Python cache
        for root, dirs, files in os.walk('.'):
            if '__pycache__' in dirs:
                pycache = os.path.join(root, '__pycache__')
                shutil.rmtree(pycache)
                print(f"Cleared Python cache: {pycache}")
    
    @staticmethod
    def hot_reload_attempt():
        """Attempt to reload without restart (limited effectiveness)"""
        import importlib
        import sys
        
        # Find and reload plugin modules
        for name, module in list(sys.modules.items()):
            if name.startswith('calibre_plugins.'):
                try:
                    importlib.reload(module)
                    print(f"Reloaded: {name}")
                except:
                    pass
```

**Quick development cycle:**
```bash
#!/bin/bash
# dev-reload.sh
calibre-debug -s  # Shutdown
sleep 2
calibre-customize -b .  # Install from current directory
calibre-debug -g  # Start with debug
```

#### Problem 9.2: Debugging without print statements

**Symptoms:**
- Need breakpoint debugging
- Print statements not showing
- Complex logic hard to trace

**Root Cause:**
- Calibre captures stdout
- No integrated debugger
- Remote debugging setup needed

**Solution:**
```python
# Option 1: Enhanced logging
import logging
import sys

class DebugLogger:
    """Enhanced debugging output"""
    
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        
        # Console output
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter('[%(name)s] %(message)s')
        )
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)
        
        # File output
        from calibre.constants import cache_dir
        log_file = os.path.join(cache_dir, f'{name}.log')
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(
            logging.Formatter(
                '%(asctime)s [%(levelname)s] %(message)s'
            )
        )
        self.logger.addHandler(file_handler)
    
    def debug(self, msg, *args, **kwargs):
        """Enhanced debug output"""
        # Add caller information
        import inspect
        frame = inspect.currentframe().f_back
        
        location = f"{frame.f_code.co_filename}:{frame.f_lineno}"
        self.logger.debug(f"{location} - {msg}", *args, **kwargs)

# Option 2: Remote debugging with debugpy
def setup_remote_debugging(port=5678):
    """Enable remote debugging"""
    try:
        import debugpy
        
        debugpy.listen(port)
        print(f"Waiting for debugger on port {port}...")
        print("In VS Code, attach to 'Python: Remote Attach'")
        
        # Optional: wait for debugger
        # debugpy.wait_for_client()
        
    except ImportError:
        print("debugpy not available - install in Calibre's Python:")
        print("calibre-debug -c 'import pip; pip.main([\"install\", \"debugpy\"])'")

# Option 3: Interactive debugging
def interactive_debug_point(locals_dict):
    """Drop into interactive debugger"""
    import code
    
    # Create banner
    banner = """
    === Interactive Debug Point ===
    Available variables: {}
    Type 'c' or Ctrl-D to continue
    """.format(', '.join(locals_dict.keys()))
    
    # Start interactive console
    code.interact(banner=banner, local=locals_dict)
```

#### Problem 9.3: Testing with mock data

**Symptoms:**
- Need to test without full Calibre
- Database not available in tests
- GUI components hard to test

**Root Cause:**
- Calibre integration tightly coupled
- No test framework provided
- Heavy dependencies

**Solution:**
```python
# Mock Calibre environment for testing
class MockCalibreEnvironment:
    """Mock Calibre for unit testing"""
    
    def __init__(self):
        self.setup_mocks()
    
    def setup_mocks(self):
        """Create all necessary mocks"""
        
        # Mock Qt
        import sys
        from unittest.mock import MagicMock
        
        sys.modules['qt.core'] = MagicMock()
        
        # Mock database
        self.mock_db = MockDatabase()
        
        # Mock GUI
        self.mock_gui = MockGUI(self.mock_db)
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        # Cleanup
        pass

class MockDatabase:
    """Mock Calibre database"""
    
    def __init__(self):
        self.books = {
            1: {
                'title': 'Test Book 1',
                'authors': ['Author 1'],
                'tags': ['fiction', 'test'],
                'formats': ['EPUB', 'PDF']
            },
            2: {
                'title': 'Test Book 2',
                'authors': ['Author 2'],
                'tags': ['non-fiction', 'test'],
                'formats': ['MOBI']
            }
        }
    
    def all_book_ids(self):
        return list(self.books.keys())
    
    def get_metadata(self, book_id):
        from collections import namedtuple
        
        Metadata = namedtuple('Metadata', ['title', 'authors', 'tags'])
        book = self.books.get(book_id, {})
        
        return Metadata(
            title=book.get('title', ''),
            authors=book.get('authors', []),
            tags=book.get('tags', [])
        )
    
    def has_format(self, book_id, fmt):
        book = self.books.get(book_id, {})
        return fmt in book.get('formats', [])

class MockGUI:
    """Mock Calibre GUI"""
    
    def __init__(self, db):
        self.current_db = MagicMock()
        self.current_db.new_api = db
        self.status_bar = MagicMock()
        self.job_manager = MagicMock()

# Usage in tests:
def test_plugin_functionality():
    with MockCalibreEnvironment() as env:
        # Import plugin after mocks are set up
        from calibre_plugins.my_plugin import MyPlugin
        
        # Create plugin instance
        plugin = MyPlugin(env.mock_gui)
        
        # Test functionality
        results = plugin.search_books('test')
        assert len(results) == 2
```

---

### 10. Advanced Debugging Techniques

#### Pattern 10.1: State inspection

```python
class StateInspector:
    """Inspect plugin state for debugging"""
    
    def __init__(self, plugin):
        self.plugin = plugin
    
    def dump_state(self):
        """Dump complete plugin state"""
        import pprint
        import json
        
        state = {
            'class': self.plugin.__class__.__name__,
            'attributes': {},
            'config': {},
            'cache_sizes': {},
        }
        
        # Get all attributes
        for attr in dir(self.plugin):
            if not attr.startswith('_'):
                try:
                    value = getattr(self.plugin, attr)
                    
                    # Skip methods
                    if callable(value):
                        continue
                    
                    # Convert to serializable
                    if hasattr(value, '__dict__'):
                        value = str(value)
                    elif isinstance(value, (list, dict, str, int, float, bool)):
                        pass
                    else:
                        value = str(value)
                    
                    state['attributes'][attr] = value
                    
                except Exception as e:
                    state['attributes'][attr] = f"<Error: {e}>"
        
        # Get configuration
        try:
            if hasattr(self.plugin, 'prefs'):
                state['config'] = dict(self.plugin.prefs)
        except:
            pass
        
        # Get cache sizes
        for attr in dir(self.plugin):
            try:
                value = getattr(self.plugin, attr)
                if isinstance(value, (dict, list)):
                    state['cache_sizes'][attr] = len(value)
            except:
                pass
        
        # Pretty print
        pp = pprint.PrettyPrinter(indent=2)
        pp.pprint(state)
        
        # Also save to file
        from calibre.constants import cache_dir
        debug_file = os.path.join(
            cache_dir, 
            f'{self.plugin.name}_debug_state.json'
        )
        
        with open(debug_file, 'w') as f:
            json.dump(state, f, indent=2, default=str)
        
        print(f"State saved to: {debug_file}")
```

#### Pattern 10.2: Performance profiling

```python
import cProfile
import pstats
import io

class PerformanceProfiler:
    """Profile plugin performance"""
    
    def __init__(self):
        self.profiler = None
    
    def start_profiling(self):
        """Start profiling"""
        self.profiler = cProfile.Profile()
        self.profiler.enable()
    
    def stop_profiling(self, top_n=20):
        """Stop and display results"""
        self.profiler.disable()
        
        # Get stats
        s = io.StringIO()
        ps = pstats.Stats(self.profiler, stream=s)
        ps.strip_dirs()
        ps.sort_stats('cumulative')
        ps.print_stats(top_n)
        
        print("\n=== Performance Profile ===")
        print(s.getvalue())
        
        # Save detailed profile
        from calibre.constants import cache_dir
        profile_file = os.path.join(cache_dir, 'plugin_profile.stats')
        ps.dump_stats(profile_file)
        print(f"Detailed profile saved to: {profile_file}")
    
    def profile_function(self, func):
        """Decorator to profile specific function"""
        def wrapper(*args, **kwargs):
            self.start_profiling()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                self.stop_profiling()
        
        return wrapper
```

### Debugging Checklist

When encountering issues, follow this systematic checklist:

1. **Verify basics:**
   - [ ] Correct Python version (3.x for Calibre 5+)
   - [ ] All imports use `qt.core`
   - [ ] Plugin ZIP has correct structure
   - [ ] `__init__.py` at root level
   - [ ] Multi-file marker present if needed

2. **Check environment:**
   - [ ] Run `calibre-debug -g` for console output
   - [ ] Check `~/.config/calibre/plugins/` for errors
   - [ ] Verify no conflicting plugins
   - [ ] Test with clean library

3. **Isolate the problem:**
   - [ ] Disable other plugins
   - [ ] Test with minimal code
   - [ ] Add debug prints at key points
   - [ ] Check if platform-specific

4. **Gather information:**
   - [ ] Full error traceback
   - [ ] Calibre version
   - [ ] Platform details
   - [ ] Steps to reproduce

5. **Common fixes to try:**
   - [ ] Full Calibre restart
   - [ ] Clear plugin cache
   - [ ] Reinstall plugin
   - [ ] Test with new library
   - [ ] Check file permissions

### Best Practices for Avoiding Issues

1. **Always test on all platforms** before release
2. **Use defensive programming** - check for None, handle exceptions
3. **Follow Calibre patterns** - study built-in plugins
4. **Keep imports minimal** - reduce dependencies
5. **Cache appropriately** - balance memory vs performance
6. **Document requirements** clearly
7. **Version your plugins** to track issues
8. **Provide debug mode** for users
9. **Log errors properly** with context
10. **Test edge cases** - empty libraries, missing files, etc.

This comprehensive troubleshooting guide should help resolve most common issues encountered during Calibre plugin development. Remember that the Calibre forum and developer documentation are valuable resources for additional help.