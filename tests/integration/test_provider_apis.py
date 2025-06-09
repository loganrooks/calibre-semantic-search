#!/usr/bin/env python3
"""
Test provider-specific API discovery functions in LiteLLM
"""

import inspect

try:
    import litellm
    
    print("=== PROVIDER-SPECIFIC FUNCTIONS ===")
    
    # Look for provider-specific model listing functions
    provider_functions = []
    
    for name in dir(litellm):
        obj = getattr(litellm, name)
        if callable(obj) and ('provider' in name.lower() or 'models' in name.lower() or 'list' in name.lower()):
            provider_functions.append((name, obj))
    
    print("Provider/model listing functions:")
    for name, func in provider_functions:
        try:
            sig = inspect.signature(func)
            print(f"  {name}{sig}")
        except:
            print(f"  {name}: {type(func)}")
    
    # Check for specific provider model discovery
    print("\n=== TESTING PROVIDER DISCOVERY FUNCTIONS ===")
    
    discovery_functions = [
        'get_llm_provider',
        'get_supported_openai_params', 
        'alist_models',
        'list_models',
        'get_available_models'
    ]
    
    for func_name in discovery_functions:
        if hasattr(litellm, func_name):
            func = getattr(litellm, func_name)
            print(f"\n{func_name}:")
            try:
                sig = inspect.signature(func)
                print(f"  Signature: {sig}")
                
                # Try calling with common parameters
                if func_name == 'get_llm_provider':
                    test_models = ['text-embedding-ada-002', 'openai/text-embedding-ada-002']
                    for model in test_models:
                        try:
                            result = func(model)
                            print(f"  {model}: {result}")
                        except Exception as e:
                            print(f"  {model}: Error - {e}")
                
                elif func_name == 'get_supported_openai_params':
                    test_models = ['text-embedding-ada-002']
                    for model in test_models:
                        try:
                            result = func(model)
                            print(f"  {model}: {result}")
                        except Exception as e:
                            print(f"  {model}: Error - {e}")
                
            except Exception as e:
                print(f"  Error: {e}")
    
    # Check for any hidden model discovery APIs
    print("\n=== HIDDEN APIS ===")
    
    hidden_funcs = []
    for name in dir(litellm):
        if name.startswith('_') and ('model' in name.lower() or 'provider' in name.lower()):
            obj = getattr(litellm, name)
            if callable(obj):
                hidden_funcs.append((name, obj))
    
    for name, func in hidden_funcs[:10]:  # Show first 10
        try:
            sig = inspect.signature(func)
            print(f"  {name}{sig}")
        except:
            print(f"  {name}: {type(func)}")
    
    # Test if we can call OpenAI API directly through LiteLLM
    print("\n=== DIRECT API TESTING ===")
    
    # Check if there's a way to test connections without full API calls
    if hasattr(litellm, 'validate'):
        print("Found validate function")
    if hasattr(litellm, 'check_valid_key'):
        print("Found check_valid_key function") 
    if hasattr(litellm, 'test_connection'):
        print("Found test_connection function")
    
    # Look for any configuration objects that might have model lists
    print("\n=== CONFIGURATION OBJECTS ===")
    
    config_objects = []
    for name in dir(litellm):
        obj = getattr(litellm, name)
        if hasattr(obj, '__dict__') and ('config' in name.lower() or 'settings' in name.lower()):
            config_objects.append((name, obj))
    
    for name, obj in config_objects:
        print(f"\n{name}:")
        if hasattr(obj, '__dict__'):
            for attr, value in obj.__dict__.items():
                if 'model' in attr.lower():
                    print(f"  {attr}: {type(value)}")
    
    print("\n=== MODEL STRING GENERATION ===")
    
    # Test how to construct proper model strings for different providers
    providers = ['openai', 'vertex_ai', 'cohere', 'azure', 'bedrock']
    base_models = ['text-embedding-ada-002', 'textembedding-gecko', 'embed-english-v3.0']
    
    print("Testing model string formats:")
    for provider in providers:
        for base_model in base_models:
            # Test bare model name
            try:
                info = litellm.get_model_info(base_model)
                if info.get('litellm_provider') == provider:
                    print(f"  ✓ {base_model} → {provider}")
            except:
                pass
            
            # Test prefixed model name  
            prefixed = f"{provider}/{base_model}"
            try:
                info = litellm.get_model_info(prefixed)
                print(f"  ✓ {prefixed} → {info.get('litellm_provider')}")
            except:
                pass

except ImportError as e:
    print(f"LiteLLM not available: {e}")

print("\n=== ANALYSIS COMPLETE ===")