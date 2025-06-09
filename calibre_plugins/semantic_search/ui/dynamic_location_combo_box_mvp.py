"""
DynamicLocationComboBox - MVP Pattern Implementation

This is the refactored version following MVP architecture to fix focus-stealing bug.
The original version is preserved in dynamic_location_combo_box.py for safety.
"""

import logging
from typing import List, Optional

# Use Calibre's Qt abstraction layer instead of direct PyQt5 imports
try:
    from qt.core import (
        QComboBox, QCompleter, QStringListModel, QTimer, QLabel,
        QHBoxLayout, QWidget, QToolButton, QMenu, QAction,
        Qt, QSize, QPixmap, QIcon, QPainter, QColor, QBrush, QPen, QApplication,
        QEvent, QFocusEvent
    )
except ImportError:
    # Fallback for testing outside Calibre
    from PyQt5.Qt import (
        QComboBox, QCompleter, QStringListModel, QTimer, QLabel,
        QHBoxLayout, QWidget, QToolButton, QMenu, QAction,
        Qt, QSize, QPixmap, QIcon, QPainter, QColor, QBrush, QPen, QApplication,
        QEvent, QFocusEvent
    )

from ..presenters.location_combo_presenter import LocationComboPresenter


class LoadingIndicator(QLabel):
    """Animated loading indicator for the combo box"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(16, 16)
        self.setVisible(False)
        
        # Create a simple animated loading indicator
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_animation)
        self.angle = 0
        
    def start_animation(self):
        """Start the loading animation"""
        self.setVisible(True)
        self.timer.start(100)  # Update every 100ms
        
    def stop_animation(self):
        """Stop the loading animation"""
        self.timer.stop()
        self.setVisible(False)
        self.angle = 0
        
    def _update_animation(self):
        """Update the loading animation"""
        self.angle = (self.angle + 30) % 360
        self.update()  # Trigger paintEvent
        
    def paintEvent(self, event):
        """Draw the rotating loading indicator"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Clear background
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))
        
        # Draw loading spinner
        center = self.rect().center()
        radius = 6
        
        painter.translate(center)
        painter.rotate(self.angle)
        
        # Draw dots around circle
        for i in range(8):
            alpha = 255 - (i * 30)
            alpha = max(alpha, 50)
            
            painter.setBrush(QBrush(QColor(100, 100, 100, alpha)))
            painter.setPen(QPen(QColor(100, 100, 100, alpha)))
            
            painter.drawEllipse(radius - 1, -1, 2, 2)
            painter.rotate(45)


class DynamicLocationComboBox(QComboBox):
    """
    MVP Pattern Implementation of Dynamic Location ComboBox
    
    This view is "dumb" - it only handles UI updates and delegates all business logic
    to the LocationComboPresenter. This prevents focus-stealing by ensuring view
    updates are properly debounced and controlled by the presenter.
    """
    
    def __init__(self, provider_type: str, parent=None):
        super().__init__(parent)
        
        # Initialize logger
        self.logger = logging.getLogger(f'calibre_plugins.semantic_search.ui.dynamic_location_combo_box')
        self.logger.info(f"Initializing DynamicLocationComboBox for {provider_type}")
        
        self.provider_type = provider_type
        
        # Setup basic UI components
        self._setup_combo_box()
        self._setup_loading_indicator()
        self._setup_completer()
        self._setup_context_menu()
        
        # Initialize presenter (MVP pattern)
        self.presenter = LocationComboPresenter(self, provider_type)
        
        # Connect text changes to presenter (with debouncing)
        if self.lineEdit():
            self.lineEdit().textChanged.connect(self.presenter.on_text_changed)
        
        self.logger.info(f"DynamicLocationComboBox initialized for {provider_type}")
    
    def _setup_combo_box(self):
        """Configure the combo box for optimal user experience"""
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.NoInsert)
        self.setDuplicatesEnabled(False)
        self.setMaxVisibleItems(15)
        
        # Configure placeholder
        placeholder_map = {
            "vertex_ai": "Type to search GCP regions (e.g., us-central1)...",
            "direct_vertex_ai": "Type to search GCP regions (e.g., us-central1)...",
            "azure_openai": "Type to search Azure regions (e.g., eastus)...",
            "aws": "Type to search AWS regions (e.g., us-east-1)..."
        }
        placeholder = placeholder_map.get(self.provider_type, "Type to search regions...")
        
        if self.lineEdit():
            self.lineEdit().setPlaceholderText(placeholder)
    
    def _setup_completer(self):
        """Setup QCompleter for live filtering without focus stealing"""
        self.completer = QCompleter(self)
        self.completer_model = QStringListModel(self)
        self.completer.setModel(self.completer_model)
        
        # Configure completer for optimal UX
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchContains)
        self.completer.setMaxVisibleItems(15)
        
        # Set completion mode
        if hasattr(QCompleter, 'PopupCompletion'):
            self.completer.setCompletionMode(QCompleter.PopupCompletion)
        elif hasattr(QCompleter, 'UnfilteredPopupCompletion'):
            self.completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        
        # Connect to line edit
        if self.lineEdit():
            self.lineEdit().setCompleter(self.completer)
        
        # Handle completion selection
        self.completer.activated.connect(self._on_completion_selected)
        
        # Store mapping of display text to region code
        self.completion_to_code = {}
    
    def _on_completion_selected(self, completion_text: str):
        """Handle when user selects a completion"""
        region_code = self.completion_to_code.get(completion_text, completion_text)
        
        # Set the region code in the line edit
        if self.lineEdit():
            self.lineEdit().setText(region_code)
            self.editTextChanged.emit(region_code)
    
    def _setup_loading_indicator(self):
        """Setup loading indicator widget"""
        self.loading_indicator = LoadingIndicator(self)
        self._position_loading_indicator()
        
    def _position_loading_indicator(self):
        """Position the loading indicator within the combo box"""
        combo_rect = self.rect()
        indicator_x = combo_rect.width() - 35  # 35px from right edge
        indicator_y = (combo_rect.height() - 16) // 2  # Center vertically
        self.loading_indicator.move(indicator_x, indicator_y)
    
    def resizeEvent(self, event):
        """Handle resize events to reposition loading indicator"""
        super().resizeEvent(event)
        self._position_loading_indicator()
    
    def _setup_context_menu(self):
        """Setup context menu functionality"""
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
    
    def _show_context_menu(self, position):
        """Show context menu with refresh options"""
        menu = QMenu(self)
        
        refresh_action = QAction("🔄 Refresh Regions", self)
        refresh_action.triggered.connect(lambda: self.presenter.refresh_regions())
        menu.addAction(refresh_action)
        
        clear_cache_action = QAction("🗑️ Clear Cache", self)
        clear_cache_action.triggered.connect(lambda: self.presenter.clear_cache())
        menu.addAction(clear_cache_action)
        
        menu.addSeparator()
        
        status_action = QAction(f"📍 Provider: {self.provider_type}", self)
        status_action.setEnabled(False)
        menu.addAction(status_action)
        
        region_count_action = QAction(f"📊 Regions: {self.presenter.get_total_count()}", self)
        region_count_action.setEnabled(False)
        menu.addAction(region_count_action)
        
        menu.exec_(self.mapToGlobal(position))
    
    # MVP VIEW INTERFACE - These methods are called by the presenter
    
    def update_locations(self, location_strings: List[str]):
        """
        Update the combo box with new location data.
        This is a simple setter with no business logic (MVP pattern).
        
        Args:
            location_strings: List of formatted location strings for display
        """
        # Preserve current text and cursor position to prevent focus stealing
        current_text = ""
        cursor_position = 0
        
        if self.lineEdit():
            current_text = self.lineEdit().text()
            cursor_position = self.lineEdit().cursorPosition()
        
        # Block signals during update to prevent recursion
        self.blockSignals(True)
        
        try:
            # Update completer data
            self.completer_model.setStringList(location_strings)
            
            # Update completion mapping
            self.completion_to_code.clear()
            for location_str in location_strings:
                # Extract region code from formatted string
                if " (" in location_str:
                    # Format: "⭐ us-central1 (Iowa)" -> "us-central1"
                    parts = location_str.split(" (")
                    if len(parts) >= 2:
                        code_part = parts[0]
                        # Remove emoji prefix if present
                        if code_part.startswith(("⭐ ", "✅ ", "⚠️ ")):
                            region_code = code_part[2:]  # Remove emoji and space
                        else:
                            region_code = code_part
                        self.completion_to_code[location_str] = region_code
                        # Also map the code directly
                        self.completion_to_code[region_code] = region_code
                else:
                    # Plain region code
                    self.completion_to_code[location_str] = location_str
            
            # Restore text and cursor position
            if self.lineEdit():
                self.lineEdit().setText(current_text)
                self.lineEdit().setCursorPosition(cursor_position)
        
        finally:
            # Re-enable signals
            self.blockSignals(False)
    
    def set_loading_state(self, is_loading: bool):
        """
        Set the loading state of the combo box.
        
        Args:
            is_loading: Whether the combo box is in loading state
        """
        if is_loading:
            self.loading_indicator.start_animation()
            if self.lineEdit():
                original_placeholder = self.lineEdit().placeholderText()
                self.lineEdit().setPlaceholderText("Loading regions...")
        else:
            self.loading_indicator.stop_animation()
            if self.lineEdit():
                # Restore appropriate placeholder
                placeholder_map = {
                    "vertex_ai": "Type to search GCP regions (e.g., us-central1)...",
                    "direct_vertex_ai": "Type to search GCP regions (e.g., us-central1)...",
                    "azure_openai": "Type to search Azure regions (e.g., eastus)...",
                    "aws": "Type to search AWS regions (e.g., us-east-1)..."
                }
                placeholder = placeholder_map.get(self.provider_type, "Type to search regions...")
                self.lineEdit().setPlaceholderText(placeholder)
    
    # PUBLIC API (delegates to presenter)
    
    def get_region_code(self) -> str:
        """Get the selected region code"""
        if self.lineEdit():
            return self.lineEdit().text().strip()
        return ""
    
    def set_region_code(self, region_code: str):
        """Set the selected region"""
        if self.lineEdit():
            self.lineEdit().setText(region_code)
    
    def update_provider_via_presenter(self, new_provider_type: str):
        """Update provider through presenter (MVP pattern)"""
        self.provider_type = new_provider_type
        self.presenter.on_provider_changed(new_provider_type)
    
    def get_region_info(self, region_code: str):
        """Get detailed info for a region code (delegate to presenter)"""
        return self.presenter.get_region_info(region_code)
    
    def get_total_count(self) -> int:
        """Get total number of regions available (delegate to presenter)"""
        return self.presenter.get_total_count()
    
    def is_region_popular(self, region_code: str) -> bool:
        """Check if a region is marked as popular (delegate to presenter)"""
        return self.presenter.is_region_popular(region_code)
    
    def cleanup(self):
        """Clean up resources"""
        if hasattr(self, 'presenter'):
            self.presenter.cleanup()
        
        if hasattr(self, 'loading_indicator'):
            self.loading_indicator.stop_animation()