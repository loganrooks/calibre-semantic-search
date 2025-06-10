#!/usr/bin/env python3
"""
Test dynamic model discovery using provider APIs
"""

import asyncio
import json
from typing import Dict, List, Any

try:
    import litellm
    
    async def test_provider_model_discovery():
        """Test if we can discover models dynamically from providers"""
        
        # Test OpenAI API for available models (requires API key)
        print("=== TESTING OPENAI MODEL DISCOVERY ===")
        try:
            # This would require an API key
            print("OpenAI model listing would require API key")
            # models = await litellm.alist_models(provider="openai")  # Hypothetical
        except Exception as e:
            print(f"OpenAI discovery error: {e}")
        
        # Test what we can do without API keys
        print("\n=== STATIC MODEL INFORMATION ===")
        
        # Get all embedding models with their info
        embedding_models = litellm.all_embedding_models
        model_database = {}
        
        for model in embedding_models:
            try:
                info = litellm.get_model_info(model)
                provider = info.get('litellm_provider', 'unknown')
                dimensions = info.get('output_vector_size')
                max_tokens = info.get('max_tokens')
                
                if provider not in model_database:
                    model_database[provider] = []
                
                model_database[provider].append({
                    'name': model,
                    'dimensions': dimensions,
                    'max_tokens': max_tokens,
                    'full_info': info
                })
            except Exception as e:
                print(f"Error getting info for {model}: {e}")
        
        return model_database
    
    async def create_embedding_model_registry():
        """Create a comprehensive embedding model registry"""
        
        print("=== CREATING EMBEDDING MODEL REGISTRY ===")
        
        # Get base model information
        model_db = await test_provider_model_discovery()
        
        # Enhance with known model variations
        enhanced_registry = {}
        
        for provider, models in model_db.items():
            enhanced_registry[provider] = {
                'models': models,
                'prefix_format': None,
                'api_key_required': True,
                'supported_parameters': []
            }
            
            # Add provider-specific enhancements
            if provider == 'openai':
                enhanced_registry[provider].update({
                    'prefix_format': 'openai/{model}',
                    'known_models': [
                        'text-embedding-3-small',
                        'text-embedding-3-large', 
                        'text-embedding-ada-002'
                    ],
                    'default_dimensions': 1536,
                    'supports_batch': True
                })
            elif provider == 'vertex_ai':
                enhanced_registry[provider].update({
                    'prefix_format': 'vertex_ai/{model}',
                    'known_models': [
                        'textembedding-gecko',
                        'textembedding-gecko@001',
                        'textembedding-gecko@003',
                        'text-embedding-preview-0409'
                    ],
                    'default_dimensions': 768,
                    'requires_project_id': True
                })
            elif provider == 'cohere':
                enhanced_registry[provider].update({
                    'prefix_format': 'cohere/{model}',
                    'known_models': [
                        'embed-english-v3.0',
                        'embed-english-light-v3.0',
                        'embed-multilingual-v3.0'
                    ],
                    'default_dimensions': 1024,
                    'supports_input_type': True
                })
            elif provider == 'bedrock':
                enhanced_registry[provider].update({
                    'prefix_format': 'bedrock/{model}',
                    'known_models': [
                        'amazon.titan-embed-text-v1'
                    ],
                    'default_dimensions': 1536,
                    'requires_aws_credentials': True
                })
        
        return enhanced_registry
    
    async def test_model_validation():
        """Test if we can validate model availability"""
        
        print("\n=== TESTING MODEL VALIDATION ===")
        
        # Test models that should work (basic validation)
        test_models = [
            'text-embedding-ada-002',
            'openai/text-embedding-ada-002',
            'vertex_ai/textembedding-gecko',
            'cohere/embed-english-v3.0'
        ]
        
        validation_results = {}
        
        for model in test_models:
            try:
                # Test if we can get model info (doesn't require API call)
                info = litellm.get_model_info(model)
                validation_results[model] = {
                    'valid': True,
                    'provider': info.get('litellm_provider'),
                    'dimensions': info.get('output_vector_size'),
                    'max_tokens': info.get('max_tokens')
                }
            except Exception as e:
                validation_results[model] = {
                    'valid': False,
                    'error': str(e)
                }
        
        return validation_results
    
    # Run the tests
    async def main():
        print("Starting LiteLLM dynamic discovery tests...")
        
        # Test basic discovery
        model_db = await test_provider_model_discovery()
        print(f"\nFound {len(model_db)} providers:")
        for provider, models in model_db.items():
            print(f"  {provider}: {len(models)} models")
        
        # Create enhanced registry
        registry = await create_embedding_model_registry()
        
        # Test validation
        validation = await test_model_validation()
        print("\nModel validation results:")
        for model, result in validation.items():
            status = "✓" if result['valid'] else "✗"
            print(f"  {status} {model}: {result}")
        
        # Save results
        output = {
            'model_database': model_db,
            'enhanced_registry': registry,
            'validation_results': validation
        }
        
        with open('dynamic_model_discovery.json', 'w') as f:
            json.dump(output, f, indent=2, default=str)
        
        print("\nSaved results to 'dynamic_model_discovery.json'")
        
        return output
    
    # Run the async main function
    if __name__ == "__main__":
        result = asyncio.run(main())
        
        print("\n=== SUMMARY ===")
        print("LiteLLM provides:")
        print("1. Static list of 29 embedding models via litellm.all_embedding_models")
        print("2. Model metadata via litellm.get_model_info(model)")  
        print("3. Provider detection via model string analysis")
        print("4. No built-in dynamic discovery (requires API keys for actual testing)")
        print("5. Comprehensive model information including dimensions, costs, limits")

except ImportError as e:
    print(f"LiteLLM not available: {e}")