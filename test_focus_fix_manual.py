#!/usr/bin/env python3
"""
Manual test to verify the focus-stealing fix works in practice
"""

import sys
import os
from PyQt5.Qt import QApplication, QWidget, QVBoxLayout, QLabel

# Add the plugin to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'calibre_plugins/semantic_search'))

try:
    from ui.dynamic_location_combo_box import DynamicLocationComboBox
    from core.location_fetcher import CloudRegion
except ImportError as e:
    print(f"Import error: {e}")
    print("Running fallback test...")

def test_focus_fix():
    """Test that the QCompleter approach works without focus stealing"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    
    # Create test window
    window = QWidget()
    layout = QVBoxLayout()
    
    # Add instructions
    instructions = QLabel("""
    Focus Fix Test - Type in the dropdown below:
    
    1. Click in the dropdown field
    2. Start typing (e.g., "us-c")
    3. Verify that:
       - Suggestions appear as you type
       - You can continue typing without interruption
       - No threading errors in console
       - Arrow keys work to navigate suggestions
    
    Expected behavior: Smooth typing with live suggestions!
    """)
    layout.addWidget(instructions)
    
    # Create combo box
    combo = DynamicLocationComboBox("vertex_ai", window)
    
    # Add some mock data to test with
    mock_regions = [
        type('Region', (), {
            'code': 'us-central1',
            'name': 'US Central 1',
            'location': 'Iowa',
            'popular': True,
            'status': 'available'
        }),
        type('Region', (), {
            'code': 'us-east1',
            'name': 'US East 1', 
            'location': 'South Carolina',
            'popular': True,
            'status': 'available'
        }),
        type('Region', (), {
            'code': 'europe-west1',
            'name': 'Europe West 1',
            'location': 'Belgium',
            'popular': False,
            'status': 'available'
        }),
    ]
    
    # Set the regions and update completer
    combo.all_regions = mock_regions
    if hasattr(combo, '_update_completer_data'):
        combo._update_completer_data()
    
    layout.addWidget(combo)
    
    window.setLayout(layout)
    window.setWindowTitle("Focus Stealing Fix Test")
    window.resize(500, 300)
    window.show()
    
    print("Test window opened. Try typing in the dropdown!")
    print("Watch console for any threading errors...")
    
    return app.exec_()

if __name__ == "__main__":
    sys.exit(test_focus_fix())