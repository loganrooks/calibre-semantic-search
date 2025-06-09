"""
Location ComboBox Widget

Intelligent, searchable dropdown for cloud provider locations with
filtering capabilities and custom entry support.
"""

from typing import Optional
from PyQt5.Qt import QComboBox, QCompleter, Qt

from calibre_plugins.semantic_search.core.cloud_regions import CloudRegionsData


class LocationComboBox(QComboBox):
    """Searchable combo box for cloud provider locations"""
    
    def __init__(self, provider_type: str, parent=None):
        super().__init__(parent)
        self.provider_type = provider_type
        self.regions_data = CloudRegionsData()
        self._original_regions = []
        
        self._setup_combo_box()
        self._populate_regions()
        self._setup_filtering()
    
    def _setup_combo_box(self):
        """Configure the combo box for optimal user experience"""
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.NoInsert)  # Don't insert typed text as new item
        self.setDuplicatesEnabled(False)
        
        # Allow user to type and filter
        self.setEditText("")
        
        # Configure completer for better search experience
        completer = self.completer()
        if completer:
            completer.setCompletionMode(QCompleter.PopupCompletion)
            completer.setCaseSensitivity(Qt.CaseInsensitive)
    
    def _populate_regions(self):
        """Populate the combo box with regions for the provider"""
        if not self.provider_type:
            return
        
        regions = self.regions_data.get_regions(self.provider_type)
        self._original_regions = regions.copy()
        
        # Clear existing items
        self.clear()
        
        # Sort regions: popular first, then alphabetically
        popular_regions = [r for r in regions if r.get("popular", False)]
        other_regions = [r for r in regions if not r.get("popular", False)]
        
        # Sort each group alphabetically
        popular_regions.sort(key=lambda x: x["code"])
        other_regions.sort(key=lambda x: x["code"])
        
        # Add popular regions first
        for region in popular_regions:
            display_text = f"{region['code']} ({region['name']})"
            self.addItem(display_text, region['code'])
        
        # Add separator if we have both popular and other regions
        if popular_regions and other_regions:
            self.insertSeparator(len(popular_regions))
        
        # Add other regions
        for region in other_regions:
            display_text = f"{region['code']} ({region['name']})"
            self.addItem(display_text, region['code'])
        
        # Set placeholder text
        if self.lineEdit():
            placeholder_examples = {
                "vertex_ai": "e.g., us-central1, europe-west1",
                "direct_vertex_ai": "e.g., us-central1, europe-west1", 
                "azure_openai": "e.g., eastus, westeurope"
            }
            placeholder = placeholder_examples.get(self.provider_type, "Select or type region...")
            self.lineEdit().setPlaceholderText(placeholder)
    
    def _setup_filtering(self):
        """Setup real-time filtering as user types"""
        if self.lineEdit():
            self.lineEdit().textEdited.connect(self._filter_items)
            # Also connect to text changes from selection
            self.editTextChanged.connect(self._on_text_changed)
    
    def _filter_items(self, text: str):
        """Filter items based on user input"""
        if not text:
            # If no text, show all regions
            self._populate_regions()
            return
        
        # Get matching regions
        matching_regions = self.regions_data.search_regions(self.provider_type, text)
        
        # Update combo box with filtered results
        self.clear()
        
        if matching_regions:
            # Sort: popular first, then alphabetical
            popular_matches = [r for r in matching_regions if r.get("popular", False)]
            other_matches = [r for r in matching_regions if not r.get("popular", False)]
            
            popular_matches.sort(key=lambda x: x["code"])
            other_matches.sort(key=lambda x: x["code"])
            
            # Add popular matches first
            for region in popular_matches:
                display_text = f"{region['code']} ({region['name']})"
                self.addItem(display_text, region['code'])
            
            # Add separator if needed
            if popular_matches and other_matches:
                self.insertSeparator(len(popular_matches))
            
            # Add other matches
            for region in other_matches:
                display_text = f"{region['code']} ({region['name']})"
                self.addItem(display_text, region['code'])
        
        # Show the popup to display filtered results
        if matching_regions and not self.view().isVisible():
            self.showPopup()
    
    def _on_text_changed(self, text: str):
        """Handle text changes from both typing and selection"""
        # If user selected an item, don't filter
        if self.currentIndex() >= 0:
            return
        
        # If user is typing, trigger filtering
        self._filter_items(text)
    
    def get_region_code(self) -> str:
        """Get the actual region code from current selection or input"""
        # If an item is selected, return its data (the region code)
        current_data = self.currentData()
        if current_data:
            return current_data
        
        # If no item selected, return the current text (custom entry)
        return self.currentText().strip()
    
    def set_region_code(self, region_code: str):
        """Set the combo box to a specific region code"""
        if not region_code:
            self.setEditText("")
            return
        
        # Try to find the region in our items
        for i in range(self.count()):
            if self.itemData(i) == region_code:
                self.setCurrentIndex(i)
                return
        
        # If not found, set as custom text
        self.setEditText(region_code)
    
    def update_provider(self, new_provider_type: str):
        """Update the provider type and repopulate regions"""
        if new_provider_type != self.provider_type:
            self.provider_type = new_provider_type
            self._populate_regions()
    
    def get_display_text_for_code(self, region_code: str) -> str:
        """Get display text for a given region code"""
        return self.regions_data.get_region_display_name(self.provider_type, region_code)
    
    def validate_current_region(self) -> bool:
        """Validate if the current region is known for this provider"""
        region_code = self.get_region_code()
        if not region_code:
            return False
        
        return self.regions_data.validate_region(self.provider_type, region_code)
    
    def get_popular_regions(self) -> list:
        """Get list of popular regions for current provider"""
        return self.regions_data.get_popular_regions(self.provider_type)
    
    def reset_to_default(self):
        """Reset to show all regions without filter"""
        self.setEditText("")
        self._populate_regions()