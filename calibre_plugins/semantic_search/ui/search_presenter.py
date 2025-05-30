"""
Search Dialog Presenter - Coordinates UI and business logic

This presenter implements the integration layer between the UI
and the business logic, following the MVP pattern.
"""

import asyncio
import logging
import os
from typing import Any, Optional, Dict
from unittest.mock import Mock  # Temporary - will be removed when real implementation is connected

logger = logging.getLogger(__name__)


class SearchDialogPresenter:
    """Presenter that coordinates between UI view and business logic"""
    
    def __init__(self, view, search_engine, validator, cache):
        """
        Initialize presenter with dependencies
        
        Args:
            view: UI view interface
            search_engine: Search engine for executing searches
            validator: Query validator
            cache: Cache manager for results
        """
        self.view = view
        self.search_engine = search_engine
        self.validator = validator
        self.cache = cache
    
    def perform_search(self, query: str, options: Any) -> None:
        """
        Perform a search with the given query and options
        
        This is the minimal implementation to pass our test.
        
        Args:
            query: Search query text
            options: Search options (mode, scope, threshold, etc.)
        """
        # 1. Validate query (using real validator)
        validation = self.validator.validate(query)
        if not validation.is_valid:
            self.view.show_validation_error(validation.error_message)
            return
        
        # 2. Generate cache key
        cache_key = self.cache.generate_cache_key(
            query, options.mode, options.scope, options.similarity_threshold
        )
        
        # 3. Check cache
        cached_results = self.cache.get(cache_key)
        if cached_results is not None:
            self.view.display_results(cached_results)
            return
        
        # 4. Show progress
        self.view.show_search_progress()
        
        try:
            # 5. Execute search (minimal sync wrapper for now)
            # In real implementation, this would be properly async
            results = asyncio.run(self.search_engine.search(query, options))
            
            # 6. Display results
            self.view.display_results(results)
            
            # 7. Cache results
            self.cache.set(cache_key, results)
            
        except Exception as e:
            # Handle search errors gracefully
            logger.error(f"Search error: {e}")
            self.view.show_search_error(str(e))


class SearchEngineFactory:
    """Factory for creating search engine with all dependencies"""
    
    def __init__(self, library_path: str, calibre_api: Any, config: Dict[str, Any]):
        """
        Initialize factory with configuration
        
        Args:
            library_path: Path to Calibre library
            calibre_api: Calibre database API
            config: Configuration dictionary
        """
        self.library_path = library_path
        self.calibre_api = calibre_api
        self.config = config
    
    def create_search_engine(self) -> Any:
        """
        Create search engine with all dependencies
        
        Returns:
            Configured search engine instance
        """
        # Create dependencies in order
        embedding_repo = self._create_embedding_repository()
        calibre_repo = self._create_calibre_repository()
        embedding_service = self._create_embedding_service()
        
        # Create and return search engine
        return self._create_search_engine(embedding_repo, embedding_service)
    
    def _create_embedding_repository(self) -> Any:
        """Create embedding repository"""
        # Create database directory if it doesn't exist
        db_dir = os.path.join(self.library_path, 'semantic_search')
        if not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        
        # Create database path
        db_path = os.path.join(db_dir, 'embeddings.db')
        
        # Import and create repository
        # For now, return a mock since we can't import the real class
        # This will be replaced when we connect the real implementation
        return Mock(db_path=db_path)
    
    def _create_calibre_repository(self) -> Any:
        """Create calibre repository"""
        # Minimal implementation for test
        pass
    
    def _create_embedding_service(self) -> Any:
        """Create embedding service"""
        # Minimal implementation for test
        pass
    
    def _create_search_engine(self, embedding_repo: Any, embedding_service: Any) -> Any:
        """Create search engine"""
        # Minimal implementation for test
        pass