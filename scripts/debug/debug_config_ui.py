#!/usr/bin/env python3
"""
Debug script to test what's happening with the config UI
"""

import sys
import os

def test_config_in_calibre_environment():
    """Test the config widget in a way that simulates Calibre's environment"""
    
    print("🔍 Debugging Configuration UI Issues")
    print("=" * 50)
    
    # Add plugin path like Calibre would
    plugin_path = os.path.join(os.path.dirname(__file__), 'calibre_plugins', 'semantic_search')
    if plugin_path not in sys.path:
        sys.path.insert(0, plugin_path)
    
    # Mock calibre modules that the config needs
    class MockJSONConfig:
        def __init__(self):
            self._data = {
                "embedding_provider": "openai",
                "embedding_model": "text-embedding-3-small",
                "embedding_dimensions": 1536,
                "api_keys": {},
                "search_options": {"default_limit": 20, "similarity_threshold": 0.7, "scope": "library"},
                "ui_options": {"floating_window": False, "window_opacity": 0.95, "remember_position": True},
                "performance": {"cache_enabled": True, "cache_size_mb": 100, "batch_size": 100}
            }
        
        def get(self, key, default=None):
            keys = key.split('.')
            data = self._data
            for k in keys:
                if isinstance(data, dict) and k in data:
                    data = data[k]
                else:
                    return default
            return data
        
        def set(self, key, value):
            pass
            
        def save(self):
            pass
    
    # Mock PyQt5/Qt
    class MockQWidget:
        def __init__(self): pass
        def setLayout(self, layout): pass
    
    class MockQVBoxLayout:
        def __init__(self): pass
        def addWidget(self, widget): pass
        def addStretch(self): pass
        def addRow(self, label, widget): pass
    
    class MockQTabWidget:
        def __init__(self): pass
        def addTab(self, widget, name): pass
    
    class MockQComboBox:
        def __init__(self): 
            self._items = []
            self._current = 0
        def addItems(self, items): 
            self._items.extend(items)
            print(f"   📝 Added {len(items)} items to dropdown: {items[:3]}{'...' if len(items) > 3 else ''}")
        def setCurrentText(self, text): pass
        def currentText(self): return self._items[self._current] if self._items else ""
        def setToolTip(self, tip): pass
        def setEditable(self, editable): pass
        def setInsertPolicy(self, policy): pass
        def currentTextChanged(self): 
            class MockSignal:
                def connect(self, func): pass
            return MockSignal()
        def clear(self): 
            self._items = []
            print("   🧹 Cleared dropdown items")
        def lineEdit(self):
            class MockLineEdit:
                def setPlaceholderText(self, text): pass
                def setCompleter(self, completer): pass
            return MockLineEdit()
        def setCurrentIndex(self, index): pass
        def setEnabled(self, enabled): pass
    
    class MockQGroupBox:
        def __init__(self, title): 
            self.title = title
            print(f"   📦 Created group box: {title}")
        def setLayout(self, layout): pass
        def setVisible(self, visible): 
            status = "visible" if visible else "hidden"
            print(f"   👁️ {self.title}: {status}")
    
    class MockQLabel:
        def __init__(self, text=""): 
            self.text = text
        def setWordWrap(self, wrap): pass
        def setStyleSheet(self, style): pass
        def setText(self, text): 
            if text and "dimensions" in text:
                print(f"   📊 Model metadata: {text}")
    
    class MockQLineEdit:
        def __init__(self): pass
        def setPlaceholderText(self, text): pass
        def setText(self, text): pass
        def text(self): return ""
        def setEchoMode(self, mode): pass
        def setEnabled(self, enabled): pass
    
    class MockQFormLayout:
        def __init__(self): pass
        def addRow(self, *args): pass
    
    class MockQPushButton:
        def __init__(self, text): pass
        def clicked(self):
            class MockSignal:
                def connect(self, func): pass
            return MockSignal()
    
    # Other mocks
    class MockQSpinBox:
        def __init__(self): pass
        def setRange(self, min_val, max_val): pass
        def setValue(self, val): pass
        def value(self): return 768
        def setSingleStep(self, step): pass
        def setSuffix(self, suffix): pass
    
    class MockQCheckBox:
        def __init__(self, text=""): pass
        def setChecked(self, checked): pass
    
    class MockQSlider:
        def __init__(self, orientation): pass
        def setRange(self, min_val, max_val): pass
        def setValue(self, val): pass
        def setSingleStep(self, step): pass
        def valueChanged(self):
            class MockSignal:
                def connect(self, func): pass
            return MockSignal()
    
    class MockQt:
        Horizontal = 1
        CaseInsensitive = 1
        MatchContains = 1
    
    class MockQCompleter:
        def __init__(self, items): 
            print(f"   🔍 Created search completer with {len(items)} items")
        def setCaseSensitivity(self, case): pass
        def setFilterMode(self, mode): pass
    
    # Mock the modules
    import types
    calibre_utils_config = types.ModuleType('calibre.utils.config')
    calibre_utils_config.JSONConfig = MockJSONConfig
    sys.modules['calibre.utils.config'] = calibre_utils_config
    
    pyqt5_qt = types.ModuleType('PyQt5.Qt')
    pyqt5_qt.QWidget = MockQWidget
    pyqt5_qt.QVBoxLayout = MockQVBoxLayout
    pyqt5_qt.QTabWidget = MockQTabWidget
    pyqt5_qt.QComboBox = MockQComboBox
    pyqt5_qt.QGroupBox = MockQGroupBox
    pyqt5_qt.QLabel = MockQLabel
    pyqt5_qt.QLineEdit = MockQLineEdit
    pyqt5_qt.QFormLayout = MockQFormLayout
    pyqt5_qt.QPushButton = MockQPushButton
    pyqt5_qt.QSpinBox = MockQSpinBox
    pyqt5_qt.QCheckBox = MockQCheckBox
    pyqt5_qt.QSlider = MockQSlider
    pyqt5_qt.Qt = MockQt
    pyqt5_qt.QCompleter = MockQCompleter
    sys.modules['PyQt5.Qt'] = pyqt5_qt
    
    # Now try to import and create the config widget
    try:
        print("\n1. Testing ConfigWidget Import...")
        from config import ConfigWidget
        print("   ✅ ConfigWidget imported successfully")
        
        print("\n2. Testing ConfigWidget Creation...")
        config_widget = ConfigWidget()
        print("   ✅ ConfigWidget created successfully")
        
        print("\n3. Testing Provider Sections...")
        sections = ['openai_group', 'vertex_group', 'cohere_group', 'azure_group']
        for section in sections:
            if hasattr(config_widget, section):
                print(f"   ✅ {section} exists")
            else:
                print(f"   ❌ {section} missing")
        
        print("\n4. Testing Model Selection Enhancement...")
        if hasattr(config_widget, 'model_metadata_label'):
            print("   ✅ model_metadata_label exists")
        else:
            print("   ❌ model_metadata_label missing")
        
        print("\n5. Testing Provider Change...")
        config_widget._on_provider_changed("openai")
        
        print("\n6. Testing Model Selection...")
        config_widget._update_provider_models("openai")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_config_in_calibre_environment()
    if success:
        print("\n🎉 Configuration widget appears to be working!")
        print("The issue might be with how Calibre is loading the config.")
    else:
        print("\n❌ Configuration widget has issues that need fixing.")