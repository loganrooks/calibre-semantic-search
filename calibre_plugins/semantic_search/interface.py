"""
Main UI interface for Semantic Search plugin
"""

import logging

from calibre.gui2 import error_dialog, info_dialog
from calibre.gui2.actions import InterfaceAction

# Import job management classes
try:
    from .background_jobs import BackgroundJobManager
except ImportError:
    # May not be available during testing
    BackgroundJobManager = None

# Import from qt.core instead of PyQt5 for Calibre compatibility
try:
    from qt.core import QAction, QIcon, QMenu, QToolButton, QCursor
except ImportError:
    # Fallback for older Calibre versions
    from PyQt5.Qt import QAction, QIcon, QMenu, QCursor, Qt as QtCompat
    QToolButton = QtCompat.QToolButton

from calibre_plugins.semantic_search.config import SemanticSearchConfig
from calibre_plugins.semantic_search.core.logging_config import setup_logging

# Qt imports for threading support
from PyQt5.Qt import QTimer


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
    # Don't exclude from any context menus - we want to appear in library view context menu
    dont_add_to = frozenset()  # Empty set means add to all context menus
    action_type = 'current'  # Work with currently selected books

    def genesis(self):
        """
        This method is called once per plugin, do initial setup here
        """
        # Initialize logging system first
        setup_logging(self.name)
        
        # Get logger for this module
        self.logger = logging.getLogger(f'calibre_plugins.semantic_search.interface')
        self.logger.info("SemanticSearchInterface genesis() starting")
        
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
        self.qaction.triggered.connect(self.toolbar_action_triggered)

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

    def toolbar_action_triggered(self):
        """
        Handle main action trigger - context aware.
        Shows different behavior based on whether books are selected.
        """
        # Guard against calls before GUI is ready
        if not self.gui or not hasattr(self.gui, 'current_view') or not self.gui.current_view():
            self.show_dialog()
            return
            
        current_view = self.gui.current_view()
        if not current_view or not current_view.selectionModel():
            self.show_dialog()
            return
        
        # Check if books are selected (context menu scenario)
        rows = current_view.selectionModel().selectedRows()
        if rows:
            # Books are selected - show context menu with options
            menu = QMenu(self.gui)
            
            # Add context-specific actions
            if len(rows) == 1:
                # Single book selected - show all options
                search_similar = menu.addAction("Find Similar Books")
                search_similar.triggered.connect(self._find_similar_from_context)
                menu.addSeparator()
            
            # Multiple or single book selected
            index_action = menu.addAction(f"Index {len(rows)} Selected Book{'s' if len(rows) > 1 else ''}")
            index_action.triggered.connect(self.index_selected_books)
            
            menu.addSeparator()
            search_action = menu.addAction("Open Semantic Search...")
            search_action.triggered.connect(self.show_dialog)
            
            # Show menu at cursor position
            menu.exec(QCursor.pos())
        else:
            # No selection - show search dialog (toolbar click)
            self.show_dialog()

    def create_menu_actions(self):
        """Create the plugin menu"""
        # Search action
        self.search_action = QAction("Search Library...", self.gui)
        self.search_action.triggered.connect(self.show_dialog)
        self.menu.addAction(self.search_action)
        
        # Find Similar Books (context menu action)
        self.similar_action = QAction("Find Similar Books", self.gui)
        self.similar_action.setToolTip("Search for books with similar content to the selected book")
        self.similar_action.triggered.connect(self._find_similar_from_context)
        self.menu.addAction(self.similar_action)

        self.menu.addSeparator()

        # Indexing submenu
        index_menu = self.menu.addMenu("Indexing")

        # Index selected books (also context menu action)
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
        
        # Index manager
        index_menu.addSeparator()
        self.index_manager_action = QAction("Manage Index...", self.gui)
        self.index_manager_action.setToolTip("View and manage the search index")
        self.index_manager_action.triggered.connect(self.show_index_manager)
        index_menu.addAction(self.index_manager_action)

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
        """Start the indexing process using Calibre's ThreadedJob system"""
        # Ensure services are initialized
        if not hasattr(self, 'indexing_service') or not self.indexing_service:
            self._initialize_services()
        
        if not self.indexing_service:
            error_dialog(
                self.gui,
                "Indexing Error",
                "Indexing service could not be initialized.\n\n"
                "Please check your configuration and try again.",
                show=True,
            )
            return
        
        # Use BackgroundJobManager for job management
        if not hasattr(self, 'job_manager'):
            if BackgroundJobManager is None:
                error_dialog(
                    self.gui,
                    "Job Manager Error",
                    "Job management not available.",
                    show=True,
                )
                return
            self.job_manager = BackgroundJobManager()
        
        # Start indexing job with services passed to job manager
        self.current_indexing_job_id = self.job_manager.start_indexing_job(
            book_ids, 
            self._indexing_job_complete,
            indexing_service=self.indexing_service,
            gui=self.gui
        )
        
        # Show status message
        if hasattr(self.gui, 'status_bar') and self.gui.status_bar:
            self.gui.status_bar.show_message(
                f'Starting indexing of {len(book_ids)} books...', 3000
            )


    def _indexing_job_complete(self, result):
        """Handle indexing job completion from BackgroundJobManager"""
        
        if "error" in result:
            error_dialog(
                self.gui,
                "Indexing Error", 
                f"Indexing failed:\n\n{result['error']}",
                show=True
            )
        else:
            # Handle successful completion with detailed stats
            success_count = result.get('successful_books', 0)
            failed_count = result.get('failed_books', 0)
            total_chunks = result.get('total_chunks', 0)
            total_time = result.get('total_time', 0)
            
            message = (
                f"Indexing completed!\n\n"
                f"Successfully indexed: {success_count} books\n"
                f"Failed: {failed_count} books\n"
                f"Total text chunks created: {total_chunks}\n"
                f"Time taken: {total_time:.1f} seconds"
            )
            
            if failed_count > 0:
                errors = result.get('errors', [])
                error_details = "\n".join([f"Book {e['book_id']}: {e['error']}" for e in errors[:3]])
                if len(errors) > 3:
                    error_details += f"\n... and {len(errors) - 3} more errors"
                message += f"\n\nErrors:\n{error_details}"
            
            if failed_count > 0:
                error_dialog(self.gui, "Indexing Results", message, show=True)
            else:
                info_dialog(self.gui, "Indexing Complete", message, show=True)
        
        # Clear job reference
        if hasattr(self, 'current_indexing_job_id'):
            del self.current_indexing_job_id

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
                
                # Format status message with safe access
                message = f"""Indexing Status:

Total Books: {status.get('total_books', 0)}
Indexed Books: {status.get('indexed_books', 0)}
In Progress: {status.get('in_progress', 0)}
Errors: {status.get('errors', 0)}
Last Indexed: {status.get('last_indexed', 'Never')}"""
                
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

    def show_index_manager(self):
        """Show the index management dialog"""
        from calibre_plugins.semantic_search.ui.index_manager_dialog import IndexManagerDialog
        
        dialog = IndexManagerDialog(self, self.gui)
        dialog.exec_()
    
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
        self.logger.info("=== _initialize_services() called ===")
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
            self.logger.info(f"Library path: {library_path}")
            db_dir = os.path.join(library_path, 'semantic_search')
            os.makedirs(db_dir, exist_ok=True)
            self.db_path = os.path.join(db_dir, 'embeddings.db')
            self.logger.info(f"Database path will be: {self.db_path}")
            self.logger.info(f"Database file exists: {os.path.exists(self.db_path)}")
            
            # Initialize database and repositories
            self.logger.info(f"Initializing database at: {self.db_path}")
            try:
                self.logger.info("Creating EmbeddingRepository...")
                self.embedding_repo = EmbeddingRepository(self.db_path)
                self.logger.info("EmbeddingRepository created successfully")
            except Exception as e:
                self.logger.error(f"Failed to create EmbeddingRepository: {e}")
                import traceback
                self.logger.error(traceback.format_exc())
                self.embedding_repo = None
            
            # Try multiple ways to get Calibre database
            self.logger.info("Checking CalibreRepository availability...")
            self.calibre_repo = None
            
            # Method 1: current_db.new_api (preferred)
            if hasattr(self.gui, 'current_db') and self.gui.current_db:
                self.logger.info("current_db is available")
                if hasattr(self.gui.current_db, 'new_api'):
                    try:
                        self.logger.info("current_db has new_api, creating CalibreRepository")
                        self.calibre_repo = CalibreRepository(self.gui.current_db.new_api)
                        self.logger.info("CalibreRepository created successfully")
                    except Exception as e:
                        self.logger.warning(f"Failed to create CalibreRepository with current_db.new_api: {e}")
                        import traceback
                        self.logger.warning(traceback.format_exc())
                else:
                    self.logger.warning("current_db doesn't have new_api")
            
            # Method 2: library_view.model().db (fallback)
            if not self.calibre_repo and hasattr(self.gui, 'library_view'):
                try:
                    self.logger.info("Trying library_view.model().db")
                    model = self.gui.library_view.model()
                    if model and hasattr(model, 'db'):
                        if hasattr(model.db, 'new_api'):
                            try:
                                self.logger.info("Creating CalibreRepository with library_view.model().db.new_api")
                                self.calibre_repo = CalibreRepository(model.db.new_api)
                                self.logger.info("CalibreRepository created successfully via library_view")
                            except Exception as e:
                                self.logger.warning(f"Failed to create CalibreRepository with library_view.model().db.new_api: {e}")
                        else:
                            self.logger.warning("library_view.model().db doesn't have new_api")
                except Exception as e:
                    self.logger.warning(f"Failed to get db from library_view: {e}")
            
            # Method 3: Direct db access (last resort)
            if not self.calibre_repo and hasattr(self.gui, 'db'):
                try:
                    self.logger.info("Trying gui.db")
                    if hasattr(self.gui.db, 'new_api'):
                        self.logger.info("Creating CalibreRepository with gui.db.new_api")
                        self.calibre_repo = CalibreRepository(self.gui.db.new_api)
                        self.logger.info("CalibreRepository created successfully via gui.db")
                    else:
                        self.logger.warning("gui.db doesn't have new_api")
                except Exception as e:
                    self.logger.warning(f"Failed to create CalibreRepository with gui.db.new_api: {e}")
                    import traceback
                    self.logger.warning(traceback.format_exc())
                    
            if not self.calibre_repo:
                self.logger.warning("Could not create CalibreRepository - will retry later")
            
            # Create services
            self.logger.info("Creating embedding and text processing services...")
            config_dict = self.config.as_dict()
            self.embedding_service = create_embedding_service(config_dict)
            self.text_processor = TextProcessor()
            self.logger.info("Embedding and text processing services created")
            
            # Create indexing service only if we have both repositories
            self.logger.info("Attempting to create IndexingService...")
            if self.calibre_repo and self.embedding_repo:
                self.logger.info("Both repositories available, creating IndexingService")
                self.indexing_service = IndexingService(
                    text_processor=self.text_processor,
                    embedding_service=self.embedding_service,
                    embedding_repo=self.embedding_repo,
                    calibre_repo=self.calibre_repo
                )
                self.logger.info("IndexingService created successfully")
            else:
                self.logger.warning(f"Cannot create IndexingService - calibre_repo: {self.calibre_repo is not None}, embedding_repo: {self.embedding_repo is not None}")
                self.indexing_service = None
            
            # Summary of what was created
            self.logger.info("=== SERVICE INITIALIZATION SUMMARY ===")
            self.logger.info(f"Database path: {self.db_path}")
            self.logger.info(f"EmbeddingRepository: {'✓' if self.embedding_repo else '✗'}")
            self.logger.info(f"CalibreRepository: {'✓' if self.calibre_repo else '✗'}")
            self.logger.info(f"EmbeddingService: {'✓' if self.embedding_service else '✗'}")
            self.logger.info(f"IndexingService: {'✓' if self.indexing_service else '✗'}")
            self.logger.info("=== END SUMMARY ===")
            
            if self.indexing_service:
                self.logger.info("All services initialized successfully")
            else:
                self.logger.warning("Services partially initialized - indexing may not work")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize services: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            # Store the error for display
            self.initialization_error = str(e)
            # Services will be created on-demand if initialization fails
    
    def get_embedding_service(self):
        """Get the embedding service, creating if needed"""
        self.logger.info("get_embedding_service() called")
        if not hasattr(self, 'embedding_service') or not self.embedding_service:
            self.logger.info("embedding_service not available, calling _initialize_services()")
            self._initialize_services()
        else:
            self.logger.info("embedding_service already available")
        return self.embedding_service if hasattr(self, 'embedding_service') else None
    
    def get_indexing_service(self):
        """Get the indexing service, creating if needed"""
        self.logger.info("get_indexing_service() called")
        if not hasattr(self, 'indexing_service') or not self.indexing_service:
            self.logger.info("indexing_service not available, calling _initialize_services()")
            self._initialize_services()
        else:
            self.logger.info("indexing_service already available")
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
    
    def debug_database_state(self):
        """Debug function to check database state"""
        try:
            if hasattr(self, 'embedding_repo') and self.embedding_repo:
                status = self.embedding_repo.db.verify_schema()
                self.logger.info(f"Database status: {status}")
                return status
            else:
                self.logger.warning("No embedding repository available for debugging")
                return {"error": "No embedding repository"}
        except Exception as e:
            self.logger.error(f"Error checking database state: {e}")
            return {"error": str(e)}

    
    def location_selected(self, loc):
        """
        Called when plugin is visible and user selects books.
        This enables the context menu items for selected books.
        """
        # Guard against early calls before GUI is ready
        if not self.gui or not hasattr(self.gui, 'current_view') or not self.gui.current_view():
            return
            
        current_view = self.gui.current_view()
        if not current_view or not current_view.selectionModel():
            return
        
        # Enable/disable context menu items based on selection
        selected_rows = current_view.selectionModel().selectedRows()
        enabled = len(selected_rows) > 0
        
        # Enable index selected action when books are selected
        if hasattr(self, 'index_selected_action'):
            self.index_selected_action.setEnabled(enabled)
        
        # Enable find similar action only for single selection
        if hasattr(self, 'similar_action'):
            single_selection = len(selected_rows) == 1
            self.similar_action.setEnabled(single_selection)

    def shutting_down(self):
        """
        Called when Calibre is shutting down
        """
        # Clean up resources
        if hasattr(self, "search_dialog"):
            self.search_dialog.close()
    
    def _find_similar_from_context(self):
        """Find similar books from context menu"""
        # Get selected book (single selection for similarity)
        rows = self.gui.current_view().selectionModel().selectedRows()
        if not rows:
            error_dialog(
                self.gui,
                "No Selection", 
                "Please select a book to find similar books.",
                show=True,
            )
            return
        
        if len(rows) > 1:
            error_dialog(
                self.gui,
                "Multiple Selection",
                "Please select only one book to find similar books.\n\n"
                "Select a single book and try again.",
                show=True,
            )
            return
        
        # Get the selected book
        book_id = self.gui.current_view().model().id(rows[0])
        
        try:
            # Get book metadata for search
            if hasattr(self.gui, 'current_db') and self.gui.current_db:
                mi = self.gui.current_db.new_api.get_metadata(book_id)
                book_title = mi.title
                
                # Create search query from book title and authors
                search_query = book_title
                if mi.authors:
                    # Add first author to help with similarity
                    search_query += f" {mi.authors[0]}"
                
                # Open search dialog with pre-filled query
                self.show_dialog()
                if hasattr(self, "search_dialog"):
                    self.search_dialog.set_initial_query(search_query)
                    self.search_dialog.set_scope_to_exclude_book(book_id)
            else:
                error_dialog(
                    self.gui,
                    "Database Error",
                    "Cannot access book information. Please try again.",
                    show=True,
                )
                
        except Exception as e:
            self.logger.error(f"Error finding similar books: {e}")
            error_dialog(
                self.gui,
                "Search Error", 
                f"An error occurred while preparing similarity search:\n\n{str(e)}",
                show=True,
            )
    


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
