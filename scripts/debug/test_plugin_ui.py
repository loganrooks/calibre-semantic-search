#!/usr/bin/env python3
"""
Test Calibre Plugin UI Components Standalone
This allows testing without constantly reloading Calibre
"""

import sys
import os

# Add calibre to path
calibre_src = os.path.expanduser('~/Code/calibre-src/src')
if os.path.exists(calibre_src):
    sys.path.insert(0, calibre_src)

# Test imports
def test_imports():
    """Test if all imports work correctly"""
    print("Testing imports...")
    
    try:
        from qt.core import QToolButton, QIcon, QAction
        print("✅ qt.core imports successful")
        print(f"   QToolButton.ToolButtonPopupMode.MenuButtonPopup = {QToolButton.ToolButtonPopupMode.MenuButtonPopup}")
    except ImportError as e:
        print(f"❌ qt.core import failed: {e}")
        try:
            from PyQt5.Qt import QToolButton, QIcon, QAction
            print("✅ PyQt5 fallback successful")
        except:
            print("❌ PyQt5 fallback also failed")
            
    try:
        from calibre.gui2.actions import InterfaceAction
        print("✅ InterfaceAction import successful")
    except ImportError as e:
        print(f"❌ InterfaceAction import failed: {e}")
        
    try:
        from calibre.gui2 import error_dialog, info_dialog
        print("✅ Dialog imports successful")
    except ImportError as e:
        print(f"❌ Dialog import failed: {e}")

def test_icon_loading():
    """Test icon loading methods"""
    print("\nTesting icon loading...")
    
    try:
        from qt.core import QIcon
        
        # Test QIcon.ic method
        if hasattr(QIcon, 'ic'):
            icon = QIcon.ic('search.png')
            print(f"✅ QIcon.ic() available - icon null: {icon.isNull()}")
        else:
            print("❌ QIcon.ic() not available")
            
        # Test alternative icon loading
        from calibre.gui2 import get_icons
        icon = get_icons('search.png')
        print(f"✅ get_icons() works - type: {type(icon)}")
        
    except Exception as e:
        print(f"❌ Icon loading failed: {e}")

def test_popup_type_values():
    """Test the correct popup type values"""
    print("\nTesting popup type values...")
    
    try:
        from qt.core import QToolButton
        
        print(f"✅ MenuButtonPopup = {QToolButton.ToolButtonPopupMode.MenuButtonPopup}")
        print(f"✅ InstantPopup = {QToolButton.ToolButtonPopupMode.InstantPopup}")
        print(f"✅ DelayedPopup = {QToolButton.ToolButtonPopupMode.DelayedPopup}")
        
    except Exception as e:
        print(f"❌ Failed to get popup types: {e}")

def test_plugin_structure():
    """Test if our plugin structure is correct"""
    print("\nTesting plugin structure...")
    
    # Add our plugin to path
    plugin_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..')
    sys.path.insert(0, plugin_path)
    
    try:
        from calibre_plugins.semantic_search.ui import SemanticSearchInterface
        print("✅ Plugin import successful")
        
        # Check attributes
        plugin = SemanticSearchInterface(None, None)
        print(f"✅ name = {plugin.name}")
        print(f"✅ popup_type = {plugin.popup_type}")
        print(f"✅ action_add_menu = {plugin.action_add_menu}")
        
    except Exception as e:
        import traceback
        print(f"❌ Plugin test failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    print("=== Calibre Plugin UI Testing ===\n")
    
    test_imports()
    test_icon_loading()
    test_popup_type_values()
    test_plugin_structure()
    
    print("\n=== Testing Complete ===")