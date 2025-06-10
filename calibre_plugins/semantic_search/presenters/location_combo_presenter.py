"""
LocationComboPresenter - Specialized presenter for DynamicLocationComboBox
"""

import logging
from typing import List, Optional, Callable, Any
from .location_presenter import LocationPresenter

try:
    from ..core.location_fetcher import LocationDataFetcher, CloudRegion
except ImportError:
    LocationDataFetcher = None
    CloudRegion = None

try:
    from ..core.cloud_regions import CloudRegionsData
except ImportError:
    CloudRegionsData = None


class LocationComboPresenter(LocationPresenter):
    """
    Specialized presenter for DynamicLocationComboBox that handles:
    - Region data fetching from APIs
    - Static fallback data
    - Provider switching
    - Loading states
    """
    
    def __init__(self, view: Any, provider_type: str, typing_delay_ms: int = None):
        """
        Initialize combo presenter
        
        Args:
            view: The DynamicLocationComboBox view
            provider_type: Cloud provider type (vertex_ai, azure_openai, etc.)
            typing_delay_ms: Typing delay for debouncing
        """
        super().__init__(view, typing_delay_ms)
        
        self.provider_type = provider_type
        self.all_regions: List[CloudRegion] = []
        self.is_loading = False
        self.logger = logging.getLogger(f'calibre_plugins.semantic_search.presenters.location_combo')
        
        # Initialize fetcher
        self.fetcher = LocationDataFetcher() if LocationDataFetcher else None
        
        # Start initial data fetch
        self._fetch_regions_async()
    
    def on_text_changed(self, text: str):
        """
        Handle text changes with filtering logic
        
        Args:
            text: Current text in the combo box
        """
        # Store the current text for filtering
        self.pending_text = text
        
        # If we have regions, filter them immediately for responsive UX
        if self.all_regions and text:
            filtered_regions = self._filter_regions(text)
            self._update_view_immediately(filtered_regions)
        
        # Still use debouncing for expensive operations like API calls
        super().on_text_changed(text)
    
    def _filter_regions(self, text: str) -> List[CloudRegion]:
        """
        Filter regions based on text input
        
        Args:
            text: Text to filter by
            
        Returns:
            Filtered list of regions
        """
        if not text:
            return self.all_regions
        
        text_lower = text.lower()
        filtered = []
        
        for region in self.all_regions:
            # Match on code or name
            if (text_lower in region.code.lower() or 
                text_lower in region.name.lower()):
                filtered.append(region)
        
        # Sort: exact matches first, then popular regions, then alphabetical
        def sort_key(region):
            exact_code_match = region.code.lower() == text_lower
            exact_name_match = region.name.lower() == text_lower
            starts_with_code = region.code.lower().startswith(text_lower)
            starts_with_name = region.name.lower().startswith(text_lower)
            
            # Priority: exact matches > starts with > popular > alphabetical
            return (
                not exact_code_match,
                not exact_name_match,
                not starts_with_code,
                not starts_with_name,
                not region.popular,
                region.code.lower()
            )
        
        filtered.sort(key=sort_key)
        return filtered
    
    def _update_view_immediately(self, regions: List[CloudRegion]):
        """
        Update view immediately with filtered regions (no debouncing)
        
        Args:
            regions: Regions to show in view
        """
        if self.view and hasattr(self.view, 'update_locations'):
            location_data = self._format_regions_for_view(regions)
            self.view.update_locations(location_data)
    
    def _typing_timer_expired(self):
        """
        Called when typing delay expires - trigger any expensive operations
        """
        # For now, just update with all filtered regions
        if self.pending_text is not None:
            filtered_regions = self._filter_regions(self.pending_text)
            self._update_view_immediately(filtered_regions)
    
    def _format_regions_for_view(self, regions: List[CloudRegion]) -> List[str]:
        """
        Format regions for display in view
        
        Args:
            regions: List of CloudRegion objects
            
        Returns:
            List of formatted strings for display
        """
        formatted = []
        
        for region in regions:
            if region.popular:
                display_text = f"⭐ {region.code} ({region.name})"
            else:
                status_icon = "✅" if region.status == "available" else "⚠️"
                display_text = f"{status_icon} {region.code} ({region.name})"
            
            formatted.append(display_text)
        
        return formatted
    
    def on_provider_changed(self, new_provider_type: str):
        """
        Handle provider type changes
        
        Args:
            new_provider_type: New provider type
        """
        if new_provider_type != self.provider_type:
            self.logger.info(f"Provider changed from {self.provider_type} to {new_provider_type}")
            self.provider_type = new_provider_type
            self.all_regions.clear()
            
            # Update view to clear old data
            if self.view and hasattr(self.view, 'update_locations'):
                self.view.update_locations([])
            
            # Fetch new data
            self._fetch_regions_async()
    
    def _fetch_regions_async(self, force_refresh: bool = False):
        """
        Fetch regions asynchronously
        
        Args:
            force_refresh: Whether to force refresh from API
        """
        if not self.fetcher:
            # Fallback to static data
            self._load_static_fallback()
            return
        
        if self.is_loading:
            return
        
        self.is_loading = True
        self.logger.info(f"Fetching regions for {self.provider_type}")
        
        # Notify view of loading state
        if self.view and hasattr(self.view, 'set_loading_state'):
            self.view.set_loading_state(True)
        
        def on_regions_received(regions: List[CloudRegion]):
            """Callback when regions are fetched"""
            self.is_loading = False
            self.logger.info(f"Received {len(regions)} regions for {self.provider_type}")
            
            # Update regions
            self.all_regions = regions
            
            # Update view
            if self.view and hasattr(self.view, 'set_loading_state'):
                self.view.set_loading_state(False)
            
            # Update with current filter
            if self.pending_text:
                filtered_regions = self._filter_regions(self.pending_text)
            else:
                filtered_regions = regions
            
            self._update_view_immediately(filtered_regions)
        
        # Fetch regions asynchronously
        self.fetcher.get_regions_async(
            provider=self.provider_type,
            callback=on_regions_received,
            force_refresh=force_refresh
        )
    
    def _load_static_fallback(self):
        """Load static fallback data when fetcher is not available"""
        try:
            if not CloudRegionsData:
                self.logger.warning("No fallback data available")
                return
            
            static_data = CloudRegionsData()
            regions_dict = static_data.get_regions(self.provider_type)
            
            # Convert to CloudRegion objects if possible
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
            self.logger.info(f"Loaded {len(regions)} static regions for {self.provider_type}")
            
            # Update view
            self._update_view_immediately(regions)
            
        except Exception as e:
            self.logger.error(f"Failed to load static fallback: {e}")
    
    def refresh_regions(self):
        """Refresh regions from API (force refresh)"""
        self._fetch_regions_async(force_refresh=True)
    
    def clear_cache(self):
        """Clear cache for this provider"""
        if self.fetcher:
            self.fetcher.clear_cache(self.provider_type)
        self.refresh_regions()
    
    def get_region_info(self, region_code: str) -> Optional[CloudRegion]:
        """Get detailed info for a region code"""
        for region in self.all_regions:
            if region.code == region_code:
                return region
        return None
    
    def get_total_count(self) -> int:
        """Get total number of regions available"""
        return len(self.all_regions)
    
    def is_region_popular(self, region_code: str) -> bool:
        """Check if a region is marked as popular"""
        region_info = self.get_region_info(region_code)
        return region_info.popular if region_info else False