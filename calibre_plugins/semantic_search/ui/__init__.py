"""
User interface components for semantic search
"""

from .search_dialog import SemanticSearchDialog
from .widgets import SimilaritySlider, ResultCard, ScopeSelector
from .viewer_integration import ViewerIntegration

__all__ = ['SemanticSearchDialog', 'SimilaritySlider', 'ResultCard', 
           'ScopeSelector', 'ViewerIntegration']