"""
TDD Tests for Index Configuration Management

These tests define the behavior for index configuration validation,
compatibility checking, and configuration management.
"""

import pytest
from typing import Dict, Any


class TestIndexConfigValidation:
    """Test index configuration validation logic"""
    
    def test_valid_openai_config(self):
        """Test valid OpenAI configuration passes validation"""
        from calibre_plugins.semantic_search.core.index_config import IndexConfig
        
        config = IndexConfig({
            'provider': 'openai',
            'model_name': 'text-embedding-3-small',
            'dimensions': 1536,
            'chunk_size': 1000,
            'chunk_overlap': 200
        })
        
        assert config.is_valid() is True
        assert config.get_errors() == []
    
    def test_invalid_dimension_mismatch(self):
        """Test dimension mismatch is caught"""
        from calibre_plugins.semantic_search.core.index_config import IndexConfig
        
        config = IndexConfig({
            'provider': 'openai',
            'model_name': 'text-embedding-3-small',
            'dimensions': 768,  # Wrong! Should be 1536
            'chunk_size': 1000,
            'chunk_overlap': 200
        })
        
        assert config.is_valid() is False
        errors = config.get_errors()
        assert any('dimension' in error.lower() for error in errors)
    
    def test_invalid_chunk_overlap_too_large(self):
        """Test chunk overlap larger than chunk size is invalid"""
        from calibre_plugins.semantic_search.core.index_config import IndexConfig
        
        config = IndexConfig({
            'provider': 'vertex',
            'model_name': 'textembedding-gecko',
            'dimensions': 768,
            'chunk_size': 500,
            'chunk_overlap': 600  # Invalid! Overlap > size
        })
        
        assert config.is_valid() is False
        errors = config.get_errors()
        assert any('overlap' in error.lower() for error in errors)
    
    def test_unknown_provider_validation(self):
        """Test unknown provider is flagged"""
        from calibre_plugins.semantic_search.core.index_config import IndexConfig
        
        config = IndexConfig({
            'provider': 'unknown_provider',
            'model_name': 'some-model',
            'dimensions': 768,
            'chunk_size': 1000,
            'chunk_overlap': 200
        })
        
        assert config.is_valid() is False
        errors = config.get_errors()
        assert any('provider' in error.lower() for error in errors)


class TestIndexCompatibility:
    """Test index compatibility checking"""
    
    def test_compatible_same_provider_and_dimensions(self):
        """Test compatibility when provider and dimensions match"""
        from calibre_plugins.semantic_search.core.index_config import IndexConfig
        
        index_config = IndexConfig({
            'provider': 'openai',
            'model_name': 'text-embedding-3-small',
            'dimensions': 1536
        })
        
        # Query with same provider and dimensions should be compatible
        assert index_config.is_compatible_with_query(
            provider='openai',
            dimensions=1536
        ) is True
    
    def test_incompatible_different_provider(self):
        """Test incompatibility when providers differ"""
        from calibre_plugins.semantic_search.core.index_config import IndexConfig
        
        index_config = IndexConfig({
            'provider': 'openai',
            'model_name': 'text-embedding-3-small',
            'dimensions': 1536
        })
        
        # Different provider should be incompatible
        assert index_config.is_compatible_with_query(
            provider='vertex',
            dimensions=1536
        ) is False
    
    def test_incompatible_different_dimensions(self):
        """Test incompatibility when dimensions differ"""
        from calibre_plugins.semantic_search.core.index_config import IndexConfig
        
        index_config = IndexConfig({
            'provider': 'vertex',
            'model_name': 'textembedding-gecko',
            'dimensions': 768
        })
        
        # Different dimensions should be incompatible
        assert index_config.is_compatible_with_query(
            provider='vertex',
            dimensions=1536
        ) is False
    
    def test_model_version_compatibility(self):
        """Test that different model versions of same provider are compatible"""
        from calibre_plugins.semantic_search.core.index_config import IndexConfig
        
        # Index created with older model
        index_config = IndexConfig({
            'provider': 'openai',
            'model_name': 'text-embedding-ada-002',
            'dimensions': 1536
        })
        
        # Query with newer model should still be compatible
        # (assuming same dimensions)
        assert index_config.is_compatible_with_query(
            provider='openai',
            model_name='text-embedding-3-small',
            dimensions=1536
        ) is True


class TestProviderSpecificValidation:
    """Test provider-specific validation rules"""
    
    def test_openai_model_dimension_mapping(self):
        """Test OpenAI models have correct dimension requirements"""
        from calibre_plugins.semantic_search.core.index_config import IndexConfig
        
        # Valid OpenAI model configurations
        valid_configs = [
            ('text-embedding-ada-002', 1536),
            ('text-embedding-3-small', 1536),
            ('text-embedding-3-large', 3072),
        ]
        
        for model, dims in valid_configs:
            config = IndexConfig({
                'provider': 'openai',
                'model_name': model,
                'dimensions': dims,
                'chunk_size': 1000,
                'chunk_overlap': 200
            })
            assert config.is_valid(), f"Should be valid: {model} with {dims} dims"
    
    def test_vertex_model_dimension_mapping(self):
        """Test Vertex AI models have correct dimension requirements"""
        from calibre_plugins.semantic_search.core.index_config import IndexConfig
        
        # Valid Vertex AI configurations
        valid_configs = [
            ('textembedding-gecko', 768),
            ('textembedding-gecko-multilingual', 768),
        ]
        
        for model, dims in valid_configs:
            config = IndexConfig({
                'provider': 'vertex',
                'model_name': model,
                'dimensions': dims,
                'chunk_size': 1000,
                'chunk_overlap': 200
            })
            assert config.is_valid(), f"Should be valid: {model} with {dims} dims"
    
    def test_cohere_model_dimension_mapping(self):
        """Test Cohere models have correct dimension requirements"""
        from calibre_plugins.semantic_search.core.index_config import IndexConfig
        
        # Valid Cohere configurations
        valid_configs = [
            ('embed-english-v3.0', 1024),
            ('embed-multilingual-v3.0', 1024),
        ]
        
        for model, dims in valid_configs:
            config = IndexConfig({
                'provider': 'cohere',
                'model_name': model,
                'dimensions': dims,
                'chunk_size': 1000,
                'chunk_overlap': 200
            })
            assert config.is_valid(), f"Should be valid: {model} with {dims} dims"


class TestIndexConfigSerialization:
    """Test serialization/deserialization of index configurations"""
    
    def test_to_dict_serialization(self):
        """Test converting config to dictionary"""
        from calibre_plugins.semantic_search.core.index_config import IndexConfig
        
        config = IndexConfig({
            'provider': 'openai',
            'model_name': 'text-embedding-3-small',
            'dimensions': 1536,
            'chunk_size': 1000,
            'chunk_overlap': 200
        })
        
        config_dict = config.to_dict()
        
        expected_keys = {
            'provider', 'model_name', 'dimensions', 
            'chunk_size', 'chunk_overlap'
        }
        assert set(config_dict.keys()) >= expected_keys
        assert config_dict['provider'] == 'openai'
        assert config_dict['dimensions'] == 1536
    
    def test_from_dict_deserialization(self):
        """Test creating config from dictionary"""
        from calibre_plugins.semantic_search.core.index_config import IndexConfig
        
        config_dict = {
            'provider': 'vertex',
            'model_name': 'textembedding-gecko',
            'dimensions': 768,
            'chunk_size': 800,
            'chunk_overlap': 100,
            'metadata': {'custom_setting': 'value'}
        }
        
        config = IndexConfig.from_dict(config_dict)
        
        assert config.provider == 'vertex'
        assert config.model_name == 'textembedding-gecko'
        assert config.dimensions == 768
        assert config.chunk_size == 800
        assert config.chunk_overlap == 100
    
    def test_json_serialization_roundtrip(self):
        """Test JSON serialization/deserialization roundtrip"""
        from calibre_plugins.semantic_search.core.index_config import IndexConfig
        import json
        
        original_config = IndexConfig({
            'provider': 'cohere',
            'model_name': 'embed-english-v3.0',
            'dimensions': 1024,
            'chunk_size': 1200,
            'chunk_overlap': 300
        })
        
        # Serialize to JSON
        json_str = original_config.to_json()
        
        # Deserialize from JSON
        restored_config = IndexConfig.from_json(json_str)
        
        # Should be equivalent
        assert restored_config.provider == original_config.provider
        assert restored_config.model_name == original_config.model_name
        assert restored_config.dimensions == original_config.dimensions
        assert restored_config.chunk_size == original_config.chunk_size
        assert restored_config.chunk_overlap == original_config.chunk_overlap


class TestIndexConfigComparison:
    """Test comparing index configurations"""
    
    def test_config_equality(self):
        """Test that identical configs are considered equal"""
        from calibre_plugins.semantic_search.core.index_config import IndexConfig
        
        config1 = IndexConfig({
            'provider': 'openai',
            'model_name': 'text-embedding-3-small',
            'dimensions': 1536,
            'chunk_size': 1000,
            'chunk_overlap': 200
        })
        
        config2 = IndexConfig({
            'provider': 'openai',
            'model_name': 'text-embedding-3-small',
            'dimensions': 1536,
            'chunk_size': 1000,
            'chunk_overlap': 200
        })
        
        assert config1 == config2
        assert config1.get_hash() == config2.get_hash()
    
    def test_config_inequality(self):
        """Test that different configs are not equal"""
        from calibre_plugins.semantic_search.core.index_config import IndexConfig
        
        config1 = IndexConfig({
            'provider': 'openai',
            'model_name': 'text-embedding-3-small',
            'dimensions': 1536,
            'chunk_size': 1000,
            'chunk_overlap': 200
        })
        
        config2 = IndexConfig({
            'provider': 'openai',
            'model_name': 'text-embedding-3-small',
            'dimensions': 1536,
            'chunk_size': 1500,  # Different chunk size
            'chunk_overlap': 200
        })
        
        assert config1 != config2
        assert config1.get_hash() != config2.get_hash()
    
    def test_config_signature_for_uniqueness(self):
        """Test config signatures for database uniqueness constraints"""
        from calibre_plugins.semantic_search.core.index_config import IndexConfig
        
        config = IndexConfig({
            'provider': 'vertex',
            'model_name': 'textembedding-gecko',
            'dimensions': 768,
            'chunk_size': 800,
            'chunk_overlap': 100
        })
        
        # Signature should include all uniqueness-relevant fields
        signature = config.get_uniqueness_signature()
        
        assert 'vertex' in signature
        assert 'textembedding-gecko' in signature
        assert '768' in signature
        assert '800' in signature
        assert '100' in signature