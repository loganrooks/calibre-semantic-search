"""
Test REAL plugin initialization without mocks - fix actual problems with TDD
"""

import pytest
import tempfile
import os
from unittest.mock import Mock

# Add path for modules
import sys
project_path = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_path)


class TestRealPluginInitialization:
    """Test plugin initialization with minimal mocking - find and fix real issues"""
    
    def test_plugin_handles_missing_current_db_gracefully(self):
        """
        Test that plugin handles the case when current_db is not available during genesis
        
        The error we're seeing: 'Main' object has no attribute 'current_db'
        This happens because genesis() is called before the library is fully loaded
        """
        # GIVEN: A minimal mock GUI that simulates Calibre during startup
        mock_gui = Mock()
        mock_gui.library_path = tempfile.mkdtemp()  # Real temp directory
        # Simulate that current_db doesn't exist yet (like during startup)
        mock_gui.current_db = None
        
        # Only mock the absolute minimum - Qt stuff
        from unittest.mock import patch
        with patch('calibre_plugins.semantic_search.interface.QMenu'):
            with patch('calibre_plugins.semantic_search.interface.QAction'):
                # Import the real plugin
                from calibre_plugins.semantic_search.interface import SemanticSearchInterface
                
                plugin = SemanticSearchInterface()
                plugin.gui = mock_gui
                plugin.qaction = Mock()
                
                # WHEN: genesis is called (like Calibre does on startup)
                # This should NOT crash even without current_db
                plugin.genesis()
                
                # THEN: Plugin should initialize without error
                # Services might not be created yet, but that's OK
                assert hasattr(plugin, 'config')
                # Should not have services yet since db isn't ready
                assert not hasattr(plugin, 'embedding_service')
    
    def test_plugin_initializes_services_when_db_becomes_available(self):
        """
        Test that plugin can initialize services later when database becomes available
        """
        # GIVEN: Plugin initialized without database
        mock_gui = Mock()
        mock_gui.library_path = tempfile.mkdtemp()
        mock_gui.current_db = None  # Not available initially
        
        with patch('calibre_plugins.semantic_search.interface.QMenu'):
            with patch('calibre_plugins.semantic_search.interface.QAction'):
                from calibre_plugins.semantic_search.interface import SemanticSearchInterface
                
                plugin = SemanticSearchInterface()
                plugin.gui = mock_gui
                plugin.qaction = Mock()
                plugin.genesis()
                
                # Services should not be initialized
                assert not hasattr(plugin, 'embedding_service')
                
                # WHEN: Database becomes available (like after library loads)
                mock_db = Mock()
                mock_db.new_api = Mock()
                mock_gui.current_db = mock_db
                
                # Try to get embedding service - should trigger initialization
                service = plugin.get_embedding_service()
                
                # THEN: Service should be created
                assert service is not None
                assert hasattr(plugin, 'embedding_service')
    
    def test_plugin_reinitializes_on_library_change(self):
        """
        Test that plugin reinitializes services when library changes
        """
        # GIVEN: Plugin with initialized services
        mock_gui = Mock()
        mock_gui.library_path = tempfile.mkdtemp()
        mock_db = Mock()
        mock_db.new_api = Mock()
        mock_gui.current_db = mock_db
        
        with patch('calibre_plugins.semantic_search.interface.QMenu'):
            with patch('calibre_plugins.semantic_search.interface.QAction'):
                from calibre_plugins.semantic_search.interface import SemanticSearchInterface
                
                plugin = SemanticSearchInterface()
                plugin.gui = mock_gui
                plugin.qaction = Mock()
                plugin.genesis()
                
                # Force service initialization
                first_service = plugin.get_embedding_service()
                first_db_path = plugin.db_path if hasattr(plugin, 'db_path') else None
                
                # WHEN: Library changes
                new_library_path = tempfile.mkdtemp()
                mock_gui.library_path = new_library_path
                plugin.library_changed(mock_db)
                
                # THEN: Services should be reinitialized
                second_service = plugin.get_embedding_service()
                second_db_path = plugin.db_path if hasattr(plugin, 'db_path') else None
                
                # Database path should change
                assert first_db_path != second_db_path
                assert new_library_path in second_db_path


class TestActualServiceCreation:
    """Test that services are actually created correctly"""
    
    def test_embedding_service_is_created_with_mock_provider(self):
        """
        Test that embedding service is created with mock provider by default
        """
        # GIVEN: Config that should create mock provider
        from calibre_plugins.semantic_search.config import SemanticSearchConfig
        from calibre_plugins.semantic_search.core.embedding_service import create_embedding_service
        
        config = SemanticSearchConfig()
        config_dict = config.as_dict()
        
        # WHEN: Create embedding service
        service = create_embedding_service(config_dict)
        
        # THEN: Service should be created with mock provider
        assert service is not None
        # Test that it can actually generate embeddings
        embedding = service.embed_text("test")
        assert embedding is not None
        assert len(embedding) > 0


if __name__ == "__main__":
    # Import Qt mocking at module level
    from unittest.mock import Mock, patch
    sys.modules['calibre'] = Mock()
    sys.modules['calibre.gui2'] = Mock()
    sys.modules['calibre.customize'] = Mock()
    sys.modules['calibre.customize.ui'] = Mock()
    
    pytest.main([__file__, "-v"])