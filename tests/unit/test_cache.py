"""
Unit tests for cache module following TDD approach
"""

import pytest
import tempfile
import shutil
import time
from pathlib import Path
import pickle
import numpy as np
from unittest.mock import Mock, patch, mock_open

# Direct import to avoid Calibre dependencies
import sys
plugin_path = Path(__file__).parent.parent.parent / "calibre_plugins" / "semantic_search"
sys.path.insert(0, str(plugin_path))

# Import cache module directly
import importlib.util
spec = importlib.util.spec_from_file_location(
    "cache", 
    plugin_path / "data" / "cache.py"
)
cache_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cache_module)

TTLCache = cache_module.TTLCache
LRUCache = cache_module.LRUCache
CacheManager = cache_module.CacheManager
SearchResultCache = cache_module.SearchResultCache


@pytest.fixture
def temp_cache_dir():
    """Create temporary cache directory"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_embedding():
    """Create sample embedding vector"""
    return np.random.rand(768).astype(np.float32)


class TestTTLCache:
    """Test TTLCache class"""
    
    def test_ttl_cache_init(self):
        """Test TTL cache initialization"""
        cache = TTLCache(max_size=100, ttl_seconds=3600)
        
        assert cache.max_size == 100
        assert cache.ttl_seconds == 3600
        assert cache.size() == 0
        
    def test_ttl_cache_init_defaults(self):
        """Test TTL cache with default parameters"""
        cache = TTLCache()
        
        assert cache.max_size == 1000
        assert cache.ttl_seconds == 3600
        
    def test_set_and_get_basic(self):
        """Test basic set and get operations"""
        cache = TTLCache(max_size=10, ttl_seconds=3600)
        
        cache.set("key1", "value1")
        cache.set("key2", 42)
        cache.set("key3", ["list", "data"])
        
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == 42
        assert cache.get("key3") == ["list", "data"]
        assert cache.size() == 3
        
    def test_get_nonexistent_key(self):
        """Test getting non-existent key"""
        cache = TTLCache()
        
        assert cache.get("nonexistent") is None
        
    def test_ttl_expiration(self):
        """Test TTL expiration"""
        cache = TTLCache(max_size=10, ttl_seconds=1)  # 1 second TTL
        
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        
        # Wait for expiration
        time.sleep(1.1)
        assert cache.get("key1") is None
        assert cache.size() == 0
        
    def test_lru_behavior(self):
        """Test LRU behavior within TTL"""
        cache = TTLCache(max_size=3, ttl_seconds=3600)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        # Access key1 to make it most recent
        cache.get("key1")
        
        # Add key4, should evict key2 (oldest)
        cache.set("key4", "value4")
        
        assert cache.get("key1") == "value1"  # Still exists
        assert cache.get("key2") is None     # Evicted
        assert cache.get("key3") == "value3" # Still exists
        assert cache.get("key4") == "value4" # New item
        assert cache.size() == 3
        
    def test_update_existing_key(self):
        """Test updating existing key"""
        cache = TTLCache(max_size=10, ttl_seconds=3600)
        
        cache.set("key1", "value1")
        cache.set("key1", "updated_value")
        
        assert cache.get("key1") == "updated_value"
        assert cache.size() == 1
        
    def test_clear_cache(self):
        """Test clearing cache"""
        cache = TTLCache(max_size=10, ttl_seconds=3600)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        assert cache.size() == 2
        
        cache.clear()
        assert cache.size() == 0
        assert cache.get("key1") is None
        assert cache.get("key2") is None
        
    def test_cleanup_expired(self):
        """Test cleanup of expired entries"""
        cache = TTLCache(max_size=10, ttl_seconds=1)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Add new item after expiration
        cache.set("key4", "value4")
        
        # Cleanup expired
        cleaned = cache.cleanup_expired()
        
        assert cleaned == 3  # 3 expired items cleaned
        assert cache.size() == 1  # Only key4 remains
        assert cache.get("key4") == "value4"
        
    def test_evict_method(self):
        """Test internal eviction method"""
        cache = TTLCache(max_size=10, ttl_seconds=3600)
        
        cache.set("key1", "value1")
        assert cache.size() == 1
        
        cache._evict("key1")
        assert cache.size() == 0
        assert cache.get("key1") is None
        
    def test_evict_nonexistent_key(self):
        """Test evicting non-existent key"""
        cache = TTLCache(max_size=10, ttl_seconds=3600)
        
        # Should not raise error
        cache._evict("nonexistent")
        assert cache.size() == 0


class TestLRUCache:
    """Test LRUCache class"""
    
    def test_lru_cache_init(self):
        """Test LRU cache initialization"""
        cache = LRUCache(max_size=100)
        
        assert cache.max_size == 100
        assert cache.size() == 0
        
    def test_lru_cache_init_default(self):
        """Test LRU cache with default size"""
        cache = LRUCache()
        
        assert cache.max_size == 1000
        
    def test_set_and_get_basic(self):
        """Test basic set and get operations"""
        cache = LRUCache(max_size=10)
        
        cache.set("key1", "value1")
        cache.set("key2", 42)
        cache.set("key3", {"dict": "data"})
        
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == 42
        assert cache.get("key3") == {"dict": "data"}
        assert cache.size() == 3
        
    def test_get_nonexistent_key(self):
        """Test getting non-existent key"""
        cache = LRUCache()
        
        assert cache.get("nonexistent") is None
        
    def test_lru_eviction(self):
        """Test LRU eviction when at capacity"""
        cache = LRUCache(max_size=3)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        # Access key1 to make it more recent
        cache.get("key1")
        
        # Add key4, should evict key2 (least recently used)
        cache.set("key4", "value4")
        
        assert cache.get("key1") == "value1"  # Most recent, still exists
        assert cache.get("key2") is None     # Evicted (LRU)
        assert cache.get("key3") == "value3" # Still exists
        assert cache.get("key4") == "value4" # New item
        assert cache.size() == 3
        
    def test_update_existing_key(self):
        """Test updating existing key moves it to end"""
        cache = LRUCache(max_size=3)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        # Update key1 to make it most recent
        cache.set("key1", "updated_value1")
        
        # Add new key, should evict key2 (now LRU)
        cache.set("key4", "value4")
        
        assert cache.get("key1") == "updated_value1"  # Updated and recent
        assert cache.get("key2") is None              # Evicted
        assert cache.get("key3") == "value3"          # Still exists
        assert cache.get("key4") == "value4"          # New item
        
    def test_clear_cache(self):
        """Test clearing cache"""
        cache = LRUCache(max_size=10)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        assert cache.size() == 2
        
        cache.clear()
        assert cache.size() == 0
        assert cache.get("key1") is None
        assert cache.get("key2") is None


class TestCacheManager:
    """Test CacheManager class"""
    
    def test_cache_manager_init_no_dir(self):
        """Test cache manager initialization without directory"""
        manager = CacheManager(cache_dir=None, cache_size_mb=50)
        
        assert manager.cache_dir is None
        assert isinstance(manager.query_cache, TTLCache)
        assert isinstance(manager.embedding_cache, TTLCache)
        assert isinstance(manager.metadata_cache, LRUCache)
        assert isinstance(manager.result_cache, TTLCache)
        
        # Check cache configurations
        assert manager.query_cache.max_size == 1000
        assert manager.query_cache.ttl_seconds == 3600
        assert manager.embedding_cache.ttl_seconds == 86400
        assert manager.metadata_cache.max_size == 10000
        assert manager.result_cache.ttl_seconds == 1800
        
    def test_cache_manager_init_with_dir(self, temp_cache_dir):
        """Test cache manager initialization with directory"""
        manager = CacheManager(cache_dir=temp_cache_dir, cache_size_mb=100)
        
        assert manager.cache_dir == temp_cache_dir
        assert temp_cache_dir.exists()
        
    def test_query_embedding_cache(self):
        """Test query embedding caching"""
        manager = CacheManager()
        embedding = [0.1, 0.2, 0.3]
        
        # Cache miss
        assert manager.get_query_embedding("test query", "model1") is None
        
        # Set and get
        manager.set_query_embedding("test query", "model1", embedding)
        cached = manager.get_query_embedding("test query", "model1")
        
        assert cached == embedding
        
    def test_query_embedding_different_models(self):
        """Test query embeddings are separate for different models"""
        manager = CacheManager()
        embedding1 = [0.1, 0.2, 0.3]
        embedding2 = [0.4, 0.5, 0.6]
        
        manager.set_query_embedding("same query", "model1", embedding1)
        manager.set_query_embedding("same query", "model2", embedding2)
        
        assert manager.get_query_embedding("same query", "model1") == embedding1
        assert manager.get_query_embedding("same query", "model2") == embedding2
        
    def test_chunk_embedding_cache(self):
        """Test chunk embedding caching"""
        manager = CacheManager()
        embedding = np.random.rand(768)
        
        # Cache miss
        assert manager.get_chunk_embedding(123) is None
        
        # Set and get
        manager.set_chunk_embedding(123, embedding)
        cached = manager.get_chunk_embedding(123)
        
        np.testing.assert_array_equal(cached, embedding)
        
    def test_book_metadata_cache(self):
        """Test book metadata caching"""
        manager = CacheManager()
        metadata = {
            "title": "Test Book",
            "authors": ["Test Author"],
            "tags": ["Fiction"]
        }
        
        # Cache miss
        assert manager.get_book_metadata(456) is None
        
        # Set and get
        manager.set_book_metadata(456, metadata)
        cached = manager.get_book_metadata(456)
        
        assert cached == metadata
        
    def test_search_results_cache(self):
        """Test search results caching"""
        manager = CacheManager()
        results = [
            {"chunk_id": 1, "similarity": 0.9},
            {"chunk_id": 2, "similarity": 0.8}
        ]
        options_hash = "hash123"
        
        # Cache miss
        assert manager.get_search_results("test query", options_hash) is None
        
        # Set and get
        manager.set_search_results("test query", options_hash, results)
        cached = manager.get_search_results("test query", options_hash)
        
        assert cached == results
        
    def test_get_query_key(self):
        """Test query key generation"""
        manager = CacheManager()
        
        key1 = manager._get_query_key("test query", "model1")
        key2 = manager._get_query_key("test query", "model2")
        key3 = manager._get_query_key("different query", "model1")
        key4 = manager._get_query_key("test query", "model1")  # Same as key1
        
        assert key1 != key2  # Different models
        assert key1 != key3  # Different queries
        assert key1 == key4  # Same query and model
        assert len(key1) == 64  # SHA256 hex length
        
    def test_get_search_key(self):
        """Test search key generation"""
        manager = CacheManager()
        
        key1 = manager._get_search_key("test query", "options1")
        key2 = manager._get_search_key("test query", "options2")
        key3 = manager._get_search_key("different query", "options1")
        key4 = manager._get_search_key("test query", "options1")  # Same as key1
        
        assert key1 != key2  # Different options
        assert key1 != key3  # Different queries
        assert key1 == key4  # Same query and options
        assert len(key1) == 64  # SHA256 hex length
        
    def test_clear_all_caches(self):
        """Test clearing all caches"""
        manager = CacheManager()
        
        # Add data to all caches
        manager.set_query_embedding("query", "model", [0.1, 0.2])
        manager.set_chunk_embedding(123, [0.3, 0.4])
        manager.set_book_metadata(456, {"title": "Book"})
        manager.set_search_results("query", "hash", [{"result": 1}])
        
        # Verify data exists
        assert manager.get_query_embedding("query", "model") is not None
        assert manager.get_chunk_embedding(123) is not None
        assert manager.get_book_metadata(456) is not None
        assert manager.get_search_results("query", "hash") is not None
        
        # Clear all
        manager.clear_all()
        
        # Verify all cleared
        assert manager.get_query_embedding("query", "model") is None
        assert manager.get_chunk_embedding(123) is None
        assert manager.get_book_metadata(456) is None
        assert manager.get_search_results("query", "hash") is None
        
    def test_clear_all_with_cache_dir(self, temp_cache_dir):
        """Test clearing all caches including disk files"""
        # Create some cache files
        cache_file1 = temp_cache_dir / "test1.cache"
        cache_file2 = temp_cache_dir / "test2.cache"
        cache_file1.write_text("test")
        cache_file2.write_text("test")
        
        manager = CacheManager(cache_dir=temp_cache_dir)
        manager.clear_all()
        
        # Cache files should be deleted
        assert not cache_file1.exists()
        assert not cache_file2.exists()
        
    def test_cleanup_expired(self):
        """Test cleanup of expired entries"""
        manager = CacheManager()
        
        # Mock the cleanup methods to return specific counts
        manager.query_cache.cleanup_expired = Mock(return_value=2)
        manager.embedding_cache.cleanup_expired = Mock(return_value=5)
        manager.result_cache.cleanup_expired = Mock(return_value=1)
        
        stats = manager.cleanup_expired()
        
        assert stats == {
            'query_cache': 2,
            'embedding_cache': 5,
            'result_cache': 1
        }
        
        # Verify methods were called
        manager.query_cache.cleanup_expired.assert_called_once()
        manager.embedding_cache.cleanup_expired.assert_called_once()
        manager.result_cache.cleanup_expired.assert_called_once()
        
    def test_get_statistics(self):
        """Test getting cache statistics"""
        manager = CacheManager()
        
        # Add some data to get non-zero sizes
        manager.set_query_embedding("query1", "model", [0.1])
        manager.set_chunk_embedding(1, [0.2])
        manager.set_book_metadata(1, {"title": "Book"})
        manager.set_search_results("query1", "hash", [{"result": 1}])
        
        stats = manager.get_statistics()
        
        assert 'query_cache' in stats
        assert 'embedding_cache' in stats
        assert 'metadata_cache' in stats
        assert 'result_cache' in stats
        
        # Check query cache stats
        query_stats = stats['query_cache']
        assert query_stats['size'] == 1
        assert query_stats['max_size'] == 1000
        assert query_stats['ttl_seconds'] == 3600
        
        # Check metadata cache stats (no TTL)
        meta_stats = stats['metadata_cache']
        assert meta_stats['size'] == 1
        assert meta_stats['max_size'] == 10000
        assert 'ttl_seconds' not in meta_stats
        
    def test_save_to_disk_no_cache_dir(self):
        """Test save to disk when no cache directory"""
        manager = CacheManager(cache_dir=None)
        
        # Should not raise error
        manager.save_to_disk("test_key", "test_value")
        
    def test_save_to_disk_success(self, temp_cache_dir):
        """Test successful save to disk"""
        manager = CacheManager(cache_dir=temp_cache_dir)
        test_data = {"key": "value", "number": 42}
        
        manager.save_to_disk("test_key", test_data)
        
        cache_file = temp_cache_dir / "test_key.cache"
        assert cache_file.exists()
        
        # Verify content
        with open(cache_file, 'rb') as f:
            loaded_data = pickle.load(f)
        assert loaded_data == test_data
        
    def test_save_to_disk_error(self, temp_cache_dir):
        """Test save to disk with error"""
        manager = CacheManager(cache_dir=temp_cache_dir)
        
        # Mock open to raise exception
        with patch('builtins.open', side_effect=IOError("Permission denied")):
            # Should not raise error, just log
            manager.save_to_disk("test_key", "test_value")
            
    def test_load_from_disk_no_cache_dir(self):
        """Test load from disk when no cache directory"""
        manager = CacheManager(cache_dir=None)
        
        result = manager.load_from_disk("test_key")
        assert result is None
        
    def test_load_from_disk_file_not_exists(self, temp_cache_dir):
        """Test load from disk when file doesn't exist"""
        manager = CacheManager(cache_dir=temp_cache_dir)
        
        result = manager.load_from_disk("nonexistent_key")
        assert result is None
        
    def test_load_from_disk_success(self, temp_cache_dir):
        """Test successful load from disk"""
        manager = CacheManager(cache_dir=temp_cache_dir)
        test_data = {"key": "value", "list": [1, 2, 3]}
        
        # Save first
        manager.save_to_disk("test_key", test_data)
        
        # Load back
        loaded_data = manager.load_from_disk("test_key")
        assert loaded_data == test_data
        
    def test_load_from_disk_corrupted_file(self, temp_cache_dir):
        """Test load from disk with corrupted file"""
        manager = CacheManager(cache_dir=temp_cache_dir)
        
        # Create corrupted cache file
        cache_file = temp_cache_dir / "corrupted.cache"
        cache_file.write_text("not valid pickle data")
        
        result = manager.load_from_disk("corrupted")
        
        # Should return None and delete corrupted file
        assert result is None
        assert not cache_file.exists()
        
    def test_cache_size_calculation(self):
        """Test cache size calculation based on MB limit"""
        manager = CacheManager(cache_size_mb=300)  # 300MB
        
        # Should calculate max embeddings: (300 * 1024) / 3 = 102400
        expected_max_embeddings = (300 * 1024) // 3
        assert manager.embedding_cache.max_size == expected_max_embeddings


class TestSearchResultCache:
    """Test SearchResultCache class"""
    
    def test_search_result_cache_init(self):
        """Test search result cache initialization"""
        cache = SearchResultCache(similarity_threshold=0.9)
        
        assert cache.similarity_threshold == 0.9
        assert len(cache._cache) == 0
        assert len(cache._embeddings) == 0
        
    def test_search_result_cache_init_default(self):
        """Test search result cache with default threshold"""
        cache = SearchResultCache()
        
        assert cache.similarity_threshold == 0.95
        
    def test_add_results(self):
        """Test adding search results"""
        cache = SearchResultCache()
        
        query = "test query"
        embedding = np.random.rand(768)
        options_hash = "hash123"
        results = [{"chunk_id": 1, "similarity": 0.9}]
        
        cache.add_results(query, embedding, options_hash, results)
        
        expected_key = f"{query}:{options_hash}"
        assert expected_key in cache._cache
        assert expected_key in cache._embeddings
        assert cache._cache[expected_key] == results
        np.testing.assert_array_equal(cache._embeddings[expected_key], embedding)
        
    def test_get_similar_results_not_implemented(self):
        """Test get_similar_results returns None (not implemented)"""
        cache = SearchResultCache()
        
        embedding = np.random.rand(768)
        result = cache.get_similar_results(embedding, "hash123")
        
        assert result is None


class TestIntegration:
    """Integration tests for cache components"""
    
    def test_cache_manager_workflow(self, temp_cache_dir):
        """Test complete cache manager workflow"""
        manager = CacheManager(cache_dir=temp_cache_dir, cache_size_mb=10)
        
        # Test query embedding workflow
        query = "What is the meaning of life?"
        model = "sentence-transformers/all-MiniLM-L6-v2"
        embedding = np.random.rand(384).astype(np.float32)
        
        # Cache miss
        assert manager.get_query_embedding(query, model) is None
        
        # Cache hit after setting
        manager.set_query_embedding(query, model, embedding)
        cached_embedding = manager.get_query_embedding(query, model)
        np.testing.assert_array_equal(cached_embedding, embedding)
        
        # Test chunk embedding workflow
        chunk_id = 12345
        chunk_embedding = np.random.rand(768).astype(np.float32)
        
        manager.set_chunk_embedding(chunk_id, chunk_embedding)
        cached_chunk = manager.get_chunk_embedding(chunk_id)
        np.testing.assert_array_equal(cached_chunk, chunk_embedding)
        
        # Test metadata workflow
        book_id = 789
        metadata = {
            "title": "Being and Time",
            "authors": ["Martin Heidegger"],
            "year": 1927
        }
        
        manager.set_book_metadata(book_id, metadata)
        cached_metadata = manager.get_book_metadata(book_id)
        assert cached_metadata == metadata
        
        # Test search results workflow
        search_query = "existential philosophy"
        options_hash = "search_options_hash"
        results = [
            {"chunk_id": 1, "similarity": 0.95, "text": "Existential analysis..."},
            {"chunk_id": 2, "similarity": 0.87, "text": "Being-in-the-world..."}
        ]
        
        manager.set_search_results(search_query, options_hash, results)
        cached_results = manager.get_search_results(search_query, options_hash)
        assert cached_results == results
        
        # Test persistence
        test_key = "persistent_data"
        test_value = {"data": "persisted", "timestamp": time.time()}
        
        manager.save_to_disk(test_key, test_value)
        loaded_value = manager.load_from_disk(test_key)
        assert loaded_value == test_value
        
        # Test statistics
        stats = manager.get_statistics()
        assert stats['query_cache']['size'] >= 1
        assert stats['embedding_cache']['size'] >= 1
        assert stats['metadata_cache']['size'] >= 1
        assert stats['result_cache']['size'] >= 1
        
        # Test cleanup
        manager.clear_all()
        final_stats = manager.get_statistics()
        assert final_stats['query_cache']['size'] == 0
        assert final_stats['embedding_cache']['size'] == 0
        assert final_stats['metadata_cache']['size'] == 0
        assert final_stats['result_cache']['size'] == 0
        
    def test_cache_expiration_workflow(self):
        """Test cache expiration workflow"""
        # Use very short TTL for testing
        manager = CacheManager()
        manager.query_cache = TTLCache(max_size=100, ttl_seconds=1)
        manager.result_cache = TTLCache(max_size=100, ttl_seconds=1)
        
        # Add data
        manager.set_query_embedding("test", "model", [0.1, 0.2])
        manager.set_search_results("query", "hash", [{"result": 1}])
        
        # Verify data exists
        assert manager.get_query_embedding("test", "model") is not None
        assert manager.get_search_results("query", "hash") is not None
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Verify data expired
        assert manager.get_query_embedding("test", "model") is None
        assert manager.get_search_results("query", "hash") is None
        
    def test_lru_eviction_workflow(self):
        """Test LRU eviction workflow"""
        manager = CacheManager()
        manager.metadata_cache = LRUCache(max_size=2)  # Small cache for testing
        
        # Fill cache
        manager.set_book_metadata(1, {"title": "Book 1"})
        manager.set_book_metadata(2, {"title": "Book 2"})
        
        # Access book 1 to make it recent
        manager.get_book_metadata(1)
        
        # Add book 3, should evict book 2 (LRU)
        manager.set_book_metadata(3, {"title": "Book 3"})
        
        assert manager.get_book_metadata(1) is not None  # Recent, kept
        assert manager.get_book_metadata(2) is None      # Evicted
        assert manager.get_book_metadata(3) is not None  # New, kept


if __name__ == "__main__":
    pytest.main([__file__, "-v"])