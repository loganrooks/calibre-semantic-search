"""
Theme manager for dynamic styling based on Calibre's theme
"""

from PyQt5.Qt import QApplication, QPalette


class ThemeManager:
    """Manages theme-aware styling for the plugin"""
    
    def __init__(self):
        """Initialize theme manager"""
        self._cache = {}  # Cache for generated styles
    
    @staticmethod
    def get_palette() -> QPalette:
        """Get the current application palette"""
        return QApplication.palette()
    
    @staticmethod
    def is_dark_theme() -> bool:
        """Check if current theme is dark"""
        palette = QApplication.palette()
        bg_color = palette.color(QPalette.Window)
        # Simple check: if background luminance is low, it's dark
        luminance = (0.299 * bg_color.red() + 
                    0.587 * bg_color.green() + 
                    0.114 * bg_color.blue())
        return luminance < 128
    
    @staticmethod
    def get_muted_text_color() -> str:
        """Get color for muted/secondary text"""
        palette = QApplication.palette()
        if ThemeManager.is_dark_theme():
            # For dark themes, use a lighter gray
            return palette.color(QPalette.Disabled, QPalette.Text).name()
        else:
            # For light themes, use darker gray
            return palette.color(QPalette.Mid).name()
    
    @staticmethod
    def get_highlight_bg_color() -> str:
        """Get background color for highlighted items"""
        palette = QApplication.palette()
        return palette.color(QPalette.Highlight).name()
    
    @staticmethod
    def get_highlight_text_color() -> str:
        """Get text color for highlighted items"""
        palette = QApplication.palette()
        return palette.color(QPalette.HighlightedText).name()
    
    @staticmethod
    def get_alternate_bg_color() -> str:
        """Get alternate background color"""
        palette = QApplication.palette()
        return palette.color(QPalette.AlternateBase).name()
    
    @staticmethod
    def get_base_bg_color() -> str:
        """Get base background color for content areas"""
        palette = QApplication.palette()
        return palette.color(QPalette.Base).name()
    
    @staticmethod
    def get_window_bg_color() -> str:
        """Get window background color"""
        palette = QApplication.palette()
        return palette.color(QPalette.Window).name()
    
    @staticmethod
    def get_text_color() -> str:
        """Get standard text color"""
        palette = QApplication.palette()
        return palette.color(QPalette.Text).name()
    
    @staticmethod
    def get_border_color() -> str:
        """Get border color"""
        palette = QApplication.palette()
        return palette.color(QPalette.Mid).name()
    
    @staticmethod
    def get_hover_border_color() -> str:
        """Get border color for hover state"""
        palette = QApplication.palette()
        return palette.color(QPalette.Highlight).name()
    
    # Specific widget styles
    
    @staticmethod
    def get_status_bar_style() -> str:
        """Get style for status bar labels"""
        return f"QLabel {{ color: {ThemeManager.get_muted_text_color()}; }}"
    
    @staticmethod
    def get_char_counter_style(is_over_limit: bool = False) -> str:
        """Get style for character counter"""
        if is_over_limit:
            # Use error color (usually red)
            palette = QApplication.palette()
            color = "#dc3545"  # Bootstrap danger color as fallback
            # Try to get from palette if available
            if hasattr(QPalette, 'PlaceholderText'):
                color = palette.color(QPalette.PlaceholderText).name()
        else:
            color = ThemeManager.get_muted_text_color()
        return f"QLabel {{ color: {color}; }}"
    
    @staticmethod
    def get_description_label_style() -> str:
        """Get style for description labels"""
        return f"QLabel {{ color: {ThemeManager.get_muted_text_color()}; font-size: 10pt; }}"
    
    def get_result_card_style(self) -> str:
        """Get style for result cards"""
        bg_color = self.get_base_bg_color()
        text_color = self.get_text_color()
        border_color = self.get_border_color()
        hover_bg = self.get_alternate_bg_color()
        hover_border = self.get_hover_border_color()
        
        style = f"""
            background-color: {bg_color};
            color: {text_color};
            border: 1px solid {border_color};
            border-radius: 6px;
            padding: 12px;
        """
        
        # Add hover state
        style += f"""
ResultCard:hover {{
    border-color: {hover_border};
    background-color: {hover_bg};
}}
        """
        
        return style.strip()
    
    @staticmethod
    def get_content_preview_style() -> str:
        """Get style for content preview in result cards"""
        bg_color = ThemeManager.get_alternate_bg_color()
        border_color = ThemeManager.get_border_color()
        
        return f"""
            QLabel {{ 
                background-color: {bg_color}; 
                padding: 8px; 
                border-radius: 4px;
                border: 1px solid {border_color};
            }}
        """
    
    @staticmethod
    def get_score_color(score: float) -> str:
        """Get color based on similarity score"""
        # These colors work well on both light and dark themes
        if score >= 0.8:
            return "#28a745"  # Green
        elif score >= 0.6:
            return "#ffc107"  # Yellow/Amber
        elif score >= 0.4:
            return "#fd7e14"  # Orange
        else:
            return "#dc3545"  # Red
    
    @staticmethod
    def get_score_label_style(score: float) -> str:
        """Get style for score label"""
        bg_color = ThemeManager.get_score_color(score)
        # White text works well on all these background colors
        return f"""
            QLabel {{ 
                background-color: {bg_color}; 
                color: white; 
                padding: 4px 8px; 
                border-radius: 4px;
                font-size: 12pt;
            }}
        """
    
    def get_style(self, widget_type: str) -> str:
        """Get style for specific widget type"""
        if widget_type in self._cache:
            return self._cache[widget_type]
            
        style = ""
        if widget_type == 'result_card':
            style = self.get_result_card_style()
        elif widget_type == 'search_input':
            style = self._get_search_input_style()
        elif widget_type == 'button':
            style = self._get_button_style()
        elif widget_type == 'list_item':
            style = self._get_list_item_style()
        elif widget_type == 'scroll_area':
            style = self._get_scroll_area_style()
        else:
            style = ""
            
        self._cache[widget_type] = style
        return style
    
    def _get_search_input_style(self) -> str:
        """Get style for search input"""
        bg_color = self.get_base_bg_color()
        text_color = self.get_text_color()
        border_color = self.get_border_color()
        
        return f"""
            QTextEdit {{
                background-color: {bg_color};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 4px;
                padding: 8px;
            }}
        """
    
    def _get_button_style(self) -> str:
        """Get style for buttons"""
        bg_color = self.get_window_bg_color()
        text_color = self.get_text_color()
        border_color = self.get_border_color()
        hover_bg = self.get_highlight_bg_color()
        hover_text = self.get_highlight_text_color()
        
        return f"""
            QPushButton {{
                background-color: {bg_color};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 4px;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                background-color: {hover_bg};
                color: {hover_text};
            }}
            QPushButton:pressed {{
                background-color: {border_color};
            }}
        """
    
    def _get_list_item_style(self) -> str:
        """Get style for list items"""
        bg_color = self.get_base_bg_color()
        text_color = self.get_text_color()
        selected_bg = self.get_highlight_bg_color()
        selected_text = self.get_highlight_text_color()
        
        return f"""
            QListWidget {{
                background-color: {bg_color};
                color: {text_color};
                border: 1px solid {self.get_border_color()};
            }}
            QListWidget::item:selected {{
                background-color: {selected_bg};
                color: {selected_text};
            }}
        """
    
    def _get_scroll_area_style(self) -> str:
        """Get style for scroll areas"""
        bg_color = self.get_base_bg_color()
        
        return f"""
            QScrollArea {{
                background-color: {bg_color};
                border: none;
            }}
        """
    
    def generate_complete_stylesheet(self) -> str:
        """Generate complete stylesheet for all UI components"""
        components = []
        
        # Result cards
        components.append(f".ResultCard {{{self.get_result_card_style()}}}")
        
        # Search input
        components.append(f".SearchInput {{{self._get_search_input_style()}}}")
        
        # Buttons
        components.append(self._get_button_style())
        
        # Lists
        components.append(self._get_list_item_style())
        
        # Scroll areas
        components.append(self._get_scroll_area_style())
        
        # Status labels
        components.append(f"QLabel.status {{{self.get_status_bar_style()}}}")
        
        # Ensure no problematic hard-coded colors
        stylesheet = "\n".join(components)
        
        # Remove any hard-coded problematic colors
        problematic_colors = ['#f0f0f0', 'lightgray', 'lightgrey', '#d3d3d3']
        for color in problematic_colors:
            stylesheet = stylesheet.replace(color, self.get_alternate_bg_color())
            
        return stylesheet
    
    def detect_theme_type(self) -> str:
        """Detect current theme type"""
        if self.is_dark_theme():
            return 'dark'
        else:
            return 'light'
    
    def refresh_theme(self):
        """Refresh theme cache"""
        self._cache.clear()