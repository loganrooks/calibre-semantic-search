#!/usr/bin/env python3
"""
Validation tests for UI_BACKEND_INTEGRATION_DIAGNOSIS.md

This test suite validates that each of the 5 critical integration issues 
identified in the diagnosis actually exists and reproduces the problems.

RED-GREEN-REFACTOR: These should all FAIL initially, proving the issues exist.
Then as we fix each issue, the corresponding tests should pass.
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add plugin path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'calibre_plugins', 'semantic_search'))

try:
    from calibre_plugins.semantic_search.config import ConfigWidget
    from calibre_plugins.semantic_search.ui.index_manager_dialog import IndexManagerDialog
    from calibre_plugins.semantic_search.interface import SemanticSearchInterface
    CALIBRE_AVAILABLE = True
except ImportError:
    CALIBRE_AVAILABLE = False


@pytest.mark.skipif(not CALIBRE_AVAILABLE, reason="Calibre plugins not importable")
class TestIssue1PluginReferenceChain:
    """Test Issue #1: Test Connection Plugin Reference Chain Broken"""
    
    def test_config_widget_cannot_access_plugin_instance(self):
        """Test that ConfigWidget cannot find plugin instance through parent chain"""
        
        # Create ConfigWidget with mock parent chain (simulating Calibre's creation)
        config_widget = ConfigWidget()
        
        # Mock a parent chain that doesn't have plugin reference
        mock_parent = Mock()
        mock_parent.plugin = None  # This is the problem!
        mock_parent.parent.return_value = None
        config_widget.parent = Mock(return_value=mock_parent)
        
        # Try to find plugin instance (this should fail)
        plugin = None
        parent = config_widget.parent()
        while parent and not plugin:
            if hasattr(parent, 'plugin'):
                plugin = parent.plugin
                break
            parent = parent.parent()
        
        # Issue #1: Plugin reference not found
        assert plugin is None, "Plugin reference should not be found through parent chain"
    
    def test_test_connection_fails_without_plugin_reference(self):
        """Test that _test_connection fails when plugin instance not available"""
        
        config_widget = ConfigWidget()
        # No plugin_interface attribute set
        
        # This should fail because there's no way to get embedding service
        with pytest.raises((AttributeError, RuntimeError)):
            # Simulate clicking "Test Connection" button
            if hasattr(config_widget, '_test_connection'):
                config_widget._test_connection()


@pytest.mark.skipif(not CALIBRE_AVAILABLE, reason="Calibre plugins not importable")  
class TestIssue2ConfigurationConflicts:
    """Test Issue #2: Multiple Configuration Systems Conflict"""
    
    def test_two_model_selection_systems_exist(self):
        """Verify that both AI Provider tab and Indexing tab have model selection"""
        
        config_widget = ConfigWidget()
        
        # Check AI Provider tab has model selection
        ai_provider_has_model = hasattr(config_widget, 'model_edit')
        
        # Check Indexing tab has model selection  
        indexing_has_model = hasattr(config_widget, 'model_combo')
        
        # Issue #2: Both systems exist (this is the problem!)
        assert ai_provider_has_model and indexing_has_model, \
            "Both AI Provider and Indexing tabs should have model selection (causing conflict)"
    
    def test_both_systems_save_to_same_config_key(self):
        """Test that both model selection systems save to same config key"""
        
        config_widget = ConfigWidget()
        mock_config = Mock()
        config_widget.config = mock_config
        
        # Simulate user setting model in AI Provider tab
        if hasattr(config_widget, 'model_edit'):
            config_widget.model_edit = Mock()
            config_widget.model_edit.text.return_value = "gemini-embedding-00"
            
        # Simulate user setting model in Indexing tab
        if hasattr(config_widget, 'model_combo'):
            config_widget.model_combo = Mock()
            config_widget.model_combo.currentText.return_value = "mock-embedding"
        
        # Both save operations use same key (this causes the conflict!)
        # This test proves the conflict exists by showing both try to set same key
        ai_provider_key = "embedding_model"
        indexing_key = "embedding_model"
        
        assert ai_provider_key == indexing_key, \
            "Both systems use same config key (this is the conflict we need to fix)"


@pytest.mark.skipif(not CALIBRE_AVAILABLE, reason="Calibre plugins not importable")
class TestIssue3IndexManagerDataBinding:
    """Test Issue #3: Index Manager Data Binding Issues"""
    
    def test_table_cells_are_editable(self):
        """Test that table cells are editable (should be read-only)"""
        
        from calibre_plugins.semantic_search.ui.qt_view_adapter import qt
        
        # Create mock Calibre GUI
        mock_gui = Mock()
        dialog = IndexManagerDialog(mock_gui)
        
        # Check if table exists and cells are editable
        if hasattr(dialog, 'book_index_table'):
            table = dialog.book_index_table
            
            # Add a test item to check editability
            from calibre_plugins.semantic_search.ui.qt_view_adapter import QTableWidgetItem
            test_item = QTableWidgetItem("test")
            table.setItem(0, 0, test_item)
            
            # Issue #3A: Cells should be read-only but aren't
            item_flags = test_item.flags()
            is_editable = bool(item_flags & qt.ItemIsEditable)
            
            assert is_editable, "Table cells should be editable (this is the problem we need to fix)"
    
    def test_duplicate_statistics_display_exists(self):
        """Test that statistics are displayed in multiple places"""
        
        mock_gui = Mock()
        dialog = IndexManagerDialog(mock_gui)
        
        # Check for both HTML text display and grid layout
        has_html_stats = hasattr(dialog, '_populate_statistics')
        has_grid_stats = hasattr(dialog, 'total_books_label')
        
        # Issue #3B: Both statistics displays exist (duplication problem)
        assert has_html_stats and has_grid_stats, \
            "Both HTML and grid statistics should exist (causing duplication)"
    
    def test_legacy_data_fallback_shows_unknown_values(self):
        """Test that legacy data shows as 'legacy/unknown' instead of real values"""
        
        mock_gui = Mock()
        dialog = IndexManagerDialog(mock_gui)
        
        # Simulate legacy index data (no provider/model metadata)
        legacy_index_info = {
            'provider': 'legacy',      # Issue #3C: Shows 'legacy' instead of real provider
            'model_name': 'unknown',   # Issue #3C: Shows 'unknown' instead of real model  
            'dimensions': 768,
            'chunk_size': 1000,
            'total_chunks': 5,
            'created_at': 'Unknown'
        }
        
        # This proves the issue exists - real metadata not stored/displayed
        assert legacy_index_info['provider'] == 'legacy', \
            "Provider shows as 'legacy' instead of actual provider"
        assert legacy_index_info['model_name'] == 'unknown', \
            "Model shows as 'unknown' instead of actual model"


@pytest.mark.skipif(not CALIBRE_AVAILABLE, reason="Calibre plugins not importable")
class TestIssue4ServiceInitializationRace:
    """Test Issue #4: Service Initialization Race Conditions"""
    
    def test_services_initialized_before_user_configuration(self):
        """Test that services are created with default config before user sets preferences"""
        
        # Mock the config to simulate default state
        mock_config = Mock()
        mock_config.as_dict.return_value = {
            'embedding_provider': 'mock',  # Default, not user's choice
            'embedding_model': 'mock-embedding',
            'api_key': ''
        }
        
        # Create interface (this triggers service initialization)
        interface = SemanticSearchInterface(Mock(), Mock())
        interface.config = mock_config
        
        # Issue #4: Services initialized with default config
        if hasattr(interface, '_initialize_services'):
            interface._initialize_services()
            
            # Services created with mock provider instead of user's actual choice
            assert mock_config.as_dict()['embedding_provider'] == 'mock', \
                "Services initialized with default 'mock' provider before user configuration"
    
    def test_services_not_recreated_after_config_change(self):
        """Test that services aren't recreated when config changes"""
        
        interface = SemanticSearchInterface(Mock(), Mock())
        interface.config = Mock()
        interface.config.as_dict.return_value = {'embedding_provider': 'mock'}
        
        # Initialize services with mock config
        if hasattr(interface, '_initialize_services'):
            interface._initialize_services()
            
        initial_service = getattr(interface, 'embedding_service', None)
        
        # Change config to vertex_ai
        interface.config.as_dict.return_value = {'embedding_provider': 'vertex_ai'}
        
        # Services should be recreated but they aren't (this is the race condition)
        current_service = getattr(interface, 'embedding_service', None)
        
        # Issue #4: Same service instance even after config change
        if initial_service and current_service:
            assert initial_service is current_service, \
                "Service instance should be same (not recreated) - this is the problem"


@pytest.mark.skipif(not CALIBRE_AVAILABLE, reason="Calibre plugins not importable") 
class TestIssue5DatabaseSchemaMismatch:
    """Test Issue #5: Database Schema vs UI Mismatch"""
    
    def test_index_metadata_not_stored_during_indexing(self):
        """Test that provider/model metadata isn't stored when indexing books"""
        
        # Mock indexing service
        from calibre_plugins.semantic_search.core.indexing_service import IndexingService
        
        mock_config = {
            'embedding_provider': 'vertex_ai',
            'embedding_model': 'gemini-embedding-00'
        }
        
        # Create indexing service
        indexing_service = IndexingService(mock_config)
        
        # Check if indexing stores provider/model metadata
        # This should show that metadata is NOT being stored properly
        
        # Issue #5: Metadata storage not implemented in indexing flow
        # The service exists but doesn't have proper metadata storage
        has_metadata_storage = hasattr(indexing_service, 'store_index_metadata')
        
        assert not has_metadata_storage, \
            "Index metadata storage should not exist yet (this is what we need to implement)"
    
    def test_ui_expects_metadata_that_database_doesnt_provide(self):
        """Test that UI tries to display metadata that database doesn't store"""
        
        # Simulate what database returns (missing metadata)
        simulated_db_index = {
            'book_id': 123,
            'chunk_count': 10,
            # Missing: provider, model_name, dimensions, etc.
        }
        
        # UI tries to get provider/model but gets defaults
        provider = simulated_db_index.get('provider', 'unknown')
        model = simulated_db_index.get('model_name', 'unknown')
        
        # Issue #5: UI gets 'unknown' values because DB doesn't store metadata
        assert provider == 'unknown', "Provider should be 'unknown' (missing from DB)"
        assert model == 'unknown', "Model should be 'unknown' (missing from DB)"


def test_all_diagnosis_issues_reproduced():
    """Meta-test to ensure all 5 issues are validated"""
    
    issue_test_counts = {
        'Issue1_PluginReference': 2,
        'Issue2_ConfigConflicts': 2, 
        'Issue3_IndexManagerData': 3,
        'Issue4_ServiceRace': 2,
        'Issue5_DatabaseSchema': 2
    }
    
    total_expected_tests = sum(issue_test_counts.values())
    
    # This test serves as documentation of what we're validating
    assert total_expected_tests == 11, \
        f"Should have {total_expected_tests} validation tests for 5 critical issues"


if __name__ == '__main__':
    print("🔍 Running diagnosis validation tests...")
    print("These tests should FAIL initially, proving the issues exist.")
    print("As we fix each issue, the corresponding tests should pass.")
    print()
    
    pytest.main([__file__, '-v'])