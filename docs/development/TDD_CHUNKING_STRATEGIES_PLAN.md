# TDD Implementation Plan: Advanced Chunking Strategies

## Overview

This document outlines the Test-Driven Development approach for implementing multiple chunking strategies beyond the current fixed-size approach.

## Chunking Strategy Requirements

### 1. Fixed Size (✅ Implemented)
- Split text into chunks of fixed character/word count
- Configurable overlap between chunks
- Current implementation in `TextProcessor`

### 2. Sentence-based Chunking
- **Need**: Split at sentence boundaries
- **Need**: Respect minimum/maximum chunk sizes
- **Need**: Handle edge cases (abbreviations, decimals)
- **Use Case**: Better semantic coherence for general text

### 3. Paragraph-based Chunking  
- **Need**: Split at paragraph boundaries
- **Need**: Handle very long/short paragraphs
- **Need**: Combine small paragraphs to meet minimum size
- **Use Case**: Academic texts with clear paragraph structure

### 4. Semantic Chunking
- **Need**: Use NLP to find semantic boundaries
- **Need**: Identify topic shifts
- **Need**: Preserve complete thoughts/arguments
- **Use Case**: Philosophy texts where arguments span multiple paragraphs

### 5. Hybrid Chunking
- **Need**: Combine strategies based on text type
- **Need**: Auto-detect optimal strategy
- **Need**: User override capability
- **Use Case**: Mixed content books

## Architecture Design

### Strategy Pattern Implementation

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class ChunkingStrategy(ABC):
    """Abstract base class for chunking strategies"""
    
    @abstractmethod
    def chunk(self, text: str, config: Dict[str, Any]) -> List[str]:
        """Split text into chunks according to strategy"""
        pass
    
    @abstractmethod
    def get_config_schema(self) -> Dict[str, Any]:
        """Return configuration schema for this strategy"""
        pass

class FixedSizeChunker(ChunkingStrategy):
    """Current implementation - fixed size chunks"""
    
    def chunk(self, text: str, config: Dict[str, Any]) -> List[str]:
        chunk_size = config.get('chunk_size', 1000)
        overlap = config.get('overlap', 200)
        # ... existing implementation
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            'chunk_size': {'type': 'int', 'min': 100, 'max': 2000},
            'overlap': {'type': 'int', 'min': 0, 'max': 500}
        }

class SentenceChunker(ChunkingStrategy):
    """Sentence-based chunking"""
    
    def chunk(self, text: str, config: Dict[str, Any]) -> List[str]:
        min_sentences = config.get('min_sentences', 3)
        max_sentences = config.get('max_sentences', 10)
        # ... implementation
```

## Test Categories

### 1. Unit Tests for Each Strategy

```python
# test_chunking_strategies.py

class TestSentenceChunker:
    def test_basic_sentence_split(self):
        """Test basic sentence boundary detection"""
        chunker = SentenceChunker()
        text = "First sentence. Second sentence. Third sentence."
        chunks = chunker.chunk(text, {'min_sentences': 2})
        assert len(chunks) == 2
        assert chunks[0] == "First sentence. Second sentence."
        assert chunks[1] == "Third sentence."
    
    def test_abbreviation_handling(self):
        """Test that abbreviations don't break sentences"""
        chunker = SentenceChunker()
        text = "Dr. Smith works at U.S.A. Inc. He is great."
        chunks = chunker.chunk(text, {'min_sentences': 1})
        assert len(chunks) == 2
        assert "Dr. Smith" in chunks[0]
        assert "Inc." in chunks[0]
    
    def test_minimum_size_enforcement(self):
        """Test that chunks meet minimum size requirements"""
        # ... test implementation
```

### 2. Integration Tests

```python
class TestChunkingIntegration:
    def test_strategy_selection(self):
        """Test that correct strategy is selected based on config"""
        processor = TextProcessor()
        config = {'strategy': 'sentence', 'min_sentences': 5}
        chunks = processor.chunk_text("Long text...", config)
        # Verify sentence-based chunking was used
    
    def test_fallback_on_error(self):
        """Test fallback to fixed-size if strategy fails"""
        # ... test implementation
```

### 3. Performance Tests

```python
class TestChunkingPerformance:
    def test_large_text_performance(self):
        """Test chunking performance on large texts"""
        text = "Very long text..." * 10000
        chunker = SentenceChunker()
        
        start = time.time()
        chunks = chunker.chunk(text, {})
        duration = time.time() - start
        
        assert duration < 1.0  # Should chunk in under 1 second
```

## Implementation Plan

### Phase 1: Sentence-based Chunking (2 days)

1. **Day 1: Core Implementation**
   - ❌ Write failing tests for sentence detection
   - ❌ Implement basic sentence splitting
   - ❌ Handle edge cases (abbreviations, etc.)
   - ❌ Make tests pass

2. **Day 2: Integration**
   - ❌ Write integration tests
   - ❌ Add to TextProcessor
   - ❌ Update UI to show option
   - ❌ Test in Calibre

### Phase 2: Paragraph-based Chunking (1 day)

1. **Implementation**
   - ❌ Write tests for paragraph detection
   - ❌ Implement paragraph chunking
   - ❌ Handle size constraints
   - ❌ Integration and UI

### Phase 3: Semantic Chunking (3 days)

1. **Day 1: Research & Design**
   - ❌ Research NLP libraries (spaCy, NLTK)
   - ❌ Design semantic boundary detection
   - ❌ Write comprehensive tests

2. **Day 2: Implementation**
   - ❌ Implement topic segmentation
   - ❌ Add configuration options
   - ❌ Performance optimization

3. **Day 3: Integration**
   - ❌ Integration with TextProcessor
   - ❌ UI updates
   - ❌ End-to-end testing

### Phase 4: Hybrid & Auto-detection (2 days)

1. **Auto-detection Logic**
   - ❌ Text type classification
   - ❌ Strategy recommendation
   - ❌ User override capability

2. **Testing & Polish**
   - ❌ Comprehensive testing
   - ❌ Documentation
   - ❌ Performance benchmarks

## Configuration UI Design

```python
# In config dialog
chunking_group = QGroupBox("Chunking Configuration")

# Strategy selection
strategy_combo = QComboBox()
strategy_combo.addItems([
    "Fixed Size",
    "Sentence-based", 
    "Paragraph-based",
    "Semantic (Advanced)",
    "Auto-detect"
])

# Dynamic config based on strategy
config_stack = QStackedWidget()

# Fixed size config
fixed_widget = QWidget()
# ... chunk_size, overlap spinboxes

# Sentence config  
sentence_widget = QWidget()
# ... min_sentences, max_sentences spinboxes

# Add widgets to stack
config_stack.addWidget(fixed_widget)
config_stack.addWidget(sentence_widget)
# ...

# Connect strategy change to show appropriate config
strategy_combo.currentIndexChanged.connect(
    config_stack.setCurrentIndex
)
```

## Success Metrics

1. **Accuracy**: Chunks preserve semantic meaning
2. **Performance**: <100ms for average book chapter
3. **Flexibility**: Easy to add new strategies
4. **User Experience**: Clear configuration options
5. **Compatibility**: Works with all text formats

## Risk Mitigation

### Risk: NLP libraries add heavy dependencies
**Mitigation**: Make semantic chunking optional, use lightweight libraries

### Risk: Performance degradation with complex strategies
**Mitigation**: Implement caching, offer performance/quality tradeoff settings

### Risk: Poor results on edge cases
**Mitigation**: Comprehensive test suite, fallback mechanisms

## Next Steps

1. ✅ Create this planning document
2. ❌ Review with stakeholders
3. ❌ Begin Phase 1 implementation
4. ❌ Regular progress updates