"""
Test-Driven Development for Multiple Indexes Performance

Tests performance and scalability scenarios for multiple indexes.
Focuses on response times, memory usage, and large-scale operations.

Part of comprehensive multiple indexes implementation following SPARC+TDD.
Corresponds to IMPLEMENTATION_PLAN_2025.md Phase 3: Performance Optimizations
"""

import pytest
from pathlib import Path
from datetime import datetime
import time

from calibre_plugins.semantic_search.data.repositories import EmbeddingRepository
from calibre_plugins.semantic_search.core.text_processor import Chunk


class TestPerformanceAndScalability:
    """Test performance and scalability scenarios"""
    
    @pytest.fixture
    def repo(self, tmp_path):
        db_path = tmp_path / "test.db"
        return EmbeddingRepository(db_path)
    
    def test_large_number_indexes_creation_performance(self, repo):
        """Test performance with creating many indexes"""
        # Create 50 books with 3 providers each = 150 indexes
        num_books = 50
        providers = ['openai', 'vertex', 'cohere']
        
        start_time = time.time()
        
        created_indexes = []
        for book_id in range(1, num_books + 1):
            for provider in providers:
                dimensions = {'openai': 1536, 'vertex': 768, 'cohere': 1024}[provider]
                index_id = repo.create_index(book_id, provider=provider, dimensions=dimensions)
                created_indexes.append(index_id)
        
        creation_time = time.time() - start_time
        
        # Should complete in reasonable time (adjust threshold as needed)
        assert creation_time < 10.0  # 10 seconds for 150 indexes
        
        # Verify all created
        assert len(created_indexes) == 150
        
        # Test query performance with many indexes
        openai_indexes = repo.get_indexes_by_provider('openai')
        vertex_indexes = repo.get_indexes_by_provider('vertex')
        cohere_indexes = repo.get_indexes_by_provider('cohere')
        
        assert len(openai_indexes) == 50
        assert len(vertex_indexes) == 50
        assert len(cohere_indexes) == 50
    
    def test_search_performance_many_indexes(self, repo):
        """Test search performance across many populated indexes"""
        # Create multiple indexes with content
        num_books = 20
        providers = ['openai', 'vertex']
        
        # Setup phase
        setup_start = time.time()
        
        for book_id in range(1, num_books + 1):
            for provider in providers:
                dimensions = {'openai': 1536, 'vertex': 768}[provider]
                index_id = repo.create_index(book_id, provider=provider, dimensions=dimensions)
                
                # Add multiple chunks to each index
                for chunk_idx in range(5):
                    chunk = Chunk(
                        text=f"Book {book_id} {provider} chunk {chunk_idx} with substantial content to make search meaningful",
                        index=chunk_idx, book_id=book_id,
                        start_pos=chunk_idx*100, end_pos=(chunk_idx+1)*100,
                        metadata={'book_title': f'Book {book_id}', 'provider': provider}
                    )
                    embedding = [0.1 + book_id*0.001 + chunk_idx*0.0001] * dimensions
                    repo.store_embedding_for_index(index_id, chunk, embedding)
        
        setup_time = time.time() - setup_start
        print(f"Setup time for {num_books*2} indexes with {num_books*2*5} chunks: {setup_time:.2f}s")
        
        # Test search performance
        search_start = time.time()
        
        openai_indexes = repo.get_indexes_by_provider('openai')
        results = repo.search_across_indexes(openai_indexes, [0.1] * 1536, limit=20)
        
        search_time = time.time() - search_start
        
        # Should complete search quickly
        assert search_time < 5.0  # 5 seconds max for search across 20 indexes
        assert len(results) > 0
        assert len(results) <= 20  # Should respect limit
        
        print(f"Search time across {len(openai_indexes)} indexes: {search_time:.3f}s")
    
    def test_bulk_deletion_performance(self, repo):
        """Test performance of bulk deletion operations"""
        # Create many indexes
        num_books = 30
        providers = ['openai', 'vertex', 'cohere']
        
        # Create all indexes
        for book_id in range(1, num_books + 1):
            for provider in providers:
                dimensions = {'openai': 1536, 'vertex': 768, 'cohere': 1024}[provider]
                index_id = repo.create_index(book_id, provider=provider, dimensions=dimensions)
                
                # Add content to make deletion more realistic
                chunk = Chunk(
                    text=f"Content for book {book_id} provider {provider}",
                    index=0, book_id=book_id, start_pos=0, end_pos=30, metadata={}
                )
                repo.store_embedding_for_index(index_id, chunk, [0.1] * dimensions)
        
        # Test bulk deletion performance
        openai_indexes = repo.get_indexes_by_provider('openai')
        assert len(openai_indexes) == num_books
        
        deletion_start = time.time()
        
        # Delete all OpenAI indexes
        for index in openai_indexes:
            success = repo.delete_index(index['index_id'])
            assert success
        
        deletion_time = time.time() - deletion_start
        
        # Should complete deletion quickly
        assert deletion_time < 5.0  # 5 seconds for 30 deletions
        
        # Verify deletion worked
        remaining_openai = repo.get_indexes_by_provider('openai')
        assert len(remaining_openai) == 0
        
        print(f"Bulk deletion time for {num_books} indexes: {deletion_time:.3f}s")
    
    def test_memory_usage_with_large_embeddings(self, repo):
        """Test memory usage doesn't grow excessively with large embeddings"""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        book_id = 1
        
        # Create indexes with progressively larger dimensions
        dimension_sizes = [768, 1536, 2048, 4096]
        
        for i, dimensions in enumerate(dimension_sizes):
            index_id = repo.create_index(book_id + i, provider=f'test_{dimensions}', dimensions=dimensions)
            
            # Add multiple chunks with large embeddings
            for chunk_idx in range(10):
                chunk = Chunk(
                    text=f"Large embedding test content {chunk_idx} " * 20,  # Make text substantial
                    index=chunk_idx, book_id=book_id + i,
                    start_pos=chunk_idx*500, end_pos=(chunk_idx+1)*500, metadata={}
                )
                large_embedding = [0.1 + chunk_idx*0.01] * dimensions
                repo.store_embedding_for_index(index_id, chunk, large_embedding)
        
        # Check memory usage after operations
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (adjust threshold as needed)
        assert memory_increase < 500  # Less than 500MB increase
        
        print(f"Memory usage: {initial_memory:.1f}MB → {final_memory:.1f}MB (+{memory_increase:.1f}MB)")
    
    def test_concurrent_operations_performance(self, repo):
        """Test performance under simulated concurrent operations"""
        import threading
        import queue
        
        num_threads = 5
        operations_per_thread = 10
        results_queue = queue.Queue()
        
        def worker_operations(thread_id):
            """Simulate concurrent user operations"""
            start_time = time.time()
            
            try:
                # Each thread works with different book IDs to avoid conflicts
                base_book_id = thread_id * 100
                
                for i in range(operations_per_thread):
                    book_id = base_book_id + i
                    
                    # Create index
                    index_id = repo.create_index(book_id, provider='openai', dimensions=768)
                    
                    # Add content
                    chunk = Chunk(
                        text=f"Thread {thread_id} content {i}",
                        index=0, book_id=book_id, start_pos=0, end_pos=20, metadata={}
                    )
                    repo.store_embedding_for_index(index_id, chunk, [0.1 + thread_id*0.01] * 768)
                    
                    # Perform search
                    results = repo.search_similar_in_index(index_id, [0.1 + thread_id*0.01] * 768)
                    assert len(results) == 1
                
                end_time = time.time()
                results_queue.put((thread_id, end_time - start_time, None))
                
            except Exception as e:
                end_time = time.time()
                results_queue.put((thread_id, end_time - start_time, str(e)))
        
        # Start all threads
        threads = []
        overall_start = time.time()
        
        for thread_id in range(num_threads):
            thread = threading.Thread(target=worker_operations, args=(thread_id,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=30)  # 30 second timeout
            if thread.is_alive():
                pytest.fail("Thread did not complete within timeout")
        
        overall_time = time.time() - overall_start
        
        # Collect results
        thread_results = []
        while not results_queue.empty():
            thread_results.append(results_queue.get())
        
        assert len(thread_results) == num_threads
        
        # Check that all threads completed successfully
        for thread_id, duration, error in thread_results:
            if error:
                pytest.fail(f"Thread {thread_id} failed: {error}")
            
            # Each thread should complete in reasonable time
            assert duration < 15.0  # 15 seconds per thread
        
        print(f"Concurrent operations: {num_threads} threads, {operations_per_thread} ops each, total time: {overall_time:.2f}s")
    
    def test_index_statistics_performance(self, repo):
        """Test performance of statistics calculations on large indexes"""
        book_id = 1
        index_id = repo.create_index(book_id, provider='openai', dimensions=768)
        
        # Add many chunks to make statistics calculation meaningful
        num_chunks = 100
        
        for i in range(num_chunks):
            chunk = Chunk(
                text=f"Performance test chunk {i} with enough content to make it realistic " * 5,
                index=i, book_id=book_id, start_pos=i*300, end_pos=(i+1)*300, metadata={}
            )
            repo.store_embedding_for_index(index_id, chunk, [0.1 + i*0.001] * 768)
        
        # Test statistics calculation performance
        stats_start = time.time()
        
        for _ in range(10):  # Multiple calls to test consistency
            stats = repo.get_index_statistics(index_id)
            assert stats['total_chunks'] == num_chunks
            assert stats['storage_size'] > 0
        
        stats_time = time.time() - stats_start
        
        # Statistics should be calculated quickly even with many chunks
        assert stats_time < 2.0  # 2 seconds for 10 statistics calculations
        
        print(f"Statistics calculation time for {num_chunks} chunks (10 calls): {stats_time:.3f}s")
    
    def test_database_size_growth_patterns(self, repo):
        """Test database size growth patterns with multiple indexes"""
        db_path = repo.db.db_path
        
        # Get initial database size
        initial_size = db_path.stat().st_size if db_path.exists() else 0
        
        # Add indexes and content in stages, measuring growth
        sizes = [initial_size]
        
        for stage in range(5):
            # Add 10 books with 2 providers each in this stage
            for book_id in range(stage*10 + 1, (stage+1)*10 + 1):
                for provider in ['openai', 'vertex']:
                    dimensions = {'openai': 1536, 'vertex': 768}[provider]
                    index_id = repo.create_index(book_id, provider=provider, dimensions=dimensions)
                    
                    # Add content
                    for chunk_idx in range(3):
                        chunk = Chunk(
                            text=f"Stage {stage} book {book_id} {provider} chunk {chunk_idx} content",
                            index=chunk_idx, book_id=book_id,
                            start_pos=chunk_idx*50, end_pos=(chunk_idx+1)*50, metadata={}
                        )
                        repo.store_embedding_for_index(index_id, chunk, [0.1] * dimensions)
            
            # Measure database size after this stage
            current_size = db_path.stat().st_size
            sizes.append(current_size)
            print(f"Stage {stage}: DB size = {current_size / 1024:.1f}KB")
        
        # Database should grow roughly linearly (within reason)
        growth_rates = []
        for i in range(1, len(sizes)):
            if sizes[i-1] > 0:
                growth_rate = (sizes[i] - sizes[i-1]) / sizes[i-1]
                growth_rates.append(growth_rate)
        
        # Growth should be consistent (no exponential growth or corruption)
        if len(growth_rates) > 1:
            max_growth = max(growth_rates)
            min_growth = min(growth_rates)
            assert max_growth < 10.0  # No more than 10x growth in any stage
            
        print(f"Final database size: {sizes[-1] / 1024:.1f}KB")
        
        # Final size should be reasonable for the amount of data
        # 50 books × 2 providers × 3 chunks × (text + embedding) should be manageable
        assert sizes[-1] < 50 * 1024 * 1024  # Less than 50MB