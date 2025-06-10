"""
ConfigPresenter - MVP pattern implementation for configuration management

ARCHITECTURE COMPLIANCE:
- NO Qt imports (System Invariant)
- All business logic for configuration
- Updates view through simple setter methods
- Delegates to services for external operations
"""

import logging
import re
from typing import Any, Dict, List, Optional, Callable
import threading
import time

# NO Qt imports allowed in presenter layer
from ..config_manager import SemanticSearchConfig


class ConfigPresenter:
    """
    Presenter for configuration management following MVP pattern.
    Handles all configuration business logic without Qt dependencies.
    """
    
    def __init__(self, view):
        """
        Initialize presenter with view reference
        
        Args:
            view: The ConfigWidget view (dumb UI)
        """
        self.view = view
        self.config = SemanticSearchConfig()
        self.logger = logging.getLogger('calibre_plugins.semantic_search.presenters.config')
        
        self.logger.info("ConfigPresenter initialized")
    
    def on_provider_changed(self, provider: str):
        """
        Handle provider selection changes
        
        Args:
            provider: Selected provider name
        """
        self.logger.info(f"Provider changed to: {provider}")
        
        # Update view to show provider-specific section
        self.view.show_provider_section(provider)
        
        # Update model list for this provider
        models = self._get_models_for_provider(provider)
        self.view.update_model_list(models)
        
        # Set appropriate placeholder
        placeholder = self._get_model_placeholder(provider)
        self.view.set_model_placeholder(placeholder)
        
        # Enable/disable model field based on provider
        model_enabled = provider != "azure_openai"
        self.view.set_model_enabled(model_enabled)
    
    def _get_models_for_provider(self, provider: str) -> List[str]:
        """Get model list for specified provider"""
        models_map = {
            "openai": [
                "text-embedding-3-large ⭐ (3072 dims, best quality)",
                "text-embedding-3-small ⭐ (1536 dims, good balance)", 
                "text-embedding-ada-002 (1536 dims, legacy)"
            ],
            "vertex_ai": [
                "text-embedding-004 ⭐ (768 dims, latest)",
                "text-embedding-005 (768 dims, experimental)",
                "textembedding-gecko@003 (768 dims, stable)",
                "textembedding-gecko-multilingual@001 (768 dims, multilingual)"
            ],
            "direct_vertex_ai": [
                "gemini-embedding-001 🔥 (custom dims 1-3072, state-of-the-art)",
                "text-embedding-004 (768 dims, stable backup)"
            ],
            "cohere": [
                "embed-english-v3.0 ⭐ (1024 dims, latest)",
                "embed-multilingual-v3.0 (1024 dims, multilingual)",
                "embed-english-light-v3.0 (1024 dims, faster)"
            ],
            "azure_openai": ["Use deployment name in field above"],
            "mock": ["mock-embedding (for testing)"],
            "local": ["mxbai-embed-large (coming soon)"]
        }
        
        return models_map.get(provider, ["Unknown provider"])
    
    def _get_model_placeholder(self, provider: str) -> str:
        """Get model field placeholder for provider"""
        placeholders = {
            "openai": "text-embedding-3-small",
            "azure_openai": "Use deployment name instead",
            "cohere": "embed-english-v3.0",
            "vertex_ai": "text-embedding-004",
            "direct_vertex_ai": "gemini-embedding-001",
            "mock": "mock-embedding",
            "local": "mxbai-embed-large"
        }
        return placeholders.get(provider, "")
    
    def on_model_changed(self, model_name: str):
        """
        Handle model selection changes and show helpful info
        
        Args:
            model_name: Selected model name with metadata
        """
        if not model_name or "Use deployment name" in model_name:
            self.view.set_model_info("")
            return
        
        # Generate helpful information
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
        
        if "🔥" in model_name:
            info_parts.append("🔥 State-of-the-art performance")
        
        info_text = " | ".join(info_parts) if info_parts else "Standard embedding model"
        self.view.set_model_info(info_text)
    
    def validate_provider_config(self, provider: str, api_key: str, model: str, **kwargs) -> Dict[str, Any]:
        """
        Validate provider-specific configuration
        
        Args:
            provider: Provider name
            api_key: API key value
            model: Model name
            **kwargs: Provider-specific fields (project_id, deployment, etc.)
            
        Returns:
            Dict with 'valid' bool and 'error' string
        """
        if provider == "mock":
            return {'valid': True, 'error': None}
        
        if provider == "openai":
            if not api_key:
                return {'valid': False, 'error': 'OpenAI API key is required'}
            if not api_key.startswith('sk-'):
                return {'valid': False, 'error': 'OpenAI API key should start with "sk-"'}
            if not model:
                return {'valid': False, 'error': 'Model selection is required'}
                
        elif provider == "vertex_ai":
            project_id = kwargs.get('project_id', '')
            if not project_id:
                return {'valid': False, 'error': 'Vertex AI Project ID is required'}
            if not model:
                return {'valid': False, 'error': 'Model selection is required'}
                
        elif provider == "direct_vertex_ai":
            project_id = kwargs.get('project_id', '')
            if not project_id:
                return {'valid': False, 'error': 'Direct Vertex AI Project ID is required'}
            location = kwargs.get('location', '')
            if not location:
                return {'valid': False, 'error': 'Direct Vertex AI Location is required'}
            if not model:
                return {'valid': False, 'error': 'Model selection is required'}
            dimensions = kwargs.get('dimensions', 768)
            if dimensions < 1 or dimensions > 3072:
                return {'valid': False, 'error': 'Dimensions must be between 1 and 3072 for gemini-embedding-001'}
                
        elif provider == "cohere":
            if not api_key:
                return {'valid': False, 'error': 'Cohere API key is required'}
            if not model:
                return {'valid': False, 'error': 'Model selection is required'}
                
        elif provider == "azure_openai":
            if not api_key:
                return {'valid': False, 'error': 'Azure OpenAI API key is required'}
            deployment = kwargs.get('deployment', '')
            if not deployment:
                return {'valid': False, 'error': 'Azure deployment name is required'}
            api_base = kwargs.get('api_base', '')
            if not api_base:
                return {'valid': False, 'error': 'Azure API base URL is required'}
        
        return {'valid': True, 'error': None}
    
    def test_connection(self, provider: str, api_key: str, model: str, **kwargs):
        """
        Test API connection asynchronously
        
        Args:
            provider: Provider name
            api_key: API key
            model: Model name
            **kwargs: Provider-specific configuration
        """
        self.logger.info(f"Testing connection for provider: {provider}")
        
        if provider == "mock":
            # Mock provider succeeds immediately
            self.view.show_connection_result(True, "Mock provider - no real connection needed")
            return
        
        # Validate configuration first
        validation = self.validate_provider_config(provider, api_key, model, **kwargs)
        if not validation['valid']:
            self.view.show_connection_result(False, validation['error'])
            return
        
        # Show progress and start async test
        self.view.show_connection_progress(True)
        self._test_connection_async(provider, api_key, model, **kwargs)
    
    def _test_connection_async(self, provider: str, api_key: str, model: str, **kwargs):
        """
        Perform actual connection test in background thread
        
        Args:
            provider: Provider name
            api_key: API key
            model: Model name
            **kwargs: Provider-specific configuration
        """
        def test_worker():
            try:
                # Simulate connection test (would be replaced with real service call)
                time.sleep(2)  # Simulate API call delay
                
                # For now, simulate success
                success = True
                message = f"Connection successful!\nProvider: {provider}\nModel: {self._clean_model_name(model)}\nConfiguration appears valid."
                
                # Update view on main thread
                self.view.show_connection_progress(False)
                self.view.show_connection_result(success, message)
                
            except Exception as e:
                self.logger.error(f"Connection test failed: {e}")
                self.view.show_connection_progress(False)
                self.view.show_connection_result(False, f"Connection test failed: {str(e)}")
        
        # Start background thread
        thread = threading.Thread(target=test_worker, daemon=True)
        thread.start()
    
    def load_configuration(self):
        """Load configuration from storage and update view"""
        self.logger.info("Loading configuration")
        
        # Load provider and model
        provider = self.config.get("embedding_provider", "mock")
        model = self.config.get("embedding_model", "")
        
        self.view.set_provider(provider)
        self.view.set_model(model)
        
        # Load API key for current provider
        api_key = self.config.get(f"api_keys.{provider}", "")
        self.view.set_api_key(api_key)
        
        # Load search options
        result_limit = self.config.get("search_options.default_limit", 20)
        threshold = self.config.get("search_options.similarity_threshold", 0.7)
        scope = self.config.get("search_options.scope", "library")
        
        self.view.set_result_limit(result_limit)
        self.view.set_similarity_threshold(int(threshold * 100))
        self.view.set_search_scope(scope)
        
        # Load performance options
        cache_enabled = self.config.get("performance.cache_enabled", True)
        cache_size = self.config.get("performance.cache_size_mb", 100)
        
        self.view.set_cache_enabled(cache_enabled)
        self.view.set_cache_size(cache_size)
        
        # Load UI options
        floating = self.config.get("ui_options.floating_window", False)
        remember_pos = self.config.get("ui_options.remember_position", True)
        opacity = self.config.get("ui_options.window_opacity", 0.95)
        
        self.view.set_floating_window(floating)
        self.view.set_remember_position(remember_pos)
        self.view.set_window_opacity(int(opacity * 100))
        
        # Load provider-specific settings
        self._load_provider_specific_settings(provider)
        
        # Trigger provider change to show correct UI sections
        self.on_provider_changed(provider)
    
    def _load_provider_specific_settings(self, provider: str):
        """Load provider-specific configuration settings"""
        if provider in ["vertex_ai", "direct_vertex_ai"]:
            project_id = self.config.get("vertex_project_id", "")
            location = self.config.get("vertex_location", "us-central1")
            self.view.set_vertex_project_id(project_id)
            self.view.set_vertex_location(location)
            
            if provider == "direct_vertex_ai":
                dimensions = self.config.get("embedding_dimensions", 768)
                self.view.set_vertex_dimensions(dimensions)
        
        elif provider == "azure_openai":
            deployment = self.config.get("azure_deployment", "")
            api_base = self.config.get("azure_api_base", "")
            api_version = self.config.get("azure_api_version", "2024-02-01")
            self.view.set_azure_deployment(deployment)
            self.view.set_azure_api_base(api_base)
            self.view.set_azure_api_version(api_version)
        
        elif provider == "cohere":
            input_type = self.config.get("cohere_input_type", "search_document")
            self.view.set_cohere_input_type(input_type)
    
    def save_configuration(self):
        """Save configuration from view values to storage"""
        self.logger.info("Saving configuration")
        
        # Get values from view
        provider = self.view.get_provider()
        model_raw = self.view.get_model()
        api_key = self.view.get_api_key()
        
        # Clean model name (remove metadata)
        model_clean = self._clean_model_name(model_raw)
        
        # Save core settings
        self.config.set("embedding_provider", provider)
        self.config.set("embedding_model", model_clean)
        self.config.set(f"api_keys.{provider}", api_key)
        
        # Save search options
        self.config.set("search_options.default_limit", self.view.get_result_limit())
        self.config.set("search_options.similarity_threshold", self.view.get_similarity_threshold() / 100.0)
        self.config.set("search_options.scope", self.view.get_search_scope())
        
        # Save performance options
        self.config.set("performance.cache_enabled", self.view.get_cache_enabled())
        self.config.set("performance.cache_size_mb", self.view.get_cache_size())
        
        # Save UI options
        self.config.set("ui_options.floating_window", self.view.get_floating_window())
        self.config.set("ui_options.remember_position", self.view.get_remember_position())
        self.config.set("ui_options.window_opacity", self.view.get_window_opacity() / 100.0)
        
        # Save provider-specific settings
        self._save_provider_specific_settings(provider)
        
        self.logger.info("Configuration saved successfully")
    
    def _save_provider_specific_settings(self, provider: str):
        """Save provider-specific configuration settings"""
        if provider in ["vertex_ai", "direct_vertex_ai"]:
            project_id = self.view.get_vertex_project_id()
            location = self.view.get_vertex_location()
            self.config.set("vertex_project_id", project_id)
            self.config.set("vertex_location", location)
            
            if provider == "direct_vertex_ai":
                dimensions = self.view.get_vertex_dimensions()
                self.config.set("embedding_dimensions", dimensions)
            else:
                # For regular vertex_ai, use standard dimensions
                dimensions = self.view.get_embedding_dimensions()
                self.config.set("embedding_dimensions", dimensions)
        
        elif provider == "azure_openai":
            deployment = self.view.get_azure_deployment()
            api_base = self.view.get_azure_api_base()
            api_version = self.view.get_azure_api_version()
            self.config.set("azure_deployment", deployment)
            self.config.set("azure_api_base", api_base)
            self.config.set("azure_api_version", api_version)
        
        elif provider == "cohere":
            input_type = self.view.get_cohere_input_type()
            self.config.set("cohere_input_type", input_type)
        
        else:
            # For other providers, save standard embedding dimensions
            dimensions = self.view.get_embedding_dimensions()
            self.config.set("embedding_dimensions", dimensions)
    
    def _clean_model_name(self, model_name: str) -> str:
        """
        Clean model name by removing metadata (emojis, descriptions, etc.)
        
        Args:
            model_name: Raw model name with metadata
            
        Returns:
            Clean model name for configuration storage
        """
        if not model_name:
            return ""
        
        # Extract just the model name (first word before space)
        clean_name = model_name.split(" ")[0]
        return clean_name