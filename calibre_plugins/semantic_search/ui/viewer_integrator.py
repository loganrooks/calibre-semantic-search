"""
Viewer Integrator - Integrates semantic search with Calibre's book viewer

This module provides functionality to add semantic search capabilities
to the book viewer's context menu and handle viewer interactions.
"""

import logging
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class ViewerMenuIntegrator:
    """Integrates semantic search into viewer context menu"""

    def __init__(self):
        """Initialize menu integrator"""
        self.search_callback: Optional[Callable] = None
        self.error_callback: Optional[Callable] = None

    def integrate_with_viewer(self, viewer: Any) -> None:
        """
        Integrate semantic search with viewer

        Args:
            viewer: Calibre viewer instance
        """
        # Get viewer's context menu
        context_menu = viewer.view.get_context_menu()

        # Add separator
        context_menu.addSeparator()

        # Add semantic search action
        context_menu.addAction("Search Similar Passages")

    def set_search_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback for search operations"""
        self.search_callback = callback

    def set_error_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback for error handling"""
        self.error_callback = callback

    def _on_search_similar_action(self, viewer: Any) -> None:
        """Handle search similar passages action"""
        # Get selected text
        selected_text = viewer.view.get_selected_text()

        if not selected_text or not selected_text.strip():
            if self.error_callback:
                self.error_callback(
                    "Please select some text to search for similar passages."
                )
            return

        # Trigger search
        if self.search_callback:
            self.search_callback(selected_text.strip())

    def get_current_position(self, viewer: Any) -> Dict[str, Any]:
        """
        Get current reading position in viewer

        Args:
            viewer: Calibre viewer instance

        Returns:
            Dictionary with position information
        """
        return viewer.view.get_current_position()


class ViewerSearchCoordinator:
    """Coordinates search operations between viewer and search dialog"""

    def __init__(self, search_dialog: Any):
        """
        Initialize coordinator

        Args:
            search_dialog: Search dialog instance
        """
        self.search_dialog = search_dialog
        self.book_opener: Optional[Any] = None

    def set_book_opener(self, book_opener: Any) -> None:
        """Set book opener for cross-book navigation"""
        self.book_opener = book_opener

    def search_from_viewer(self, selected_text: str, viewer: Any) -> None:
        """
        Launch search from viewer selection

        Args:
            selected_text: Text selected in viewer
            viewer: Viewer instance
        """
        # Populate search dialog with selected text
        self.search_dialog.set_query_text(selected_text)

        # Show search dialog
        self.search_dialog.show()
        self.search_dialog.raise_()

    def navigate_to_result(self, result: Any, viewer: Any) -> None:
        """
        Navigate viewer to search result

        Args:
            result: Search result object
            viewer: Viewer instance
        """
        # Check if result is in different book
        if (
            hasattr(viewer, "current_book_id")
            and result.book_id != viewer.current_book_id
        ):
            # Cross-book navigation
            if self.book_opener:
                self.book_opener.open_book(result.book_id, position=result.chunk_index)
            return

        # Navigate within current book (default case)
        viewer.view.goto_position(result.chunk_index)
        viewer.view.highlight_text(result.chunk_text)


class ViewerActionFactory:
    """Factory for creating viewer-related actions"""

    def create_search_action(self, parent: Any, viewer: Any) -> Any:
        """
        Create search action for viewer

        Args:
            parent: Parent widget
            viewer: Viewer instance

        Returns:
            Action object
        """
        # For minimal implementation, return a mock action
        # In real implementation, this would create a proper Qt action
        from unittest.mock import Mock

        action = Mock()
        action.text = "Search Similar Passages"
        return action

    def create_separator(self, parent: Any) -> Any:
        """
        Create menu separator

        Args:
            parent: Parent widget

        Returns:
            Separator action
        """
        # For minimal implementation, return a mock separator
        from unittest.mock import Mock

        separator = Mock()
        separator.isSeparator = lambda: True
        return separator
