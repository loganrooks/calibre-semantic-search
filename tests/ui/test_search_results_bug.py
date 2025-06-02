"""
Bug-First TDD: Search results showing corrupted/binary data

BUG: Search dialog shows results with:
- Title: 'Unknown'
- Author: ''
- Chunk text: 'PK\x03\x04...' (ZIP headers)

This test captures the bug where search results display binary data instead of
actual book content, causing the "Copy Citation" feature to fail.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from PyQt5.Qt import QApplication, QListWidgetItem, QLabel

# Direct imports to avoid Calibre dependencies
import sys
from pathlib import Path
plugin_path = Path(__file__).parent.parent.parent / "calibre_plugins"
sys.path.insert(0, str(plugin_path))

from semantic_search.ui.search_dialog import SemanticSearchDialog
from semantic_search.core.search_engine import SearchResult, SearchOptions, SearchScope, SearchMode


class TestSearchResultsBug:
    """Test that captures the corrupted search results bug"""
    
    @pytest.fixture
    def search_dialog(self, qtbot):
        """Create search dialog with mocked dependencies"""
        mock_gui = Mock()
        mock_gui.library_path = "/test/library"
        mock_gui.current_db = Mock()
        mock_gui.current_db.new_api = Mock()
        
        mock_plugin = Mock()
        
        dialog = SemanticSearchDialog(mock_gui, mock_plugin)
        qtbot.addWidget(dialog)
        
        return dialog
    
    def test_search_results_show_binary_data_bug(self, search_dialog, qtbot):
        """
        BUG: Search results display binary ZIP data instead of actual text.
        This test should FAIL until we fix the data extraction/display.
        """
        # Create mock search results that reproduce the bug
        corrupted_results = [
            SearchResult(
                chunk_id=1,
                book_id=123,
                book_title="Unknown",  # Bug: No title
                authors=[],  # Bug: No authors
                chunk_text="PK\x03\x04\x14\x00\x16\x08\x00\x004QVoa,\x14\x00\x00\x00\x14\x00\x00\x00\x08\x00\x00\x00mimetypeapplication/epub+zip",  # Bug: Binary data
                chunk_index=0,
                similarity_score=0.7785308554889042,
                metadata={}
            )
        ]
        
        # Mock search engine to return corrupted results
        mock_search_engine = Mock()
        async def mock_search(*args, **kwargs):
            return corrupted_results
        mock_search_engine.search = mock_search
        search_dialog.search_engine = mock_search_engine
        
        # Perform search
        search_dialog.query_input.setText("test query")
        search_dialog.perform_search()
        
        # Wait for results to be displayed
        qtbot.wait(500)  # Give time for async operations
        
        # ASSERTIONS: What should NOT happen
        assert search_dialog.results_list.count() > 0, "No results displayed"
        
        # Get the result widget
        item = search_dialog.results_list.item(0)
        result_card = search_dialog.results_list.itemWidget(item)
        
        # Check that binary data is NOT displayed
        result_text = result_card.findChild(QLabel, "content_label").text()
        assert "PK\x03\x04" not in result_text, "Binary ZIP header displayed in UI!"
        assert "mimetypeapplication/epub+zip" not in result_text, "EPUB mimetype displayed!"
        
        # Check that proper metadata IS displayed
        title_text = result_card.findChild(QLabel, "title_label").text()
        assert "Unknown" not in title_text, "Should have actual book title, not 'Unknown'"
        
        author_text = result_card.findChild(QLabel, "author_label").text()
        assert "Unknown Author" not in author_text, "Should have actual author"
        
    def test_copy_citation_with_proper_data(self, search_dialog, qtbot):
        """
        Test that copy citation works when given proper search results.
        This should PASS after fixing the data extraction issue.
        """
        # Create proper search results
        proper_results = [
            SearchResult(
                chunk_id=1,
                book_id=123,
                book_title="Being and Time",
                authors=["Martin Heidegger"],
                chunk_text="The question of Being has today been forgotten.",
                chunk_index=0,
                similarity_score=0.85,
                metadata={}
            )
        ]
        
        # Set up current results
        search_dialog.current_results = proper_results
        
        # Test copy citation
        with patch('PyQt5.Qt.QApplication.clipboard') as mock_clipboard:
            mock_clipboard_instance = Mock()
            mock_clipboard.return_value = mock_clipboard_instance
            
            # Call copy citation
            search_dialog._copy_citation(123, 1)
            
            # Verify proper citation was copied
            mock_clipboard_instance.setText.assert_called_once()
            citation = mock_clipboard_instance.setText.call_args[0][0]
            
            assert "Martin Heidegger" in citation
            assert "Being and Time" in citation
            assert "The question of Being" in citation
            
    def test_search_integration_end_to_end(self, search_dialog, qtbot):
        """
        Test the full search flow to identify where corruption occurs.
        """
        # Mock the entire search chain
        
        # 1. Mock repository to return proper book data
        mock_book_data = {
            'id': 123,
            'title': 'Test Book',
            'authors': ['Test Author'],
            'formats': ['EPUB']
        }
        
        # 2. Mock embedding repository to return embeddings
        mock_embeddings = [
            {
                'chunk_id': 1,
                'book_id': 123,
                'chunk_text': 'This is the actual text content of the book.',
                'chunk_index': 0,
                'embedding': [0.1] * 768  # Mock embedding vector
            }
        ]
        
        # 3. Mock search to return proper results
        async def mock_search(query, options):
            return [
                SearchResult(
                    chunk_id=1,
                    book_id=123,
                    book_title='Test Book',
                    authors=['Test Author'],
                    chunk_text='This is the actual text content of the book.',
                    chunk_index=0,
                    similarity_score=0.9,
                    metadata={}
                )
            ]
        
        # Initialize search engine with mocks
        mock_search_engine = Mock()
        mock_search_engine.search = mock_search
        search_dialog.search_engine = mock_search_engine
        
        # Perform search
        search_dialog.query_input.setText("test query")
        search_dialog.perform_search()
        
        # Wait for results
        qtbot.wait(500)
        
        # Verify results are properly displayed
        assert search_dialog.results_list.count() == 1
        
        # Get result widget and check content
        item = search_dialog.results_list.item(0)
        result_card = search_dialog.results_list.itemWidget(item)
        
        # Find the actual labels (they might not have names)
        labels = result_card.findChildren(QLabel)
        
        # Check that proper content is displayed
        content_found = False
        for label in labels:
            text = label.text()
            if "actual text content" in text:
                content_found = True
            # Should NOT find binary data
            assert "PK\x03\x04" not in text, f"Found binary data in label: {text}"
            
        assert content_found, "Actual text content not found in any label"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])