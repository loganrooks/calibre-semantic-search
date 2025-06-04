"""
Plugin system for embedding providers
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Type
import logging

from .base import BaseEmbeddingProvider

logger = logging.getLogger(__name__)


@dataclass
class ProviderInfo:
    """Information about an embedding provider plugin"""
    name: str
    display_name: str
    description: str
    version: str
    supported_models: List[str]
    default_dimensions: int
    requires_api_key: bool
    config_schema: Dict[str, Any]
    
    def __post_init__(self):
        """Validate provider info after initialization"""
        if not self.name:
            raise ValueError("Provider name cannot be empty")
        if not self.supported_models:
            raise ValueError("Provider must support at least one model")
        if self.default_dimensions <= 0:
            raise ValueError("Default dimensions must be positive")


class EmbeddingProviderPlugin(ABC):
    """Base class for embedding provider plugins"""
    
    @abstractmethod
    def get_provider_info(self) -> ProviderInfo:
        """Get information about this provider"""
        pass
    
    @abstractmethod
    def create_provider(self, config: Dict[str, Any]) -> BaseEmbeddingProvider:
        """Create an instance of the provider with given config"""
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate provider configuration"""
        pass
    
    def get_config_ui_schema(self) -> Optional[Dict[str, Any]]:
        """Get UI schema for configuration (optional)"""
        return None


class PluginManager:
    """Manages embedding provider plugins"""
    
    def __init__(self):
        self._plugins: Dict[str, EmbeddingProviderPlugin] = {}
        self._provider_infos: Dict[str, ProviderInfo] = {}
        self._discovered_plugins: Dict[str, Any] = {}
        self._loaded_plugins: Dict[str, Any] = {}
        
    def register_plugin(self, plugin: EmbeddingProviderPlugin) -> None:
        """Register a new provider plugin"""
        try:
            provider_info = plugin.get_provider_info()
            
            if provider_info.name in self._plugins:
                logger.warning(f"Provider {provider_info.name} already registered, overwriting")
            
            self._plugins[provider_info.name] = plugin
            self._provider_infos[provider_info.name] = provider_info
            
            logger.info(f"Registered provider plugin: {provider_info.display_name} v{provider_info.version}")
            
        except Exception as e:
            logger.error(f"Failed to register plugin: {e}")
            raise
    
    def unregister_plugin(self, name: str) -> bool:
        """Unregister a provider plugin"""
        if name in self._plugins:
            del self._plugins[name]
            del self._provider_infos[name]
            logger.info(f"Unregistered provider plugin: {name}")
            return True
        return False
    
    def get_available_providers(self) -> List[str]:
        """Get all available provider plugins"""
        return list(self._loaded_plugins.keys())
    
    def get_provider_info(self, name: str) -> Optional[ProviderInfo]:
        """Get information about a specific provider"""
        # First try the provider_infos cache
        if name in self._provider_infos:
            return self._provider_infos[name]
        
        # If not cached, try to get from loaded plugin
        plugin = self._loaded_plugins.get(name)
        if plugin and hasattr(plugin, 'get_provider_info'):
            return plugin.get_provider_info()
        
        return None
    
    def create_provider(self, name: str, config: Dict[str, Any]) -> Optional[BaseEmbeddingProvider]:
        """Create a provider instance"""
        # Try both _plugins and _loaded_plugins
        plugin = self._plugins.get(name) or self._loaded_plugins.get(name)
        if not plugin:
            logger.error(f"Provider plugin not found: {name}")
            return None
            
        try:
            # Validate configuration
            if not plugin.validate_config(config):
                logger.error(f"Invalid configuration for provider: {name}")
                return None
            
            # Create provider instance
            provider = plugin.create_provider(config)
            logger.info(f"Created provider instance: {name}")
            return provider
            
        except Exception as e:
            logger.error(f"Failed to create provider {name}: {e}")
            return None
    
    def validate_provider_config(self, name: str, config: Dict[str, Any]) -> bool:
        """Validate configuration for a provider"""
        # Try both _plugins and _loaded_plugins
        plugin = self._plugins.get(name) or self._loaded_plugins.get(name)
        if not plugin:
            return False
        
        try:
            return plugin.validate_config(config)
        except Exception as e:
            logger.error(f"Error validating config for {name}: {e}")
            return False
    
    def is_provider_available(self, name: str) -> bool:
        """Check if a provider is available"""
        return name in self._plugins
    
    def get_supported_models(self, name: str) -> List[str]:
        """Get supported models for a provider"""
        provider_info = self._provider_infos.get(name)
        return provider_info.supported_models if provider_info else []
    
    def discover_plugins(self, plugin_directories: Optional[List[str]] = None) -> List[str]:
        """Discover and load plugins from directories"""
        if plugin_directories is None:
            # Default to looking in current directory
            plugin_directories = ["."]
        
        discovered = []
        
        for directory in plugin_directories:
            try:
                discovered.extend(self._load_plugins_from_directory(directory))
            except Exception as e:
                logger.error(f"Error discovering plugins in {directory}: {e}")
        
        return discovered
    
    def load_plugin(self, name: str, plugin_class: Type[EmbeddingProviderPlugin]) -> bool:
        """Load a specific plugin class"""
        try:
            plugin_instance = plugin_class()
            self.register_plugin(plugin_instance)
            self._loaded_plugins[name] = plugin_instance
            return True
        except Exception as e:
            logger.error(f"Failed to load plugin {name}: {e}")
            return False
    
    def _load_plugins_from_directory(self, directory: str) -> List[str]:
        """Load plugins from a specific directory"""
        # This would implement plugin discovery from filesystem
        try:
            from pathlib import Path
            plugin_files = list(Path(directory).glob("*_plugin.py"))
            return [str(p.name) for p in plugin_files]
        except Exception as e:
            logger.error(f"Error scanning directory {directory}: {e}")
            return []


# Global plugin manager instance
plugin_manager = PluginManager()


def get_plugin_manager() -> PluginManager:
    """Get the global plugin manager instance"""
    return plugin_manager