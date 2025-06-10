# Guide: Integrating LiteLLM into Calibre Semantic Search Plugin

**To:** AI Development Agent for `calibre-semantic-search`
**From:** @loganrooks
**Date:** 2025-06-05
**Subject:** Enhancing Embedding Provider Support with LiteLLM

## 1. Introduction

This document outlines a plan to integrate the LiteLLM library into the `calibre-semantic-search` Calibre plugin. The primary goal is to significantly expand the range of supported embedding models and providers with minimal per-provider integration effort, offering users greater flexibility and access to the latest models.

LiteLLM acts as a unified API interface to a wide array of LLM providers (OpenAI, Azure, Cohere, Hugging Face, Vertex AI, Bedrock, etc.), including many embedding models. By integrating LiteLLM, we can abstract away the complexities of individual provider SDKs.

## 2. Current Embedding Architecture in `calibre-semantic-search`

The plugin currently features a modular embedding architecture:

*   **`core/embedding_service.py`:**
    *   `EmbeddingService`: Orchestrates embedding generation, potentially handling fallbacks.
    *   `BaseEmbeddingProvider`: An abstract base class defining the interface for providers.
    *   Concrete implementations like `OpenAIProvider`, `AzureOpenAIProvider`, `CohereProvider`, and `LocalProvider` (for SentenceTransformers).
*   **`config.py`:**
    *   Handles user configuration for selecting providers, models, API keys, and other settings like dimensions.
    *   UI elements (`QComboBox`, `QLineEdit`, `QSpinBox`) allow users to input these settings.

This existing structure is a good foundation for adding LiteLLM as another provider option.

## 3. Integrating LiteLLM

### 3.1. Create `LiteLLMProvider`

A new provider class, `LiteLLMProvider`, should be created, inheriting from `BaseEmbeddingProvider`.

**File:** `calibre_plugins/semantic_search/core/embedding_providers/lite_llm_provider.py` (new file)

```python
# calibre_plugins/semantic_search/core/embedding_providers/lite_llm_provider.py
import logging
from typing import List, Dict, Any, Optional
import asyncio

from litellm import embedding as litellm_embedding_sync, aembedding as litellm_aembedding
# It's good practice to also allow configuring litellm itself, e.g., for logging, routing, etc.
# import litellm
# litellm.set_verbose = True # Example

from calibre_plugins.semantic_search.core.embedding_providers.base import BaseEmbeddingProvider
from calibre_plugins.semantic_search.core.utils.async_utils import run_sync_in_executor # If needed for sync parts

logger = logging.getLogger(__name__)

# Default dimensions if a model's dimensions are unknown and not user-specified
# This should ideally be avoided by requiring user input or having a good map.
FALLBACK_DIMENSIONS = 768

# A map of known LiteLLM model strings to their dimensions.
# This can be expanded over time.
KNOWN_MODEL_DIMENSIONS = {
    "text-embedding-ada-002": 1536, # Often used as openai/text-embedding-ada-002
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "cohere/embed-english-v3.0": 1024,
    "cohere/embed-multilingual-v3.0": 1024,
    "sentence-transformers/all-MiniLM-L6-v2": 384,
    "vertex_ai/textembedding-gecko@003": 768,
    # Add gemini-embedding-001 once confirmed/tested
    # "vertex_ai/gemini-embedding-001": ???, (e.g. 768)
}

class LiteLLMProvider(BaseEmbeddingProvider):
    """
    Embedding provider using LiteLLM to interface with various models.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize LiteLLM provider.
        Config expected keys:
        - 'litellm_model_string': The full model string LiteLLM expects (e.g., "openai/text-embedding-ada-002", "vertex_ai/gemini-pro").
        - 'litellm_api_key': Optional API key for the underlying model or LiteLLM proxy.
        - 'litellm_base_url': Optional custom base URL for LiteLLM or the target API.
        - 'dimensions': The expected output dimensionality of the embeddings. Crucial.
        - 'litellm_custom_llm_provider': Optional, for models not directly named (e.g. 'azure', 'bedrock')
                                         where API base, key, etc. are part of the call.
        - Additional LiteLLM passthrough parameters (e.g., vertex_project, vertex_location for Vertex AI)
        """
        super().__init__(config)
        self.model_string = config.get("litellm_model_string")
        if not self.model_string:
            raise ValueError("LiteLLM model string ('litellm_model_string') is required.")

        self.api_key = config.get("litellm_api_key")
        self.base_url = config.get("litellm_base_url")
        self.custom_llm_provider = config.get("litellm_custom_llm_provider") # e.g. 'vertex_ai'

        # Handle dimensions:
        # 1. Explicitly from user config (highest priority)
        # 2. From our known map
        # 3. Fallback (least ideal)
        self._dimensions = config.get("dimensions")
        if not self._dimensions:
            # Try to infer from model_string (the part after any provider prefix)
            model_key_for_map = self.model_string.split('/')[-1] if '/' in self.model_string else self.model_string
            self._dimensions = KNOWN_MODEL_DIMENSIONS.get(model_key_for_map)
            if not self._dimensions:
                logger.warning(
                    f"Dimensions for LiteLLM model '{self.model_string}' not explicitly set or known. "
                    f"Falling back to {FALLBACK_DIMENSIONS}. Please configure dimensions for accuracy."
                )
                self._dimensions = FALLBACK_DIMENSIONS
        
        # Store other potential passthrough args for LiteLLM
        self.litellm_passthrough_args = {
            k: v for k, v in config.items() 
            if k.startswith("litellm_") and k not in [
                "litellm_model_string", "litellm_api_key", 
                "litellm_base_url", "litellm_custom_llm_provider"
            ] and v is not None
        }
        # map to actual litellm params, e.g. litellm_vertex_project -> vertex_project
        self.litellm_passthrough_args = { 
            k.replace("litellm_", ""): v for k,v in self.litellm_passthrough_args.items()
        }


    async def _generate_embeddings_internal(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        call_kwargs = {
            "model": self.model_string,
            "input": texts,
            "api_key": self.api_key if self.api_key else None,
            "api_base": self.base_url if self.base_url else None,
            "custom_llm_provider": self.custom_llm_provider if self.custom_llm_provider else None,
            **self.litellm_passthrough_args
        }
        # Filter out None values for kwargs LiteLLM might not like
        call_kwargs = {k: v for k, v in call_kwargs.items() if v is not None}

        try:
            logger.debug(f"Calling LiteLLM aembedding with kwargs: { {k:v for k,v in call_kwargs.items() if k != 'api_key'} }") # Avoid logging key
            response = await litellm_aembedding(**call_kwargs)
            
            # LiteLLM response structure for embeddings is a ModelResponse object,
            # with a 'data' attribute which is a list of EmbeddingObject.
            # Each EmbeddingObject has an 'embedding' attribute.
            embeddings = [item['embedding'] for item in response.data]
            
            # Validate dimensions of the first embedding
            if embeddings and len(embeddings[0]) != self._dimensions:
                logger.error(
                    f"LiteLLM returned embedding dimension {len(embeddings[0])} "
                    f"does not match configured dimension {self._dimensions} for model {self.model_string}."
                )
                # Decide on error handling: raise, return empty, or try to use what was returned?
                # For now, let's raise to make the mismatch clear.
                raise ValueError(
                    f"Embedding dimension mismatch for model {self.model_string}. "
                    f"Expected {self._dimensions}, got {len(embeddings[0])}."
                )
            return embeddings
        except Exception as e:
            logger.error(f"LiteLLM embedding generation failed for model {self.model_string}: {e}", exc_info=True)
            # Consider specific exception handling for LiteLLM errors if available
            raise # Re-raise to be handled by EmbeddingService

    async def generate_embedding(self, text: str) -> List[float]:
        if not text.strip(): # Handle empty string input
            logger.warning("generate_embedding called with empty text. Returning zero vector.")
            return [0.0] * self._dimensions # Or handle as an error
            
        embeddings = await self._generate_embeddings_internal([text])
        return embeddings[0] if embeddings else []

    async def generate_batch(self, texts: List[str]) -> List[List[float]]:
        # LiteLLM's aembedding can handle batches directly.
        # However, some underlying models might have strict limits.
        # For now, assume LiteLLM handles batching or we handle it at a higher level if needed.
        return await self._generate_embeddings_internal(texts)

    def get_dimensions(self) -> int:
        return self._dimensions

    def get_model_name(self) -> str:
        # Provides a descriptive name for logging or UI.
        return f"LiteLLM ({self.model_string})"

    # Optional: Implement get_max_batch_size and get_max_text_length
    # These might be hard to determine generically for LiteLLM unless LiteLLM itself exposes this.
    # For now, rely on BaseEmbeddingProvider defaults or user knowledge.
```

### 3.2. Modify `EmbeddingService`

Update `EmbeddingService` in `core/embedding_service.py` to recognize and instantiate `LiteLLMProvider`.

```python
# In core/embedding_service.py
# ... other imports ...
from calibre_plugins.semantic_search.core.embedding_providers.lite_llm_provider import LiteLLMProvider # Add this

# ... in EmbeddingService.get_provider_from_config method or similar logic ...
# when instantiating providers based on config['provider_type'] or similar:

# elif provider_type == "litellm": # Or your chosen identifier
#     provider_config = {
#         "litellm_model_string": config.get("litellm_model_string"),
#         "litellm_api_key": config.get("litellm_api_key"),
#         "litellm_base_url": config.get("litellm_base_url"),
#         "dimensions": config.get("embedding_dimensions"), # Ensure this is passed
#         "litellm_custom_llm_provider": config.get("litellm_custom_llm_provider"),
#         # Add any other passthrough args like vertex_project, vertex_location
#         "litellm_vertex_project": config.get("litellm_vertex_project"),
#         "litellm_vertex_location": config.get("litellm_vertex_location"),
#         # ... potentially more for other LiteLLM features
#     }
#     return LiteLLMProvider(provider_config)
```

### 3.3. Handling Model Dimensionality

This is critical. Embedding vectors must have consistent dimensions for storage and comparison.

*   **User Input:** The `dimensions_spin` in `config.py` becomes the primary source of truth for the expected dimensionality when using LiteLLM.
*   **`LiteLLMProvider.get_dimensions()`:** Must return the user-configured (or inferred/defaulted) dimension.
*   **Validation:** The `LiteLLMProvider` should, if possible, validate that the first embedding received from LiteLLM matches the configured dimension. If not, log an error and potentially raise an exception, as this indicates a misconfiguration.
*   **`KNOWN_MODEL_DIMENSIONS` Map:** The map in `lite_llm_provider.py` can provide sensible defaults for the dimensions spinbox when a known model string is entered by the user in the config UI.

## 4. UI and Configuration Changes (`config.py`)

### 4.1. Add "LiteLLM" to Provider Choices

```python
# In ConfigWidget class in config.py
self.provider_combo.addItems([
    "OpenAI", "Azure OpenAI", "Cohere", "Local (SentenceTransformer)", "Mock", 
    "LiteLLM" # Add LiteLLM
])
```

### 4.2. LiteLLM-Specific Settings Group

Create a new `QGroupBox` for LiteLLM settings that becomes visible when "LiteLLM" is selected.

```python
# In ConfigWidget.__init__
self.litellm_group = QGroupBox("LiteLLM Settings")
litellm_layout = QFormLayout()

self.litellm_model_string_edit = QLineEdit()
self.litellm_model_string_edit.setPlaceholderText("e.g., openai/text-embedding-ada-002, vertex_ai/gemini-embedding-001")
litellm_layout.addRow("LiteLLM Model String:", self.litellm_model_string_edit)

self.litellm_api_key_edit = QLineEdit()
self.litellm_api_key_edit.setEchoMode(QLineEdit.Password)
litellm_layout.addRow("LiteLLM/Model API Key (Optional):", self.litellm_api_key_edit)

self.litellm_base_url_edit = QLineEdit()
self.litellm_base_url_edit.setPlaceholderText("Optional: For self-hosted LiteLLM or custom endpoint")
litellm_layout.addRow("LiteLLM/Model Base URL (Optional):", self.litellm_base_url_edit)

# Specific passthrough for Vertex AI example
self.litellm_vertex_project_edit = QLineEdit()
self.litellm_vertex_project_edit.setPlaceholderText("Your Google Cloud Project ID (if using Vertex AI)")
litellm_layout.addRow("Vertex AI Project (Optional):", self.litellm_vertex_project_edit)

self.litellm_vertex_location_edit = QLineEdit()
self.litellm_vertex_location_edit.setPlaceholderText("e.g., us-central1 (if using Vertex AI)")
litellm_layout.addRow("Vertex AI Location (Optional):", self.litellm_vertex_location_edit)

# Consider a field for 'custom_llm_provider' if needed for more complex LiteLLM setups
# self.litellm_custom_provider_edit = QLineEdit()
# self.litellm_custom_provider_edit.setPlaceholderText("e.g., azure, bedrock (see LiteLLM docs)")
# litellm_layout.addRow("LiteLLM Custom Provider (Optional):", self.litellm_custom_provider_edit)


self.litellm_group.setLayout(litellm_layout)
main_layout.addWidget(self.litellm_group) # Add to your main config layout
```

### 4.3. Show/Hide Logic and Defaults

In `_on_provider_changed(self, provider_text)`:

```python
# In ConfigWidget._on_provider_changed
provider_key = self.config_key_map.get(provider_text, provider_text.lower().replace(" ", "_"))

is_litellm = (provider_key == "litellm")
self.litellm_group.setVisible(is_litellm)
self.dimensions_spin.setEnabled(True) # Dimensions always needed, especially for LiteLLM

if is_litellm:
    # Potentially disable/hide other provider-specific groups
    self.openai_group.setVisible(False)
    self.azure_group.setVisible(False)
    # ... etc.
    
    # When LiteLLM is selected, the model_combo for specific OpenAI/Cohere models is less relevant.
    # The primary model identifier will come from litellm_model_string_edit.
    # You might want to disable/hide self.model_combo or self.model_edit
    self.model_label.setVisible(False) # Or change text
    self.model_combo.setVisible(False) # Or clear and disable
    self.model_edit.setVisible(False)

    # Attempt to set default dimension if model string changes and is known
    self.litellm_model_string_edit.textChanged.connect(self._update_litellm_dimensions_default)

else: # For other providers
    self.model_label.setVisible(True)
    self.model_combo.setVisible(True) # Or model_edit depending on your existing logic
    self.litellm_model_string_edit.textChanged.disconnect(self._update_litellm_dimensions_default) # Disconnect
    # Restore visibility/state of other provider groups and model fields
```

Add a new method `_update_litellm_dimensions_default`:

```python
# In ConfigWidget class
def _update_litellm_dimensions_default(self, model_string_text: str):
    model_key = model_string_text.split('/')[-1] if '/' in model_string_text else model_string_text
    if model_key in KNOWN_MODEL_DIMENSIONS: # Use the same map as in LiteLLMProvider
        self.dimensions_spin.setValue(KNOWN_MODEL_DIMENSIONS[model_key])
    # else: leave user-set value or previous default
```
*(Ensure `KNOWN_MODEL_DIMENSIONS` is accessible here, perhaps defined in a shared constants file or passed appropriately).*

### 4.4. Saving and Loading Configuration

Update `_load_settings` and `_save_settings` in `ConfigWidget` to handle the new LiteLLM fields:

```python
# In _load_settings:
self.litellm_model_string_edit.setText(self.config.get("litellm_model_string", ""))
self.litellm_api_key_edit.setText(self.config.get("litellm_api_key", ""))
self.litellm_base_url_edit.setText(self.config.get("litellm_base_url", ""))
self.litellm_vertex_project_edit.setText(self.config.get("litellm_vertex_project", ""))
self.litellm_vertex_location_edit.setText(self.config.get("litellm_vertex_location", ""))
# self.litellm_custom_provider_edit.setText(self.config.get("litellm_custom_llm_provider", ""))


# In _save_settings:
# ... (existing saves) ...
if self.provider_combo.currentText() == "LiteLLM":
    self.config.set("embedding_provider", "litellm") # General provider type
    self.config.set("litellm_model_string", self.litellm_model_string_edit.text().strip())
    self.config.set("litellm_api_key", self.litellm_api_key_edit.text()) # No strip for keys
    self.config.set("litellm_base_url", self.litellm_base_url_edit.text().strip())
    self.config.set("litellm_vertex_project", self.litellm_vertex_project_edit.text().strip())
    self.config.set("litellm_vertex_location", self.litellm_vertex_location_edit.text().strip())
    # self.config.set("litellm_custom_llm_provider", self.litellm_custom_provider_edit.text().strip())

# Crucially, ensure 'embedding_dimensions' is always saved correctly.
self.config.set("embedding_dimensions", self.dimensions_spin.value())
```

## 5. Supporting New Models (e.g., Vertex AI `gemini-embedding-001`)

### 5.1. How LiteLLM Supports Models

LiteLLM aims to support models by:
1.  Recognizing the model string (e.g., `vertex_ai/model-name`).
2.  Knowing how to authenticate with the provider (e.g., Vertex AI needs project, location, credentials).
3.  Transforming the input into the provider's expected request format.
4.  Parsing the provider's response.

### 5.2. Using `gemini-embedding-001` via LiteLLM

1.  **Model String:** The exact string would be `vertex_ai/gemini-embedding-001` or similar. Check LiteLLM's documentation or GitHub issues for confirmation if it's a new model.
2.  **Authentication & Parameters (Vertex AI specific):**
    *   LiteLLM needs Google Cloud credentials. This is often handled by setting the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to point to a service account JSON key file.
    *   LiteLLM calls to Vertex AI often require `vertex_project` and `vertex_location` to be passed in the `aembedding` call. The `LiteLLMProvider` and `ConfigWidget` example above include fields for these.
3.  **Dimensionality:** `gemini-embedding-001` reportedly has 768 dimensions. This should be added to `KNOWN_MODEL_DIMENSIONS` and set by the user.
4.  **Single Input Text per Request:** Google's documentation for `gemini-embedding-001` states: "each request can only include a single input text."
    *   If LiteLLM's `aembedding` function with the Vertex AI provider doesn't automatically handle batching for this model (by making multiple single calls), the `LiteLLMProvider.generate_batch` method might need to implement this client-side batching:
        ```python
        # Potential adjustment in LiteLLMProvider.generate_batch if needed for specific models
        # async def generate_batch(self, texts: List[str]) -> List[List[float]]:
        #     if self.model_string == "vertex_ai/gemini-embedding-001": # Or a more generic check
        #         logger.info(f"Model {self.model_string} might not support batching directly. Generating embeddings sequentially.")
        #         embeddings = []
        #         for text_item in texts:
        #             # Make sure _generate_embeddings_internal correctly handles single item list
        #             single_embedding_list = await self._generate_embeddings_internal([text_item])
        #             if single_embedding_list:
        #                 embeddings.append(single_embedding_list[0])
        #             else:
        #                 embeddings.append([0.0] * self._dimensions) # Or handle error
        #         return embeddings
        #     else:
        #         return await self._generate_embeddings_internal(texts)
        ```
    *   However, it's best to rely on LiteLLM to handle this if possible. Test first.

### 5.3. If LiteLLM Lacks Support

*   **Check LiteLLM Updates:** LiteLLM is actively developed. Update to the latest version.
*   **GitHub Issue:** Raise an issue on [BerriAI/litellm](https://github.com/BerriAI/litellm) with details.
*   **Contribute to LiteLLM:** If feasible, contribute the necessary changes to LiteLLM.
*   **Direct Integration (Fallback):** As a last resort for an urgent unsupported model, you could create a specific provider (e.g., `VertexGeminiEmbeddingProvider`) in `calibre-semantic-search` using the `google-cloud-aiplatform` SDK directly. This bypasses LiteLLM for that model.

## 6. Key Code Considerations

*   **Async Operations:** Ensure all LiteLLM calls are `async` and correctly `await`ed, fitting into the plugin's `asyncio` structure. `litellm.aembedding` is the async version.
*   **Error Handling:** Wrap LiteLLM calls in `try...except` blocks. Log errors comprehensively. LiteLLM may raise specific exceptions; handle them if documented.
*   **Dependencies:** Add `litellm` to the plugin's dependencies (e.g., in `setup.py` or `requirements.txt` if used for development).
    ```
    install_requires=[
        ...
        'litellm>=<LATEST_VERSION_COMPATIBLE>', # Specify version range
    ],
    ```
*   **Testing:** Thoroughly test with various LiteLLM configurations:
    *   Different model strings (OpenAI, Cohere, HuggingFace via LiteLLM).
    *   With and without API keys/base URLs.
    *   Vertex AI specific setup.
    *   Correct and incorrect dimension settings to see error handling.

## 7. Actionable Steps for the AI Agent

1.  **Implement `LiteLLMProvider`:** Create the class as detailed in section 3.1.
2.  **Update `EmbeddingService`:** Modify it to use `LiteLLMProvider` as per section 3.2.
3.  **Enhance `ConfigWidget`:**
    *   Add "LiteLLM" to provider choices.
    *   Create the LiteLLM settings group.
    *   Implement show/hide logic for UI elements.
    *   Implement saving/loading of LiteLLM configurations.
    *   Implement the `_update_litellm_dimensions_default` helper.
4.  **Dimensionality Handling:** Ensure dimensions are correctly passed, used, and (ideally) validated. Populate `KNOWN_MODEL_DIMENSIONS`.
5.  **Test Basic LiteLLM Functionality:** Use a common, easily accessible model via LiteLLM first (e.g., an OpenAI model if you have a key, or a free Hugging Face Sentence Transformer model string that LiteLLM supports).
6.  **Test Vertex AI `gemini-embedding-001`:**
    *   Configure with the correct model string, dimensions (768), project, and location.
    *   Ensure Google Cloud authentication is set up for the environment where Calibre runs.
    *   Pay attention to batching behavior.
7.  **Refine Error Handling and Logging:** Add detailed logs for LiteLLM calls, successes, and failures.
8.  **Update Documentation:** If user-facing documentation exists for the plugin, update it to explain how to configure LiteLLM, including Vertex AI specifics.

This integration will significantly enhance the flexibility of `calibre-semantic-search`.