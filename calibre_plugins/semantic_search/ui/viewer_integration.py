"""
Integration with Calibre's ebook viewer
"""

import logging

from PyQt5.Qt import QAction, QMenu, QPoint

logger = logging.getLogger(__name__)


class ViewerIntegration:
    """Handles integration with Calibre's viewer"""

    def __init__(self, plugin):
        self.plugin = plugin
        self.viewers = {}  # Track active viewers

    def inject_into_viewer(self, viewer):
        """
        Add semantic search functionality to viewer

        Args:
            viewer: Calibre viewer instance
        """
        logger.info(f"Injecting semantic search into viewer {id(viewer)}")

        # Store viewer reference
        self.viewers[id(viewer)] = viewer

        # Get the web view widget
        try:
            web_view = viewer.view

            # Connect to context menu signal
            web_view.customContextMenuRequested.connect(
                lambda point: self._show_context_menu(viewer, point)
            )

            # Add toolbar action
            self._add_toolbar_action(viewer)

            # Mark as injected
            viewer._semantic_search_injected = True

        except Exception as e:
            logger.error(f"Failed to inject into viewer: {e}")

    def _show_context_menu(self, viewer, point: QPoint):
        """
        Show context menu with semantic search options

        Args:
            viewer: Viewer instance
            point: Menu position
        """
        try:
            web_view = viewer.view

            # Get selected text via JavaScript
            web_view.page().runJavaScript(
                "window.getSelection().toString()",
                lambda text: self._handle_selection(viewer, text, point),
            )
        except Exception as e:
            logger.error(f"Context menu error: {e}")

    def _handle_selection(self, viewer, selected_text: str, point: QPoint):
        """
        Handle text selection for context menu

        Args:
            viewer: Viewer instance
            selected_text: Selected text
            point: Menu position
        """
        if not selected_text or not selected_text.strip():
            return

        # Create context menu
        menu = QMenu(viewer.view)

        # Add semantic search action
        search_action = QAction(f"Semantic Search: '{selected_text[:30]}...'", menu)
        search_action.triggered.connect(
            lambda: self._search_selected_text(viewer, selected_text)
        )
        menu.addAction(search_action)

        # Add separator
        menu.addSeparator()

        # Add search in this book action
        search_book_action = QAction("Search in This Book", menu)
        search_book_action.triggered.connect(
            lambda: self._search_in_book(viewer, selected_text)
        )
        menu.addAction(search_book_action)

        # Add find similar action
        similar_action = QAction("Find Similar Passages", menu)
        similar_action.triggered.connect(
            lambda: self._find_similar_passages(viewer, selected_text)
        )
        menu.addAction(similar_action)

        # Show menu
        menu.exec_(viewer.view.mapToGlobal(point))

    def _search_selected_text(self, viewer, text: str):
        """
        Search for selected text across library

        Args:
            viewer: Viewer instance
            text: Selected text
        """
        # Open search dialog with selected text
        if hasattr(self.plugin, "show_dialog"):
            self.plugin.show_dialog()

            # Populate search with selected text
            if hasattr(self.plugin, "search_dialog"):
                dialog = self.plugin.search_dialog
                dialog.query_input.setPlainText(text)
                dialog.perform_search()

    def _search_in_book(self, viewer, text: str):
        """
        Search within current book only

        Args:
            viewer: Viewer instance
            text: Selected text
        """
        # Get current book ID
        book_id = self._get_current_book_id(viewer)

        if book_id:
            # Open search dialog with book scope
            if hasattr(self.plugin, "show_dialog"):
                self.plugin.show_dialog()

                if hasattr(self.plugin, "search_dialog"):
                    dialog = self.plugin.search_dialog
                    dialog.query_input.setPlainText(text)
                    dialog.scope_combo.setCurrentIndex(1)  # Current Book
                    dialog.perform_search()

    def _find_similar_passages(self, viewer, text: str):
        """
        Find passages similar to selected text

        Args:
            viewer: Viewer instance
            text: Selected text
        """
        # This would find the chunk containing this text
        # and search for similar chunks
        logger.info(f"Finding similar passages to: {text[:50]}...")

        # For now, just do a regular search
        self._search_selected_text(viewer, text)

    def _add_toolbar_action(self, viewer):
        """
        Add semantic search button to viewer toolbar

        Args:
            viewer: Viewer instance
        """
        try:
            toolbar = viewer.tool_bar

            # Create action
            action = QAction("Semantic Search", viewer)
            action.setToolTip("Open semantic search dialog")
            action.triggered.connect(
                lambda: (
                    self.plugin.show_dialog()
                    if hasattr(self.plugin, "show_dialog")
                    else None
                )
            )

            # Add to toolbar
            toolbar.addSeparator()
            toolbar.addAction(action)

        except Exception as e:
            logger.error(f"Failed to add toolbar action: {e}")

    def _get_current_book_id(self, viewer):
        """
        Get the ID of the currently viewed book

        Args:
            viewer: Viewer instance

        Returns:
            Book ID or None
        """
        try:
            # Try to get book ID from viewer
            if hasattr(viewer, "current_book_id"):
                return viewer.current_book_id

            # Try to get from iterator
            if hasattr(viewer, "iterator") and hasattr(viewer.iterator, "book_id"):
                return viewer.iterator.book_id

            # Try to get from path
            if hasattr(viewer, "iterator") and hasattr(viewer.iterator, "pathtoebook"):
                path = viewer.iterator.pathtoebook
                # Would need to look up book ID from path
                # This requires database access

        except Exception as e:
            logger.error(f"Failed to get book ID: {e}")

        return None

    def remove_from_viewer(self, viewer):
        """
        Remove integration from viewer

        Args:
            viewer: Viewer instance
        """
        viewer_id = id(viewer)
        if viewer_id in self.viewers:
            del self.viewers[viewer_id]

    def navigate_to_result(self, viewer, book_id: int, position: str):
        """
        Navigate to a search result in the viewer

        Args:
            viewer: Viewer instance
            book_id: Book to open
            position: Position in book (could be character offset, paragraph, etc.)
        """
        try:
            # This would use Calibre's viewer API to navigate
            # For now, just log
            logger.info(f"Navigate to book {book_id} at position {position}")

            # Basic implementation:
            # 1. Open book if not current
            # 2. Navigate to position
            # 3. Highlight text

        except Exception as e:
            logger.error(f"Navigation error: {e}")
