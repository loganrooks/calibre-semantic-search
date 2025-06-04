"""
Test-Driven Development for Multiple Indexes Repository Methods

Tests the repository methods for managing multiple indexes per book.
Focuses on CRUD operations, search functionality, and data integrity.

Part of comprehensive multiple indexes implementation following SPARC+TDD.
"""

import pytest
from pathlib import Path
from typing import List, Dict, Any

from calibre_plugins.semantic_search.data.repositories import EmbeddingRepository
from calibre_plugins.semantic_search.core.text_processor import Chunk


class TestMultipleIndexesRepository:
    """Test repository methods for multiple indexes"""
    
    @pytest.fixture
    def repo(self, tmp_path):
        db_path = tmp_path / "test.db"
        return EmbeddingRepository(db_path)
    
    def test_create_index_for_book(self, repo):
        """Test creating a new index for a book"""
        book_id = 1
        index_config = {
            'provider': 'openai',
            'model_name': 'text-embedding-3-small',
            'dimensions': 1536,
            'chunk_size': 1000,
            'chunk_overlap': 200
        }
        
        # This should create a new index and return its ID
        index_id = repo.create_index(book_id, **index_config)
        
        assert index_id is not None
        assert isinstance(index_id, int)
    
    def test_get_indexes_for_book(self, repo):
        """Test retrieving all indexes for a book"""
        book_id = 1
        
        # Create multiple indexes with different configurations
        configs = [
            {'provider': 'openai', 'model_name': 'text-embedding-3-small', 'dimensions': 1536},
            {'provider': 'vertex', 'model_name': 'textembedding-gecko', 'dimensions': 768},
            {'provider': 'cohere', 'model_name': 'embed-english-v3.0', 'dimensions': 1024}
        ]
        
        for config in configs:
            repo.create_index(book_id, **config)
        
        # Get all indexes for the book
        indexes = repo.get_indexes_for_book(book_id)
        
        assert len(indexes) == 3
        assert all(idx['book_id'] == book_id for idx in indexes)
        assert {idx['provider'] for idx in indexes} == {'openai', 'vertex', 'cohere'}
    
    def test_store_embedding_with_index(self, repo):
        """Test storing embeddings associated with specific index"""
        book_id = 1
        index_id = repo.create_index(
            book_id, 
            provider='openai',
            model_name='text-embedding-3-small',
            dimensions=1536
        )
        
        chunk = Chunk(
            text="Test philosophical content",
            index=0,
            book_id=book_id,
            start_pos=0,
            end_pos=100,
            metadata={'title': 'Test Book'}
        )
        
        embedding = [0.1] * 1536  # Mock embedding
        
        # Store embedding with specific index
        chunk_id = repo.store_embedding_for_index(index_id, chunk, embedding)
        
        assert chunk_id is not None
        
        # Verify it's associated with the correct index
        stored = repo.get_chunk_with_index(chunk_id)
        assert stored['index_id'] == index_id
    
    def test_search_using_specific_index(self, repo):
        """Test searching within a specific index"""
        book_id = 1
        
        # Create two different indexes
        index1 = repo.create_index(book_id, provider='openai', dimensions=1536)
        index2 = repo.create_index(book_id, provider='vertex', dimensions=768)
        
        # Add embeddings to each index
        chunk1 = Chunk(text="Philosophy content", index=0, book_id=book_id, start_pos=0, end_pos=100, metadata={})
        chunk2 = Chunk(text="Different content", index=0, book_id=book_id, start_pos=0, end_pos=100, metadata={})
        
        repo.store_embedding_for_index(index1, chunk1, [0.1] * 1536)
        repo.store_embedding_for_index(index2, chunk2, [0.2] * 768)
        
        # Search using specific index
        query_embedding = [0.15] * 1536
        results = repo.search_similar_in_index(index1, query_embedding, limit=10)
        
        assert len(results) > 0
        assert all(r['index_id'] == index1 for r in results)
    
    def test_delete_specific_index(self, repo):
        """Test deleting a specific index while preserving others"""
        book_id = 1
        
        # Create multiple indexes
        index1 = repo.create_index(book_id, provider='openai', dimensions=1536)
        index2 = repo.create_index(book_id, provider='vertex', dimensions=768)
        
        # Delete only index1
        repo.delete_index(index1)
        
        # Verify index1 is gone but index2 remains
        indexes = repo.get_indexes_for_book(book_id)
        assert len(indexes) == 1
        assert indexes[0]['index_id'] == index2
    
    def test_get_books_with_indexes(self, repo):
        """Test getting list of books that have indexes"""
        # Create indexes for some books
        repo.create_index(1, provider='openai', dimensions=1536)
        repo.create_index(3, provider='vertex', dimensions=768)
        repo.create_index(3, provider='cohere', dimensions=1024)  # Book 3 has 2 indexes
        
        books_with_indexes = repo.get_books_with_indexes()
        
        assert set(books_with_indexes) == {1, 3}
    
    def test_index_statistics(self, repo):
        """Test getting statistics for each index"""
        book_id = 1
        index_id = repo.create_index(book_id, provider='openai', dimensions=1536)
        
        # Add some chunks
        for i in range(5):
            chunk = Chunk(text=f"Chunk {i}", index=i, book_id=book_id, start_pos=i*100, end_pos=(i+1)*100, metadata={})
            repo.store_embedding_for_index(index_id, chunk, [0.1] * 1536)
        
        stats = repo.get_index_statistics(index_id)
        
        assert stats['total_chunks'] == 5
        assert stats['book_id'] == book_id
        assert stats['provider'] == 'openai'
        assert 'created_at' in stats
        assert 'storage_size' in stats

    def test_get_indexes_by_provider(self, repo):
        """Test getting all indexes for a specific provider"""
        # Create indexes for different providers
        repo.create_index(1, provider='openai', dimensions=1536)
        repo.create_index(2, provider='openai', dimensions=1536)
        repo.create_index(3, provider='vertex', dimensions=768)
        repo.create_index(4, provider='cohere', dimensions=1024)
        
        # Test provider-specific queries
        openai_indexes = repo.get_indexes_by_provider('openai')
        vertex_indexes = repo.get_indexes_by_provider('vertex')
        cohere_indexes = repo.get_indexes_by_provider('cohere')
        
        assert len(openai_indexes) == 2
        assert len(vertex_indexes) == 1
        assert len(cohere_indexes) == 1
        
        # Verify provider filtering
        assert all(idx['provider'] == 'openai' for idx in openai_indexes)
        assert all(idx['provider'] == 'vertex' for idx in vertex_indexes)

    def test_search_across_multiple_indexes(self, repo):
        """Test searching across multiple indexes with result aggregation"""
        book_id = 1
        
        # Create multiple indexes
        openai_index = repo.create_index(book_id, provider='openai', dimensions=768)
        vertex_index = repo.create_index(book_id, provider='vertex', dimensions=768)
        
        # Add content to each index
        openai_chunk = Chunk(text="OpenAI content", index=0, book_id=book_id, start_pos=0, end_pos=14, metadata={})
        vertex_chunk = Chunk(text="Vertex content", index=0, book_id=book_id, start_pos=0, end_pos=14, metadata={})
        
        repo.store_embedding_for_index(openai_index, openai_chunk, [0.1] * 768)
        repo.store_embedding_for_index(vertex_index, vertex_chunk, [0.2] * 768)
        
        # Get all indexes for searching
        all_indexes = repo.get_indexes_for_book(book_id)
        
        # Search across all indexes
        results = repo.search_across_indexes(all_indexes, [0.15] * 768, limit=10)
        
        assert len(results) == 2
        content_texts = {r['chunk_text'] for r in results}
        assert content_texts == {"OpenAI content", "Vertex content"}

    def test_mixed_dimension_compatibility(self, repo):
        """Test handling indexes with different vector dimensions"""
        book_id = 1
        
        # Create indexes with different dimensions
        index_1536 = repo.create_index(book_id, provider='openai', dimensions=1536)
        index_768 = repo.create_index(book_id, provider='vertex', dimensions=768)
        index_1024 = repo.create_index(book_id, provider='cohere', dimensions=1024)
        
        # Add embeddings with correct dimensions to each
        chunk1 = Chunk(text="Content 1", index=0, book_id=book_id, start_pos=0, end_pos=9, metadata={})
        chunk2 = Chunk(text="Content 2", index=0, book_id=book_id, start_pos=0, end_pos=9, metadata={})
        chunk3 = Chunk(text="Content 3", index=0, book_id=book_id, start_pos=0, end_pos=9, metadata={})
        
        repo.store_embedding_for_index(index_1536, chunk1, [0.1] * 1536)
        repo.store_embedding_for_index(index_768, chunk2, [0.2] * 768)
        repo.store_embedding_for_index(index_1024, chunk3, [0.3] * 1024)
        
        # Verify each index has correct data
        results_1536 = repo.search_similar_in_index(index_1536, [0.1] * 1536)
        results_768 = repo.search_similar_in_index(index_768, [0.2] * 768)
        results_1024 = repo.search_similar_in_index(index_1024, [0.3] * 1024)
        
        assert len(results_1536) == 1
        assert len(results_768) == 1
        assert len(results_1024) == 1
        
        assert results_1536[0]['chunk_text'] == "Content 1"
        assert results_768[0]['chunk_text'] == "Content 2" 
        assert results_1024[0]['chunk_text'] == "Content 3"

    def test_bulk_index_operations(self, repo):
        """Test bulk operations on multiple indexes"""
        # Create many indexes across multiple books and providers
        books = range(1, 11)  # 10 books
        providers = ['openai', 'vertex', 'cohere']
        
        created_count = 0
        for book_id in books:
            for provider in providers:
                dimensions = {'openai': 1536, 'vertex': 768, 'cohere': 1024}[provider]
                index_id = repo.create_index(book_id, provider=provider, dimensions=dimensions)
                assert index_id is not None
                created_count += 1
        
        # Should have created 30 indexes (10 books × 3 providers)
        assert created_count == 30
        
        # Test bulk queries
        all_openai = repo.get_indexes_by_provider('openai')
        all_vertex = repo.get_indexes_by_provider('vertex')
        all_cohere = repo.get_indexes_by_provider('cohere')
        
        assert len(all_openai) == 10  # 10 books with OpenAI indexes
        assert len(all_vertex) == 10   # 10 books with Vertex indexes  
        assert len(all_cohere) == 10   # 10 books with Cohere indexes
        
        # Test bulk deletion (delete all OpenAI indexes)
        for index in all_openai:
            success = repo.delete_index(index['index_id'])
            assert success
        
        # Verify deletion
        remaining_openai = repo.get_indexes_by_provider('openai')
        remaining_vertex = repo.get_indexes_by_provider('vertex')
        remaining_cohere = repo.get_indexes_by_provider('cohere')
        
        assert len(remaining_openai) == 0
        assert len(remaining_vertex) == 10  # Should remain unchanged
        assert len(remaining_cohere) == 10  # Should remain unchanged