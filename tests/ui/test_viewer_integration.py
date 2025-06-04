"""
Tests for viewer context menu integration using TDD

These tests verify that the semantic search functionality
integrates properly with Calibre's book viewer.
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add path for our modules
module_path = os.path.join(os.path.dirname(__file__), '..', '..', 'calibre_plugins', 'semantic_search', 'ui')
sys.path.insert(0, module_path)


class TestViewerMenuIntegrator:
    """Test viewer context menu integration"""
    
    def test_integrator_adds_search_action_to_viewer(self):
        """Test that integrator adds semantic search action to viewer context menu"""
        # GIVEN: Mock viewer with context menu
        mock_viewer = Mock()
        mock_context_menu = Mock()
        mock_viewer.view.contextMenuEvent = Mock()
        mock_viewer.view.get_context_menu = Mock(return_value=mock_context_menu)
        
        # Create integrator (this will fail initially - no integrator exists!)
        from viewer_integrator import ViewerMenuIntegrator
        
        integrator = ViewerMenuIntegrator()
        
        # WHEN: Integrate with viewer
        integrator.integrate_with_viewer(mock_viewer)
        
        # THEN: Should add semantic search action to context menu
        mock_context_menu.addSeparator.assert_called()
        mock_context_menu.addAction.assert_called_with("Search Similar Passages")
    
    def test_integrator_handles_text_selection_search(self):
        """Test that integrator handles search for selected text"""
        # GIVEN: Mock viewer with text selection
        mock_viewer = Mock()
        mock_viewer.view.get_selected_text.return_value = "consciousness and phenomenology"
        
        from viewer_integrator import ViewerMenuIntegrator
        integrator = ViewerMenuIntegrator()
        
        # Mock search callback
        search_callback = Mock()
        integrator.set_search_callback(search_callback)
        
        # WHEN: User selects "Search Similar Passages" from context menu
        integrator._on_search_similar_action(mock_viewer)
        
        # THEN: Should trigger search with selected text
        search_callback.assert_called_once_with("consciousness and phenomenology")
    
    def test_integrator_handles_empty_text_selection(self):
        """Test that integrator handles case when no text is selected"""
        # GIVEN: Mock viewer with no text selection
        mock_viewer = Mock()
        mock_viewer.view.get_selected_text.return_value = ""
        
        from viewer_integrator import ViewerMenuIntegrator
        integrator = ViewerMenuIntegrator()
        
        # Mock error callback
        error_callback = Mock()
        integrator.set_error_callback(error_callback)
        
        # WHEN: User tries to search with no selection
        integrator._on_search_similar_action(mock_viewer)
        
        # THEN: Should show error message
        error_callback.assert_called_once_with("Please select some text to search for similar passages.")
    
    def test_integrator_extracts_current_position(self):
        """Test that integrator extracts current reading position"""
        # GIVEN: Mock viewer with position information
        mock_viewer = Mock()
        mock_viewer.view.get_current_position.return_value = {
            'book_id': 456,
            'chapter': 3,
            'page': 45,
            'position': 0.35  # 35% through book
        }
        
        from viewer_integrator import ViewerMenuIntegrator
        integrator = ViewerMenuIntegrator()
        
        # WHEN: Extract current position
        position = integrator.get_current_position(mock_viewer)
        
        # THEN: Should return position information
        assert position['book_id'] == 456
        assert position['chapter'] == 3
        assert position['page'] == 45
        assert position['position'] == 0.35


class TestViewerSearchCoordinator:
    """Test coordination between viewer and search functionality"""
    
    def test_coordinator_launches_search_from_viewer(self):
        """Test that coordinator launches search dialog from viewer selection"""
        # GIVEN: Mock search dialog and viewer
        mock_search_dialog = Mock()
        mock_viewer = Mock()
        
        # Create coordinator (this will fail initially - no coordinator exists!)
        from viewer_integrator import ViewerSearchCoordinator
        
        coordinator = ViewerSearchCoordinator(mock_search_dialog)
        
        # WHEN: Launch search with selected text
        selected_text = "the nature of being"
        coordinator.search_from_viewer(selected_text, mock_viewer)
        
        # THEN: Should populate search dialog and show it
        mock_search_dialog.set_query_text.assert_called_once_with(selected_text)
        mock_search_dialog.show.assert_called_once()
        mock_search_dialog.raise_.assert_called_once()
    
    def test_coordinator_navigates_to_search_result(self):
        """Test that coordinator navigates viewer to search result"""
        # GIVEN: Mock search dialog and viewer with same book
        mock_search_dialog = Mock()
        mock_viewer = Mock()
        mock_viewer.current_book_id = 789  # Same as result book
        
        from viewer_integrator import ViewerSearchCoordinator
        coordinator = ViewerSearchCoordinator(mock_search_dialog)
        
        # WHEN: Navigate to search result in same book
        result = Mock()
        result.book_id = 789  # Same book
        result.chunk_index = 2
        result.chunk_text = "Being and Time explores..."
        
        coordinator.navigate_to_result(result, mock_viewer)
        
        # THEN: Should navigate viewer to result position
        mock_viewer.view.goto_position.assert_called_once_with(2)
        mock_viewer.view.highlight_text.assert_called_once_with("Being and Time explores...")
    
    def test_coordinator_handles_cross_book_navigation(self):
        """Test that coordinator handles navigation to different book"""
        # GIVEN: Mock components for cross-book navigation
        mock_search_dialog = Mock()
        mock_viewer = Mock()
        mock_viewer.current_book_id = 100  # Different from result book
        
        from viewer_integrator import ViewerSearchCoordinator
        coordinator = ViewerSearchCoordinator(mock_search_dialog)
        
        # Mock book opener
        book_opener = Mock()
        coordinator.set_book_opener(book_opener)
        
        # WHEN: Navigate to result in different book
        result = Mock()
        result.book_id = 200  # Different book
        result.chunk_index = 5
        
        coordinator.navigate_to_result(result, mock_viewer)
        
        # THEN: Should open different book
        book_opener.open_book.assert_called_once_with(200, position=5)


class TestViewerActionFactory:
    """Test factory for creating viewer actions"""
    
    def test_factory_creates_search_action(self):
        """Test that factory creates search action with proper configuration"""
        # GIVEN: Mock viewer and parent widget
        mock_viewer = Mock()
        mock_parent = Mock()
        
        # Create factory (this will fail initially - no factory exists!)
        from viewer_integrator import ViewerActionFactory
        
        factory = ViewerActionFactory()
        
        # WHEN: Create search action
        action = factory.create_search_action(mock_parent, mock_viewer)
        
        # THEN: Should create action with proper text and icon
        assert action is not None
        # Note: In real implementation, this would test Qt action properties
    
    def test_factory_creates_separator_action(self):
        """Test that factory creates menu separator"""
        # GIVEN: Mock parent widget
        mock_parent = Mock()
        
        from viewer_integrator import ViewerActionFactory
        factory = ViewerActionFactory()
        
        # WHEN: Create separator
        separator = factory.create_separator(mock_parent)
        
        # THEN: Should create separator action
        assert separator is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])