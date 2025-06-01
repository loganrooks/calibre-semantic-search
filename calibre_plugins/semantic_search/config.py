"""
Configuration management for Semantic Search plugin
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

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
        self.provider_combo.addItems(["mock", "openai", "vertex_ai", "cohere", "local"])
        self.provider_combo.setToolTip(
            "Choose the AI service that will analyze your text during indexing.\n"
            "Mock = Free testing mode (no real AI)\n"
            "OpenAI = GPT embeddings (requires API key)\n"
            "Vertex AI = Google Cloud (requires setup)\n"
            "Cohere = Cohere AI (requires API key)\n"
            "Local = Ollama (coming soon)"
        )
        provider_layout.addRow("Provider:", self.provider_combo)

        # Model selection
        self.model_edit = QLineEdit()
        provider_layout.addRow("Model:", self.model_edit)

        # API Key
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        provider_layout.addRow("API Key:", self.api_key_edit)

        # Test connection button
        test_btn = QPushButton("Test Connection")
        test_btn.clicked.connect(self._test_connection)
        provider_layout.addRow("", test_btn)

        layout.addWidget(provider_group)
        layout.addStretch()

        return widget

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
        
        # Text Processing Settings
        process_group = QGroupBox("Text Processing")
        process_layout = QFormLayout()
        process_group.setLayout(process_layout)
        
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
        self.model_edit.setText(self.config.get("embedding_model"))

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

    def save_settings(self):
        """Save settings to config"""
        # API settings
        self.config.set("embedding_provider", self.provider_combo.currentText())
        self.config.set("embedding_model", self.model_edit.text())

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

        # Save to disk
        self.config.save()

    def _test_connection(self):
        """Test API connection"""
        from PyQt5.Qt import QMessageBox
        import asyncio
        
        try:
            # Get the plugin instance through the parent chain
            # ConfigWidget -> ConfigDialog -> plugin
            plugin = None
            parent = self.parent()
            while parent and not plugin:
                if hasattr(parent, 'plugin'):
                    plugin = parent.plugin
                    break
                parent = parent.parent()
            
            if not plugin:
                QMessageBox.critical(
                    self,
                    "Test Connection",
                    "Unable to access plugin instance."
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
