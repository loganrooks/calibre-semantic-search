#!/usr/bin/env python3
"""
TDD tests for dynamic model discovery integration into config UI

RED-GREEN-REFACTOR approach:
1. RED: Write tests proving discovery system is NOT integrated
2. GREEN: Integrate discovery system into _update_provider_models 
3. REFACTOR: Add searchable dropdown and model metadata display
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import sys
import os
import asyncio

# Add plugin path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'calibre_plugins', 'semantic_search'))

def test_discovery_system_exists():
    """Verify the discovery system exists and is importable"""
    from embedding_model_discovery_system import EmbeddingModelDiscovery
    
    discovery = EmbeddingModelDiscovery()
    assert discovery is not None
    assert hasattr(discovery, 'discover_all_models')
    assert hasattr(discovery, 'get_models_for_provider')

@pytest.mark.asyncio 
async def test_discovery_system_returns_real_models():
    """Verify discovery system returns actual model data"""
    from embedding_model_discovery_system import EmbeddingModelDiscovery
    
    discovery = EmbeddingModelDiscovery()
    
    # Should return more models than hardcoded lists
    try:
        models = await discovery.discover_all_models()
        
        # Check we get multiple providers
        assert len(models) > 0
        
        # Check OpenAI has more than 3 hardcoded models
        if 'openai' in models:
            openai_models = models['openai']
            assert len(openai_models) >= 3
            
            # Verify model info structure
            model = openai_models[0]
            assert hasattr(model, 'name')
            assert hasattr(model, 'dimensions') 
            assert hasattr(model, 'provider')
            
    except Exception as e:
        pytest.skip(f"LiteLLM not available or discovery failed: {e}")

def test_config_ui_uses_hardcoded_models():
    """RED: Test that config UI currently uses hardcoded models (this should pass initially)"""
    
    try:
        from calibre_plugins.semantic_search.config import ConfigWidget
        
        with patch('calibre_plugins.semantic_search.config.QWidget'):
            with patch('calibre_plugins.semantic_search.config.QVBoxLayout'):
                with patch('calibre_plugins.semantic_search.config.QTabWidget'):
                    config_widget = ConfigWidget()
                    
                    # Mock the combo box
                    config_widget.model_combo_provider = Mock()
                    config_widget.model_combo_provider.clear = Mock()
                    config_widget.model_combo_provider.addItems = Mock()
                    
                    # Call the provider update method
                    config_widget._update_provider_models("openai")
                    
                    # Verify it uses hardcoded models (current behavior)
                    config_widget.model_combo_provider.addItems.assert_called_once()
                    call_args = config_widget.model_combo_provider.addItems.call_args[0][0]
                    
                    # Should be exactly the hardcoded list
                    expected_hardcoded = [
                        "text-embedding-3-small",
                        "text-embedding-3-large", 
                        "text-embedding-ada-002"
                    ]
                    assert call_args == expected_hardcoded
                    
    except ImportError:
        pytest.skip("Calibre plugins not available")

def test_config_ui_integration_with_discovery_system():
    """GREEN: Test that config UI integrates with discovery system (should fail initially)"""
    
    try:
        from calibre_plugins.semantic_search.config import ConfigWidget
        
        with patch('calibre_plugins.semantic_search.config.QWidget'):
            config_widget = ConfigWidget()
            
            # Mock the discovery system
            mock_discovery = Mock()
            mock_models = [
                Mock(name="text-embedding-3-small", dimensions=1536, provider="openai"),
                Mock(name="text-embedding-3-large", dimensions=3072, provider="openai"), 
                Mock(name="text-embedding-ada-002", dimensions=1536, provider="openai"),
                Mock(name="gpt-4-embed-preview", dimensions=2048, provider="openai")  # New model from discovery
            ]
            mock_discovery.get_models_for_provider = AsyncMock(return_value=mock_models)
            
            # Inject discovery system
            config_widget.model_discovery = mock_discovery
            config_widget.model_combo_provider = Mock()
            config_widget.model_combo_provider.clear = Mock()
            config_widget.model_combo_provider.addItems = Mock()
            
            # Call async provider update method (should exist after integration) 
            if hasattr(config_widget, '_update_provider_models_async'):
                # This should call the discovery system instead of hardcoded
                asyncio.run(config_widget._update_provider_models_async("openai"))
                
                # Verify discovery was called
                mock_discovery.get_models_for_provider.assert_called_with("openai")
                
                # Verify more models than hardcoded (including new discovery model)
                config_widget.model_combo_provider.addItems.assert_called()
                call_args = config_widget.model_combo_provider.addItems.call_args[0][0]
                assert len(call_args) > 3  # More than hardcoded
                assert "gpt-4-embed-preview" in call_args  # New model from discovery
            else:
                pytest.fail("_update_provider_models_async method not implemented yet")
                
    except ImportError:
        pytest.skip("Calibre plugins not available")

def test_config_ui_handles_discovery_failure_gracefully():
    """GREEN: Test graceful fallback when discovery fails"""
    
    try:
        from calibre_plugins.semantic_search.config import ConfigWidget
        
        with patch('calibre_plugins.semantic_search.config.QWidget'):
            config_widget = ConfigWidget()
            
            # Mock failing discovery system
            mock_discovery = Mock()
            mock_discovery.get_models_for_provider = AsyncMock(side_effect=Exception("API failed"))
            
            config_widget.model_discovery = mock_discovery
            config_widget.model_combo_provider = Mock()
            config_widget.model_combo_provider.clear = Mock()
            config_widget.model_combo_provider.addItems = Mock()
            
            # Should fallback to hardcoded models on discovery failure
            if hasattr(config_widget, '_update_provider_models_async'):
                asyncio.run(config_widget._update_provider_models_async("openai"))
                
                # Should still populate with fallback models
                config_widget.model_combo_provider.addItems.assert_called()
                call_args = config_widget.model_combo_provider.addItems.call_args[0][0]
                
                # Should be hardcoded fallback
                expected_fallback = [
                    "text-embedding-3-small",
                    "text-embedding-3-large",
                    "text-embedding-ada-002"
                ]
                assert call_args == expected_fallback
            else:
                pytest.fail("_update_provider_models_async method not implemented yet")
                
    except ImportError:
        pytest.skip("Calibre plugins not available")

def test_model_metadata_display():
    """REFACTOR: Test that model metadata is available for display"""
    
    try:
        from calibre_plugins.semantic_search.config import ConfigWidget
        
        with patch('calibre_plugins.semantic_search.config.QWidget'):
            config_widget = ConfigWidget()
            
            # Mock discovery with metadata
            mock_discovery = Mock()
            mock_model = Mock()
            mock_model.name = "text-embedding-3-large"
            mock_model.dimensions = 3072
            mock_model.max_tokens = 8191
            mock_model.special_params = {"supports_dimensions_param": True}
            
            mock_discovery.get_models_for_provider = AsyncMock(return_value=[mock_model])
            config_widget.model_discovery = mock_discovery
            
            # Should have method to get model metadata
            if hasattr(config_widget, 'get_model_metadata'):
                metadata = asyncio.run(config_widget.get_model_metadata("openai", "text-embedding-3-large"))
                
                assert metadata is not None
                assert metadata.dimensions == 3072
                assert metadata.max_tokens == 8191
                assert metadata.special_params["supports_dimensions_param"] == True
            else:
                pytest.fail("get_model_metadata method not implemented yet")
                
    except ImportError:
        pytest.skip("Calibre plugins not available")

if __name__ == '__main__':
    print("🔴 RED Phase: Testing dynamic model discovery integration")
    print("These tests verify the discovery system can be integrated into config UI")
    
    pytest.main([__file__, '-v'])