#!/usr/bin/env python3
"""
Test script to explore LiteLLM's model discovery capabilities
"""

import sys
import json
import inspect

try:
    import litellm
    print("LiteLLM imported successfully")
    
    # Try to get version
    try:
        print(f"LiteLLM version: {litellm.__version__}")
    except AttributeError:
        try:
            import pkg_resources
            version = pkg_resources.get_distribution("litellm").version
            print(f"LiteLLM version: {version}")
        except:
            print("Version information not available")
    
    # Check what functions and constants are available
    print("\n=== LiteLLM Available Functions and Constants ===")
    
    # Look for model-related functions
    model_functions = []
    for name in dir(litellm):
        obj = getattr(litellm, name)
        if 'model' in name.lower() or 'provider' in name.lower():
            model_functions.append((name, type(obj)))
    
    print("Model-related functions/constants:")
    for name, obj_type in sorted(model_functions):
        print(f"  {name}: {obj_type}")
    
    # Check for specific discovery functions
    discovery_candidates = [
        'model_list',
        'get_model_info',
        'get_supported_models',
        'list_models',
        'model_cost_map',
        'get_model_cost_map',
        'supported_models',
        'model_fallbacks',
        'provider_list',
        'get_providers',
        'embedding_models'
    ]
    
    print("\n=== Checking for Discovery Functions ===")
    available_functions = []
    for func_name in discovery_candidates:
        if hasattr(litellm, func_name):
            func = getattr(litellm, func_name)
            available_functions.append((func_name, func))
            print(f"✓ Found: {func_name} - {type(func)}")
        else:
            print(f"✗ Not found: {func_name}")
    
    # Try to call available functions
    print("\n=== Testing Available Functions ===")
    for func_name, func in available_functions:
        try:
            if callable(func):
                print(f"\nTesting {func_name}():")
                # Get function signature
                try:
                    sig = inspect.signature(func)
                    print(f"  Signature: {sig}")
                    
                    # Try calling with no arguments
                    if len(sig.parameters) == 0:
                        result = func()
                        print(f"  Result type: {type(result)}")
                        if isinstance(result, (dict, list)) and len(str(result)) < 1000:
                            print(f"  Result: {result}")
                        else:
                            print(f"  Result size: {len(str(result))} characters")
                    else:
                        print(f"  Requires parameters: {list(sig.parameters.keys())}")
                        
                except Exception as e:
                    print(f"  Error calling {func_name}: {e}")
            else:
                # It's a constant/variable
                print(f"\n{func_name} value:")
                if isinstance(func, (dict, list)) and len(str(func)) < 2000:
                    print(f"  {func}")
                else:
                    print(f"  Type: {type(func)}, Size: {len(str(func))} characters")
                    
        except Exception as e:
            print(f"Error with {func_name}: {e}")
    
    # Check for embedding-specific constants/mappings
    print("\n=== Checking for Embedding Model Information ===")
    embedding_attrs = []
    for name in dir(litellm):
        if 'embed' in name.lower():
            embedding_attrs.append(name)
    
    for attr in embedding_attrs:
        try:
            value = getattr(litellm, attr)
            print(f"{attr}: {type(value)}")
            if isinstance(value, dict) and len(str(value)) < 1000:
                print(f"  {value}")
        except Exception as e:
            print(f"Error accessing {attr}: {e}")
    
    # Try to test a simple embedding call to see response structure
    print("\n=== Testing Embedding Response Structure ===")
    try:
        # Use mock/test to see structure without API call
        print("Testing with a minimal embedding call (this may fail without API key)...")
        # This will likely fail but might show us the expected structure
        
    except Exception as e:
        print(f"Expected error (no API key): {e}")
    
    # Look for any hidden model information in the module
    print("\n=== Looking for Hidden Model Constants ===")
    for name in dir(litellm):
        if not name.startswith('_'):
            continue
        obj = getattr(litellm, name)
        if isinstance(obj, dict) and ('model' in str(obj).lower() or 'embed' in str(obj).lower()):
            print(f"Found potential model dict: {name}")
            if len(str(obj)) < 1000:
                print(f"  {obj}")
            else:
                print(f"  Size: {len(str(obj))} characters")
    
except ImportError as e:
    print(f"LiteLLM not available: {e}")
    print("Install with: pip install litellm")
    sys.exit(1)

print("\n=== Discovery Complete ===")