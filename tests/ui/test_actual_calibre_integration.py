"""
Test that captures real Calibre integration bugs

This test file captures bugs that occur when actually running in Calibre,
following TDD best practice of writing failing tests for bugs before fixing them.
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


class TestActualCalibreIntegration:
    """Tests that capture real Calibre integration issues"""
    
    def test_interface_index_selected_books_without_threaded_job_error(self):
        """
        BUG: interface.py line 248 still has broken ThreadedJob code
        ERROR: ThreadedJob.__init__() got an unexpected keyword argument 'job_data'
        
        This test should FAIL until the bug is fixed.
        """
        try:
            # Import and set up interface
            from background_jobs import BackgroundJobManager
            import interface as interface_module
            interface_module.BackgroundJobManager = BackgroundJobManager
            
            from interface import SemanticSearchInterface
            
            interface = SemanticSearchInterface()
            interface.gui = Mock()
            interface.gui.current_view = Mock()
            interface.gui.current_view.return_value.selectionModel.return_value.selectedRows.return_value = [Mock(), Mock()]
            interface.gui.status_bar = Mock()
            interface.indexing_service = Mock()
            
            # This should NOT raise ThreadedJob errors
            # Currently FAILS with: ThreadedJob.__init__() got an unexpected keyword argument 'job_data'
            interface.index_selected_books()
            
            # If we get here without error, the bug is fixed
            assert True
            
        except TypeError as e:
            if "ThreadedJob" in str(e) and "job_data" in str(e):
                pytest.fail(f"BUG DETECTED: ThreadedJob still being used incorrectly: {e}")
            else:
                raise  # Re-raise if it's a different error
    
    def test_interface_does_not_import_threaded_job_at_all(self):
        """
        Test that interface.py doesn't import ThreadedJob anymore
        since it was causing errors in actual Calibre.
        """
        # Read the interface.py file content
        interface_file_path = os.path.join(
            os.path.dirname(__file__), 
            '..', '..', 'calibre_plugins', 'semantic_search', 'interface.py'
        )
        
        with open(interface_file_path, 'r') as f:
            content = f.read()
        
        # Should not contain ThreadedJob imports or usage
        assert "from calibre.gui2.threaded_jobs import ThreadedJob" not in content, \
            "interface.py still imports ThreadedJob - this causes Calibre errors"
        
        assert "ThreadedJob(" not in content, \
            "interface.py still creates ThreadedJob instances - this causes Calibre errors"
    
    def test_interface_uses_background_job_manager_instead(self):
        """
        Test that interface.py uses our BackgroundJobManager instead of ThreadedJob
        """
        try:
            from background_jobs import BackgroundJobManager
            import interface as interface_module
            interface_module.BackgroundJobManager = BackgroundJobManager
            
            from interface import SemanticSearchInterface
            
            interface = SemanticSearchInterface()
            interface.gui = Mock()
            interface.gui.current_view = Mock()
            interface.gui.current_view.return_value.selectionModel.return_value.selectedRows.return_value = [Mock()]
            interface.gui.status_bar = Mock()
            interface.indexing_service = Mock()
            
            # Should use BackgroundJobManager, not ThreadedJob
            interface.index_selected_books()
            
            # Verify BackgroundJobManager was created
            assert hasattr(interface, 'job_manager')
            assert isinstance(interface.job_manager, BackgroundJobManager)
            
        except ImportError as e:
            pytest.fail(f"BackgroundJobManager integration missing: {e}")
    
    def test_interface_start_indexing_works_without_calibre_specific_imports(self):
        """
        Test that _start_indexing works without any Calibre-specific job imports
        """
        try:
            from background_jobs import BackgroundJobManager
            import interface as interface_module
            interface_module.BackgroundJobManager = BackgroundJobManager
            
            from interface import SemanticSearchInterface
            
            interface = SemanticSearchInterface()
            interface.gui = Mock()
            interface.gui.status_bar = Mock()
            interface.indexing_service = Mock()
            
            # This should work without any ThreadedJob errors
            interface._start_indexing([1, 2, 3])
            
            # Should have created a job using BackgroundJobManager
            assert hasattr(interface, 'current_indexing_job_id')
            assert interface.current_indexing_job_id is not None
            
        except Exception as e:
            if "ThreadedJob" in str(e):
                pytest.fail(f"Still using ThreadedJob - causes Calibre errors: {e}")
            else:
                raise