#!/usr/bin/env python3
"""
Quick test to verify discovery system integration works
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'calibre_plugins', 'semantic_search'))

def test_discovery_import():
    """Test that we can import the discovery system"""
    try:
        from embedding_model_discovery_system import EmbeddingModelDiscovery
        discovery = EmbeddingModelDiscovery()
        print("✅ Discovery system import: SUCCESS")
        return True
    except ImportError as e:
        print(f"❌ Discovery system import: FAILED - {e}")
        return False

def test_config_integration():
    """Test that config widget can integrate discovery"""
    try:
        # Mock Qt components for testing
        from unittest.mock import Mock, patch
        
        with patch('calibre_plugins.semantic_search.config.QWidget'):
            with patch('calibre_plugins.semantic_search.config.QVBoxLayout'):
                with patch('calibre_plugins.semantic_search.config.QTabWidget'):
                    with patch('calibre_plugins.semantic_search.config.QComboBox'):
                        from calibre_plugins.semantic_search.config import ConfigWidget
                        
                        # Create widget (should not crash)
                        widget = ConfigWidget()
                        
                        # Check discovery integration
                        has_discovery = hasattr(widget, 'model_discovery')
                        has_cache = hasattr(widget, '_model_cache')
                        has_async_method = hasattr(widget, '_update_provider_models_async')
                        has_metadata_method = hasattr(widget, 'get_model_metadata')
                        
                        print(f"✅ Config widget creation: SUCCESS")
                        print(f"✅ Has model_discovery: {has_discovery}")
                        print(f"✅ Has model cache: {has_cache}")
                        print(f"✅ Has async method: {has_async_method}")
                        print(f"✅ Has metadata method: {has_metadata_method}")
                        
                        return all([has_discovery, has_cache, has_async_method, has_metadata_method])
                        
    except Exception as e:
        print(f"❌ Config integration: FAILED - {e}")
        return False

def test_discovery_data_available():
    """Test that we have discovery data"""
    try:
        import json
        with open('comprehensive_model_discovery.json', 'r') as f:
            data = json.load(f)
        
        providers = list(data['discovered_models'].keys())
        total_models = sum(len(models) for models in data['discovered_models'].values())
        
        print(f"✅ Discovery data available: {total_models} models across {len(providers)} providers")
        print(f"   Providers: {providers}")
        return True
        
    except Exception as e:
        print(f"❌ Discovery data: FAILED - {e}")
        return False

if __name__ == '__main__':
    print("🔧 Testing Discovery System Integration")
    print("=" * 50)
    
    tests = [
        test_discovery_import,
        test_config_integration, 
        test_discovery_data_available
    ]
    
    results = []
    for test in tests:
        results.append(test())
        print()
    
    if all(results):
        print("🎉 All integration tests PASSED!")
        print("Discovery system is successfully integrated into config UI")
    else:
        print("❌ Some integration tests FAILED")
        print("Discovery system integration needs more work")