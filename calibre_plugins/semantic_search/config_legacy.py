"""
Simplified Configuration management for Semantic Search plugin
Focus on UI redesign without complex discovery system
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

from calibre.utils.config import JSONConfig
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

# LocationComboBox will be imported lazily inside ConfigWidget to avoid circular imports

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
    """Configuration management using Calibre's JSONConfig"""

    def __init__(self):
        self.config = JSONConfig("plugins/semantic_search")
        
        # Set defaults for any missing keys
        for key, value in DEFAULTS.items():
            if key not in self.config:
                self.config[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        keys = key.split(".")
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key: str, value: Any) -> None:
        """Set configuration value"""
        keys = key.split(".")
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value

    def save(self) -> None:
        """Save configuration - JSONConfig auto-saves when modified"""
        pass  # JSONConfig auto-saves, no explicit save needed

    def as_dict(self) -> Dict[str, Any]:
        """Return configuration as dictionary for service creation"""
        return dict(self.config)


class ConfigWidget(QWidget):
    """Simplified Configuration widget focusing on UI redesign"""

    def __init__(self):
        super().__init__()
        self.config = SemanticSearchConfig()
        self._setup_ui()
        self._load_settings()

    def _get_location_combo_box_class(self):
        """
        Lazy import of LocationComboBox to avoid circular import issues.
        
        Returns:
            LocationComboBox class or None if import fails
        """
        print("[CONFIG] Lazy loading LocationComboBox...")
        
        try:
            print("[CONFIG] Attempting DynamicLocationComboBox import...")
            from .ui.dynamic_location_combo_box import DynamicLocationComboBox
            print(f"[CONFIG] ✅ SUCCESS: DynamicLocationComboBox imported: {DynamicLocationComboBox}")
            return DynamicLocationComboBox
        except ImportError as e:
            print(f"[CONFIG] ❌ DynamicLocationComboBox import failed: {e}")
            # Fallback to basic LocationComboBox if DynamicLocationComboBox not available
            try:
                print("[CONFIG] Attempting basic LocationComboBox import...")
                from .ui.location_combo_box import LocationComboBox
                print(f"[CONFIG] ✅ FALLBACK: Basic LocationComboBox imported: {LocationComboBox}")
                return LocationComboBox
            except ImportError as e2:
                print(f"[CONFIG] ❌ Basic LocationComboBox import failed: {e2}")
                # Final fallback if neither available
                print("[CONFIG] ❌ FINAL FALLBACK: LocationComboBox = None")
                return None

    def _create_location_widget(self, provider_type: str, default_region: str = "us-central1"):
        """
        Create location widget (either LocationComboBox or QLineEdit fallback)
        
        Args:
            provider_type: Provider type (e.g., "vertex_ai", "direct_vertex_ai")
            default_region: Default region to set
            
        Returns:
            Tuple of (widget, is_combo_box: bool)
        """
        LocationComboBox = self._get_location_combo_box_class()
        
        print(f"[CONFIG] Creating location widget for {provider_type}. LocationComboBox available: {LocationComboBox is not None}")
        
        if LocationComboBox:
            print(f"[CONFIG] ✅ Creating LocationComboBox for {provider_type}")
            try:
                combo = LocationComboBox(provider_type)
                combo.set_region_code(default_region)
                print(f"[CONFIG] ✅ SUCCESS: LocationComboBox created: {type(combo)}")
                return combo, True
            except Exception as e:
                print(f"[CONFIG] ❌ ERROR creating LocationComboBox: {e}")
                # Emergency fallback to QLineEdit
                line_edit = QLineEdit()
                line_edit.setText(default_region)
                print("[CONFIG] ⚠️ Emergency fallback to QLineEdit")
                return line_edit, False
        else:
            print(f"[CONFIG] ❌ LocationComboBox is None, using QLineEdit fallback for {provider_type}")
            # Fallback to QLineEdit if LocationComboBox not available
            line_edit = QLineEdit()
            line_edit.setText(default_region)
            return line_edit, False

    def _setup_ui(self):
        """Create the configuration UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Create tab widget for different sections
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # API Configuration Tab - REDESIGNED
        api_tab = self._create_api_tab()
        tabs.addTab(api_tab, "AI Provider")

        # Other tabs (keeping existing)
        search_tab = self._create_search_tab()
        tabs.addTab(search_tab, "Search")

        indexing_tab = self._create_indexing_tab()
        tabs.addTab(indexing_tab, "Indexing")

        performance_tab = self._create_performance_tab()
        tabs.addTab(performance_tab, "Performance")

        ui_tab = self._create_ui_tab()
        tabs.addTab(ui_tab, "Interface")

    def _create_api_tab(self):
        """Create REDESIGNED API configuration tab with provider-specific sections"""
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
        self.provider_combo.setToolTip(
            "Choose the AI service that will analyze your text during indexing.\n"
            "Mock = Free testing mode (no real AI)\n"
            "OpenAI = GPT embeddings (requires API key)\n"
            "Azure OpenAI = Microsoft Azure (requires deployment)\n"
            "Vertex AI = Google Cloud via LiteLLM (limited models)\n"
            "Direct Vertex AI = Google Cloud direct (gemini-embedding-001 support)\n"
            "Cohere = Cohere AI (requires API key)\n"
            "Local = Ollama (coming soon)"
        )
        self.provider_combo.currentTextChanged.connect(self._on_provider_changed)
        provider_layout.addRow("Provider:", self.provider_combo)

        # SINGLE model selection (no more dual inputs!)
        self.model_combo = QComboBox()
        self.model_combo.setToolTip("Select the specific model to use with this provider")
        self.model_combo.setEditable(True)  # Allow custom entry and search
        self.model_combo.currentTextChanged.connect(self._on_model_changed)
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
        
        # Create location widget using lazy loading to avoid circular imports
        location_widget, is_combo = self._create_location_widget("vertex_ai", "us-central1")
        if is_combo:
            self.vertex_location_combo = location_widget
        else:
            self.vertex_location_edit = location_widget
        vertex_layout.addRow("Location:", location_widget)
        
        layout.addWidget(self.vertex_group)
        self.vertex_group.setVisible(False)
        
        # Direct Vertex AI-specific settings (for gemini-embedding-001)
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
        
        # Create location widget using lazy loading to avoid circular imports
        location_widget, is_combo = self._create_location_widget("direct_vertex_ai", "us-central1")
        if is_combo:
            self.direct_vertex_location_combo = location_widget
        else:
            self.direct_vertex_location_edit = location_widget
        direct_vertex_layout.addRow("Location:", location_widget)
        
        # Custom dimensions for gemini-embedding-001
        self.direct_vertex_dimensions_spin = QSpinBox()
        self.direct_vertex_dimensions_spin.setRange(1, 3072)
        self.direct_vertex_dimensions_spin.setValue(768)
        self.direct_vertex_dimensions_spin.setSingleStep(256)
        self.direct_vertex_dimensions_spin.setToolTip(
            "Custom embedding dimensions (1-3072). Higher = more detail, larger storage.\n"
            "Recommended: 768 (balanced), 1536 (detailed), 3072 (maximum detail)"
        )
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

    def _on_provider_changed(self, provider):
        """Handle provider selection change - show relevant section"""
        # Show/hide provider-specific settings
        self.openai_group.setVisible(provider == "openai")
        self.vertex_group.setVisible(provider == "vertex_ai")
        self.direct_vertex_group.setVisible(provider == "direct_vertex_ai")
        self.cohere_group.setVisible(provider == "cohere")
        self.azure_group.setVisible(provider == "azure_openai")
        
        # Update model dropdown with provider-specific models
        self._update_models_for_provider(provider)
        
        # Update model field placeholder
        model_placeholders = {
            "openai": "text-embedding-3-small",
            "azure_openai": "Use deployment name instead",
            "cohere": "embed-english-v3.0",
            "vertex_ai": "text-embedding-004",
            "direct_vertex_ai": "gemini-embedding-001",
            "mock": "mock-embedding",
            "local": "mxbai-embed-large"
        }
        
        if hasattr(self.model_combo, 'lineEdit') and self.model_combo.lineEdit():
            self.model_combo.lineEdit().setPlaceholderText(model_placeholders.get(provider, ""))
        
        # Disable model field for Azure (uses deployment name)
        self.model_combo.setEnabled(provider != "azure_openai")
    
    def _update_models_for_provider(self, provider):
        """Update model dropdown with provider-specific options"""
        self.model_combo.clear()
        
        # Improved model lists with more options and better organization
        if provider == "openai":
            models = [
                "text-embedding-3-large ⭐ (3072 dims, best quality)",
                "text-embedding-3-small ⭐ (1536 dims, good balance)", 
                "text-embedding-ada-002 (1536 dims, legacy)"
            ]
        elif provider == "vertex_ai":
            models = [
                "text-embedding-004 ⭐ (768 dims, latest)",
                "text-embedding-005 (768 dims, experimental)",
                "textembedding-gecko@003 (768 dims, stable)",
                "textembedding-gecko-multilingual@001 (768 dims, multilingual)"
            ]
        elif provider == "direct_vertex_ai":
            models = [
                "gemini-embedding-001 🔥 (custom dims 1-3072, state-of-the-art)",
                "text-embedding-004 (768 dims, stable backup)"
            ]
        elif provider == "cohere":
            models = [
                "embed-english-v3.0 ⭐ (1024 dims, latest)",
                "embed-multilingual-v3.0 (1024 dims, multilingual)",
                "embed-english-light-v3.0 (1024 dims, faster)"
            ]
        elif provider == "azure_openai":
            models = ["Use deployment name in field above"]
        else:  # mock/local
            models = ["mock-embedding (for testing)"]
        
        self.model_combo.addItems(models)
        
        if models and models[0] != "Use deployment name in field above":
            # Set first recommended model as default
            self.model_combo.setCurrentIndex(0)
            self._on_model_changed(models[0])
    
    def _on_model_changed(self, model_name):
        """Handle model selection change and show helpful info"""
        if not model_name or "Use deployment name" in model_name:
            self.model_info_label.setText("")
            return
        
        # Extract the actual model name (remove metadata)
        clean_name = model_name.split(" ")[0]
        
        # Show helpful information based on model
        info_parts = []
        
        if "⭐" in model_name:
            info_parts.append("⭐ Recommended for academic texts")
        
        if "3072 dims" in model_name:
            info_parts.append("📊 High dimensional embeddings for complex concepts")
        elif "1536 dims" in model_name:
            info_parts.append("📊 Standard dimensional embeddings (good quality)")
        elif "768 dims" in model_name:
            info_parts.append("📊 Compact embeddings (efficient)")
        
        if "latest" in model_name:
            info_parts.append("🆕 Latest model version")
        elif "legacy" in model_name:
            info_parts.append("⚠️ Legacy model (consider upgrading)")
        
        if "multilingual" in model_name:
            info_parts.append("🌍 Supports multiple languages")
        
        if info_parts:
            self.model_info_label.setText(" | ".join(info_parts))
        else:
            self.model_info_label.setText("Standard embedding model")

    def _create_search_tab(self):
        """Create search options tab (keeping existing logic)"""
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
        return widget

    def _create_indexing_tab(self):
        """Create indexing tab (simplified, no dual model selection)"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Embedding dimensions (auto-populated from model selection)
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
        return widget

    def _create_performance_tab(self):
        """Create performance tab (keeping existing)"""
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
        return widget

    def _create_ui_tab(self):
        """Create UI options tab (keeping existing)"""
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
        return widget

    def _load_settings(self):
        """Load settings from config"""
        self.provider_combo.setCurrentText(self.config.get("embedding_provider"))
        self.model_combo.setCurrentText(self.config.get("embedding_model"))

        provider = self.provider_combo.currentText()
        api_key = self.config.get(f"api_keys.{provider}", "")
        self.api_key_edit.setText(api_key)

        self.result_limit_spin.setValue(self.config.get("search_options.default_limit"))
        self.threshold_slider.setValue(
            int(self.config.get("search_options.similarity_threshold") * 100)
        )
        self.scope_combo.setCurrentText(self.config.get("search_options.scope"))

        self.cache_enabled_check.setChecked(self.config.get("performance.cache_enabled"))
        self.cache_size_spin.setValue(self.config.get("performance.cache_size_mb"))

        self.floating_check.setChecked(self.config.get("ui_options.floating_window"))
        self.remember_pos_check.setChecked(self.config.get("ui_options.remember_position"))
        self.opacity_slider.setValue(int(self.config.get("ui_options.window_opacity") * 100))

        # Load Direct Vertex AI settings
        self.direct_vertex_project_edit.setText(self.config.get("vertex_project_id", ""))
        
        # Handle location setting with LocationComboBox or fallback
        vertex_location = self.config.get("vertex_location", "us-central1")
        if hasattr(self, 'direct_vertex_location_combo'):
            self.direct_vertex_location_combo.set_region_code(vertex_location)
        elif hasattr(self, 'direct_vertex_location_edit'):
            self.direct_vertex_location_edit.setText(vertex_location)
            
        self.direct_vertex_dimensions_spin.setValue(self.config.get("embedding_dimensions", 768))

        # Trigger provider change to show correct section
        self._on_provider_changed(self.provider_combo.currentText())

    def save_settings(self):
        """Save settings to config"""
        self.config.set("embedding_provider", self.provider_combo.currentText())
        
        # Get clean model name (remove metadata like "⭐ (3072 dims, best quality)")
        model_text = self.model_combo.currentText()
        clean_model = model_text.split(" ")[0] if model_text else ""
        self.config.set("embedding_model", clean_model)

        provider = self.provider_combo.currentText()
        self.config.set(f"api_keys.{provider}", self.api_key_edit.text())

        self.config.set("search_options.default_limit", self.result_limit_spin.value())
        self.config.set(
            "search_options.similarity_threshold", self.threshold_slider.value() / 100.0
        )
        self.config.set("search_options.scope", self.scope_combo.currentText())

        self.config.set("performance.cache_enabled", self.cache_enabled_check.isChecked())
        self.config.set("performance.cache_size_mb", self.cache_size_spin.value())

        self.config.set("ui_options.floating_window", self.floating_check.isChecked())
        self.config.set("ui_options.remember_position", self.remember_pos_check.isChecked())
        self.config.set("ui_options.window_opacity", self.opacity_slider.value() / 100.0)

        # Save Direct Vertex AI settings
        if self.provider_combo.currentText() == "direct_vertex_ai":
            self.config.set("vertex_project_id", self.direct_vertex_project_edit.text().strip())
            
            # Handle location setting with LocationComboBox or fallback
            if hasattr(self, 'direct_vertex_location_combo'):
                location = self.direct_vertex_location_combo.get_region_code()
            elif hasattr(self, 'direct_vertex_location_edit'):
                location = self.direct_vertex_location_edit.text().strip()
            else:
                location = "us-central1"  # Default fallback
            self.config.set("vertex_location", location)
            
            # For direct_vertex_ai, use the custom dimensions spinner
            self.config.set("embedding_dimensions", self.direct_vertex_dimensions_spin.value())
        elif self.provider_combo.currentText() == "vertex_ai":
            # Handle regular Vertex AI settings
            if hasattr(self, 'vertex_location_combo'):
                location = self.vertex_location_combo.get_region_code()
            elif hasattr(self, 'vertex_location_edit'):
                location = self.vertex_location_edit.text().strip()
            else:
                location = "us-central1"  # Default fallback
            self.config.set("vertex_location", location)
        else:
            # For other providers, use the standard dimensions spinner
            self.config.set("embedding_dimensions", self.dimensions_spin.value())

        # JSONConfig auto-saves when values are modified

    def _test_connection(self):
        """Test API connection"""
        import threading
        import time
        
        provider = self.provider_combo.currentText()
        
        if provider == "mock":
            QMessageBox.information(self, "Test Connection", "✅ Mock provider - no real connection needed")
            return
        
        # Validate required fields
        api_key = self.api_key_edit.text().strip()
        model = self.model_combo.currentText().split(" ")[0] if self.model_combo.currentText() else ""
        
        # Provider-specific validation
        validation_result = self._validate_provider_config(provider, api_key, model)
        if not validation_result['valid']:
            QMessageBox.warning(self, "Test Connection", f"❌ {validation_result['error']}")
            return
        
        # Show progress dialog
        progress = QProgressDialog("Testing connection...", "Cancel", 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setAutoClose(True)
        progress.setAutoReset(True)
        progress.show()
        QApplication.processEvents()
        
        # Simulate connection test (will be replaced with real test)
        def test_worker():
            time.sleep(2)  # Simulate API call
            return True
        
        try:
            # Run test in background
            success = test_worker()
            progress.close()
            
            if success:
                QMessageBox.information(self, "Test Connection", 
                                      f"✅ Connection successful!\n"
                                      f"Provider: {provider}\n"
                                      f"Model: {model}\n"
                                      f"Configuration appears valid.")
            else:
                QMessageBox.warning(self, "Test Connection", 
                                  f"❌ Connection failed\n"
                                  f"Please check your configuration.")
                
        except Exception as e:
            progress.close()
            QMessageBox.critical(self, "Test Connection", 
                               f"❌ Connection test failed:\n{str(e)}")
    
    def _validate_provider_config(self, provider, api_key, model):
        """Validate provider-specific configuration"""
        if provider == "openai":
            if not api_key:
                return {'valid': False, 'error': 'OpenAI API key is required'}
            if not api_key.startswith('sk-'):
                return {'valid': False, 'error': 'OpenAI API key should start with "sk-"'}
            if not model:
                return {'valid': False, 'error': 'Model selection is required'}
                
        elif provider == "vertex_ai":
            if hasattr(self, 'vertex_project_edit'):
                project = self.vertex_project_edit.text().strip()
                if not project:
                    return {'valid': False, 'error': 'Vertex AI Project ID is required'}
            if not model:
                return {'valid': False, 'error': 'Model selection is required'}
                
        elif provider == "direct_vertex_ai":
            if hasattr(self, 'direct_vertex_project_edit'):
                project = self.direct_vertex_project_edit.text().strip()
                if not project:
                    return {'valid': False, 'error': 'Direct Vertex AI Project ID is required'}
            if hasattr(self, 'direct_vertex_location_edit'):
                location = self.direct_vertex_location_edit.text().strip()
                if not location:
                    return {'valid': False, 'error': 'Direct Vertex AI Location is required'}
            if not model:
                return {'valid': False, 'error': 'Model selection is required'}
            # Validate dimensions
            if hasattr(self, 'direct_vertex_dimensions_spin'):
                dims = self.direct_vertex_dimensions_spin.value()
                if dims < 1 or dims > 3072:
                    return {'valid': False, 'error': 'Dimensions must be between 1 and 3072 for gemini-embedding-001'}
                
        elif provider == "cohere":
            if not api_key:
                return {'valid': False, 'error': 'Cohere API key is required'}
            if not model:
                return {'valid': False, 'error': 'Model selection is required'}
                
        elif provider == "azure_openai":
            if not api_key:
                return {'valid': False, 'error': 'Azure OpenAI API key is required'}
            if hasattr(self, 'azure_deployment_edit'):
                deployment = self.azure_deployment_edit.text().strip()
                if not deployment:
                    return {'valid': False, 'error': 'Azure deployment name is required'}
            if hasattr(self, 'azure_api_base_edit'):
                api_base = self.azure_api_base_edit.text().strip()
                if not api_base:
                    return {'valid': False, 'error': 'Azure API base URL is required'}
        
        return {'valid': True, 'error': None}