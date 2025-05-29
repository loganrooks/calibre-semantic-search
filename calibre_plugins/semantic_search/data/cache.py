"""
Cache management for search results and embeddings
"""

import time
import json
from typing import Dict, List, Any, Optional, Tuple
from collections import OrderedDict
import hashlib
import logging
import pickle
from pathlib import Path

logger = logging.getLogger(__name__)


class TTLCache:
    """Time-based cache with TTL support"""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        """
        Initialize TTL cache
        
        Args:
            max_size: Maximum number of items to cache
            ttl_seconds: Time to live in seconds
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache = OrderedDict()
        self._timestamps = {}
        
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache if not expired"""
        if key not in self._cache:
            return None
            
        # Check if expired
        if time.time() - self._timestamps[key] > self.ttl_seconds:
            self._evict(key)
            return None
            
        # Move to end (LRU)
        self._cache.move_to_end(key)
        return self._cache[key]
        
    def set(self, key: str, value: Any):
        """Set item in cache"""
        # Evict if at capacity
        if key not in self._cache and len(self._cache) >= self.max_size:
            # Remove oldest
            oldest_key = next(iter(self._cache))
            self._evict(oldest_key)
            
        self._cache[key] = value
        self._timestamps[key] = time.time()
        self._cache.move_to_end(key)
        
    def _evict(self, key: str):
        """Remove item from cache"""
        if key in self._cache:
            del self._cache[key]
            del self._timestamps[key]
            
    def clear(self):
        """Clear all cache entries"""
        self._cache.clear()
        self._timestamps.clear()
        
    def size(self) -> int:
        """Get current cache size"""
        return len(self._cache)
        
    def cleanup_expired(self):
        """Remove all expired entries"""
        current_time = time.time()
        expired_keys = [
            key for key, timestamp in self._timestamps.items()
            if current_time - timestamp > self.ttl_seconds
        ]
        
        for key in expired_keys:
            self._evict(key)
            
        return len(expired_keys)


class LRUCache:
    """Least Recently Used cache"""
    
    def __init__(self, max_size: int = 1000):
        """
        Initialize LRU cache
        
        Args:
            max_size: Maximum number of items to cache
        """
        self.max_size = max_size
        self._cache = OrderedDict()
        
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        if key not in self._cache:
            return None
            
        # Move to end (most recently used)
        self._cache.move_to_end(key)
        return self._cache[key]
        
    def set(self, key: str, value: Any):
        """Set item in cache"""
        if key in self._cache:
            # Update and move to end
            self._cache[key] = value
            self._cache.move_to_end(key)
        else:
            # Add new item
            if len(self._cache) >= self.max_size:
                # Remove least recently used
                self._cache.popitem(last=False)
                
            self._cache[key] = value
            
    def clear(self):
        """Clear cache"""
        self._cache.clear()
        
    def size(self) -> int:
        """Get current cache size"""
        return len(self._cache)


class CacheManager:
    """Manages multiple cache types for the search system"""
    
    def __init__(self, cache_dir: Optional[Path] = None, 
                 cache_size_mb: int = 100):
        """
        Initialize cache manager
        
        Args:
            cache_dir: Directory for persistent cache
            cache_size_mb: Maximum cache size in MB
        """
        self.cache_dir = cache_dir
        if cache_dir:
            cache_dir.mkdir(parents=True, exist_ok=True)
            
        # Estimate cache sizes based on MB limit
        # Assume average embedding is 3KB (768 floats * 4 bytes)
        max_embeddings = (cache_size_mb * 1024) // 3
        
        # Query cache - short TTL
        self.query_cache = TTLCache(max_size=1000, ttl_seconds=3600)  # 1 hour
        
        # Embedding cache - longer TTL
        self.embedding_cache = TTLCache(max_size=max_embeddings, ttl_seconds=86400)  # 24 hours
        
        # Metadata cache - LRU (no expiry)
        self.metadata_cache = LRUCache(max_size=10000)
        
        # Search result cache
        self.result_cache = TTLCache(max_size=100, ttl_seconds=1800)  # 30 minutes
        
        logger.info(f"Cache manager initialized with {cache_size_mb}MB limit")
        
    def get_query_embedding(self, query: str, model: str) -> Optional[Any]:
        """Get cached query embedding"""
        key = self._get_query_key(query, model)
        return self.query_cache.get(key)
        
    def set_query_embedding(self, query: str, model: str, embedding: Any):
        """Cache query embedding"""
        key = self._get_query_key(query, model)
        self.query_cache.set(key, embedding)
        
    def get_chunk_embedding(self, chunk_id: int) -> Optional[Any]:
        """Get cached chunk embedding"""
        key = f"chunk_{chunk_id}"
        return self.embedding_cache.get(key)
        
    def set_chunk_embedding(self, chunk_id: int, embedding: Any):
        """Cache chunk embedding"""
        key = f"chunk_{chunk_id}"
        self.embedding_cache.set(key, embedding)
        
    def get_book_metadata(self, book_id: int) -> Optional[Dict[str, Any]]:
        """Get cached book metadata"""
        key = f"book_meta_{book_id}"
        return self.metadata_cache.get(key)
        
    def set_book_metadata(self, book_id: int, metadata: Dict[str, Any]):
        """Cache book metadata"""
        key = f"book_meta_{book_id}"
        self.metadata_cache.set(key, metadata)
        
    def get_search_results(self, query: str, options_hash: str) -> Optional[List[Any]]:
        """Get cached search results"""
        key = self._get_search_key(query, options_hash)
        return self.result_cache.get(key)
        
    def set_search_results(self, query: str, options_hash: str, results: List[Any]):
        """Cache search results"""
        key = self._get_search_key(query, options_hash)
        self.result_cache.set(key, results)
        
    def _get_query_key(self, query: str, model: str) -> str:
        """Generate cache key for query embedding"""
        content = f"{model}:{query}"
        return hashlib.sha256(content.encode()).hexdigest()
        
    def _get_search_key(self, query: str, options_hash: str) -> str:
        """Generate cache key for search results"""
        content = f"search:{query}:{options_hash}"
        return hashlib.sha256(content.encode()).hexdigest()
        
    def clear_all(self):
        """Clear all caches"""
        self.query_cache.clear()
        self.embedding_cache.clear()
        self.metadata_cache.clear()
        self.result_cache.clear()
        
        if self.cache_dir and self.cache_dir.exists():
            # Clear persistent cache files
            for cache_file in self.cache_dir.glob("*.cache"):
                try:
                    cache_file.unlink()
                except Exception as e:
                    logger.error(f"Error deleting cache file {cache_file}: {e}")
                    
    def cleanup_expired(self) -> Dict[str, int]:
        """Clean up expired entries from all TTL caches"""
        stats = {
            'query_cache': self.query_cache.cleanup_expired(),
            'embedding_cache': self.embedding_cache.cleanup_expired(),
            'result_cache': self.result_cache.cleanup_expired()
        }
        
        total_cleaned = sum(stats.values())
        if total_cleaned > 0:
            logger.info(f"Cleaned up {total_cleaned} expired cache entries")
            
        return stats
        
    def get_statistics(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'query_cache': {
                'size': self.query_cache.size(),
                'max_size': self.query_cache.max_size,
                'ttl_seconds': self.query_cache.ttl_seconds
            },
            'embedding_cache': {
                'size': self.embedding_cache.size(),
                'max_size': self.embedding_cache.max_size,
                'ttl_seconds': self.embedding_cache.ttl_seconds
            },
            'metadata_cache': {
                'size': self.metadata_cache.size(),
                'max_size': self.metadata_cache.max_size
            },
            'result_cache': {
                'size': self.result_cache.size(),
                'max_size': self.result_cache.max_size,
                'ttl_seconds': self.result_cache.ttl_seconds
            }
        }
        
    def save_to_disk(self, key: str, value: Any):
        """Save cache entry to disk"""
        if not self.cache_dir:
            return
            
        cache_file = self.cache_dir / f"{key}.cache"
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(value, f)
        except Exception as e:
            logger.error(f"Error saving cache to disk: {e}")
            
    def load_from_disk(self, key: str) -> Optional[Any]:
        """Load cache entry from disk"""
        if not self.cache_dir:
            return None
            
        cache_file = self.cache_dir / f"{key}.cache"
        if not cache_file.exists():
            return None
            
        try:
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            logger.error(f"Error loading cache from disk: {e}")
            # Delete corrupted cache file
            try:
                cache_file.unlink()
            except:
                pass
            return None


class SearchResultCache:
    """Specialized cache for search results with similarity-based deduplication"""
    
    def __init__(self, similarity_threshold: float = 0.95):
        """
        Initialize search result cache
        
        Args:
            similarity_threshold: Threshold for considering queries similar
        """
        self.similarity_threshold = similarity_threshold
        self._cache = OrderedDict()
        self._embeddings = {}  # Store query embeddings for similarity
        
    def get_similar_results(self, query_embedding: Any, 
                          options_hash: str) -> Optional[List[Any]]:
        """Get results for similar query if exists"""
        # This would use actual similarity calculation
        # For now, just return None
        return None
        
    def add_results(self, query: str, query_embedding: Any, 
                   options_hash: str, results: List[Any]):
        """Add search results to cache"""
        key = f"{query}:{options_hash}"
        self._cache[key] = results
        self._embeddings[key] = query_embedding