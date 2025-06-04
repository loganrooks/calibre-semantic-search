"""
Test interface.py indexing status integration using TDD

This test verifies that show_indexing_status() connects to real
indexing service instead of showing placeholder.
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os

# Mock calibre before importing anything
sys.modules['calibre'] = Mock()
sys.modules['calibre.gui2'] = Mock() 
sys.modules['calibre.customize'] = Mock()
sys.modules['calibre.customize.ui'] = Mock()

# Add path for modules
project_path = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_path)


class TestInterfaceIndexingStatus:
    """Test interface indexing status functionality"""
    
    def test_show_indexing_status_displays_real_data_not_placeholder(self):
        """
        Test that show_indexing_status shows real indexing data
        instead of placeholder message
        """
        # GIVEN: Mock GUI and interface with indexing service
        mock_gui = Mock()
        
        # Import and create interface
        from calibre_plugins.semantic_search.interface import SemanticSearchInterface
        plugin = SemanticSearchInterface()
        plugin.gui = mock_gui  # Set GUI reference manually
        
        # Mock indexing service with real status data
        mock_indexing_service = Mock()
        mock_indexing_service.get_indexing_status.return_value = {
            'total_books': 100,
            'indexed_books': 75,
            'in_progress': 2, 
            'errors': 1,
            'last_indexed': '2025-05-31 10:30:00'
        }
        
        # Connect indexing service to plugin
        plugin.indexing_service = mock_indexing_service
        
        # Mock info_dialog to capture what's displayed
        with patch('calibre_plugins.semantic_search.interface.info_dialog') as mock_dialog:
            
            # WHEN: Show indexing status
            plugin.show_indexing_status()
            
            # THEN: Should display real data, not placeholder
            mock_dialog.assert_called_once()
            call_args = mock_dialog.call_args
            
            # Should NOT contain placeholder text
            displayed_message = call_args[0][2]  # Third argument is the message
            assert "Indexing status will be available once the database is implemented" not in displayed_message
            
            # Should contain real status information
            assert "75" in displayed_message  # indexed_books count
            assert "100" in displayed_message  # total_books count
            assert "2" in displayed_message   # in_progress count
    
    def test_show_indexing_status_handles_no_indexing_service(self):
        """
        Test that show_indexing_status gracefully handles when
        indexing service is not initialized
        """
        # GIVEN: Interface without indexing service
        mock_gui = Mock()
        
        from calibre_plugins.semantic_search.interface import SemanticSearchInterface
        plugin = SemanticSearchInterface()
        plugin.gui = mock_gui  # Set GUI reference manually
        # Don't set plugin.indexing_service
        
        # Mock info_dialog
        with patch('calibre_plugins.semantic_search.interface.info_dialog') as mock_dialog:
            
            # WHEN: Show indexing status
            plugin.show_indexing_status()
            
            # THEN: Should show appropriate message about service not ready
            mock_dialog.assert_called_once()
            call_args = mock_dialog.call_args
            displayed_message = call_args[0][2]
            
            # Should indicate service is not ready, not generic placeholder
            assert "indexing service" in displayed_message.lower()
            assert "not initialized" in displayed_message.lower() or "not ready" in displayed_message.lower()
    
    def test_show_indexing_status_handles_service_error(self):
        """
        Test that show_indexing_status handles errors from indexing service
        """
        # GIVEN: Interface with failing indexing service
        mock_gui = Mock()
        
        from calibre_plugins.semantic_search.interface import SemanticSearchInterface
        plugin = SemanticSearchInterface()
        plugin.gui = mock_gui  # Set GUI reference manually
        
        # Mock indexing service that raises error
        mock_indexing_service = Mock()
        mock_indexing_service.get_indexing_status.side_effect = Exception("Database connection error")
        plugin.indexing_service = mock_indexing_service
        
        # Mock info_dialog
        with patch('calibre_plugins.semantic_search.interface.info_dialog') as mock_dialog:
            
            # WHEN: Show indexing status
            plugin.show_indexing_status()
            
            # THEN: Should handle error gracefully
            mock_dialog.assert_called_once()
            call_args = mock_dialog.call_args
            displayed_message = call_args[0][2]
            
            # Should show error information
            assert "error" in displayed_message.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])