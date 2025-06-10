#!/usr/bin/env python3
"""
Unit tests for model discovery integration into config methods
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import sys
import os
import asyncio

# Add plugin path 
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'calibre_plugins', 'semantic_search'))

def test_update_provider_models_uses_hardcoded_list():
    """RED: Test current _update_provider_models uses hardcoded models"""
    
    from calibre_plugins.semantic_search.config import ConfigWidget
    
    # Create partial config widget for testing
    config_widget = object.__new__(ConfigWidget)  # Skip __init__
    config_widget.model_combo_provider = Mock()
    
    # Call the method directly
    config_widget._update_provider_models("openai")
    
    # Verify hardcoded models were used
    config_widget.model_combo_provider.clear.assert_called_once()
    config_widget.model_combo_provider.addItems.assert_called_once()
    
    # Check exact hardcoded list
    call_args = config_widget.model_combo_provider.addItems.call_args[0][0]
    expected_hardcoded = [
        "text-embedding-3-small",
        "text-embedding-3-large", 
        "text-embedding-ada-002"
    ]
    assert call_args == expected_hardcoded

def test_update_provider_models_vertex_ai():
    """RED: Test current hardcoded models for vertex_ai"""
    
    from calibre_plugins.semantic_search.config import ConfigWidget
    
    config_widget = object.__new__(ConfigWidget)  
    config_widget.model_combo_provider = Mock()
    
    config_widget._update_provider_models("vertex_ai")
    
    call_args = config_widget.model_combo_provider.addItems.call_args[0][0]
    expected_hardcoded = [
        "text-embedding-004",
        "text-embedding-preview-0815",
        "textembedding-gecko@003", 
        "textembedding-gecko-multilingual@001"
    ]
    assert call_args == expected_hardcoded

def test_discovery_system_integration_missing():
    """RED: Test that discovery integration doesn't exist yet"""
    
    from calibre_plugins.semantic_search.config import ConfigWidget
    
    config_widget = object.__new__(ConfigWidget)
    
    # These methods shouldn't exist yet
    assert not hasattr(config_widget, '_update_provider_models_async')
    assert not hasattr(config_widget, 'model_discovery')
    assert not hasattr(config_widget, 'get_model_metadata')

@pytest.mark.asyncio
async def test_async_model_loading_not_implemented():
    """RED: Test that async model loading is not implemented"""
    
    from calibre_plugins.semantic_search.config import ConfigWidget
    
    config_widget = object.__new__(ConfigWidget)
    config_widget.model_combo_provider = Mock()
    
    # Should not have async version yet
    assert not hasattr(config_widget, '_update_provider_models_async')

def test_hardcoded_models_limited_count():
    """RED: Test that hardcoded models are limited compared to discovery"""
    
    from calibre_plugins.semantic_search.config import ConfigWidget
    
    config_widget = object.__new__(ConfigWidget)
    config_widget.model_combo_provider = Mock()
    
    # Get hardcoded counts
    config_widget._update_provider_models("openai")
    openai_hardcoded = len(config_widget.model_combo_provider.addItems.call_args[0][0])
    
    config_widget.model_combo_provider.reset_mock()
    config_widget._update_provider_models("vertex_ai") 
    vertex_hardcoded = len(config_widget.model_combo_provider.addItems.call_args[0][0])
    
    # Hardcoded should be small numbers
    assert openai_hardcoded == 3  # Only 3 OpenAI models hardcoded
    assert vertex_hardcoded == 4  # Only 4 Vertex AI models hardcoded
    
    # This proves the limitation - discovery has many more models available

if __name__ == '__main__':
    print("🔴 RED Phase: Testing that discovery is NOT integrated yet")
    print("These tests should pass, proving current limitations")
    
    pytest.main([__file__, '-v'])