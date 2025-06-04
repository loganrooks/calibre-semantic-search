"""
Test ThreadedJob integration for indexing operations

These tests verify that the indexing system properly uses Calibre's
ThreadedJob system instead of raw threading.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import sys
import os

# Add the main plugin directory to Python path
plugin_path = os.path.join(os.path.dirname(__file__), '..', '..', 'calibre_plugins', 'semantic_search')
sys.path.insert(0, plugin_path)

# Import mocks
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from calibre_mocks import *


class TestThreadedJobIntegration:
    """Test that indexing uses ThreadedJob system properly"""
    
    @pytest.fixture
    def mock_interface(self):
        """Create a mock interface with necessary components"""
        with patch('calibre_plugins.semantic_search.interface.ThreadedJob') as mock_threaded_job:
            # Import here to ensure patches are applied
            from interface import SemanticSearchInterface
            
            # Create mock interface
            interface = SemanticSearchInterface(None, 'test')
            
            # Mock GUI components
            interface.gui = Mock()
            interface.gui.job_manager = Mock()
            interface.gui.status_bar = Mock()
            
            # Mock indexing service
            interface.indexing_service = Mock()
            
            return interface, mock_threaded_job
    
    def test_start_indexing_creates_threaded_job(self, mock_interface):
        """Test that _start_indexing creates a ThreadedJob with correct parameters"""
        interface, mock_threaded_job = mock_interface
        book_ids = [1, 2, 3]
        
        # WHEN: Starting indexing
        interface._start_indexing(book_ids)
        
        # THEN: ThreadedJob should be created with correct parameters
        mock_threaded_job.assert_called_once()
        call_args = mock_threaded_job.call_args
        
        # Verify job parameters
        assert call_args[0][0] == 'semantic_search_indexing'  # Job name
        assert 'Indexing 3 books' in call_args[0][1]  # Job description
        assert call_args[0][2] == interface._run_indexing_job  # Callback function
        assert call_args[0][3] == interface._indexing_job_complete  # Complete callback
        assert call_args[1]['job_data']['book_ids'] == book_ids  # Job data
        assert call_args[1]['max_concurrent_count'] == 1  # Concurrent limit
    
    def test_start_indexing_submits_job_to_manager(self, mock_interface):
        """Test that job is submitted to Calibre's job manager"""
        interface, mock_threaded_job = mock_interface
        mock_job = Mock()
        mock_threaded_job.return_value = mock_job
        
        # WHEN: Starting indexing
        interface._start_indexing([1, 2, 3])
        
        # THEN: Job should be submitted to job manager
        interface.gui.job_manager.run_threaded_job.assert_called_once_with(mock_job)
    
    def test_start_indexing_shows_status_message(self, mock_interface):
        """Test that status message is shown when starting indexing"""
        interface, mock_threaded_job = mock_interface
        
        # WHEN: Starting indexing
        interface._start_indexing([1, 2, 3])
        
        # THEN: Status message should be shown
        interface.gui.status_bar.show_message.assert_called_once()
        call_args = interface.gui.status_bar.show_message.call_args[0]
        assert 'Starting indexing of 3 books' in call_args[0]
    
    def test_start_indexing_stores_job_reference(self, mock_interface):
        """Test that job reference is stored for potential cancellation"""
        interface, mock_threaded_job = mock_interface
        mock_job = Mock()
        mock_threaded_job.return_value = mock_job
        
        # WHEN: Starting indexing
        interface._start_indexing([1, 2, 3])
        
        # THEN: Job reference should be stored
        assert interface.current_indexing_job == mock_job
    
    @patch('asyncio.new_event_loop')
    @patch('asyncio.set_event_loop')
    def test_run_indexing_job_creates_event_loop(self, mock_set_loop, mock_new_loop, mock_interface):
        """Test that background job creates its own event loop"""
        interface, _ = mock_interface
        mock_loop = Mock()
        mock_new_loop.return_value = mock_loop
        
        # Mock job object
        mock_job = Mock()
        mock_job.job_data = {'book_ids': [1, 2, 3]}
        
        # Mock indexing service
        interface.indexing_service.add_progress_callback = Mock()
        interface.indexing_service.remove_progress_callback = Mock()
        mock_loop.run_until_complete = Mock(return_value={'successful_books': 3})
        
        # WHEN: Running indexing job
        result = interface._run_indexing_job(mock_job)
        
        # THEN: Event loop should be created and set
        mock_new_loop.assert_called_once()
        mock_set_loop.assert_called_once_with(mock_loop)
        mock_loop.close.assert_called_once()
    
    def test_run_indexing_job_sets_progress_callback(self, mock_interface):
        """Test that progress callback is properly set up"""
        interface, _ = mock_interface
        
        # Mock job and components
        mock_job = Mock()
        mock_job.job_data = {'book_ids': [1, 2, 3]}
        
        with patch('asyncio.new_event_loop') as mock_new_loop:
            mock_loop = Mock()
            mock_new_loop.return_value = mock_loop
            mock_loop.run_until_complete = Mock(return_value={'successful_books': 3})
            
            # WHEN: Running indexing job
            interface._run_indexing_job(mock_job)
            
            # THEN: Progress callback should be added and removed
            interface.indexing_service.add_progress_callback.assert_called_once()
            interface.indexing_service.remove_progress_callback.assert_called_once()
    
    def test_indexing_job_complete_handles_success(self, mock_interface):
        """Test that successful job completion is handled properly"""
        interface, _ = mock_interface
        
        # Mock successful job
        mock_job = Mock()
        mock_job.failed = False
        mock_job.result = {
            'successful_books': 3,
            'failed_books': 0,
            'total_chunks': 150,
            'total_time': 45.5
        }
        
        with patch('calibre_plugins.semantic_search.interface.info_dialog') as mock_info:
            # WHEN: Job completes successfully
            interface._indexing_job_complete(mock_job)
            
            # THEN: Info dialog should be shown with results
            mock_info.assert_called_once()
            call_args = mock_info.call_args[0]
            assert 'Successfully indexed: 3 books' in call_args[2]
            assert 'Total text chunks created: 150' in call_args[2]
    
    def test_indexing_job_complete_handles_failure(self, mock_interface):
        """Test that failed job completion is handled properly"""
        interface, _ = mock_interface
        
        # Mock failed job
        mock_job = Mock()
        mock_job.failed = True
        mock_job.exception = Exception("Test error")
        
        with patch('calibre_plugins.semantic_search.interface.error_dialog') as mock_error:
            # WHEN: Job completes with failure
            interface._indexing_job_complete(mock_job)
            
            # THEN: Error dialog should be shown
            mock_error.assert_called_once()
            call_args = mock_error.call_args[0]
            assert 'Test error' in call_args[2]
    
    def test_indexing_job_complete_clears_job_reference(self, mock_interface):
        """Test that job reference is cleared after completion"""
        interface, _ = mock_interface
        
        # Set up job reference
        interface.current_indexing_job = Mock()
        
        # Mock job completion
        mock_job = Mock()
        mock_job.failed = False
        mock_job.result = {'successful_books': 1}
        
        with patch('calibre_plugins.semantic_search.interface.info_dialog'):
            # WHEN: Job completes
            interface._indexing_job_complete(mock_job)
            
            # THEN: Job reference should be cleared
            assert not hasattr(interface, 'current_indexing_job')
    
    def test_start_indexing_handles_no_service(self, mock_interface):
        """Test that missing indexing service is handled gracefully"""
        interface, _ = mock_interface
        interface.indexing_service = None
        
        with patch('calibre_plugins.semantic_search.interface.error_dialog') as mock_error:
            # WHEN: Starting indexing without service
            interface._start_indexing([1, 2, 3])
            
            # THEN: Error dialog should be shown
            mock_error.assert_called_once()
            call_args = mock_error.call_args[0]
            assert 'could not be initialized' in call_args[2]