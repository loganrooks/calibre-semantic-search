"""
Test complete indexing flow from UI to storage
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from calibre_plugins.semantic_search.core.indexing_service import IndexingService
from calibre_plugins.semantic_search.core.embedding_service import create_embedding_service
from calibre_plugins.semantic_search.core.text_processor import TextProcessor
from calibre_plugins.semantic_search.data.repositories import EmbeddingRepository, CalibreRepository


class TestIndexingFlow:
    """Test the complete indexing flow"""

    @pytest.fixture
    def mock_calibre_repo(self):
        """Create mock Calibre repository"""
        repo = Mock(spec=CalibreRepository)
        repo.get_book_metadata.return_value = {
            'title': 'Test Book',
            'authors': ['Test Author'],
            'tags': ['philosophy'],
            'language': 'en'
        }
        repo.get_book_text.return_value = "This is a test book about philosophy. It has multiple sentences to chunk."
        return repo

    @pytest.fixture
    def mock_embedding_repo(self):
        """Create mock embedding repository"""
        repo = Mock(spec=EmbeddingRepository)
        repo.get_embeddings = AsyncMock(return_value=[])  # Not indexed yet
        repo.store_embedding = AsyncMock()
        repo.delete_book_embeddings = AsyncMock()
        repo.update_indexing_status = Mock()
        return repo

    @pytest.fixture
    def text_processor(self):
        """Create real text processor"""
        return TextProcessor()

    @pytest.fixture
    def embedding_service(self):
        """Create mock embedding service"""
        config = {
            "embedding_provider": "mock",
            "embedding_model": "test-model",
            "performance": {"cache_enabled": False}
        }
        return create_embedding_service(config)

    @pytest.fixture
    def indexing_service(self, text_processor, embedding_service, mock_embedding_repo, mock_calibre_repo):
        """Create indexing service with mocked dependencies"""
        return IndexingService(
            text_processor=text_processor,
            embedding_service=embedding_service,
            embedding_repo=mock_embedding_repo,
            calibre_repo=mock_calibre_repo,
            batch_size=2,  # Small batch for testing
            max_concurrent=1
        )

    @pytest.mark.asyncio
    async def test_single_book_indexing_flow(self, indexing_service, mock_embedding_repo, mock_calibre_repo):
        """Test indexing a single book"""
        book_id = 123
        
        # Run indexing
        result = await indexing_service.index_single_book(book_id)
        
        # Verify metadata was retrieved
        mock_calibre_repo.get_book_metadata.assert_called_once_with(book_id)
        
        # Verify text was retrieved
        mock_calibre_repo.get_book_text.assert_called_once_with(book_id)
        
        # Verify existing embeddings were deleted
        mock_embedding_repo.delete_book_embeddings.assert_called_once_with(book_id)
        
        # Verify embeddings were stored (should have been called multiple times for chunks)
        assert mock_embedding_repo.store_embedding.call_count > 0
        
        # Verify status updates were called
        assert mock_embedding_repo.update_indexing_status.call_count >= 2
        
        # Check result structure
        assert 'chunk_count' in result
        assert result['chunk_count'] > 0

    @pytest.mark.asyncio
    async def test_multiple_books_indexing(self, indexing_service, mock_embedding_repo):
        """Test indexing multiple books"""
        book_ids = [1, 2, 3]
        
        # Run batch indexing
        stats = await indexing_service.index_books(book_ids)
        
        # Verify statistics
        assert stats['total_books'] == 3
        assert stats['processed_books'] == 3
        assert stats['successful_books'] == 3
        assert stats['failed_books'] == 0
        assert stats['total_chunks'] > 0
        assert 'total_time' in stats

    @pytest.mark.asyncio
    async def test_progress_callbacks(self, indexing_service):
        """Test that progress callbacks are called during indexing"""
        progress_updates = []
        
        def progress_callback(progress_info):
            progress_updates.append(progress_info)
        
        # Add callback
        indexing_service.add_progress_callback(progress_callback)
        
        # Run indexing
        await indexing_service.index_books([1])
        
        # Verify progress updates were received
        assert len(progress_updates) > 0
        
        # Check that progress updates have expected structure
        for update in progress_updates:
            assert 'current_book' in update
            assert 'total_books' in update
            assert 'book_id' in update
            assert 'status' in update

    @pytest.mark.asyncio
    async def test_skip_already_indexed_books(self, indexing_service, mock_embedding_repo):
        """Test that already indexed books are skipped"""
        book_id = 123
        
        # Mock that book is already indexed
        mock_embedding_repo.get_embeddings.return_value = [Mock()]  # Has embeddings
        
        # Run indexing
        stats = await indexing_service.index_books([book_id], reindex=False)
        
        # Verify book was skipped
        assert stats['processed_books'] == 1
        assert stats['successful_books'] == 0  # Skipped, not processed
        
        # Verify no new embeddings were stored
        mock_embedding_repo.store_embedding.assert_not_called()

    @pytest.mark.asyncio
    async def test_reindex_existing_books(self, indexing_service, mock_embedding_repo):
        """Test that reindex=True processes already indexed books"""
        book_id = 123
        
        # Mock that book is already indexed
        mock_embedding_repo.get_embeddings.return_value = [Mock()]  # Has embeddings
        
        # Run indexing with reindex=True
        stats = await indexing_service.index_books([book_id], reindex=True)
        
        # Verify book was processed despite existing embeddings
        assert stats['successful_books'] == 1
        
        # Verify existing embeddings were deleted and new ones stored
        mock_embedding_repo.delete_book_embeddings.assert_called_once_with(book_id)
        assert mock_embedding_repo.store_embedding.call_count > 0

    @pytest.mark.asyncio
    async def test_error_handling(self, indexing_service, mock_calibre_repo):
        """Test error handling during indexing"""
        book_id = 999
        
        # Mock an error during text retrieval
        mock_calibre_repo.get_book_text.side_effect = Exception("Book not found")
        
        # Run indexing
        stats = await indexing_service.index_books([book_id])
        
        # Verify error was handled
        assert stats['failed_books'] == 1
        assert stats['successful_books'] == 0
        assert len(stats['errors']) == 1
        assert stats['errors'][0]['book_id'] == book_id
        assert "Book not found" in stats['errors'][0]['error']

    def test_progress_callback_management(self, indexing_service):
        """Test adding and removing progress callbacks"""
        callback1 = Mock()
        callback2 = Mock()
        
        # Add callbacks
        indexing_service.add_progress_callback(callback1)
        indexing_service.add_progress_callback(callback2)
        
        assert len(indexing_service._progress_callbacks) == 2
        
        # Remove one callback
        indexing_service.remove_progress_callback(callback1)
        
        assert len(indexing_service._progress_callbacks) == 1
        assert callback2 in indexing_service._progress_callbacks
        assert callback1 not in indexing_service._progress_callbacks

    def test_cancellation(self, indexing_service):
        """Test cancellation functionality"""
        # Request cancellation
        indexing_service.request_cancel()
        
        assert indexing_service._cancel_requested is True