"""
Test delayed initialization - services created when DB becomes available
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch

# Mock calibre
import sys
sys.modules['calibre'] = Mock()
sys.modules['calibre.gui2'] = Mock()
sys.modules['calibre.customize'] = Mock()
sys.modules['calibre.customize.ui'] = Mock()

# Add path
project_path = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_path)


class TestDelayedInitialization:
    """Test that plugin handles delayed DB availability correctly"""
    
    def test_genesis_without_current_db_succeeds(self):
        """
        Test that genesis succeeds even when current_db is missing
        This simulates Calibre starting up
        """
        # GIVEN: GUI without current_db (like during startup)
        mock_gui = Mock()
        mock_gui.library_path = tempfile.mkdtemp()
        # Simulate missing current_db attribute
        del mock_gui.current_db
        
        with patch('calibre_plugins.semantic_search.interface.QMenu'):
            with patch('calibre_plugins.semantic_search.interface.QAction'):
                from calibre_plugins.semantic_search.interface import SemanticSearchInterface
                
                plugin = SemanticSearchInterface()
                plugin.gui = mock_gui
                plugin.qaction = Mock()
                
                # WHEN: genesis is called
                # Should not crash!
                plugin.genesis()
                
                # THEN: Basic initialization should succeed
                assert hasattr(plugin, 'config')
                # But services requiring DB should not exist
                assert not hasattr(plugin, 'indexing_service') or plugin.indexing_service is None
    
    def test_show_indexing_status_triggers_initialization(self):
        """
        Test that accessing indexing status triggers initialization
        when DB becomes available
        """
        # GIVEN: Plugin initialized without DB
        mock_gui = Mock()
        mock_gui.library_path = tempfile.mkdtemp()
        del mock_gui.current_db  # No DB initially
        
        with patch('calibre_plugins.semantic_search.interface.QMenu'):
            with patch('calibre_plugins.semantic_search.interface.QAction'):
                from calibre_plugins.semantic_search.interface import SemanticSearchInterface
                
                plugin = SemanticSearchInterface()
                plugin.gui = mock_gui
                plugin.qaction = Mock()
                plugin.genesis()
                
                # No indexing service yet
                assert not hasattr(plugin, 'indexing_service') or plugin.indexing_service is None
                
                # WHEN: DB becomes available and we check status
                mock_db = Mock()
                mock_db.new_api = Mock()
                mock_gui.current_db = mock_db
                
                # Mock info_dialog to capture output
                with patch('calibre_plugins.semantic_search.interface.info_dialog') as mock_dialog:
                    plugin.show_indexing_status()
                
                # THEN: Should have tried to initialize
                # Even if it fails, embedding_service should exist
                assert hasattr(plugin, 'embedding_service')
    
    def test_services_created_on_first_use(self):
        """
        Test that services are created on first use if not during genesis
        """
        # GIVEN: Plugin without services
        mock_gui = Mock()
        mock_gui.library_path = tempfile.mkdtemp()
        
        with patch('calibre_plugins.semantic_search.interface.QMenu'):
            with patch('calibre_plugins.semantic_search.interface.QAction'):
                from calibre_plugins.semantic_search.interface import SemanticSearchInterface
                
                plugin = SemanticSearchInterface()
                plugin.gui = mock_gui
                plugin.qaction = Mock()
                
                # Don't call genesis, simulate partial initialization
                plugin.config = Mock()
                plugin.config.as_dict.return_value = {"embedding_provider": "mock"}
                
                # WHEN: Get embedding service
                mock_db = Mock()
                mock_db.new_api = Mock()
                mock_gui.current_db = mock_db
                
                service = plugin.get_embedding_service()
                
                # THEN: Service should be created
                assert service is not None
                assert hasattr(plugin, 'embedding_service')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])