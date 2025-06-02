"""
Theme manager for dynamic styling based on Calibre's theme
"""

from PyQt5.Qt import QApplication, QPalette


class ThemeManager:
    """Manages theme-aware styling for the plugin"""
    
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
    
    @staticmethod
    def get_result_card_style() -> str:
        """Get style for result cards"""
        bg_color = ThemeManager.get_base_bg_color()
        border_color = ThemeManager.get_border_color()
        hover_bg = ThemeManager.get_alternate_bg_color()
        hover_border = ThemeManager.get_hover_border_color()
        
        return f"""
            ResultCard {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 6px;
            }}
            ResultCard:hover {{
                border-color: {hover_border};
                background-color: {hover_bg};
            }}
        """
    
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