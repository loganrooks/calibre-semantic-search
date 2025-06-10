"""
Simple Location ComboBox Widget

A straightforward implementation that avoids floating dropdown issues
by using standard QComboBox behavior without automatic popup triggering.
"""

try:
    from qt.core import QComboBox, QCompleter, Qt
except ImportError:
    from PyQt5.Qt import QComboBox, QCompleter, Qt

try:
    from ..core.cloud_regions import CloudRegionsData
except ImportError:
    from calibre_plugins.semantic_search.core.cloud_regions import CloudRegionsData


class SimpleLocationCombo(QComboBox):
    """Simple location dropdown that works reliably in Calibre"""
    
    def __init__(self, provider_type: str, parent=None):
        super().__init__(parent)
        self.provider_type = provider_type
        self.regions_data = CloudRegionsData()
        
        # Make it editable so users can type custom regions
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.NoInsert)
        
        # Set up completer for autocomplete
        completer = self.completer()
        if completer:
            # Use proper enum access for Calibre's Qt
            completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            # Note: setFilterMode might not exist in older Qt versions
            if hasattr(completer, 'setFilterMode'):
                completer.setFilterMode(Qt.MatchFlag.MatchContains)
        
        # Populate with regions
        self._populate_regions()
    
    def _populate_regions(self):
        """Populate the combo box with regions"""
        regions = self.regions_data.get_regions(self.provider_type)
        
        # Clear and add regions
        self.clear()
        
        # Sort regions: popular first, then alphabetically
        popular = [r for r in regions if r.get("popular", False)]
        others = [r for r in regions if not r.get("popular", False)]
        
        # Add popular regions
        for region in sorted(popular, key=lambda x: x["code"]):
            display = f"{region['code']} ({region['name']})"
            self.addItem(display, region['code'])
        
        # Add separator if we have both
        if popular and others:
            self.insertSeparator(self.count())
        
        # Add other regions
        for region in sorted(others, key=lambda x: x["code"]):
            display = f"{region['code']} ({region['name']})"
            self.addItem(display, region['code'])
    
    def get_region_code(self) -> str:
        """Get the region code from current text"""
        text = self.currentText().strip()
        
        # If it's in format "code (name)", extract code
        if ' (' in text and text.endswith(')'):
            return text.split(' (')[0]
        
        # Otherwise return as-is
        return text
    
    def set_region_code(self, code: str):
        """Set the region code"""
        if not code:
            self.setEditText("")
            return
        
        # Try to find and select the item
        for i in range(self.count()):
            if self.itemData(i) == code:
                self.setCurrentIndex(i)
                return
        
        # If not found, just set the text
        self.setEditText(code)