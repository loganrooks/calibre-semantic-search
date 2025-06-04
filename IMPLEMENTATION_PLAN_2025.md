# Calibre Semantic Search Plugin - Implementation Plan 2025

**Date Created**: 2025-01-06
**Target Version**: 1.0.0
**Estimated Completion**: 2-3 weeks

## Executive Summary

This document outlines the implementation plan to address critical issues and missing features in the Calibre Semantic Search Plugin. The plugin is 88% complete but has several critical gaps preventing a successful v1.0 release.

## Critical Issues Identified

### 1. **Metadata Extraction Failure** (Priority: CRITICAL)
**Issue**: Search results show "Unknown Author. Unknown." instead of actual book metadata
**Root Cause**: SearchResult objects aren't being populated with author data from CalibreRepository
**Location**: `search_dialog.py:297` - authors field not populated in search results

### 2. **"View in Book" Not Working** (Priority: HIGH)
**Issue**: Clicking "View in Book" opens viewer but doesn't navigate to search result location
**Root Cause**: Missing viewer integration - only opens book, doesn't navigate to chunk
**Location**: `search_dialog.py:423-445` - missing chunk navigation implementation

### 3. **UI Theming Issues** (Priority: MEDIUM)
**Issue**: Light gray text on light background is hard to read
**Root Cause**: Hard-coded colors don't respect Calibre's theme
**Location**: Multiple setStyleSheet calls with hard-coded colors

### 4. **No Index Management UI** (Priority: HIGH)
**Issue**: No way to view, clear, or manage the search index
**Root Cause**: Feature not implemented
**Location**: Missing UI component

### 5. **Poor Extensibility** (Priority: MEDIUM)
**Issue**: Hard-coded providers, no plugin system for adding new ones
**Root Cause**: Architecture not designed for extensibility

## Implementation Plan

### Phase 1: Critical Fixes (Week 1)

#### 1.1 Fix Metadata Extraction (Day 1)
```python
# In search_engine.py - ensure SearchResult includes authors
# Modify search() method to populate authors from CalibreRepository

# In search_dialog.py:297
# Instead of:
'author': ', '.join(result.authors) if hasattr(result, 'authors') else 'Unknown',
# Ensure result.authors is always populated from metadata
```

**Tasks**:
- [ ] Modify SearchEngine to fetch metadata for each result
- [ ] Update SearchResult dataclass to guarantee authors field
- [ ] Add metadata caching to avoid repeated lookups
- [ ] Test with various book formats

#### 1.2 Implement Viewer Integration (Days 2-3)
```python
# Create viewer_integration.py enhancements
class ViewerIntegration:
    def navigate_to_chunk(self, viewer, book_id: int, chunk_id: int):
        """Navigate viewer to specific chunk location"""
        # Get chunk location from database
        # Convert to viewer position (page/location)
        # Highlight the found text
```

**Tasks**:
- [ ] Research Calibre viewer API for navigation
- [ ] Implement chunk location mapping
- [ ] Add text highlighting in viewer
- [ ] Handle different book formats (EPUB, PDF, etc.)
- [ ] Test navigation accuracy

#### 1.3 Fix UI Theming (Day 4)
```python
# Create theme-aware styling system
class ThemeManager:
    def get_style(self, widget_type: str) -> str:
        """Get theme-appropriate styles"""
        palette = QApplication.palette()
        return self._generate_style(widget_type, palette)
```

**Tasks**:
- [ ] Remove all hard-coded colors
- [ ] Create ThemeManager class
- [ ] Use QPalette for color values
- [ ] Test with Calibre's light/dark themes
- [ ] Ensure accessibility compliance

### Phase 2: Core Features (Week 2)

#### 2.1 Index Management UI (Days 5-6)
```python
# Create index_manager_dialog.py
class IndexManagerDialog(QDialog):
    """Dialog for managing search index"""
    
    def __init__(self, plugin):
        # Show index statistics
        # List indexed books
        # Provide clear/rebuild options
        # Show storage usage
```

**Features**:
- [ ] Index statistics dashboard
- [ ] Book-by-book index status
- [ ] Clear entire index
- [ ] Clear specific books
- [ ] Rebuild index
- [ ] Storage usage visualization
- [ ] Export/import index

#### 2.2 Provider Plugin System (Days 7-8)
```python
# Create provider plugin architecture
class EmbeddingProviderPlugin:
    """Base class for embedding provider plugins"""
    
    @abstractmethod
    def get_provider_info(self) -> ProviderInfo:
        pass
    
    @abstractmethod
    def create_provider(self, config: dict) -> BaseEmbeddingProvider:
        pass
```

**Tasks**:
- [ ] Define provider plugin interface
- [ ] Create plugin discovery mechanism
- [ ] Move existing providers to plugin format
- [ ] Add provider management UI
- [ ] Document plugin development

### Phase 3: Enhanced Features (Week 3)

#### 3.1 Advanced Search Features (Days 9-10)
- [ ] Search history with quick recall
- [ ] Saved searches
- [ ] Search templates for common queries
- [ ] Export search results
- [ ] Batch operations on results

#### 3.2 Performance Optimizations (Days 11-12)
- [ ] Implement search result caching
- [ ] Add background index updates
- [ ] Optimize database queries
- [ ] Add index compression
- [ ] Implement incremental indexing

#### 3.3 User Experience Polish (Days 13-14)
- [ ] Add keyboard shortcuts
- [ ] Implement drag-and-drop for books
- [ ] Add tooltips and help system
- [ ] Create welcome/tutorial dialog
- [ ] Add progress notifications

## Technical Implementation Details

### 1. Metadata Fix Implementation

```python
# In search_engine.py
async def search(self, query: str, options: SearchOptions) -> List[SearchResult]:
    # ... existing search logic ...
    
    # After getting raw results, enrich with metadata
    enriched_results = []
    for raw_result in raw_results:
        # Get metadata from Calibre
        metadata = self.calibre_repo.get_book_metadata(raw_result.book_id)
        
        # Create enriched result
        result = SearchResult(
            chunk_id=raw_result.chunk_id,
            book_id=raw_result.book_id,
            book_title=metadata.get('title', 'Unknown Title'),
            authors=metadata.get('authors', ['Unknown Author']),
            chunk_text=raw_result.chunk_text,
            chunk_index=raw_result.chunk_index,
            similarity_score=raw_result.similarity_score,
            metadata=metadata
        )
        enriched_results.append(result)
    
    return enriched_results
```

### 2. Viewer Integration Implementation

```python
# In viewer_integration.py
def navigate_to_result(self, viewer, book_id: int, chunk_id: int):
    """Navigate viewer to search result"""
    # Get chunk info from database
    chunk = self.embedding_repo.get_chunk(chunk_id)
    
    # Calculate position in book
    # This requires understanding Calibre's viewer position system
    position = self._calculate_viewer_position(chunk)
    
    # Navigate viewer
    viewer.goto_position(position)
    
    # Highlight text
    viewer.highlight_text(chunk.text, duration=5000)
```

### 3. Theme-Aware Styling

```python
# In ui/theme_manager.py
class ThemeManager:
    @staticmethod
    def get_result_card_style() -> str:
        palette = QApplication.palette()
        return f"""
            ResultCard {{
                background-color: {palette.base().color().name()};
                border: 1px solid {palette.mid().color().name()};
                color: {palette.text().color().name()};
            }}
            ResultCard:hover {{
                background-color: {palette.alternateBase().color().name()};
                border-color: {palette.highlight().color().name()};
            }}
        """
```

## Testing Strategy

### Unit Tests
- [ ] Test metadata enrichment
- [ ] Test viewer navigation calculations
- [ ] Test theme manager with different palettes
- [ ] Test index management operations
- [ ] Test provider plugin loading

### Integration Tests
- [ ] Test full search flow with metadata
- [ ] Test viewer integration with different formats
- [ ] Test UI with Calibre themes
- [ ] Test index management workflow
- [ ] Test custom provider plugins

### User Acceptance Tests
- [ ] Search returns correct metadata
- [ ] View in Book navigates correctly
- [ ] UI readable in all themes
- [ ] Index management intuitive
- [ ] Custom providers work

## Documentation Updates

### User Documentation
- [ ] Update search guide with metadata info
- [ ] Document viewer integration features
- [ ] Add index management guide
- [ ] Create provider plugin guide

### Developer Documentation
- [ ] Document metadata flow
- [ ] Document viewer API usage
- [ ] Document theme system
- [ ] Document plugin architecture

## Success Metrics

1. **Metadata Display**: 100% of search results show correct author/title
2. **Viewer Navigation**: 95% accuracy in navigating to correct location
3. **Theme Support**: Works with all Calibre themes
4. **Index Management**: Users can manage index without command line
5. **Extensibility**: At least 2 custom provider plugins created

## Risk Mitigation

### Risk 1: Viewer API Limitations
**Mitigation**: Research viewer API early, have fallback to show page number

### Risk 2: Performance Impact of Metadata Lookups
**Mitigation**: Implement caching layer, batch lookups

### Risk 3: Theme Compatibility Issues
**Mitigation**: Test with multiple themes early, use QPalette exclusively

### Risk 4: Plugin System Complexity
**Mitigation**: Start simple, iterate based on feedback

## Timeline Summary

- **Week 1**: Critical fixes (metadata, viewer, theming)
- **Week 2**: Core features (index management, plugin system)
- **Week 3**: Polish and optimization

**Total Time**: 3 weeks to v1.0 release

## Next Steps

1. **Immediate** (Today):
   - Fix metadata extraction bug
   - Start viewer API research

2. **This Week**:
   - Complete Phase 1 critical fixes
   - Begin index management UI

3. **Next Week**:
   - Complete Phase 2 features
   - Begin testing and documentation

---
*This plan will be updated daily with progress. Check git commits for implementation details.*