"""
Configuration management for Semantic Search plugin
"""

import os
import asyncio
from pathlib import Path
from typing import Any, Dict, Optional, List

from calibre.utils.config import JSONConfig
from PyQt5.Qt import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QSpinBox,
    Qt,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

# Import discovery system (with fallback if not available)
try:
    import sys
    import os
    # Add root directory to path to import discovery system
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)
    from embedding_model_discovery_system import EmbeddingModelDiscovery, EmbeddingModelInfo
    DISCOVERY_AVAILABLE = True
except ImportError:
    DISCOVERY_AVAILABLE = False
    EmbeddingModelDiscovery = None
    EmbeddingModelInfo = None

# Default configuration values
DEFAULTS = {
    "embedding_provider": "mock",
    "embedding_model": "text-embedding-preview-0815",
    "embedding_dimensions": 768,
    "chunk_size": 512,
    "chunk_overlap": 50,
    "api_keys": {},
    "search_options": {
        "default_limit": 20,
        "similarity_threshold": 0.7,
        "scope": "library",
    },
    "ui_options": {
        "floating_window": False,
        "window_opacity": 0.95,
        "remember_position": True,
    },
    "performance": {
        "cache_enabled": True,
        "cache_size_mb": 100,
        "batch_size": 100,
        "max_concurrent_requests": 3,
    },
}


class SemanticSearchConfig:
    """Configuration management for semantic search"""

    def __init__(self, config_path: Optional[str] = None):
        if config_path:
            # For testing
            self._config = JSONConfig(os.path.join(config_path, "semantic_search"))
        else:
            # Production
            self._config = JSONConfig("plugins/semantic_search")

        self._config.defaults = DEFAULTS

    def get(self, key: str, default: Any = None) -> Any:
        """Get config value with dot notation support"""
        # Handle nested keys
        if "." in key:
            parts = key.split(".")
            value = self._config
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part, {})
                else:
                    value = getattr(value, "get", lambda x, y: y)(part, {})
            return value if value != {} else default
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set config value with dot notation support"""
        if "." in key:
            parts = key.split(".")
            # Get existing config as dict-like structure
            config_dict = {}
            for k in self._config:
                config_dict[k] = self._config[k]
            
            current = config_dict

            # Navigate to the parent of the target key
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]

            # Set the value
            current[parts[-1]] = value

            # Save back to config
            for k, v in config_dict.items():
                self._config[k] = v
        else:
            self._config[key] = value

    def as_dict(self) -> Dict[str, Any]:
        """Get configuration as dictionary"""
        result = {}
        for key in self._config:
            result[key] = self._config[key]
        return result

    def save(self):
        """Save configuration to disk"""
        self._config.commit()


class ConfigWidget(QWidget):
    """Configuration widget for plugin settings"""

    def __init__(self):
        super().__init__()
        self.config = SemanticSearchConfig()
        
        # Initialize model discovery system
        self.model_discovery = None
        self._model_cache = {}  # Cache model names by provider
        self._model_objects_cache = {}  # Cache full model objects by provider
        if DISCOVERY_AVAILABLE:
            try:
                self.model_discovery = EmbeddingModelDiscovery()
                print("Model discovery system initialized successfully")
            except Exception as e:
                print(f"Failed to initialize model discovery: {e}")
                self.model_discovery = None
        
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        """Create the configuration UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Create tab widget for different sections
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # API Configuration Tab
        api_tab = self._create_api_tab()
        tabs.addTab(api_tab, "AI Provider")

        # Search Options Tab
        search_tab = self._create_search_tab()
        tabs.addTab(search_tab, "Search Options")
        
        # Indexing Tab
        indexing_tab = self._create_indexing_tab()
        tabs.addTab(indexing_tab, "Indexing")

        # Performance Tab
        performance_tab = self._create_performance_tab()
        tabs.addTab(performance_tab, "Performance")

        # UI Options Tab
        ui_tab = self._create_ui_tab()
        tabs.addTab(ui_tab, "UI Options")

    def _create_api_tab(self):
        """Create API configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # Add explanation
        explanation = QLabel(
            "The AI provider generates 'embeddings' - numerical representations of text meaning.\n"
            "This enables semantic search to find conceptually similar passages.\n"
            "Embeddings are created during the indexing process."
        )
        explanation.setWordWrap(True)
        explanation.setStyleSheet("QLabel { color: #666; margin-bottom: 10px; }")
        layout.addWidget(explanation)

        # Provider selection
        provider_group = QGroupBox("AI Provider for Embeddings")
        provider_layout = QFormLayout()
        provider_group.setLayout(provider_layout)

        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["mock", "openai", "azure_openai", "vertex_ai", "cohere", "local"])
        self.provider_combo.setToolTip(
            "Choose the AI service that will analyze your text during indexing.\n"
            "Mock = Free testing mode (no real AI)\n"
            "OpenAI = GPT embeddings (requires API key)\n"
            "Azure OpenAI = Microsoft Azure (requires deployment)\n"
            "Vertex AI = Google Cloud (requires setup)\n"
            "Cohere = Cohere AI (requires API key)\n"
            "Local = Ollama (coming soon)"
        )
        self.provider_combo.currentTextChanged.connect(self._on_provider_changed)
        self.provider_combo.currentTextChanged.connect(self._update_model_options)
        self.provider_combo.currentTextChanged.connect(self._update_provider_models)
        provider_layout.addRow("Provider:", self.provider_combo)

        # Enhanced model selection with search and metadata
        model_layout = QVBoxLayout()
        
        # Model dropdown with search capability
        self.model_combo_provider = QComboBox()
        self.model_combo_provider.setToolTip("Select the specific model to use with this provider")
        self.model_combo_provider.setEditable(True)  # Allow search/custom entry
        self.model_combo_provider.setInsertPolicy(QComboBox.NoInsert)  # Don't add typed text as items
        
        # Model metadata display
        self.model_metadata_label = QLabel("")
        self.model_metadata_label.setWordWrap(True)
        self.model_metadata_label.setStyleSheet("QLabel { color: #666; font-size: 11px; margin-top: 2px; }")
        
        model_layout.addWidget(self.model_combo_provider)
        model_layout.addWidget(self.model_metadata_label)
        
        provider_layout.addRow("Model:", model_layout)
        
        # Connect model selection to metadata display
        self.model_combo_provider.currentTextChanged.connect(self._on_model_changed)

        # API Key
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        provider_layout.addRow("API Key:", self.api_key_edit)

        # Test connection button
        test_btn = QPushButton("Test Connection")
        test_btn.clicked.connect(self._test_connection)
        provider_layout.addRow("", test_btn)

        layout.addWidget(provider_group)
        
        # Provider-specific configuration sections
        self._create_provider_sections(layout)
        
        layout.addStretch()

        return widget
        
    def _create_provider_sections(self, layout):
        """Create provider-specific configuration sections"""
        
        # OpenAI-specific settings
        self.openai_group = QGroupBox("OpenAI Settings")
        openai_layout = QFormLayout()
        self.openai_group.setLayout(openai_layout)
        
        openai_help = QLabel("OpenAI provides high-quality embeddings with various model sizes.")
        openai_help.setWordWrap(True)
        openai_help.setStyleSheet("QLabel { color: #666; margin-bottom: 5px; }")
        openai_layout.addRow("", openai_help)
        
        layout.addWidget(self.openai_group)
        self.openai_group.setVisible(False)  # Hidden by default
        
        # Vertex AI-specific settings  
        self.vertex_group = QGroupBox("Google Vertex AI Settings")
        vertex_layout = QFormLayout()
        self.vertex_group.setLayout(vertex_layout)
        
        vertex_help = QLabel("Vertex AI requires a Google Cloud project with the Vertex AI API enabled.")
        vertex_help.setWordWrap(True)
        vertex_help.setStyleSheet("QLabel { color: #666; margin-bottom: 5px; }")
        vertex_layout.addRow("", vertex_help)
        
        self.vertex_project_edit = QLineEdit()
        self.vertex_project_edit.setPlaceholderText("your-gcp-project-id")
        vertex_layout.addRow("Project ID*:", self.vertex_project_edit)
        
        self.vertex_location_edit = QLineEdit()
        self.vertex_location_edit.setText("us-central1")
        vertex_layout.addRow("Location:", self.vertex_location_edit)
        
        layout.addWidget(self.vertex_group)
        self.vertex_group.setVisible(False)  # Hidden by default
        
        # Cohere-specific settings
        self.cohere_group = QGroupBox("Cohere Settings")
        cohere_layout = QFormLayout()
        self.cohere_group.setLayout(cohere_layout)
        
        cohere_help = QLabel("Cohere models support input type specification for optimized embeddings.")
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
        self.cohere_group.setVisible(False)  # Hidden by default
        
        # Azure OpenAI-specific settings (keeping existing)
        self.azure_group = QGroupBox("Azure OpenAI Settings")
        azure_layout = QFormLayout()
        self.azure_group.setLayout(azure_layout)
        
        azure_help = QLabel("Azure OpenAI requires deployment-specific configuration.")
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
        self.azure_group.setVisible(False)  # Hidden by default

    def _create_search_tab(self):
        """Create search options tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Search settings
        search_group = QGroupBox("Search Settings")
        search_layout = QFormLayout()
        search_group.setLayout(search_layout)

        # Result limit
        self.result_limit_spin = QSpinBox()
        self.result_limit_spin.setRange(5, 100)
        self.result_limit_spin.setSingleStep(5)
        search_layout.addRow("Default Result Limit:", self.result_limit_spin)

        # Similarity threshold
        threshold_layout = QHBoxLayout()
        self.threshold_slider = QSlider(Qt.Horizontal)
        self.threshold_slider.setRange(0, 100)
        self.threshold_slider.setSingleStep(5)
        self.threshold_label = QLabel("0.70")
        self.threshold_slider.valueChanged.connect(
            lambda v: self.threshold_label.setText(f"{v/100:.2f}")
        )
        threshold_layout.addWidget(self.threshold_slider)
        threshold_layout.addWidget(self.threshold_label)
        search_layout.addRow("Similarity Threshold:", threshold_layout)

        # Default scope
        self.scope_combo = QComboBox()
        self.scope_combo.addItems(["library", "current_book", "selected_books"])
        search_layout.addRow("Default Scope:", self.scope_combo)

        layout.addWidget(search_group)
        layout.addStretch()

        return widget
    
    def _create_indexing_tab(self):
        """Create indexing options tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Add explanation
        explanation = QLabel(
            "Indexing prepares your books for semantic search by:\n"
            "1. Extracting text from books\n"
            "2. Splitting text into searchable chunks\n"
            "3. Generating embeddings (via AI provider)\n"
            "4. Storing everything in the search database"
        )
        explanation.setWordWrap(True)
        explanation.setStyleSheet("QLabel { color: #666; margin-bottom: 10px; }")
        layout.addWidget(explanation)
        
        # Batch Processing Settings
        batch_group = QGroupBox("Batch Processing")
        batch_layout = QFormLayout()
        batch_group.setLayout(batch_layout)
        
        # Books per batch
        self.batch_size_spin = QSpinBox()
        self.batch_size_spin.setRange(1, 100)
        self.batch_size_spin.setSingleStep(5)
        batch_layout.addRow("Books per batch:", self.batch_size_spin)
        
        # Concurrent requests
        self.max_concurrent_spin = QSpinBox()
        self.max_concurrent_spin.setRange(1, 10)
        batch_layout.addRow("Max concurrent requests:", self.max_concurrent_spin)
        
        layout.addWidget(batch_group)
        
        # Auto-indexing Settings
        auto_group = QGroupBox("Automatic Indexing")
        auto_layout = QFormLayout()
        auto_group.setLayout(auto_layout)
        
        # Auto-index new books
        self.auto_index_new = QCheckBox("Automatically index new books")
        auto_layout.addRow("", self.auto_index_new)
        
        # Auto-index on library change
        self.auto_index_library = QCheckBox("Re-index when switching libraries")
        auto_layout.addRow("", self.auto_index_library)
        
        layout.addWidget(auto_group)
        
        # Embedding Configuration
        embedding_group = QGroupBox("Embedding Configuration")
        embedding_layout = QFormLayout()
        embedding_group.setLayout(embedding_layout)
        
        # Model selection removed from Indexing tab to avoid conflicts
        # Model is configured in AI Provider tab only
        
        # Embedding dimensions
        self.dimensions_spin = QSpinBox()
        self.dimensions_spin.setRange(256, 4096)
        self.dimensions_spin.setSingleStep(256)
        self.dimensions_spin.setValue(768)  # Default
        self.dimensions_spin.setToolTip("Number of dimensions in the embedding vector")
        embedding_layout.addRow("Embedding Dimensions:", self.dimensions_spin)
        
        layout.addWidget(embedding_group)
        
        # Text Processing Settings
        process_group = QGroupBox("Text Processing")
        process_layout = QFormLayout()
        process_group.setLayout(process_layout)
        
        # Chunking strategy
        self.chunking_strategy_combo = QComboBox()
        self.chunking_strategy_combo.addItems([
            "Fixed Size", 
            "Sentence-based (Coming Soon)",
            "Paragraph-based (Coming Soon)",
            "Semantic (Coming Soon)"
        ])
        self.chunking_strategy_combo.setCurrentIndex(0)
        self.chunking_strategy_combo.setToolTip("How to split text into chunks")
        process_layout.addRow("Chunking Strategy:", self.chunking_strategy_combo)
        
        # Chunk size
        self.chunk_size_spin = QSpinBox()
        self.chunk_size_spin.setRange(100, 2000)
        self.chunk_size_spin.setSingleStep(100)
        self.chunk_size_spin.setToolTip(
            "Size of text chunks for embedding generation.\n"
            "Smaller chunks = more precise search results.\n"
            "Larger chunks = more context preserved."
        )
        process_layout.addRow("Chunk Size (words):", self.chunk_size_spin)

        # Chunk overlap
        self.chunk_overlap_spin = QSpinBox()
        self.chunk_overlap_spin.setRange(0, 500)
        self.chunk_overlap_spin.setSingleStep(10)
        self.chunk_overlap_spin.setToolTip(
            "Overlap between consecutive chunks.\n"
            "Helps preserve context across chunk boundaries."
        )
        process_layout.addRow("Chunk Overlap (words):", self.chunk_overlap_spin)
        
        # Philosophy mode
        self.philosophy_mode = QCheckBox("Enable philosophy-aware processing")
        self.philosophy_mode.setToolTip(
            "Preserves arguments and philosophical structure during chunking"
        )
        process_layout.addRow("", self.philosophy_mode)
        
        # Skip front/back matter
        self.skip_matter = QCheckBox("Skip front/back matter")
        self.skip_matter.setToolTip(
            "Skip table of contents, indexes, bibliographies"
        )
        process_layout.addRow("", self.skip_matter)
        
        layout.addWidget(process_group)
        layout.addStretch()
        
        return widget

    def _create_performance_tab(self):
        """Create performance options tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Cache settings
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

        # Note: Batch processing settings have been moved to Indexing tab
        # This tab now focuses on cache settings only
        
        layout.addStretch()

        return widget

    def _create_ui_tab(self):
        """Create UI options tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Window options
        window_group = QGroupBox("Window Options")
        window_layout = QFormLayout()
        window_group.setLayout(window_layout)

        self.floating_check = QCheckBox("Enable floating search window")
        window_layout.addRow("", self.floating_check)

        self.remember_pos_check = QCheckBox("Remember window position")
        window_layout.addRow("", self.remember_pos_check)

        # Opacity
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

        return widget

    def _load_settings(self):
        """Load settings from config"""
        # API settings
        self.provider_combo.setCurrentText(self.config.get("embedding_provider"))
        self.model_combo_provider.setCurrentText(self.config.get("embedding_model"))

        # Load API key for current provider
        provider = self.provider_combo.currentText()
        api_key = self.config.get(f"api_keys.{provider}", "")
        self.api_key_edit.setText(api_key)

        # Search settings
        self.result_limit_spin.setValue(self.config.get("search_options.default_limit"))
        self.threshold_slider.setValue(
            int(self.config.get("search_options.similarity_threshold") * 100)
        )
        self.scope_combo.setCurrentText(self.config.get("search_options.scope"))

        # Performance settings
        self.cache_enabled_check.setChecked(
            self.config.get("performance.cache_enabled")
        )
        self.cache_size_spin.setValue(self.config.get("performance.cache_size_mb"))

        # UI settings
        self.floating_check.setChecked(self.config.get("ui_options.floating_window"))
        self.remember_pos_check.setChecked(
            self.config.get("ui_options.remember_position")
        )
        self.opacity_slider.setValue(
            int(self.config.get("ui_options.window_opacity") * 100)
        )
        
        # Indexing settings
        self.batch_size_spin.setValue(
            self.config.get("indexing_options.batch_size", 10)
        )
        self.max_concurrent_spin.setValue(
            self.config.get("indexing_options.max_concurrent_requests", 3)
        )
        self.auto_index_new.setChecked(
            self.config.get("indexing_options.auto_index_new", False)
        )
        self.auto_index_library.setChecked(
            self.config.get("indexing_options.auto_index_library", False)
        )
        self.chunk_size_spin.setValue(self.config.get("chunk_size", 512))
        self.chunk_overlap_spin.setValue(self.config.get("chunk_overlap", 50))
        self.philosophy_mode.setChecked(
            self.config.get("indexing_options.philosophy_mode", True)
        )
        self.skip_matter.setChecked(
            self.config.get("indexing_options.skip_matter", True)
        )
        
        # New embedding configuration
        self.dimensions_spin.setValue(
            self.config.get("embedding_dimensions", 768)
        )
        self.chunking_strategy_combo.setCurrentIndex(
            self.config.get("chunking_strategy", 0)
        )
        
        # Model selection handled in AI Provider tab only
        
        # Azure-specific settings
        self.azure_deployment_edit.setText(self.config.get("azure_deployment", ""))
        self.azure_api_base_edit.setText(self.config.get("azure_api_base", ""))
        self.azure_api_version_edit.setText(self.config.get("azure_api_version", "2024-02-01"))
        
        # Trigger provider changed to show/hide fields
        self._on_provider_changed(self.provider_combo.currentText())

    def save_settings(self):
        """Save settings to config"""
        # API settings
        self.config.set("embedding_provider", self.provider_combo.currentText())
        self.config.set("embedding_model", self.model_combo_provider.currentText())

        # Save API key for current provider
        provider = self.provider_combo.currentText()
        self.config.set(f"api_keys.{provider}", self.api_key_edit.text())

        # Search settings
        self.config.set("search_options.default_limit", self.result_limit_spin.value())
        self.config.set(
            "search_options.similarity_threshold", self.threshold_slider.value() / 100
        )
        self.config.set("search_options.scope", self.scope_combo.currentText())

        # Performance settings
        self.config.set(
            "performance.cache_enabled", self.cache_enabled_check.isChecked()
        )
        self.config.set("performance.cache_size_mb", self.cache_size_spin.value())

        # UI settings
        self.config.set("ui_options.floating_window", self.floating_check.isChecked())
        self.config.set(
            "ui_options.remember_position", self.remember_pos_check.isChecked()
        )
        self.config.set("ui_options.window_opacity", self.opacity_slider.value() / 100)
        
        # Indexing settings
        self.config.set("indexing_options.batch_size", self.batch_size_spin.value())
        self.config.set("indexing_options.max_concurrent_requests", self.max_concurrent_spin.value())
        self.config.set("indexing_options.auto_index_new", self.auto_index_new.isChecked())
        self.config.set("indexing_options.auto_index_library", self.auto_index_library.isChecked())
        self.config.set("chunk_size", self.chunk_size_spin.value())
        self.config.set("chunk_overlap", self.chunk_overlap_spin.value())
        self.config.set("indexing_options.philosophy_mode", self.philosophy_mode.isChecked())
        self.config.set("indexing_options.skip_matter", self.skip_matter.isChecked())
        
        # New embedding configuration
        # Model is set in AI Provider tab only (removed model_combo conflict)
        self.config.set("embedding_dimensions", self.dimensions_spin.value())
        self.config.set("chunking_strategy", self.chunking_strategy_combo.currentIndex())
        
        # Azure-specific settings
        self.config.set("azure_deployment", self.azure_deployment_edit.text())
        self.config.set("azure_api_base", self.azure_api_base_edit.text())
        self.config.set("azure_api_version", self.azure_api_version_edit.text())

        # Save to disk
        self.config.save()

    def _update_model_options(self, provider):
        """Update default dimensions based on selected provider"""
        # Set reasonable defaults for dimensions based on provider
        if provider == "OpenAI":
            self.dimensions_spin.setValue(1536)  # Default for OpenAI
        elif provider == "Vertex AI":
            self.dimensions_spin.setValue(768)  # Default for Vertex
        elif provider == "Cohere":
            self.dimensions_spin.setValue(1024)  # Default for Cohere
        elif provider == "Azure OpenAI":
            self.dimensions_spin.setValue(1536)
        else:  # Mock/Local
            self.dimensions_spin.setValue(768)
    
    def _update_provider_models(self, provider):
        """Update AI Provider tab model dropdown based on selected provider"""
        self.model_combo_provider.clear()
        
        # Try dynamic discovery first, fallback to hardcoded
        if self.model_discovery:
            # Start async discovery (non-blocking)
            try:
                # Check cache first
                if provider in self._model_cache:
                    print(f"Using cached models for {provider}")
                    models = self._model_cache[provider]
                    self.model_combo_provider.addItems(models)
                    
                    # Trigger metadata display for current selection
                    current_model = self.model_combo_provider.currentText()
                    if current_model:
                        self._on_model_changed(current_model)
                    return
                
                # Start discovery in background
                print(f"Starting dynamic model discovery for {provider}")
                asyncio.create_task(self._update_provider_models_async(provider))
                
                # Meanwhile, show hardcoded models as placeholder
                self._add_hardcoded_models(provider)
                
            except Exception as e:
                print(f"Discovery failed, using hardcoded models: {e}")
                self._add_hardcoded_models(provider)
        else:
            # Discovery not available, use hardcoded
            self._add_hardcoded_models(provider)
    
    def _add_hardcoded_models(self, provider):
        """Fallback to hardcoded model lists"""
        if provider == "openai":
            self.model_combo_provider.addItems([
                "text-embedding-3-small",
                "text-embedding-3-large",
                "text-embedding-ada-002"
            ])
        elif provider == "vertex_ai":
            self.model_combo_provider.addItems([
                "text-embedding-004",
                "text-embedding-preview-0815",
                "textembedding-gecko@003",
                "textembedding-gecko-multilingual@001"
            ])
        elif provider == "cohere":
            self.model_combo_provider.addItems([
                "embed-english-v3.0",
                "embed-multilingual-v3.0",
                "embed-english-light-v3.0"
            ])
        elif provider == "azure_openai":
            self.model_combo_provider.addItems([
                "text-embedding-3-small",
                "text-embedding-3-large", 
                "text-embedding-ada-002"
            ])
        else:  # mock/local
            self.model_combo_provider.addItems(["mock-embedding"])
    
    async def _update_provider_models_async(self, provider):
        """Async method to discover and update models from LiteLLM"""
        try:
            print(f"Discovering models for provider: {provider}")
            
            # Get models for this provider
            models = await self.model_discovery.get_models_for_provider(provider)
            
            if models:
                # Extract model names for dropdown
                model_names = [model.name for model in models]
                print(f"Found {len(model_names)} models for {provider}: {model_names[:3]}...")
                
                # Cache both names and full objects
                self._model_cache[provider] = model_names
                self._model_objects_cache[provider] = models
                
                # Sort models with recommended ones first
                sorted_names = self._sort_models_by_recommendation(models)
                
                # Update UI (must be done in main thread)
                self.model_combo_provider.clear()
                self.model_combo_provider.addItems(sorted_names)
                
                # Set up search functionality with completer
                self._setup_model_search_completer(sorted_names)
                
                # Trigger metadata display for first model
                if sorted_names:
                    self.model_combo_provider.setCurrentIndex(0)
                    self._on_model_changed(sorted_names[0])
                
                print(f"Updated {provider} dropdown with {len(model_names)} discovered models")
            else:
                print(f"No models found for {provider}, keeping hardcoded")
                
        except Exception as e:
            print(f"Error in async model discovery for {provider}: {e}")
            # Keep the hardcoded models that were already loaded
    
    def get_model_metadata(self, provider: str, model_name: str) -> Optional[EmbeddingModelInfo]:
        """Get metadata for a specific model"""
        if not self.model_discovery:
            return None
            
        try:
            # Check if we have cached discovery data
            if provider in self._model_cache:
                # TODO: Store full model objects, not just names, for metadata access
                pass
            return None
        except Exception as e:
            print(f"Error getting model metadata: {e}")
            return None
    
    def _on_provider_changed(self, provider):
        """Handle provider selection change"""
        # Show/hide provider-specific settings
        self.openai_group.setVisible(provider == "openai")
        self.vertex_group.setVisible(provider == "vertex_ai")
        self.cohere_group.setVisible(provider == "cohere")
        self.azure_group.setVisible(provider == "azure_openai")
        
        # Update model field placeholder based on provider
        model_placeholders = {
            "openai": "text-embedding-3-small",
            "azure_openai": "Use deployment name instead",
            "cohere": "embed-english-v3.0",
            "vertex_ai": "text-embedding-preview-0815",
            "mock": "Not applicable",
            "local": "mxbai-embed-large"
        }
        
        # For editable combo box, we can set placeholder text via lineEdit
        if hasattr(self.model_combo_provider, 'lineEdit'):
            self.model_combo_provider.lineEdit().setPlaceholderText(model_placeholders.get(provider, ""))
        
        # Disable model field for Azure (uses deployment name)
        self.model_combo_provider.setEnabled(provider != "azure_openai")
    
    def _on_model_changed(self, model_name):
        """Handle model selection change and display metadata"""
        if not model_name:
            self.model_metadata_label.setText("")
            return
            
        provider = self.provider_combo.currentText()
        
        # Look for model metadata in cached objects
        if provider in self._model_objects_cache:
            for model_obj in self._model_objects_cache[provider]:
                if model_obj.name == model_name:
                    # Display metadata
                    metadata_parts = []
                    
                    if model_obj.dimensions:
                        metadata_parts.append(f"📊 {model_obj.dimensions} dimensions")
                    
                    if model_obj.max_tokens:
                        metadata_parts.append(f"📝 Max {model_obj.max_tokens:,} tokens")
                    
                    # Check if it's recommended for academic use
                    if self._is_recommended_for_academic(model_obj):
                        metadata_parts.append("⭐ Recommended for academic texts")
                    
                    # Show special features
                    if model_obj.special_params:
                        if model_obj.special_params.get('supports_dimensions_param'):
                            metadata_parts.append("🔧 Supports custom dimensions")
                        if model_obj.special_params.get('supports_input_type'):
                            metadata_parts.append("🎯 Supports input type optimization")
                    
                    metadata_text = " | ".join(metadata_parts) if metadata_parts else "Model information loading..."
                    self.model_metadata_label.setText(metadata_text)
                    
                    # Auto-update dimensions if available
                    if model_obj.dimensions and hasattr(self, 'dimensions_spin'):
                        self.dimensions_spin.setValue(model_obj.dimensions)
                    
                    return
        
        # Fallback: show basic info or loading message
        self.model_metadata_label.setText("Loading model information...")
    
    def _is_recommended_for_academic(self, model_obj):
        """Check if model is recommended for academic/philosophical texts"""
        # Recommend models with good dimensions for complex concepts
        if model_obj.dimensions and model_obj.dimensions >= 1536:
            return True
        
        # Recommend specific high-quality models
        academic_models = [
            "text-embedding-3-large", "text-embedding-ada-002",
            "text-embedding-004", "textembedding-gecko@003",
            "embed-english-v3.0"
        ]
        return model_obj.name in academic_models
    
    def _sort_models_by_recommendation(self, models):
        """Sort models with recommended ones first"""
        recommended = []
        others = []
        
        for model in models:
            if self._is_recommended_for_academic(model):
                recommended.append(model.name)
            else:
                others.append(model.name)
        
        # Sort each group alphabetically
        recommended.sort()
        others.sort()
        
        return recommended + others
    
    def _setup_model_search_completer(self, model_names):
        """Set up auto-complete search functionality for model dropdown"""
        try:
            from PyQt5.Qt import QCompleter, QStringListModel
            
            # Create completer with model names
            completer = QCompleter(model_names)
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            completer.setFilterMode(Qt.MatchContains)  # Allow partial matching
            
            # Set completer on the line edit of the combo box
            if hasattr(self.model_combo_provider, 'lineEdit'):
                self.model_combo_provider.lineEdit().setCompleter(completer)
                print(f"Set up search completer with {len(model_names)} models")
        except Exception as e:
            print(f"Failed to set up model search completer: {e}")
    
    def _test_connection(self):
        """Test API connection"""
        from PyQt5.Qt import QMessageBox
        import asyncio
        
        try:
            # DEBUG: Log what we're seeing
            print("=== DEBUG: Test Connection Debug Info ===")
            print(f"hasattr(self, 'plugin_interface'): {hasattr(self, 'plugin_interface')}")
            if hasattr(self, 'plugin_interface'):
                print(f"self.plugin_interface: {self.plugin_interface}")
                print(f"self.plugin_interface type: {type(self.plugin_interface)}")
            print("==========================================")
            
            # Use the interface reference passed during creation
            if hasattr(self, 'plugin_interface') and self.plugin_interface:
                plugin = self.plugin_interface
                print(f"DEBUG: Using plugin_interface: {plugin}")
            else:
                print("DEBUG: plugin_interface not available, trying fallback")
                # Fallback to old method for debugging
                plugin = None
                parent = self.parent()
                while parent and not plugin:
                    print(f"DEBUG: Checking parent: {parent} (type: {type(parent)})")
                    if hasattr(parent, 'plugin'):
                        print(f"DEBUG: Found parent.plugin: {parent.plugin}")
                        plugin = parent.plugin
                        break
                    if hasattr(parent, 'actual_plugin_'):
                        print(f"DEBUG: Found parent.actual_plugin_: {parent.actual_plugin_}")
                        plugin = parent.actual_plugin_
                        break
                    parent = parent.parent()
                
                if not plugin:
                    QMessageBox.critical(
                        self,
                        "Test Connection", 
                        "DEBUG: No plugin found through any method.\nCheck console for debug info."
                    )
                    return
            
            # Get embedding service
            service = plugin.get_embedding_service()
            if not service:
                QMessageBox.critical(
                    self,
                    "Test Connection", 
                    "Embedding service is not initialized.\nPlease check your configuration."
                )
                return
            
            # Test the connection
            QMessageBox.information(
                self,
                "Test Connection",
                "Testing connection..."
            )
            
            try:
                # Run async test
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(service.test_connection())
            finally:
                loop.close()
            
            # Show result
            if result.get('status') == 'success':
                QMessageBox.information(
                    self,
                    "Connection Test Successful",
                    f"Provider: {result.get('provider', 'Unknown')}\n"
                    f"Status: {result.get('message', 'Connected successfully')}"
                )
            else:
                QMessageBox.critical(
                    self,
                    "Connection Test Failed",
                    f"Provider: {result.get('provider', 'Unknown')}\n"
                    f"Error: {result.get('message', 'Connection failed')}"
                )
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Test Connection Error",
                f"An error occurred while testing connection:\n\n{str(e)}"
            )
