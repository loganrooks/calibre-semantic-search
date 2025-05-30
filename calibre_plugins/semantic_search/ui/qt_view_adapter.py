"""
Qt View Adapter - Adapts Qt dialog to presenter interface

This adapter allows the presenter to work with Qt widgets without
directly depending on Qt, maintaining testability.
"""


class QtViewAdapter:
    """Adapter that connects Qt dialog to presenter interface"""
    
    def __init__(self, qt_dialog):
        """
        Initialize adapter with Qt dialog
        
        Args:
            qt_dialog: The Qt dialog instance to adapt
        """
        self.dialog = qt_dialog
    
    def show_validation_error(self, error_message: str) -> None:
        """
        Show validation error to user
        
        Args:
            error_message: The error message to display
        """
        # Minimal implementation to pass test
        self.dialog.show_warning("Invalid Query", error_message)
    
    def display_results(self, results) -> None:
        """
        Display search results
        
        Args:
            results: List of search results
        """
        # Clear previous results
        self.dialog.results_list.clear()
        self.dialog.current_results = results
        
        # Delegate to dialog's display method
        self.dialog._display_results(results)
    
    def show_search_progress(self) -> None:
        """Show search is in progress"""
        # Show progress bar
        self.dialog.progress_bar.show()
        self.dialog.progress_bar.setRange(0, 0)  # Indeterminate
        self.dialog.status_bar.setText("Searching...")
        self.dialog.search_button.setEnabled(False)
    
    def show_search_error(self, error_message: str) -> None:
        """
        Show search error to user
        
        Args:
            error_message: The error message to display
        """
        # Hide progress and re-enable search
        self.dialog.progress_bar.hide()
        self.dialog.search_button.setEnabled(True)
        self.dialog.status_bar.setText(f"Search error: {error_message}")
        
        # Show error dialog
        self.dialog._search_error(error_message)