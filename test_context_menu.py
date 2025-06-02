#!/usr/bin/env python3
"""
Test script to verify context menu integration approaches in Calibre
"""

import sys
from calibre.customize import InterfaceActionBase
from calibre.gui2.actions import InterfaceAction

# Print information about InterfaceAction's context menu support
print("InterfaceAction attributes related to context menus:")
print("-" * 50)

# Check for context menu related attributes
attrs = ['action_type', 'dont_add_to', 'action_spec', 'popup_type', 'accepts_drops']
for attr in attrs:
    if hasattr(InterfaceAction, attr):
        print(f"{attr}: present")
    else:
        print(f"{attr}: NOT FOUND")

print("\nChecking InterfaceAction methods:")
print("-" * 50)

# Check for methods
methods = ['location_selected', 'genesis', 'initialization_complete', 
           'library_changed', 'shutting_down', 'create_menu_action']
for method in methods:
    if hasattr(InterfaceAction, method):
        print(f"{method}: present")
    else:
        print(f"{method}: NOT FOUND")

# Check the dont_add_to default values
print("\nKnown dont_add_to values:")
print("-" * 50)
common_values = [
    'context-menu',
    'context-menu-device',
    'toolbar-child',
    'toolbar',
    'menubar',
    'menubar-device',
]
print("Common exclusion values:", common_values)

print("\nContext Menu Integration Summary:")
print("-" * 50)
print("1. Set dont_add_to = frozenset() to appear in all menus")
print("2. Set action_type = 'current' to work with selected books")
print("3. The plugin menu will automatically appear in context menu")
print("4. Use location_selected() to enable/disable actions based on selection")
print("5. No need to manually add to library view context menu")