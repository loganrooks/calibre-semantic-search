"""
Pytest configuration for UI tests that require PyQt5
"""

import pytest
import sys
from pathlib import Path

try:
    from PyQt5.QtWidgets import QApplication
    PYQT5_AVAILABLE = True
except ImportError:
    PYQT5_AVAILABLE = False


@pytest.fixture(scope='session')
def qapp():
    """Create QApplication for GUI tests"""
    if not PYQT5_AVAILABLE:
        pytest.skip("PyQt5 not available for UI tests")
    
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def skip_if_no_pyqt5():
    """Skip test if PyQt5 is not available"""
    if not PYQT5_AVAILABLE:
        pytest.skip("PyQt5 not available")