"""
Bug-First TDD: ThreadedJob calling convention mismatch

BUG: SemanticSearchInterface._run_indexing_job() missing 1 required positional argument: 'job'

From the error, Calibre's ThreadedJob calls our function with:
- Called with args: () {'notifications': <queue.Queue>, 'abort': <threading.Event>, 'log': <logging object>}

This shows ThreadedJob calls func(**kwargs) not func(job, **kwargs)

This test should FAIL until we fix the function signature.
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os
import queue
import threading

# Add paths
plugin_path = os.path.join(os.path.dirname(__file__), '..', '..', 'calibre_plugins', 'semantic_search')
sys.path.insert(0, plugin_path)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from calibre_mocks import *


class TestThreadedJobCallingConventionBug:
    """Test that captures ThreadedJob calling convention bug"""
    
    def test_run_indexing_job_called_without_job_parameter(self):
        """
        BUG: _run_indexing_job() missing 1 required positional argument: 'job'
        
        Calibre's ThreadedJob calls functions with ONLY kwargs, no positional args:
        func(**kwargs) not func(job, **kwargs)
        
        Args: () - empty tuple, no positional arguments
        Kwargs: {'notifications': queue, 'abort': event, 'log': logger}
        
        This test should FAIL until we fix the function signature.
        """
        try:
            from interface import SemanticSearchInterface
            
            interface = SemanticSearchInterface()
            interface.indexing_service = Mock()
            
            # Set up book_ids on interface (what _start_indexing would do)
            interface.current_indexing_book_ids = [1, 2, 3]
            
            # Mock the async indexing service call as a coroutine
            async def mock_index_books(*args, **kwargs):
                return {'successful_books': 1, 'failed_books': 0}
            interface.indexing_service.index_books = mock_index_books
            
            # Create the EXACT kwargs that Calibre passes (no job parameter!)
            calibre_kwargs = {
                'notifications': queue.Queue(),
                'abort': threading.Event(),
                'log': Mock()  # Mock the GUILog object
            }
            
            # This should NOT raise TypeError about missing 'job' argument
            # Currently FAILS because our function requires job as positional arg
            # But ThreadedJob calls with ONLY kwargs
            result = interface._run_indexing_job(**calibre_kwargs)
            
            # Should return the indexing stats
            assert result is not None
            assert result['successful_books'] == 1
            
        except TypeError as e:
            if "missing 1 required positional argument: 'job'" in str(e):
                pytest.fail(f"BUG DETECTED: _run_indexing_job expects 'job' but ThreadedJob doesn't pass it: {e}")
            else:
                raise  # Re-raise if it's a different error
    
    def test_run_indexing_job_must_get_job_data_from_kwargs_or_elsewhere(self):
        """
        Test that _run_indexing_job can work without job parameter.
        
        Since ThreadedJob doesn't pass the job object, we need to get book_ids
        from somewhere else (stored on interface, passed in kwargs, etc.)
        """
        try:
            from interface import SemanticSearchInterface
            
            interface = SemanticSearchInterface()
            interface.indexing_service = Mock()
            
            # Store book_ids on the interface (common pattern)
            interface.current_indexing_book_ids = [1, 2, 3]
            
            # Create a call tracker
            call_tracker = Mock()
            
            # Mock the async indexing service call
            async def mock_index_books(*args, **kwargs):
                # Record the call for verification
                call_tracker(*args, **kwargs)
                return {'successful_books': 3, 'failed_books': 0}
            interface.indexing_service.index_books = mock_index_books
            
            calibre_kwargs = {
                'notifications': queue.Queue(),
                'abort': threading.Event(),
                'log': Mock()
            }
            
            # Function should work without job parameter
            result = interface._run_indexing_job(**calibre_kwargs)
            
            # Should have used stored book_ids
            assert result is not None
            assert result['successful_books'] == 3
            
            # Should have called indexing service with book_ids
            call_tracker.assert_called_once()
            call_args = call_tracker.call_args
            assert [1, 2, 3] in call_args[0]  # book_ids should be in args
            
        except Exception as e:
            pytest.fail(f"_run_indexing_job should work without job parameter: {e}")
    
    def test_interface_stores_book_ids_before_starting_job(self):
        """
        Test that the interface stores book_ids before starting ThreadedJob.
        
        Since ThreadedJob doesn't pass the job object with book_ids,
        we need to store them on the interface first.
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
            
            book_ids = [10, 20, 30]
            
            # Start indexing - should store book_ids on interface
            interface._start_indexing(book_ids)
            
            # Should have stored book_ids for job function to access
            assert hasattr(interface, 'current_indexing_book_ids'), \
                "Interface should store book_ids for job function"
            assert interface.current_indexing_book_ids == book_ids
            
        finally:
            # Cleanup
            interface_module.ThreadedJob = None
    
    def test_threaded_job_signature_matches_real_calibre_behavior(self):
        """
        Test that our ThreadedJob usage matches real Calibre behavior.
        
        Based on the error, ThreadedJob calls functions with:
        func(**kwargs) not func(job, **kwargs)
        """
        from interface import SemanticSearchInterface
        import inspect
        
        interface = SemanticSearchInterface()
        
        # Get the function signature
        sig = inspect.signature(interface._run_indexing_job)
        params = list(sig.parameters.keys())
        
        # Should NOT require a 'job' parameter since ThreadedJob doesn't pass it
        # OR should have job as optional with default
        if 'job' in params:
            job_param = sig.parameters['job']
            assert job_param.default is not inspect.Parameter.empty, \
                "If 'job' parameter exists, it should have a default value since ThreadedJob doesn't pass it"
        
        # Should accept **kwargs to handle Calibre's arguments
        has_var_keyword = any(
            param.kind == inspect.Parameter.VAR_KEYWORD 
            for param in sig.parameters.values()
        )
        assert has_var_keyword, "Function should accept **kwargs for Calibre arguments"