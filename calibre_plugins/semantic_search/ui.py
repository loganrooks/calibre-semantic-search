"""
Main UI interface for Semantic Search plugin
"""

from calibre.gui2 import error_dialog, info_dialog
from calibre.gui2.actions import InterfaceAction
from PyQt5.Qt import QAction, QIcon, QMenu, Qt

from calibre_plugins.semantic_search.config import SemanticSearchConfig


class SemanticSearchInterface(InterfaceAction):
    """
    Main interface action for the plugin
    """

    name = "Semantic Search"
    action_spec = (
        "Semantic Search",
        None,
        "Search for books and passages by meaning",
        None,
    )
    popup_type = Qt.ToolButtonTextBesideIcon
    action_add_menu = True

    def genesis(self):
        """
        This method is called once per plugin, do initial setup here
        """
        # Set the icon for this interface action
        icon = get_icons("search.png")
        self.qaction.setIcon(icon)

        # The qaction is automatically created from the action_spec
        self.qaction.triggered.connect(self.show_dialog)

        # Create the menu
        self.menu = QMenu(self.gui)
        self.create_menu_actions()
        self.qaction.setMenu(self.menu)

        # Initialize configuration
        self.config = SemanticSearchConfig()

        # Track open viewers for integration
        self.viewers = {}

    def create_menu_actions(self):
        """Create the plugin menu"""
        # Search action
        self.search_action = QAction("Search Library...", self.gui)
        self.search_action.triggered.connect(self.show_dialog)
        self.menu.addAction(self.search_action)

        self.menu.addSeparator()

        # Indexing submenu
        index_menu = self.menu.addMenu("Indexing")

        # Index selected books
        self.index_selected_action = QAction("Index Selected Books", self.gui)
        self.index_selected_action.triggered.connect(self.index_selected_books)
        index_menu.addAction(self.index_selected_action)

        # Index all books
        self.index_all_action = QAction("Index All Books", self.gui)
        self.index_all_action.triggered.connect(self.index_all_books)
        index_menu.addAction(self.index_all_action)

        # Check indexing status
        self.index_status_action = QAction("Indexing Status...", self.gui)
        self.index_status_action.triggered.connect(self.show_indexing_status)
        index_menu.addAction(self.index_status_action)

        self.menu.addSeparator()

        # Settings
        self.settings_action = QAction("Settings...", self.gui)
        self.settings_action.triggered.connect(self.show_configuration)
        self.menu.addAction(self.settings_action)

        # About
        self.about_action = QAction("About...", self.gui)
        self.about_action.triggered.connect(self.show_about)
        self.menu.addAction(self.about_action)

    def show_dialog(self):
        """Show the main search dialog"""
        # Import here to avoid circular imports
        from calibre_plugins.semantic_search.ui.search_dialog import (
            SemanticSearchDialog,
        )

        # Create dialog if it doesn't exist
        if not hasattr(self, "search_dialog"):
            self.search_dialog = SemanticSearchDialog(self.gui, self)

        # Show and raise the dialog
        self.search_dialog.show()
        self.search_dialog.raise_()
        self.search_dialog.activateWindow()

    def index_selected_books(self):
        """Index the currently selected books"""
        # Get selected book IDs
        rows = self.gui.current_view().selectionModel().selectedRows()
        if not rows:
            error_dialog(
                self.gui,
                "No Selection",
                "No books selected. Please select books to index.",
                show=True,
            )
            return

        book_ids = [self.gui.current_view().model().id(row) for row in rows]

        # Start indexing job
        self._start_indexing(book_ids)

    def index_all_books(self):
        """Index all books in the library"""
        # Get all book IDs
        db = self.gui.current_db.new_api
        book_ids = list(db.all_book_ids())

        if not book_ids:
            error_dialog(
                self.gui,
                "Empty Library",
                "No books found in the current library.",
                show=True,
            )
            return

        # Confirm with user
        from PyQt5.Qt import QMessageBox

        result = QMessageBox.question(
            self.gui,
            "Index All Books",
            f"This will index {len(book_ids)} books. This may take a while.\n\n"
            "Do you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if result == QMessageBox.Yes:
            self._start_indexing(book_ids)

    def _start_indexing(self, book_ids):
        """Start the indexing process for given books"""
        # This will be implemented when we create the indexing service
        info_dialog(
            self.gui,
            "Indexing",
            f"Indexing {len(book_ids)} books...\n\n"
            "This feature will be implemented with the indexing service.",
            show=True,
        )

    def show_indexing_status(self):
        """Show the current indexing status"""
        # This will be implemented with the database layer
        info_dialog(
            self.gui,
            "Indexing Status",
            "Indexing status will be available once the database is implemented.",
            show=True,
        )

    def show_configuration(self):
        """Show the configuration dialog"""
        self.interface_action_base_plugin.do_user_config(self.gui)

    def show_about(self):
        """Show about dialog"""
        text = self.interface_action_base_plugin.about()
        from PyQt5.Qt import QMessageBox

        QMessageBox.about(self.gui, "About Semantic Search", text)

    def initialization_complete(self):
        """
        Called after all plugins have been initialized
        """
        # Set up viewer integration
        self.gui.viewer_opened.connect(self.viewer_opened)

    def viewer_opened(self, viewer):
        """
        Called when a viewer window is opened
        """
        # Store viewer reference
        self.viewers[id(viewer)] = viewer

        # Inject our context menu
        self._inject_viewer_menu(viewer)

        # Connect to viewer closed signal
        viewer.destroyed.connect(lambda: self.viewers.pop(id(viewer), None))

    def _inject_viewer_menu(self, viewer):
        """Add semantic search to viewer context menu"""
        # This will be implemented in the viewer integration module
        pass

    def library_changed(self, db):
        """
        Called when the library is changed
        """
        # Clear any cached data
        if hasattr(self, "search_dialog"):
            self.search_dialog.library_changed()

    def shutting_down(self):
        """
        Called when Calibre is shutting down
        """
        # Clean up resources
        if hasattr(self, "search_dialog"):
            self.search_dialog.close()


def get_icons(name):
    """
    Get icon from resources
    """
    import os
    from PyQt5.Qt import QPixmap
    
    # Get the directory where this module is located
    plugin_dir = os.path.dirname(__file__)
    icon_path = os.path.join(plugin_dir, 'resources', 'icons', name)
    
    # Try to load the icon
    if os.path.exists(icon_path):
        pixmap = QPixmap(icon_path)
        if not pixmap.isNull():
            return QIcon(pixmap)
    
    # Fallback to default Calibre icon or empty icon
    return QIcon()
