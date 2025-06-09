"""
Direct Vertex AI Provider for gemini-embedding-001

This provider bypasses LiteLLM to directly integrate with Google Cloud AI Platform,
enabling support for gemini-embedding-001 model which is not supported by LiteLLM.

Key Features:
- Direct google-cloud-aiplatform SDK integration
- gemini-embedding-001 model support
- Custom dimensionality (1-3072) via output_dimensionality parameter
- Proper Google Cloud authentication handling
- Sequential batch processing (gemini limitation)
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
import os

from .base import BaseEmbeddingProvider

logger = logging.getLogger(__name__)

# Model specifications for Vertex AI models
VERTEX_AI_MODEL_SPECS = {
    "gemini-embedding-001": {
        "max_dimensions": 3072,
        "default_dimensions": 768,
        "supports_batch": False,  # gemini requires single input per request
        "max_input_tokens": 2048
    },
    "text-embedding-004": {
        "max_dimensions": 768,
        "default_dimensions": 768,
        "supports_batch": True,
        "max_input_tokens": 20000
    }
}


class DirectVertexAIProvider(BaseEmbeddingProvider):
    """
    Direct Vertex AI embedding provider using google-cloud-aiplatform SDK.
    
    Specifically designed to support gemini-embedding-001 and other Vertex AI
    models with full control over dimensionality and authentication.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Direct Vertex AI provider.
        
        Required config keys:
        - model: Vertex AI model name (e.g., "gemini-embedding-001")
        - project_id: Google Cloud project ID
        - location: Google Cloud location (e.g., "us-central1")
        - dimensions: Output embedding dimensions
        
        Optional config keys:
        - service_account_key: Path to service account JSON key file
        - credentials: Google Cloud credentials object
        """
        super().__init__(config)
        
        # Validate required configuration
        self.model = config.get("model")
        if not self.model:
            raise ValueError("model is required for DirectVertexAIProvider")
        
        self.project_id = config.get("project_id")
        if not self.project_id:
            raise ValueError("project_id is required for DirectVertexAIProvider")
        
        self.location = config.get("location")
        if not self.location:
            raise ValueError("location is required for DirectVertexAIProvider")
        
        # Validate and set dimensions
        self.dimensions = config.get("dimensions")
        if not self.dimensions:
            # Use default for model
            model_spec = VERTEX_AI_MODEL_SPECS.get(self.model, {})
            self.dimensions = model_spec.get("default_dimensions", 768)
        
        # Validate dimension limits
        model_spec = VERTEX_AI_MODEL_SPECS.get(self.model, {})
        max_dims = model_spec.get("max_dimensions", 3072)
        
        if not isinstance(self.dimensions, int) or self.dimensions < 1 or self.dimensions > max_dims:
            raise ValueError(f"dimensions must be between 1 and {max_dims} for model {self.model}")
        
        # Authentication configuration
        self.service_account_key = config.get("service_account_key")
        self.credentials = config.get("credentials")
        
        # Model capabilities
        self.model_spec = model_spec
        self.supports_batch = model_spec.get("supports_batch", True)
        self.max_input_tokens = model_spec.get("max_input_tokens", 8192)
        
        # Initialize Google Cloud AI Platform client (lazy loading)
        self._client = None
        self._model_instance = None
        
        logger.info(f"DirectVertexAIProvider initialized: model={self.model}, "
                   f"dimensions={self.dimensions}, project={self.project_id}, "
                   f"location={self.location}")
    
    async def _get_model_instance(self):
        """Lazy load and return the Vertex AI model instance"""
        if self._model_instance is None:
            try:
                # Import here to avoid issues if google-cloud-aiplatform not installed
                import google.cloud.aiplatform as aiplatform
                from google.cloud.aiplatform import TextEmbeddingModel
                
                # Initialize Vertex AI
                aiplatform.init(
                    project=self.project_id,
                    location=self.location,
                    credentials=self.credentials
                )
                
                # Get the model
                self._model_instance = TextEmbeddingModel.from_pretrained(self.model)
                
                logger.debug(f"Vertex AI model instance created: {self.model}")
                
            except ImportError as e:
                raise ImportError(
                    "google-cloud-aiplatform is required for DirectVertexAIProvider. "
                    "Install with: pip install google-cloud-aiplatform"
                ) from e
            except Exception as e:
                logger.error(f"Failed to initialize Vertex AI model {self.model}: {e}")
                raise
        
        return self._model_instance
    
    async def _call_vertex_ai_api(self, text: str) -> List[float]:
        """Make direct API call to Vertex AI for single text embedding"""
        try:
            model = await self._get_model_instance()
            
            # Prepare the embedding request
            # For gemini-embedding-001, we use get_embeddings with output_dimensionality
            if self.model == "gemini-embedding-001":
                # Import here to handle the specific types
                from google.cloud.aiplatform import TextEmbeddingInput
                
                # Create input with task type for better embeddings
                embedding_input = TextEmbeddingInput(
                    text=text,
                    task_type="RETRIEVAL_DOCUMENT"  # Optimized for search/retrieval
                )
                
                # Call with output dimensionality
                embeddings = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: model.get_embeddings(
                        [embedding_input],
                        output_dimensionality=self.dimensions
                    )
                )
            else:
                # For other models, use standard approach
                embeddings = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: model.get_embeddings([text])
                )
            
            # Extract the embedding vector
            if embeddings and len(embeddings) > 0:
                embedding_vector = embeddings[0].values
                
                # Validate dimensions
                if len(embedding_vector) != self.dimensions:
                    logger.warning(
                        f"Received embedding dimension {len(embedding_vector)} "
                        f"doesn't match configured {self.dimensions}. "
                        f"This might indicate a configuration issue."
                    )
                
                return list(embedding_vector)
            else:
                raise ValueError(f"No embedding returned from Vertex AI for text: {text[:50]}...")
                
        except Exception as e:
            logger.error(f"Vertex AI API call failed for model {self.model}: {e}")
            raise
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        if not text or not text.strip():
            logger.warning("Empty text provided to generate_embedding")
            return [0.0] * self.dimensions
        
        # Truncate text if too long
        text = self._truncate_text(text)
        
        try:
            embedding = await self._call_vertex_ai_api(text)
            
            logger.debug(f"Generated embedding for text length {len(text)}, "
                        f"embedding dimensions: {len(embedding)}")
            
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
    
    async def generate_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        For gemini-embedding-001, this makes sequential calls since the model
        doesn't support batching. For other models, we can optimize this.
        """
        if not texts:
            return []
        
        # Filter and truncate texts
        processed_texts = []
        for text in texts:
            if text and text.strip():
                processed_texts.append(self._truncate_text(text))
            else:
                processed_texts.append("")  # Keep empty for consistent indexing
        
        try:
            if self.supports_batch and len(processed_texts) > 1:
                # For models that support batching
                logger.debug(f"Batch processing {len(processed_texts)} texts")
                
                model = await self._get_model_instance()
                
                # Use batch processing
                embeddings = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: model.get_embeddings(processed_texts)
                )
                
                return [list(emb.values) for emb in embeddings]
                
            else:
                # Sequential processing for gemini-embedding-001 and small batches
                logger.debug(f"Sequential processing {len(processed_texts)} texts")
                
                results = []
                for text in processed_texts:
                    if text:
                        embedding = await self.generate_embedding(text)
                        results.append(embedding)
                    else:
                        # Return zero vector for empty texts
                        results.append([0.0] * self.dimensions)
                
                return results
                
        except Exception as e:
            logger.error(f"Batch embedding generation failed: {e}")
            # Fallback to base class sequential processing
            return await super().generate_batch(texts)
    
    def get_dimensions(self) -> int:
        """Get the embedding dimension count"""
        return self.dimensions
    
    def get_max_batch_size(self) -> int:
        """Get maximum batch size for this provider"""
        if self.model == "gemini-embedding-001":
            return 1  # gemini requires single input
        return 25  # Conservative batch size for other models
    
    def get_max_text_length(self) -> int:
        """Get maximum text length for this provider"""
        return self.max_input_tokens
    
    def get_model_name(self) -> str:
        """Get descriptive model name"""
        return f"vertex_ai_direct/{self.model}"
    
    def _truncate_text(self, text: str) -> str:
        """Truncate text to fit within model limits"""
        # Simple character-based truncation
        # In a production system, you might want token-based truncation
        max_chars = self.max_input_tokens * 4  # Rough estimate: 1 token ≈ 4 chars
        
        if len(text) > max_chars:
            logger.warning(f"Truncating text from {len(text)} to {max_chars} characters")
            return text[:max_chars]
        
        return text
    
    def __str__(self) -> str:
        return f"DirectVertexAIProvider(model={self.model}, dims={self.dimensions})"
    
    def __repr__(self) -> str:
        return (f"DirectVertexAIProvider(model='{self.model}', "
                f"project_id='{self.project_id}', location='{self.location}', "
                f"dimensions={self.dimensions})")