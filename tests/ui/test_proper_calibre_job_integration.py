"""
Bug-First TDD: Implement PROPER Calibre job integration

Based on research, we need to:
1. Replace BackgroundJobManager with ThreadedJob
2. Use self.gui.job_manager.run_threaded_job(job) 
3. This will make jobs show in Calibre's job indicator

These tests define the CORRECT behavior we want.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add paths
plugin_path = os.path.join(os.path.dirname(__file__), '..', '..', 'calibre_plugins', 'semantic_search')
sys.path.insert(0, plugin_path)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from calibre_mocks import *


class TestProperCalibreJobIntegration:
    """Tests for proper Calibre ThreadedJob integration"""
    
    def test_interface_uses_threaded_job_instead_of_background_manager(self):
        """
        REQUIREMENT: interface should use ThreadedJob, not BackgroundJobManager
        This should FAIL until we implement proper ThreadedJob integration
        """
        # Need to patch both the import and the interface module
        mock_threaded_job_class = Mock()
        mock_job = Mock()
        mock_threaded_job_class.return_value = mock_job
        
        # Patch the interface module to have ThreadedJob available
        import interface as interface_module
        interface_module.ThreadedJob = mock_threaded_job_class
        
        try:
            from interface import SemanticSearchInterface
            
            interface = SemanticSearchInterface()
            interface.gui = Mock()
            interface.gui.job_manager = Mock()
            interface.gui.status_bar = Mock()
            interface.indexing_service = Mock()
            
            # Start indexing - should use ThreadedJob
            interface._start_indexing([1, 2, 3])
            
            # Should create ThreadedJob with correct parameters
            mock_threaded_job_class.assert_called_once()
            call_args = mock_threaded_job_class.call_args
            
            # Verify ThreadedJob parameters (new signature)
            assert call_args[0][0] == 'semantic_search_indexing'  # Job name
            assert 'Indexing' in call_args[0][1]  # Job description
            assert callable(call_args[0][2])  # run function
            assert call_args[0][3] == ()  # args tuple
            assert call_args[0][4] == {}  # kwargs dict
            assert callable(call_args[0][5])  # done function
            
            # Should submit job to Calibre's job manager
            interface.gui.job_manager.run_threaded_job.assert_called_once_with(mock_job)
            
        finally:
            # Cleanup
            interface_module.ThreadedJob = None
    
    def test_interface_does_not_use_background_job_manager(self):
        """
        REQUIREMENT: interface should NOT use BackgroundJobManager anymore
        """
        # Mock ThreadedJob to be available
        with patch('calibre_plugins.semantic_search.interface.ThreadedJob'):
            from interface import SemanticSearchInterface
            
            interface = SemanticSearchInterface()
            interface.gui = Mock()
            interface.gui.job_manager = Mock()
            interface.gui.status_bar = Mock()
            interface.indexing_service = Mock()
            
            # Start indexing
            interface._start_indexing([1, 2, 3])
            
            # Should NOT have created a BackgroundJobManager
            assert not hasattr(interface, 'job_manager'), \
                "Interface should not create BackgroundJobManager anymore"
    
    def test_threaded_job_run_function_calls_indexing_service(self):
        """
        REQUIREMENT: ThreadedJob run function should call indexing service
        """
        with patch('calibre_plugins.semantic_search.interface.ThreadedJob') as mock_threaded_job:
            from interface import SemanticSearchInterface
            
            interface = SemanticSearchInterface()
            interface.gui = Mock()
            interface.gui.job_manager = Mock()
            interface.gui.status_bar = Mock()
            interface.indexing_service = Mock()
            
            # Mock async indexing service
            import asyncio
            future = asyncio.Future()
            future.set_result({'successful_books': 3, 'failed_books': 0})
            interface.indexing_service.index_books = Mock(return_value=future)
            
            # Start indexing
            interface._start_indexing([1, 2, 3])
            
            # Get the run function that was passed to ThreadedJob
            call_args = mock_threaded_job.call_args
            run_function = call_args[0][2]  # Third argument is run function
            
            # Mock job parameter for run function
            mock_job = Mock()
            
            # Call the run function
            result = run_function(mock_job)
            
            # Should have called indexing service
            interface.indexing_service.index_books.assert_called_once()
    
    def test_threaded_job_done_function_shows_completion_dialog(self):
        """
        REQUIREMENT: ThreadedJob done function should show completion dialog
        """
        with patch('calibre_plugins.semantic_search.interface.ThreadedJob') as mock_threaded_job:
            with patch('calibre_plugins.semantic_search.interface.info_dialog') as mock_info:
                from interface import SemanticSearchInterface
                
                interface = SemanticSearchInterface()
                interface.gui = Mock()
                interface.gui.job_manager = Mock()
                interface.gui.status_bar = Mock()
                interface.indexing_service = Mock()
                
                # Start indexing
                interface._start_indexing([1, 2, 3])
                
                # Get the done function that was passed to ThreadedJob
                call_args = mock_threaded_job.call_args
                done_function = call_args[0][3]  # Fourth argument is done function
                
                # Mock successful job completion
                mock_job = Mock()
                mock_job.failed = False
                mock_job.result = {'successful_books': 3, 'failed_books': 0}
                
                # Call the done function
                done_function(mock_job)
                
                # Should show completion dialog
                mock_info.assert_called_once()
    
    def test_indexing_status_shows_correct_information_without_errors(self):
        """
        BUG FIX: show_indexing_status should not error on 'in_progress' field
        """
        from interface import SemanticSearchInterface
        
        interface = SemanticSearchInterface()
        interface.gui = Mock()
        interface.indexing_service = Mock()
        
        # Mock status that includes 'in_progress' - this currently causes errors
        mock_status = {
            'total_books': 100,
            'indexed_books': 50, 
            'in_progress': 5,  # This is causing the error
            'errors': 2,
            'last_indexed': '2025-06-01 12:00:00'
        }
        
        # Mock the async call
        import asyncio
        future = asyncio.Future()
        future.set_result(mock_status)
        interface.indexing_service.get_library_statistics = Mock(return_value=future)
        
        with patch('calibre_plugins.semantic_search.interface.info_dialog') as mock_info:
            # This should NOT raise an error about 'in_progress'
            interface.show_indexing_status()
            
            # Should show info dialog with status
            mock_info.assert_called_once()
            call_args = mock_info.call_args[0]
            
            # Should contain the status information
            assert 'Indexed Books: 50' in call_args[2]
            assert 'In Progress: 5' in call_args[2]
            
            # Should NOT contain error message
            assert 'Error retrieving' not in call_args[2]