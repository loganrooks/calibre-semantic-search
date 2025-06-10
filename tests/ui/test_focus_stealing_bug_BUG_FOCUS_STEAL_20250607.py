"""
BUG: Focus stealing during typing in location dropdown

This test captures the exact bug where typing in the location dropdown
gets interrupted because showPopup() steals focus from the line edit.

Bug ID: BUG-FOCUS-STEAL-20250607
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from PyQt5.Qt import QApplication, QWidget, QTimer
import time

# Add src to path for imports
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from calibre_plugins.semantic_search.ui.dynamic_location_combo_box import DynamicLocationComboBox


@pytest.fixture
def app():
    """Create QApplication for Qt tests"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def parent_widget(app):
    """Create parent widget for combo box"""
    widget = QWidget()
    widget.show()
    return widget


@pytest.fixture
def mock_fetcher():
    """Mock LocationDataFetcher to avoid network calls"""
    with patch('calibre_plugins.semantic_search.ui.dynamic_location_combo_box.LocationDataFetcher') as mock:
        mock_instance = Mock()
        mock.return_value = mock_instance
        yield mock_instance


class TestFocusStealingBug:
    """Test cases for the focus stealing bug during typing"""
    
    def test_typing_continuous_focus_preservation(self, app, parent_widget, mock_fetcher):
        """
        BUG: Focus gets stolen when typing triggers dropdown updates
        
        This test should FAIL until the bug is fixed.
        
        Expected behavior:
        1. User starts typing in line edit
        2. Dropdown updates with filtered results
        3. Line edit maintains focus throughout
        4. User can continue typing without interruption
        
        Actual broken behavior:
        1. User types first character
        2. showPopup() gets called which steals focus
        3. Line edit loses focus
        4. User must click back to continue typing
        """
        # Create combo box
        combo = DynamicLocationComboBox("vertex_ai", parent_widget)
        
        # Ensure line edit has focus initially
        line_edit = combo.lineEdit()
        assert line_edit is not None, "ComboBox should have line edit"
        
        line_edit.setFocus()
        app.processEvents()
        
        # Verify initial focus
        assert app.focusWidget() == line_edit, "Line edit should have initial focus"
        
        # Simulate user typing (this triggers the bug)
        line_edit.setText("us")
        line_edit.textEdited.emit("us")
        
        # Process events to trigger filtering
        app.processEvents()
        
        # BUG: At this point, showPopup() gets called and steals focus
        # The line edit should STILL have focus, but currently it doesn't
        current_focus = app.focusWidget()
        
        assert current_focus == line_edit, (
            f"BUG: Line edit should maintain focus during typing, "
            f"but focus is on {current_focus} instead. "
            f"This indicates showPopup() stole focus."
        )
    
    def test_no_qtimer_threading_errors_during_typing(self, app, parent_widget, mock_fetcher, caplog):
        """
        BUG: QTimer threading errors occur during focus restoration
        
        Expected: No threading errors should occur
        Actual: "QObject::killTimer: Timers cannot be stopped from another thread"
        """
        combo = DynamicLocationComboBox("vertex_ai", parent_widget)
        line_edit = combo.lineEdit()
        
        line_edit.setFocus()
        app.processEvents()
        
        # Simulate rapid typing that triggers multiple filter updates
        for char in "us-central1":
            current_text = line_edit.text() + char
            line_edit.setText(current_text)
            line_edit.textEdited.emit(current_text)
            app.processEvents()
            time.sleep(0.01)  # Small delay to simulate real typing
        
        # Check that no QTimer threading errors occurred
        error_messages = [record.message for record in caplog.records if "killTimer" in record.message]
        
        assert len(error_messages) == 0, (
            f"BUG: QTimer threading errors detected: {error_messages}. "
            f"This indicates unsafe timer usage across threads."
        )
    
    def test_dropdown_updates_without_focus_interruption(self, app, parent_widget, mock_fetcher):
        """
        BUG: Dropdown should update filtered results without stealing focus
        
        Expected behavior:
        1. User types -> dropdown model updates -> user continues typing
        
        Broken behavior:  
        1. User types -> showPopup() called -> focus stolen -> typing interrupted
        """
        combo = DynamicLocationComboBox("vertex_ai", parent_widget)
        line_edit = combo.lineEdit()
        
        # Mock some regions for filtering
        combo.all_regions = [
            Mock(code="us-central1", name="US Central 1", location="Iowa", popular=True),
            Mock(code="us-east1", name="US East 1", location="South Carolina", popular=True),
            Mock(code="europe-west1", name="Europe West 1", location="Belgium", popular=False),
        ]
        combo.filtered_regions = combo.all_regions.copy()
        
        line_edit.setFocus()
        app.processEvents()
        
        focus_widget_before = app.focusWidget()
        
        # Simulate typing that should filter results
        line_edit.setText("us")
        line_edit.textEdited.emit("us")
        app.processEvents()
        
        # Check that filtering occurred (should have 2 "us" regions)
        assert len(combo.filtered_regions) == 2, "Filtering should have occurred"
        
        # BUG: Focus should still be on line edit
        focus_widget_after = app.focusWidget()
        
        assert focus_widget_before == focus_widget_after == line_edit, (
            f"BUG: Focus changed from {focus_widget_before} to {focus_widget_after} "
            f"during filtering. This breaks continuous typing."
        )
    
    def test_showPopup_not_called_during_filtering(self, app, parent_widget, mock_fetcher):
        """
        BUG: showPopup() should NOT be called automatically during filtering
        
        showPopup() is designed to steal focus. It should only be called
        when user explicitly requests dropdown (double-click, focus, etc.)
        NOT during typing/filtering.
        """
        combo = DynamicLocationComboBox("vertex_ai", parent_widget)
        line_edit = combo.lineEdit()
        
        # Mock showPopup to track calls
        original_showPopup = combo.showPopup
        show_popup_calls = []
        
        def mock_showPopup():
            show_popup_calls.append("called")
            return original_showPopup()
        
        combo.showPopup = mock_showPopup
        
        # Set up regions for filtering
        combo.all_regions = [
            Mock(code="us-central1", name="US Central 1", location="Iowa", popular=True),
        ]
        combo.filtered_regions = combo.all_regions.copy()
        
        line_edit.setFocus()
        app.processEvents()
        
        # Simulate typing (this should NOT call showPopup)
        line_edit.setText("u")
        line_edit.textEdited.emit("u")
        app.processEvents()
        
        # BUG: showPopup should NOT have been called during filtering
        assert len(show_popup_calls) == 0, (
            f"BUG: showPopup() was called {len(show_popup_calls)} times during filtering. "
            f"This is the root cause of focus stealing. showPopup() should only be called "
            f"for explicit user actions, not automatic filtering."
        )