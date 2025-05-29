"""
Unit tests for search engine
"""

import pytest
import numpy as np
from unittest.mock import Mock, AsyncMock, MagicMock
from typing import List, Dict, Any
import sys
from pathlib import Path

# Direct import without going through plugin __init__.py
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "calibre_plugins" / "semantic_search"))

from core.search_engine import (
    SearchEngine, SearchOptions, SearchScope, SearchMode, SearchResult
)


class MockRepository:
    """Mock repository for testing"""
    
    def __init__(self, mock_data: List[Dict[str, Any]] = None):
        self.mock_data = mock_data or []
        
    async def search_similar(self, embedding: np.ndarray, limit: int,
                           filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Mock search that returns predefined data"""
        # Simple mock: return data sorted by mock similarity
        results = []
        for item in self.mock_data:
            if self._matches_filters(item, filters):
                results.append(item)
                
        # Sort by similarity (mock)
        results.sort(key=lambda x: x.get('similarity', 0), reverse=True)
        return results[:limit]
        
    def _matches_filters(self, item: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if item matches filters"""
        if 'book_ids' in filters and item.get('book_id') not in filters['book_ids']:
            return False
        if 'author' in filters and filters['author'] not in str(item.get('authors', [])):
            return False
        return True
        
    async def get_chunk(self, chunk_id: int) -> Dict[str, Any]:
        """Get chunk by ID"""
        for item in self.mock_data:
            if item.get('chunk_id') == chunk_id:
                return item
        return None


class TestSearchResult:
    """Test SearchResult dataclass"""
    
    def test_search_result_creation(self):
        """Test creating a search result"""
        result = SearchResult(
            chunk_id=1,
            book_id=100,
            book_title="Being and Time",
            authors=["Martin Heidegger"],
            chunk_text="Dasein is being-in-the-world",
            chunk_index=5,
            similarity_score=0.85,
            metadata={'chapter': 'Introduction'}
        )
        
        assert result.chunk_id == 1
        assert result.book_id == 100
        assert result.similarity_score == 0.85
        assert result.metadata['chapter'] == 'Introduction'
        
    def test_citation_generation(self):
        """Test citation property"""
        result = SearchResult(
            chunk_id=1,
            book_id=100,
            book_title="The Republic",
            authors=["Plato"],
            chunk_text="Justice is...",
            chunk_index=10,
            similarity_score=0.9,
            metadata={}
        )
        
        assert result.citation == "Plato. The Republic."
        
        # Test with multiple authors
        result.authors = ["Karl Marx", "Friedrich Engels"]
        assert result.citation == "Karl Marx, Friedrich Engels. The Republic."


class TestSearchOptions:
    """Test SearchOptions configuration"""
    
    def test_default_options(self):
        """Test default search options"""
        options = SearchOptions()
        
        assert options.scope == SearchScope.LIBRARY
        assert options.mode == SearchMode.SEMANTIC
        assert options.limit == 20
        assert options.similarity_threshold == 0.7
        assert options.include_context is True
        
    def test_custom_options(self):
        """Test custom search options"""
        options = SearchOptions(
            scope=SearchScope.CURRENT_BOOK,
            mode=SearchMode.DIALECTICAL,
            limit=50,
            similarity_threshold=0.8,
            filters={'author': 'Kant'}
        )
        
        assert options.scope == SearchScope.CURRENT_BOOK
        assert options.mode == SearchMode.DIALECTICAL
        assert options.limit == 50
        assert options.filters['author'] == 'Kant'


class TestSearchEngine:
    """Test main search engine functionality"""
    
    @pytest.fixture
    def mock_data(self):
        """Sample data for testing"""
        return [
            {
                'chunk_id': 1,
                'book_id': 100,
                'title': 'Being and Time',
                'authors': ['Martin Heidegger'],
                'chunk_text': 'Dasein is essentially being-in-the-world',
                'chunk_index': 0,
                'similarity': 0.9,
                'metadata': {}
            },
            {
                'chunk_id': 2,
                'book_id': 100,
                'title': 'Being and Time',
                'authors': ['Martin Heidegger'],
                'chunk_text': 'The being of Dasein is care',
                'chunk_index': 1,
                'similarity': 0.85,
                'metadata': {}
            },
            {
                'chunk_id': 3,
                'book_id': 101,
                'title': 'The Republic',
                'authors': ['Plato'],
                'chunk_text': 'Justice is the harmony of the soul',
                'chunk_index': 0,
                'similarity': 0.7,
                'metadata': {}
            },
            {
                'chunk_id': 4,
                'book_id': 102,
                'title': 'Phenomenology of Spirit',
                'authors': ['G.W.F. Hegel'],
                'chunk_text': 'Being and Nothing are the same',
                'chunk_index': 0,
                'similarity': 0.8,
                'metadata': {}
            }
        ]
        
    @pytest.fixture
    def search_engine(self, mock_data):
        """Create search engine with mock data"""
        repository = MockRepository(mock_data)
        embedding_service = Mock()
        embedding_service.generate_embedding = AsyncMock(
            return_value=np.random.rand(768)
        )
        return SearchEngine(repository, embedding_service)
        
    @pytest.mark.asyncio
    async def test_basic_semantic_search(self, search_engine):
        """Test basic semantic search"""
        options = SearchOptions(limit=3)
        results = await search_engine.search("being and existence", options)
        
        assert len(results) <= 3
        assert all(isinstance(r, SearchResult) for r in results)
        # Results should be sorted by similarity
        scores = [r.similarity_score for r in results]
        assert scores == sorted(scores, reverse=True)
        
    @pytest.mark.asyncio
    async def test_empty_query(self, search_engine):
        """Test empty query handling"""
        options = SearchOptions()
        results = await search_engine.search("", options)
        assert results == []
        
        results = await search_engine.search("   ", options)
        assert results == []
        
    @pytest.mark.asyncio
    async def test_similarity_threshold(self, search_engine):
        """Test similarity threshold filtering"""
        options = SearchOptions(similarity_threshold=0.85)
        results = await search_engine.search("being", options)
        
        # All results should meet threshold
        assert all(r.similarity_score >= 0.85 for r in results)
        
    @pytest.mark.asyncio
    async def test_scope_filtering(self, search_engine):
        """Test search scope filtering"""
        # Test book scope
        options = SearchOptions(
            scope=SearchScope.CURRENT_BOOK,
            filters={'book_id': 100}
        )
        results = await search_engine.search("being", options)
        
        # All results should be from book 100
        assert all(r.book_id == 100 for r in results)
        
    @pytest.mark.asyncio
    async def test_author_filtering(self, search_engine, mock_data):
        """Test author filtering"""
        options = SearchOptions(filters={'author': 'Heidegger'})
        results = await search_engine.search("being", options)
        
        # All results should be from Heidegger
        assert all('Heidegger' in author for r in results for author in r.authors)
        
    def test_query_validation(self, search_engine):
        """Test query validation"""
        # Valid queries
        is_valid, error = search_engine.validate_query("valid query")
        assert is_valid is True
        assert error is None
        
        # Empty query
        is_valid, error = search_engine.validate_query("")
        assert is_valid is False
        assert "empty" in error.lower()
        
        # Too short
        is_valid, error = search_engine.validate_query("ab")
        assert is_valid is False
        assert "short" in error.lower()
        
        # Too long
        is_valid, error = search_engine.validate_query("x" * 6000)
        assert is_valid is False
        assert "long" in error.lower()
        
    def test_search_explanation(self, search_engine):
        """Test search explanation generation"""
        options = SearchOptions(mode=SearchMode.DIALECTICAL)
        explanation = search_engine.explain_search("freedom", options)
        
        assert "freedom" in explanation
        assert "dialectical" in explanation.lower()
        assert str(options.similarity_threshold) in explanation


class TestDialecticalSearch:
    """Test dialectical search mode"""
    
    @pytest.fixture
    def dialectical_data(self):
        """Data with dialectical oppositions"""
        return [
            {
                'chunk_id': 1,
                'book_id': 100,
                'title': 'Philosophy Book',
                'authors': ['Author'],
                'chunk_text': 'Freedom is the recognition of necessity',
                'chunk_index': 0,
                'similarity': 0.9,
                'metadata': {}
            },
            {
                'chunk_id': 2,
                'book_id': 100,
                'title': 'Philosophy Book',
                'authors': ['Author'],
                'chunk_text': 'Necessity constrains freedom',
                'chunk_index': 1,
                'similarity': 0.85,
                'metadata': {}
            },
            {
                'chunk_id': 3,
                'book_id': 100,
                'title': 'Philosophy Book',
                'authors': ['Author'],
                'chunk_text': 'Being is opposed to nothing',
                'chunk_index': 2,
                'similarity': 0.8,
                'metadata': {}
            }
        ]
        
    @pytest.mark.asyncio
    async def test_dialectical_search_finds_oppositions(self, dialectical_data):
        """Test that dialectical search finds oppositions"""
        repository = MockRepository(dialectical_data)
        embedding_service = Mock()
        
        # Mock to return different embeddings for different queries
        async def mock_embedding(text):
            if 'freedom' in text.lower():
                return np.array([1.0] + [0.0] * 767)
            elif 'necessity' in text.lower():
                return np.array([0.0, 1.0] + [0.0] * 766)
            return np.random.rand(768)
            
        embedding_service.generate_embedding = mock_embedding
        
        engine = SearchEngine(repository, embedding_service)
        options = SearchOptions(mode=SearchMode.DIALECTICAL)
        
        results = await engine.search("freedom", options)
        
        # Should find both freedom and necessity passages
        texts = [r.chunk_text for r in results]
        assert any('freedom' in t.lower() for t in texts)
        # Dialectical results should be marked
        assert any(r.metadata.get('dialectical', False) for r in results)


class TestSearchModes:
    """Test different search modes"""
    
    def test_search_mode_enum(self):
        """Test SearchMode enum values"""
        assert SearchMode.SEMANTIC.value == "semantic"
        assert SearchMode.DIALECTICAL.value == "dialectical"
        assert SearchMode.GENEALOGICAL.value == "genealogical"
        assert SearchMode.HYBRID.value == "hybrid"
        
    def test_search_scope_enum(self):
        """Test SearchScope enum values"""
        assert SearchScope.LIBRARY.value == "library"
        assert SearchScope.CURRENT_BOOK.value == "current_book"
        assert SearchScope.SELECTED_BOOKS.value == "selected_books"


class TestFindSimilar:
    """Test finding similar chunks"""
    
    @pytest.fixture
    def mock_data_with_embedding(self):
        """Sample data with embeddings for testing"""
        return [
            {
                'chunk_id': 1,
                'book_id': 100,
                'title': 'Being and Time',
                'authors': ['Martin Heidegger'],
                'chunk_text': 'Dasein is essentially being-in-the-world',
                'chunk_index': 0,
                'similarity': 0.9,
                'embedding': np.random.rand(768),
                'metadata': {}
            }
        ]
        
    @pytest.fixture
    def search_engine_for_similar(self, mock_data_with_embedding):
        """Create search engine for similar search tests"""
        repository = MockRepository(mock_data_with_embedding)
        embedding_service = Mock()
        embedding_service.generate_embedding = AsyncMock(
            return_value=np.random.rand(768)
        )
        return SearchEngine(repository, embedding_service)
    
    @pytest.mark.asyncio
    async def test_find_similar_chunks(self, search_engine_for_similar, mock_data_with_embedding):
        """Test finding similar chunks to a given chunk"""
        # Mock the repository to have a get_chunk method
        search_engine_for_similar.repository.get_chunk = AsyncMock(
            return_value=mock_data_with_embedding[0]
        )
        
        results = await search_engine_for_similar.find_similar(chunk_id=1, limit=5)
        
        # Should not include the chunk itself
        assert all(r.chunk_id != 1 for r in results)
        # Should be sorted by similarity
        scores = [r.similarity_score for r in results]
        assert scores == sorted(scores, reverse=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])