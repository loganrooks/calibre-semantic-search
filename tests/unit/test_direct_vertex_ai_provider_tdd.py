#!/usr/bin/env python3
"""
TDD Tests for Direct Vertex AI Provider (gemini-embedding-001 support)

RED-GREEN-REFACTOR approach for implementing direct Vertex AI integration
that bypasses LiteLLM to support gemini-embedding-001 model.

Research Findings:
- LiteLLM does NOT support gemini-embedding-001
- gemini-embedding-001 supports up to 3072 dimensions with output_dimensionality param
- Single input text per request (no batching)
- Requires Google Cloud authentication
- Need project_id and location parameters
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import sys
import os
import asyncio

# Add plugin path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'calibre_plugins', 'semantic_search'))

class TestDirectVertexAIProviderRequirements:
    """RED: Test requirements for direct Vertex AI provider"""
    
    def test_direct_vertex_ai_provider_exists(self):
        """RED: Direct Vertex AI provider should exist separately from LiteLLM version"""
        try:
            from core.embedding_providers.direct_vertex_ai import DirectVertexAIProvider
            assert DirectVertexAIProvider is not None
            print("✅ DirectVertexAIProvider class exists")
        except ImportError:
            pytest.fail("DirectVertexAIProvider not implemented yet")
    
    def test_supports_gemini_embedding_001(self):
        """RED: Provider should explicitly support gemini-embedding-001"""
        try:
            from core.embedding_providers.direct_vertex_ai import DirectVertexAIProvider
            
            config = {
                "model": "gemini-embedding-001",
                "project_id": "test-project",
                "location": "us-central1",
                "dimensions": 3072
            }
            
            provider = DirectVertexAIProvider(config)
            assert provider.model == "gemini-embedding-001"
            assert provider.get_dimensions() == 3072
            print("✅ gemini-embedding-001 configuration supported")
            
        except ImportError:
            pytest.fail("DirectVertexAIProvider not implemented yet")
    
    def test_supports_custom_dimensionality(self):
        """RED: Provider should support output_dimensionality parameter"""
        try:
            from core.embedding_providers.direct_vertex_ai import DirectVertexAIProvider
            
            # Test various dimension sizes
            for dims in [256, 768, 1536, 3072]:
                config = {
                    "model": "gemini-embedding-001",
                    "project_id": "test-project", 
                    "location": "us-central1",
                    "dimensions": dims
                }
                
                provider = DirectVertexAIProvider(config)
                assert provider.get_dimensions() == dims
                
            print("✅ Custom dimensionality support verified")
            
        except ImportError:
            pytest.fail("DirectVertexAIProvider not implemented yet")
    
    def test_authentication_configuration(self):
        """RED: Provider should handle Google Cloud authentication"""
        try:
            from core.embedding_providers.direct_vertex_ai import DirectVertexAIProvider
            
            # Test with service account key
            config_service_account = {
                "model": "gemini-embedding-001",
                "project_id": "test-project",
                "location": "us-central1", 
                "dimensions": 768,
                "service_account_key": "/path/to/key.json"
            }
            
            provider1 = DirectVertexAIProvider(config_service_account)
            assert hasattr(provider1, 'service_account_key')
            
            # Test with Application Default Credentials
            config_adc = {
                "model": "gemini-embedding-001",
                "project_id": "test-project",
                "location": "us-central1",
                "dimensions": 768
            }
            
            provider2 = DirectVertexAIProvider(config_adc)
            assert provider2.project_id == "test-project"
            
            print("✅ Authentication configuration supported")
            
        except ImportError:
            pytest.fail("DirectVertexAIProvider not implemented yet")

class TestDirectVertexAIProviderBehavior:
    """RED: Test specific behavior requirements"""
    
    @pytest.mark.asyncio
    async def test_single_text_embedding_generation(self):
        """RED: Should generate embeddings for single text"""
        try:
            from core.embedding_providers.direct_vertex_ai import DirectVertexAIProvider
            
            config = {
                "model": "gemini-embedding-001",
                "project_id": "test-project",
                "location": "us-central1",
                "dimensions": 768
            }
            
            provider = DirectVertexAIProvider(config)
            
            # Mock the Google Cloud AI Platform call
            with patch.object(provider, '_call_vertex_ai_api', new_callable=AsyncMock) as mock_api:
                mock_api.return_value = [0.1] * 768  # Mock embedding vector
                
                result = await provider.generate_embedding("Test philosophical text about consciousness")
                
                assert len(result) == 768
                assert isinstance(result, list)
                assert all(isinstance(x, float) for x in result)
                mock_api.assert_called_once()
                
            print("✅ Single text embedding generation works")
            
        except ImportError:
            pytest.fail("DirectVertexAIProvider not implemented yet")
    
    @pytest.mark.asyncio
    async def test_batch_embedding_with_sequential_calls(self):
        """RED: Should handle batch via sequential calls (gemini limitation)"""
        try:
            from core.embedding_providers.direct_vertex_ai import DirectVertexAIProvider
            
            config = {
                "model": "gemini-embedding-001",
                "project_id": "test-project",
                "location": "us-central1",
                "dimensions": 768
            }
            
            provider = DirectVertexAIProvider(config)
            
            texts = [
                "First philosophical text",
                "Second philosophical text", 
                "Third philosophical text"
            ]
            
            with patch.object(provider, '_call_vertex_ai_api', new_callable=AsyncMock) as mock_api:
                mock_api.return_value = [0.1] * 768  # Mock embedding vector
                
                results = await provider.generate_batch(texts)
                
                assert len(results) == 3
                assert len(results[0]) == 768
                assert mock_api.call_count == 3  # Should make 3 sequential calls
                
            print("✅ Batch embedding via sequential calls works")
            
        except ImportError:
            pytest.fail("DirectVertexAIProvider not implemented yet")
    
    def test_error_handling_and_validation(self):
        """RED: Should validate configuration and handle errors gracefully"""
        try:
            from core.embedding_providers.direct_vertex_ai import DirectVertexAIProvider
            
            # Test missing required fields
            with pytest.raises(ValueError, match="project_id.*required"):
                DirectVertexAIProvider({"model": "gemini-embedding-001"})
            
            with pytest.raises(ValueError, match="location.*required"):
                DirectVertexAIProvider({
                    "model": "gemini-embedding-001", 
                    "project_id": "test-project"
                })
            
            # Test invalid dimensions
            with pytest.raises(ValueError, match="dimensions.*between 1 and 3072"):
                DirectVertexAIProvider({
                    "model": "gemini-embedding-001",
                    "project_id": "test-project",
                    "location": "us-central1", 
                    "dimensions": 5000  # Too large
                })
            
            print("✅ Configuration validation works")
            
        except ImportError:
            pytest.fail("DirectVertexAIProvider not implemented yet")

class TestDirectVertexAIProviderIntegration:
    """RED: Test integration with existing embedding service"""
    
    def test_integrates_with_embedding_service(self):
        """RED: Should integrate with existing EmbeddingService"""
        try:
            from core.embedding_service import create_embedding_service
            from core.embedding_providers.direct_vertex_ai import DirectVertexAIProvider
            
            # Mock configuration
            config = {
                "embedding_provider": "direct_vertex_ai",
                "embedding_model": "gemini-embedding-001",
                "vertex_project_id": "test-project",
                "vertex_location": "us-central1", 
                "embedding_dimensions": 1536
            }
            
            # EmbeddingService should be able to create DirectVertexAIProvider
            service = create_embedding_service(config)
            
            # Check that DirectVertexAIProvider was created
            assert len(service.providers) >= 1
            
            # Find the DirectVertexAIProvider in the providers list
            direct_vertex_provider = None
            for provider in service.providers:
                if isinstance(provider, DirectVertexAIProvider):
                    direct_vertex_provider = provider
                    break
            
            assert direct_vertex_provider is not None, "DirectVertexAIProvider not found in service providers"
            assert direct_vertex_provider.get_dimensions() == 1536
            assert direct_vertex_provider.model == "gemini-embedding-001"
            
            print("✅ Integration with EmbeddingService works")
            
        except ImportError:
            pytest.fail("DirectVertexAIProvider not implemented yet")
        except AttributeError:
            pytest.fail("EmbeddingService doesn't support DirectVertexAIProvider yet")

class TestVertexAIAPIIntegration:
    """RED: Test actual Google Cloud AI Platform API integration"""
    
    @pytest.mark.asyncio
    async def test_real_vertex_ai_api_call_structure(self):
        """RED: Should structure API calls correctly for Vertex AI"""
        try:
            from core.embedding_providers.direct_vertex_ai import DirectVertexAIProvider
            
            config = {
                "model": "gemini-embedding-001",
                "project_id": "test-project",
                "location": "us-central1",
                "dimensions": 1024
            }
            
            provider = DirectVertexAIProvider(config)
            
            # Mock google.cloud.aiplatform calls
            with patch('google.cloud.aiplatform.init') as mock_init:
                with patch('google.cloud.aiplatform.TextEmbeddingModel') as mock_model_class:
                    mock_model = Mock()
                    mock_model.get_embeddings = AsyncMock()
                    mock_model.get_embeddings.return_value = [
                        Mock(values=[0.1] * 1024)  # Mock TextEmbedding object
                    ]
                    mock_model_class.from_pretrained.return_value = mock_model
                    
                    result = await provider.generate_embedding("Test text")
                    
                    # Verify correct API usage
                    mock_init.assert_called_once_with(
                        project="test-project",
                        location="us-central1"
                    )
                    mock_model_class.from_pretrained.assert_called_once_with("gemini-embedding-001")
                    
                    assert len(result) == 1024
                    
            print("✅ Real Vertex AI API call structure correct")
            
        except ImportError:
            pytest.fail("DirectVertexAIProvider or google-cloud-aiplatform not available")

if __name__ == '__main__':
    print("🔴 RED Phase: TDD Tests for Direct Vertex AI Provider")
    print("=" * 60)
    print("These tests define requirements for gemini-embedding-001 support")
    print("All tests should FAIL initially, then we implement to make them PASS")
    print()
    print("Key Requirements:")
    print("✓ Direct Vertex AI integration (no LiteLLM)")
    print("✓ gemini-embedding-001 model support")
    print("✓ Custom dimensionality (1-3072)")
    print("✓ Google Cloud authentication")
    print("✓ Sequential batch processing (gemini limitation)")
    print("✓ Integration with existing EmbeddingService")
    print()
    
    pytest.main([__file__, '-v'])