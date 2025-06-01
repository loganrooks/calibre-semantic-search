"""
Test the Test Connection functionality using TDD
"""

import pytest
import os
from unittest.mock import Mock, patch, AsyncMock
import sys

# Mock calibre
sys.modules['calibre'] = Mock()
sys.modules['calibre.gui2'] = Mock()

# Add path
project_path = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_path)


class TestConnectionTesting:
    """Test that Test Connection actually tests the embedding service"""
    
    def test_test_connection_button_calls_embedding_service(self):
        """
        Test that clicking Test Connection actually tests the service
        instead of showing a placeholder
        """
        # GIVEN: Configuration dialog with mock embedding service
        from calibre_plugins.semantic_search.config import ConfigWidget
        
        # Create minimal parent
        parent = Mock()
        parent.plugin = Mock()
        parent.plugin.get_embedding_service = Mock()
        
        # Mock embedding service with test method
        mock_service = Mock()
        mock_service.test_connection = AsyncMock(return_value={
            'status': 'success',
            'provider': 'mock',
            'message': 'Connection successful'
        })
        parent.plugin.get_embedding_service.return_value = mock_service
        
        # Create config widget
        widget = ConfigWidget(parent)
        
        # Mock QMessageBox to capture output
        with patch('calibre_plugins.semantic_search.config.QMessageBox') as mock_msgbox:
            # WHEN: Test connection is clicked
            widget._test_connection()
            
            # THEN: Should call the embedding service test
            mock_service.test_connection.assert_called_once()
            
            # Should show result in message box
            mock_msgbox.information.assert_called_once()
            args = mock_msgbox.information.call_args[0]
            assert "Connection successful" in args[2]
            assert "mock" in args[2]
    
    def test_test_connection_handles_service_error(self):
        """
        Test that connection errors are displayed properly
        """
        # GIVEN: Service that returns error
        from calibre_plugins.semantic_search.config import ConfigWidget
        
        parent = Mock()
        parent.plugin = Mock()
        parent.plugin.get_embedding_service = Mock()
        
        mock_service = Mock()
        mock_service.test_connection = AsyncMock(return_value={
            'status': 'error',
            'provider': 'openai',
            'message': 'Invalid API key'
        })
        parent.plugin.get_embedding_service.return_value = mock_service
        
        widget = ConfigWidget(parent)
        
        with patch('calibre_plugins.semantic_search.config.QMessageBox') as mock_msgbox:
            # WHEN: Test connection with error
            widget._test_connection()
            
            # THEN: Should show error message
            mock_msgbox.critical.assert_called_once()
            args = mock_msgbox.critical.call_args[0]
            assert "Invalid API key" in args[2]
    
    def test_test_connection_handles_no_service(self):
        """
        Test graceful handling when no service is available
        """
        # GIVEN: No embedding service
        from calibre_plugins.semantic_search.config import ConfigWidget
        
        parent = Mock()
        parent.plugin = Mock()
        parent.plugin.get_embedding_service = Mock(return_value=None)
        
        widget = ConfigWidget(parent)
        
        with patch('calibre_plugins.semantic_search.config.QMessageBox') as mock_msgbox:
            # WHEN: Test connection without service
            widget._test_connection()
            
            # THEN: Should show appropriate error
            mock_msgbox.critical.assert_called_once()
            args = mock_msgbox.critical.call_args[0]
            assert "service" in args[2].lower()


class TestIndexingSettings:
    """Test that indexing settings are available in config"""
    
    def test_config_has_indexing_tab(self):
        """
        Test that configuration dialog has indexing settings tab
        """
        # GIVEN: Configuration widget
        from calibre_plugins.semantic_search.config import ConfigWidget
        
        parent = Mock()
        parent.plugin = Mock()
        
        widget = ConfigWidget(parent)
        
        # THEN: Should have indexing tab
        # Check tab widget for indexing tab
        tab_widget = widget.tab_widget
        
        # Find indexing tab
        indexing_tab_found = False
        for i in range(tab_widget.count()):
            if "index" in tab_widget.tabText(i).lower():
                indexing_tab_found = True
                break
        
        assert indexing_tab_found, "No indexing tab found in configuration"
    
    def test_indexing_settings_include_batch_size(self):
        """
        Test that indexing settings include batch processing options
        """
        # GIVEN: Configuration widget
        from calibre_plugins.semantic_search.config import ConfigWidget
        
        parent = Mock()
        parent.plugin = Mock()
        
        widget = ConfigWidget(parent)
        
        # THEN: Should have batch size setting
        assert hasattr(widget, 'batch_size_spin') or \
               any('batch' in str(w) for w in widget.findChildren(Mock))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])