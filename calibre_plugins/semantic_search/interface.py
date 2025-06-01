"""
Main UI interface for Semantic Search plugin
"""

import logging

from calibre.gui2 import error_dialog, info_dialog
from calibre.gui2.actions import InterfaceAction

logger = logging.getLogger(__name__)

# Import from qt.core instead of PyQt5 for Calibre compatibility
try:
    from qt.core import QAction, QIcon, QMenu, QToolButton
except ImportError:
    # Fallback for older Calibre versions
    from PyQt5.Qt import QAction, QIcon, QMenu, Qt as QtCompat
    QToolButton = QtCompat.QToolButton

from calibre_plugins.semantic_search.config import SemanticSearchConfig


class SemanticSearchInterface(InterfaceAction):
    """
    Main interface action for the plugin
    """

    name = "Semantic Search"
    action_spec = (
        "Semantic Search",
        "search.png",  # Use Calibre's built-in search icon
        "Search for books and passages by meaning",
        None,
    )
    popup_type = QToolButton.ToolButtonPopupMode.MenuButtonPopup
    action_add_menu = True
    allowed_in_toolbar = True
    allowed_in_menu = True

    def genesis(self):
        """
        This method is called once per plugin, do initial setup here
        """
        # Set the icon for this interface action
        # The icon should be loaded from action_spec automatically
        # but we can also try to load a custom icon
        try:
            # Try to use Calibre's built-in search icon
            icon = QIcon.ic('search.png')
            if icon and not icon.isNull():
                self.qaction.setIcon(icon)
        except:
            # Icon will use default from action_spec
            pass

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
        
        # Initialize services on startup
        self._initialize_services()

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
        try:
            # Try to initialize if not already done
            if not hasattr(self, 'indexing_service') or not self.indexing_service:
                self._initialize_services()
            
            # Check if indexing service is available
            if hasattr(self, 'indexing_service') and self.indexing_service:
                # Get real status from indexing service (handle async)
                import asyncio
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    status = loop.run_until_complete(self.indexing_service.get_library_statistics())
                finally:
                    loop.close()
                
                # Format status message
                message = f"""Indexing Status:

Total Books: {status['total_books']}
Indexed Books: {status['indexed_books']}
In Progress: {status['in_progress']}
Errors: {status['errors']}
Last Indexed: {status['last_indexed']}"""
                
            else:
                # Indexing service not initialized
                if hasattr(self, 'initialization_error'):
                    message = f"Indexing service initialization failed:\n\n{self.initialization_error}\n\nPlease check your configuration."
                else:
                    message = "Indexing service is not initialized. Please configure the plugin first."
                
        except Exception as e:
            # Handle errors gracefully
            message = f"Error retrieving indexing status: {str(e)}"
        
        info_dialog(
            self.gui,
            "Indexing Status",
            message,
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
        # Set up viewer integration if signal exists
        if hasattr(self.gui, 'viewer_opened'):
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

    def _initialize_services(self):
        """Initialize services on plugin startup"""
        try:
            import os
            from calibre_plugins.semantic_search.core.embedding_service import create_embedding_service
            from calibre_plugins.semantic_search.core.indexing_service import IndexingService
            from calibre_plugins.semantic_search.core.text_processor import TextProcessor
            from calibre_plugins.semantic_search.data.repositories import (
                EmbeddingRepository, CalibreRepository
            )
            from calibre_plugins.semantic_search.data.database import SemanticSearchDB
            
            # Set up database path
            library_path = self.gui.library_path
            db_dir = os.path.join(library_path, 'semantic_search')
            os.makedirs(db_dir, exist_ok=True)
            self.db_path = os.path.join(db_dir, 'embeddings.db')
            
            # Initialize database if needed
            if not os.path.exists(self.db_path):
                # Database will be initialized on first use
                pass
            
            # Create repositories
            self.embedding_repo = EmbeddingRepository(self.db_path)
            
            # Check if current_db is available
            if hasattr(self.gui, 'current_db') and self.gui.current_db:
                if hasattr(self.gui.current_db, 'new_api'):
                    self.calibre_repo = CalibreRepository(self.gui.current_db.new_api)
                else:
                    # Old Calibre version or DB not ready
                    logger.warning("current_db doesn't have new_api, skipping CalibreRepository")
                    self.calibre_repo = None
            else:
                logger.warning("current_db not available yet, skipping CalibreRepository") 
                self.calibre_repo = None
            
            # Create services
            config_dict = self.config.as_dict()
            self.embedding_service = create_embedding_service(config_dict)
            self.text_processor = TextProcessor()
            
            # Create indexing service only if we have calibre_repo
            if self.calibre_repo:
                self.indexing_service = IndexingService(
                    text_processor=self.text_processor,
                    embedding_service=self.embedding_service,
                    embedding_repo=self.embedding_repo,
                    calibre_repo=self.calibre_repo
                )
            else:
                logger.warning("Cannot create IndexingService without CalibreRepository")
                self.indexing_service = None
            
            logger.info("Successfully initialized semantic search services")
            
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Store the error for display
            self.initialization_error = str(e)
            # Services will be created on-demand if initialization fails
    
    def get_embedding_service(self):
        """Get the embedding service, creating if needed"""
        if not hasattr(self, 'embedding_service') or not self.embedding_service:
            self._initialize_services()
        return self.embedding_service if hasattr(self, 'embedding_service') else None
    
    def get_indexing_service(self):
        """Get the indexing service, creating if needed"""
        if not hasattr(self, 'indexing_service') or not self.indexing_service:
            self._initialize_services()
        return self.indexing_service if hasattr(self, 'indexing_service') else None

    def library_changed(self, db):
        """
        Called when the library is changed
        """
        # Clear any cached data
        if hasattr(self, "search_dialog"):
            self.search_dialog.library_changed()
        
        # Re-initialize services for new library
        self._initialize_services()

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
