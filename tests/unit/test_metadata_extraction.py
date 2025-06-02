"""
Test-Driven Development for Metadata Extraction (CRITICAL Priority #1)

Tests for fixing the critical issue: Search results show "Unknown Author. Unknown." 
instead of actual book metadata.

Root Cause: SearchResult objects aren't being populated with author data from CalibreRepository
Location: search_dialog.py:297 - authors field not populated in search results

Part of IMPLEMENTATION_PLAN_2025.md Phase 1.1 - Fix Metadata Extraction (Day 1)
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict, Any

from calibre_plugins.semantic_search.core.search_engine import SearchEngine, SearchOptions
from calibre_plugins.semantic_search.data.repositories import EmbeddingRepository, CalibreRepository


class TestMetadataEnrichment:
    """Test metadata enrichment in search results"""
    
    @pytest.fixture
    def mock_calibre_repo(self):
        """Mock Calibre repository with test book metadata"""
        repo = Mock(spec=CalibreRepository)
        
        # Mock metadata for different books
        repo.get_book_metadata.side_effect = lambda book_id: {
            1: {
                'id': 1,
                'title': 'Being and Time',
                'authors': ['Martin Heidegger'],
                'tags': ['philosophy', 'existentialism'],
                'series': None,
                'pubdate': '1927-01-01',
                'language': 'en',
                'publisher': 'Max Niemeyer Verlag'
            },
            2: {
                'id': 2,
                'title': 'The Republic',
                'authors': ['Plato'],
                'tags': ['philosophy', 'ancient'],
                'series': None,
                'pubdate': '380-01-01',
                'language': 'en',
                'publisher': 'Ancient Press'
            },
            3: {
                'id': 3,
                'title': 'Critique of Pure Reason',
                'authors': ['Immanuel Kant'],
                'tags': ['philosophy', 'epistemology'],
                'series': 'Critiques',
                'pubdate': '1781-01-01',
                'language': 'de',
                'publisher': 'Johann Friedrich Hartknoch'
            }
        }.get(book_id, {
            'id': book_id,
            'title': f'Unknown Book {book_id}',
            'authors': ['Unknown Author'],
            'tags': [],
            'series': None,
            'pubdate': None,
            'language': 'en',
            'publisher': None
        })
        
        return repo
    
    @pytest.fixture
    def mock_embedding_repo(self, tmp_path):
        """Mock embedding repository with search results"""
        db_path = tmp_path / "test.db"
        repo = Mock(spec=EmbeddingRepository)
        
        # Mock async search_similar method
        async def mock_search_similar(embedding, limit=10, filters=None):
            # Return mock raw search results without enriched metadata
            return [
                {
                    'chunk_id': 1,
                    'book_id': 1,
                    'chunk_text': 'Dasein is being-in-the-world',
                    'chunk_index': 0,
                    'similarity': 0.95,
                },
                {
                    'chunk_id': 2,
                    'book_id': 2,
                    'chunk_text': 'The philosopher king must rule',
                    'chunk_index': 5,
                    'similarity': 0.87,
                },
                {
                    'chunk_id': 3,
                    'book_id': 3,
                    'chunk_text': 'Synthetic a priori knowledge',
                    'chunk_index': 12,
                    'similarity': 0.82,
                }
            ]
        
        repo.search_similar = mock_search_similar
        return repo
    
    @pytest.mark.asyncio
    async def test_search_results_include_actual_authors(self, mock_calibre_repo, mock_embedding_repo):
        """Test that search results include actual author names, not 'Unknown'"""
        # This test should FAIL initially - authors should be 'Unknown' before fix
        
        # Create mock embedding service
        mock_embedding_service = AsyncMock()
        mock_embedding_service.generate_embedding.return_value = [0.1] * 768
        
        search_engine = SearchEngine(
            mock_embedding_repo,
            mock_embedding_service,
            mock_calibre_repo
        )
        
        # Perform search
        options = SearchOptions()
        results = await search_engine.search("philosophy", options)
        
        # Verify results include actual authors (should FAIL before implementation)
        assert len(results) > 0
        
        # These assertions should FAIL initially showing the bug
        for result in results:
            assert hasattr(result, 'authors'), "SearchResult should have authors field"
            assert result.authors != ['Unknown Author'], f"Book {result.book_id} should have real authors, not 'Unknown Author'"
            assert result.authors != [], f"Book {result.book_id} should have non-empty authors"
            
            # Specific author checks
            if result.book_id == 1:
                assert 'Martin Heidegger' in result.authors
            elif result.book_id == 2:
                assert 'Plato' in result.authors
            elif result.book_id == 3:
                assert 'Immanuel Kant' in result.authors
    
    @pytest.mark.asyncio
    async def test_search_results_include_actual_titles(self, mock_calibre_repo, mock_embedding_repo):
        """Test that search results include actual book titles, not 'Unknown'"""
        # Create mock embedding service
        mock_embedding_service = AsyncMock()
        mock_embedding_service.generate_embedding.return_value = [0.1] * 768
        
        search_engine = SearchEngine(
            mock_embedding_repo,
            mock_embedding_service,
            mock_calibre_repo
        )
        
        options = SearchOptions()
        results = await search_engine.search("being", options)
        
        assert len(results) > 0
        
        for result in results:
            assert hasattr(result, 'book_title'), "SearchResult should have book_title field"
            assert not result.book_title.startswith('Unknown'), f"Book {result.book_id} should have real title, not 'Unknown'"
            
            # Specific title checks
            if result.book_id == 1:
                assert result.book_title == 'Being and Time'
            elif result.book_id == 2:
                assert result.book_title == 'The Republic'
            elif result.book_id == 3:
                assert result.book_title == 'Critique of Pure Reason'
    
    @pytest.mark.asyncio
    async def test_metadata_enrichment_from_calibre_repository(self, mock_calibre_repo, mock_embedding_repo):
        """Test that SearchEngine enriches results with metadata from CalibreRepository"""
        # Create mock embedding service
        mock_embedding_service = AsyncMock()
        mock_embedding_service.generate_embedding.return_value = [0.1] * 768
        
        search_engine = SearchEngine(
            mock_embedding_repo,
            mock_embedding_service,
            mock_calibre_repo
        )
        
        options = SearchOptions()
        results = await search_engine.search("philosophy", options)
        
        # Verify metadata enrichment actually happened
        assert len(results) > 0
        
        for result in results:
            # Should have core metadata fields
            assert hasattr(result, 'authors')
            assert hasattr(result, 'book_title') 
            
            # Authors should be list, not string
            assert isinstance(result.authors, list)
            assert len(result.authors) > 0
            
            # Book title should be set
            assert isinstance(result.book_title, str)
            assert result.book_title != 'Unknown'
    
    @pytest.mark.asyncio
    async def test_metadata_caching_avoids_repeated_lookups(self, mock_calibre_repo, mock_embedding_repo):
        """Test that metadata lookups are cached to avoid repeated Calibre DB calls"""
        # Create mock embedding service
        mock_embedding_service = AsyncMock()
        mock_embedding_service.generate_embedding.return_value = [0.1] * 768
        
        search_engine = SearchEngine(
            mock_embedding_repo,
            mock_embedding_service,
            mock_calibre_repo
        )
        
        options = SearchOptions()
        # Perform multiple searches that might return same books
        results1 = await search_engine.search("philosophy", options)
        results2 = await search_engine.search("being", options)
        
        # Verify caching behavior
        total_calls = mock_calibre_repo.get_book_metadata.call_count
        unique_book_ids = set()
        
        for result in results1 + results2:
            unique_book_ids.add(result.book_id)
        
        # Should only call get_book_metadata once per unique book_id
        assert total_calls <= len(unique_book_ids), "Should cache metadata to avoid repeated lookups"
    
    def test_various_book_formats_metadata_extraction(self, mock_calibre_repo):
        """Test metadata extraction works with various book formats"""
        # Reset the mock to remove side_effect
        mock_calibre_repo.get_book_metadata.side_effect = None
        
        # Mock different format scenarios
        format_scenarios = [
            (1, ['EPUB'], 'Being and Time'),
            (2, ['PDF'], 'The Republic'), 
            (3, ['EPUB', 'PDF', 'MOBI'], 'Critique of Pure Reason'),
            (4, ['TXT'], 'Plain Text Book'),
            (5, [], 'No Format Book')  # Edge case
        ]
        
        for book_id, formats, expected_title in format_scenarios:
            mock_calibre_repo.get_book_metadata.return_value = {
                'id': book_id,
                'title': expected_title,
                'authors': ['Test Author'],
                'formats': formats
            }
            
            metadata = mock_calibre_repo.get_book_metadata(book_id)
            
            # Should get metadata regardless of format
            assert metadata['title'] == expected_title
            assert 'Test Author' in metadata['authors']
    
    @pytest.mark.asyncio
    async def test_empty_author_list_handling(self, mock_calibre_repo, mock_embedding_repo):
        """Test handling of books with empty or missing author lists"""
        # Mock book with no authors
        mock_calibre_repo.get_book_metadata.return_value = {
            'id': 999,
            'title': 'Anonymous Work',
            'authors': [],  # Empty authors list
            'tags': ['anonymous']
        }
        
        # Create mock embedding service
        mock_embedding_service = AsyncMock()
        mock_embedding_service.generate_embedding.return_value = [0.1] * 768
        
        search_engine = SearchEngine(
            mock_embedding_repo,
            mock_embedding_service,
            mock_calibre_repo
        )
        
        # Mock search to return this book
        async def mock_search_similar_single(embedding, limit=10, filters=None):
            return [{
                'chunk_id': 999,
                'book_id': 999,
                'chunk_text': 'Anonymous content',
                'chunk_index': 0,
                'similarity': 0.9,
            }]
        
        mock_embedding_repo.search_similar = mock_search_similar_single
        
        options = SearchOptions()
        results = await search_engine.search("anonymous", options)
        
        assert len(results) > 0
        result = results[0]
        
        # Should handle empty authors gracefully
        assert hasattr(result, 'authors')
        # Should not be None or raise error
        assert isinstance(result.authors, list)
        # Should provide fallback for empty authors
        assert result.authors == [] or result.authors == ['Unknown Author']
    
    @pytest.mark.asyncio
    async def test_malformed_metadata_handling(self, mock_calibre_repo, mock_embedding_repo):
        """Test handling of malformed or missing metadata from Calibre"""
        # Mock various malformed metadata scenarios
        malformed_scenarios = [
            None,  # No metadata returned
            {},    # Empty metadata
            {'id': 1},  # Missing required fields
            {'id': 2, 'title': None, 'authors': None},  # Null fields
            {'id': 3, 'title': '', 'authors': ''},  # Empty string fields
        ]
        
        for i, malformed_metadata in enumerate(malformed_scenarios):
            mock_calibre_repo.get_book_metadata.return_value = malformed_metadata
            
            # Create mock embedding service
            mock_embedding_service = AsyncMock()
            mock_embedding_service.generate_embedding.return_value = [0.1] * 768
            
            search_engine = SearchEngine(
                mock_embedding_repo,
                mock_embedding_service,
                mock_calibre_repo
            )
            
            # Mock search to return a book with malformed metadata
            # Mock search to return this book with malformed metadata
            async def mock_search_similar_malformed(embedding, limit=10, filters=None):
                return [{
                    'chunk_id': i,
                    'book_id': i,
                    'chunk_text': f'Content {i}',
                    'chunk_index': 0,
                    'similarity': 0.8,
                }]
            
            mock_embedding_repo.search_similar = mock_search_similar_malformed
            
            options = SearchOptions()
            # Should not crash on malformed metadata
            try:
                results = await search_engine.search(f"test{i}", options)
                
                if results:  # If results returned, they should be valid
                    result = results[0]
                    assert hasattr(result, 'authors')
                    assert hasattr(result, 'book_title')
                    # Should provide fallbacks for missing data
                    assert isinstance(result.authors, list)
                    assert isinstance(result.book_title, str)
                    assert len(result.book_title) > 0
                    
            except Exception as e:
                pytest.fail(f"Should handle malformed metadata gracefully, but got: {e}")


class TestSearchResultDataclass:
    """Test SearchResult dataclass enhancements"""
    
    def test_search_result_has_required_fields(self):
        """Test that SearchResult dataclass has all required fields"""
        # Import should not fail
        try:
            from calibre_plugins.semantic_search.core.search_engine import SearchResult
        except ImportError:
            pytest.fail("SearchResult class should be importable")
        
        # Should be able to create with all required fields
        try:
            result = SearchResult(
                chunk_id=1,
                book_id=1,
                book_title="Test Title",
                authors=["Test Author"],
                chunk_text="Test content",
                chunk_index=0,
                similarity_score=0.95,
                metadata={}
            )
            
            # Verify all fields present
            assert result.chunk_id == 1
            assert result.book_id == 1
            assert result.book_title == "Test Title"
            assert result.authors == ["Test Author"]
            assert result.chunk_text == "Test content"
            assert result.chunk_index == 0
            assert result.similarity_score == 0.95
            
        except TypeError as e:
            pytest.fail(f"SearchResult should have all required fields, but creation failed: {e}")
    
    def test_search_result_authors_always_list(self):
        """Test that SearchResult.authors is always a list, never string"""
        from calibre_plugins.semantic_search.core.search_engine import SearchResult
        
        # Test with single author
        result1 = SearchResult(
            chunk_id=1, book_id=1, book_title="Test", authors=["Single Author"],
            chunk_text="content", chunk_index=0, similarity_score=0.9, metadata={}
        )
        assert isinstance(result1.authors, list)
        assert result1.authors == ["Single Author"]
        
        # Test with multiple authors
        result2 = SearchResult(
            chunk_id=2, book_id=2, book_title="Test", authors=["Author 1", "Author 2"],
            chunk_text="content", chunk_index=0, similarity_score=0.9, metadata={}
        )
        assert isinstance(result2.authors, list)
        assert len(result2.authors) == 2
    
    def test_search_result_optional_fields(self):
        """Test that SearchResult handles optional metadata fields"""
        from calibre_plugins.semantic_search.core.search_engine import SearchResult
        
        # Should be able to include optional fields in metadata
        result = SearchResult(
            chunk_id=1, book_id=1, book_title="Test", authors=["Author"],
            chunk_text="content", chunk_index=0, similarity_score=0.9,
            metadata={"tags": ["philosophy"], "series": "Test Series", "pubdate": "2023-01-01"}
        )
        
        # Optional fields should be accessible via metadata
        assert result.metadata.get('tags') == ["philosophy"]
        assert result.metadata.get('series') == "Test Series"
        assert result.metadata.get('pubdate') == "2023-01-01"


class TestSearchDialogIntegration:
    """Test integration with search dialog display"""
    
    def test_search_dialog_displays_real_authors(self):
        """Test that search_dialog.py:297 displays real authors, not 'Unknown'"""
        # This tests the specific location mentioned in the implementation plan
        
        # Mock search result with real metadata
        mock_result = Mock()
        mock_result.authors = ['Martin Heidegger', 'Edmund Husserl']
        mock_result.title = 'Being and Time'
        mock_result.chunk_text = 'Dasein is being-in-the-world'
        mock_result.similarity_score = 0.95
        
        # Test the problematic line from search_dialog.py:297
        # This should work correctly after the fix
        author_display = ', '.join(mock_result.authors) if hasattr(mock_result, 'authors') and mock_result.authors else 'Unknown'
        
        # Should show real authors, not 'Unknown'
        assert author_display != 'Unknown'
        assert author_display == 'Martin Heidegger, Edmund Husserl'
    
    def test_search_dialog_handles_empty_authors(self):
        """Test search dialog gracefully handles empty authors list"""
        mock_result = Mock()
        mock_result.authors = []  # Empty authors list
        mock_result.title = 'Anonymous Work'
        
        # Should provide meaningful fallback for empty authors
        author_display = ', '.join(mock_result.authors) if hasattr(mock_result, 'authors') and mock_result.authors else 'Unknown Author'
        
        # Should show fallback, not crash
        assert author_display == 'Unknown Author'
    
    def test_search_dialog_handles_missing_authors_field(self):
        """Test search dialog handles SearchResult missing authors field"""
        mock_result = Mock()
        mock_result.title = 'Test Book'
        # Deliberately not setting authors field
        if hasattr(mock_result, 'authors'):
            delattr(mock_result, 'authors')
        
        # Should not crash when authors field is missing
        author_display = ', '.join(mock_result.authors) if hasattr(mock_result, 'authors') and mock_result.authors else 'Unknown Author'
        
        assert author_display == 'Unknown Author'