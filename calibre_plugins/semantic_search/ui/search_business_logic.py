"""
Business logic for semantic search UI - extracted for testability

This module contains the business logic that can be tested
independently of Qt/Calibre UI dependencies.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class SearchValidationResult:
    """Result of search query validation"""

    is_valid: bool
    error_message: Optional[str] = None


class SearchQueryValidator:
    """Validates search queries according to business rules"""

    MIN_QUERY_LENGTH = 3
    MAX_QUERY_LENGTH = 5000

    def validate(self, query: Optional[str]) -> SearchValidationResult:
        """
        Validate a search query

        Args:
            query: The search query to validate

        Returns:
            SearchValidationResult with validation status
        """
        if not query or not query.strip():
            return SearchValidationResult(
                is_valid=False, error_message="Please enter a search query."
            )

        # Validate the stripped query length
        stripped_query = query.strip()
        query_length = len(stripped_query)

        if query_length < self.MIN_QUERY_LENGTH:
            return SearchValidationResult(
                is_valid=False,
                error_message=f"Query must be at least {self.MIN_QUERY_LENGTH} characters.",
            )

        if query_length > self.MAX_QUERY_LENGTH:
            return SearchValidationResult(
                is_valid=False,
                error_message=f"Query must be less than {self.MAX_QUERY_LENGTH} characters.",
            )

        return SearchValidationResult(is_valid=True)


class SearchCacheManager:
    """Manages search result caching with LRU eviction"""

    def __init__(self, max_size: int = 100):
        """
        Initialize cache manager

        Args:
            max_size: Maximum number of cached queries
        """
        self.max_size = max_size
        self._cache: Dict[str, Any] = {}

    def generate_cache_key(
        self, query: str, mode: str, scope: str, threshold: float
    ) -> str:
        """
        Generate a cache key for the search parameters

        Args:
            query: Search query
            mode: Search mode (semantic, dialectical, etc.)
            scope: Search scope (library, current_book, etc.)
            threshold: Similarity threshold

        Returns:
            Cache key string
        """
        return f"{query}:{mode}:{scope}:{threshold}"

    def get(self, cache_key: str) -> Optional[Any]:
        """Get cached results if available"""
        return self._cache.get(cache_key)

    def set(self, cache_key: str, results: Any) -> None:
        """
        Store results in cache with LRU eviction

        Args:
            cache_key: Cache key
            results: Results to cache
        """
        if cache_key and results:
            self._cache[cache_key] = results

            # Enforce size limit with FIFO eviction
            if len(self._cache) > self.max_size:
                # Remove oldest entry
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                logger.debug(f"Evicted cache entry: {oldest_key}")

    def clear(self) -> None:
        """Clear all cached results"""
        self._cache.clear()
        logger.debug("Search cache cleared")

    def size(self) -> int:
        """Get current cache size"""
        return len(self._cache)


class NavigationParameterExtractor:
    """Extracts navigation parameters from search results"""

    def extract_from_result(self, result: Any) -> Dict[str, Any]:
        """
        Extract navigation parameters from a search result

        Args:
            result: Search result object

        Returns:
            Dictionary with navigation parameters
        """
        return {
            "book_id": getattr(result, "book_id", None),
            "position": getattr(result, "chunk_index", 0),
            "highlight_text": self._truncate_text(
                getattr(result, "chunk_text", ""), max_length=100
            ),
        }

    def _truncate_text(self, text: str, max_length: int) -> str:
        """Truncate text to maximum length"""
        if text and len(text) > max_length:
            return text[:max_length]
        return text


class SearchDependencyBuilder:
    """Builds dependencies needed for search engine initialization"""

    def build_database_path(self, library_path: str) -> str:
        """
        Build the database path for embeddings

        Args:
            library_path: Calibre library path

        Returns:
            Full path to embeddings database
        """
        import os

        return os.path.join(library_path, "semantic_search", "embeddings.db")

    def enhance_config_for_performance(
        self, base_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enhance configuration with performance settings

        Args:
            base_config: Base configuration dictionary

        Returns:
            Enhanced configuration
        """
        enhanced = base_config.copy()
        enhanced.setdefault("performance", {}).update(
            {
                "cache_enabled": True,
                "batch_size": 50,  # Optimize for UI responsiveness
                "timeout": 30,  # 30 second timeout for searches
            }
        )
        return enhanced


class SearchStateManager:
    """Manages search UI state"""

    def __init__(self):
        """Initialize state manager"""
        self.is_searching = False
        self.last_query: Optional[str] = None
        self.initialization_attempted = False

    def can_initialize_engine(self) -> bool:
        """Check if search engine initialization should be attempted"""
        if self.initialization_attempted:
            logger.debug("Search engine initialization already attempted")
            return False
        return True

    def mark_initialization_attempted(self) -> None:
        """Mark that initialization has been attempted"""
        self.initialization_attempted = True

    def reset_initialization_flag(self) -> None:
        """Reset initialization flag (e.g., after error)"""
        self.initialization_attempted = False

    def start_search(self, query: str) -> None:
        """Mark search as started"""
        self.is_searching = True
        self.last_query = query

    def end_search(self) -> None:
        """Mark search as completed"""
        self.is_searching = False
