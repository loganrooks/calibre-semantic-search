"""
Index detection and status management for UI components
"""

from typing import Dict, List, Any, Optional


class IndexDetector:
    """Detects and provides status information about book indexes"""
    
    def __init__(self, embedding_repo=None):
        """
        Initialize index detector
        
        Args:
            embedding_repo: EmbeddingRepository instance (optional)
        """
        self.embedding_repo = embedding_repo
    
    def _get_repository(self):
        """Get or create embedding repository"""
        if self.embedding_repo:
            return self.embedding_repo
        
        # For testing, return None - tests will mock this
        return None
    
    def get_index_status(self, book_ids: List[int]) -> Dict[int, Dict[str, Any]]:
        """
        Get index status for multiple books
        
        Args:
            book_ids: List of book IDs to check
            
        Returns:
            Dict mapping book_id to status dict with keys:
            - has_index: bool
            - index_count: int  
            - providers: List[str]
        """
        repo = self._get_repository()
        status = {}
        
        for book_id in book_ids:
            if repo:
                try:
                    indexes = repo.get_indexes_for_book(book_id)
                    providers = [idx.get('provider', 'unknown') for idx in indexes]
                    
                    status[book_id] = {
                        'has_index': len(indexes) > 0,
                        'index_count': len(indexes),
                        'providers': providers
                    }
                except Exception:
                    # Fallback if repo call fails
                    status[book_id] = {
                        'has_index': False,
                        'index_count': 0,
                        'providers': []
                    }
            else:
                # No repo available (e.g., testing)
                status[book_id] = {
                    'has_index': False,
                    'index_count': 0,
                    'providers': []
                }
        
        return status
    
    def format_status_for_display(self, status: Dict[str, Any]) -> str:
        """
        Format index status for UI display
        
        Args:
            status: Status dict with has_index, index_count, providers
            
        Returns:
            Formatted string for display
        """
        if not status.get('has_index', False):
            return 'No indexes'
        
        count = status.get('index_count', 0)
        providers = status.get('providers', [])
        
        if count == 1:
            if providers:
                provider_name = self._format_provider_name(providers[0])
                return f'1 index ({provider_name})'
            else:
                return '1 index'
        else:
            if providers:
                provider_names = [self._format_provider_name(p) for p in providers]
                provider_str = ', '.join(provider_names)
                return f'{count} indexes ({provider_str})'
            else:
                return f'{count} indexes'
    
    def get_status_icon(self, status: Dict[str, Any]) -> str:
        """
        Get appropriate icon for index status
        
        Args:
            status: Status dict with has_index, index_count
            
        Returns:
            Icon name or identifier
        """
        if not status.get('has_index', False):
            return 'warning'
        
        count = status.get('index_count', 0)
        if count > 1:
            return 'multi-check'
        else:
            return 'check'
    
    def _format_provider_name(self, provider: str) -> str:
        """
        Format provider name for display
        
        Args:
            provider: Provider name (e.g., 'openai', 'vertex')
            
        Returns:
            Formatted provider name (e.g., 'OpenAI', 'Vertex')
        """
        provider_mapping = {
            'openai': 'OpenAI',
            'vertex': 'Vertex',
            'cohere': 'Cohere',
            'azure': 'Azure',
            'huggingface': 'HuggingFace',
            'default': 'Default',
            'mock': 'Mock'
        }
        
        return provider_mapping.get(provider.lower(), provider.title())