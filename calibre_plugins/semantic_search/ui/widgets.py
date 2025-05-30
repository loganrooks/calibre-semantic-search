"""
Custom widgets for semantic search UI
"""

from PyQt5.Qt import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    Qt,
    QVBoxLayout,
    QWidget,
    pyqtSignal,
)


class SimilaritySlider(QWidget):
    """Custom slider widget for similarity threshold"""

    valueChanged = pyqtSignal(float)

    def __init__(self, initial_value=0.7, parent=None):
        super().__init__(parent)
        self._setup_ui(initial_value)

    def _setup_ui(self, initial_value):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # Slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(int(initial_value * 100))
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setTickInterval(10)

        # Labels
        layout.addWidget(QLabel("0.0"))
        layout.addWidget(self.slider)
        layout.addWidget(QLabel("1.0"))

        # Value label
        self.value_label = QLabel(f"{initial_value:.2f}")
        self.value_label.setMinimumWidth(40)
        self.value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.value_label)

        # Connect signal
        self.slider.valueChanged.connect(self._on_slider_change)

    def _on_slider_change(self, value):
        float_value = value / 100.0
        self.value_label.setText(f"{float_value:.2f}")
        self.valueChanged.emit(float_value)

    def value(self) -> float:
        return self.slider.value() / 100.0

    def setValue(self, value: float):
        self.slider.setValue(int(value * 100))


class ScopeSelector(QWidget):
    """Widget for selecting search scope"""

    scopeChanged = pyqtSignal(str, object)  # scope_type, scope_data

    def __init__(self, gui, parent=None):
        super().__init__(parent)
        self.gui = gui
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # Scope type selector
        self.scope_combo = QComboBox()
        self.scope_combo.addItems(
            [
                "Entire Library",
                "Current Book",
                "Selected Books",
                "Books by Author",
                "Books with Tag",
                "Custom Collection",
            ]
        )
        layout.addWidget(self.scope_combo)

        # Dynamic options area
        self.options_widget = QWidget()
        self.options_layout = QVBoxLayout()
        self.options_widget.setLayout(self.options_layout)
        layout.addWidget(self.options_widget)

        # Connect signal
        self.scope_combo.currentIndexChanged.connect(self._on_scope_change)

        # Initialize
        self._on_scope_change(0)

    def _on_scope_change(self, index):
        """Handle scope type change"""
        # Clear previous options
        while self.options_layout.count():
            child = self.options_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        scope_type = self.scope_combo.currentText()

        if scope_type == "Books by Author":
            # Add author selector
            self.author_combo = QComboBox()
            self.author_combo.setEditable(True)
            self.author_combo.setInsertPolicy(QComboBox.NoInsert)

            # Populate with authors from library
            self._populate_authors()

            self.options_layout.addWidget(QLabel("Select Author:"))
            self.options_layout.addWidget(self.author_combo)

        elif scope_type == "Books with Tag":
            # Add tag selector
            self.tag_combo = QComboBox()
            self.tag_combo.setEditable(True)

            # Populate with tags
            self._populate_tags()

            self.options_layout.addWidget(QLabel("Select Tag:"))
            self.options_layout.addWidget(self.tag_combo)

        elif scope_type == "Custom Collection":
            # Add collection selector
            self.collection_combo = QComboBox()
            self._populate_collections()

            self.options_layout.addWidget(QLabel("Select Collection:"))
            self.options_layout.addWidget(self.collection_combo)

        # Emit change signal
        self.scopeChanged.emit(scope_type, self.get_scope_data())

    def _populate_authors(self):
        """Populate author combo box"""
        try:
            db = self.gui.current_db.new_api
            authors = db.all_author_names()
            self.author_combo.addItems(sorted(authors))
        except:
            pass

    def _populate_tags(self):
        """Populate tag combo box"""
        try:
            db = self.gui.current_db.new_api
            tags = db.all_tag_names()
            self.tag_combo.addItems(sorted(tags))
        except:
            pass

    def _populate_collections(self):
        """Populate collection combo box"""
        # This would get saved search collections
        self.collection_combo.addItems(["My Research", "Philosophy Papers", "To Read"])

    def get_scope_data(self):
        """Get current scope configuration"""
        scope_type = self.scope_combo.currentText()

        if scope_type == "Entire Library":
            return {}
        elif scope_type == "Current Book":
            return {"current_book": True}
        elif scope_type == "Selected Books":
            # Get selected book IDs from library view
            try:
                rows = self.gui.current_view().selectionModel().selectedRows()
                book_ids = [self.gui.current_view().model().id(row) for row in rows]
                return {"book_ids": book_ids}
            except:
                return {"book_ids": []}
        elif scope_type == "Books by Author":
            if hasattr(self, "author_combo"):
                return {"author": self.author_combo.currentText()}
        elif scope_type == "Books with Tag":
            if hasattr(self, "tag_combo"):
                return {"tag": self.tag_combo.currentText()}
        elif scope_type == "Custom Collection":
            if hasattr(self, "collection_combo"):
                return {"collection": self.collection_combo.currentText()}

        return {}


class SearchModeSelector(QGroupBox):
    """Widget for selecting search mode with explanations"""

    modeChanged = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__("Search Mode", parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QGridLayout()
        self.setLayout(layout)

        # Search modes with descriptions
        modes = [
            (
                "Semantic",
                "Find conceptually similar passages",
                "Best for exploring related ideas and concepts",
            ),
            (
                "Dialectical",
                "Find opposing concepts and tensions",
                "Useful for philosophical analysis of contradictions",
            ),
            (
                "Genealogical",
                "Trace concept development over time",
                "Perfect for historical analysis of ideas",
            ),
            (
                "Hybrid",
                "Combine semantic and keyword search",
                "Balanced approach for comprehensive results",
            ),
        ]

        self.mode_buttons = []

        for i, (mode, short_desc, long_desc) in enumerate(modes):
            # Radio button
            from PyQt5.Qt import QRadioButton

            radio = QRadioButton(mode)
            radio.setToolTip(long_desc)

            if i == 0:  # Default to semantic
                radio.setChecked(True)

            # Description label
            desc_label = QLabel(short_desc)
            desc_label.setStyleSheet("QLabel { color: gray; font-size: 10pt; }")

            layout.addWidget(radio, i, 0)
            layout.addWidget(desc_label, i, 1)

            self.mode_buttons.append(radio)

            # Connect signal
            radio.toggled.connect(
                lambda checked, m=mode: self.modeChanged.emit(m) if checked else None
            )

    def get_mode(self) -> str:
        """Get currently selected mode"""
        for button in self.mode_buttons:
            if button.isChecked():
                return button.text()
        return "Semantic"


class ResultFilterPanel(QFrame):
    """Panel for filtering search results"""

    filtersChanged = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.StyledPanel)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Title
        title = QLabel("Filter Results")
        title.setStyleSheet("QLabel { font-weight: bold; }")
        layout.addWidget(title)

        # Author filter
        self.author_check = QCheckBox("By Author")
        self.author_combo = QComboBox()
        self.author_combo.setEnabled(False)

        self.author_check.toggled.connect(self.author_combo.setEnabled)
        self.author_check.toggled.connect(self._emit_filters)
        self.author_combo.currentTextChanged.connect(self._emit_filters)

        layout.addWidget(self.author_check)
        layout.addWidget(self.author_combo)

        # Date range filter
        self.date_check = QCheckBox("By Publication Date")
        date_widget = QWidget()
        date_layout = QHBoxLayout()
        date_layout.setContentsMargins(0, 0, 0, 0)
        date_widget.setLayout(date_layout)

        from PyQt5.Qt import QSpinBox

        self.year_from = QSpinBox()
        self.year_from.setRange(1000, 2100)
        self.year_from.setValue(1900)
        self.year_from.setEnabled(False)

        self.year_to = QSpinBox()
        self.year_to.setRange(1000, 2100)
        self.year_to.setValue(2024)
        self.year_to.setEnabled(False)

        date_layout.addWidget(self.year_from)
        date_layout.addWidget(QLabel("to"))
        date_layout.addWidget(self.year_to)

        self.date_check.toggled.connect(self.year_from.setEnabled)
        self.date_check.toggled.connect(self.year_to.setEnabled)
        self.date_check.toggled.connect(self._emit_filters)
        self.year_from.valueChanged.connect(self._emit_filters)
        self.year_to.valueChanged.connect(self._emit_filters)

        layout.addWidget(self.date_check)
        layout.addWidget(date_widget)

        # Language filter
        self.language_check = QCheckBox("By Language")
        self.language_combo = QComboBox()
        self.language_combo.addItems(
            ["English", "German", "French", "Spanish", "Latin"]
        )
        self.language_combo.setEnabled(False)

        self.language_check.toggled.connect(self.language_combo.setEnabled)
        self.language_check.toggled.connect(self._emit_filters)
        self.language_combo.currentTextChanged.connect(self._emit_filters)

        layout.addWidget(self.language_check)
        layout.addWidget(self.language_combo)

        # Minimum score filter
        self.score_check = QCheckBox("Minimum Similarity")
        self.score_slider = SimilaritySlider(0.5)
        self.score_slider.setEnabled(False)

        self.score_check.toggled.connect(self.score_slider.setEnabled)
        self.score_check.toggled.connect(self._emit_filters)
        self.score_slider.valueChanged.connect(self._emit_filters)

        layout.addWidget(self.score_check)
        layout.addWidget(self.score_slider)

        layout.addStretch()

        # Clear filters button
        clear_btn = QPushButton("Clear All Filters")
        clear_btn.clicked.connect(self.clear_filters)
        layout.addWidget(clear_btn)

    def _emit_filters(self):
        """Emit current filter configuration"""
        filters = {}

        if self.author_check.isChecked():
            filters["author"] = self.author_combo.currentText()

        if self.date_check.isChecked():
            filters["year_from"] = self.year_from.value()
            filters["year_to"] = self.year_to.value()

        if self.language_check.isChecked():
            filters["language"] = self.language_combo.currentText()

        if self.score_check.isChecked():
            filters["min_score"] = self.score_slider.value()

        self.filtersChanged.emit(filters)

    def clear_filters(self):
        """Clear all filters"""
        self.author_check.setChecked(False)
        self.date_check.setChecked(False)
        self.language_check.setChecked(False)
        self.score_check.setChecked(False)

    def update_authors(self, authors):
        """Update author list from search results"""
        self.author_combo.clear()
        self.author_combo.addItems(sorted(set(authors)))
