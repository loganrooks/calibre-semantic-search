"""
Tests for book navigation functionality using TDD

These tests verify that the book navigation system properly
opens books and navigates to specific positions.
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add path for our modules
module_path = os.path.join(os.path.dirname(__file__), '..', '..', 'calibre_plugins', 'semantic_search', 'ui')
sys.path.insert(0, module_path)


class TestBookNavigator:
    """Test book navigation functionality"""
    
    def test_navigator_opens_book_in_viewer(self):
        """Test that navigator opens book in Calibre viewer"""
        # GIVEN: Mock GUI and book navigation parameters
        mock_gui = Mock()
        mock_gui.iactions = {'View': Mock()}
        mock_viewer_action = mock_gui.iactions['View']
        
        # Create navigator (this will fail initially - no navigator exists!)
        from book_navigator import BookNavigator
        
        navigator = BookNavigator(mock_gui)
        
        # WHEN: Navigate to book
        book_id = 123
        position = None  # No specific position
        navigator.view_book(book_id, position)
        
        # THEN: Should open book in viewer
        mock_viewer_action.view_book.assert_called_once_with(book_id)
    
    def test_navigator_opens_book_with_position(self):
        """Test that navigator opens book at specific position"""
        # GIVEN: Mock GUI with viewer
        mock_gui = Mock()
        mock_gui.iactions = {'View': Mock()}
        mock_viewer_action = mock_gui.iactions['View']
        
        from book_navigator import BookNavigator
        navigator = BookNavigator(mock_gui)
        
        # WHEN: Navigate to specific position in book
        book_id = 456
        position = {"chunk_index": 5, "highlight_text": "philosophy of mind"}
        navigator.view_book(book_id, position)
        
        # THEN: Should open book and navigate to position
        mock_viewer_action.view_book.assert_called_once_with(book_id)
        # Note: Position navigation will be tested separately since it requires viewer integration
    
    def test_navigator_handles_missing_book(self):
        """Test that navigator gracefully handles missing books"""
        # GIVEN: Mock GUI that raises exception for missing book
        mock_gui = Mock()
        mock_gui.iactions = {'View': Mock()}
        mock_viewer_action = mock_gui.iactions['View']
        mock_viewer_action.view_book.side_effect = Exception("Book not found")
        
        from book_navigator import BookNavigator
        navigator = BookNavigator(mock_gui)
        
        # WHEN: Try to navigate to missing book
        book_id = 999
        result = navigator.view_book(book_id, None)
        
        # THEN: Should handle error gracefully
        assert result is False  # Indicates failure
        mock_viewer_action.view_book.assert_called_once_with(book_id)
    
    def test_navigator_extracts_position_from_search_result(self):
        """Test that navigator extracts position data from search result"""
        # GIVEN: Mock search result
        mock_result = Mock()
        mock_result.book_id = 789
        mock_result.chunk_index = 3
        mock_result.chunk_text = "The nature of consciousness remains..."
        mock_result.book_title = "Philosophy of Mind"
        mock_result.authors = ["John Doe"]
        
        mock_gui = Mock()
        from book_navigator import BookNavigator
        navigator = BookNavigator(mock_gui)
        
        # WHEN: Extract navigation parameters
        nav_params = navigator.extract_navigation_params(mock_result)
        
        # THEN: Should extract correct parameters
        assert nav_params['book_id'] == 789
        assert nav_params['chunk_index'] == 3
        assert nav_params['highlight_text'] == "The nature of consciousness remains..."
        assert nav_params['book_title'] == "Philosophy of Mind"
        assert nav_params['authors'] == ["John Doe"]


class TestSimilarPassageFinder:
    """Test finding similar passages functionality"""
    
    def test_finder_searches_for_similar_chunks(self):
        """Test that finder searches for passages similar to given chunk"""
        # GIVEN: Mock search engine and chunk ID
        mock_search_engine = Mock()
        mock_search_engine.find_similar_chunks.return_value = [
            Mock(book_id=1, chunk_text="Similar passage 1"),
            Mock(book_id=2, chunk_text="Similar passage 2")
        ]
        
        # Create finder (this will fail initially - no finder exists!)
        from book_navigator import SimilarPassageFinder
        
        finder = SimilarPassageFinder(mock_search_engine)
        
        # WHEN: Find similar passages
        chunk_id = 42
        results = finder.find_similar(chunk_id)
        
        # THEN: Should search for similar chunks
        mock_search_engine.find_similar_chunks.assert_called_once_with(chunk_id)
        assert len(results) == 2
        assert results[0].book_id == 1
        assert results[1].book_id == 2
    
    def test_finder_handles_no_similar_passages(self):
        """Test that finder handles case when no similar passages found"""
        # GIVEN: Mock search engine that returns empty results
        mock_search_engine = Mock()
        mock_search_engine.find_similar_chunks.return_value = []
        
        from book_navigator import SimilarPassageFinder
        finder = SimilarPassageFinder(mock_search_engine)
        
        # WHEN: Find similar passages for chunk with no matches
        chunk_id = 99
        results = finder.find_similar(chunk_id)
        
        # THEN: Should return empty list
        assert results == []
        mock_search_engine.find_similar_chunks.assert_called_once_with(chunk_id)
    
    def test_finder_handles_search_error(self):
        """Test that finder handles search engine errors gracefully"""
        # GIVEN: Mock search engine that raises error
        mock_search_engine = Mock()
        mock_search_engine.find_similar_chunks.side_effect = Exception("Search failed")
        
        from book_navigator import SimilarPassageFinder
        finder = SimilarPassageFinder(mock_search_engine)
        
        # WHEN: Find similar passages when search fails
        chunk_id = 123
        results = finder.find_similar(chunk_id)
        
        # THEN: Should handle error and return empty list
        assert results == []
        mock_search_engine.find_similar_chunks.assert_called_once_with(chunk_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])