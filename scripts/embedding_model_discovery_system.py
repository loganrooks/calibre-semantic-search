#!/usr/bin/env python3
"""
Comprehensive embedding model discovery system using LiteLLM
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

try:
    import litellm
    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False


@dataclass
class EmbeddingModelInfo:
    """Information about an embedding model"""
    name: str
    provider: str
    dimensions: Optional[int]
    max_tokens: Optional[int] 
    cost_per_token: Optional[float]
    supports_batch: bool = True
    prefix_format: Optional[str] = None
    api_key_required: bool = True
    special_params: Dict[str, Any] = None

    def __post_init__(self):
        if self.special_params is None:
            self.special_params = {}


class EmbeddingModelDiscovery:
    """Dynamic embedding model discovery using LiteLLM"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._static_models = None
        self._model_cache = {}
        
    async def discover_all_models(self) -> Dict[str, List[EmbeddingModelInfo]]:
        """Discover all available embedding models by provider"""
        
        if not LITELLM_AVAILABLE:
            self.logger.warning("LiteLLM not available, returning empty results")
            return {}
        
        models_by_provider = {}
        
        # Get static model list from LiteLLM
        static_models = self._get_static_models()
        
        # Process each model
        for model_name in static_models:
            try:
                model_info = await self._get_model_info(model_name)
                if model_info:
                    provider = model_info.provider
                    if provider not in models_by_provider:
                        models_by_provider[provider] = []
                    models_by_provider[provider].append(model_info)
                    
            except Exception as e:
                self.logger.warning(f"Failed to get info for model {model_name}: {e}")
        
        # Add known models that might not be in static list
        self._add_known_models(models_by_provider)
        
        return models_by_provider
    
    def _get_static_models(self) -> List[str]:
        """Get static list of embedding models from LiteLLM"""
        
        if self._static_models is not None:
            return self._static_models
            
        try:
            self._static_models = litellm.all_embedding_models.copy()
            self.logger.info(f"Found {len(self._static_models)} static embedding models")
            return self._static_models
        except Exception as e:
            self.logger.error(f"Failed to get static models: {e}")
            return []
    
    async def _get_model_info(self, model_name: str) -> Optional[EmbeddingModelInfo]:
        """Get detailed information about a specific model"""
        
        # Check cache first
        if model_name in self._model_cache:
            return self._model_cache[model_name]
        
        try:
            info = litellm.get_model_info(model_name)
            
            model_info = EmbeddingModelInfo(
                name=model_name,
                provider=info.get('litellm_provider', 'unknown'),
                dimensions=info.get('output_vector_size'),
                max_tokens=info.get('max_tokens'),
                cost_per_token=info.get('input_cost_per_token'),
                supports_batch=True,  # Most do
                api_key_required=True  # Most do
            )
            
            # Add provider-specific enhancements
            self._enhance_model_info(model_info, info)
            
            # Cache the result
            self._model_cache[model_name] = model_info
            
            return model_info
            
        except Exception as e:
            self.logger.warning(f"Failed to get model info for {model_name}: {e}")
            return None
    
    def _enhance_model_info(self, model_info: EmbeddingModelInfo, raw_info: Dict[str, Any]):
        """Add provider-specific enhancements to model info"""
        
        provider = model_info.provider
        
        if provider == 'openai':
            model_info.prefix_format = f"openai/{model_info.name}"
            model_info.special_params = {
                'supports_dimensions_param': model_info.name in ['text-embedding-3-small', 'text-embedding-3-large']
            }
            
        elif provider == 'vertex_ai' or 'vertex' in provider:
            model_info.prefix_format = f"vertex_ai/{model_info.name}"
            model_info.special_params = {
                'requires_project_id': True,
                'requires_location': True,
                'default_location': 'us-central1'
            }
            model_info.api_key_required = False  # Uses service account
            
        elif provider == 'cohere':
            model_info.prefix_format = f"cohere/{model_info.name}"
            model_info.special_params = {
                'supports_input_type': True,
                'input_types': ['search_document', 'search_query', 'classification', 'clustering']
            }
            
        elif provider == 'bedrock' or 'bedrock' in provider:
            model_info.prefix_format = f"bedrock/{model_info.name}"
            model_info.special_params = {
                'requires_aws_credentials': True,
                'region_dependent': True
            }
            model_info.api_key_required = False  # Uses AWS credentials
            
        elif 'fireworks' in provider:
            model_info.prefix_format = model_info.name  # Already has prefix
            model_info.special_params = {
                'requires_fireworks_api_key': True
            }
    
    def _add_known_models(self, models_by_provider: Dict[str, List[EmbeddingModelInfo]]):
        """Add known models that might not be in the static list"""
        
        # Add newer OpenAI models
        if 'openai' not in models_by_provider:
            models_by_provider['openai'] = []
            
        known_openai = [
            ('text-embedding-3-small', 1536),
            ('text-embedding-3-large', 3072),
            ('text-embedding-ada-002', 1536)
        ]
        
        existing_openai = {model.name for model in models_by_provider['openai']}
        
        for model_name, dimensions in known_openai:
            if model_name not in existing_openai:
                model_info = EmbeddingModelInfo(
                    name=model_name,
                    provider='openai',
                    dimensions=dimensions,
                    max_tokens=8191,
                    cost_per_token=1e-7,
                    prefix_format=f"openai/{model_name}"
                )
                models_by_provider['openai'].append(model_info)
    
    async def validate_model(self, model_name: str, api_key: Optional[str] = None) -> Dict[str, Any]:
        """Validate if a model is available and working"""
        
        result = {
            'model': model_name,
            'valid': False,
            'provider': None,
            'error': None,
            'dimensions': None
        }
        
        try:
            # First check if model exists in LiteLLM
            info = litellm.get_model_info(model_name)
            result['provider'] = info.get('litellm_provider')
            result['dimensions'] = info.get('output_vector_size')
            result['valid'] = True
            result['metadata_available'] = True
            
            # Could add actual API test here if API key provided
            if api_key:
                # result['api_test'] = await self._test_api_call(model_name, api_key)
                pass
                
        except Exception as e:
            result['error'] = str(e)
            result['metadata_available'] = False
        
        return result
    
    async def get_models_for_provider(self, provider: str) -> List[EmbeddingModelInfo]:
        """Get all models for a specific provider"""
        
        all_models = await self.discover_all_models()
        return all_models.get(provider, [])
    
    async def find_best_model_for_use_case(self, 
                                         use_case: str,
                                         max_dimensions: Optional[int] = None,
                                         preferred_provider: Optional[str] = None) -> List[EmbeddingModelInfo]:
        """Find best models for a specific use case"""
        
        all_models = await self.discover_all_models()
        candidates = []
        
        for provider, models in all_models.items():
            if preferred_provider and provider != preferred_provider:
                continue
                
            for model in models:
                # Filter by dimensions if specified
                if max_dimensions and model.dimensions and model.dimensions > max_dimensions:
                    continue
                
                # Score model based on use case
                score = self._score_model_for_use_case(model, use_case)
                candidates.append((score, model))
        
        # Sort by score (higher is better)
        candidates.sort(key=lambda x: x[0], reverse=True)
        
        return [model for score, model in candidates[:5]]  # Top 5
    
    def _score_model_for_use_case(self, model: EmbeddingModelInfo, use_case: str) -> float:
        """Score a model for a specific use case"""
        
        score = 0.0
        
        # Philosophy/academic texts (our use case)
        if use_case == 'academic':
            # Prefer larger dimensions for complex concepts
            if model.dimensions:
                if model.dimensions >= 1000:
                    score += 2.0
                elif model.dimensions >= 500:
                    score += 1.0
            
            # Prefer certain providers
            if model.provider == 'openai':
                score += 1.5
            elif model.provider == 'vertex_ai':
                score += 1.2
            
            # Prefer models that support longer texts
            if model.max_tokens and model.max_tokens >= 8000:
                score += 1.0
        
        return score
    
    def get_model_usage_example(self, model_info: EmbeddingModelInfo) -> Dict[str, Any]:
        """Get usage example for a specific model"""
        
        example = {
            'model_string': model_info.prefix_format or model_info.name,
            'required_params': {},
            'optional_params': {},
            'example_code': None
        }
        
        if model_info.provider == 'openai':
            example['required_params']['api_key'] = 'your_openai_api_key'
            example['example_code'] = f"""
from litellm import aembedding

response = await aembedding(
    model="{model_info.prefix_format or model_info.name}",
    input="Your text here",
    api_key="your_openai_api_key"
)
embedding = response['data'][0]['embedding']
"""
        
        elif 'vertex' in model_info.provider:
            example['required_params']['vertex_project'] = 'your_gcp_project_id'
            example['optional_params']['vertex_location'] = 'us-central1'
            example['example_code'] = f"""
from litellm import aembedding

response = await aembedding(
    model="{model_info.prefix_format or model_info.name}",
    input="Your text here",
    vertex_project="your_gcp_project_id",
    vertex_location="us-central1"
)
embedding = response['data'][0]['embedding']
"""
        
        elif model_info.provider == 'cohere':
            example['required_params']['api_key'] = 'your_cohere_api_key'
            example['optional_params']['input_type'] = 'search_document'
            example['example_code'] = f"""
from litellm import aembedding

response = await aembedding(
    model="{model_info.prefix_format or model_info.name}",
    input="Your text here",
    api_key="your_cohere_api_key",
    input_type="search_document"
)
embedding = response['data'][0]['embedding']
"""
        
        return example


async def main():
    """Demonstration of the discovery system"""
    
    if not LITELLM_AVAILABLE:
        print("LiteLLM not available - install with: pip install litellm")
        return
    
    discovery = EmbeddingModelDiscovery()
    
    print("=== DISCOVERING ALL EMBEDDING MODELS ===")
    all_models = await discovery.discover_all_models()
    
    for provider, models in all_models.items():
        print(f"\n{provider.upper()} ({len(models)} models):")
        for model in models[:3]:  # Show first 3 per provider
            print(f"  {model.name}")
            print(f"    Dimensions: {model.dimensions}")
            print(f"    Max tokens: {model.max_tokens}")
            print(f"    Format: {model.prefix_format}")
    
    print("\n=== FINDING BEST MODELS FOR ACADEMIC USE ===")
    best_models = await discovery.find_best_model_for_use_case('academic')
    
    for model in best_models:
        print(f"\n{model.name} ({model.provider}):")
        print(f"  Dimensions: {model.dimensions}")
        print(f"  Max tokens: {model.max_tokens}")
        
        example = discovery.get_model_usage_example(model)
        print(f"  Usage: {example['model_string']}")
    
    # Save comprehensive results
    results = {
        'discovered_models': {
            provider: [
                {
                    'name': model.name,
                    'provider': model.provider,
                    'dimensions': model.dimensions,
                    'max_tokens': model.max_tokens,
                    'prefix_format': model.prefix_format,
                    'special_params': model.special_params
                }
                for model in models
            ]
            for provider, models in all_models.items()
        },
        'best_for_academic': [
            {
                'name': model.name,
                'provider': model.provider,
                'dimensions': model.dimensions,
                'usage_example': discovery.get_model_usage_example(model)
            }
            for model in best_models
        ]
    }
    
    with open('comprehensive_model_discovery.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\nSaved comprehensive results to 'comprehensive_model_discovery.json'")


if __name__ == "__main__":
    asyncio.run(main())