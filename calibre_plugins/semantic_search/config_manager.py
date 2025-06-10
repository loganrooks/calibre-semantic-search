"""
Configuration management for Semantic Search plugin
Separated to avoid circular imports with MVP pattern
"""

from pathlib import Path
from typing import Any, Dict, Optional

from calibre.utils.config import JSONConfig

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