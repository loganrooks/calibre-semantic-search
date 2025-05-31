"""
Mock Calibre modules for testing
This must be imported BEFORE any plugin modules
"""

import sys
import unittest.mock as mock

# Mock all Calibre modules that our plugin uses
calibre_modules = [
    'calibre',
    'calibre.customize',
    'calibre.gui2',
    'calibre.gui2.actions',
    'calibre.utils',
    'calibre.utils.config',
    'calibre.utils.browser',
    'calibre.constants',
    'calibre.ebooks',
    'calibre.library',
    'calibre.library.field_metadata',
    'qt',
    'qt.core',
    'PyQt5',
    'PyQt5.Qt',
]

# Create mock modules
for module_name in calibre_modules:
    sys.modules[module_name] = mock.MagicMock()

# Set up specific mocks that need special behavior
# InterfaceActionBase for plugin base class
sys.modules['calibre.customize'].InterfaceActionBase = type('InterfaceActionBase', (), {})

# InterfaceAction for UI
sys.modules['calibre.gui2.actions'].InterfaceAction = type('InterfaceAction', (), {
    'name': 'Test',
    'action_spec': ('Test', None, 'Test', None),
    'genesis': lambda self: None,
})

# JSONConfig for configuration
class MockJSONConfig:
    def __init__(self, name):
        self.name = name
        self._data = {}
    
    def __getitem__(self, key):
        return self._data.get(key, {})
    
    def __setitem__(self, key, value):
        self._data[key] = value
    
    def get(self, key, default=None):
        return self._data.get(key, default)
    
    def set(self, key, value):
        self._data[key] = value
    
    def commit(self):
        pass

sys.modules['calibre.utils.config'].JSONConfig = MockJSONConfig

# Qt mocks
class MockQToolButton:
    class ToolButtonPopupMode:
        MenuButtonPopup = 0
        InstantPopup = 1
        DelayedPopup = 2

sys.modules['qt.core'].QToolButton = MockQToolButton
sys.modules['PyQt5.Qt'].QToolButton = MockQToolButton

# Mock other Qt classes as needed
for qt_class in ['QAction', 'QIcon', 'QMenu', 'QWidget', 'QDialog']:
    setattr(sys.modules['qt.core'], qt_class, mock.MagicMock)
    setattr(sys.modules['PyQt5.Qt'], qt_class, mock.MagicMock)