"""
Tests for indexing service integration using TDD

These tests verify that the indexing UI properly connects to
the indexing service and handles batch operations.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# Add path for our modules
module_path = os.path.join(os.path.dirname(__file__), '..', '..', 'calibre_plugins', 'semantic_search', 'ui')
sys.path.insert(0, module_path)


class TestIndexingJobManager:
    """Test indexing job management functionality"""
    
    def test_manager_creates_single_book_indexing_job(self):
        """Test that manager creates job for indexing single book"""
        # GIVEN: Mock indexing service and GUI
        mock_indexing_service = Mock()
        mock_gui = Mock()
        
        # Create manager (this will fail initially - no manager exists!)
        from indexing_manager import IndexingJobManager
        
        manager = IndexingJobManager(mock_indexing_service, mock_gui)
        
        # WHEN: Start indexing single book
        book_id = 123
        job_id = manager.start_single_book_indexing(book_id)
        
        # THEN: Should create indexing job
        mock_indexing_service.index_book.assert_called_once_with(book_id)
        assert job_id is not None
    
    def test_manager_creates_batch_indexing_job(self):
        """Test that manager creates job for batch indexing"""
        # GIVEN: Mock indexing service and book IDs
        mock_indexing_service = Mock()
        mock_gui = Mock()
        
        from indexing_manager import IndexingJobManager
        manager = IndexingJobManager(mock_indexing_service, mock_gui)
        
        # WHEN: Start batch indexing
        book_ids = [1, 2, 3, 4, 5]
        job_id = manager.start_batch_indexing(book_ids)
        
        # THEN: Should create batch indexing job
        mock_indexing_service.index_books_batch.assert_called_once_with(book_ids)
        assert job_id is not None
    
    def test_manager_tracks_indexing_progress(self):
        """Test that manager tracks progress of indexing jobs"""
        # GIVEN: Mock indexing service with progress callback
        mock_indexing_service = Mock()
        mock_gui = Mock()
        
        from indexing_manager import IndexingJobManager
        manager = IndexingJobManager(mock_indexing_service, mock_gui)
        
        # Mock progress callback
        progress_callback = Mock()
        manager.set_progress_callback(progress_callback)
        
        # WHEN: Progress update occurs
        manager._on_progress_update("job_123", 50, 100, "Indexing book 2 of 4")
        
        # THEN: Should call progress callback
        progress_callback.assert_called_once_with("job_123", 50, 100, "Indexing book 2 of 4")
    
    def test_manager_handles_indexing_completion(self):
        """Test that manager handles job completion"""
        # GIVEN: Manager with completion callback
        mock_indexing_service = Mock()
        mock_gui = Mock()
        
        from indexing_manager import IndexingJobManager
        manager = IndexingJobManager(mock_indexing_service, mock_gui)
        
        completion_callback = Mock()
        manager.set_completion_callback(completion_callback)
        
        # WHEN: Job completes successfully
        manager._on_job_completion("job_456", success=True, message="Indexing completed")
        
        # THEN: Should call completion callback
        completion_callback.assert_called_once_with("job_456", True, "Indexing completed")
    
    def test_manager_handles_indexing_error(self):
        """Test that manager handles indexing errors"""
        # GIVEN: Manager with error callback
        mock_indexing_service = Mock()
        mock_gui = Mock()
        
        from indexing_manager import IndexingJobManager
        manager = IndexingJobManager(mock_indexing_service, mock_gui)
        
        error_callback = Mock()
        manager.set_error_callback(error_callback)
        
        # WHEN: Job fails with error
        error_message = "Failed to connect to embedding service"
        manager._on_job_error("job_789", error_message)
        
        # THEN: Should call error callback
        error_callback.assert_called_once_with("job_789", error_message)


class TestIndexingProgressTracker:
    """Test indexing progress tracking functionality"""
    
    def test_tracker_updates_progress_display(self):
        """Test that tracker updates progress display correctly"""
        # GIVEN: Mock GUI elements
        mock_progress_bar = Mock()
        mock_status_label = Mock()
        mock_details_text = Mock()
        
        # Create tracker (this will fail initially - no tracker exists!)
        from indexing_manager import IndexingProgressTracker
        
        tracker = IndexingProgressTracker(
            progress_bar=mock_progress_bar,
            status_label=mock_status_label,
            details_text=mock_details_text
        )
        
        # WHEN: Update progress
        tracker.update_progress(75, 100, "Processing book 3 of 4: Philosophy of Mind")
        
        # THEN: Should update GUI elements
        mock_progress_bar.setValue.assert_called_once_with(75)
        mock_progress_bar.setMaximum.assert_called_once_with(100)
        mock_status_label.setText.assert_called_once_with("Processing book 3 of 4: Philosophy of Mind")
    
    def test_tracker_shows_completion_message(self):
        """Test that tracker shows completion message"""
        # GIVEN: Mock GUI elements
        mock_progress_bar = Mock()
        mock_status_label = Mock()
        mock_details_text = Mock()
        
        from indexing_manager import IndexingProgressTracker
        tracker = IndexingProgressTracker(
            progress_bar=mock_progress_bar,
            status_label=mock_status_label,
            details_text=mock_details_text
        )
        
        # WHEN: Show completion
        tracker.show_completion(4, "Successfully indexed 4 books")
        
        # THEN: Should update with completion status
        mock_progress_bar.setValue.assert_called_once_with(100)
        mock_status_label.setText.assert_called_once_with("Successfully indexed 4 books")
        mock_details_text.append.assert_called_once()
    
    def test_tracker_shows_error_message(self):
        """Test that tracker shows error message"""
        # GIVEN: Mock GUI elements
        mock_progress_bar = Mock()
        mock_status_label = Mock()
        mock_details_text = Mock()
        
        from indexing_manager import IndexingProgressTracker
        tracker = IndexingProgressTracker(
            progress_bar=mock_progress_bar,
            status_label=mock_status_label,
            details_text=mock_details_text
        )
        
        # WHEN: Show error
        tracker.show_error("Failed to index 2 books due to network error")
        
        # THEN: Should update with error status
        mock_status_label.setText.assert_called_once_with("Failed to index 2 books due to network error")
        mock_details_text.append.assert_called_once()


class TestIndexingUIConnector:
    """Test connection between indexing UI and services"""
    
    def test_connector_starts_selected_books_indexing(self):
        """Test that connector starts indexing for selected books"""
        # GIVEN: Mock GUI with selected books
        mock_gui = Mock()
        mock_gui.current_view().selectionModel().selectedRows.return_value = [
            Mock(), Mock(), Mock()  # 3 selected rows
        ]
        mock_gui.current_view().model().id.side_effect = [101, 102, 103]  # Book IDs
        
        # Create connector (this will fail initially - no connector exists!)
        from indexing_manager import IndexingUIConnector
        
        connector = IndexingUIConnector(mock_gui)
        
        # Mock job manager
        mock_job_manager = Mock()
        connector.job_manager = mock_job_manager
        
        # WHEN: Start indexing selected books
        connector.index_selected_books()
        
        # THEN: Should start batch indexing with selected book IDs
        mock_job_manager.start_batch_indexing.assert_called_once_with([101, 102, 103])
    
    def test_connector_handles_no_books_selected(self):
        """Test that connector handles case when no books are selected"""
        # GIVEN: Mock GUI with no selection
        mock_gui = Mock()
        mock_gui.current_view().selectionModel().selectedRows.return_value = []
        
        from indexing_manager import IndexingUIConnector
        connector = IndexingUIConnector(mock_gui)
        
        # Mock error callback
        error_callback = Mock()
        connector.set_error_callback(error_callback)
        
        # WHEN: Try to index with no selection
        connector.index_selected_books()
        
        # THEN: Should call error callback
        error_callback.assert_called_once_with("No books selected. Please select books to index.")
    
    def test_connector_starts_library_indexing_with_confirmation(self):
        """Test that connector starts full library indexing with user confirmation"""
        # GIVEN: Mock GUI and database
        mock_gui = Mock()
        mock_gui.current_db.new_api.all_book_ids.return_value = [1, 2, 3, 4, 5]
        
        from indexing_manager import IndexingUIConnector
        connector = IndexingUIConnector(mock_gui)
        
        # Mock confirmation dialog
        with patch('indexing_manager.confirm_large_indexing') as mock_confirm:
            mock_confirm.return_value = True  # User confirms
            
            mock_job_manager = Mock()
            connector.job_manager = mock_job_manager
            
            # WHEN: Start full library indexing
            connector.index_all_books()
            
            # THEN: Should confirm and start batch indexing
            mock_confirm.assert_called_once_with(5)
            mock_job_manager.start_batch_indexing.assert_called_once_with([1, 2, 3, 4, 5])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])