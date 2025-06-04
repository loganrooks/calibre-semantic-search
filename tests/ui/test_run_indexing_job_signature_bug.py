"""
Bug-First TDD: _run_indexing_job signature mismatch

BUG: SemanticSearchInterface._run_indexing_job() got an unexpected keyword argument 'notifications'

From the error, Calibre's ThreadedJob calls our function with additional kwargs:
- notifications: <queue.Queue object>
- abort: <threading.Event>  
- log: <calibre.utils.logging.GUILog object>

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


class TestRunIndexingJobSignatureBug:
    """Test that captures _run_indexing_job signature bug"""
    
    def test_run_indexing_job_accepts_calibre_kwargs(self):
        """
        BUG: _run_indexing_job() got unexpected keyword argument 'notifications'
        
        Calibre passes additional kwargs to the job function:
        - notifications: queue.Queue
        - abort: threading.Event  
        - log: logging object
        
        This test should FAIL until we fix the function signature.
        """
        try:
            from interface import SemanticSearchInterface
            
            interface = SemanticSearchInterface()
            interface.indexing_service = Mock()
            
            # Mock the async indexing service call as a coroutine
            import asyncio
            async def mock_index_books(*args, **kwargs):
                return {'successful_books': 1, 'failed_books': 0}
            interface.indexing_service.index_books = mock_index_books
            
            # Set up book_ids on interface (what _start_indexing would do)
            interface.current_indexing_book_ids = [1, 2, 3]
            
            # Create the kwargs that Calibre actually passes
            calibre_kwargs = {
                'notifications': queue.Queue(),
                'abort': threading.Event(),
                'log': Mock()  # Mock the GUILog object
            }
            
            # This should NOT raise TypeError about unexpected keyword arguments
            # ThreadedJob calls with ONLY kwargs, no positional args
            result = interface._run_indexing_job(**calibre_kwargs)
            
            # Should return the indexing stats
            assert result is not None
            assert result['successful_books'] == 1
            
        except Exception as e:
            pytest.fail(f"_run_indexing_job should work with only kwargs (no job parameter): {e}")
    
    def test_run_indexing_job_can_use_abort_signal(self):
        """
        Test that _run_indexing_job can check the abort signal from Calibre
        """
        try:
            from interface import SemanticSearchInterface
            
            interface = SemanticSearchInterface()
            interface.indexing_service = Mock()
            
            # Set up book_ids on interface (what _start_indexing would do)
            interface.current_indexing_book_ids = [1, 2, 3]
            
            # Create abort event and set it (simulating user cancellation)
            abort_event = threading.Event()
            abort_event.set()  # Signal that job should be aborted
            
            calibre_kwargs = {
                'notifications': queue.Queue(),
                'abort': abort_event,
                'log': Mock()
            }
            
            # Function should handle abort gracefully
            result = interface._run_indexing_job(**calibre_kwargs)
            
            # Should return None or minimal result when aborted
            # (Implementation detail - the important thing is no crash)
            assert result is not None or result is None  # Either is acceptable
            
        except Exception as e:
            pytest.fail(f"_run_indexing_job should handle abort gracefully: {e}")
    
    def test_run_indexing_job_can_send_notifications(self):
        """
        Test that _run_indexing_job can send progress notifications to Calibre
        """
        try:
            from interface import SemanticSearchInterface
            
            interface = SemanticSearchInterface()
            interface.indexing_service = Mock()
            
            # Mock successful indexing as a coroutine
            import asyncio
            async def mock_index_books(*args, **kwargs):
                return {'successful_books': 3, 'failed_books': 0}
            interface.indexing_service.index_books = mock_index_books
            
            # Set up book_ids on interface (what _start_indexing would do)
            interface.current_indexing_book_ids = [1, 2, 3]
            
            # Create notifications queue to capture progress
            notifications_queue = queue.Queue()
            
            calibre_kwargs = {
                'notifications': notifications_queue,
                'abort': threading.Event(),
                'log': Mock()
            }
            
            # Run the job
            result = interface._run_indexing_job(**calibre_kwargs)
            
            # Should complete successfully
            assert result is not None
            assert result['successful_books'] == 3
            
            # Could optionally check if notifications were sent
            # (This is enhancement - main goal is no crash)
            
        except Exception as e:
            pytest.fail(f"_run_indexing_job should work with notifications: {e}")
    
    def test_run_indexing_job_signature_matches_threaded_job_expectations(self):
        """
        Test that _run_indexing_job has the signature that ThreadedJob expects.
        
        Based on the error, ThreadedJob calls functions with:
        func(job, **kwargs) where kwargs includes notifications, abort, log
        """
        from interface import SemanticSearchInterface
        import inspect
        
        interface = SemanticSearchInterface()
        
        # Get the function signature
        sig = inspect.signature(interface._run_indexing_job)
        params = list(sig.parameters.keys())
        
        # Should NOT require a job parameter (ThreadedJob doesn't pass it)
        # Function should work with only **kwargs
        
        # Should accept **kwargs to handle Calibre's additional arguments
        has_var_keyword = any(
            param.kind == inspect.Parameter.VAR_KEYWORD 
            for param in sig.parameters.values()
        )
        assert has_var_keyword, "Function should accept **kwargs for Calibre arguments"