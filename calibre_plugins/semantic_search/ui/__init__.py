"""
User interface components for semantic search
"""

from .search_dialog import SemanticSearchDialog
from .viewer_integration import ViewerIntegration
from .widgets import ResultCard, ScopeSelector, SimilaritySlider

__all__ = [
    "SemanticSearchDialog",
    "SimilaritySlider",
    "ResultCard",
    "ScopeSelector",
    "ViewerIntegration",
]
