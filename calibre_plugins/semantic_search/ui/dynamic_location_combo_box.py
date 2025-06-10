"""
Dynamic Location ComboBox with Real-time Filtering

Advanced QComboBox that fetches cloud provider regions dynamically from APIs,
provides instant search filtering, and maintains excellent user experience
with loading states, error handling, and intelligent caching.
"""

import logging
from typing import List, Optional, Callable

# Use Calibre's Qt abstraction layer instead of direct PyQt5 imports
try:
    from qt.core import (
        QComboBox, QCompleter, QStringListModel, QTimer, QMovie, QLabel,
        QHBoxLayout, QWidget, QProgressBar, QToolButton, QMenu, QAction,
        Qt, QSize, QPixmap, QIcon, QPainter, QColor, QBrush, QPen, QApplication,
        QEvent, QFocusEvent
    )
except ImportError:
    # Fallback for testing outside Calibre
    from PyQt5.Qt import (
        QComboBox, QCompleter, QStringListModel, QTimer, QMovie, QLabel,
        QHBoxLayout, QWidget, QProgressBar, QToolButton, QMenu, QAction,
        Qt, QSize, QPixmap, QIcon, QPainter, QColor, QBrush, QPen, QApplication,
        QEvent, QFocusEvent
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
        print(f"[COMBO] 🚀 Initializing DynamicLocationComboBox for {provider_type}")
        
        try:
            super().__init__(parent)
            self.provider_type = provider_type
            self.all_regions: List[CloudRegion] = []
            self.is_loading = False
            print(f"[COMBO] ✅ Basic initialization complete for {provider_type}")
            
            # Initialize fetcher
            self.fetcher = LocationDataFetcher() if LocationDataFetcher else None
            print(f"[COMBO] ✅ Fetcher initialized: {self.fetcher is not None}")
            
            print(f"[COMBO] 🔧 Setting up combo box...")
            self._setup_combo_box()
            
            print(f"[COMBO] 🔧 Setting up loading indicator...")
            self._setup_loading_indicator()
            
            print(f"[COMBO] 🔧 Setting up refresh functionality...")
            self._setup_refresh_functionality()
            
            print(f"[COMBO] 🔧 Setting up filtering...")
            self._setup_filtering()
            
            print(f"[COMBO] 🔧 Starting initial data fetch...")
            # Start initial data fetch
            self._fetch_regions_async()
            
            print(f"[COMBO] ✅ DynamicLocationComboBox fully initialized for {provider_type}")
            
        except Exception as e:
            print(f"[COMBO] ❌ CRITICAL ERROR during initialization: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _setup_combo_box(self):
        """Configure the combo box for optimal filtering experience using QCompleter"""
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
        
        # SOLUTION: Use QCompleter for live filtering popup (BETTER APPROACH - doesn't steal focus!)
        print(f"[COMBO] 🔧 Setting up QCompleter...")
        self._setup_completer()
        print(f"[COMBO] ✅ Configured {self.provider_type} combo box successfully")
            
        # Enhanced interaction patterns for better UX
        self._setup_interaction_patterns()
    
    def _setup_completer(self):
        """Setup QCompleter for live filtering without focus stealing (BETTER APPROACH)"""
        print(f"[COMBO] 🔧 Setting up QCompleter for {self.provider_type}")
        
        try:
            # Create completer with custom string list model
            self.completer = QCompleter(self)
            self.completer_model = QStringListModel(self)
            self.completer.setModel(self.completer_model)
            print(f"[COMBO] ✅ QCompleter and model created")
            
            # Configure completer for optimal UX
            # Use proper enum access for Calibre's Qt
            self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            if hasattr(self.completer, 'setFilterMode'):
                self.completer.setFilterMode(Qt.MatchFlag.MatchContains)  # Match anywhere in string
            self.completer.setMaxVisibleItems(15)
            print(f"[COMBO] ✅ QCompleter configured")
            
            # CRITICAL: Set completion mode - research shows PopupCompletion exists in Qt6
            print(f"[COMBO] 🔍 Checking available completion modes...")
            completion_modes = []
            for attr in ['PopupCompletion', 'UnfilteredPopupCompletion', 'InlineCompletion']:
                if hasattr(QCompleter, attr):
                    mode_value = getattr(QCompleter, attr)
                    completion_modes.append(f"{attr}={mode_value}")
                else:
                    completion_modes.append(f"{attr}=MISSING")
            print(f"[COMBO] 🔍 Available modes: {completion_modes}")
            
            # Try PopupCompletion first (standard mode)
            if hasattr(QCompleter, 'PopupCompletion'):
                self.completer.setCompletionMode(QCompleter.PopupCompletion)
                print(f"[COMBO] ✅ Using QCompleter.PopupCompletion")
            elif hasattr(QCompleter, 'UnfilteredPopupCompletion'):
                self.completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
                print(f"[COMBO] ✅ Using QCompleter.UnfilteredPopupCompletion (fallback)")
            else:
                print(f"[COMBO] ❌ No suitable completion mode found")
                return
            
            # Connect to line edit
            if self.lineEdit():
                self.lineEdit().setCompleter(self.completer)
                print(f"[COMBO] ✅ QCompleter connected to line edit")
            
            # Handle completion selection
            self.completer.activated.connect(self._on_completion_selected)
            print(f"[COMBO] ✅ QCompleter activation signal connected")
            
            # Store mapping of display text to region code for selection
            self.completion_to_code = {}
            print(f"[COMBO] ✅ QCompleter setup complete for {self.provider_type}")
            
        except Exception as e:
            print(f"[COMBO] ❌ CRITICAL ERROR setting up QCompleter: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _on_completion_selected(self, completion_text: str):
        """Handle when user selects a completion"""
        print(f"[COMBO] 🎯 Completion selected: {completion_text}")
        region_code = self.completion_to_code.get(completion_text, completion_text)
        
        # Set the region code in the line edit
        if self.lineEdit():
            self.lineEdit().setText(region_code)
            # Trigger any change handlers
            self.editTextChanged.emit(region_code)
            print(f"[COMBO] ✅ Set region code: {region_code}")
    
    def _update_completer_data(self):
        """Update completer with current region data"""
        if not hasattr(self, 'completer') or not self.completer:
            print(f"[COMBO] ⚠️ No completer to update")
            return
        
        print(f"[COMBO] 🔄 Updating completer data with {len(self.all_regions)} regions")
        
        completion_strings = []
        self.completion_to_code.clear()
        
        # Create completion strings with visual indicators
        for region in self.all_regions:
            if region.popular:
                display_text = f"⭐ {region.code} ({region.name})"
            else:
                status_icon = "✅" if region.status == "available" else "⚠️"
                display_text = f"{status_icon} {region.code} ({region.name})"
            
            completion_strings.append(display_text)
            self.completion_to_code[display_text] = region.code
            
            # Also add just the region code for exact matches
            completion_strings.append(region.code)
            self.completion_to_code[region.code] = region.code
        
        # Update the model
        self.completer_model.setStringList(completion_strings)
        print(f"[COMBO] ✅ Completer updated with {len(completion_strings)} items")
    
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
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
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
        """Setup enhanced interaction patterns for better UX with QCompleter"""
        if self.lineEdit():
            # Store original event handlers
            original_double_click = self.lineEdit().mouseDoubleClickEvent
            original_focus_in = self.lineEdit().focusInEvent
            
            def enhanced_double_click(event):
                """Double-click to select text and show completer popup"""
                print(f"[COMBO] 🖱️ Double-click detected")
                # Call original handler to select text
                original_double_click(event)
                
                # Force completer to show all completions
                if hasattr(self, 'completer') and self.completer:
                    print(f"[COMBO] 🎯 Triggering completer popup from double-click")
                    self.completer.complete()
            
            def enhanced_focus_in(event):
                """Focus in - show completer popup for easier access"""
                print(f"[COMBO] 👁️ Focus in detected")
                # Call original handler first
                original_focus_in(event)
                
                # Show completer popup when focused (if we have data)
                if hasattr(self, 'completer') and self.completer and self.all_regions:
                    print(f"[COMBO] 🎯 Triggering completer popup from focus in")
                    self.completer.complete()
            
            # Install enhanced event handlers
            self.lineEdit().mouseDoubleClickEvent = enhanced_double_click
            self.lineEdit().focusInEvent = enhanced_focus_in
    
    
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
            
            # Update regions and completer data
            self.all_regions = regions
            self._update_completer_data()  # Use QCompleter instead of old dropdown
            
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
            self._update_completer_data()
            
        except Exception as e:
            logger.error(f"Failed to load static fallback: {e}")
    
    
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
            
            # Clear completer data
            if hasattr(self, 'completer') and self.completer:
                self.completion_to_code.clear()
                self.completer_model.setStringList([])
            
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
        """Get number of filtered regions currently shown (via QCompleter)"""
        if hasattr(self, 'completer_model') and self.completer_model:
            return self.completer_model.rowCount()
        return 0
    
    def get_total_count(self) -> int:
        """Get total number of regions available"""
        return len(self.all_regions)
    
    def is_region_popular(self, region_code: str) -> bool:
        """Check if a region is marked as popular"""
        region_info = self.get_region_info(region_code)
        return region_info.popular if region_info else False