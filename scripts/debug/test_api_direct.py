#!/usr/bin/env python3
"""
Direct API Testing Script - Test embedding providers without UI
"""

import asyncio
import os
import sys

# Add the plugin to path
sys.path.insert(0, 'calibre_plugins/semantic_search')

from core.embedding_service import create_embedding_service

async def test_mock_provider():
    """Test mock provider (should always work)"""
    print("Testing Mock Provider...")
    config = {
        'embedding': {
            'providers': ['mock'],
            'mock': {'enabled': True}
        }
    }
    
    service = create_embedding_service(config)
    result = await service.generate_embedding("Test text for mock provider")
    print(f"Mock result: {len(result)} dimensions, sample: {result[:5]}")
    return True

async def test_vertex_ai():
    """Test Vertex AI provider"""
    print("\nTesting Vertex AI Provider...")
    
    # Check for credentials
    creds_file = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    if not creds_file:
        print("❌ GOOGLE_APPLICATION_CREDENTIALS not set")
        return False
        
    if not os.path.exists(creds_file):
        print(f"❌ Credentials file not found: {creds_file}")
        return False
        
    print(f"✅ Found credentials: {creds_file}")
    
    config = {
        'embedding': {
            'providers': ['vertex_ai'],
            'vertex_ai': {
                'enabled': True,
                'model': 'textembedding-gecko@003',
                'project_id': os.environ.get('GOOGLE_CLOUD_PROJECT', 'test-project')
            }
        }
    }
    
    try:
        service = create_embedding_service(config)
        result = await service.generate_embedding("Test philosophical concept: Being and Time")
        print(f"✅ Vertex AI result: {len(result)} dimensions, sample: {result[:5]}")
        return True
    except Exception as e:
        print(f"❌ Vertex AI failed: {str(e)}")
        return False

async def test_openai():
    """Test OpenAI provider"""
    print("\nTesting OpenAI Provider...")
    
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY not set")
        return False
        
    print("✅ Found OpenAI API key")
    
    config = {
        'embedding': {
            'providers': ['openai'],
            'openai': {
                'enabled': True,
                'model': 'text-embedding-3-small',
                'api_key': api_key
            }
        }
    }
    
    try:
        service = create_embedding_service(config)
        result = await service.generate_embedding("Test philosophical concept: Dialectical materialism")
        print(f"✅ OpenAI result: {len(result)} dimensions, sample: {result[:5]}")
        return True
    except Exception as e:
        print(f"❌ OpenAI failed: {str(e)}")
        return False

async def test_litellm_installation():
    """Test LiteLLM is properly installed"""
    print("\nTesting LiteLLM Installation...")
    try:
        import litellm
        version = getattr(litellm, '__version__', 'unknown')
        print(f"✅ LiteLLM version: {version}")
        
        # Test a simple embedding call
        # This will fail without credentials but should show LiteLLM is working
        try:
            await litellm.aembedding(
                model="text-embedding-3-small",
                input=["test"],
                api_key="fake-key"
            )
        except Exception as e:
            if "api_key" in str(e).lower() or "unauthorized" in str(e).lower():
                print("✅ LiteLLM working (expected auth error)")
                return True
            else:
                print(f"❌ LiteLLM error: {str(e)}")
                return False
                
    except ImportError:
        print("❌ LiteLLM not installed")
        return False

async def main():
    """Run all tests"""
    print("=== Direct API Integration Testing ===\n")
    
    results = {}
    
    # Test LiteLLM installation first
    results['litellm'] = await test_litellm_installation()
    
    # Test mock provider (should always work)
    results['mock'] = await test_mock_provider()
    
    # Test cloud providers if credentials available
    results['vertex_ai'] = await test_vertex_ai()
    results['openai'] = await test_openai()
    
    # Summary
    print(f"\n=== Test Results ===")
    for provider, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{provider.upper()}: {status}")
    
    # Critical assessment
    if results['mock'] and results['litellm']:
        print("\n✅ Core infrastructure working")
    else:
        print("\n❌ Critical infrastructure issues")
        
    working_providers = sum(1 for success in results.values() if success)
    print(f"\nWorking providers: {working_providers}/{len(results)}")

if __name__ == "__main__":
    asyncio.run(main())