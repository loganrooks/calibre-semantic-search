#!/usr/bin/env python3
"""
Detailed examination of LiteLLM model information for embedding models
"""

import json
import pprint

try:
    import litellm
    
    print("=== EMBEDDING MODEL DETAILS ===")
    
    # Get all embedding models
    all_models = litellm.all_embedding_models
    print(f"Total embedding models: {len(all_models)}")
    print("\nAll embedding models:")
    for i, model in enumerate(all_models):
        print(f"  {i+1:2d}: {model}")
    
    # Test get_model_info for each embedding model
    print("\n=== MODEL INFO DETAILS ===")
    model_info_map = {}
    
    for model in all_models:
        try:
            info = litellm.get_model_info(model)
            model_info_map[model] = info
            
            # Extract key information
            provider = info.get('litellm_provider', 'unknown')
            dimensions = info.get('output_vector_size', 'unknown')
            max_tokens = info.get('max_tokens', 'unknown')
            
            print(f"\n{model}:")
            print(f"  Provider: {provider}")
            print(f"  Dimensions: {dimensions}")
            print(f"  Max tokens: {max_tokens}")
            
            # Show any other interesting fields
            for key, value in info.items():
                if key in ['supports_vision', 'supports_function_calling', 'mode']:
                    print(f"  {key}: {value}")
                    
        except Exception as e:
            print(f"\n{model}: Error - {e}")
    
    # Create provider mapping
    print("\n=== PROVIDER MAPPING ===")
    providers = {}
    for model, info in model_info_map.items():
        provider = info.get('litellm_provider', 'unknown')
        if provider not in providers:
            providers[provider] = []
        providers[provider].append({
            'model': model,
            'dimensions': info.get('output_vector_size'),
            'max_tokens': info.get('max_tokens')
        })
    
    for provider, models in providers.items():
        print(f"\n{provider.upper()}:")
        for model_data in models:
            print(f"  {model_data['model']} (dim: {model_data['dimensions']}, max: {model_data['max_tokens']})")
    
    # Test get_llm_provider function
    print("\n=== PROVIDER DETECTION ===")
    if hasattr(litellm, 'get_llm_provider'):
        test_models = [
            'text-embedding-ada-002',
            'openai/text-embedding-ada-002', 
            'vertex_ai/textembedding-gecko',
            'cohere/embed-english-v3.0',
            'azure/text-embedding-ada-002'
        ]
        
        for model in test_models:
            try:
                provider_info = litellm.get_llm_provider(model)
                print(f"  {model}: {provider_info}")
            except Exception as e:
                print(f"  {model}: Error - {e}")
    
    # Check if there are more models available through provider-specific calls
    print("\n=== CHECKING PROVIDER-SPECIFIC MODEL LISTS ===")
    
    # Check vertex AI models
    if hasattr(litellm, 'vertex_ai_models'):
        vertex_models = litellm.vertex_ai_models
        print(f"\nVertex AI models: {len(vertex_models) if isinstance(vertex_models, list) else 'Not a list'}")
        if isinstance(vertex_models, list):
            embedding_models = [m for m in vertex_models if 'embed' in str(m).lower()]
            print(f"  Embedding models: {embedding_models}")
    
    # Check OpenAI models  
    if hasattr(litellm, 'openai_models'):
        openai_models = litellm.openai_models
        print(f"\nOpenAI models: {len(openai_models) if isinstance(openai_models, list) else 'Not a list'}")
        if isinstance(openai_models, list):
            embedding_models = [m for m in openai_models if 'embed' in str(m).lower()]
            print(f"  Embedding models: {embedding_models}")
    
    # Save detailed info to JSON for reference
    print("\n=== SAVING DETAILED INFO ===")
    output = {
        'all_embedding_models': all_models,
        'model_details': model_info_map,
        'provider_summary': providers
    }
    
    with open('litellm_embedding_models.json', 'w') as f:
        json.dump(output, f, indent=2, default=str)
    print("Saved detailed model information to 'litellm_embedding_models.json'")
    
    # Test dynamic provider string construction
    print("\n=== DYNAMIC PROVIDER TESTING ===")
    provider_prefixes = ['openai', 'vertex_ai', 'cohere', 'azure', 'bedrock']
    base_models = ['text-embedding-ada-002', 'textembedding-gecko', 'embed-english-v3.0']
    
    for prefix in provider_prefixes:
        for base_model in base_models:
            full_model = f"{prefix}/{base_model}"
            try:
                info = litellm.get_model_info(full_model)
                print(f"✓ {full_model}: {info.get('litellm_provider', 'unknown')}")
            except Exception as e:
                print(f"✗ {full_model}: {str(e)[:50]}")
    
except ImportError as e:
    print(f"LiteLLM not available: {e}")

print("\n=== Analysis Complete ===")