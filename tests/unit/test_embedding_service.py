"""
Unit tests for embedding service
"""

import pytest
import math
from unittest.mock import Mock, AsyncMock, patch
import asyncio
import sys
from pathlib import Path
import importlib.util

# Direct import without going through plugin __init__.py
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "calibre_plugins" / "semantic_search"))

from core.embedding_service import (
    EmbeddingService, BaseEmbeddingProvider, MockProvider,
    VertexAIProvider, OpenAIProvider, EmbeddingCache
)

# Load VectorOps directly
vector_ops_path = Path(__file__).parent.parent.parent / "calibre_plugins" / "semantic_search" / "core" / "vector_ops.py"
spec = importlib.util.spec_from_file_location("vector_ops", vector_ops_path)
vector_ops_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vector_ops_module)
VectorOps = vector_ops_module.VectorOps


class TestMockProvider:
    """Test the mock embedding provider"""
    
    def test_mock_provider_creation(self):
        """Test creating mock provider"""
        provider = MockProvider(dimensions=768, fail=False)
        assert provider.get_dimensions() == 768
        assert provider.get_model_name() == "mock"
        
    @pytest.mark.asyncio
    async def test_mock_embedding_generation(self):
        """Test mock embedding generation"""
        provider = MockProvider(dimensions=768)
        embedding = await provider.generate_embedding("test text")
        
        assert isinstance(embedding, list)
        assert len(embedding) == 768
        # Check normalization using VectorOps
        norm = VectorOps.norm(embedding)
        assert abs(norm - 1.0) < 0.001
        
    @pytest.mark.asyncio
    async def test_mock_deterministic(self):
        """Test that mock embeddings are deterministic"""
        provider = MockProvider()
        text = "test text"
        
        emb1 = await provider.generate_embedding(text)
        emb2 = await provider.generate_embedding(text)
        
        assert emb1 == emb2  # Lists should be identical for same input
        
    @pytest.mark.asyncio
    async def test_mock_failure_mode(self):
        """Test mock provider failure mode"""
        provider = MockProvider(fail=True)
        
        with pytest.raises(Exception, match="Mock provider configured to fail"):
            await provider.generate_embedding("test")


class TestEmbeddingCache:
    """Test embedding cache functionality"""
    
    def test_cache_basic_operations(self):
        """Test basic cache operations"""
        cache = EmbeddingCache(max_size=3)
        
        # Test set and get
        import random
        random.seed(42)
        embedding = [random.random() for _ in range(768)]
        cache.set("test", "model1", embedding)
        
        retrieved = cache.get("test", "model1")
        assert retrieved is not None
        assert retrieved == embedding
        
        # Test cache miss
        assert cache.get("nonexistent", "model1") is None
        
    def test_cache_eviction(self):
        """Test LRU eviction"""
        cache = EmbeddingCache(max_size=2)
        
        # Fill cache
        emb1 = [1.0]
        emb2 = [2.0]
        emb3 = [3.0]
        
        cache.set("text1", "model", emb1)
        cache.set("text2", "model", emb2)
        
        # This should evict text1
        cache.set("text3", "model", emb3)
        
        assert cache.get("text1", "model") is None
        assert cache.get("text2", "model") is not None
        assert cache.get("text3", "model") is not None
        
    def test_cache_key_generation(self):
        """Test cache key uniqueness"""
        cache = EmbeddingCache()
        
        # Different texts should have different keys
        key1 = cache._get_key("text1", "model")
        key2 = cache._get_key("text2", "model")
        assert key1 != key2
        
        # Different models should have different keys
        key3 = cache._get_key("text1", "model2")
        assert key1 != key3


class TestEmbeddingService:
    """Test the main embedding service"""
    
    @pytest.mark.asyncio
    async def test_service_with_single_provider(self):
        """Test service with single provider"""
        provider = MockProvider()
        service = EmbeddingService([provider])
        
        embedding = await service.generate_embedding("test text")
        
        assert isinstance(embedding, list)
        assert len(embedding) == 768
        assert service.last_provider == provider
        
    @pytest.mark.asyncio
    async def test_fallback_mechanism(self):
        """Test fallback between providers"""
        primary = MockProvider(fail=True)
        fallback = MockProvider(fail=False)
        
        service = EmbeddingService([primary, fallback])
        embedding = await service.generate_embedding("test")
        
        assert embedding is not None
        assert service.last_provider == fallback
        
    @pytest.mark.asyncio
    async def test_all_providers_fail(self):
        """Test when all providers fail"""
        provider1 = MockProvider(fail=True)
        provider2 = MockProvider(fail=True)
        
        service = EmbeddingService([provider1, provider2])
        
        with pytest.raises(Exception, match="All providers failed"):
            await service.generate_embedding("test")
            
    @pytest.mark.asyncio
    async def test_caching(self):
        """Test embedding caching"""
        provider = MockProvider()
        service = EmbeddingService([provider], cache_enabled=True)
        
        # First call should hit provider
        emb1 = await service.generate_embedding("test")
        
        # Mock the provider to return different embedding
        with patch.object(provider, 'generate_embedding', 
                         new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = [1.0] * 768
            
            # Second call should return cached value
            emb2 = await service.generate_embedding("test")
            
            # Should not have called provider
            mock_gen.assert_not_called()
            
        # Should return same embedding
        assert emb1 == emb2  # Lists should be identical for same input
        
    @pytest.mark.asyncio
    async def test_batch_generation(self):
        """Test batch embedding generation"""
        provider = MockProvider()
        service = EmbeddingService([provider])
        
        texts = ["text1", "text2", "text3"]
        embeddings = await service.generate_batch(texts)
        
        assert len(embeddings) == 3
        assert all(isinstance(emb, list) for emb in embeddings)
        assert all(len(emb) == 768 for emb in embeddings)
        
        # Check that different texts get different embeddings
        assert embeddings[0] != embeddings[1]
        
    @pytest.mark.asyncio
    async def test_batch_with_cache(self):
        """Test batch generation with caching"""
        provider = MockProvider()
        service = EmbeddingService([provider], cache_enabled=True)
        
        # Pre-cache one embedding
        await service.generate_embedding("text1")
        
        # Batch request including cached text
        with patch.object(provider, 'generate_batch', 
                         new_callable=AsyncMock) as mock_batch:
            # Mock should only be called with uncached texts
            import random
            random.seed(123)
            mock_batch.return_value = [
                [random.random() for _ in range(768)] for _ in range(2)
            ]
            
            texts = ["text1", "text2", "text3"]
            embeddings = await service.generate_batch(texts)
            
            # Should only call with uncached texts
            mock_batch.assert_called_once()
            call_args = mock_batch.call_args[0][0]
            assert "text1" not in call_args
            assert "text2" in call_args
            assert "text3" in call_args
            
        assert len(embeddings) == 3


class TestProviderImplementations:
    """Test specific provider implementations"""
    
    def test_openai_provider_init(self):
        """Test OpenAI provider initialization"""
        provider = OpenAIProvider(api_key="test_key", model="text-embedding-3-small")
        
        assert provider.api_key == "test_key"
        assert provider.model == "text-embedding-3-small"
        assert provider.get_dimensions() == 1536
        assert provider.get_model_name() == "openai/text-embedding-3-small"
        
    def test_vertex_ai_provider_init(self):
        """Test Vertex AI provider initialization"""
        provider = VertexAIProvider(
            project_id="test_project",
            model="text-embedding-preview-0815"
        )
        
        assert provider.project_id == "test_project"
        assert provider.model == "text-embedding-preview-0815"
        assert provider.get_dimensions() == 768
        assert provider.location == "us-central1"
        
    def test_text_truncation(self):
        """Test text truncation for long inputs"""
        provider = MockProvider()
        
        # Create very long text
        long_text = " ".join(["word"] * 10000)
        truncated = provider._truncate_text(long_text, max_tokens=100)
        
        # Should be significantly shorter
        assert len(truncated.split()) < len(long_text.split())
        assert len(truncated.split()) <= 100 / 1.3  # Approximate token ratio


class TestEmbeddingServiceFactory:
    """Test embedding service factory"""
    
    def test_create_service_with_mock(self):
        """Test creating service with mock provider"""
        from core.embedding_service import create_embedding_service
        
        config = {
            'embedding_provider': 'mock',
            'api_keys': {},
            'performance': {
                'cache_enabled': True,
                'cache_size_mb': 10
            }
        }
        
        service = create_embedding_service(config)
        
        assert isinstance(service, EmbeddingService)
        assert len(service.providers) >= 1
        assert isinstance(service.providers[-1], MockProvider)
        
    def test_create_service_with_api_provider(self):
        """Test creating service with API provider"""
        from core.embedding_service import create_embedding_service
        
        config = {
            'embedding_provider': 'openai',
            'embedding_model': 'text-embedding-3-small',
            'api_keys': {
                'openai': 'test_key'
            },
            'performance': {
                'cache_enabled': False
            }
        }
        
        service = create_embedding_service(config)
        
        assert isinstance(service, EmbeddingService)
        assert any(isinstance(p, OpenAIProvider) for p in service.providers)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])