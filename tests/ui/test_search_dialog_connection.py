"""
Tests for connecting actual search dialog to presenter using TDD

These tests verify that the Qt search dialog properly uses our
presenter pattern for search operations.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add path for our modules
module_path = os.path.join(os.path.dirname(__file__), '..', '..', 'calibre_plugins', 'semantic_search', 'ui')
sys.path.insert(0, module_path)


class TestSearchDialogConnection:
    """Test connection of search dialog to presenter"""
    
    def test_connector_initializes_presenter_correctly(self):
        """Test that connector initializes presenter with proper dependencies"""
        # GIVEN: Mock dependencies
        mock_gui = Mock()
        mock_gui.library_path = "/test/library"
        mock_gui.current_db = Mock()
        mock_gui.current_db.new_api = Mock()
        
        mock_plugin = Mock()
        mock_config = Mock()
        mock_config.as_dict.return_value = {"api_key": "test"}
        
        from search_dialog_connector import SearchDialogConnector
        connector = SearchDialogConnector(mock_gui, mock_plugin, mock_config)
        
        # Mock all the classes that get imported
        with patch.object(connector, 'initialize_presenter') as mock_init:
            # WHEN: Initialize presenter
            connector.initialize_presenter()
            
            # THEN: Should call initialization
            mock_init.assert_called_once()
    
    def test_connector_builds_search_options_correctly(self):
        """Test that connector builds search options from UI state"""
        # GIVEN: Connector with mock dependencies
        mock_gui = Mock()
        mock_plugin = Mock()
        mock_config = Mock()
        
        from search_dialog_connector import SearchDialogConnector
        connector = SearchDialogConnector(mock_gui, mock_plugin, mock_config)
        
        # WHEN: Build search options from UI state
        ui_state = {
            'mode_index': 1,  # Dialectical
            'scope_index': 0,  # Library
            'threshold': 75,
            'limit': 25,
            'include_context': False
        }
        
        options = connector.build_search_options(ui_state)
        
        # THEN: Should create options with correct values
        assert options.mode == "dialectical"
        assert options.scope == "library"
        assert options.similarity_threshold == 0.75
        assert options.limit == 25
        assert options.include_context == False
    
    def test_connector_performs_search_via_presenter(self):
        """Test that connector delegates search to presenter"""
        # GIVEN: Connector with mock presenter
        mock_gui = Mock()
        mock_plugin = Mock()
        mock_config = Mock()
        
        from search_dialog_connector import SearchDialogConnector
        connector = SearchDialogConnector(mock_gui, mock_plugin, mock_config)
        
        # Mock presenter
        mock_presenter = Mock()
        connector.presenter = mock_presenter
        
        # WHEN: Perform search
        query = "test query"
        ui_state = {
            'mode_index': 0,
            'scope_index': 0,
            'threshold': 70,
            'limit': 20,
            'include_context': True
        }
        
        connector.perform_search(query, ui_state)
        
        # THEN: Should delegate to presenter
        mock_presenter.perform_search.assert_called_once()
        call_args = mock_presenter.perform_search.call_args
        assert call_args[0][0] == "test query"
        
        options = call_args[0][1]
        assert options.mode == "semantic"
        assert options.scope == "library"
        assert options.similarity_threshold == 0.7


if __name__ == "__main__":
    pytest.main([__file__, "-v"])