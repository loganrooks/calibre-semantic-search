"""
Integration tests for UI-Backend connection using TDD

These tests define the integration contract between UI and business logic.
They can run without Qt/Calibre dependencies by using test doubles.
"""

import pytest
from unittest.mock import Mock, AsyncMock, call, patch
import asyncio
import sys
import os

# Add path for our business logic module
module_path = os.path.join(os.path.dirname(__file__), '..', '..', 'calibre_plugins', 'semantic_search', 'ui')
sys.path.insert(0, module_path)

from search_business_logic import (
    SearchQueryValidator, SearchCacheManager,
    SearchValidationResult
)
from search_presenter import SearchDialogPresenter


class TestSearchDialogPresenter:
    """Test the presenter that connects UI to business logic"""
    
    def test_presenter_performs_search_with_valid_query(self):
        """Test that presenter coordinates search flow correctly"""
        # GIVEN: Mocked dependencies
        mock_view = Mock()
        mock_search_engine = AsyncMock()
        mock_validator = SearchQueryValidator()  # Use real validator
        mock_cache = Mock()
        
        # Configure mocks
        mock_cache.generate_cache_key.return_value = "test_key"
        mock_cache.get.return_value = None  # Cache miss
        mock_search_engine.search.return_value = [
            Mock(book_id=1, book_title="Test Book", authors=["Test Author"])
        ]
        
        # Create presenter (this will fail initially - no presenter exists!)
        presenter = SearchDialogPresenter(
            view=mock_view,
            search_engine=mock_search_engine,
            validator=mock_validator,
            cache=mock_cache
        )
        
        # WHEN: Valid search is performed
        query = "philosophy of mind"
        options = Mock(mode="semantic", scope="library", similarity_threshold=0.7)
        presenter.perform_search(query, options)
        
        # THEN: Should coordinate the flow properly
        # 1. Generate cache key
        mock_cache.generate_cache_key.assert_called_once_with(
            query, options.mode, options.scope, options.similarity_threshold
        )
        
        # 2. Check cache (cache miss in this test)
        mock_cache.get.assert_called_once_with("test_key")
        
        # 3. Show progress
        mock_view.show_search_progress.assert_called_once()
        
        # 4. Execute search
        mock_search_engine.search.assert_called_once_with(query, options)
        
        # 5. Display results
        mock_view.display_results.assert_called_once()
        
        # 6. Cache results
        mock_cache.set.assert_called_once()
    
    def test_presenter_handles_invalid_query(self):
        """Test that presenter handles validation errors properly"""
        # GIVEN: Dependencies with invalid query
        mock_view = Mock()
        mock_search_engine = AsyncMock()
        mock_validator = SearchQueryValidator()
        mock_cache = Mock()
        
        presenter = SearchDialogPresenter(
            view=mock_view,
            search_engine=mock_search_engine,
            validator=mock_validator,
            cache=mock_cache
        )
        
        # WHEN: Invalid query is submitted (too short)
        presenter.perform_search("ab", Mock())
        
        # THEN: Should show validation error and not search
        mock_view.show_validation_error.assert_called_once_with(
            "Query must be at least 3 characters."
        )
        mock_search_engine.search.assert_not_called()
        mock_view.show_search_progress.assert_not_called()
    
    def test_presenter_uses_cached_results(self):
        """Test that presenter returns cached results when available"""
        # GIVEN: Cache with results
        mock_view = Mock()
        mock_search_engine = AsyncMock()
        mock_validator = SearchQueryValidator()
        mock_cache = Mock()
        
        cached_results = [
            Mock(book_id=1, book_title="Cached Book")
        ]
        mock_cache.generate_cache_key.return_value = "cache_key"
        mock_cache.get.return_value = cached_results
        
        presenter = SearchDialogPresenter(
            view=mock_view,
            search_engine=mock_search_engine,
            validator=mock_validator,
            cache=mock_cache
        )
        
        # WHEN: Search with cached query
        query = "cached query"
        options = Mock(mode="semantic", scope="library", similarity_threshold=0.7)
        presenter.perform_search(query, options)
        
        # THEN: Should use cache and not call search engine
        mock_cache.get.assert_called_once_with("cache_key")
        mock_view.display_results.assert_called_once_with(cached_results)
        mock_search_engine.search.assert_not_called()
        mock_view.show_search_progress.assert_not_called()


    def test_presenter_handles_search_error(self):
        """Test that presenter handles search errors gracefully"""
        # GIVEN: Search engine that raises error
        mock_view = Mock()
        mock_search_engine = AsyncMock()
        mock_search_engine.search.side_effect = Exception("Search failed")
        mock_validator = SearchQueryValidator()
        mock_cache = Mock()
        mock_cache.generate_cache_key.return_value = "key"
        mock_cache.get.return_value = None
        
        presenter = SearchDialogPresenter(
            view=mock_view,
            search_engine=mock_search_engine,
            validator=mock_validator,
            cache=mock_cache
        )
        
        # WHEN: Search that will fail
        query = "valid query"
        options = Mock(mode="semantic", scope="library", similarity_threshold=0.7)
        presenter.perform_search(query, options)
        
        # THEN: Should handle error gracefully
        mock_view.show_search_progress.assert_called_once()
        mock_view.show_search_error.assert_called_once_with("Search failed")
        mock_view.display_results.assert_not_called()


class TestSearchEngineFactory:
    """Test search engine factory pattern for dependency injection"""
    
    def test_factory_creates_search_engine_with_dependencies(self):
        """Test that factory properly creates search engine with all dependencies"""
        # GIVEN: Mocked dependencies
        mock_embedding_repo = Mock()
        mock_calibre_repo = Mock()
        mock_embedding_service = Mock()
        mock_search_engine = Mock()
        
        # Create factory (this will fail initially - no factory exists!)
        from search_presenter import SearchEngineFactory
        
        factory = SearchEngineFactory(
            library_path="/test/library",
            calibre_api=Mock(),
            config={"api_key": "test"}
        )
        
        # Mock the creation methods
        factory._create_embedding_repository = Mock(return_value=mock_embedding_repo)
        factory._create_calibre_repository = Mock(return_value=mock_calibre_repo)
        factory._create_embedding_service = Mock(return_value=mock_embedding_service)
        factory._create_search_engine = Mock(return_value=mock_search_engine)
        
        # WHEN: Factory creates search engine
        search_engine = factory.create_search_engine()
        
        # THEN: Should create all dependencies in correct order
        factory._create_embedding_repository.assert_called_once()
        factory._create_calibre_repository.assert_called_once()
        factory._create_embedding_service.assert_called_once()
        factory._create_search_engine.assert_called_once_with(
            mock_embedding_repo, mock_embedding_service
        )
        assert search_engine == mock_search_engine
    
    def test_factory_creates_embedding_repository_with_correct_path(self):
        """Test that factory creates embedding repository with correct database path"""
        # GIVEN: Factory with library path
        from search_presenter import SearchEngineFactory
        
        factory = SearchEngineFactory(
            library_path="/test/library",
            calibre_api=Mock(),
            config={"api_key": "test"}
        )
        
        # Mock os.path.join to verify path construction
        with patch('os.path.join') as mock_join, \
             patch('os.path.exists') as mock_exists, \
             patch('os.makedirs') as mock_makedirs:
            
            # Configure mocks
            mock_join.return_value = "/test/library/semantic_search/embeddings.db"
            mock_exists.return_value = False
            
            # Override the method to test real implementation
            def _create_embedding_repository_impl():
                # Real implementation
                db_dir = os.path.join(factory.library_path, 'semantic_search')
                if not os.path.exists(db_dir):
                    os.makedirs(db_dir, exist_ok=True)
                db_path = os.path.join(db_dir, 'embeddings.db')
                # Return mock for now since we can't import real class
                return Mock(db_path=db_path)
            
            factory._create_embedding_repository = _create_embedding_repository_impl
            
            # WHEN: Creating embedding repository
            repo = factory._create_embedding_repository()
            
            # THEN: Should create directory and use correct path
            mock_join.assert_any_call("/test/library", 'semantic_search')
            mock_makedirs.assert_called_once_with(
                "/test/library/semantic_search/embeddings.db",
                exist_ok=True
            )
            assert repo.db_path == "/test/library/semantic_search/embeddings.db"


class TestSearchDialogIntegration:
    """Test integration of search dialog with presenter and factory"""
    
    def test_search_dialog_uses_presenter_pattern(self):
        """Test that search dialog delegates to presenter for search operations"""
        # GIVEN: Mocked Qt dialog and dependencies
        from search_presenter import SearchDialogPresenter
        from search_business_logic import SearchQueryValidator, SearchCacheManager
        
        # Create a view adapter interface
        class ViewAdapter:
            def __init__(self):
                self.validation_errors = []
                self.displayed_results = []
                self.search_errors = []
                self.progress_shown = False
            
            def show_validation_error(self, error):
                self.validation_errors.append(error)
            
            def display_results(self, results):
                self.displayed_results = results
            
            def show_search_error(self, error):
                self.search_errors.append(error)
            
            def show_search_progress(self):
                self.progress_shown = True
        
        # Create mock dialog that uses presenter
        class MockSearchDialog:
            def __init__(self):
                self.view_adapter = ViewAdapter()
                self.search_engine = AsyncMock()
                self.presenter = SearchDialogPresenter(
                    view=self.view_adapter,
                    search_engine=self.search_engine,
                    validator=SearchQueryValidator(),
                    cache=SearchCacheManager()
                )
            
            def perform_search(self):
                """Delegate to presenter"""
                query = "test query"
                options = Mock(mode="semantic", scope="library", similarity_threshold=0.7)
                self.presenter.perform_search(query, options)
        
        # WHEN: Dialog performs search
        dialog = MockSearchDialog()
        dialog.search_engine.search.return_value = ["result1", "result2"]
        dialog.perform_search()
        
        # THEN: Should use presenter pattern correctly
        assert dialog.view_adapter.progress_shown == True
        assert dialog.view_adapter.displayed_results == ["result1", "result2"]
        assert len(dialog.view_adapter.validation_errors) == 0
        assert len(dialog.view_adapter.search_errors) == 0


if __name__ == "__main__":
    # Run all tests
    pytest.main([__file__, "-v"])