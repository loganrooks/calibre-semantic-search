#!/usr/bin/env python3
"""
Test script to examine LiteLLM's embedding model information
"""

import json
import pprint

try:
    import litellm
    print("LiteLLM imported successfully")
    
    # Check all_embedding_models
    print("\n=== ALL EMBEDDING MODELS ===")
    if hasattr(litellm, 'all_embedding_models'):
        models = litellm.all_embedding_models
        print(f"Type: {type(models)}")
        print(f"Length: {len(models)}")
        print("Sample models:")
        for i, model in enumerate(models[:10]):  # First 10
            print(f"  {i+1}: {model}")
        
        # Look for specific providers
        print("\nOpenAI models:")
        openai_models = [m for m in models if 'openai' in str(m).lower()]
        for model in openai_models[:5]:
            print(f"  {model}")
            
        print("\nVertex AI models:")
        vertex_models = [m for m in models if 'vertex' in str(m).lower() or 'google' in str(m).lower()]
        for model in vertex_models[:5]:
            print(f"  {model}")
            
        print("\nCohere models:")
        cohere_models = [m for m in models if 'cohere' in str(m).lower()]
        for model in cohere_models[:5]:
            print(f"  {model}")
    
    # Check model_cost_map
    print("\n=== MODEL COST MAP ===")
    if hasattr(litellm, 'model_cost_map'):
        cost_map = litellm.model_cost_map
        print(f"Type: {type(cost_map)}")
        print(f"Keys count: {len(cost_map.keys()) if isinstance(cost_map, dict) else 'Not a dict'}")
        
        if isinstance(cost_map, dict):
            # Look for embedding models in cost map
            embedding_costs = {}
            for model_name, model_info in cost_map.items():
                if 'embed' in model_name.lower():
                    embedding_costs[model_name] = model_info
            
            print(f"\nEmbedding models in cost map: {len(embedding_costs)}")
            for model_name, info in list(embedding_costs.items())[:5]:
                print(f"  {model_name}: {info}")
    
    # Check for get_model_cost_map function
    print("\n=== GET MODEL COST MAP FUNCTION ===")
    if hasattr(litellm, 'get_model_cost_map'):
        func = litellm.get_model_cost_map
        print(f"Function available: {func}")
        try:
            result = func()
            print(f"Function result type: {type(result)}")
            if isinstance(result, dict):
                print(f"Result keys count: {len(result)}")
        except Exception as e:
            print(f"Error calling function: {e}")
    
    # Check for specific model info functions
    print("\n=== MODEL INFO FUNCTIONS ===")
    info_functions = ['get_model_info', 'get_llm_provider', 'get_supported_openai_params']
    
    for func_name in info_functions:
        if hasattr(litellm, func_name):
            func = getattr(litellm, func_name)
            print(f"\n{func_name}: {func}")
            
            # Try calling with an embedding model
            test_models = [
                'text-embedding-ada-002',
                'text-embedding-3-small',
                'openai/text-embedding-ada-002',
                'vertex_ai/textembedding-gecko'
            ]
            
            for model in test_models:
                try:
                    result = func(model)
                    print(f"  {model}: {result}")
                    break  # If one works, show example
                except Exception as e:
                    print(f"  {model}: Error - {e}")
    
    # Check provider lists
    print("\n=== PROVIDER LISTS ===")
    provider_attrs = [
        'openai_models',
        'vertex_ai_models', 
        'cohere_models',
        'azure_models',
        'anthropic_models'
    ]
    
    for attr in provider_attrs:
        if hasattr(litellm, attr):
            models = getattr(litellm, attr)
            print(f"\n{attr}: {type(models)}")
            if isinstance(models, list):
                print(f"  Count: {len(models)}")
                # Look for embedding models
                embedding_models = [m for m in models if 'embed' in str(m).lower()]
                if embedding_models:
                    print(f"  Embedding models: {embedding_models[:3]}")
    
    # Try to understand model string format
    print("\n=== MODEL STRING FORMATS ===")
    if hasattr(litellm, 'all_embedding_models'):
        models = litellm.all_embedding_models
        formats = {}
        for model in models[:20]:  # Sample
            if '/' in str(model):
                provider = str(model).split('/')[0]
                if provider not in formats:
                    formats[provider] = []
                formats[provider].append(str(model))
        
        for provider, provider_models in formats.items():
            print(f"\n{provider} format:")
            for model in provider_models[:3]:
                print(f"  {model}")
    
except ImportError as e:
    print(f"LiteLLM not available: {e}")

print("\n=== Analysis Complete ===")