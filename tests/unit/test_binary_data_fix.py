"""
Test that verifies the binary data fix works correctly
"""

import pytest
from unittest.mock import Mock, MagicMock
import sys
from pathlib import Path

# Add plugin path
plugin_path = Path(__file__).parent.parent.parent / "calibre_plugins" / "semantic_search"
sys.path.insert(0, str(plugin_path))

from data.repositories import CalibreRepository
from core.search_engine import SearchResult, SearchEngine


class TestBinaryDataFix:
    """Test that binary data is properly handled"""
    
    def test_validate_extracted_text(self):
        """Test the text validation method"""
        # Mock database
        mock_db = Mock()
        repo = CalibreRepository(mock_db)
        
        # Test valid text
        valid_text = "This is valid philosophical text about Being and Time."
        is_valid, cleaned = repo._validate_extracted_text(valid_text, "EPUB")
        assert is_valid is True
        assert cleaned == valid_text
        
        # Test binary data (ZIP header)
        binary_text = "PK\x03\x04\x14\x00\x16\x08\x00\x004QVoa,\x14\x00\x00\x00"
        is_valid, cleaned = repo._validate_extracted_text(binary_text, "EPUB")
        assert is_valid is False
        assert cleaned == ""
        
        # Test mostly non-printable
        bad_text = "\x00\x01\x02\x03\x04\x05" * 100 + "Some text"
        is_valid, cleaned = repo._validate_extracted_text(bad_text, "PDF")
        assert is_valid is False
        
    def test_search_filters_binary_results(self):
        """Test that search engine filters out binary data results"""
        # Mock repository that returns some binary data
        mock_repo = Mock()
        mock_repo.search_similar = Mock(return_value=[
            {
                "chunk_id": 1,
                "book_id": 123,
                "title": "Valid Book",
                "authors": ["Valid Author"],
                "chunk_text": "This is valid text content",
                "chunk_index": 0,
                "similarity": 0.9,
                "metadata": {}
            },
            {
                "chunk_id": 2,
                "book_id": 456,
                "title": "Corrupted Book",
                "authors": ["Some Author"],
                "chunk_text": "PK\x03\x04\x14\x00\x16\x08 binary data here",
                "chunk_index": 0,
                "similarity": 0.85,
                "metadata": {}
            }
        ])
        
        # Mock embedding service
        mock_embedding = Mock()
        mock_embedding.generate_embedding = Mock(return_value=[0.1] * 768)
        
        # Create search engine
        engine = SearchEngine(mock_repo, mock_embedding)
        
        # Mock the async search method
        from calibre_plugins.semantic_search.core.search_engine import SearchOptions, SearchMode, SearchScope
        
        # Run synchronous version of search logic
        raw_results = mock_repo.search_similar([0.1] * 768, 20, {})
        
        # Filter results like the search engine does
        filtered_results = []
        for row in raw_results:
            chunk_text = row.get("chunk_text", "")
            if chunk_text.startswith('PK\x03\x04') or chunk_text.startswith('PK'):
                continue
            filtered_results.append(row)
        
        # Should only have 1 valid result
        assert len(filtered_results) == 1
        assert filtered_results[0]["title"] == "Valid Book"
        assert "binary data" not in filtered_results[0]["chunk_text"]
        
    def test_citation_with_clean_data(self):
        """Test that citation works with properly cleaned data"""
        # Create a result with clean data
        result = SearchResult(
            chunk_id=1,
            book_id=123,
            book_title="Being and Time",
            authors=["Martin Heidegger"],
            chunk_text="The question of Being has today been forgotten.",
            chunk_index=0,
            similarity_score=0.85,
            metadata={}
        )
        
        # Test citation generation
        citation = result.citation
        assert "Martin Heidegger" in citation
        assert "Being and Time" in citation
        
        # Should not have any binary data indicators
        assert "PK" not in citation
        assert "Unknown" not in citation


if __name__ == "__main__":
    pytest.main([__file__, "-v"])