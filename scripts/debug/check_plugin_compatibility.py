#!/usr/bin/env python3
"""
Check plugin compatibility without Calibre environment
"""

import ast
import os

def analyze_plugin_file():
    """Analyze the plugin UI file for compatibility issues"""
    
    plugin_file = 'calibre_plugins/semantic_search/ui.py'
    
    print(f"Analyzing {plugin_file}...\n")
    
    with open(plugin_file, 'r') as f:
        content = f.read()
        
    # Check imports
    print("=== Import Analysis ===")
    if 'from qt.core import' in content:
        print("✅ Using qt.core imports (correct for modern Calibre)")
    elif 'from PyQt5' in content:
        print("⚠️  Using PyQt5 imports (may need compatibility handling)")
        
    # Check popup_type
    print("\n=== popup_type Analysis ===")
    if 'QToolButton.ToolButtonPopupMode.MenuButtonPopup' in content:
        print("✅ Using correct popup_type enum")
    elif 'Qt.ToolButtonTextBesideIcon' in content:
        print("❌ Using incorrect Qt enum for popup_type")
        
    # Check action_spec
    print("\n=== action_spec Analysis ===") 
    if 'action_spec' in content:
        # Extract action_spec using regex or string search
        import re
        match = re.search(r'action_spec\s*=\s*\((.*?)\)', content, re.DOTALL)
        if match:
            spec = match.group(1)
            parts = spec.count(',') + 1
            print(f"✅ action_spec found with {parts} parts")
            if 'None' in spec:
                print("⚠️  Using None for icon - plugin won't have an icon")
                
    # Check for get_icons usage
    print("\n=== Icon Loading Analysis ===")
    if 'QIcon.ic(' in content:
        print("✅ Using QIcon.ic() for icon loading")
    elif 'get_icons(' in content:
        print("⚠️  Using get_icons() - may need proper import")
        
    # Summary
    print("\n=== Recommendations ===")
    print("1. For the icon issue:")
    print("   - Add a search.png to resources/icons/")
    print("   - Update action_spec to use 'search.png' instead of None")
    print("   - Or use a Calibre built-in icon like 'search.png'")
    print("\n2. For better debugging:")
    print("   - Use calibre-debug -g to see console output")
    print("   - Add print statements in genesis() method")
    print("   - Check ~/.config/calibre/plugins/ for error logs")

if __name__ == "__main__":
    analyze_plugin_file()