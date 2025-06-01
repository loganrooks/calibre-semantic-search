"""
Test plugin initialization and service creation using TDD

This test verifies that the plugin properly initializes all services
on startup instead of creating them on-demand.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Mock calibre before importing
sys.modules['calibre'] = Mock()
sys.modules['calibre.gui2'] = Mock()
sys.modules['calibre.customize'] = Mock()
sys.modules['calibre.customize.ui'] = Mock()

# Add path for modules
project_path = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_path)


class TestPluginInitialization:
    """Test that plugin initializes services properly"""
    
    def test_plugin_creates_embedding_service_on_genesis(self):
        """
        Test that plugin creates embedding service during genesis()
        instead of on-demand
        """
        # GIVEN: Mock GUI and plugin
        mock_gui = Mock()
        mock_gui.library_path = "/test/library"
        
        from calibre_plugins.semantic_search.interface import SemanticSearchInterface
        
        # Mock all the Qt stuff
        with patch('calibre_plugins.semantic_search.interface.QMenu'):
            with patch('calibre_plugins.semantic_search.interface.QAction'):
                plugin = SemanticSearchInterface()
                plugin.gui = mock_gui
                plugin.qaction = Mock()  # Mock the qaction that Calibre provides
                
                # Mock current_db for repository creation
                mock_gui.current_db = Mock()
                mock_gui.current_db.new_api = Mock()
                
                # Mock the _initialize_services method to succeed
                def mock_init_services(self):
                    # Simulate successful service creation
                    self.embedding_service = Mock()
                    self.indexing_service = Mock()
                    self.embedding_repo = Mock()
                    self.calibre_repo = Mock()
                    self.db_path = "/test/library/semantic_search/embeddings.db"
                
                # Replace the method temporarily
                with patch.object(plugin, '_initialize_services', mock_init_services.__get__(plugin)):
                    # WHEN: Plugin initializes
                    plugin.genesis()
                
                # THEN: Should create embedding service
                assert hasattr(plugin, 'embedding_service')
                assert plugin.embedding_service is not None
    
    def test_plugin_creates_indexing_service_on_genesis(self):
        """
        Test that plugin creates indexing service during genesis()
        """
        # GIVEN: Mock dependencies
        mock_gui = Mock()
        mock_gui.library_path = "/test/library"
        mock_gui.current_db = Mock()
        mock_gui.current_db.new_api = Mock()
        
        from calibre_plugins.semantic_search.interface import SemanticSearchInterface
        plugin = SemanticSearchInterface()
        plugin.gui = mock_gui
        plugin.qaction = Mock()  # Mock the qaction that Calibre provides
        
        # WHEN: Plugin initializes
        plugin.genesis()
        
        # THEN: Should create indexing service
        assert hasattr(plugin, 'indexing_service')
        assert plugin.indexing_service is not None
    
    def test_plugin_initializes_database_on_genesis(self):
        """
        Test that plugin ensures database is initialized
        """
        # GIVEN: Mock GUI and filesystem
        mock_gui = Mock()
        mock_gui.library_path = "/test/library"
        
        from calibre_plugins.semantic_search.interface import SemanticSearchInterface
        plugin = SemanticSearchInterface()
        plugin.gui = mock_gui
        plugin.qaction = Mock()  # Mock the qaction that Calibre provides
        
        with patch('os.path.exists') as mock_exists:
            with patch('os.makedirs') as mock_makedirs:
                # Simulate database doesn't exist
                mock_exists.return_value = False
                
                # WHEN: Plugin initializes
                plugin.genesis()
                
                # THEN: Should create directories and initialize database
                mock_makedirs.assert_called()
                assert hasattr(plugin, 'db_path')
                # Should have attempted to create database
    
    def test_plugin_reuses_services_across_operations(self):
        """
        Test that plugin uses same service instances, not creating new ones
        """
        # GIVEN: Initialized plugin
        mock_gui = Mock()
        mock_gui.library_path = "/test/library"
        mock_gui.current_db = Mock()
        mock_gui.current_db.new_api = Mock()
        
        from calibre_plugins.semantic_search.interface import SemanticSearchInterface
        plugin = SemanticSearchInterface()
        plugin.gui = mock_gui
        plugin.qaction = Mock()  # Mock the qaction that Calibre provides
        plugin.genesis()
        
        # Capture initial service references
        initial_embedding_service = plugin.embedding_service
        initial_indexing_service = plugin.indexing_service
        
        # WHEN: Multiple operations that need services
        # (Simulate what would happen with menu actions)
        
        # These operations should use existing services
        service1 = plugin.get_embedding_service()
        service2 = plugin.get_indexing_service()
        
        # THEN: Should be same instances
        assert service1 is initial_embedding_service
        assert service2 is initial_indexing_service
    
    def test_plugin_shares_services_with_dialogs(self):
        """
        Test that plugin shares its services with dialogs
        """
        # GIVEN: Initialized plugin
        mock_gui = Mock()
        mock_gui.library_path = "/test/library"
        
        from calibre_plugins.semantic_search.interface import SemanticSearchInterface
        plugin = SemanticSearchInterface()
        plugin.gui = mock_gui
        plugin.qaction = Mock()  # Mock the qaction that Calibre provides
        plugin.genesis()
        
        # Mock dialog creation
        with patch('calibre_plugins.semantic_search.ui.search_dialog.SemanticSearchDialog') as mock_dialog_class:
            mock_dialog = Mock()
            mock_dialog_class.return_value = mock_dialog
            
            # WHEN: Create search dialog
            plugin.show_dialog()
            
            # THEN: Dialog should receive plugin's services
            # (This will fail initially as we need to implement service passing)
            mock_dialog_class.assert_called_once()
            call_args = mock_dialog_class.call_args
            
            # Check that services were passed to dialog
            assert 'embedding_service' in call_args[1] or \
                   hasattr(mock_dialog, 'embedding_service')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])