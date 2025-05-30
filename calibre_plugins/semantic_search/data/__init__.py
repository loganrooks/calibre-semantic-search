"""
Data access layer for semantic search
"""

from .cache import CacheManager
from .database import SemanticSearchDB
from .repositories import CalibreRepository, EmbeddingRepository

__all__ = [
    "SemanticSearchDB",
    "EmbeddingRepository",
    "CalibreRepository",
    "CacheManager",
]
