"""
Tests for search business logic - properly isolated from UI dependencies

These tests follow proper TDD principles and can actually run!
"""

import pytest
from unittest.mock import Mock
import sys
import os

# Import directly from the module file to avoid the calibre dependency in __init__.py
module_path = os.path.join(os.path.dirname(__file__), '..', '..', 'calibre_plugins', 'semantic_search', 'ui')
sys.path.insert(0, module_path)

from search_business_logic import (
    SearchQueryValidator, SearchValidationResult,
    SearchCacheManager, NavigationParameterExtractor,
    SearchDependencyBuilder, SearchStateManager
)


class TestSearchQueryValidator:
    """Test search query validation logic"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.validator = SearchQueryValidator()
    
    def test_validate_empty_queries(self):
        """Test that empty queries are rejected"""
        # Test various empty query cases
        empty_queries = ["", "   ", "\t\n", None]
        
        for query in empty_queries:
            result = self.validator.validate(query)
            assert not result.is_valid
            assert result.error_message == "Please enter a search query."
    
    def test_validate_query_too_short(self):
        """Test that queries below minimum length are rejected"""
        short_queries = ["a", "ab", "  x  "]
        
        for query in short_queries:
            result = self.validator.validate(query)
            assert not result.is_valid
            assert "at least 3 characters" in result.error_message
    
    def test_validate_query_too_long(self):
        """Test that queries above maximum length are rejected"""
        long_query = "x" * 5001
        
        result = self.validator.validate(long_query)
        assert not result.is_valid
        assert "less than 5000 characters" in result.error_message
    
    def test_validate_valid_queries(self):
        """Test that valid queries pass validation"""
        valid_queries = [
            "abc",  # Minimum length
            "test query",  # Normal query
            "x" * 5000,  # Maximum length
            "philosophical concepts about being and nothingness"
        ]
        
        for query in valid_queries:
            result = self.validator.validate(query)
            assert result.is_valid
            assert result.error_message is None


class TestSearchCacheManager:
    """Test search result caching logic"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.cache = SearchCacheManager(max_size=3)
    
    def test_generate_cache_key(self):
        """Test cache key generation"""
        key = self.cache.generate_cache_key(
            query="test query",
            mode="semantic",
            scope="library",
            threshold=0.7
        )
        
        assert key == "test query:semantic:library:0.7"
    
    def test_cache_storage_and_retrieval(self):
        """Test storing and retrieving from cache"""
        key = "test_key"
        results = ["result1", "result2"]
        
        # Initially cache should be empty
        assert self.cache.get(key) is None
        
        # Store results
        self.cache.set(key, results)
        
        # Retrieve results
        cached = self.cache.get(key)
        assert cached == results
    
    def test_cache_lru_eviction(self):
        """Test that cache enforces size limit with LRU eviction"""
        # Add items up to limit
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        self.cache.set("key3", "value3")
        
        assert self.cache.size() == 3
        
        # Add one more - should evict oldest
        self.cache.set("key4", "value4")
        
        assert self.cache.size() == 3
        assert self.cache.get("key1") is None  # Evicted
        assert self.cache.get("key4") == "value4"  # Newest
    
    def test_cache_clear(self):
        """Test cache clearing"""
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        
        assert self.cache.size() == 2
        
        self.cache.clear()
        
        assert self.cache.size() == 0
        assert self.cache.get("key1") is None


class TestNavigationParameterExtractor:
    """Test navigation parameter extraction"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.extractor = NavigationParameterExtractor()
    
    def test_extract_from_complete_result(self):
        """Test extraction when all data is present"""
        # Mock result with all attributes
        result = Mock()
        result.book_id = 123
        result.chunk_index = 5
        result.chunk_text = "This is a long text that should be truncated after 100 characters to avoid UI overflow issues in the result display"
        
        params = self.extractor.extract_from_result(result)
        
        assert params['book_id'] == 123
        assert params['position'] == 5
        assert len(params['highlight_text']) == 100
        assert params['highlight_text'].startswith("This is a long text")
    
    def test_extract_from_partial_result(self):
        """Test extraction when some data is missing"""
        # Mock result with missing attributes
        result = Mock()
        result.book_id = 456
        # chunk_index and chunk_text are missing
        
        # Remove the missing attributes
        delattr(result, 'chunk_index')
        delattr(result, 'chunk_text')
        
        params = self.extractor.extract_from_result(result)
        
        assert params['book_id'] == 456
        assert params['position'] == 0  # Default
        assert params['highlight_text'] == ""  # Default


class TestSearchDependencyBuilder:
    """Test dependency building logic"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.builder = SearchDependencyBuilder()
    
    def test_build_database_path(self):
        """Test database path construction"""
        library_path = "/home/user/calibre/library"
        
        db_path = self.builder.build_database_path(library_path)
        
        expected = os.path.join(library_path, 'semantic_search', 'embeddings.db')
        assert db_path == expected
    
    def test_enhance_config_for_performance(self):
        """Test configuration enhancement"""
        base_config = {
            'embedding_provider': 'mock',
            'api_key': 'test_key'
        }
        
        enhanced = self.builder.enhance_config_for_performance(base_config)
        
        # Original config preserved
        assert enhanced['embedding_provider'] == 'mock'
        assert enhanced['api_key'] == 'test_key'
        
        # Performance settings added
        assert 'performance' in enhanced
        assert enhanced['performance']['cache_enabled'] is True
        assert enhanced['performance']['batch_size'] == 50
        assert enhanced['performance']['timeout'] == 30
    
    def test_enhance_config_preserves_existing_performance(self):
        """Test that existing performance settings are preserved"""
        base_config = {
            'embedding_provider': 'mock',
            'performance': {
                'cache_enabled': False,  # Should be overridden
                'custom_setting': 'preserved'  # Should be preserved
            }
        }
        
        enhanced = self.builder.enhance_config_for_performance(base_config)
        
        assert enhanced['performance']['cache_enabled'] is True  # Overridden
        assert enhanced['performance']['custom_setting'] == 'preserved'  # Preserved


class TestSearchStateManager:
    """Test search state management"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.state = SearchStateManager()
    
    def test_initialization_state(self):
        """Test initialization state management"""
        # Initially should allow initialization
        assert self.state.can_initialize_engine() is True
        
        # Mark as attempted
        self.state.mark_initialization_attempted()
        assert self.state.can_initialize_engine() is False
        
        # Reset flag
        self.state.reset_initialization_flag()
        assert self.state.can_initialize_engine() is True
    
    def test_search_state(self):
        """Test search state tracking"""
        # Initially not searching
        assert self.state.is_searching is False
        assert self.state.last_query is None
        
        # Start search
        self.state.start_search("test query")
        assert self.state.is_searching is True
        assert self.state.last_query == "test query"
        
        # End search
        self.state.end_search()
        assert self.state.is_searching is False
        assert self.state.last_query == "test query"  # Preserved


if __name__ == "__main__":
    # Run tests with simple runner for verification
    pytest.main([__file__, "-v"])