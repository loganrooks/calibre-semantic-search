"""
Base embedding provider interface
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any


class BaseEmbeddingProvider(ABC):
    """Base class for all embedding providers"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize provider with configuration"""
        self.config = config
    
    @abstractmethod
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        pass
    
    @abstractmethod
    async def generate_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        pass
    
    @abstractmethod
    def get_dimensions(self) -> int:
        """Get the dimension count of embeddings"""
        pass
    
    def get_max_batch_size(self) -> int:
        """Get maximum batch size for this provider"""
        return 32
    
    def get_max_text_length(self) -> int:
        """Get maximum text length for this provider"""
        return 8192