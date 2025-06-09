# UI Rework Plan - Focus Stealing Bug Fix

**Created:** 2025-06-09  
**Objective:** Fix focus-stealing bug by refactoring to MVP pattern

## Problem Analysis

### Current Issue
The `DynamicLocationComboBox` steals focus during typing due to:
1. Timer-based updates that refresh the widget
2. Mixing UI logic with view updates
3. Improper event handling during model updates

### Root Cause
The UI components violate the "UI is Dumb" principle by containing business logic that triggers unwanted updates.

## Solution Design

### MVP Architecture for DynamicLocationComboBox

```
┌─────────────────────────────────────────┐
│  DynamicLocationComboBox (View)         │
│  - Only handles Qt signals/slots        │
│  - No business logic                    │
│  - Simple setters for updating content  │
└──────────────────▲──────────────────────┘
                   │
┌──────────────────┼──────────────────────┐
│  LocationPresenter (Presenter)          │
│  - Handles typing detection             │
│  - Manages update timing                │
│  - Filters and formats location data    │
└──────────────────┴──────────────────────┘
```

## Implementation Plan (TDD)

### Phase 1: Write Failing Tests for Presenter
```python
# tests/ui/test_location_presenter.py
def test_presenter_delays_updates_during_typing():
    """Presenter should not update view while user is typing"""
    view = Mock()
    presenter = LocationPresenter(view)
    
    # Simulate typing
    presenter.on_text_changed("NYC")
    presenter.on_text_changed("NYC ")
    presenter.on_text_changed("NYC Public")
    
    # View should not be updated during typing
    view.update_locations.assert_not_called()
    
    # After typing stops (simulate delay)
    presenter._typing_timer_expired()
    
    # Now view should be updated once
    view.update_locations.assert_called_once()
```

### Phase 2: Create LocationPresenter
```python
# calibre_plugins/semantic_search/presenters/location_presenter.py
class LocationPresenter:
    TYPING_DELAY_MS = 500
    
    def __init__(self, view):
        self.view = view
        self.typing_timer = None
        self.pending_text = None
        
    def on_text_changed(self, text):
        """Handle text changes without immediate updates"""
        self.pending_text = text
        
        # Cancel existing timer
        if self.typing_timer:
            self.typing_timer.cancel()
            
        # Start new timer
        self.typing_timer = threading.Timer(
            self.TYPING_DELAY_MS / 1000.0,
            self._typing_timer_expired
        )
        self.typing_timer.start()
```

### Phase 3: Refactor DynamicLocationComboBox
```python
# calibre_plugins/semantic_search/ui/dynamic_location_combo_box.py
class DynamicLocationComboBox(QComboBox):
    def __init__(self):
        super().__init__()
        self.presenter = LocationPresenter(self)
        self.textChanged.connect(self.presenter.on_text_changed)
        
    def update_locations(self, locations):
        """Simple setter - just update the model"""
        current_text = self.currentText()
        
        self.blockSignals(True)
        self.clear()
        self.addItems(locations)
        self.setEditText(current_text)  # Preserve text
        self.blockSignals(False)
```

### Phase 4: Fix Event Handling
1. Use `blockSignals()` during updates
2. Preserve cursor position
3. Avoid triggering unnecessary events

## Test Cases

### Required Tests (TDD)
1. ✅ `test_typing_continuous_focus_preservation`
2. ✅ `test_no_qtimer_threading_errors_during_typing`  
3. ✅ `test_dropdown_updates_without_focus_interruption`
4. 🆕 `test_presenter_delays_updates_during_typing`
5. 🆕 `test_presenter_batches_rapid_changes`
6. 🆕 `test_view_preserves_cursor_position`
7. 🆕 `test_view_has_no_business_logic`

## Migration Strategy

1. **Create presenter tests first** (Red)
2. **Implement presenter** (Green)
3. **Create view refactoring tests** (Red)
4. **Refactor view to use presenter** (Green)
5. **Verify existing tests pass** (Refactor)
6. **Manual test in Calibre** (Verify)

## Success Criteria

- User can type continuously without focus loss
- Dropdown updates after typing stops (500ms delay)
- No Qt timer errors in console
- All existing functionality preserved
- Clean separation of view and logic

## Risk Mitigation

- Keep old implementation until new one verified
- Test extensively with different typing speeds
- Verify with multiple Calibre versions
- Document any Qt version-specific workarounds