# Agent 6: Testing & Development Workflow Expert Report
## Comprehensive Guide to Testing and Development Workflows for Calibre Plugins

### Executive Summary

Testing Calibre plugins requires a unique approach due to the embedded Python environment, Qt GUI framework, and lack of built-in testing infrastructure. This report provides comprehensive strategies for development workflows, testing methodologies, debugging techniques, and continuous integration approaches that ensure robust plugin development.

### 1. Development Environment Setup

#### Complete Development Configuration

```bash
# Essential Environment Variables
export CALIBRE_DEVELOP_FROM="/path/to/calibre/src"
export CALIBRE_USE_DARK_PALETTE=1  # For dark theme testing
export CALIBRE_OVERRIDE_LANG="de"  # For i18n testing
export QT_LOGGING_RULES="*=true"   # Enable Qt debug output

# Development Installation Methods
# Method 1: From source
git clone https://github.com/kovidgoyal/calibre.git
cd calibre
python setup.py develop

# Method 2: Using packaged Calibre with development mode
calibre-debug -g --develop-from=/path/to/plugin/src
```

#### Project Structure for Development

```
semantic_search_plugin/
├── .git/
├── .github/
│   └── workflows/
│       ├── test.yml          # CI testing
│       └── release.yml       # Auto-release
├── src/
│   ├── __init__.py
│   ├── plugin-import-name-semantic_search.txt
│   ├── ui.py
│   ├── config.py
│   ├── indexer.py
│   └── search.py
├── tests/
│   ├── __init__.py
│   ├── test_indexer.py
│   ├── test_search.py
│   ├── test_integration.py
│   └── fixtures/
│       └── test_library/
├── resources/
│   ├── images/
│   └── translations/
├── tools/
│   ├── build.py
│   ├── test_runner.py
│   └── debug_launcher.py
├── Makefile
├── README.md
└── requirements-dev.txt
```

### 2. Development Workflow Automation

#### Makefile for Common Tasks

```makefile
# Makefile for Calibre plugin development
PLUGIN_NAME = semantic_search
CALIBRE_LIBRARY = ./test_library

.PHONY: build install uninstall test clean debug release

build:
	@echo "Building plugin..."
	cd src && zip -r ../$(PLUGIN_NAME).zip . -x "*.pyc" -x "__pycache__/*"

install: build
	@echo "Installing plugin..."
	calibre-customize -a $(PLUGIN_NAME).zip

uninstall:
	@echo "Uninstalling plugin..."
	calibre-customize -r "$(PLUGIN_NAME)"

test: install
	@echo "Running tests..."
	calibre-debug -e tests/test_runner.py

clean:
	@echo "Cleaning..."
	rm -f $(PLUGIN_NAME).zip
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} +

debug: install
	@echo "Launching Calibre in debug mode..."
	calibre-debug -g --with-library=$(CALIBRE_LIBRARY)

watch:
	@echo "Watching for changes..."
	@while true; do \
		make install; \
		inotifywait -qre modify src/; \
	done

profile: install
	@echo "Running with profiler..."
	calibre-debug -g --profile --with-library=$(CALIBRE_LIBRARY)
```

#### Build Script with Validation

```python
#!/usr/bin/env python3
# tools/build.py
import os
import sys
import zipfile
import ast
from pathlib import Path

class PluginBuilder:
    """Automated plugin builder with validation"""
    
    def __init__(self, src_dir='src', output='plugin.zip'):
        self.src_dir = Path(src_dir)
        self.output = output
        self.errors = []
    
    def validate_structure(self):
        """Validate plugin structure"""
        # Check required files
        required_files = ['__init__.py']
        for req_file in required_files:
            if not (self.src_dir / req_file).exists():
                self.errors.append(f"Missing required file: {req_file}")
        
        # Check for multi-file marker if needed
        py_files = list(self.src_dir.glob('*.py'))
        if len(py_files) > 1:
            marker_files = list(self.src_dir.glob('plugin-import-name-*.txt'))
            if not marker_files:
                self.errors.append("Multi-file plugin missing import marker")
    
    def validate_syntax(self):
        """Validate Python syntax"""
        for py_file in self.src_dir.rglob('*.py'):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    ast.parse(f.read())
            except SyntaxError as e:
                self.errors.append(f"Syntax error in {py_file}: {e}")
    
    def validate_imports(self):
        """Check for problematic imports"""
        problematic = ['PyQt5', 'PyQt6', 'numpy', 'scipy']
        
        for py_file in self.src_dir.rglob('*.py'):
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                for prob in problematic:
                    if f'import {prob}' in content or f'from {prob}' in content:
                        self.errors.append(
                            f"Problematic import '{prob}' in {py_file}"
                        )
    
    def build(self):
        """Build the plugin ZIP"""
        if self.errors:
            print("Validation errors found:")
            for error in self.errors:
                print(f"  - {error}")
            return False
        
        with zipfile.ZipFile(self.output, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path in self.src_dir.rglob('*'):
                if file_path.is_file():
                    if '__pycache__' in str(file_path):
                        continue
                    if file_path.suffix == '.pyc':
                        continue
                    
                    arcname = file_path.relative_to(self.src_dir)
                    zf.write(file_path, arcname)
        
        print(f"Plugin built successfully: {self.output}")
        return True
    
    def run(self):
        """Run all validations and build"""
        print("Validating plugin structure...")
        self.validate_structure()
        
        print("Validating Python syntax...")
        self.validate_syntax()
        
        print("Checking imports...")
        self.validate_imports()
        
        return self.build()

if __name__ == '__main__':
    builder = PluginBuilder()
    sys.exit(0 if builder.run() else 1)
```

### 3. Unit Testing Strategies

#### Mock Framework for Calibre Components

```python
# tests/mocks.py
from unittest.mock import Mock, MagicMock, PropertyMock
from collections import defaultdict

class MockDatabase:
    """Mock Calibre database for testing"""
    
    def __init__(self):
        self.data = defaultdict(dict)
        self.metadata = {}
        
    def all_book_ids(self):
        return list(self.data.keys())
    
    def get_metadata(self, book_id):
        meta = Mock()
        meta.title = f"Book {book_id}"
        meta.authors = ["Test Author"]
        return meta
    
    def set_metadata(self, book_id, metadata):
        self.metadata[book_id] = metadata

class MockGUI:
    """Mock Calibre GUI for testing"""
    
    def __init__(self):
        self.current_db = Mock()
        self.current_db.new_api = MockDatabase()
        self.library_view = Mock()
        self.tags_view = Mock()
        self.status_bar = Mock()
        self.job_manager = Mock()

class MockQWidget:
    """Mock Qt widget for testing"""
    
    def __init__(self, parent=None):
        self.parent = parent
        self._visible = False
        self._enabled = True
        
    def show(self):
        self._visible = True
    
    def hide(self):
        self._visible = False
    
    def setEnabled(self, enabled):
        self._enabled = enabled
```

#### Test Runner Implementation

```python
#!/usr/bin/env python3
# tests/test_runner.py
import sys
import unittest
from pathlib import Path

# Add plugin source to path
plugin_dir = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(plugin_dir))

class CalibreTestRunner:
    """Custom test runner for Calibre plugins"""
    
    def __init__(self):
        self.test_dir = Path(__file__).parent
        self.results = []
    
    def discover_tests(self):
        """Discover all test modules"""
        loader = unittest.TestLoader()
        suite = loader.discover(str(self.test_dir), pattern='test_*.py')
        return suite
    
    def run_tests(self):
        """Run all tests with detailed output"""
        suite = self.discover_tests()
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        return result.wasSuccessful()
    
    def run_specific_test(self, test_name):
        """Run a specific test case"""
        loader = unittest.TestLoader()
        try:
            suite = loader.loadTestsFromName(test_name)
            runner = unittest.TextTestRunner(verbosity=2)
            result = runner.run(suite)
            return result.wasSuccessful()
        except Exception as e:
            print(f"Error running test {test_name}: {e}")
            return False

if __name__ == '__main__':
    runner = CalibreTestRunner()
    
    if len(sys.argv) > 1:
        # Run specific test
        success = runner.run_specific_test(sys.argv[1])
    else:
        # Run all tests
        success = runner.run_tests()
    
    sys.exit(0 if success else 1)
```

#### Unit Test Examples

```python
# tests/test_indexer.py
import unittest
from unittest.mock import Mock, patch
import sys

# Mock Qt before importing plugin
sys.modules['qt.core'] = Mock()

from calibre_plugins.semantic_search.indexer import BookIndexer

class TestBookIndexer(unittest.TestCase):
    """Test book indexing functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_gui = Mock()
        self.mock_db = Mock()
        self.indexer = BookIndexer(self.mock_gui)
    
    def test_extract_text_from_book(self):
        """Test text extraction"""
        # Mock book data
        book_id = 1
        self.mock_db.format_metadata.return_value = {
            'EPUB': {'path': '/path/to/book.epub'}
        }
        
        with patch('calibre_plugins.semantic_search.indexer.get_epub_text') as mock_get_text:
            mock_get_text.return_value = "Sample book text"
            
            text = self.indexer.extract_text(book_id, self.mock_db)
            
            self.assertEqual(text, "Sample book text")
            mock_get_text.assert_called_once()
    
    def test_generate_embedding(self):
        """Test embedding generation"""
        text = "Sample text for embedding"
        
        # Test with mock embedding service
        with patch('calibre_plugins.semantic_search.indexer.EmbeddingService') as mock_service:
            mock_service.return_value.generate.return_value = [0.1] * 768
            
            embedding = self.indexer.generate_embedding(text)
            
            self.assertEqual(len(embedding), 768)
            self.assertTrue(all(isinstance(x, float) for x in embedding))
    
    def test_batch_indexing(self):
        """Test batch indexing of multiple books"""
        book_ids = [1, 2, 3]
        
        with patch.object(self.indexer, 'index_book') as mock_index:
            mock_index.return_value = True
            
            results = self.indexer.batch_index(book_ids)
            
            self.assertEqual(mock_index.call_count, 3)
            self.assertEqual(len(results), 3)
```

### 4. Integration Testing

#### Full Plugin Integration Tests

```python
# tests/test_integration.py
import unittest
import tempfile
import shutil
from pathlib import Path

class TestPluginIntegration(unittest.TestCase):
    """Integration tests for the full plugin"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test library"""
        cls.temp_dir = tempfile.mkdtemp()
        cls.library_path = Path(cls.temp_dir) / 'test_library'
        
        # Create minimal Calibre library structure
        cls.library_path.mkdir()
        (cls.library_path / 'metadata.db').touch()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test library"""
        shutil.rmtree(cls.temp_dir)
    
    def test_plugin_loads_in_calibre(self):
        """Test that plugin loads without errors"""
        # This would require running actual Calibre
        # Typically done with subprocess
        import subprocess
        
        result = subprocess.run([
            'calibre-debug', '-c',
            'from calibre.customize.ui import find_plugin; '
            'print(find_plugin("Semantic Search") is not None)'
        ], capture_output=True, text=True)
        
        self.assertIn('True', result.stdout)
    
    def test_database_operations(self):
        """Test database operations in isolation"""
        from calibre.library import db
        
        # Create test database
        test_db = db(self.library_path).new_api
        
        # Add test book
        book_id = test_db.add_book({
            'title': 'Test Book',
            'authors': ['Test Author']
        })
        
        self.assertIsNotNone(book_id)
        
        # Test plugin database operations
        # ... plugin-specific database tests
```

### 5. GUI Testing Strategies

#### Qt Test Framework Integration

```python
# tests/test_gui.py
import unittest
from unittest.mock import Mock, patch

# Mock Qt test utilities
class MockQTest:
    @staticmethod
    def mouseClick(widget, button, modifier=None, pos=None, delay=-1):
        widget.clicked.emit()
    
    @staticmethod
    def keyClick(widget, key, modifier=None, delay=-1):
        widget.key_pressed.emit(key)
    
    @staticmethod
    def keyClicks(widget, text, modifier=None, delay=-1):
        widget.setText(text)

class TestPluginGUI(unittest.TestCase):
    """Test plugin GUI components"""
    
    def setUp(self):
        """Set up GUI mocks"""
        # Mock Qt modules
        self.qt_core_mock = Mock()
        self.qt_core_mock.QWidget = Mock
        self.qt_core_mock.QDialog = Mock
        self.qt_core_mock.QPushButton = Mock
        
        # Patch imports
        self.patcher = patch.dict('sys.modules', {
            'qt.core': self.qt_core_mock
        })
        self.patcher.start()
    
    def tearDown(self):
        self.patcher.stop()
    
    def test_dialog_creation(self):
        """Test dialog initialization"""
        from calibre_plugins.semantic_search.dialog import SearchDialog
        
        mock_parent = Mock()
        mock_icon = Mock()
        
        dialog = SearchDialog(mock_parent, mock_icon)
        
        # Verify dialog setup
        self.assertIsNotNone(dialog)
        # Add specific assertions based on dialog structure
    
    def test_search_interaction(self):
        """Test search functionality"""
        from calibre_plugins.semantic_search.dialog import SearchDialog
        
        dialog = SearchDialog(Mock(), Mock())
        
        # Simulate user input
        MockQTest.keyClicks(dialog.search_input, "test query")
        MockQTest.mouseClick(dialog.search_button, Mock())
        
        # Verify search was triggered
        # Add assertions for search behavior
```

### 6. Debugging Techniques

#### Advanced Debugging Setup

```python
#!/usr/bin/env python3
# tools/debug_launcher.py
import os
import sys
import subprocess
from pathlib import Path

class DebugLauncher:
    """Advanced debugging launcher for Calibre plugins"""
    
    def __init__(self):
        self.plugin_dir = Path(__file__).parent.parent
        self.options = {
            'verbose': False,
            'profile': False,
            'trace': False,
            'breakpoint': None,
            'library': None,
        }
    
    def setup_debugging_environment(self):
        """Configure debugging environment"""
        # Enable verbose Qt logging
        os.environ['QT_LOGGING_RULES'] = '*=true'
        
        # Enable Python development mode
        os.environ['PYTHONDEVMODE'] = '1'
        
        # Set up remote debugging if requested
        if self.options.get('remote_debug'):
            self.setup_remote_debugging()
    
    def setup_remote_debugging(self):
        """Set up remote debugging with debugpy"""
        try:
            import debugpy
            debugpy.listen(5678)
            print("Waiting for debugger to attach on port 5678...")
            debugpy.wait_for_client()
        except ImportError:
            print("debugpy not available for remote debugging")
    
    def build_command(self):
        """Build calibre-debug command with options"""
        cmd = ['calibre-debug', '-g']
        
        if self.options['verbose']:
            cmd.append('-v')
        
        if self.options['profile']:
            cmd.append('--profile')
        
        if self.options['library']:
            cmd.extend(['--with-library', self.options['library']])
        
        if self.options['trace']:
            # Add Python trace
            cmd.extend(['-c', '''
import sys
import trace

def trace_calls(frame, event, arg):
    if event != 'call':
        return
    code = frame.f_code
    print(f"Called: {code.co_filename}:{code.co_name}")
    return trace_calls

sys.settrace(trace_calls)
'''])
        
        return cmd
    
    def launch(self):
        """Launch Calibre with debugging"""
        self.setup_debugging_environment()
        cmd = self.build_command()
        
        print(f"Launching: {' '.join(cmd)}")
        subprocess.run(cmd)

if __name__ == '__main__':
    launcher = DebugLauncher()
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-p', '--profile', action='store_true')
    parser.add_argument('-t', '--trace', action='store_true')
    parser.add_argument('-r', '--remote-debug', action='store_true')
    parser.add_argument('-l', '--library', help='Path to test library')
    
    args = parser.parse_args()
    launcher.options.update(vars(args))
    
    launcher.launch()
```

#### Logging and Tracing System

```python
# src/debug_utils.py
import logging
import functools
import time
from datetime import datetime

class PluginDebugger:
    """Comprehensive debugging utilities"""
    
    def __init__(self, plugin_name):
        self.plugin_name = plugin_name
        self.setup_logging()
    
    def setup_logging(self):
        """Configure detailed logging"""
        # Create logger
        self.logger = logging.getLogger(f'calibre_plugins.{self.plugin_name}')
        self.logger.setLevel(logging.DEBUG)
        
        # Console handler with detailed format
        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
        
        formatter = logging.Formatter(
            '%(asctime)s [%(name)s] %(levelname)s '
            '%(filename)s:%(lineno)d - %(message)s'
        )
        console.setFormatter(formatter)
        
        self.logger.addHandler(console)
        
        # File handler for persistent logs
        from calibre.constants import cache_dir
        log_file = os.path.join(cache_dir, f'{self.plugin_name}_debug.log')
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
    
    def trace_calls(self, func):
        """Decorator to trace function calls"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Log entry
            self.logger.debug(
                f"Entering {func.__name__} "
                f"args={args} kwargs={kwargs}"
            )
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                
                # Log successful completion
                self.logger.debug(
                    f"Exiting {func.__name__} "
                    f"elapsed={elapsed:.3f}s result={result}"
                )
                
                return result
                
            except Exception as e:
                elapsed = time.time() - start_time
                
                # Log exception
                self.logger.exception(
                    f"Exception in {func.__name__} "
                    f"elapsed={elapsed:.3f}s"
                )
                raise
        
        return wrapper
    
    def memory_profile(self, func):
        """Decorator to profile memory usage"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import tracemalloc
            
            tracemalloc.start()
            snapshot1 = tracemalloc.take_snapshot()
            
            result = func(*args, **kwargs)
            
            snapshot2 = tracemalloc.take_snapshot()
            top_stats = snapshot2.compare_to(snapshot1, 'lineno')
            
            self.logger.debug(f"Memory profile for {func.__name__}:")
            for stat in top_stats[:10]:
                self.logger.debug(stat)
            
            tracemalloc.stop()
            return result
        
        return wrapper
```

### 7. Continuous Integration

#### GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Test Plugin

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        calibre-version: ['5.44.0', '6.0.0', 'latest']
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install Calibre (Linux)
      if: runner.os == 'Linux'
      run: |
        sudo -v
        wget -nv -O- https://download.calibre-ebook.com/linux-installer.sh | sudo sh /dev/stdin
    
    - name: Install Calibre (Windows)
      if: runner.os == 'Windows'
      run: |
        choco install calibre --version=${{ matrix.calibre-version }}
    
    - name: Install Calibre (macOS)
      if: runner.os == 'macOS'
      run: |
        brew install --cask calibre
    
    - name: Build plugin
      run: |
        python tools/build.py
    
    - name: Install plugin
      run: |
        calibre-customize -a semantic_search.zip
    
    - name: Run unit tests
      run: |
        python -m pytest tests/unit/ -v
    
    - name: Run integration tests
      run: |
        calibre-debug -e tests/test_runner.py
    
    - name: Lint code
      run: |
        pip install flake8 pylint
        flake8 src/ --max-line-length=100
        pylint src/
    
    - name: Check imports
      run: |
        python tools/check_imports.py
    
    - name: Generate coverage report
      if: runner.os == 'Linux'
      run: |
        pip install coverage
        coverage run -m pytest tests/
        coverage xml
    
    - name: Upload coverage
      if: runner.os == 'Linux'
      uses: codecov/codecov-action@v3
```

#### Local CI Simulation

```python
#!/usr/bin/env python3
# tools/ci_local.py
import subprocess
import sys
from pathlib import Path

class LocalCI:
    """Simulate CI pipeline locally"""
    
    def __init__(self):
        self.root = Path(__file__).parent.parent
        self.passed = []
        self.failed = []
    
    def run_step(self, name, command):
        """Run a CI