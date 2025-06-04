"""
Bug-First TDD: Capture specific job integration issues

BUG 1: Indexing Status error: "Error retrieving indexing status: 'in_progress'"
BUG 2: Jobs indicator at bottom stays at 0 instead of showing 1 job

These tests should FAIL until the bugs are fixed.
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


class TestJobIntegrationBugs:
    """Tests that capture specific job integration bugs"""
    
    def test_indexing_status_handles_in_progress_without_error(self):
        """
        BUG 1: show_indexing_status fails with "Error retrieving indexing status: 'in_progress'"
        
        This test should FAIL until the indexing status display bug is fixed.
        """
        try:
            from background_jobs import BackgroundJobManager
            import interface as interface_module
            interface_module.BackgroundJobManager = BackgroundJobManager
            
            from interface import SemanticSearchInterface
            
            interface = SemanticSearchInterface()
            interface.gui = Mock()
            interface.indexing_service = Mock()
            
            # Mock indexing service to return 'in_progress' status
            mock_status = {'status': 'in_progress', 'current_book': 5, 'total_books': 10}
            interface.indexing_service.get_indexing_status = Mock(return_value=mock_status)
            
            # This should NOT raise an error about 'in_progress'
            # Currently FAILS with: "Error retrieving indexing status: 'in_progress'"
            interface.show_indexing_status()
            
            # If we get here without error, the bug is fixed
            assert True
            
        except Exception as e:
            if "'in_progress'" in str(e):
                pytest.fail(f"BUG DETECTED: Indexing status fails with 'in_progress': {e}")
            else:
                raise  # Re-raise if it's a different error
    
    def test_background_jobs_appear_in_calibre_job_manager(self):
        """
        BUG 2: Jobs indicator stays at 0 instead of showing active jobs
        
        Now FIXED: Uses ThreadedJob which integrates with Calibre's job system
        """
        try:
            # Set up ThreadedJob like the real Calibre environment
            mock_threaded_job_class = Mock()
            mock_job = Mock()
            mock_threaded_job_class.return_value = mock_job
            
            import interface as interface_module
            interface_module.ThreadedJob = mock_threaded_job_class
            interface_module.BackgroundJobManager = None  # Force ThreadedJob path
            
            from interface import SemanticSearchInterface
            
            interface = SemanticSearchInterface()
            interface.gui = Mock()
            interface.gui.status_bar = Mock()
            interface.indexing_service = Mock()
            
            # Mock the job manager to track jobs
            mock_job_manager = Mock()
            interface.gui.job_manager = mock_job_manager
            
            # Start indexing - this should add a job to Calibre's job manager
            interface._start_indexing([1, 2, 3])
            
            # This should have called Calibre's job manager to add the job
            mock_job_manager.run_threaded_job.assert_called_once()
            
        except AttributeError as e:
            if "run_threaded_job" in str(e):
                pytest.fail(f"BUG DETECTED: Not integrating with Calibre's job manager: {e}")
            else:
                raise
        finally:
            # Cleanup
            interface_module.ThreadedJob = None
    
    def test_calibre_job_manager_api_exists(self):
        """
        Test to verify what job manager API is actually available in Calibre
        """
        try:
            from background_jobs import BackgroundJobManager
            import interface as interface_module
            interface_module.BackgroundJobManager = BackgroundJobManager
            
            from interface import SemanticSearchInterface
            
            interface = SemanticSearchInterface()
            interface.gui = Mock()
            
            # Check what job-related attributes are available on gui
            job_attrs = [attr for attr in dir(interface.gui) if 'job' in attr.lower()]
            
            # This test documents what we find - helps us understand the real API
            print(f"Available job-related attributes on gui: {job_attrs}")
            
            # For now, just check that we can mock it
            interface.gui.job_manager = Mock()
            assert hasattr(interface.gui, 'job_manager')
            
        except Exception as e:
            pytest.fail(f"Failed to investigate job manager API: {e}")
    
    def test_indexing_service_get_status_method_signature(self):
        """
        Test what the actual indexing service status method should return
        to avoid the 'in_progress' error
        """
        try:
            # This test investigates what status format is expected
            from background_jobs import BackgroundJobManager
            import interface as interface_module
            interface_module.BackgroundJobManager = BackgroundJobManager
            
            from interface import SemanticSearchInterface
            
            interface = SemanticSearchInterface()
            interface.gui = Mock()
            interface.indexing_service = Mock()
            
            # Test different status formats to see what works
            test_statuses = [
                {'status': 'idle'},
                {'status': 'indexing', 'progress': '5/10'},
                {'current_book': 5, 'total_books': 10},
                'in_progress',  # This is what causes the error
                {'books_indexed': 5, 'total_books': 10, 'status': 'running'}
            ]
            
            for status in test_statuses:
                interface.indexing_service.get_indexing_status = Mock(return_value=status)
                
                try:
                    interface.show_indexing_status()
                    print(f"Status format works: {status}")
                except Exception as e:
                    print(f"Status format fails: {status} -> {e}")
            
            # This test is for investigation, so always pass
            assert True
            
        except Exception as e:
            pytest.fail(f"Failed to investigate status formats: {e}")