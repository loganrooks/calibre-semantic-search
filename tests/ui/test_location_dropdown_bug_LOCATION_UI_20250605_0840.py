#!/usr/bin/env python3
"""
BUG TEST: LOCATION-UI-20250605-0840

BUG: Location selector in settings UI is not using the dynamic dropdown.
     Still showing manual typing (QLineEdit) instead of DynamicLocationComboBox.

This test should FAIL until the bug is fixed.
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch
from PyQt5.Qt import QApplication, QComboBox, QLineEdit

# Add plugin path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'calibre_plugins', 'semantic_search'))

# Ensure QApplication exists for widget tests
if not QApplication.instance():
    app = QApplication([])

class TestLocationDropdownBug:
    """BUG TEST: Location dropdown not working in config UI"""
    
    def test_dynamic_location_combo_box_import_succeeds(self):
        """
        BUG TEST: DynamicLocationComboBox should be importable without errors
        This test verifies the import chain works correctly.
        """
        try:
            from calibre_plugins.semantic_search.ui.dynamic_location_combo_box import DynamicLocationComboBox
            assert DynamicLocationComboBox is not None, "DynamicLocationComboBox should not be None"
            assert hasattr(DynamicLocationComboBox, '__init__'), "DynamicLocationComboBox should be a proper class"
            print("✅ DynamicLocationComboBox import test passed")
        except ImportError as e:
            pytest.fail(f"BUG CONFIRMED: DynamicLocationComboBox import failed: {e}")
    
    def test_location_data_fetcher_import_succeeds(self):
        """
        BUG TEST: LocationDataFetcher dependency should be importable
        """
        try:
            from calibre_plugins.semantic_search.core.location_fetcher import LocationDataFetcher, CloudRegion
            assert LocationDataFetcher is not None, "LocationDataFetcher should not be None"
            assert CloudRegion is not None, "CloudRegion should not be None"
            print("✅ LocationDataFetcher import test passed")
        except ImportError as e:
            pytest.fail(f"BUG CONFIRMED: LocationDataFetcher import failed: {e}")
    
    def test_config_location_combo_box_is_not_none(self):
        """
        BUG TEST: Config module should successfully import LocationComboBox (not None)
        This is the core bug - config.LocationComboBox is None due to import failures.
        """
        try:
            from calibre_plugins.semantic_search.config import LocationComboBox
            
            if LocationComboBox is None:
                pytest.fail("BUG CONFIRMED: LocationComboBox is None in config module - import chain failed!")
            
            # Check it's the right class
            assert hasattr(LocationComboBox, '__init__'), "LocationComboBox should be a proper class"
            assert hasattr(LocationComboBox, 'get_region_code'), "LocationComboBox should have get_region_code method"
            
            print(f"✅ Config LocationComboBox is properly imported: {LocationComboBox}")
            
        except ImportError as e:
            pytest.fail(f"BUG CONFIRMED: Config LocationComboBox import failed: {e}")
    
    def test_config_widget_uses_location_combo_box_not_line_edit(self):
        """
        BUG TEST: ConfigWidget should create LocationComboBox widgets, not QLineEdit fallbacks
        This test verifies the UI actually uses the dropdown.
        """
        try:
            from calibre_plugins.semantic_search.config import ConfigWidget, LocationComboBox
            
            if LocationComboBox is None:
                pytest.fail("BUG CONFIRMED: Cannot test UI because LocationComboBox is None")
            
            # Create config widget
            config_widget = ConfigWidget()
            
            # Check for vertex_location_combo (should exist if LocationComboBox works)
            assert hasattr(config_widget, 'vertex_location_combo'), \
                "BUG CONFIRMED: ConfigWidget should have vertex_location_combo attribute"
            
            # Verify it's actually a LocationComboBox, not a QLineEdit
            vertex_location_widget = config_widget.vertex_location_combo
            assert not isinstance(vertex_location_widget, QLineEdit), \
                "BUG CONFIRMED: vertex_location_combo is QLineEdit fallback, should be LocationComboBox"
            
            assert isinstance(vertex_location_widget, QComboBox), \
                "BUG CONFIRMED: vertex_location_combo should be a QComboBox (LocationComboBox inherits from it)"
            
            # Check for direct_vertex_location_combo too
            assert hasattr(config_widget, 'direct_vertex_location_combo'), \
                "BUG CONFIRMED: ConfigWidget should have direct_vertex_location_combo attribute"
            
            direct_vertex_location_widget = config_widget.direct_vertex_location_combo
            assert not isinstance(direct_vertex_location_widget, QLineEdit), \
                "BUG CONFIRMED: direct_vertex_location_combo is QLineEdit fallback, should be LocationComboBox"
            
            print("✅ ConfigWidget correctly uses LocationComboBox widgets")
            
        except Exception as e:
            pytest.fail(f"BUG CONFIRMED: ConfigWidget UI test failed: {e}")
    
    def test_location_combo_box_can_be_instantiated(self):
        """
        BUG TEST: LocationComboBox should be instantiable and functional
        """
        try:
            from calibre_plugins.semantic_search.config import LocationComboBox
            
            if LocationComboBox is None:
                pytest.fail("BUG CONFIRMED: Cannot instantiate because LocationComboBox is None")
            
            # Try to create instance
            combo = LocationComboBox("vertex_ai")
            assert combo is not None, "LocationComboBox instance should not be None"
            assert combo.provider_type == "vertex_ai", "Provider type should be set correctly"
            
            # Test basic functionality
            assert hasattr(combo, 'get_region_code'), "Should have get_region_code method"
            assert hasattr(combo, 'set_region_code'), "Should have set_region_code method"
            
            # Test that it's editable (key requirement)
            assert combo.isEditable(), "BUG CONFIRMED: LocationComboBox should be editable for typing"
            
            print("✅ LocationComboBox instantiation and basic functionality test passed")
            
        except Exception as e:
            pytest.fail(f"BUG CONFIRMED: LocationComboBox instantiation failed: {e}")
    
    def test_location_combo_box_has_dynamic_features(self):
        """
        BUG TEST: LocationComboBox should have dynamic features (loading, filtering, etc.)
        """
        try:
            from calibre_plugins.semantic_search.config import LocationComboBox
            
            if LocationComboBox is None:
                pytest.fail("BUG CONFIRMED: Cannot test dynamic features because LocationComboBox is None")
            
            combo = LocationComboBox("vertex_ai")
            
            # Check for dynamic features that should be present
            assert hasattr(combo, 'fetcher'), "Should have fetcher attribute for dynamic loading"
            assert hasattr(combo, 'loading_indicator'), "Should have loading_indicator for visual feedback"
            assert hasattr(combo, 'all_regions'), "Should have all_regions list"
            assert hasattr(combo, 'filtered_regions'), "Should have filtered_regions list"
            
            # Check for context menu functionality
            assert hasattr(combo, '_show_context_menu'), "Should have context menu functionality"
            assert hasattr(combo, '_refresh_regions'), "Should have refresh functionality"
            
            print("✅ LocationComboBox dynamic features test passed")
            
        except Exception as e:
            pytest.fail(f"BUG CONFIRMED: LocationComboBox dynamic features test failed: {e}")

if __name__ == '__main__':
    print("🔴 BUG TEST: LOCATION-UI-20250605-0840")
    print("=" * 60)
    print("Testing location dropdown bug - these tests should FAIL until bug is fixed")
    print()
    
    pytest.main([__file__, '-v', '-s'])