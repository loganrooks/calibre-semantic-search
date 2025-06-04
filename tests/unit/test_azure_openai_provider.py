"""
Test Azure OpenAI provider implementation
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

from calibre_plugins.semantic_search.core.embedding_service import (
    AzureOpenAIProvider,
    create_embedding_service
)


class TestAzureOpenAIProvider:
    """Test Azure OpenAI embedding provider"""

    @pytest.fixture
    def provider(self):
        """Create test provider"""
        return AzureOpenAIProvider(
            api_key="test-key",
            deployment="text-embedding-ada-002",
            api_base="https://test.openai.azure.com/",
            api_version="2024-02-01"
        )

    def test_initialization(self, provider):
        """Test provider initialization"""
        assert provider.api_key == "test-key"
        assert provider.deployment == "text-embedding-ada-002"
        assert provider.api_base == "https://test.openai.azure.com/"
        assert provider.api_version == "2024-02-01"
        assert provider.get_dimensions() == 1536

    def test_model_name(self, provider):
        """Test model name formatting"""
        assert provider.get_model_name() == "azure/text-embedding-ada-002"

    @pytest.mark.asyncio
    async def test_generate_embedding(self, provider):
        """Test single embedding generation"""
        mock_response = {
            "data": [{"embedding": [0.1] * 1536}]
        }
        
        with patch("litellm.aembedding", new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = mock_response
            
            result = await provider.generate_embedding("test text")
            
            assert len(result) == 1536
            assert all(v == 0.1 for v in result)
            
            # Verify correct parameters passed
            mock_embed.assert_called_once()
            call_args = mock_embed.call_args[1]
            assert call_args["model"] == "azure/text-embedding-ada-002"
            assert call_args["api_key"] == "test-key"
            assert call_args["api_base"] == "https://test.openai.azure.com/"
            assert call_args["api_version"] == "2024-02-01"

    @pytest.mark.asyncio
    async def test_generate_batch(self, provider):
        """Test batch embedding generation"""
        mock_response = {
            "data": [
                {"embedding": [0.1] * 1536},
                {"embedding": [0.2] * 1536}
            ]
        }
        
        with patch("litellm.aembedding", new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = mock_response
            
            result = await provider.generate_batch(["text1", "text2"])
            
            assert len(result) == 2
            assert len(result[0]) == 1536
            assert len(result[1]) == 1536
            assert all(v == 0.1 for v in result[0])
            assert all(v == 0.2 for v in result[1])

    def test_create_embedding_service_with_azure(self):
        """Test creating embedding service with Azure provider"""
        config = {
            "embedding_provider": "azure_openai",
            "api_keys": {"azure_openai": "test-key"},
            "azure_deployment": "my-deployment",
            "azure_api_base": "https://myresource.openai.azure.com/",
            "azure_api_version": "2024-02-01"
        }
        
        service = create_embedding_service(config)
        
        # Should have Azure provider + Mock fallback
        assert len(service.providers) == 2
        assert isinstance(service.providers[0], AzureOpenAIProvider)
        assert service.providers[0].deployment == "my-deployment"
        assert service.providers[0].api_base == "https://myresource.openai.azure.com/"