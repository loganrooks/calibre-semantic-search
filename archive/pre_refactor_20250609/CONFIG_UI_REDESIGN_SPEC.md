# Configuration UI Redesign Specification

## Current Problems Analysis

### Major UI Issues
1. **Dual Model Input Confusion**: Both `model_combo_provider` AND `model_edit` exist
2. **Provider Inequality**: Only Azure gets dedicated section, others neglected  
3. **Poor Model Selection**: No search, no metadata, limited to 3-4 hardcoded models
4. **Visual Chaos**: Everything visible at once, no progressive disclosure
5. **Missing Guidance**: No clear required vs optional indicators

### User Pain Points
- "Which model field do I use?"
- "What API key format does Vertex AI need?"
- "How do I know which model is best for academic texts?"
- "What's required vs optional for each provider?"

## Target User Experience

### UX Principles
1. **Guided Discovery**: Progressive disclosure from simple to complex
2. **Provider Parity**: Every provider gets equal, dedicated treatment  
3. **Informed Choice**: Model selection with rich metadata and recommendations
4. **Immediate Feedback**: Real-time validation and helpful error messages
5. **Expert Mode**: Advanced users can access all options directly

### User Flow Design

```
┌─────────────────────────────────────────────────────┐
│                 AI Provider Setup                   │
├─────────────────────────────────────────────────────┤
│                                                     │
│  🎯 Choose Your AI Provider                         │
│  ┌─────┐ ┌─────────┐ ┌─────────┐ ┌────────┐         │
│  │Mock │ │ OpenAI  │ │Vertex AI│ │ Cohere │ ...     │
│  └─────┘ └─────────┘ └─────────┘ └────────┘         │
│                                                     │
│  ↓ (when provider selected)                         │
│                                                     │
│  📋 OpenAI Configuration                            │
│  ┌─────────────────────────────────────────────────┐│
│  │ ✅ API Key*: [sk-...] [Test] [Valid ✓]         ││
│  │                                                 ││
│  │ 🎯 Model Selection:                             ││
│  │ [text-embedding-3-large ▼] [🔍 Search models] ││
│  │ 💡 Recommended for academic texts               ││
│  │ 📊 3072 dimensions | $0.00013/1K tokens        ││
│  │                                                 ││
│  │ ⚙️  Advanced Options [Show ▼]                   ││
│  │ ┌─────────────────────────────────────────────┐ ││
│  │ │ Batch Size: [100]                           │ ││
│  │ │ Custom Dimensions: [ ] Auto-detect          │ ││
│  │ └─────────────────────────────────────────────┘ ││
│  └─────────────────────────────────────────────────┘│
│                                                     │
│  [Test Connection] [Save Configuration]             │
└─────────────────────────────────────────────────────┘
```

## Technical Implementation Plan

### Phase 1: Clean Up Current Mess (2-3 hours)
1. **Remove Dual Model Inputs**: Eliminate confusing `model_edit` vs `model_combo_provider`
2. **Standardize Provider Sections**: Create consistent sections for all providers
3. **Fix Visual Hierarchy**: Implement clear grouping and progressive disclosure

### Phase 2: Enhanced Model Selection (2-3 hours)  
1. **Integrate Discovery System**: Connect real LiteLLM model data
2. **Searchable Dropdown**: Add filtering and search functionality
3. **Model Metadata Display**: Show dimensions, cost, recommendations
4. **Auto-population**: Update dimensions automatically based on model selection

### Phase 3: Provider-Specific UX (3-4 hours)
1. **Provider Sections**: Dedicated configuration for each provider
2. **Field Validation**: Real-time validation with helpful messages  
3. **Smart Defaults**: Provider-specific reasonable defaults
4. **Progressive Disclosure**: Advanced options hidden by default

### Phase 4: Polish & Guidance (1-2 hours)
1. **Visual Improvements**: Better styling, icons, hierarchy
2. **Tooltips & Help**: Contextual guidance for each field
3. **Setup Wizard**: Optional guided flow for new users

## Detailed Component Design

### 1. Provider Selection Component
```python
class ProviderSelector(QWidget):
    """Clean provider selection with immediate visual feedback"""
    
    def __init__(self):
        # Radio buttons or card-style selection
        # Clear provider descriptions
        # Immediate section switching
```

### 2. Provider Configuration Sections
```python
class OpenAIConfigSection(QWidget):
    """Dedicated OpenAI configuration"""
    # API key with format validation
    # Model dropdown with search
    # Advanced options (collapsed)

class VertexAIConfigSection(QWidget):  
    """Dedicated Vertex AI configuration"""
    # Project ID field with validation
    # Location selection
    # Service account guidance
    
class CohereConfigSection(QWidget):
    """Dedicated Cohere configuration"""  
    # API key field
    # Input type selection
    # Usage guidance
```

### 3. Enhanced Model Selection Component
```python
class ModelSelectionWidget(QWidget):
    """Searchable model dropdown with metadata"""
    
    def __init__(self, provider: str):
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)  # For search
        self.search_completer = QCompleter()  # Auto-complete
        self.metadata_display = ModelMetadataWidget()
        
    def update_models(self, provider: str):
        # Load from discovery system
        # Show metadata for selected model
        # Highlight recommendations
```

### 4. Real-time Validation
```python
class ValidationManager:
    """Handles real-time field validation"""
    
    def validate_api_key(self, provider: str, key: str) -> ValidationResult:
        # Format validation (not connection test)
        # Provider-specific key format checking
        
    def validate_configuration(self, config: dict) -> ValidationResult:
        # Check all required fields
        # Provider-specific validation rules
```

## Implementation Order (TDD-Driven)

### Step 1: Write Failing Integration Tests
```python
def test_openai_provider_section_appears_when_selected():
    # Select OpenAI → see OpenAI section, others hidden
    
def test_model_dropdown_shows_search_and_metadata():
    # Model dropdown is searchable with metadata display
    
def test_all_providers_have_dedicated_sections():
    # Every provider gets equal treatment
```

### Step 2: Implement Core Structure
1. Create `ProviderConfigurationWidget` base class
2. Implement provider-specific sections
3. Add section switching logic

### Step 3: Enhance Model Selection
1. Create `ModelSelectionWidget` with search
2. Integrate discovery system data
3. Add metadata display

### Step 4: Add Validation & Polish
1. Implement real-time validation
2. Add progressive disclosure
3. Polish visual design

## Success Metrics

### Quantitative
- [ ] Single model input mechanism (eliminate dual inputs)
- [ ] All 5 providers have dedicated sections (not just Azure)
- [ ] Model dropdown shows 30+ models (vs 3-4 hardcoded)
- [ ] Search functionality works with <100ms response
- [ ] Real-time validation on all input fields

### Qualitative  
- [ ] New user can configure provider without external docs
- [ ] Model selection provides enough info to make informed choice
- [ ] Advanced users can access all options efficiently
- [ ] Visual hierarchy guides attention appropriately
- [ ] Error messages help users fix problems immediately

## Risk Mitigation

### Technical Risks
- **Qt/Calibre Integration**: Test UI changes in real Calibre environment
- **Async Model Loading**: Ensure UI remains responsive during discovery
- **Configuration Migration**: Don't break existing user configs

### UX Risks  
- **Overwhelming Complexity**: Use progressive disclosure extensively
- **Provider Bias**: Ensure equal treatment across all providers
- **Expert User Friction**: Maintain advanced/expert mode access

## Implementation Notes

### Qt-Specific Considerations
- Use `QStackedWidget` for provider section switching
- `QCompleter` for model search functionality  
- `QValidator` classes for real-time field validation
- `QGroupBox` with styling for visual hierarchy

### Calibre Integration
- Maintain existing configuration schema
- Test in actual Calibre environment frequently
- Preserve backward compatibility with existing configs

This redesign transforms the configuration from "trash" to professional, guided experience that scales from novice to expert users.