"""
Embedding service with multiple provider support and fallback
"""

import asyncio
import hashlib
import logging
from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Any, Dict, List, Optional, Protocol

# Use pure Python vector operations instead of numpy
from calibre_plugins.semantic_search.core.vector_ops import VectorOps

# Setup logging
logger = logging.getLogger(__name__)


class EmbeddingProvider(Protocol):
    """Protocol for embedding providers"""

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for single text"""
        ...

    async def generate_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        ...

    def get_dimensions(self) -> int:
        """Get embedding dimensions"""
        ...

    def get_model_name(self) -> str:
        """Get model name"""
        ...


class BaseEmbeddingProvider(ABC):
    """Base class for embedding providers"""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key
        self.model = model

    @abstractmethod
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for single text"""
        pass

    async def generate_batch(self, texts: List[str]) -> List[List[float]]:
        """Default batch implementation - override for efficiency"""
        tasks = [self.generate_embedding(text) for text in texts]
        return await asyncio.gather(*tasks)

    @abstractmethod
    def get_dimensions(self) -> int:
        """Get embedding dimensions"""
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Get model name"""
        pass

    def _truncate_text(self, text: str, max_tokens: int = 8192) -> str:
        """Truncate text to max tokens (rough approximation)"""
        words = text.split()
        max_words = int(max_tokens / 1.3)  # Rough token to word ratio
        if len(words) > max_words:
            return " ".join(words[:max_words])
        return text


class VertexAIProvider(BaseEmbeddingProvider):
    """Google Vertex AI embedding provider"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "text-embedding-preview-0815",
        project_id: Optional[str] = None,
        location: str = "us-central1",
    ):
        super().__init__(api_key, model)
        self.project_id = project_id
        self.location = location
        self._dimensions = 768

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using Vertex AI"""
        try:
            # Import here to avoid dependency if not used
            from litellm import aembedding

            # Vertex AI uses project ID instead of API key
            response = await aembedding(
                model=f"vertex_ai/{self.model}",
                input=self._truncate_text(text),
                vertex_project=self.project_id,
                vertex_location=self.location,
            )

            embedding = response["data"][0]["embedding"]
            return embedding  # Already a list of floats

        except Exception as e:
            logger.error(f"Vertex AI embedding error: {e}")
            raise

    async def generate_batch(self, texts: List[str]) -> List[List[float]]:
        """Batch generation for Vertex AI"""
        try:
            from litellm import aembedding

            # Truncate all texts
            truncated = [self._truncate_text(text) for text in texts]

            response = await aembedding(
                model=f"vertex_ai/{self.model}",
                input=truncated,
                vertex_project=self.project_id,
                vertex_location=self.location,
            )

            embeddings = [
                item["embedding"]  # Already a list of floats
                for item in response["data"]
            ]
            return embeddings

        except Exception as e:
            logger.error(f"Vertex AI batch embedding error: {e}")
            # Fall back to sequential
            return await super().generate_batch(texts)

    def get_dimensions(self) -> int:
        return self._dimensions

    def get_model_name(self) -> str:
        return f"vertex_ai/{self.model}"


class OpenAIProvider(BaseEmbeddingProvider):
    """OpenAI embedding provider"""

    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        super().__init__(api_key, model)
        self._dimensions = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536,
        }.get(model, 1536)

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI"""
        try:
            from litellm import aembedding

            response = await aembedding(
                model=f"openai/{self.model}",
                input=self._truncate_text(text),
                api_key=self.api_key,
            )

            embedding = response["data"][0]["embedding"]
            return embedding  # Already a list of floats

        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}")
            raise

    async def generate_batch(self, texts: List[str]) -> List[List[float]]:
        """Batch generation for OpenAI"""
        try:
            from litellm import aembedding

            # OpenAI supports batch embedding
            truncated = [self._truncate_text(text) for text in texts]

            response = await aembedding(
                model=f"openai/{self.model}", input=truncated, api_key=self.api_key
            )

            embeddings = [
                item["embedding"]  # Already a list of floats
                for item in response["data"]
            ]
            return embeddings

        except Exception as e:
            logger.error(f"OpenAI batch embedding error: {e}")
            return await super().generate_batch(texts)

    def get_dimensions(self) -> int:
        return self._dimensions

    def get_model_name(self) -> str:
        return f"openai/{self.model}"


class CohereProvider(BaseEmbeddingProvider):
    """Cohere embedding provider"""

    def __init__(self, api_key: str, model: str = "embed-english-v3.0"):
        super().__init__(api_key, model)
        self._dimensions = 1024  # Cohere default

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using Cohere"""
        try:
            from litellm import aembedding

            response = await aembedding(
                model=f"cohere/{self.model}",
                input=self._truncate_text(text),
                api_key=self.api_key,
                input_type="search_document",  # For indexing
            )

            embedding = response["data"][0]["embedding"]
            return embedding  # Already a list of floats

        except Exception as e:
            logger.error(f"Cohere embedding error: {e}")
            raise

    def get_dimensions(self) -> int:
        return self._dimensions

    def get_model_name(self) -> str:
        return f"cohere/{self.model}"


class MockProvider(BaseEmbeddingProvider):
    """Mock provider for testing"""

    def __init__(self, dimensions: int = 768, fail: bool = False):
        super().__init__(None, "mock")
        self._dimensions = dimensions
        self._fail = fail

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate mock embedding"""
        if self._fail:
            raise Exception("Mock provider configured to fail")

        # Generate deterministic embedding based on text
        import random
        random.seed(hash(text) % (2**32))
        
        # Generate random values
        embedding = [random.random() for _ in range(self._dimensions)]
        
        # Normalize to unit length
        embedding = VectorOps.normalize(embedding)

        return embedding

    def get_dimensions(self) -> int:
        return self._dimensions

    def get_model_name(self) -> str:
        return "mock"


class EmbeddingCache:
    """Simple embedding cache"""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache = {}

    def _get_key(self, text: str, model: str) -> str:
        """Generate cache key"""
        content = f"{model}:{text}"
        return hashlib.sha256(content.encode()).hexdigest()

    def get(self, text: str, model: str) -> Optional[List[float]]:
        """Get embedding from cache"""
        key = self._get_key(text, model)
        return self._cache.get(key)

    def set(self, text: str, model: str, embedding: List[float]):
        """Store embedding in cache"""
        # Simple LRU: remove oldest if at capacity
        if len(self._cache) >= self.max_size:
            oldest = next(iter(self._cache))
            del self._cache[oldest]

        key = self._get_key(text, model)
        self._cache[key] = embedding.copy()

    def clear(self):
        """Clear cache"""
        self._cache.clear()


class EmbeddingService:
    """Main embedding service with fallback support"""

    def __init__(
        self,
        providers: List[EmbeddingProvider],
        cache_enabled: bool = True,
        cache_size: int = 1000,
    ):
        if not providers:
            raise ValueError("At least one provider required")

        self.providers = providers
        self.cache = EmbeddingCache(cache_size) if cache_enabled else None
        self.last_provider = None

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding with fallback support"""
        # Check cache first
        if self.cache:
            for provider in self.providers:
                cached = self.cache.get(text, provider.get_model_name())
                if cached is not None:
                    self.last_provider = provider
                    return cached

        # Try each provider
        errors = []
        for provider in self.providers:
            try:
                logger.info(f"Trying provider: {provider.get_model_name()}")
                embedding = await provider.generate_embedding(text)

                # Cache successful result
                if self.cache:
                    self.cache.set(text, provider.get_model_name(), embedding)

                self.last_provider = provider
                return embedding

            except Exception as e:
                logger.warning(f"Provider {provider.get_model_name()} failed: {e}")
                errors.append((provider.get_model_name(), str(e)))
                continue

        # All providers failed
        error_msg = "All providers failed: " + ", ".join(
            f"{name}: {error}" for name, error in errors
        )
        raise Exception(error_msg)

    async def generate_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        # Separate cached and uncached
        cached_embeddings = {}
        uncached_texts = []
        uncached_indices = []

        if self.cache and self.providers:
            model = self.providers[0].get_model_name()
            for i, text in enumerate(texts):
                cached = self.cache.get(text, model)
                if cached is not None:
                    cached_embeddings[i] = cached
                else:
                    uncached_texts.append(text)
                    uncached_indices.append(i)
        else:
            uncached_texts = texts
            uncached_indices = list(range(len(texts)))

        # Generate uncached embeddings
        if uncached_texts:
            # Try each provider for batch
            errors = []
            for provider in self.providers:
                try:
                    logger.info(f"Batch embedding with {provider.get_model_name()}")
                    new_embeddings = await provider.generate_batch(uncached_texts)

                    # Cache results
                    if self.cache:
                        model = provider.get_model_name()
                        for text, embedding in zip(uncached_texts, new_embeddings):
                            self.cache.set(text, model, embedding)

                    # Combine with cached
                    result = [None] * len(texts)
                    for i, embedding in cached_embeddings.items():
                        result[i] = embedding
                    for i, idx in enumerate(uncached_indices):
                        result[idx] = new_embeddings[i]

                    self.last_provider = provider
                    return result

                except Exception as e:
                    logger.warning(
                        f"Batch provider {provider.get_model_name()} failed: {e}"
                    )
                    errors.append((provider.get_model_name(), str(e)))
                    continue

            # All providers failed
            raise Exception(f"All providers failed for batch: {errors}")

        # All cached
        result = [None] * len(texts)
        for i, embedding in cached_embeddings.items():
            result[i] = embedding
        return result

    def get_dimensions(self) -> int:
        """Get embedding dimensions from first provider"""
        return self.providers[0].get_dimensions() if self.providers else 0

    def clear_cache(self):
        """Clear embedding cache"""
        if self.cache:
            self.cache.clear()


def create_embedding_service(config: Dict[str, Any]) -> EmbeddingService:
    """Factory function to create embedding service from config"""
    providers = []

    # Get provider configuration
    provider_name = config.get("embedding_provider", "mock")
    api_keys = config.get("api_keys", {})

    # Create primary provider
    if provider_name == "vertex_ai":
        provider = VertexAIProvider(
            project_id=api_keys.get("vertex_ai_project"),
            model=config.get("embedding_model", "text-embedding-preview-0815"),
        )
        providers.append(provider)

    elif provider_name == "openai":
        if api_key := api_keys.get("openai"):
            provider = OpenAIProvider(
                api_key=api_key,
                model=config.get("embedding_model", "text-embedding-3-small"),
            )
            providers.append(provider)

    elif provider_name == "cohere":
        if api_key := api_keys.get("cohere"):
            provider = CohereProvider(
                api_key=api_key,
                model=config.get("embedding_model", "embed-english-v3.0"),
            )
            providers.append(provider)

    # Add fallback providers
    # Always add mock as final fallback for development
    providers.append(MockProvider())

    # Create service
    cache_enabled = config.get("performance", {}).get("cache_enabled", True)
    cache_size = (
        config.get("performance", {}).get("cache_size_mb", 100) * 100
    )  # Rough estimate

    return EmbeddingService(
        providers=providers, cache_enabled=cache_enabled, cache_size=cache_size
    )
