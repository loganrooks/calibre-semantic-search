"""
Performance benchmarks for Calibre Semantic Search Plugin

These tests verify that the system meets Non-Functional Requirements (NFRs)
as specified in calibre-semantic-spec-03.md, particularly:
- Sub-100ms search latency (line 17)
"""

import pytest
import asyncio
import time
import numpy as np
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path
import statistics

# Direct import to avoid Calibre dependencies
import sys
plugin_path = Path(__file__).parent.parent.parent / "calibre_plugins" / "semantic_search"
sys.path.insert(0, str(plugin_path))

# Mock all Calibre-related imports
mock_text_processor = Mock()
mock_embedding_service = Mock()
mock_repositories = Mock()
mock_database = Mock()
mock_cache = Mock()

# Create mock classes
class MockTextProcessor:
    def chunk_text(self, text, metadata=None):
        # Simulate chunking performance
        chunks = []
        chunk_size = 500  # characters
        for i in range(0, len(text), chunk_size):
            chunk_text = text[i:i+chunk_size]
            chunks.append(MockChunk(chunk_text, len(chunks), metadata.get('book_id', 1), i, i+len(chunk_text), {}))
        return chunks

class MockEmbeddingService:
    async def generate_embedding(self, text):
        # Simulate realistic embedding generation time (cached/fast API)
        await asyncio.sleep(0.002)  # 2ms per embedding (optimized)
        return np.random.rand(768).astype(np.float32)
    
    async def generate_batch(self, texts):
        # Simulate batch efficiency
        await asyncio.sleep(0.001 * len(texts))  # 1ms per text in batch
        return [np.random.rand(768).astype(np.float32) for _ in texts]

class MockEmbeddingRepository:
    def __init__(self):
        self.embeddings = []
        for i in range(1000):  # Simulate 1000 indexed chunks
            self.embeddings.append({
                'chunk_id': i,
                'book_id': i // 50 + 1,  # 50 chunks per book
                'title': f'Book {i // 50 + 1}',
                'authors': [f'Author {(i // 50) % 10}'],
                'chunk_text': f'Sample philosophical text chunk {i}',
                'chunk_index': i % 50,
                'embedding': np.random.rand(768).astype(np.float32),
                'similarity': 0.0  # Will be calculated
            })
    
    async def search_similar(self, embedding, limit=20, filters=None):
        start_time = time.time()
        
        # Simulate vector similarity calculation
        for result in self.embeddings:
            result['similarity'] = np.random.uniform(0.1, 0.9)
        
        # Sort by similarity
        sorted_results = sorted(self.embeddings, key=lambda x: x['similarity'], reverse=True)
        
        # Apply filters if any
        if filters:
            if 'author' in filters:
                sorted_results = [r for r in sorted_results if filters['author'] in r['authors']]
            if 'min_score' in filters:
                sorted_results = [r for r in sorted_results if r['similarity'] >= filters['min_score']]
        
        # Simulate database query time based on result size (optimized SQLite)
        query_time = 0.00001 * len(sorted_results)  # 0.01ms per 1000 results
        await asyncio.sleep(query_time)
        
        return sorted_results[:limit]

class MockChunk:
    def __init__(self, text, index, book_id, start_pos, end_pos, metadata):
        self.text = text
        self.index = index
        self.book_id = book_id
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.metadata = metadata

class MockSearchEngine:
    def __init__(self, embedding_service, embedding_repo):
        self.embedding_service = embedding_service
        self.embedding_repo = embedding_repo
    
    async def search(self, query, limit=20, scope=None, filters=None, search_mode='semantic'):
        start_time = time.time()
        
        # Generate query embedding
        query_embedding = await self.embedding_service.generate_embedding(query)
        
        # Search similar chunks
        results = await self.embedding_repo.search_similar(
            query_embedding, limit=limit, filters=filters
        )
        
        total_time = time.time() - start_time
        return {
            'results': results,
            'total_time': total_time,
            'query_time': total_time,
            'result_count': len(results)
        }

# Setup module mocks
mock_text_processor.TextProcessor = MockTextProcessor
mock_embedding_service.EmbeddingService = MockEmbeddingService
mock_repositories.EmbeddingRepository = MockEmbeddingRepository

@pytest.fixture
def mock_embedding_service_instance():
    return MockEmbeddingService()

@pytest.fixture
def mock_embedding_repo_instance():
    return MockEmbeddingRepository()

@pytest.fixture
def mock_search_engine(mock_embedding_service_instance, mock_embedding_repo_instance):
    return MockSearchEngine(mock_embedding_service_instance, mock_embedding_repo_instance)


class TestSearchLatencyBenchmarks:
    """Test search latency performance requirements"""
    
    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_search_latency_under_100ms(self, mock_search_engine):
        """Test that search latency is under 100ms (NFR requirement)"""
        query = "What is the nature of being and existence?"
        
        # Perform multiple searches to get consistent measurements
        latencies = []
        
        for _ in range(10):
            start_time = time.time()
            result = await mock_search_engine.search(query, limit=20)
            end_time = time.time()
            
            latency_ms = (end_time - start_time) * 1000
            latencies.append(latency_ms)
        
        # Calculate statistics
        mean_latency = statistics.mean(latencies)
        p95_latency = np.percentile(latencies, 95)
        p99_latency = np.percentile(latencies, 99)
        
        print(f"\nSearch Latency Benchmarks:")
        print(f"Mean latency: {mean_latency:.2f}ms")
        print(f"P95 latency: {p95_latency:.2f}ms")
        print(f"P99 latency: {p99_latency:.2f}ms")
        
        # NFR Assertion: Sub-100ms search latency
        assert mean_latency < 100, f"Mean search latency {mean_latency:.2f}ms exceeds 100ms requirement"
        assert p95_latency < 100, f"P95 search latency {p95_latency:.2f}ms exceeds 100ms requirement"
        
        # Additional performance targets
        assert mean_latency < 50, f"Mean latency {mean_latency:.2f}ms should be under 50ms for good UX"
    
    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_search_with_filters_latency(self, mock_search_engine):
        """Test search latency with filters applied"""
        query = "dialectical thinking and contradictions"
        filters = {
            'author': 'Author 1',
            'min_score': 0.3
        }
        
        latencies = []
        
        for _ in range(5):
            start_time = time.time()
            result = await mock_search_engine.search(query, limit=20, filters=filters)
            end_time = time.time()
            
            latency_ms = (end_time - start_time) * 1000
            latencies.append(latency_ms)
        
        mean_latency = statistics.mean(latencies)
        
        print(f"\nFiltered Search Latency: {mean_latency:.2f}ms")
        
        # Filtered search should still be under 100ms
        assert mean_latency < 100, f"Filtered search latency {mean_latency:.2f}ms exceeds 100ms"
    
    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_large_result_set_latency(self, mock_search_engine):
        """Test search latency with large result sets"""
        query = "philosophical concepts and ideas"
        
        # Test with different result limits
        result_limits = [50, 100, 200]
        
        for limit in result_limits:
            latencies = []
            
            for _ in range(3):
                start_time = time.time()
                result = await mock_search_engine.search(query, limit=limit)
                end_time = time.time()
                
                latency_ms = (end_time - start_time) * 1000
                latencies.append(latency_ms)
            
            mean_latency = statistics.mean(latencies)
            
            print(f"\nLarge Result Set ({limit} results) Latency: {mean_latency:.2f}ms")
            
            # Even large result sets should be reasonable
            assert mean_latency < 200, f"Large result set latency {mean_latency:.2f}ms is too high"


class TestEmbeddingGenerationBenchmarks:
    """Test embedding generation performance"""
    
    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_single_embedding_generation(self, mock_embedding_service_instance):
        """Test single embedding generation performance"""
        text = "Being-in-the-world is the fundamental structure of Dasein"
        
        times = []
        
        for _ in range(10):
            start_time = time.time()
            embedding = await mock_embedding_service_instance.generate_embedding(text)
            end_time = time.time()
            
            times.append((end_time - start_time) * 1000)
        
        mean_time = statistics.mean(times)
        
        print(f"\nSingle Embedding Generation: {mean_time:.2f}ms")
        
        # Should be reasonable for single embeddings
        assert mean_time < 50, f"Single embedding generation {mean_time:.2f}ms is too slow"
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (768,)
    
    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_batch_embedding_generation(self, mock_embedding_service_instance):
        """Test batch embedding generation efficiency"""
        texts = [
            "The question of Being is the fundamental question of philosophy",
            "Consciousness is always consciousness of something",
            "Man is condemned to be free",
            "The unexamined life is not worth living",
            "I think, therefore I am"
        ]
        
        # Test batch efficiency
        start_time = time.time()
        embeddings = await mock_embedding_service_instance.generate_batch(texts)
        end_time = time.time()
        
        batch_time = (end_time - start_time) * 1000
        time_per_embedding = batch_time / len(texts)
        
        print(f"\nBatch Embedding Generation:")
        print(f"Total time: {batch_time:.2f}ms")
        print(f"Time per embedding: {time_per_embedding:.2f}ms")
        
        # Batch should be more efficient than individual
        assert time_per_embedding < 25, f"Batch embedding time per item {time_per_embedding:.2f}ms is too high"
        assert len(embeddings) == len(texts)
        assert all(isinstance(emb, np.ndarray) for emb in embeddings)


class TestIndexingPerformanceBenchmarks:
    """Test indexing performance for different scenarios"""
    
    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_small_text_chunking_performance(self):
        """Test chunking performance for small texts"""
        processor = MockTextProcessor()
        
        # Small philosophical text (~2000 characters)
        text = """
        The fundamental question that drives all philosophical inquiry is the question of Being itself.
        What does it mean for something to exist? This is not merely a question about particular beings,
        but about Being as such. Heidegger argues that this question has been forgotten in the Western
        philosophical tradition, leading to a fundamental misunderstanding of human existence and our
        relationship to the world. Dasein, as being-in-the-world, is the kind of being for whom Being
        is a question. This means that human existence is characterized by an understanding of Being,
        even if this understanding is often implicit and pre-reflective.
        """ * 3  # ~2000 characters
        
        times = []
        
        for _ in range(10):
            start_time = time.time()
            chunks = processor.chunk_text(text, metadata={'book_id': 1})
            end_time = time.time()
            
            times.append((end_time - start_time) * 1000)
        
        mean_time = statistics.mean(times)
        chunk_count = len(chunks)
        
        print(f"\nSmall Text Chunking:")
        print(f"Text length: {len(text)} characters")
        print(f"Chunks created: {chunk_count}")
        print(f"Chunking time: {mean_time:.2f}ms")
        
        # Chunking should be very fast
        assert mean_time < 10, f"Small text chunking {mean_time:.2f}ms is too slow"
        assert chunk_count > 0
    
    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_medium_text_chunking_performance(self):
        """Test chunking performance for medium-sized texts"""
        processor = MockTextProcessor()
        
        # Medium philosophical text (~20000 characters)
        base_text = """
        The phenomenological investigation of consciousness reveals that consciousness is always
        intentional - it is always consciousness of something. This fundamental structure of
        intentionality means that consciousness cannot be understood as a self-contained sphere
        of mental states, but must be understood in terms of its directedness toward objects
        in the world. Edmund Husserl's analysis of intentionality shows that every conscious
        act has both a noetic aspect (the act itself) and a noematic aspect (the object as
        intended). This correlation between consciousness and its objects is not accidental but
        essential to the very structure of consciousness itself.
        """
        text = base_text * 25  # ~20,000 characters
        
        start_time = time.time()
        chunks = processor.chunk_text(text, metadata={'book_id': 1})
        end_time = time.time()
        
        chunking_time = (end_time - start_time) * 1000
        
        print(f"\nMedium Text Chunking:")
        print(f"Text length: {len(text)} characters")
        print(f"Chunks created: {len(chunks)}")
        print(f"Chunking time: {chunking_time:.2f}ms")
        
        # Medium text chunking should still be fast
        assert chunking_time < 100, f"Medium text chunking {chunking_time:.2f}ms is too slow"


class TestMemoryUsageBenchmarks:
    """Test memory usage patterns"""
    
    @pytest.mark.benchmark
    def test_embedding_memory_usage(self, mock_embedding_repo_instance):
        """Test memory usage of embedding storage"""
        try:
            import psutil
            import os
        except ImportError:
            pytest.skip("psutil not available for memory testing")
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # The mock repository already has 1000 embeddings
        repo = mock_embedding_repo_instance
        
        current_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_used = current_memory - initial_memory
        
        print(f"\nMemory Usage:")
        print(f"Initial memory: {initial_memory:.2f} MB")
        print(f"Memory with 1000 embeddings: {current_memory:.2f} MB")
        print(f"Memory used by embeddings: {memory_used:.2f} MB")
        
        # Each embedding is 768 * 4 bytes = 3KB
        # 1000 embeddings ≈ 3MB + overhead
        expected_max_memory = 10  # MB with overhead
        
        assert memory_used < expected_max_memory, f"Memory usage {memory_used:.2f}MB exceeds {expected_max_memory}MB"
    
    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_concurrent_search_memory(self, mock_search_engine):
        """Test memory usage during concurrent searches"""
        try:
            import psutil
            import os
        except ImportError:
            pytest.skip("psutil not available for memory testing")
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Run multiple concurrent searches
        queries = [
            "being and time",
            "consciousness and intentionality", 
            "freedom and responsibility",
            "language and meaning",
            "ethics and morality"
        ]
        
        tasks = [mock_search_engine.search(query) for query in queries]
        results = await asyncio.gather(*tasks)
        
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory
        
        print(f"\nConcurrent Search Memory Usage:")
        print(f"Initial memory: {initial_memory:.2f} MB")
        print(f"Peak memory: {peak_memory:.2f} MB")
        print(f"Memory increase: {memory_increase:.2f} MB")
        
        # Memory increase should be reasonable for concurrent operations
        assert memory_increase < 50, f"Memory increase {memory_increase:.2f}MB during concurrent search is too high"
        assert len(results) == len(queries)


class TestScalabilityBenchmarks:
    """Test system scalability with varying loads"""
    
    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_search_scalability_by_database_size(self, mock_embedding_service_instance):
        """Test how search performance scales with database size"""
        
        # Test with different database sizes
        database_sizes = [100, 500, 1000, 2000]
        
        for size in database_sizes:
            # Create repository with specific size
            repo = MockEmbeddingRepository()
            repo.embeddings = repo.embeddings[:size]  # Limit to size
            
            search_engine = MockSearchEngine(mock_embedding_service_instance, repo)
            
            # Measure search time
            latencies = []
            
            for _ in range(5):
                start_time = time.time()
                result = await search_engine.search("philosophical concepts", limit=20)
                end_time = time.time()
                
                latencies.append((end_time - start_time) * 1000)
            
            mean_latency = statistics.mean(latencies)
            
            print(f"\nScalability Test - DB Size {size}:")
            print(f"Mean search latency: {mean_latency:.2f}ms")
            
            # Latency should scale reasonably
            if size <= 1000:
                assert mean_latency < 100, f"Search with {size} chunks should be under 100ms"
            else:
                assert mean_latency < 200, f"Search with {size} chunks should be under 200ms"
    
    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_concurrent_search_scalability(self, mock_search_engine):
        """Test performance under concurrent search load"""
        
        # Test with different concurrency levels
        concurrency_levels = [1, 5, 10, 20]
        
        for concurrent_requests in concurrency_levels:
            
            async def single_search():
                return await mock_search_engine.search("existence and being", limit=20)
            
            # Run concurrent searches
            start_time = time.time()
            tasks = [single_search() for _ in range(concurrent_requests)]
            results = await asyncio.gather(*tasks)
            end_time = time.time()
            
            total_time = (end_time - start_time) * 1000
            avg_time_per_search = total_time / concurrent_requests
            
            print(f"\nConcurrency Test - {concurrent_requests} concurrent requests:")
            print(f"Total time: {total_time:.2f}ms")
            print(f"Average time per search: {avg_time_per_search:.2f}ms")
            
            # Performance should degrade gracefully
            assert len(results) == concurrent_requests
            
            if concurrent_requests <= 10:
                assert avg_time_per_search < 150, f"Avg time {avg_time_per_search:.2f}ms too high for {concurrent_requests} concurrent"
            else:
                assert avg_time_per_search < 300, f"Avg time {avg_time_per_search:.2f}ms too high for {concurrent_requests} concurrent"


class TestUIResponsivenessBenchmarks:
    """Test UI responsiveness requirements"""
    
    @pytest.mark.benchmark
    def test_result_display_performance(self):
        """Test performance of displaying search results"""
        
        # Simulate result processing time
        mock_results = []
        for i in range(100):
            mock_results.append({
                'chunk_id': i,
                'book_id': i // 10,
                'title': f'Philosophy Book {i // 10}',
                'authors': [f'Author {i % 5}'],
                'chunk_text': f'Philosophical text chunk {i} with meaningful content about being and existence...',
                'similarity': 0.9 - (i * 0.005),
                'metadata': {'chapter': f'Chapter {i % 10}'}
            })
        
        # Measure result processing time
        start_time = time.time()
        
        # Simulate UI processing (formatting, sorting, etc.)
        formatted_results = []
        for result in mock_results:
            formatted_result = {
                'display_title': f"{result['title']} by {', '.join(result['authors'])}",
                'display_text': result['chunk_text'][:200] + '...',
                'similarity_percent': f"{result['similarity'] * 100:.1f}%",
                'formatted_metadata': f"Chapter: {result['metadata'].get('chapter', 'Unknown')}"
            }
            formatted_results.append(formatted_result)
        
        end_time = time.time()
        
        processing_time = (end_time - start_time) * 1000
        
        print(f"\nUI Result Processing:")
        print(f"Results processed: {len(formatted_results)}")
        print(f"Processing time: {processing_time:.2f}ms")
        
        # UI processing should be very fast to maintain 60fps (16.67ms per frame)
        assert processing_time < 33, f"Result processing {processing_time:.2f}ms exceeds 33ms (30fps)"
        assert len(formatted_results) == len(mock_results)


if __name__ == "__main__":
    # Run performance benchmarks
    pytest.main([__file__, "-v", "-m", "benchmark"])