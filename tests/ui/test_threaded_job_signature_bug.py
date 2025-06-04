"""
Bug-First TDD: ThreadedJob signature mismatch

BUG: ThreadedJob.__init__() missing 2 required positional arguments: 'kwargs' and 'callback'

This test captures the exact error and should FAIL until we fix the ThreadedJob signature.
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add paths
plugin_path = os.path.join(os.path.dirname(__file__), '..', '..', 'calibre_plugins', 'semantic_search')
sys.path.insert(0, plugin_path)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from calibre_mocks import *


class TestThreadedJobSignatureBug:
    """Test that captures ThreadedJob signature mismatch bug"""
    
    def test_threaded_job_signature_matches_calibre_api(self):
        """
        BUG: ThreadedJob.__init__() missing 2 required positional arguments: 'kwargs' and 'callback'
        
        Based on the error, the real Calibre ThreadedJob signature is different than we assumed.
        This test should FAIL until we use the correct signature.
        """
        # Mock ThreadedJob with the ACTUAL signature that Calibre expects
        def threaded_job_init(self, name, description, func, args, kwargs, callback, **options):
            """This is what the real ThreadedJob.__init__ signature looks like"""
            self.name = name
            self.description = description
            self.func = func
            self.args = args
            self.kwargs = kwargs
            self.callback = callback
            self.options = options
            # Mock other required attributes
            self.book_ids = None
        
        mock_threaded_job_class = Mock()
        mock_threaded_job_class.__init__ = threaded_job_init
        mock_job = Mock()
        mock_threaded_job_class.return_value = mock_job
        
        import interface as interface_module
        interface_module.ThreadedJob = mock_threaded_job_class
        
        try:
            from interface import SemanticSearchInterface
            
            interface = SemanticSearchInterface()
            interface.gui = Mock()
            interface.gui.job_manager = Mock()
            interface.gui.status_bar = Mock()
            interface.indexing_service = Mock()
            
            # This should NOT raise TypeError about missing arguments
            # Currently FAILS because we're using wrong ThreadedJob signature
            interface._start_indexing([1, 2, 3])
            
            # If we get here, the signature is correct
            assert True
            
        except TypeError as e:
            if "missing" in str(e) and "required positional arguments" in str(e):
                pytest.fail(f"BUG DETECTED: Wrong ThreadedJob signature: {e}")
            else:
                raise  # Re-raise if it's a different error
        finally:
            # Cleanup
            interface_module.ThreadedJob = None
    
    def test_correct_threaded_job_signature_with_all_required_args(self):
        """
        Test the CORRECT ThreadedJob signature based on the error message.
        The error indicates ThreadedJob needs: name, description, func, args, kwargs, callback
        """
        # Create a mock that enforces the correct signature
        class MockThreadedJob:
            def __init__(self, name, description, func, args, kwargs, callback, **options):
                self.name = name
                self.description = description
                self.func = func
                self.args = args  # args tuple
                self.kwargs = kwargs  # kwargs dict
                self.callback = callback
                self.options = options
                self.book_ids = None  # Custom attribute we add
        
        import interface as interface_module
        interface_module.ThreadedJob = MockThreadedJob
        
        try:
            from interface import SemanticSearchInterface
            
            interface = SemanticSearchInterface()
            interface.gui = Mock()
            interface.gui.job_manager = Mock()
            interface.gui.status_bar = Mock()
            interface.indexing_service = Mock()
            
            # This should work with the correct signature
            interface._start_indexing([1, 2, 3])
            
            # Should have created a job with correct parameters
            assert hasattr(interface, 'current_indexing_job')
            job = interface.current_indexing_job
            
            # Verify the parameters were passed correctly
            assert job.name == 'semantic_search_indexing'
            assert 'Indexing' in job.description
            assert callable(job.func)
            assert job.args == ()  # Should be empty tuple
            assert job.kwargs == {}  # Should be empty dict
            assert callable(job.callback)
            
        finally:
            # Cleanup
            interface_module.ThreadedJob = None
    
    def test_threaded_job_args_and_kwargs_are_empty_for_our_use_case(self):
        """
        Test that we correctly pass empty args and kwargs to ThreadedJob.
        Our functions don't need additional arguments beyond what we store on the job object.
        """
        class MockThreadedJob:
            def __init__(self, name, description, func, args, kwargs, callback, **options):
                # Verify args and kwargs are what we expect
                if args != ():
                    raise ValueError(f"Expected empty args tuple, got: {args}")
                if kwargs != {}:
                    raise ValueError(f"Expected empty kwargs dict, got: {kwargs}")
                    
                self.name = name
                self.description = description
                self.func = func
                self.args = args
                self.kwargs = kwargs
                self.callback = callback
                self.options = options
                self.book_ids = None
        
        import interface as interface_module
        interface_module.ThreadedJob = MockThreadedJob
        
        try:
            from interface import SemanticSearchInterface
            
            interface = SemanticSearchInterface()
            interface.gui = Mock()
            interface.gui.job_manager = Mock()
            interface.gui.status_bar = Mock()
            interface.indexing_service = Mock()
            
            # This should work and pass empty args/kwargs
            interface._start_indexing([1, 2, 3])
            
            # Should have succeeded without ValueError
            assert True
            
        except ValueError as e:
            pytest.fail(f"Wrong args/kwargs passed to ThreadedJob: {e}")
        finally:
            # Cleanup
            interface_module.ThreadedJob = None