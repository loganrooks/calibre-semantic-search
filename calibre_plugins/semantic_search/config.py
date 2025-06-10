"""
ConfigWidget - MVP Pattern Implementation

This is the "dumb" view component that only handles Qt UI setup and simple setters/getters.
All business logic has been moved to ConfigPresenter following DEVELOPMENT_GUIDE.md MVP patterns.
"""

import logging

from PyQt5.Qt import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QSlider,
    QSpinBox,
    Qt,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

# Import configuration manager
from .config_manager import SemanticSearchConfig

# Import presenter for MVP pattern
from .presenters.config_presenter import ConfigPresenter


class ConfigWidget(QWidget):
    """
    MVP Pattern ConfigWidget - 'Dumb' View Component
    
    ARCHITECTURE COMPLIANCE:
    - Only handles Qt widget setup and layout
    - Simple setter/getter methods for UI updates
    - Delegates ALL business logic to ConfigPresenter
    - NO configuration management in view
    - NO validation or connection testing in view
    """

    def __init__(self):
        super().__init__()
        
        # Initialize logging (MVP pattern - view can have logger)
        self.logger = logging.getLogger('calibre_plugins.semantic_search.ui.config')
        self.logger.info("ConfigWidget initializing (MVP pattern)")
        
        # Set up UI first
        self._setup_ui()
        
        # Initialize presenter (MVP pattern)
        self.presenter = ConfigPresenter(self)
        
        # Connect signals to presenter
        self._connect_signals()
        
        # Load configuration via presenter
        self.presenter.load_configuration()
        
        self.logger.info("ConfigWidget initialized successfully")

    def _setup_ui(self):
        """Create the configuration UI - ONLY Qt setup, no business logic"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Create tab widget for different sections
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Create tabs (UI setup only)
        self._create_api_tab()
        self._create_search_tab()
        self._create_indexing_tab()
        self._create_performance_tab()
        self._create_ui_tab()

    def _create_api_tab(self):
        """Create API configuration tab - UI setup only"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # Add explanation
        explanation = QLabel(
            "The AI provider generates 'embeddings' - numerical representations of text meaning.\n"
            "This enables semantic search to find conceptually similar passages.\n"
            "Choose your provider and configure the specific settings below."
        )
        explanation.setWordWrap(True)
        explanation.setStyleSheet("QLabel { color: #666; margin-bottom: 10px; }")
        layout.addWidget(explanation)

        # Main provider selection
        provider_group = QGroupBox("AI Provider Selection")
        provider_layout = QFormLayout()
        provider_group.setLayout(provider_layout)

        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["mock", "openai", "azure_openai", "vertex_ai", "direct_vertex_ai", "cohere", "local"])
        self.provider_combo.setToolTip("Choose the AI service that will analyze your text during indexing.")
        provider_layout.addRow("Provider:", self.provider_combo)

        # Model selection
        self.model_combo = QComboBox()
        self.model_combo.setToolTip("Select the specific model to use with this provider")
        self.model_combo.setEditable(True)
        provider_layout.addRow("Model:", self.model_combo)

        # Model info display
        self.model_info_label = QLabel("")
        self.model_info_label.setWordWrap(True)
        self.model_info_label.setStyleSheet("QLabel { color: #666; font-size: 11px; margin-top: 2px; }")
        provider_layout.addRow("", self.model_info_label)

        # API Key
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        provider_layout.addRow("API Key:", self.api_key_edit)

        # Test connection button
        self.test_btn = QPushButton("Test Connection")
        provider_layout.addRow("", self.test_btn)

        layout.addWidget(provider_group)
        
        # Provider-specific configuration sections
        self._create_provider_sections(layout)
        
        layout.addStretch()
        self.tabs.addTab(widget, "AI Provider")
    
    def _create_provider_sections(self, layout):
        """Create provider-specific configuration sections - UI setup only"""
        
        # OpenAI-specific settings
        self.openai_group = QGroupBox("OpenAI Configuration")
        openai_layout = QFormLayout()
        self.openai_group.setLayout(openai_layout)
        
        openai_help = QLabel("✅ OpenAI provides high-quality embeddings. API key required.")
        openai_help.setWordWrap(True)
        openai_help.setStyleSheet("QLabel { color: #666; margin-bottom: 5px; }")
        openai_layout.addRow("", openai_help)
        
        layout.addWidget(self.openai_group)
        self.openai_group.setVisible(False)
        
        # Vertex AI-specific settings  
        self.vertex_group = QGroupBox("Google Vertex AI Configuration")
        vertex_layout = QFormLayout()
        self.vertex_group.setLayout(vertex_layout)
        
        vertex_help = QLabel("⚙️ Vertex AI requires a Google Cloud project with the Vertex AI API enabled.")
        vertex_help.setWordWrap(True)
        vertex_help.setStyleSheet("QLabel { color: #666; margin-bottom: 5px; }")
        vertex_layout.addRow("", vertex_help)
        
        self.vertex_project_edit = QLineEdit()
        self.vertex_project_edit.setPlaceholderText("your-gcp-project-id")
        vertex_layout.addRow("Project ID*:", self.vertex_project_edit)
        
        # Create location dropdown with fallback to QLineEdit
        try:
            from .ui.simple_location_combo import SimpleLocationCombo
            self.vertex_location_edit = SimpleLocationCombo("vertex_ai", self)
            self.vertex_location_edit.set_region_code("us-central1")
            self.logger.info("Using SimpleLocationCombo for Vertex AI location")
        except Exception as e:
            self.logger.warning(f"Failed to create SimpleLocationCombo: {e}")
            self.vertex_location_edit = QLineEdit()
            self.vertex_location_edit.setText("us-central1")
            self.vertex_location_edit.setPlaceholderText("e.g., us-central1, europe-west1")
        vertex_layout.addRow("Location:", self.vertex_location_edit)
        
        layout.addWidget(self.vertex_group)
        self.vertex_group.setVisible(False)
        
        # Direct Vertex AI-specific settings
        self.direct_vertex_group = QGroupBox("Direct Vertex AI Configuration")
        direct_vertex_layout = QFormLayout()
        self.direct_vertex_group.setLayout(direct_vertex_layout)
        
        direct_vertex_help = QLabel("🔥 Direct Vertex AI enables gemini-embedding-001 with custom dimensionality (1-3072).")
        direct_vertex_help.setWordWrap(True)
        direct_vertex_help.setStyleSheet("QLabel { color: #666; margin-bottom: 5px; }")
        direct_vertex_layout.addRow("", direct_vertex_help)
        
        self.direct_vertex_project_edit = QLineEdit()
        self.direct_vertex_project_edit.setPlaceholderText("your-gcp-project-id")
        direct_vertex_layout.addRow("Project ID*:", self.direct_vertex_project_edit)
        
        # Create location dropdown with fallback to QLineEdit
        try:
            from .ui.simple_location_combo import SimpleLocationCombo
            self.direct_vertex_location_edit = SimpleLocationCombo("direct_vertex_ai", self)
            self.direct_vertex_location_edit.set_region_code("us-central1")
            self.logger.info("Using SimpleLocationCombo for Direct Vertex AI location")
        except Exception as e:
            self.logger.warning(f"Failed to create SimpleLocationCombo: {e}")
            self.direct_vertex_location_edit = QLineEdit()
            self.direct_vertex_location_edit.setText("us-central1")
            self.direct_vertex_location_edit.setPlaceholderText("e.g., us-central1, europe-west1")
        direct_vertex_layout.addRow("Location:", self.direct_vertex_location_edit)
        
        self.direct_vertex_dimensions_spin = QSpinBox()
        self.direct_vertex_dimensions_spin.setRange(1, 3072)
        self.direct_vertex_dimensions_spin.setValue(768)
        self.direct_vertex_dimensions_spin.setSingleStep(256)
        self.direct_vertex_dimensions_spin.setToolTip("Custom embedding dimensions (1-3072).")
        direct_vertex_layout.addRow("Custom Dimensions:", self.direct_vertex_dimensions_spin)
        
        layout.addWidget(self.direct_vertex_group)
        self.direct_vertex_group.setVisible(False)
        
        # Cohere-specific settings
        self.cohere_group = QGroupBox("Cohere Configuration")
        cohere_layout = QFormLayout()
        self.cohere_group.setLayout(cohere_layout)
        
        cohere_help = QLabel("🎯 Cohere models support input type specification for optimized embeddings.")
        cohere_help.setWordWrap(True)
        cohere_help.setStyleSheet("QLabel { color: #666; margin-bottom: 5px; }")
        cohere_layout.addRow("", cohere_help)
        
        self.cohere_input_type_combo = QComboBox()
        self.cohere_input_type_combo.addItems([
            "search_document", "search_query", "classification", "clustering"
        ])
        self.cohere_input_type_combo.setCurrentText("search_document")
        cohere_layout.addRow("Input Type:", self.cohere_input_type_combo)
        
        layout.addWidget(self.cohere_group)
        self.cohere_group.setVisible(False)
        
        # Azure OpenAI-specific settings
        self.azure_group = QGroupBox("Azure OpenAI Configuration")
        azure_layout = QFormLayout()
        self.azure_group.setLayout(azure_layout)
        
        azure_help = QLabel("🔧 Azure OpenAI requires deployment-specific configuration.")
        azure_help.setWordWrap(True)
        azure_help.setStyleSheet("QLabel { color: #666; margin-bottom: 5px; }")
        azure_layout.addRow("", azure_help)
        
        self.azure_deployment_edit = QLineEdit()
        self.azure_deployment_edit.setPlaceholderText("e.g., text-embedding-ada-002")
        azure_layout.addRow("Deployment Name*:", self.azure_deployment_edit)
        
        self.azure_api_base_edit = QLineEdit()
        self.azure_api_base_edit.setPlaceholderText("https://your-resource.openai.azure.com/")
        azure_layout.addRow("API Base URL*:", self.azure_api_base_edit)
        
        self.azure_api_version_edit = QLineEdit()
        self.azure_api_version_edit.setText("2024-02-01")
        azure_layout.addRow("API Version:", self.azure_api_version_edit)
        
        layout.addWidget(self.azure_group)
        self.azure_group.setVisible(False)

    def _create_search_tab(self):
        """Create search options tab - UI setup only"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        search_group = QGroupBox("Search Settings")
        search_layout = QFormLayout()
        search_group.setLayout(search_layout)

        self.result_limit_spin = QSpinBox()
        self.result_limit_spin.setRange(5, 100)
        self.result_limit_spin.setSingleStep(5)
        search_layout.addRow("Result Limit:", self.result_limit_spin)

        threshold_layout = QHBoxLayout()
        self.threshold_slider = QSlider(Qt.Horizontal)
        self.threshold_slider.setRange(0, 100)
        self.threshold_slider.setSingleStep(5)
        self.threshold_label = QLabel("70%")
        self.threshold_slider.valueChanged.connect(
            lambda v: self.threshold_label.setText(f"{v}%")
        )
        threshold_layout.addWidget(self.threshold_slider)
        threshold_layout.addWidget(self.threshold_label)
        search_layout.addRow("Similarity Threshold:", threshold_layout)

        self.scope_combo = QComboBox()
        self.scope_combo.addItems(["library", "selected_books", "current_book"])
        search_layout.addRow("Search Scope:", self.scope_combo)

        layout.addWidget(search_group)
        layout.addStretch()
        self.tabs.addTab(widget, "Search")

    def _create_indexing_tab(self):
        """Create indexing tab - UI setup only"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Embedding dimensions
        embedding_group = QGroupBox("Embedding Configuration")
        embedding_layout = QFormLayout()
        embedding_group.setLayout(embedding_layout)
        
        self.dimensions_spin = QSpinBox()
        self.dimensions_spin.setRange(256, 4096)
        self.dimensions_spin.setSingleStep(256)
        self.dimensions_spin.setValue(768)
        self.dimensions_spin.setToolTip("Automatically set based on model selection in AI Provider tab")
        embedding_layout.addRow("Embedding Dimensions:", self.dimensions_spin)
        
        layout.addWidget(embedding_group)

        # Text processing
        process_group = QGroupBox("Text Processing")
        process_layout = QFormLayout()
        process_group.setLayout(process_layout)

        self.chunk_size_spin = QSpinBox()
        self.chunk_size_spin.setRange(100, 2000)
        self.chunk_size_spin.setSingleStep(50)
        process_layout.addRow("Chunk Size:", self.chunk_size_spin)

        self.chunk_overlap_spin = QSpinBox()
        self.chunk_overlap_spin.setRange(0, 200)
        self.chunk_overlap_spin.setSingleStep(10)
        process_layout.addRow("Chunk Overlap:", self.chunk_overlap_spin)

        layout.addWidget(process_group)
        layout.addStretch()
        self.tabs.addTab(widget, "Indexing")

    def _create_performance_tab(self):
        """Create performance tab - UI setup only"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        cache_group = QGroupBox("Cache Settings")
        cache_layout = QFormLayout()
        cache_group.setLayout(cache_layout)

        self.cache_enabled_check = QCheckBox("Enable caching")
        cache_layout.addRow("", self.cache_enabled_check)

        self.cache_size_spin = QSpinBox()
        self.cache_size_spin.setRange(10, 1000)
        self.cache_size_spin.setSingleStep(10)
        self.cache_size_spin.setSuffix(" MB")
        cache_layout.addRow("Cache Size:", self.cache_size_spin)

        layout.addWidget(cache_group)
        layout.addStretch()
        self.tabs.addTab(widget, "Performance")

    def _create_ui_tab(self):
        """Create UI options tab - UI setup only"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        window_group = QGroupBox("Window Options")
        window_layout = QFormLayout()
        window_group.setLayout(window_layout)

        self.floating_check = QCheckBox("Enable floating search window")
        window_layout.addRow("", self.floating_check)

        self.remember_pos_check = QCheckBox("Remember window position")
        window_layout.addRow("", self.remember_pos_check)

        opacity_layout = QHBoxLayout()
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(50, 100)
        self.opacity_slider.setSingleStep(5)
        self.opacity_label = QLabel("95%")
        self.opacity_slider.valueChanged.connect(
            lambda v: self.opacity_label.setText(f"{v}%")
        )
        opacity_layout.addWidget(self.opacity_slider)
        opacity_layout.addWidget(self.opacity_label)
        window_layout.addRow("Window Opacity:", opacity_layout)

        layout.addWidget(window_group)
        layout.addStretch()
        self.tabs.addTab(widget, "Interface")

    def _connect_signals(self):
        """Connect Qt signals to presenter methods - NO business logic here"""
        self.provider_combo.currentTextChanged.connect(self._on_provider_changed)
        self.model_combo.currentTextChanged.connect(self._on_model_changed)
        self.test_btn.clicked.connect(self._test_connection)

    def _on_provider_changed(self, provider):
        """Signal handler - delegates to presenter"""
        self.presenter.on_provider_changed(provider)

    def _on_model_changed(self, model):
        """Signal handler - delegates to presenter"""
        self.presenter.on_model_changed(model)

    def _test_connection(self):
        """Test connection - delegates to presenter"""
        provider = self.get_provider()
        api_key = self.get_api_key()
        model = self.get_model()
        
        # Get provider-specific values
        kwargs = {}
        if provider in ["vertex_ai", "direct_vertex_ai"]:
            kwargs['project_id'] = self.get_vertex_project_id()
            kwargs['location'] = self.get_vertex_location()
            if provider == "direct_vertex_ai":
                kwargs['dimensions'] = self.get_vertex_dimensions()
        elif provider == "azure_openai":
            kwargs['deployment'] = self.get_azure_deployment()
            kwargs['api_base'] = self.get_azure_api_base()
        elif provider == "cohere":
            kwargs['input_type'] = self.get_cohere_input_type()
        
        self.presenter.test_connection(provider, api_key, model, **kwargs)

    # SIMPLE SETTER METHODS - MVP Pattern (called by presenter)
    
    def set_provider(self, provider):
        """Simple setter - just update UI"""
        self.provider_combo.setCurrentText(provider)
    
    def set_model(self, model):
        """Simple setter - just update UI"""
        self.model_combo.setCurrentText(model)
    
    def set_api_key(self, api_key):
        """Simple setter - just update UI"""
        self.api_key_edit.setText(api_key)
    
    def set_model_info(self, info_text):
        """Simple setter - just update UI"""
        self.model_info_label.setText(info_text)
    
    def show_provider_section(self, provider):
        """Simple setter - show/hide provider sections"""
        self.openai_group.setVisible(provider == "openai")
        self.vertex_group.setVisible(provider == "vertex_ai")
        self.direct_vertex_group.setVisible(provider == "direct_vertex_ai")
        self.cohere_group.setVisible(provider == "cohere")
        self.azure_group.setVisible(provider == "azure_openai")
    
    def update_model_list(self, models):
        """Simple setter - update model dropdown"""
        self.model_combo.clear()
        self.model_combo.addItems(models)
        if models and models[0] != "Use deployment name in field above":
            self.model_combo.setCurrentIndex(0)
    
    def set_model_placeholder(self, placeholder):
        """Simple setter - update model placeholder"""
        if self.model_combo.lineEdit():
            self.model_combo.lineEdit().setPlaceholderText(placeholder)
    
    def set_model_enabled(self, enabled):
        """Simple setter - enable/disable model field"""
        self.model_combo.setEnabled(enabled)
    
    def show_connection_progress(self, show):
        """Simple setter - show/hide connection progress"""
        if show:
            self.progress = QProgressDialog("Testing connection...", "Cancel", 0, 0, self)
            self.progress.setWindowModality(Qt.WindowModal)
            self.progress.show()
        else:
            if hasattr(self, 'progress'):
                self.progress.close()
                delattr(self, 'progress')
    
    def show_connection_result(self, success, message):
        """Simple setter - show connection result"""
        if success:
            QMessageBox.information(self, "Test Connection", message)
        else:
            QMessageBox.warning(self, "Test Connection", message)
    
    def set_result_limit(self, limit):
        """Simple setter - just update UI"""
        self.result_limit_spin.setValue(limit)
    
    def set_similarity_threshold(self, threshold):
        """Simple setter - just update UI"""
        self.threshold_slider.setValue(threshold)
    
    def set_search_scope(self, scope):
        """Simple setter - just update UI"""
        self.scope_combo.setCurrentText(scope)
    
    def set_cache_enabled(self, enabled):
        """Simple setter - just update UI"""
        self.cache_enabled_check.setChecked(enabled)
    
    def set_cache_size(self, size):
        """Simple setter - just update UI"""
        self.cache_size_spin.setValue(size)
    
    def set_floating_window(self, floating):
        """Simple setter - just update UI"""
        self.floating_check.setChecked(floating)
    
    def set_remember_position(self, remember):
        """Simple setter - just update UI"""
        self.remember_pos_check.setChecked(remember)
    
    def set_window_opacity(self, opacity):
        """Simple setter - just update UI"""
        self.opacity_slider.setValue(opacity)
    
    def set_vertex_project_id(self, project_id):
        """Simple setter - just update UI"""
        self.vertex_project_edit.setText(project_id)
        self.direct_vertex_project_edit.setText(project_id)
    
    def set_vertex_location(self, location):
        """Simple setter - just update UI"""
        # Handle both SimpleLocationCombo and QLineEdit
        if hasattr(self.vertex_location_edit, 'set_region_code'):
            self.vertex_location_edit.set_region_code(location)
        else:
            self.vertex_location_edit.setText(location)
        
        if hasattr(self.direct_vertex_location_edit, 'set_region_code'):
            self.direct_vertex_location_edit.set_region_code(location)
        else:
            self.direct_vertex_location_edit.setText(location)
    
    def set_vertex_dimensions(self, dimensions):
        """Simple setter - just update UI"""
        self.direct_vertex_dimensions_spin.setValue(dimensions)
    
    def set_azure_deployment(self, deployment):
        """Simple setter - just update UI"""
        self.azure_deployment_edit.setText(deployment)
    
    def set_azure_api_base(self, api_base):
        """Simple setter - just update UI"""
        self.azure_api_base_edit.setText(api_base)
    
    def set_azure_api_version(self, api_version):
        """Simple setter - just update UI"""
        self.azure_api_version_edit.setText(api_version)
    
    def set_cohere_input_type(self, input_type):
        """Simple setter - just update UI"""
        self.cohere_input_type_combo.setCurrentText(input_type)

    # SIMPLE GETTER METHODS - MVP Pattern (called by presenter)
    
    def get_provider(self):
        """Simple getter - just read UI"""
        return self.provider_combo.currentText()
    
    def get_model(self):
        """Simple getter - just read UI"""
        return self.model_combo.currentText()
    
    def get_api_key(self):
        """Simple getter - just read UI"""
        return self.api_key_edit.text()
    
    def get_result_limit(self):
        """Simple getter - just read UI"""
        return self.result_limit_spin.value()
    
    def get_similarity_threshold(self):
        """Simple getter - just read UI"""
        return self.threshold_slider.value()
    
    def get_search_scope(self):
        """Simple getter - just read UI"""
        return self.scope_combo.currentText()
    
    def get_cache_enabled(self):
        """Simple getter - just read UI"""
        return self.cache_enabled_check.isChecked()
    
    def get_cache_size(self):
        """Simple getter - just read UI"""
        return self.cache_size_spin.value()
    
    def get_floating_window(self):
        """Simple getter - just read UI"""
        return self.floating_check.isChecked()
    
    def get_remember_position(self):
        """Simple getter - just read UI"""
        return self.remember_pos_check.isChecked()
    
    def get_window_opacity(self):
        """Simple getter - just read UI"""
        return self.opacity_slider.value()
    
    def get_embedding_dimensions(self):
        """Simple getter - just read UI"""
        return self.dimensions_spin.value()
    
    def get_vertex_project_id(self):
        """Simple getter - just read UI"""
        return self.direct_vertex_project_edit.text().strip()
    
    def get_vertex_location(self):
        """Simple getter - just read UI"""
        # Handle both SimpleLocationCombo and QLineEdit
        if hasattr(self.direct_vertex_location_edit, 'get_region_code'):
            return self.direct_vertex_location_edit.get_region_code()
        else:
            return self.direct_vertex_location_edit.text().strip()
    
    def get_vertex_dimensions(self):
        """Simple getter - just read UI"""
        return self.direct_vertex_dimensions_spin.value()
    
    def get_azure_deployment(self):
        """Simple getter - just read UI"""
        return self.azure_deployment_edit.text().strip()
    
    def get_azure_api_base(self):
        """Simple getter - just read UI"""
        return self.azure_api_base_edit.text().strip()
    
    def get_azure_api_version(self):
        """Simple getter - just read UI"""
        return self.azure_api_version_edit.text().strip()
    
    def get_cohere_input_type(self):
        """Simple getter - just read UI"""
        return self.cohere_input_type_combo.currentText()

    def save_settings(self):
        """Save settings - delegates to presenter"""
        self.presenter.save_configuration()