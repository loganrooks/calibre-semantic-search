"""
Test-driven development for LocationPresenter - MVP pattern implementation
"""

import pytest
import time
from unittest.mock import Mock, patch
from calibre_plugins.semantic_search.presenters.location_presenter import LocationPresenter


class TestLocationPresenter:
    """Test LocationPresenter for focus-stealing bug fix"""
    
    def test_presenter_delays_updates_during_typing(self):
        """Presenter should not update view while user is typing"""
        view = Mock()
        presenter = LocationPresenter(view)
        
        # Simulate typing sequence
        presenter.on_text_changed("NYC")
        presenter.on_text_changed("NYC ")
        presenter.on_text_changed("NYC Public")
        
        # View should not be updated during typing
        view.update_locations.assert_not_called()
        
        # After typing stops (simulate delay)
        presenter._typing_timer_expired()
        
        # Now view should be updated once
        view.update_locations.assert_called_once()
    
    def test_presenter_batches_rapid_changes(self):
        """Presenter should batch multiple rapid text changes into single update"""
        view = Mock()
        presenter = LocationPresenter(view)
        
        # Simulate rapid typing (10 changes)
        for i in range(10):
            presenter.on_text_changed(f"text{i}")
        
        # No updates should have happened yet
        view.update_locations.assert_not_called()
        
        # After typing timer expires
        presenter._typing_timer_expired()
        
        # Should only get one update with the latest text
        view.update_locations.assert_called_once()
        call_args = view.update_locations.call_args
        # The presenter should have processed the latest text
        assert call_args is not None
    
    def test_presenter_cancels_previous_timers(self):
        """Each text change should cancel previous timer"""
        view = Mock()
        presenter = LocationPresenter(view)
        
        # Start typing
        presenter.on_text_changed("first")
        first_timer = presenter.typing_timer
        
        # Type more (should cancel first timer)
        presenter.on_text_changed("second")
        second_timer = presenter.typing_timer
        
        # Timers should be different objects
        assert first_timer != second_timer
        
        # First timer should be cancelled
        assert not first_timer.is_alive()
        
        # Second timer should be active
        assert second_timer.is_alive()
        
        # Clean up
        second_timer.cancel()
    
    def test_presenter_handles_empty_text(self):
        """Presenter should handle empty/None text gracefully"""
        view = Mock()
        presenter = LocationPresenter(view)
        
        # Test with empty string
        presenter.on_text_changed("")
        presenter._typing_timer_expired()
        
        # Should still call update (even for empty)
        view.update_locations.assert_called_once()
        
        # Reset mock
        view.reset_mock()
        
        # Test with None (if that can happen)
        presenter.on_text_changed(None)
        presenter._typing_timer_expired()
        
        view.update_locations.assert_called_once()
    
    def test_presenter_typing_delay_configuration(self):
        """Presenter should use configurable typing delay"""
        view = Mock()
        presenter = LocationPresenter(view, typing_delay_ms=100)
        
        # Check that delay is configurable
        assert presenter.typing_delay_ms == 100
        
        # Default should be 500ms
        default_presenter = LocationPresenter(view)
        assert default_presenter.typing_delay_ms == 500
    
    @patch('threading.Timer')
    def test_presenter_uses_proper_timer_delay(self, mock_timer):
        """Presenter should create timer with correct delay"""
        view = Mock()
        presenter = LocationPresenter(view, typing_delay_ms=300)
        
        presenter.on_text_changed("test")
        
        # Timer should be created with 0.3 seconds (300ms)
        mock_timer.assert_called_with(0.3, presenter._typing_timer_expired)
    
    def test_presenter_cleanup(self):
        """Presenter should clean up timers on destruction"""
        view = Mock()
        presenter = LocationPresenter(view)
        
        presenter.on_text_changed("test")
        timer = presenter.typing_timer
        
        # Clean up
        presenter.cleanup()
        
        # Timer should be cancelled
        assert not timer.is_alive()
        assert presenter.typing_timer is None