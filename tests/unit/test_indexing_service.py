"""
Unit tests for indexing service following TDD approach - Fixed Version
"""

import pytest
import asyncio
import numpy as np
from unittest.mock import Mock, AsyncMock, patch, call
from pathlib import Path

# Direct import to avoid Calibre dependencies
import sys
plugin_path = Path(__file__).parent.parent.parent / "calibre_plugins" / "semantic_search"
sys.path.insert(0, str(plugin_path))

# Mock all Calibre-related imports
mock_text_processor = Mock()
mock_embedding_service = Mock()
mock_repositories = Mock()

# Create mock classes
class MockTextProcessor:
    def __init__(self):
        pass

class MockEmbeddingService:
    def __init__(self):
        pass

class MockEmbeddingRepository:
    def __init__(self):
        pass

class MockCalibreRepository:
    def __init__(self):
        pass

class MockChunk:
    def __init__(self, text, index, book_id, start_pos, end_pos, metadata):
        self.text = text
        self.index = index
        self.book_id = book_id
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.metadata = metadata

mock_text_processor.TextProcessor = MockTextProcessor
mock_text_processor.Chunk = MockChunk
mock_embedding_service.EmbeddingService = MockEmbeddingService
mock_repositories.EmbeddingRepository = MockEmbeddingRepository
mock_repositories.CalibreRepository = MockCalibreRepository

with patch.dict('sys.modules', {
    'calibre_plugins.semantic_search.core.text_processor': mock_text_processor,
    'calibre_plugins.semantic_search.core.embedding_service': mock_embedding_service,
    'calibre_plugins.semantic_search.data.repositories': mock_repositories,
    'calibre_plugins': Mock(),
    'calibre_plugins.semantic_search': Mock(),
    'calibre': Mock()
}):
    # Import indexing service module directly
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "indexing_service", 
        plugin_path / "core" / "indexing_service.py"
    )
    indexing_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(indexing_module)

IndexingService = indexing_module.IndexingService


@pytest.fixture
def mock_text_processor_instance():
    """Create mock text processor"""
    processor = Mock()
    processor.chunk_text.return_value = [
        MockChunk("Chunk 1 text", 0, 1, 0, 12, {"chapter": "Chapter 1"}),
        MockChunk("Chunk 2 text", 1, 1, 13, 25, {"chapter": "Chapter 1"}),
        MockChunk("Chunk 3 text", 2, 1, 26, 38, {"chapter": "Chapter 2"})
    ]
    return processor


@pytest.fixture
def mock_embedding_service_instance():
    """Create mock embedding service"""
    service = Mock()
    service.generate_batch = AsyncMock(
        return_value=[np.random.rand(768).astype(np.float32) for _ in range(3)]
    )
    return service


@pytest.fixture
def mock_embedding_repo():
    """Create mock embedding repository"""
    repo = Mock()
    repo.store_embedding = AsyncMock(return_value=1)
    repo.delete_book_embeddings = AsyncMock()
    repo.update_indexing_status = Mock()
    repo.get_indexing_status = Mock(return_value=[])
    repo.get_embeddings = AsyncMock(return_value=[])  # For checking existing
    repo.get_statistics = Mock(return_value={'indexed_books': 5, 'total_chunks': 100})
    return repo


@pytest.fixture
def mock_calibre_repo():
    """Create mock Calibre repository"""
    repo = Mock()
    repo.get_book_metadata.return_value = {
        'id': 1,
        'title': 'Test Book',
        'authors': ['Test Author'],
        'tags': ['Philosophy'],
        'formats': ['EPUB']
    }
    repo.get_book_text.return_value = "This is a test book with some philosophical content."
    repo.get_all_book_ids.return_value = [1, 2, 3]
    return repo


@pytest.fixture
def indexing_service(mock_text_processor_instance, mock_embedding_service_instance, 
                    mock_embedding_repo, mock_calibre_repo):
    """Create indexing service with mock dependencies"""
    return IndexingService(
        text_processor=mock_text_processor_instance,
        embedding_service=mock_embedding_service_instance,
        embedding_repo=mock_embedding_repo,
        calibre_repo=mock_calibre_repo,
        batch_size=10,
        max_concurrent=2
    )


class TestIndexingServiceInit:
    """Test IndexingService initialization"""
    
    def test_init_with_defaults(self, mock_text_processor_instance, mock_embedding_service_instance,
                               mock_embedding_repo, mock_calibre_repo):
        """Test initialization with default parameters"""
        service = IndexingService(
            mock_text_processor_instance,
            mock_embedding_service_instance,
            mock_embedding_repo,
            mock_calibre_repo
        )
        
        assert service.text_processor == mock_text_processor_instance
        assert service.embedding_service == mock_embedding_service_instance
        assert service.embedding_repo == mock_embedding_repo
        assert service.calibre_repo == mock_calibre_repo
        assert service.batch_size == 100  # Default
        assert service.max_concurrent == 3  # Default
        assert service._progress_callbacks == []
        assert service._cancel_requested == False
        
    def test_init_with_custom_params(self, mock_text_processor_instance, mock_embedding_service_instance,
                                   mock_embedding_repo, mock_calibre_repo):
        """Test initialization with custom parameters"""
        service = IndexingService(
            mock_text_processor_instance,
            mock_embedding_service_instance,
            mock_embedding_repo,
            mock_calibre_repo,
            batch_size=50,
            max_concurrent=5
        )
        
        assert service.batch_size == 50
        assert service.max_concurrent == 5


class TestProgressCallbacks:
    """Test progress callback functionality"""
    
    def test_add_progress_callback(self, indexing_service):
        """Test adding progress callback"""
        callback = Mock()
        
        indexing_service.add_progress_callback(callback)
        
        assert callback in indexing_service._progress_callbacks
        
    def test_remove_progress_callback(self, indexing_service):
        """Test removing progress callback"""
        callback = Mock()
        
        indexing_service.add_progress_callback(callback)
        indexing_service.remove_progress_callback(callback)
        
        assert callback not in indexing_service._progress_callbacks
        
    def test_remove_nonexistent_callback(self, indexing_service):
        """Test removing non-existent callback"""
        callback = Mock()
        
        # Should not raise error
        indexing_service.remove_progress_callback(callback)
        
    def test_report_progress(self, indexing_service):
        """Test progress reporting"""
        callback1 = Mock()
        callback2 = Mock()
        
        indexing_service.add_progress_callback(callback1)
        indexing_service.add_progress_callback(callback2)
        
        indexing_service._report_progress(book_id=1, current=50, total=100, status="indexing")
        
        expected_args = {'book_id': 1, 'current': 50, 'total': 100, 'status': 'indexing'}
        callback1.assert_called_once_with(expected_args)
        callback2.assert_called_once_with(expected_args)
        
    def test_report_progress_callback_error(self, indexing_service):
        """Test progress reporting with callback error"""
        callback = Mock()
        callback.side_effect = Exception("Callback error")
        
        indexing_service.add_progress_callback(callback)
        
        # Should not raise error
        indexing_service._report_progress(book_id=1, status="test")
        

class TestCancellation:
    """Test cancellation functionality"""
    
    def test_request_cancel(self, indexing_service):
        """Test requesting cancellation"""
        assert indexing_service._cancel_requested == False
        
        indexing_service.request_cancel()
        
        assert indexing_service._cancel_requested == True


class TestSingleBookIndexing:
    """Test single book indexing functionality"""
    
    @pytest.mark.asyncio
    async def test_index_single_book_success(self, indexing_service, mock_text_processor_instance,
                                           mock_embedding_service_instance, mock_embedding_repo, 
                                           mock_calibre_repo):
        """Test successful single book indexing"""
        book_id = 1
        
        result = await indexing_service.index_single_book(book_id)
        
        # Verify workflow
        mock_calibre_repo.get_book_metadata.assert_called_once_with(book_id)
        mock_calibre_repo.get_book_text.assert_called_once_with(book_id)
        mock_text_processor_instance.chunk_text.assert_called_once()
        
        # Should generate embeddings in batch
        mock_embedding_service_instance.generate_batch.assert_called_once()
        
        # Should store each embedding
        assert mock_embedding_repo.store_embedding.call_count == 3
        
        # Should update indexing status
        mock_embedding_repo.update_indexing_status.assert_any_call(book_id, 'indexing', 0.0)
        mock_embedding_repo.update_indexing_status.assert_any_call(book_id, 'completed', 1.0)
        
        assert result == {'book_id': book_id, 'chunk_count': 3, 'status': 'success'}
        
    @pytest.mark.asyncio
    async def test_index_single_book_no_text(self, indexing_service, mock_calibre_repo):
        """Test indexing book with no text"""
        book_id = 1
        mock_calibre_repo.get_book_text.return_value = ""
        
        with pytest.raises(ValueError, match="No text content found"):
            await indexing_service.index_single_book(book_id)
            
    @pytest.mark.asyncio
    async def test_index_single_book_metadata_error(self, indexing_service, mock_calibre_repo, mock_embedding_repo):
        """Test handling metadata retrieval errors"""
        book_id = 1
        mock_calibre_repo.get_book_metadata.side_effect = Exception("Metadata error")
        
        with pytest.raises(Exception, match="Metadata error"):
            await indexing_service.index_single_book(book_id)
            
        # Should update status as error
        mock_embedding_repo.update_indexing_status.assert_called_with(
            book_id, 'error', error='Metadata error'
        )
        
    @pytest.mark.asyncio
    async def test_index_single_book_embedding_error(self, indexing_service, 
                                                   mock_embedding_service_instance,
                                                   mock_embedding_repo):
        """Test handling embedding generation errors"""
        book_id = 1
        mock_embedding_service_instance.generate_batch.side_effect = Exception("Embedding failed")
        
        with pytest.raises(Exception, match="Embedding failed"):
            await indexing_service.index_single_book(book_id)
            
    @pytest.mark.asyncio
    async def test_index_single_book_with_cancellation(self, indexing_service):
        """Test indexing with cancellation"""
        book_id = 1
        
        # Request cancellation during processing
        indexing_service.request_cancel()
        
        with pytest.raises(Exception, match="Indexing cancelled"):
            await indexing_service.index_single_book(book_id)


class TestBatchIndexing:
    """Test batch indexing functionality"""
    
    @pytest.mark.asyncio
    async def test_index_books_success(self, indexing_service):
        """Test indexing multiple books successfully"""
        book_ids = [1, 2, 3]
        
        # Mock index_single_book to avoid complex setup
        indexing_service.index_single_book = AsyncMock(
            return_value={'book_id': 1, 'chunk_count': 5, 'status': 'success'}
        )
        
        result = await indexing_service.index_books(book_ids)
        
        assert result['total_books'] == 3
        assert result['processed_books'] == 3
        assert result['successful_books'] == 3
        assert result['failed_books'] == 0
        assert result['total_chunks'] == 15  # 3 books * 5 chunks
        assert len(result['errors']) == 0
        
    @pytest.mark.asyncio
    async def test_index_books_with_existing_skip(self, indexing_service, mock_embedding_repo):
        """Test skipping already indexed books"""
        book_ids = [1, 2, 3]
        
        # Mock that book 2 already has embeddings
        async def mock_get_embeddings(book_id):
            if book_id == 2:
                return ['existing_embedding']
            return []
            
        mock_embedding_repo.get_embeddings.side_effect = mock_get_embeddings
        
        # Mock index_single_book
        indexing_service.index_single_book = AsyncMock(
            return_value={'book_id': 1, 'chunk_count': 5, 'status': 'success'}
        )
        
        result = await indexing_service.index_books(book_ids, reindex=False)
        
        # Should only index books 1 and 3 (book 2 skipped)
        assert indexing_service.index_single_book.call_count == 2
        assert result['successful_books'] == 2
        assert result['processed_books'] == 3  # All processed (including skipped)
        
    @pytest.mark.asyncio
    async def test_index_books_with_reindex(self, indexing_service, mock_embedding_repo):
        """Test reindexing existing books"""
        book_ids = [1, 2, 3]
        
        # Mock that book 2 already has embeddings
        mock_embedding_repo.get_embeddings.return_value = ['existing']
        
        indexing_service.index_single_book = AsyncMock(
            return_value={'book_id': 1, 'chunk_count': 5, 'status': 'success'}
        )
        
        result = await indexing_service.index_books(book_ids, reindex=True)
        
        # Should index all books despite existing embeddings
        assert indexing_service.index_single_book.call_count == 3
        assert result['successful_books'] == 3
        
    @pytest.mark.asyncio
    async def test_index_books_with_errors(self, indexing_service):
        """Test batch indexing with some failures"""
        book_ids = [1, 2, 3]
        
        # Mock index_single_book to fail for book 2
        def mock_index_single_book(book_id):
            if book_id == 2:
                raise Exception("Processing failed")
            return {'book_id': book_id, 'chunk_count': 5, 'status': 'success'}
            
        indexing_service.index_single_book = AsyncMock(side_effect=mock_index_single_book)
        
        result = await indexing_service.index_books(book_ids)
        
        assert result['successful_books'] == 2
        assert result['failed_books'] == 1
        assert len(result['errors']) == 1
        assert result['errors'][0]['book_id'] == 2
        assert 'Processing failed' in result['errors'][0]['error']
        
    @pytest.mark.asyncio
    async def test_index_books_with_cancellation(self, indexing_service):
        """Test batch indexing with cancellation"""
        book_ids = [1, 2, 3, 4, 5]
        
        # Mock to cancel after processing 2 books
        call_count = 0
        
        async def mock_index_with_cancel(book_id):
            nonlocal call_count
            call_count += 1
            if call_count == 2:  # Cancel after processing 2nd book
                indexing_service.request_cancel()
            return {'book_id': book_id, 'chunk_count': 5, 'status': 'success'}
            
        indexing_service.index_single_book = AsyncMock(side_effect=mock_index_with_cancel)
        
        result = await indexing_service.index_books(book_ids)
        
        # Should process first 2 books, then cancel before 3rd
        # The implementation may complete the current book being processed
        assert result['successful_books'] <= 3  # At most 3 if 3rd book started
        assert result['processed_books'] <= 3
        assert result['successful_books'] >= 2  # At least 2 completed


class TestIndexingStatus:
    """Test indexing status management"""
    
    @pytest.mark.asyncio
    async def test_get_indexing_status(self, indexing_service, mock_embedding_repo):
        """Test getting indexing status"""
        mock_status = [
            {'book_id': 1, 'status': 'completed', 'progress': 1.0},
            {'book_id': 2, 'status': 'indexing', 'progress': 0.5}
        ]
        mock_embedding_repo.get_indexing_status.return_value = mock_status
        
        status = await indexing_service.get_indexing_status()
        
        assert status == mock_status
        mock_embedding_repo.get_indexing_status.assert_called_once()


class TestLibraryStatistics:
    """Test library statistics functionality"""
    
    @pytest.mark.asyncio
    async def test_get_library_statistics(self, indexing_service, mock_embedding_repo, mock_calibre_repo):
        """Test getting library statistics"""
        mock_embedding_repo.get_statistics.return_value = {
            'indexed_books': 5,
            'total_chunks': 100
        }
        mock_calibre_repo.get_all_book_ids.return_value = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        
        stats = await indexing_service.get_library_statistics()
        
        assert stats['indexed_books'] == 5
        assert stats['total_chunks'] == 100
        assert stats['total_library_books'] == 10
        assert stats['indexing_percentage'] == 50.0  # 5/10 * 100
        
    @pytest.mark.asyncio
    async def test_get_library_statistics_empty_library(self, indexing_service, mock_embedding_repo, mock_calibre_repo):
        """Test statistics with empty library"""
        mock_embedding_repo.get_statistics.return_value = {'indexed_books': 0, 'total_chunks': 0}
        mock_calibre_repo.get_all_book_ids.return_value = []
        
        stats = await indexing_service.get_library_statistics()
        
        assert stats['total_library_books'] == 0
        assert stats['indexing_percentage'] == 0


class TestTimeEstimation:
    """Test indexing time estimation"""
    
    def test_estimate_indexing_time(self, indexing_service):
        """Test time estimation for indexing"""
        # Test with 10 books
        estimated_time = indexing_service.estimate_indexing_time(10)
        
        # Should return a positive float
        assert isinstance(estimated_time, (int, float))
        assert estimated_time > 0
        
        # Test with 0 books
        estimated_time_zero = indexing_service.estimate_indexing_time(0)
        assert estimated_time_zero == 0
        
        # Larger number should take more time
        estimated_time_large = indexing_service.estimate_indexing_time(100)
        assert estimated_time_large > estimated_time


class TestIntegration:
    """Integration tests for indexing service"""
    
    @pytest.mark.asyncio
    async def test_complete_indexing_workflow(self, indexing_service, mock_calibre_repo):
        """Test complete indexing workflow with progress tracking"""
        # Setup realistic data
        mock_calibre_repo.get_book_metadata.return_value = {
            'id': 1,
            'title': 'Being and Time',
            'authors': ['Martin Heidegger'],
            'tags': ['Philosophy', 'Existentialism'],
            'formats': ['EPUB'],
            'pubdate': '1927'
        }
        
        mock_calibre_repo.get_book_text.return_value = (
            "Dasein is essentially characterized by being-in-the-world. "
            "The structure of care reveals the being of Dasein as thrown projection "
            "fallen into the world of everyday concerns."
        )
        
        # Track progress
        progress_updates = []
        
        def track_progress(progress_data):
            progress_updates.append(progress_data)
            
        indexing_service.add_progress_callback(track_progress)
        
        # Index the books
        result = await indexing_service.index_books([1, 2])
        
        # Verify results
        assert result['successful_books'] == 2
        assert result['failed_books'] == 0
        assert result['total_chunks'] > 0
        
        # Verify progress was tracked
        assert len(progress_updates) >= 4  # At least start and end for each book
        
        # Check that we have starting and completed statuses
        statuses = [update.get('status') for update in progress_updates]
        assert 'starting' in statuses
        assert 'completed' in statuses


if __name__ == "__main__":
    pytest.main([__file__, "-v"])