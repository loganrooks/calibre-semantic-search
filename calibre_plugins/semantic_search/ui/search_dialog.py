"""
Main search dialog for semantic search
"""

import asyncio
import logging
from typing import List, Optional

from PyQt5.Qt import (
    QAction,
    QCheckBox,
    QComboBox,
    QDialog,
    QFont,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSize,
    QSlider,
    QSpinBox,
    QSplitter,
    Qt,
    QTextEdit,
    QTimer,
    QToolButton,
    QVBoxLayout,
    QWidget,
    pyqtSignal,
)

from calibre.gui2 import info_dialog
from calibre_plugins.semantic_search.config import SemanticSearchConfig
from calibre_plugins.semantic_search.core.search_engine import (
    SearchEngine,
    SearchMode,
    SearchOptions,
    SearchResult,
    SearchScope,
)
from calibre_plugins.semantic_search.ui.widgets import (
    ResultCard,
    ScopeSelector,
    SearchModeSelector,
    SimilaritySlider,
)

logger = logging.getLogger(__name__)


class SemanticSearchDialog(QDialog):
    """Main search dialog"""

    def __init__(self, gui, plugin):
        super().__init__(gui)
        self.gui = gui
        self.plugin = plugin
        self.config = SemanticSearchConfig()
        self.search_engine = None  # Will be initialized when needed
        self.current_results = []

        self._setup_ui()
        self._load_settings()
        self._connect_signals()

        # Setup async event loop for search
        self.loop = asyncio.new_event_loop()

    def _setup_ui(self):
        """Create the dialog UI"""
        self.setWindowTitle("Semantic Search")
        self.setMinimumSize(800, 600)

        # Main layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Search input section
        search_group = QGroupBox("Search Query")
        search_layout = QVBoxLayout()
        search_group.setLayout(search_layout)

        # Query input
        self.query_input = QTextEdit()
        self.query_input.setMaximumHeight(100)
        self.query_input.setPlaceholderText(
            "Enter your search query...\n"
            "Examples: 'consciousness and phenomenology', 'the nature of being'"
        )
        search_layout.addWidget(self.query_input)

        # Search controls
        controls_layout = QHBoxLayout()

        self.search_button = QPushButton("Search")
        self.search_button.setDefault(True)
        controls_layout.addWidget(self.search_button)

        self.clear_button = QPushButton("Clear")
        controls_layout.addWidget(self.clear_button)

        controls_layout.addStretch()

        # Character counter
        self.char_counter = QLabel("0 / 5000")
        controls_layout.addWidget(self.char_counter)

        search_layout.addLayout(controls_layout)
        layout.addWidget(search_group)

        # Options section
        options_group = QGroupBox("Search Options")
        options_layout = QGridLayout()
        options_group.setLayout(options_layout)

        # Search mode
        options_layout.addWidget(QLabel("Mode:"), 0, 0)
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(
            [
                "Semantic (Meaning-based)",
                "Dialectical (Find Oppositions)",
                "Genealogical (Historical Development)",
                "Hybrid (Semantic + Keyword)",
            ]
        )
        options_layout.addWidget(self.mode_combo, 0, 1)

        # Search scope - use advanced widget
        options_layout.addWidget(QLabel("Scope:"), 0, 2)
        self.scope_selector = ScopeSelector(self.gui)
        options_layout.addWidget(self.scope_selector, 0, 3)

        # Similarity threshold - use custom widget
        options_layout.addWidget(QLabel("Similarity:"), 1, 0)
        self.threshold_slider = SimilaritySlider(0.7)
        options_layout.addWidget(self.threshold_slider, 1, 1)

        # Result limit
        options_layout.addWidget(QLabel("Max Results:"), 1, 2)
        self.limit_spin = QSpinBox()
        self.limit_spin.setRange(5, 100)
        self.limit_spin.setValue(20)
        self.limit_spin.setSingleStep(5)
        options_layout.addWidget(self.limit_spin, 1, 3)

        # Advanced options button
        self.advanced_button = QToolButton()
        self.advanced_button.setText("Advanced ▼")
        self.advanced_button.setPopupMode(QToolButton.InstantPopup)

        advanced_menu = QMenu()
        self.include_context_action = advanced_menu.addAction("Include Context")
        self.include_context_action.setCheckable(True)
        self.include_context_action.setChecked(True)

        self.advanced_button.setMenu(advanced_menu)
        options_layout.addWidget(self.advanced_button, 1, 4)

        layout.addWidget(options_group)

        # Results section
        results_splitter = QSplitter(Qt.Vertical)

        # Results list
        self.results_list = QListWidget()
        self.results_list.setAlternatingRowColors(True)
        results_splitter.addWidget(self.results_list)

        # Status bar
        self.status_bar = QLabel("Ready to search")
        self.status_bar.setStyleSheet("QLabel { color: gray; }")

        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()

        layout.addWidget(results_splitter)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_bar)

    def _connect_signals(self):
        """Connect UI signals"""
        self.search_button.clicked.connect(self.perform_search)
        self.clear_button.clicked.connect(self.clear_search)
        self.query_input.textChanged.connect(self._update_char_counter)
        # Connect threshold slider
        self.threshold_slider.valueChanged.connect(self._on_threshold_changed)

    def _load_settings(self):
        """Load saved settings"""
        # Load search options
        self.limit_spin.setValue(self.config.get("search_options.default_limit", 20))
        threshold = self.config.get("search_options.similarity_threshold", 0.7)
        self.threshold_slider.setValue(threshold)

        # Set default scope
        scope_map = {
            "library": 0,
            "current_book": 1,
            "selected_books": 2,
        }
        # No need to set scope selector here - it initializes itself

    def _update_char_counter(self):
        """Update character counter"""
        count = len(self.query_input.toPlainText())
        self.char_counter.setText(f"{count} / 5000")

        if count > 5000:
            self.char_counter.setStyleSheet("QLabel { color: red; }")
        else:
            self.char_counter.setStyleSheet("QLabel { color: gray; }")

    def perform_search(self):
        """Execute search"""
        query = self.query_input.toPlainText().strip()

        if not query:
            QMessageBox.warning(self, "Empty Query", "Please enter a search query.")
            return

        if len(query) > 5000:
            QMessageBox.warning(
                self, "Query Too Long", "Query must be less than 5000 characters."
            )
            return

        # Initialize search engine if needed
        if not self.search_engine:
            self._initialize_search_engine()

        # Build search options
        options = self._build_search_options()

        # Show progress
        self.progress_bar.show()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.status_bar.setText("Searching...")
        self.search_button.setEnabled(False)

        # Clear previous results
        self.results_list.clear()
        self.current_results = []

        # Run search asynchronously
        try:
            # Run async search in event loop
            future = asyncio.run_coroutine_threadsafe(
                self.search_engine.search(query, options), self.loop
            )

            # Schedule result handling
            QTimer.singleShot(100, lambda: self._check_search_complete(future))

        except Exception as e:
            logger.error(f"Search error: {e}")
            self._search_error(str(e))

    def _check_search_complete(self, future):
        """Check if search is complete"""
        if future.done():
            try:
                results = future.result()
                self._display_results(results)
            except Exception as e:
                self._search_error(str(e))
        else:
            # Check again in 100ms
            QTimer.singleShot(100, lambda: self._check_search_complete(future))

    def _display_results(self, results: List[SearchResult]):
        """Display search results"""
        self.current_results = results

        self.progress_bar.hide()
        self.search_button.setEnabled(True)

        if not results:
            self.status_bar.setText("No results found")
            return

        self.status_bar.setText(f"Found {len(results)} results")

        # Add results to list
        for result in results:
            # Convert SearchResult to dict format expected by ResultCard
            result_data = {
                'title': result.book_title,
                'author': ', '.join(result.authors) if hasattr(result, 'authors') else 'Unknown',
                'similarity': result.similarity_score,
                'chunk_text': result.chunk_text,
                'book_id': result.book_id,
                'chunk_id': getattr(result, 'chunk_id', 0)
            }
            
            # Create custom widget
            card = ResultCard(result_data)
            card.viewInBook.connect(self._view_in_book)
            card.findSimilar.connect(self._find_similar)
            card.copyCitation.connect(self._copy_citation)

            # Create list item
            item = QListWidgetItem()
            item.setSizeHint(card.sizeHint())

            self.results_list.addItem(item)
            self.results_list.setItemWidget(item, card)

    def _search_error(self, error_msg: str):
        """Handle search error"""
        self.progress_bar.hide()
        self.search_button.setEnabled(True)
        self.status_bar.setText(f"Search error: {error_msg}")

        QMessageBox.critical(
            self, "Search Error", f"An error occurred during search:\n\n{error_msg}"
        )

    def _build_search_options(self) -> SearchOptions:
        """Build search options from UI"""
        # Map combo indices to enums
        mode_map = {
            0: SearchMode.SEMANTIC,
            1: SearchMode.DIALECTICAL,
            2: SearchMode.GENEALOGICAL,
            3: SearchMode.HYBRID,
        }

        # Get scope from scope selector
        scope_data = self.scope_selector.get_scope_data()
        scope_type = self.scope_selector.scope_combo.currentText()
        
        scope_map = {
            "Entire Library": SearchScope.LIBRARY,
            "Current Book": SearchScope.CURRENT_BOOK,
            "Selected Books": SearchScope.SELECTED_BOOKS,
            "Books by Author": SearchScope.AUTHOR,
            "Books with Tag": SearchScope.TAG,
            "Custom Collection": SearchScope.LIBRARY,  # Treat as library for now
        }

        options = SearchOptions(
            mode=mode_map.get(self.mode_combo.currentIndex(), SearchMode.SEMANTIC),
            scope=scope_map.get(scope_type, SearchScope.LIBRARY),
            limit=self.limit_spin.value(),
            similarity_threshold=self.threshold_slider.value(),
            include_context=self.include_context_action.isChecked(),
        )

        # Add scope-specific data
        if scope_type == "Selected Books" and "book_ids" in scope_data:
            options.book_ids = scope_data["book_ids"]
        elif scope_type == "Books by Author" and "author" in scope_data:
            options.author_filter = scope_data["author"]
        elif scope_type == "Books with Tag" and "tag" in scope_data:
            options.tag_filter = scope_data["tag"]
        elif scope_type == "Current Book":
            # Try to get current book from library view
            try:
                current_row = self.gui.current_view().currentIndex()
                if current_row.isValid():
                    options.book_ids = [self.gui.current_view().model().id(current_row)]
            except:
                pass

        return options

    def _initialize_search_engine(self):
        """Initialize search engine with dependencies"""
        try:
            import os
            import asyncio
            import threading
            from calibre_plugins.semantic_search.core.search_engine import SearchEngine
            from calibre_plugins.semantic_search.core.embedding_service import create_embedding_service
            from calibre_plugins.semantic_search.data.repositories import (
                EmbeddingRepository, CalibreRepository
            )
            
            # Get library path
            library_path = self.gui.library_path
            db_dir = os.path.join(library_path, 'semantic_search')
            os.makedirs(db_dir, exist_ok=True)
            db_path = os.path.join(db_dir, 'embeddings.db')
            
            # Create repositories
            embedding_repo = EmbeddingRepository(db_path)
            calibre_repo = CalibreRepository(self.gui.current_db.new_api)
            
            # Create embedding service with current config
            config_dict = self.config.as_dict()
            embedding_service = create_embedding_service(config_dict)
            
            # Create search engine
            self.search_engine = SearchEngine(embedding_repo, embedding_service)
            
            # Create event loop for async operations
            self.loop = asyncio.new_event_loop()
            self.loop_thread = threading.Thread(target=self.loop.run_forever)
            self.loop_thread.daemon = True
            self.loop_thread.start()
            
            self.status_bar.setText("Search engine initialized successfully")
            
        except Exception as e:
            self.status_bar.setText(f"Search engine initialization failed: {str(e)}")
            # Log the error for debugging
            import traceback
            print(f"Search engine init error: {traceback.format_exc()}")

    def _view_in_book(self, book_id: int):
        """View result in book viewer"""
        try:
            # Get the View action from Calibre's interface
            view_action = self.gui.iactions.get('View')
            if view_action:
                # Open the book in viewer
                view_action.view_book(book_id)
                self.status_bar.setText(f"Opened book {book_id} in viewer")
            else:
                info_dialog(
                    self,
                    "View in Book",
                    f"Could not find viewer action. Book ID: {book_id}",
                    show=True,
                )
        except Exception as e:
            info_dialog(
                self,
                "View in Book Error",
                f"Failed to open book {book_id}: {str(e)}",
                show=True,
            )

    def _find_similar(self, chunk_id: int):
        """Find similar passages"""
        try:
            if not self.search_engine:
                self._initialize_search_engine()
                
            # Find the current result by chunk_id
            current_result = None
            for result in self.current_results:
                if hasattr(result, 'chunk_id') and result.chunk_id == chunk_id:
                    current_result = result
                    break
                    
            if current_result:
                # Use the chunk text as the search query
                query = current_result.chunk_text[:200]  # First 200 chars
                self.query_input.setPlainText(query)
                
                # Set search mode to semantic similarity
                self.mode_combo.setCurrentIndex(0)  # Semantic mode
                
                # Perform search
                self.perform_search()
                self.status_bar.setText("Searching for similar passages...")
            else:
                info_dialog(
                    self,
                    "Find Similar",
                    f"Could not find chunk {chunk_id} in current results.",
                    show=True,
                )
        except Exception as e:
            info_dialog(
                self,
                "Find Similar Error",
                f"Failed to find similar passages: {str(e)}",
                show=True,
            )

    def _on_threshold_changed(self, value: float):
        """Handle similarity threshold change"""
        # Update the config with new threshold value
        self.config.set("search_options.similarity_threshold", value)
        self.status_bar.setText(f"Similarity threshold set to {value:.2f}")

    def _copy_citation(self, book_id: int, chunk_id: int = None):
        """Copy citation to clipboard"""
        try:
            # Find the result data
            result_data = None
            for result in self.current_results:
                if result.book_id == book_id:
                    if chunk_id is None or (hasattr(result, 'chunk_id') and result.chunk_id == chunk_id):
                        result_data = result
                        break
            
            if result_data:
                # Format citation
                authors = ', '.join(result_data.authors) if hasattr(result_data, 'authors') and result_data.authors else 'Unknown Author'
                citation = f"{authors}. {result_data.book_title}."
                
                # Add chunk context if available
                if hasattr(result_data, 'chunk_text') and result_data.chunk_text:
                    # Get first sentence or first 100 chars
                    excerpt = result_data.chunk_text[:100].strip()
                    if len(result_data.chunk_text) > 100:
                        excerpt += "..."
                    citation += f' "{excerpt}"'
                
                # Copy to clipboard
                from PyQt5.Qt import QApplication
                clipboard = QApplication.clipboard()
                clipboard.setText(citation)
                
                self.status_bar.setText("Citation copied to clipboard")
            else:
                info_dialog(
                    self,
                    "Copy Citation",
                    f"Could not find book {book_id} in current results.",
                    show=True,
                )
        except Exception as e:
            info_dialog(
                self,
                "Copy Citation Error", 
                f"Failed to copy citation: {str(e)}",
                show=True,
            )

    def clear_search(self):
        """Clear search query and results"""
        self.query_input.clear()
        self.results_list.clear()
        self.current_results = []
        self.status_bar.setText("Ready to search")

    def library_changed(self):
        """Handle library change"""
        # Clear results as they may be invalid
        self.clear_search()

        # Re-initialize search engine
        self.search_engine = None

    def closeEvent(self, event):
        """Handle dialog close"""
        # Save window geometry
        # Clean up event loop
        if hasattr(self, "loop") and self.loop and self.loop.is_running():
            # Stop the loop before closing
            self.loop.call_soon_threadsafe(self.loop.stop)
            # Wait a moment for loop to stop
            import time
            time.sleep(0.1)
        
        if hasattr(self, "loop_thread") and self.loop_thread.is_alive():
            # Thread will stop when loop stops
            pass

        event.accept()
