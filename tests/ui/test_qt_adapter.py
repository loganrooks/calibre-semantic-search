"""
Tests for Qt view adapter that connects dialog to presenter
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add path for our modules
module_path = os.path.join(os.path.dirname(__file__), '..', '..', 'calibre_plugins', 'semantic_search', 'ui')
sys.path.insert(0, module_path)


class TestQtViewAdapter:
    """Test the adapter that connects Qt dialog to presenter interface"""
    
    def test_adapter_shows_validation_error(self):
        """Test adapter shows validation error in Qt dialog"""
        # GIVEN: Mock Qt dialog
        mock_dialog = Mock()
        mock_dialog.QMessageBox = Mock()
        
        # Create adapter (will fail initially - no adapter exists!)
        from qt_view_adapter import QtViewAdapter
        adapter = QtViewAdapter(mock_dialog)
        
        # WHEN: Show validation error
        adapter.show_validation_error("Query too short")
        
        # THEN: Should show Qt message box
        mock_dialog.show_warning.assert_called_once_with(
            "Invalid Query", "Query too short"
        )
    
    def test_adapter_displays_results(self):
        """Test adapter displays results in Qt list widget"""
        # GIVEN: Mock dialog with results list
        mock_dialog = Mock()
        mock_dialog.results_list = Mock()
        mock_dialog.current_results = []
        
        from qt_view_adapter import QtViewAdapter
        adapter = QtViewAdapter(mock_dialog)
        
        # Mock results
        results = [
            Mock(book_id=1, book_title="Book 1"),
            Mock(book_id=2, book_title="Book 2")
        ]
        
        # WHEN: Display results
        adapter.display_results(results)
        
        # THEN: Should clear list and add results
        mock_dialog.results_list.clear.assert_called_once()
        assert mock_dialog.current_results == results
        assert mock_dialog._display_results.called_with(results)
    
    def test_adapter_shows_search_progress(self):
        """Test adapter shows progress bar during search"""
        # GIVEN: Mock dialog with progress bar
        mock_dialog = Mock()
        mock_dialog.progress_bar = Mock()
        mock_dialog.status_bar = Mock()
        mock_dialog.search_button = Mock()
        
        from qt_view_adapter import QtViewAdapter
        adapter = QtViewAdapter(mock_dialog)
        
        # WHEN: Show search progress
        adapter.show_search_progress()
        
        # THEN: Should show progress and disable button
        mock_dialog.progress_bar.show.assert_called_once()
        mock_dialog.progress_bar.setRange.assert_called_once_with(0, 0)
        mock_dialog.status_bar.setText.assert_called_once_with("Searching...")
        mock_dialog.search_button.setEnabled.assert_called_once_with(False)
    
    def test_adapter_shows_search_error(self):
        """Test adapter shows search error dialog"""
        # GIVEN: Mock dialog
        mock_dialog = Mock()
        mock_dialog.progress_bar = Mock()
        mock_dialog.search_button = Mock()
        mock_dialog.status_bar = Mock()
        
        from qt_view_adapter import QtViewAdapter
        adapter = QtViewAdapter(mock_dialog)
        
        # WHEN: Show search error
        adapter.show_search_error("Connection failed")
        
        # THEN: Should hide progress and show error
        mock_dialog.progress_bar.hide.assert_called_once()
        mock_dialog.search_button.setEnabled.assert_called_once_with(True)
        mock_dialog.status_bar.setText.assert_called_once_with("Search error: Connection failed")
        mock_dialog._search_error.assert_called_once_with("Connection failed")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])