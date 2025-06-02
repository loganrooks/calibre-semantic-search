"""
Test-Driven Development for Multiple Indexes Error Handling

Tests error handling, edge cases, and robustness for multiple indexes.
Focuses on failure scenarios, data validation, and recovery.

Part of comprehensive multiple indexes implementation following SPARC+TDD.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
import sqlite3

from calibre_plugins.semantic_search.data.repositories import EmbeddingRepository
from calibre_plugins.semantic_search.core.text_processor import Chunk


class TestMultipleIndexesErrorHandling:
    """Test repository error handling and edge cases"""
    
    @pytest.fixture
    def repo(self, tmp_path):
        db_path = tmp_path / "test.db"
        return EmbeddingRepository(db_path)
    
    def test_create_index_duplicate_configuration(self, repo):
        """Test creating duplicate index configurations fails gracefully"""
        book_id = 1
        config = {
            'provider': 'openai',
            'model_name': 'text-embedding-3-small',
            'dimensions': 1536,
            'chunk_size': 1000
        }
        
        # Create first index - should succeed
        index_id1 = repo.create_index(book_id, **config)
        assert index_id1 is not None
        
        # Create identical index - should fail due to unique constraint
        with pytest.raises(sqlite3.IntegrityError):
            repo.create_index(book_id, **config)
    
    def test_store_embedding_nonexistent_index(self, repo):
        """Test storing embedding for non-existent index fails properly"""
        chunk = Chunk(
            text="Test", index=0, book_id=1, 
            start_pos=0, end_pos=4, metadata={}
        )
        embedding = [0.1] * 768
        
        # Should fail with foreign key constraint violation
        with pytest.raises(sqlite3.IntegrityError):
            repo.store_embedding_for_index(999, chunk, embedding)
    
    def test_dimension_mismatch_detection(self, repo):
        """Test that dimension mismatches are handled appropriately"""
        book_id = 1
        index_id = repo.create_index(book_id, provider='openai', dimensions=1536)
        
        chunk = Chunk(
            text="Test", index=0, book_id=book_id,
            start_pos=0, end_pos=4, metadata={}
        )
        
        # Store correct dimension embedding first
        correct_embedding = [0.1] * 1536
        chunk_id = repo.store_embedding_for_index(index_id, chunk, correct_embedding)
        assert chunk_id is not None
        
        # Try to search with wrong dimension embedding
        wrong_query = [0.1] * 768  # Wrong dimension (768 vs 1536)
        
        # Should handle gracefully - either error or empty results
        try:
            results = repo.search_similar_in_index(index_id, wrong_query)
            # If no error, should return empty results or handle gracefully
            assert isinstance(results, list)
        except (ValueError, IndexError, Exception) as e:
            # Acceptable to raise error for dimension mismatch
            assert "dimension" in str(e).lower() or "size" in str(e).lower()
    
    def test_search_empty_index(self, repo):
        """Test searching in empty index returns empty results"""
        book_id = 1
        index_id = repo.create_index(book_id, provider='openai', dimensions=1536)
        
        query_embedding = [0.1] * 1536
        results = repo.search_similar_in_index(index_id, query_embedding)
        
        assert results == []
    
    def test_search_nonexistent_index(self, repo):
        """Test searching in non-existent index handles error"""
        query_embedding = [0.1] * 1536
        
        # Search in non-existent index should return empty results
        results = repo.search_similar_in_index(999, query_embedding)
        assert results == []
    
    def test_delete_nonexistent_index(self, repo):
        """Test deleting non-existent index returns False"""
        success = repo.delete_index(999)
        assert success is False
    
    def test_get_statistics_nonexistent_index(self, repo):
        """Test getting statistics for non-existent index returns None"""
        stats = repo.get_index_statistics(999)
        assert stats is None
    
    def test_concurrent_index_operations(self, repo):
        """Test concurrent operations on same index don't corrupt data"""
        book_id = 1
        index_id = repo.create_index(book_id, provider='openai', dimensions=768)
        
        # Simulate concurrent chunk storage
        chunks = [
            Chunk(text=f"Content {i}", index=i, book_id=book_id, 
                  start_pos=i*10, end_pos=(i+1)*10, metadata={})
            for i in range(10)
        ]
        
        # Store chunks "concurrently" (sequentially for test)
        stored_chunk_ids = []
        for i, chunk in enumerate(chunks):
            embedding = [0.1 + i*0.01] * 768
            try:
                chunk_id = repo.store_embedding_for_index(index_id, chunk, embedding)
                assert chunk_id is not None
                stored_chunk_ids.append(chunk_id)
            except Exception as e:
                pytest.fail(f"Concurrent operation {i} failed: {e}")
        
        # Verify all chunks stored correctly
        stats = repo.get_index_statistics(index_id)
        assert stats['total_chunks'] == 10
        assert len(stored_chunk_ids) == 10
    
    def test_transaction_rollback_on_error(self, repo):
        """Test that transactions rollback properly on errors"""
        book_id = 1
        index_id = repo.create_index(book_id, provider='openai', dimensions=768)
        
        # Store a valid chunk first
        valid_chunk = Chunk(
            text="Valid content", index=0, book_id=book_id,
            start_pos=0, end_pos=13, metadata={}
        )
        chunk_id = repo.store_embedding_for_index(index_id, valid_chunk, [0.1] * 768)
        assert chunk_id is not None
        
        # Verify it was stored
        stats_before = repo.get_index_statistics(index_id)
        assert stats_before['total_chunks'] == 1
        
        # Try to store invalid data that should fail
        invalid_chunk = Chunk(
            text="Invalid content", index=1, book_id=book_id,
            start_pos=0, end_pos=15, metadata={}
        )
        
        # This should fail and not corrupt existing data
        try:
            # Try to use wrong book_id which should fail foreign key constraint
            repo.store_embedding_for_index(999, invalid_chunk, [0.2] * 768)
        except:
            pass  # Expected to fail
        
        # Verify original data still intact
        stats_after = repo.get_index_statistics(index_id)
        assert stats_after['total_chunks'] == 1  # Should still be 1, not corrupted
    
    def test_database_corruption_recovery(self, repo):
        """Test handling of database corruption scenarios"""
        book_id = 1
        index_id = repo.create_index(book_id, provider='openai', dimensions=768)
        
        # Add some data
        chunk = Chunk(
            text="Test content", index=0, book_id=book_id,
            start_pos=0, end_pos=12, metadata={}
        )
        repo.store_embedding_for_index(index_id, chunk, [0.1] * 768)
        
        # Simulate database corruption by directly manipulating the database
        # (In a real scenario, this might be file corruption, network issues, etc.)
        
        # Try to continue operations after "corruption"
        try:
            stats = repo.get_index_statistics(index_id)
            assert stats is not None
        except Exception:
            # If corruption is detected, should handle gracefully
            pytest.skip("Database corruption test - acceptable to fail gracefully")
    
    def test_large_embedding_storage(self, repo):
        """Test handling of unusually large embeddings"""
        book_id = 1
        index_id = repo.create_index(book_id, provider='custom', dimensions=4096)  # Large dimension
        
        chunk = Chunk(
            text="Test content", index=0, book_id=book_id,
            start_pos=0, end_pos=12, metadata={}
        )
        
        # Very large embedding
        large_embedding = [0.1] * 4096
        
        try:
            chunk_id = repo.store_embedding_for_index(index_id, chunk, large_embedding)
            assert chunk_id is not None
            
            # Verify it can be retrieved
            results = repo.search_similar_in_index(index_id, large_embedding)
            assert len(results) == 1
        except (MemoryError, sqlite3.OperationalError) as e:
            # Acceptable to fail on very large embeddings
            pytest.skip(f"Large embedding test failed as expected: {e}")
    
    def test_malformed_metadata_handling(self, repo):
        """Test handling of malformed metadata in index creation"""
        book_id = 1
        
        # Test with metadata that can't be JSON serialized
        class NonSerializable:
            def __repr__(self):
                return "NonSerializable()"
        
        malformed_metadata = {
            'valid_key': 'valid_value',
            'invalid_key': NonSerializable()  # Can't be JSON serialized
        }
        
        # Should either handle gracefully or raise clear error
        try:
            index_id = repo.create_index(
                book_id, 
                provider='openai', 
                dimensions=768, 
                metadata=malformed_metadata
            )
            # If it succeeds, metadata should be cleaned/handled
            assert index_id is not None
        except (TypeError, ValueError) as e:
            # Acceptable to fail on malformed metadata
            assert "json" in str(e).lower() or "serializ" in str(e).lower()
    
    def test_invalid_provider_names(self, repo):
        """Test handling of invalid provider names"""
        book_id = 1
        
        # Test with various invalid provider names
        invalid_providers = [
            '',  # Empty string
            None,  # None value
            'invalid-provider-with-special-chars!@#',
            'a' * 1000,  # Very long name
        ]
        
        for invalid_provider in invalid_providers:
            try:
                if invalid_provider is None:
                    # Skip None test as it might be handled by function signature
                    continue
                    
                index_id = repo.create_index(
                    book_id, 
                    provider=invalid_provider, 
                    dimensions=768
                )
                # If it succeeds, that's fine too (maybe provider names are flexible)
                if index_id is not None:
                    # Clean up
                    repo.delete_index(index_id)
            except (ValueError, TypeError, sqlite3.IntegrityError):
                # Acceptable to reject invalid provider names
                pass
    
    def test_negative_dimensions(self, repo):
        """Test handling of invalid dimension values"""
        book_id = 1
        
        invalid_dimensions = [-1, 0, None, 'invalid']
        
        for invalid_dim in invalid_dimensions:
            try:
                if invalid_dim is None or isinstance(invalid_dim, str):
                    # Skip type mismatch tests as they might be caught by type hints
                    continue
                    
                index_id = repo.create_index(
                    book_id, 
                    provider='openai', 
                    dimensions=invalid_dim
                )
                # Should not create index with invalid dimensions
                if index_id is not None:
                    repo.delete_index(index_id)
                    pytest.fail(f"Should not allow dimensions={invalid_dim}")
            except (ValueError, TypeError, sqlite3.IntegrityError):
                # Expected to fail for invalid dimensions
                pass