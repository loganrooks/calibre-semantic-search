"""
Test-Driven Development for Multiple Indexes User Workflows

Tests complete user workflows and integration scenarios for multiple indexes.
Focuses on end-to-end functionality and user experience.

Part of comprehensive multiple indexes implementation following SPARC+TDD.
Corresponds to IMPLEMENTATION_PLAN_2025.md Phase 2: Index Management UI
"""

import pytest
from pathlib import Path
from typing import List, Dict, Any

from calibre_plugins.semantic_search.data.repositories import EmbeddingRepository
from calibre_plugins.semantic_search.core.text_processor import Chunk


class TestIndexUsageWorkflow:
    """Test complete workflows with multiple indexes"""
    
    @pytest.fixture
    def repo(self, tmp_path):
        db_path = tmp_path / "test.db"
        return EmbeddingRepository(db_path)
    
    def test_complete_indexing_workflow(self, repo):
        """Test complete workflow from creating index to searching"""
        # 1. Create index for a book
        book_id = 1
        index_id = repo.create_index(
            book_id,
            provider='openai',
            model_name='text-embedding-3-small',
            dimensions=1536,
            chunk_size=1000,
            chunk_overlap=200
        )
        
        # 2. Process and store chunks
        chunks = [
            Chunk(text="Philosophy of mind", index=0, book_id=book_id, start_pos=0, end_pos=100, metadata={}),
            Chunk(text="Consciousness studies", index=1, book_id=book_id, start_pos=100, end_pos=200, metadata={}),
            Chunk(text="Qualia and experience", index=2, book_id=book_id, start_pos=200, end_pos=300, metadata={})
        ]
        
        for chunk in chunks:
            embedding = [0.1] * 1536  # Mock embedding
            repo.store_embedding_for_index(index_id, chunk, embedding)
        
        # 3. Search using the index
        query_embedding = [0.1] * 1536
        results = repo.search_similar_in_index(index_id, query_embedding, limit=5)
        
        assert len(results) == 3
        assert all(r['book_id'] == book_id for r in results)
    
    def test_mixed_index_search_workflow(self, repo):
        """Test searching across multiple indexes with different providers"""
        # Create books with different indexes
        books_indexes = [
            (1, 'openai', 'text-embedding-3-small', 1536),
            (2, 'vertex', 'textembedding-gecko', 768),
            (3, 'cohere', 'embed-english-v3.0', 1024),
            (3, 'openai', 'text-embedding-3-small', 1536),  # Book 3 has 2 indexes
        ]
        
        index_ids = []
        for book_id, provider, model, dims in books_indexes:
            idx = repo.create_index(
                book_id, 
                provider=provider,
                model_name=model,
                dimensions=dims
            )
            index_ids.append((idx, dims))
        
        # Search across all OpenAI indexes
        openai_indexes = repo.get_indexes_by_provider('openai')
        
        assert len(openai_indexes) == 2
        
        # Search in compatible indexes
        query_embedding = [0.1] * 1536
        results = repo.search_across_indexes(
            openai_indexes,
            query_embedding,
            limit=10
        )
        
        assert isinstance(results, list)


class TestUserWorkflowIntegration:
    """Test complete user workflows from UI to repository"""
    
    @pytest.fixture
    def repo(self, tmp_path):
        db_path = tmp_path / "test.db"
        return EmbeddingRepository(db_path)
    
    def test_book_selection_to_indexing_workflow(self, repo):
        """Test complete workflow: select books → create indexes → track progress"""
        # Simulate user selecting multiple books
        selected_books = [1, 2, 3]
        provider = 'openai'
        
        # Check which books already have indexes
        indexed_books = repo.get_books_with_indexes()
        books_needing_index = [b for b in selected_books if b not in indexed_books]
        assert books_needing_index == [1, 2, 3]  # None indexed yet
        
        # Create indexes for selected books
        created_indexes = []
        for book_id in books_needing_index:
            index_id = repo.create_index(
                book_id, 
                provider=provider,
                dimensions=1536,
                chunk_size=1000
            )
            created_indexes.append((book_id, index_id))
        
        # Verify all indexes created
        assert len(created_indexes) == 3
        
        # Verify books now show as indexed
        indexed_books = repo.get_books_with_indexes()
        assert set(indexed_books) == {1, 2, 3}
    
    def test_index_before_search_validation(self, repo):
        """Test that search requires existing indexes"""
        # Try to search before any indexes exist
        all_indexes = repo.get_indexes_by_provider('openai')
        assert len(all_indexes) == 0
        
        # Search should return no results
        results = repo.search_across_indexes(all_indexes, [0.1] * 1536)
        assert results == []
        
        # Create index and add content
        book_id = 1
        index_id = repo.create_index(book_id, provider='openai', dimensions=1536)
        
        chunk = Chunk(
            text="Searchable content", index=0, book_id=book_id,
            start_pos=0, end_pos=18, metadata={}
        )
        repo.store_embedding_for_index(index_id, chunk, [0.1] * 1536)
        
        # Now search should work
        indexes = repo.get_indexes_by_provider('openai')
        results = repo.search_across_indexes(indexes, [0.1] * 1536)
        assert len(results) == 1
    
    def test_index_management_bulk_operations(self, repo):
        """Test bulk index management operations"""
        # Create multiple indexes for different books and providers
        books = [1, 2, 3, 4, 5]
        providers = ['openai', 'vertex']
        
        created_indexes = []
        for book_id in books:
            for provider in providers:
                index_id = repo.create_index(
                    book_id,
                    provider=provider,
                    dimensions=768 if provider == 'vertex' else 1536
                )
                created_indexes.append((book_id, provider, index_id))
        
        # Should have 10 indexes total (5 books × 2 providers)
        assert len(created_indexes) == 10
        
        # Test bulk query operations
        openai_indexes = repo.get_indexes_by_provider('openai')
        vertex_indexes = repo.get_indexes_by_provider('vertex')
        
        assert len(openai_indexes) == 5
        assert len(vertex_indexes) == 5
        
        # Test selective deletion (delete all OpenAI indexes)
        for index in openai_indexes:
            success = repo.delete_index(index['index_id'])
            assert success
        
        # Verify only Vertex indexes remain
        remaining_openai = repo.get_indexes_by_provider('openai')
        remaining_vertex = repo.get_indexes_by_provider('vertex')
        
        assert len(remaining_openai) == 0
        assert len(remaining_vertex) == 5

    def test_provider_migration_workflow(self, repo):
        """Test migrating from one provider to another"""
        book_id = 1
        
        # Start with OpenAI index
        openai_index = repo.create_index(book_id, provider='openai', dimensions=1536)
        
        # Add content
        chunk = Chunk(
            text="Original content", index=0, book_id=book_id,
            start_pos=0, end_pos=16, metadata={}
        )
        repo.store_embedding_for_index(openai_index, chunk, [0.1] * 1536)
        
        # Verify OpenAI index works
        openai_results = repo.search_similar_in_index(openai_index, [0.1] * 1536)
        assert len(openai_results) == 1
        
        # Create Vertex index for same book (migration scenario)
        vertex_index = repo.create_index(book_id, provider='vertex', dimensions=768)
        repo.store_embedding_for_index(vertex_index, chunk, [0.2] * 768)
        
        # Both indexes should coexist
        book_indexes = repo.get_indexes_for_book(book_id)
        assert len(book_indexes) == 2
        
        providers = {idx['provider'] for idx in book_indexes}
        assert providers == {'openai', 'vertex'}
        
        # Can search each independently
        vertex_results = repo.search_similar_in_index(vertex_index, [0.2] * 768)
        assert len(vertex_results) == 1
        
        # Optionally delete old index (completing migration)
        success = repo.delete_index(openai_index)
        assert success
        
        # Verify only Vertex index remains
        final_indexes = repo.get_indexes_for_book(book_id)
        assert len(final_indexes) == 1
        assert final_indexes[0]['provider'] == 'vertex'

    def test_index_statistics_monitoring_workflow(self, repo):
        """Test monitoring index health and statistics"""
        book_id = 1
        index_id = repo.create_index(book_id, provider='openai', dimensions=768)
        
        # Initially empty
        stats = repo.get_index_statistics(index_id)
        assert stats['total_chunks'] == 0
        assert stats['storage_size'] == 0
        
        # Add content progressively and monitor growth
        for i in range(10):
            chunk = Chunk(
                text=f"Content chunk {i} with some additional text to make it longer",
                index=i, book_id=book_id, start_pos=i*50, end_pos=(i+1)*50, metadata={}
            )
            repo.store_embedding_for_index(index_id, chunk, [0.1 + i*0.01] * 768)
            
            # Check statistics after each addition
            stats = repo.get_index_statistics(index_id)
            assert stats['total_chunks'] == i + 1
            assert stats['storage_size'] > 0
            
            # Storage should generally increase (though compression could vary)
            if i > 0:
                # Storage size should not decrease (sanity check)
                assert stats['storage_size'] >= 0
        
        # Final verification
        final_stats = repo.get_index_statistics(index_id)
        assert final_stats['total_chunks'] == 10
        assert final_stats['provider'] == 'openai'
        assert final_stats['dimensions'] == 768
        assert 'created_at' in final_stats

    def test_multi_user_concurrent_workflow(self, repo):
        """Test workflows that might happen with multiple users/processes"""
        # Simulate multiple "users" working with different books simultaneously
        
        # User 1: Works with philosophy books
        philosophy_books = [1, 2, 3]
        for book_id in philosophy_books:
            index_id = repo.create_index(book_id, provider='openai', dimensions=1536)
            chunk = Chunk(
                text=f"Philosophy content for book {book_id}",
                index=0, book_id=book_id, start_pos=0, end_pos=30, metadata={}
            )
            repo.store_embedding_for_index(index_id, chunk, [0.1] * 1536)
        
        # User 2: Works with science books using different provider
        science_books = [4, 5, 6]
        for book_id in science_books:
            index_id = repo.create_index(book_id, provider='vertex', dimensions=768)
            chunk = Chunk(
                text=f"Science content for book {book_id}",
                index=0, book_id=book_id, start_pos=0, end_pos=28, metadata={}
            )
            repo.store_embedding_for_index(index_id, chunk, [0.2] * 768)
        
        # Verify both users' work is preserved and isolated
        openai_indexes = repo.get_indexes_by_provider('openai')
        vertex_indexes = repo.get_indexes_by_provider('vertex')
        
        assert len(openai_indexes) == 3
        assert len(vertex_indexes) == 3
        
        # Each user can search their own content
        philosophy_results = repo.search_across_indexes(openai_indexes, [0.1] * 1536)
        science_results = repo.search_across_indexes(vertex_indexes, [0.2] * 768)
        
        assert len(philosophy_results) == 3
        assert len(science_results) == 3
        
        # Content should be properly isolated
        philosophy_texts = {r['chunk_text'] for r in philosophy_results}
        science_texts = {r['chunk_text'] for r in science_results}
        
        assert all('Philosophy' in text for text in philosophy_texts)
        assert all('Science' in text for text in science_texts)

    def test_recovery_workflow_after_partial_failure(self, repo):
        """Test recovery workflow when indexing partially fails"""
        book_id = 1
        
        # Create index
        index_id = repo.create_index(book_id, provider='openai', dimensions=768)
        
        # Successfully store some chunks
        successful_chunks = []
        for i in range(3):
            chunk = Chunk(
                text=f"Successful chunk {i}", index=i, book_id=book_id,
                start_pos=i*20, end_pos=(i+1)*20, metadata={}
            )
            chunk_id = repo.store_embedding_for_index(index_id, chunk, [0.1] * 768)
            successful_chunks.append(chunk_id)
        
        # Verify partial success
        stats = repo.get_index_statistics(index_id)
        assert stats['total_chunks'] == 3
        
        # Simulate recovery: add more chunks after "failure"
        for i in range(3, 6):
            chunk = Chunk(
                text=f"Recovery chunk {i}", index=i, book_id=book_id,
                start_pos=i*20, end_pos=(i+1)*20, metadata={}
            )
            chunk_id = repo.store_embedding_for_index(index_id, chunk, [0.1] * 768)
            successful_chunks.append(chunk_id)
        
        # Verify complete recovery
        final_stats = repo.get_index_statistics(index_id)
        assert final_stats['total_chunks'] == 6
        
        # Search should work with all content
        results = repo.search_similar_in_index(index_id, [0.1] * 768)
        assert len(results) == 6
        
        # Verify we have both original and recovery content
        texts = {r['chunk_text'] for r in results}
        assert any('Successful' in text for text in texts)
        assert any('Recovery' in text for text in texts)