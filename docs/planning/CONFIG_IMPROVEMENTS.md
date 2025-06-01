# Configuration Improvements Plan

## 🔍 Current State Analysis

### LiteLLM Integration Status
- ✅ **Properly Integrated**: All providers use `litellm.aembedding` 
- ✅ **Basic Providers**: OpenAI, Vertex AI, Cohere working
- ❌ **Missing Providers**: Only using 3 of 10+ available providers
- ❌ **Limited Configuration**: No advanced options exposed

## 🚀 Recommended Improvements

### 1. Additional Providers (Priority: HIGH)
Add these widely-used providers that LiteLLM supports:

```python
providers = [
    # Existing
    "mock",
    "openai", 
    "vertex_ai",
    "cohere",
    
    # Add these
    "azure_openai",     # Enterprise users
    "bedrock",          # AWS users  
    "mistral",          # Popular open alternative
    "voyage",           # Specialized embeddings
    "huggingface",      # Custom models
    "gemini",           # Google's latest
    "ollama",           # Local models (already planned)
]
```

### 2. Provider-Specific Configuration (Priority: HIGH)

#### Azure OpenAI
- Deployment name
- API base URL
- API version

#### AWS Bedrock
- AWS region
- AWS credentials (or use IAM role)

#### Hugging Face
- Custom endpoint URL
- Model ID

### 3. Advanced Embedding Options (Priority: MEDIUM)

```python
# Add to config dialog
advanced_options = {
    "dimensions": QSpinBox(),          # For OpenAI text-embedding-3
    "encoding_format": QComboBox(),    # "float" or "base64"
    "input_type": QComboBox(),         # For Cohere: search_document, search_query
    "api_base": QLineEdit(),           # Custom endpoints
    "timeout": QSpinBox(),             # Request timeout
    "max_retries": QSpinBox(),         # Retry attempts
}
```

### 4. Model Management (Priority: MEDIUM)

Dynamic model selection based on provider:
```python
model_presets = {
    "openai": [
        ("text-embedding-3-small", "Fast, 1536 dims, $0.02/1M tokens"),
        ("text-embedding-3-large", "Best quality, 3072 dims, $0.13/1M tokens"),
        ("text-embedding-ada-002", "Legacy, 1536 dims, $0.10/1M tokens"),
    ],
    "cohere": [
        ("embed-english-v3.0", "English, 1024 dims"),
        ("embed-multilingual-v3.0", "100+ languages, 1024 dims"),
        ("embed-english-light-v3.0", "Fast English, 384 dims"),
    ],
    "mistral": [
        ("mistral-embed", "1024 dims, competitive pricing"),
    ],
    # etc...
}
```

### 5. Configuration Profiles (Priority: LOW)

Pre-configured settings for common use cases:
```python
profiles = {
    "Fast": {
        "provider": "openai",
        "model": "text-embedding-3-small",
        "batch_size": 100,
        "cache_enabled": True,
    },
    "Quality": {
        "provider": "openai",
        "model": "text-embedding-3-large",
        "batch_size": 50,
        "dimensions": 3072,
    },
    "Offline": {
        "provider": "ollama",
        "model": "mxbai-embed-large",
        "batch_size": 20,
    },
    "Budget": {
        "provider": "huggingface",
        "model": "sentence-transformers/all-MiniLM-L6-v2",
        "batch_size": 100,
    },
}
```

### 6. Provider Health Dashboard (Priority: LOW)

Show in configuration dialog:
- ✅/❌ Connection status
- Response time
- Rate limit remaining
- Estimated cost per 1000 embeddings
- Total embeddings generated

### 7. Configuration Import/Export (Priority: LOW)

- Export configuration to JSON
- Import from file
- Share configurations between libraries

## 📝 Implementation Plan

### Phase 1: Core Provider Support (1-2 days)
1. Add Azure OpenAI provider with deployment configuration
2. Add AWS Bedrock provider with region selection
3. Add Mistral provider
4. Update provider dropdown and model selection

### Phase 2: Advanced Options (1 day)
1. Add collapsible "Advanced Options" section
2. Implement dimensions parameter for OpenAI
3. Add API base URL for custom endpoints
4. Add timeout and retry configuration

### Phase 3: UX Improvements (1 day)
1. Dynamic model dropdown based on provider
2. Show model details (dimensions, cost estimate)
3. Add "Test Configuration" that shows detailed results
4. Configuration validation before save

### Phase 4: Nice-to-Have Features (Future)
1. Configuration profiles
2. Provider health monitoring
3. Import/export functionality
4. Usage tracking and cost estimation

## 🔧 Code Changes Needed

### 1. Update Provider Factory
```python
# embedding_service.py
def create_embedding_service(config):
    # Add new provider cases
    elif provider_name == "azure_openai":
        provider = AzureOpenAIProvider(
            api_key=api_keys.get("azure_openai"),
            deployment=config.get("azure_deployment"),
            api_base=config.get("azure_api_base"),
            api_version=config.get("azure_api_version", "2024-02-01"),
        )
```

### 2. Enhance Config Dialog
```python
# config.py
def _create_api_tab(self):
    # Add provider-specific fields that show/hide based on selection
    self.provider_combo.currentTextChanged.connect(self._on_provider_changed)
    
def _on_provider_changed(self, provider):
    # Show/hide relevant configuration fields
    self.azure_group.setVisible(provider == "azure_openai")
    self.aws_group.setVisible(provider == "bedrock")
```

### 3. Update Test Connection
```python
# Make test connection show more details
def _test_connection(self):
    # Show: provider, model, dimensions, response time
    # Test with actual embedding generation
    # Display cost estimate
```

## 🎯 Priority Recommendations

**Must Have for v1.0:**
1. Azure OpenAI support (many enterprise users)
2. API base URL configuration (custom endpoints)
3. Better model selection UI

**Nice to Have for v1.1:**
1. AWS Bedrock support
2. Configuration profiles
3. Advanced options panel

**Future Enhancements:**
1. Provider health monitoring
2. Cost tracking
3. Import/export configurations