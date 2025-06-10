#!/usr/bin/env python3
"""
Test script to check Qt API availability in Calibre environment
Run with: calibre-debug -c "exec(open('test_calibre_qt_api.py').read())"
"""

print("=== Calibre Qt API Test ===")

try:
    from qt.core import QCompleter
    print("✅ Successfully imported QCompleter from qt.core")
    
    # Check what completion modes are available
    print("\n🔍 Available QCompleter attributes:")
    completer_attrs = [attr for attr in dir(QCompleter) if not attr.startswith('_')]
    for attr in sorted(completer_attrs):
        print(f"  - {attr}")
    
    print("\n🎯 Completion mode constants:")
    completion_attrs = [attr for attr in dir(QCompleter) if 'ompletion' in attr]
    for attr in completion_attrs:
        try:
            value = getattr(QCompleter, attr)
            print(f"  - QCompleter.{attr} = {value}")
        except Exception as e:
            print(f"  - QCompleter.{attr} = ERROR: {e}")
    
    # Test creating a completer instance
    print("\n🧪 Testing QCompleter instantiation:")
    try:
        completer = QCompleter()
        print("✅ QCompleter() created successfully")
        
        # Test setting completion mode
        print("\n🔧 Testing completion mode setting:")
        try:
            completer.setCompletionMode(QCompleter.PopupCompletion)
            print("✅ QCompleter.PopupCompletion works")
        except Exception as e:
            print(f"❌ QCompleter.PopupCompletion failed: {e}")
        
        try:
            completer.setCompletionMode(QCompleter.InlineCompletion)
            print("✅ QCompleter.InlineCompletion works")
        except Exception as e:
            print(f"❌ QCompleter.InlineCompletion failed: {e}")
            
        try:
            completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
            print("✅ QCompleter.UnfilteredPopupCompletion works")
        except Exception as e:
            print(f"❌ QCompleter.UnfilteredPopupCompletion failed: {e}")
            
    except Exception as e:
        print(f"❌ Failed to create QCompleter: {e}")
        
except ImportError as e:
    print(f"❌ Failed to import QCompleter from qt.core: {e}")
    
    # Try fallback
    try:
        from PyQt5.Qt import QCompleter
        print("✅ Fallback: Successfully imported QCompleter from PyQt5.Qt")
    except ImportError as e2:
        print(f"❌ Fallback also failed: {e2}")

print("\n=== Test Complete ===")