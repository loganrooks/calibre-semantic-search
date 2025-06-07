"""
Dynamic Location ComboBox with Real-time Filtering

Advanced QComboBox that fetches cloud provider regions dynamically from APIs,
provides instant search filtering, and maintains excellent user experience
with loading states, error handling, and intelligent caching.
"""

import logging
from typing import List, Optional, Callable
from PyQt5.Qt import (
    QComboBox, QCompleter, QStringListModel, QTimer, QMovie, QLabel,
    QHBoxLayout, QWidget, QProgressBar, QToolButton, QMenu, QAction,
    Qt, QSize, QPixmap, QIcon, QPainter, QColor, QBrush, QPen
)

try:
    from ..core.location_fetcher import LocationDataFetcher, CloudRegion
except ImportError:
    # Fallback for testing
    LocationDataFetcher = None
    CloudRegion = None

logger = logging.getLogger(__name__)


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
    Advanced location dropdown with dynamic data fetching and real-time filtering
    
    Features:
    - Dynamic fetching from cloud provider APIs
    - Real-time search filtering as you type
    - Loading indicators and status feedback
    - Intelligent caching with TTL
    - Graceful fallback to static data
    - Refresh functionality
    - Popular regions prioritized
    """
    
    def __init__(self, provider_type: str, parent=None):
        super().__init__(parent)
        self.provider_type = provider_type
        self.all_regions: List[CloudRegion] = []
        self.filtered_regions: List[CloudRegion] = []
        self.is_loading = False
        self.last_filter_text = ""
        
        # Initialize fetcher
        self.fetcher = LocationDataFetcher() if LocationDataFetcher else None
        
        self._setup_combo_box()
        self._setup_loading_indicator()
        self._setup_refresh_functionality()
        self._setup_filtering()
        
        # Start initial data fetch
        self._fetch_regions_async()
    
    def _setup_combo_box(self):
        """Configure the combo box for optimal filtering experience"""
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.NoInsert)
        self.setDuplicatesEnabled(False)
        self.setMaxVisibleItems(15)  # Show more items in dropdown
        
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
            
        # Enhanced interaction patterns for better UX
        self._setup_interaction_patterns()
    
    def _setup_loading_indicator(self):
        """Setup loading indicator widget"""
        self.loading_indicator = LoadingIndicator(self)
        
        # Position loading indicator in the combo box
        self._position_loading_indicator()
        
    def _position_loading_indicator(self):
        """Position the loading indicator within the combo box"""
        # Calculate position (right side of the combo box, before the dropdown arrow)
        combo_rect = self.rect()
        indicator_x = combo_rect.width() - 35  # 35px from right edge
        indicator_y = (combo_rect.height() - 16) // 2  # Center vertically
        
        self.loading_indicator.move(indicator_x, indicator_y)
    
    def resizeEvent(self, event):
        """Handle resize events to reposition loading indicator"""
        super().resizeEvent(event)
        self._position_loading_indicator()
    
    def _setup_refresh_functionality(self):
        """Setup refresh functionality with context menu"""
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
    
    def _show_context_menu(self, position):
        """Show context menu with refresh option"""
        menu = QMenu(self)
        
        refresh_action = QAction("🔄 Refresh Regions", self)
        refresh_action.triggered.connect(self._refresh_regions)
        menu.addAction(refresh_action)
        
        clear_cache_action = QAction("🗑️ Clear Cache", self)
        clear_cache_action.triggered.connect(self._clear_cache)
        menu.addAction(clear_cache_action)
        
        menu.addSeparator()
        
        status_action = QAction(f"📍 Provider: {self.provider_type}", self)
        status_action.setEnabled(False)
        menu.addAction(status_action)
        
        region_count_action = QAction(f"📊 Regions: {len(self.all_regions)}", self)
        region_count_action.setEnabled(False)
        menu.addAction(region_count_action)
        
        menu.exec_(self.mapToGlobal(position))
    
    def _setup_interaction_patterns(self):
        """Setup enhanced interaction patterns for better UX"""
        if self.lineEdit():
            # Store original event handlers
            original_double_click = self.lineEdit().mouseDoubleClickEvent
            original_focus_in = self.lineEdit().focusInEvent
            
            def enhanced_double_click(event):
                """Double-click to show all regions and select text"""
                # Clear any filter to show all regions
                if self.lineEdit().text():
                    self.lineEdit().clear()
                    self.last_filter_text = ""
                    self.filtered_regions = self.all_regions.copy()
                    self._populate_combo_with_regions_smart(self.all_regions, "")
                
                # Show dropdown
                if not self.view().isVisible():
                    self.showPopup()
                
                # Call original handler to select text
                original_double_click(event)
            
            def enhanced_focus_in(event):
                """Focus in - optionally show dropdown for easier access"""
                # Call original handler first
                original_focus_in(event)
                
                # If field is empty and user focuses, show dropdown with all regions
                if not self.lineEdit().text() and not self.view().isVisible():
                    # Small delay to let focus settle
                    QTimer.singleShot(100, self.showPopup)
            
            # Install enhanced event handlers
            self.lineEdit().mouseDoubleClickEvent = enhanced_double_click
            self.lineEdit().focusInEvent = enhanced_focus_in
    
    def _setup_filtering(self):
        """Setup real-time filtering as user types"""
        if self.lineEdit():
            self.lineEdit().textEdited.connect(self._on_text_edited)
            self.editTextChanged.connect(self._on_edit_text_changed)
        
        # Setup timer for delayed filtering (better performance)
        self.filter_timer = QTimer()
        self.filter_timer.setSingleShot(True)
        self.filter_timer.timeout.connect(self._apply_filter)
        
    def _on_text_edited(self, text: str):
        """Handle text editing with delayed filtering"""
        self.filter_timer.stop()
        self.filter_timer.start(150)  # 150ms delay for better performance
        
    def _on_edit_text_changed(self, text: str):
        """Handle text changes from selection"""
        # Don't filter when user selects from dropdown
        if self.currentIndex() >= 0:
            return
    
    def _apply_filter(self):
        """Apply search filter to regions with improved UX"""
        filter_text = self.lineEdit().text().lower().strip() if self.lineEdit() else ""
        
        # Don't re-filter if text hasn't changed
        if filter_text == self.last_filter_text:
            return
        
        self.last_filter_text = filter_text
        
        if not filter_text:
            # Show all regions when no filter
            self.filtered_regions = self.all_regions.copy()
        else:
            # Filter regions by code, name, or location
            self.filtered_regions = []
            for region in self.all_regions:
                if (filter_text in region.code.lower() or 
                    filter_text in region.name.lower() or
                    filter_text in region.location.lower()):
                    self.filtered_regions.append(region)
        
        # Update combo box items (but preserve user's input text)
        self._populate_combo_with_regions_smart(self.filtered_regions, filter_text)
        
        # Always show dropdown when user is typing (better UX)
        if filter_text and not self.view().isVisible():
            self.showPopup()
    
    def _fetch_regions_async(self, force_refresh: bool = False):
        """Fetch regions asynchronously"""
        if not self.fetcher:
            # Fallback to static data
            self._load_static_fallback()
            return
        
        if self.is_loading:
            return
        
        self.is_loading = True
        self.loading_indicator.start_animation()
        
        # Update placeholder to show loading
        if self.lineEdit():
            original_placeholder = self.lineEdit().placeholderText()
            self.lineEdit().setPlaceholderText("Loading regions...")
        
        def on_regions_received(regions: List[CloudRegion]):
            """Callback when regions are fetched"""
            self.is_loading = False
            self.loading_indicator.stop_animation()
            
            # Restore original placeholder
            if self.lineEdit():
                placeholder_map = {
                    "vertex_ai": "Type to search GCP regions (e.g., us-central1)...",
                    "direct_vertex_ai": "Type to search GCP regions (e.g., us-central1)...",
                    "azure_openai": "Type to search Azure regions (e.g., eastus)...",
                    "aws": "Type to search AWS regions (e.g., us-east-1)..."
                }
                placeholder = placeholder_map.get(self.provider_type, "Type to search regions...")
                self.lineEdit().setPlaceholderText(placeholder)
            
            # Update regions
            self.all_regions = regions
            self.filtered_regions = regions.copy()
            self._populate_combo_with_regions(regions)
            
            logger.info(f"Loaded {len(regions)} regions for {self.provider_type}")
        
        # Fetch regions asynchronously
        self.fetcher.get_regions_async(
            provider=self.provider_type,
            callback=on_regions_received,
            force_refresh=force_refresh
        )
    
    def _load_static_fallback(self):
        """Load static fallback data when fetcher is not available"""
        try:
            from ..core.cloud_regions import CloudRegionsData
            static_data = CloudRegionsData()
            regions_dict = static_data.get_regions(self.provider_type)
            
            # Convert to CloudRegion objects
            regions = []
            for region_dict in regions_dict:
                if CloudRegion:
                    region = CloudRegion(
                        code=region_dict["code"],
                        name=region_dict["name"],
                        location=region_dict["name"],
                        popular=region_dict.get("popular", False),
                        provider=self.provider_type,
                        status="available"
                    )
                    regions.append(region)
            
            self.all_regions = regions
            self.filtered_regions = regions.copy()
            self._populate_combo_with_regions(regions)
            
        except Exception as e:
            logger.error(f"Failed to load static fallback: {e}")
    
    def _populate_combo_with_regions(self, regions: List[CloudRegion]):
        """Legacy method - now calls smart version"""
        self._populate_combo_with_regions_smart(regions, "")
    
    def _populate_combo_with_regions_smart(self, regions: List[CloudRegion], filter_text: str = ""):
        """
        Populate combo box with region data using improved UX
        
        Args:
            regions: List of regions to show
            filter_text: Current filter text (to preserve user input)
        """
        # Save current text to preserve user's typing
        current_text = self.lineEdit().text() if self.lineEdit() else ""
        
        # Temporarily block signals to prevent interference
        self.blockSignals(True)
        
        try:
            # Clear existing items
            self.clear()
            
            if not regions and filter_text:
                # Show "No regions found" as disabled item when filtering
                no_match_item = f"🔍 No regions found for '{filter_text}'"
                self.addItem(no_match_item, None)
                # Make this item non-selectable
                model = self.model()
                if model and model.rowCount() > 0:
                    item = model.item(0)
                    if item:
                        item.setEnabled(False)
                        item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            elif not regions:
                # No regions available at all
                self.addItem("📭 No regions available", None)
                model = self.model()
                if model and model.rowCount() > 0:
                    item = model.item(0)
                    if item:
                        item.setEnabled(False)
                        item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            else:
                # Sort regions: popular first, then alphabetically
                popular_regions = [r for r in regions if r.popular]
                other_regions = [r for r in regions if not r.popular]
                
                popular_regions.sort(key=lambda x: x.code)
                other_regions.sort(key=lambda x: x.code)
                
                # Add popular regions first
                for region in popular_regions:
                    display_text = f"⭐ {region.code} ({region.name})"
                    self.addItem(display_text, region.code)
                
                # Add separator if we have both popular and other regions
                if popular_regions and other_regions:
                    self.insertSeparator(len(popular_regions))
                
                # Add other regions
                for region in other_regions:
                    status_icon = "✅" if region.status == "available" else "⚠️"
                    display_text = f"{status_icon} {region.code} ({region.name})"
                    self.addItem(display_text, region.code)
        
        finally:
            # Re-enable signals
            self.blockSignals(False)
            
            # CRITICAL: Always restore user's text - never interfere with typing!
            if current_text and self.lineEdit():
                self.lineEdit().setText(current_text)
    
    def get_region_code(self) -> str:
        """Get the selected region code"""
        current_data = self.currentData()
        if current_data:
            return current_data
        
        # Return text as-is for custom entries
        return self.lineEdit().text().strip() if self.lineEdit() else ""
    
    def set_region_code(self, region_code: str):
        """Set the selected region"""
        if not region_code:
            if self.lineEdit():
                self.lineEdit().setText("")
            return
        
        # Try to find in existing items
        for i in range(self.count()):
            if self.itemData(i) == region_code:
                self.setCurrentIndex(i)
                return
        
        # Set as custom text
        if self.lineEdit():
            self.lineEdit().setText(region_code)
    
    def update_provider(self, new_provider_type: str):
        """Update provider and refresh data"""
        if new_provider_type != self.provider_type:
            self.provider_type = new_provider_type
            self.all_regions.clear()
            self.filtered_regions.clear()
            
            # Update placeholder
            placeholder_map = {
                "vertex_ai": "Type to search GCP regions (e.g., us-central1)...",
                "direct_vertex_ai": "Type to search GCP regions (e.g., us-central1)...",
                "azure_openai": "Type to search Azure regions (e.g., eastus)...",
                "aws": "Type to search AWS regions (e.g., us-east-1)..."
            }
            placeholder = placeholder_map.get(self.provider_type, "Type to search regions...")
            
            if self.lineEdit():
                self.lineEdit().setPlaceholderText(placeholder)
            
            # Fetch new data
            self._fetch_regions_async()
    
    def _refresh_regions(self):
        """Refresh regions from API (force refresh)"""
        self._fetch_regions_async(force_refresh=True)
    
    def _clear_cache(self):
        """Clear cache for this provider"""
        if self.fetcher:
            self.fetcher.clear_cache(self.provider_type)
        self._refresh_regions()
    
    def get_region_info(self, region_code: str) -> Optional[CloudRegion]:
        """Get detailed info for a region code"""
        for region in self.all_regions:
            if region.code == region_code:
                return region
        return None
    
    def get_filtered_count(self) -> int:
        """Get number of filtered regions currently shown"""
        return len(self.filtered_regions)
    
    def get_total_count(self) -> int:
        """Get total number of regions available"""
        return len(self.all_regions)
    
    def is_region_popular(self, region_code: str) -> bool:
        """Check if a region is marked as popular"""
        region_info = self.get_region_info(region_code)
        return region_info.popular if region_info else False