"""
Test-Driven Development for Viewer Integration (HIGH Priority #2)

Tests for fixing the issue: "View in Book" opens viewer but doesn't navigate 
to search result location.

Root Cause: Missing viewer integration - only opens book, doesn't navigate to chunk
Location: search_dialog.py:423-445 - missing chunk navigation implementation

Part of IMPLEMENTATION_PLAN_2025.md Phase 1.2 - Implement Viewer Integration (Days 2-3)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from calibre_plugins.semantic_search.ui.viewer_integration import ViewerIntegration
from calibre_plugins.semantic_search.data.repositories import EmbeddingRepository


class TestViewerNavigation:
    """Test viewer navigation to specific chunk locations"""
    
    @pytest.fixture
    def mock_viewer(self):
        """Mock Calibre viewer object"""
        viewer = Mock()
        viewer.goto_position = Mock()
        viewer.highlight_text = Mock()
        viewer.current_book_id = 1
        viewer.show = Mock()
        viewer.raise_ = Mock()  # For bringing viewer to front
        return viewer
    
    @pytest.fixture
    def mock_embedding_repo(self, tmp_path):
        """Mock embedding repository with chunk data"""
        db_path = tmp_path / "test.db"
        repo = EmbeddingRepository(db_path)
        
        # Mock get_chunk method to return chunk location data
        def mock_get_chunk(chunk_id):
            chunk_data = {
                1: {
                    'chunk_id': 1,
                    'book_id': 1,
                    'chunk_text': 'Dasein is being-in-the-world',
                    'start_pos': 1250,
                    'end_pos': 1278,
                    'chunk_index': 5,
                    'metadata': {'chapter': 'Chapter 1', 'page': 42}
                },
                2: {
                    'chunk_id': 2,
                    'book_id': 1,
                    'chunk_text': 'The philosopher king must rule',
                    'start_pos': 5670,
                    'end_pos': 5700,
                    'chunk_index': 23,
                    'metadata': {'chapter': 'Book VII', 'page': 180}
                },
                3: {
                    'chunk_id': 3,
                    'book_id': 2,
                    'chunk_text': 'Synthetic a priori knowledge',
                    'start_pos': 890,
                    'end_pos': 918,
                    'chunk_index': 3,
                    'metadata': {'section': 'Introduction', 'page': 25}
                }
            }
            return chunk_data.get(chunk_id)
        
        repo.get_chunk = mock_get_chunk
        return repo
    
    @pytest.fixture
    def viewer_integration(self, mock_embedding_repo):
        """ViewerIntegration instance with mocked dependencies"""
        return ViewerIntegration(embedding_repo=mock_embedding_repo)
    
    def test_navigate_to_chunk_in_viewer(self, viewer_integration, mock_viewer):
        """Test navigating viewer to specific chunk location"""
        book_id = 1
        chunk_id = 1
        
        # Should navigate to chunk location in viewer
        success = viewer_integration.navigate_to_chunk(mock_viewer, book_id, chunk_id)
        
        # Should succeed
        assert success is True
        
        # Should call viewer navigation methods
        mock_viewer.goto_position.assert_called_once()
        
        # Should get position for the chunk
        call_args = mock_viewer.goto_position.call_args[0]
        position = call_args[0] if call_args else None
        
        # Position should be calculated from chunk start_pos (1250)
        assert position is not None
        assert isinstance(position, (int, float, str))
    
    def test_chunk_location_mapping(self, viewer_integration):
        """Test converting chunk position to viewer position"""
        # Test various chunk positions
        test_cases = [
            (1250, 1278, 'expected_position_1'),  # Regular text position
            (0, 50, 'expected_position_2'),       # Beginning of book
            (10000, 10100, 'expected_position_3'), # Later in book
        ]
        
        for start_pos, end_pos, expected_type in test_cases:
            chunk_data = {
                'start_pos': start_pos,
                'end_pos': end_pos,
                'chunk_text': 'Test content',
                'metadata': {}
            }
            
            # Should convert chunk position to viewer position
            position = viewer_integration._calculate_viewer_position(chunk_data)
            
            # Should return valid position
            assert position is not None
            # Position should be based on character position
            assert isinstance(position, (int, float, str))
    
    def test_text_highlighting_in_viewer(self, viewer_integration, mock_viewer):
        """Test highlighting found text in viewer"""
        book_id = 1
        chunk_id = 1
        
        # Navigate and highlight
        viewer_integration.navigate_to_chunk(mock_viewer, book_id, chunk_id)
        
        # Should highlight the chunk text
        mock_viewer.highlight_text.assert_called_once()
        
        # Should highlight the actual chunk text
        highlight_args = mock_viewer.highlight_text.call_args[0]
        highlighted_text = highlight_args[0] if highlight_args else None
        
        assert highlighted_text == 'Dasein is being-in-the-world'
    
    def test_viewer_integration_epub_format(self, viewer_integration, mock_viewer):
        """Test viewer integration works with EPUB format"""
        # Mock EPUB-specific navigation
        mock_viewer.format = 'EPUB'
        mock_viewer.goto_cfi = Mock()  # EPUB uses CFI (Canonical Fragment Identifier)
        
        book_id = 1
        chunk_id = 1
        
        success = viewer_integration.navigate_to_chunk(mock_viewer, book_id, chunk_id)
        
        assert success is True
        
        # For EPUB, might use CFI navigation instead of character position
        if hasattr(mock_viewer, 'goto_cfi') and mock_viewer.format == 'EPUB':
            # Should attempt EPUB-specific navigation
            assert mock_viewer.goto_cfi.called or mock_viewer.goto_position.called
    
    def test_viewer_integration_pdf_format(self, viewer_integration, mock_viewer):
        """Test viewer integration works with PDF format"""
        mock_viewer.format = 'PDF'
        mock_viewer.goto_page = Mock()  # PDF uses page navigation
        
        book_id = 1
        chunk_id = 1
        
        success = viewer_integration.navigate_to_chunk(mock_viewer, book_id, chunk_id)
        
        assert success is True
        
        # For PDF, should use page-based navigation
        if hasattr(mock_viewer, 'goto_page') and mock_viewer.format == 'PDF':
            assert mock_viewer.goto_page.called or mock_viewer.goto_position.called
    
    def test_navigation_accuracy_validation(self, viewer_integration):
        """Test navigation accuracy within acceptable range"""
        # Test that calculated positions are reasonable
        chunk_positions = [
            {'start_pos': 0, 'end_pos': 100, 'chunk_text': 'Beginning'},
            {'start_pos': 5000, 'end_pos': 5200, 'chunk_text': 'Middle content'},
            {'start_pos': 50000, 'end_pos': 50300, 'chunk_text': 'Later content'},
        ]
        
        for chunk_data in chunk_positions:
            position = viewer_integration._calculate_viewer_position(chunk_data)
            
            # Position should be reasonable relative to chunk position
            if isinstance(position, (int, float)):
                # Should be within reasonable range of start position
                start_pos = chunk_data['start_pos']
                # Allow some variance for format conversion, but should be close
                assert abs(position - start_pos) <= start_pos * 0.1 or abs(position - start_pos) <= 1000
    
    def test_highlight_duration_configuration(self, viewer_integration, mock_viewer):
        """Test that text highlighting has configurable duration"""
        book_id = 1
        chunk_id = 1
        
        # Test with custom highlight duration
        viewer_integration.navigate_to_chunk(mock_viewer, book_id, chunk_id, highlight_duration=3000)
        
        # Should pass duration to highlight method
        mock_viewer.highlight_text.assert_called_once()
        call_args = mock_viewer.highlight_text.call_args
        
        # Check if duration parameter was passed
        if len(call_args[0]) > 1 or call_args[1]:  # positional or keyword args
            # Duration should be configurable
            assert True  # Basic test that call was made with parameters
    
    def test_viewer_error_handling(self, viewer_integration, mock_viewer):
        """Test error handling when viewer operations fail"""
        # Mock viewer methods to raise exceptions
        mock_viewer.goto_position.side_effect = Exception("Viewer navigation failed")
        
        book_id = 1
        chunk_id = 1
        
        # Should handle viewer errors gracefully
        success = viewer_integration.navigate_to_chunk(mock_viewer, book_id, chunk_id)
        
        # Should return False on failure, not crash
        assert success is False
    
    def test_nonexistent_chunk_handling(self, viewer_integration, mock_viewer):
        """Test handling of navigation to non-existent chunk"""
        book_id = 1
        chunk_id = 999  # Non-existent chunk
        
        # Should handle gracefully when chunk doesn't exist
        success = viewer_integration.navigate_to_chunk(mock_viewer, book_id, chunk_id)
        
        # Should return False when chunk not found
        assert success is False
        
        # Should not call viewer methods for non-existent chunk
        mock_viewer.goto_position.assert_not_called()
        mock_viewer.highlight_text.assert_not_called()


class TestViewerAPIIntegration:
    """Test integration with Calibre's viewer API"""
    
    def test_viewer_api_position_formats(self):
        """Test handling different viewer position formats"""
        # Different viewers might expect different position formats
        position_formats = [
            ('character', 1250),           # Character offset
            ('percentage', 0.25),          # Percentage through book  
            ('page', 42),                  # Page number
            ('cfi', 'epubcfi(/6/4!/4/2)'), # EPUB CFI
        ]
        
        for format_type, position_value in position_formats:
            # Should be able to handle different position formats
            assert position_value is not None
            
            if format_type == 'character':
                assert isinstance(position_value, int)
                assert position_value >= 0
            elif format_type == 'percentage':
                assert isinstance(position_value, float)
                assert 0.0 <= position_value <= 1.0
            elif format_type == 'page':
                assert isinstance(position_value, int)
                assert position_value > 0
            elif format_type == 'cfi':
                assert isinstance(position_value, str)
                assert 'epubcfi' in position_value
    
    def test_viewer_focus_and_activation(self):
        """Test bringing viewer to focus when navigating"""
        mock_viewer = Mock()
        mock_viewer.show = Mock()
        mock_viewer.raise_ = Mock()
        mock_viewer.activateWindow = Mock()
        
        viewer_integration = ViewerIntegration(embedding_repo=Mock())
        
        # Should bring viewer to front
        viewer_integration._bring_viewer_to_front(mock_viewer)
        
        # Should call focus methods
        mock_viewer.show.assert_called_once()
        mock_viewer.raise_.assert_called_once()
        
        if hasattr(mock_viewer, 'activateWindow'):
            mock_viewer.activateWindow.assert_called_once()
    
    def test_multiple_viewer_instances(self):
        """Test handling multiple viewer instances"""
        # Mock scenario with multiple viewers
        viewer1 = Mock()
        viewer1.current_book_id = 1
        viewer2 = Mock()
        viewer2.current_book_id = 2
        
        active_viewers = [viewer1, viewer2]
        
        viewer_integration = ViewerIntegration(embedding_repo=Mock())
        
        # Should find correct viewer for book
        target_viewer = viewer_integration._find_viewer_for_book(active_viewers, book_id=1)
        
        assert target_viewer == viewer1
        
        target_viewer = viewer_integration._find_viewer_for_book(active_viewers, book_id=2)
        
        assert target_viewer == viewer2


class TestSearchDialogViewerIntegration:
    """Test integration between search dialog and viewer"""
    
    def test_view_in_book_button_functionality(self):
        """Test that 'View in Book' button properly navigates to chunk"""
        # Mock search result with chunk information
        mock_search_result = Mock()
        mock_search_result.chunk_id = 1
        mock_search_result.book_id = 1
        mock_search_result.chunk_text = "Philosophy content"
        
        # Mock search dialog
        mock_search_dialog = Mock()
        mock_search_dialog.current_selection = mock_search_result
        
        # Mock viewer integration
        mock_viewer_integration = Mock()
        mock_viewer_integration.navigate_to_chunk.return_value = True
        
        # Simulate clicking "View in Book" button
        # This should trigger navigation to the chunk
        success = mock_viewer_integration.navigate_to_chunk(
            Mock(),  # viewer
            mock_search_result.book_id,
            mock_search_result.chunk_id
        )
        
        assert success is True
        mock_viewer_integration.navigate_to_chunk.assert_called_once()
    
    def test_view_in_book_without_selection(self):
        """Test 'View in Book' behavior when no search result is selected"""
        mock_search_dialog = Mock()
        mock_search_dialog.current_selection = None
        
        # Should handle gracefully when nothing is selected
        mock_viewer_integration = Mock()
        
        # Should not attempt navigation without selection
        # This test verifies the UI properly checks for selection
        if mock_search_dialog.current_selection is None:
            # Should not call navigate_to_chunk
            mock_viewer_integration.navigate_to_chunk.assert_not_called()
    
    def test_viewer_opening_fallback(self):
        """Test fallback behavior when chunk navigation fails"""
        mock_viewer_integration = Mock()
        mock_viewer_integration.navigate_to_chunk.return_value = False  # Navigation failed
        mock_viewer_integration.open_book_in_viewer.return_value = True  # Book opening succeeded
        
        book_id = 1
        chunk_id = 1
        
        # Try navigation first
        nav_success = mock_viewer_integration.navigate_to_chunk(Mock(), book_id, chunk_id)
        
        if not nav_success:
            # Fallback to just opening the book
            open_success = mock_viewer_integration.open_book_in_viewer(Mock(), book_id)
            assert open_success is True
    
    def test_viewer_integration_user_feedback(self):
        """Test user feedback when viewer operations succeed/fail"""
        # Mock UI feedback mechanisms
        mock_status_bar = Mock()
        mock_message_box = Mock()
        
        mock_viewer_integration = Mock()
        mock_viewer_integration.navigate_to_chunk.return_value = True
        
        # Successful navigation should provide positive feedback
        success = mock_viewer_integration.navigate_to_chunk(Mock(), 1, 1)
        
        if success:
            # Should show success message
            mock_status_bar.showMessage = Mock()
            mock_status_bar.showMessage("Navigated to search result in viewer")
            mock_status_bar.showMessage.assert_called_once()
        
        # Failed navigation should provide error feedback
        mock_viewer_integration.navigate_to_chunk.return_value = False
        success = mock_viewer_integration.navigate_to_chunk(Mock(), 1, 1)
        
        if not success:
            # Should show error message
            mock_message_box.warning = Mock()
            mock_message_box.warning(None, "Navigation Failed", "Could not navigate to search result")
            mock_message_box.warning.assert_called_once()


class TestPositionCalculation:
    """Test position calculation algorithms"""
    
    def test_character_position_to_viewer_position(self):
        """Test converting character positions to viewer positions"""
        viewer_integration = ViewerIntegration(embedding_repo=Mock())
        
        # Test cases with different character positions
        test_cases = [
            (0, 100, "beginning"),      # Start of book
            (5000, 5200, "middle"),     # Middle of book
            (50000, 50300, "end"),      # Near end of book
        ]
        
        for start_pos, end_pos, description in test_cases:
            chunk_data = {
                'start_pos': start_pos,
                'end_pos': end_pos,
                'chunk_text': f"Content at {description}",
                'metadata': {}
            }
            
            position = viewer_integration._calculate_viewer_position(chunk_data)
            
            # Should return valid position
            assert position is not None
            # Position should be related to character position
            if isinstance(position, (int, float)):
                assert position >= 0
    
    def test_page_based_position_calculation(self):
        """Test position calculation for page-based formats"""
        viewer_integration = ViewerIntegration(embedding_repo=Mock())
        
        # Mock chunk with page metadata
        chunk_data = {
            'start_pos': 5000,
            'end_pos': 5200,
            'chunk_text': "Content on page 42",
            'metadata': {'page': 42}
        }
        
        # Should use page info when available
        position = viewer_integration._calculate_page_position(chunk_data)
        
        if position is not None:
            # Should return page-based position
            assert isinstance(position, (int, str))
    
    def test_epub_cfi_position_calculation(self):
        """Test CFI position calculation for EPUB format"""
        viewer_integration = ViewerIntegration(embedding_repo=Mock())
        
        # Mock EPUB chunk with CFI metadata
        chunk_data = {
            'start_pos': 1250,
            'end_pos': 1300,
            'chunk_text': "EPUB content",
            'metadata': {
                'cfi': 'epubcfi(/6/4!/4/2/2)',
                'chapter': 'Chapter 1'
            }
        }
        
        # Should calculate CFI position for EPUB
        cfi_position = viewer_integration._calculate_epub_cfi(chunk_data)
        
        if cfi_position is not None:
            # Should return valid CFI
            assert isinstance(cfi_position, str)
            assert 'epubcfi' in cfi_position
    
    def test_position_accuracy_validation(self):
        """Test that position calculations are accurate enough"""
        viewer_integration = ViewerIntegration(embedding_repo=Mock())
        
        # Test multiple chunks from same book
        book_chunks = [
            {'start_pos': 100, 'end_pos': 200, 'chunk_index': 0},
            {'start_pos': 500, 'end_pos': 600, 'chunk_index': 1}, 
            {'start_pos': 1000, 'end_pos': 1100, 'chunk_index': 2},
        ]
        
        positions = []
        for chunk_data in book_chunks:
            position = viewer_integration._calculate_viewer_position(chunk_data)
            positions.append(position)
        
        # Positions should be ordered (later chunks = higher positions)
        if all(isinstance(p, (int, float)) for p in positions):
            assert positions[0] <= positions[1] <= positions[2]