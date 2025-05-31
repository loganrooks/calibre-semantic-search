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

from calibre_plugins.semantic_search.config import SemanticSearchConfig
from calibre_plugins.semantic_search.core.search_engine import (
    SearchEngine,
    SearchMode,
    SearchOptions,
    SearchResult,
    SearchScope,
)

logger = logging.getLogger(__name__)


class ResultCard(QWidget):
    """Custom widget for displaying a search result"""

    view_clicked = pyqtSignal(int)  # book_id
    similar_clicked = pyqtSignal(int)  # chunk_id

    def __init__(self, result: SearchResult, parent=None):
        super().__init__(parent)
        self.result = result
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Header with title and authors
        header_layout = QHBoxLayout()

        # Book info
        book_info = QLabel(
            f"<b>{self.result.book_title}</b><br>"
            f"<i>{', '.join(self.result.authors)}</i>"
        )
        header_layout.addWidget(book_info)

        # Similarity score
        score_label = QLabel(f"{self.result.similarity_score:.2%}")
        score_label.setStyleSheet("color: green; font-weight: bold;")
        header_layout.addStretch()
        header_layout.addWidget(score_label)

        layout.addLayout(header_layout)

        # Chunk text
        text_edit = QTextEdit()
        text_edit.setPlainText(self.result.chunk_text)
        text_edit.setReadOnly(True)
        text_edit.setMaximumHeight(150)
        layout.addWidget(text_edit)

        # Action buttons
        button_layout = QHBoxLayout()

        view_btn = QPushButton("View in Book")
        view_btn.clicked.connect(lambda: self.view_clicked.emit(self.result.book_id))
        button_layout.addWidget(view_btn)

        similar_btn = QPushButton("Find Similar")
        similar_btn.clicked.connect(
            lambda: self.similar_clicked.emit(self.result.chunk_id)
        )
        button_layout.addWidget(similar_btn)

        cite_btn = QPushButton("Copy Citation")
        cite_btn.clicked.connect(self._copy_citation)
        button_layout.addWidget(cite_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        # Style
        self.setStyleSheet(
            """
            ResultCard {
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 10px;
                margin: 5px;
            }
        """
        )

    def _copy_citation(self):
        """Copy citation to clipboard"""
        from PyQt5.Qt import QApplication

        clipboard = QApplication.clipboard()
        clipboard.setText(self.result.citation)


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

        # Search scope
        options_layout.addWidget(QLabel("Scope:"), 0, 2)
        self.scope_combo = QComboBox()
        self.scope_combo.addItems(
            [
                "Entire Library",
                "Current Book",
                "Selected Books",
                "Specific Author",
                "Specific Tag",
            ]
        )
        options_layout.addWidget(self.scope_combo, 0, 3)

        # Similarity threshold
        options_layout.addWidget(QLabel("Similarity:"), 1, 0)
        threshold_layout = QHBoxLayout()
        self.threshold_slider = QSlider(Qt.Horizontal)
        self.threshold_slider.setRange(0, 100)
        self.threshold_slider.setValue(70)
        self.threshold_label = QLabel("0.70")
        threshold_layout.addWidget(self.threshold_slider)
        threshold_layout.addWidget(self.threshold_label)
        options_layout.addLayout(threshold_layout, 1, 1)

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
        self.threshold_slider.valueChanged.connect(
            lambda v: self.threshold_label.setText(f"{v/100:.2f}")
        )

    def _load_settings(self):
        """Load saved settings"""
        # Load search options
        self.limit_spin.setValue(self.config.get("search_options.default_limit", 20))
        threshold = int(
            self.config.get("search_options.similarity_threshold", 0.7) * 100
        )
        self.threshold_slider.setValue(threshold)

        # Set default scope
        scope_map = {
            "library": 0,
            "current_book": 1,
            "selected_books": 2,
        }
        scope = self.config.get("search_options.scope", "library")
        self.scope_combo.setCurrentIndex(scope_map.get(scope, 0))

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
            # Create custom widget
            card = ResultCard(result)
            card.view_clicked.connect(self._view_in_book)
            card.similar_clicked.connect(self._find_similar)

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

        scope_map = {
            0: SearchScope.LIBRARY,
            1: SearchScope.CURRENT_BOOK,
            2: SearchScope.SELECTED_BOOKS,
            3: SearchScope.AUTHOR,
            4: SearchScope.TAG,
        }

        options = SearchOptions(
            mode=mode_map.get(self.mode_combo.currentIndex(), SearchMode.SEMANTIC),
            scope=scope_map.get(self.scope_combo.currentIndex(), SearchScope.LIBRARY),
            limit=self.limit_spin.value(),
            similarity_threshold=self.threshold_slider.value() / 100,
            include_context=self.include_context_action.isChecked(),
        )

        # Add specific filters based on scope
        if options.scope == SearchScope.CURRENT_BOOK:
            # Get current book ID from viewer if available
            # For now, we'll need to implement this
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
                    self.gui,
                    "View in Book",
                    f"Could not find viewer action. Book ID: {book_id}",
                    show=True,
                )
        except Exception as e:
            info_dialog(
                self.gui,
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
                    self.gui,
                    "Find Similar",
                    f"Could not find chunk {chunk_id} in current results.",
                    show=True,
                )
        except Exception as e:
            info_dialog(
                self.gui,
                "Find Similar Error",
                f"Failed to find similar passages: {str(e)}",
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
        if hasattr(self, "loop"):
            self.loop.close()

        event.accept()
