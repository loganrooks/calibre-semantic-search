# TDD Integration Plan - UI Backend Connection

## Strategy: Integration-Focused TDD

We have tested business logic. Now we need to TDD the integration layer that connects UI to backend services.

## Phase 1: Prepare for TDD (Current State)

### 1.1 Revert UI Implementation
```bash
git checkout calibre_plugins/semantic_search/ui/search_dialog.py
git checkout calibre_plugins/semantic_search/ui.py
```
This gives us a clean slate for TDD.

### 1.2 Keep What's Tested
- ✅ Keep `search_business_logic.py` (15 passing tests)
- ✅ Keep `test_search_business_logic.py` 
- ✅ Keep architectural pseudocode for reference

## Phase 2: Create Integration Contract Tests

### 2.1 Define Integration Points
We need to test these integration points WITHOUT Qt/Calibre dependencies:

1. **SearchDialogPresenter** - Coordinates UI and business logic
2. **SearchEngineFactory** - Creates search engine with dependencies  
3. **IndexingJobFactory** - Creates indexing jobs
4. **ViewerNavigator** - Handles book navigation

### 2.2 Write Failing Integration Tests

```python
# test_search_integration.py

class TestSearchDialogPresenter:
    """Test the presenter that connects UI to business logic"""
    
    def test_search_with_valid_query(self):
        # GIVEN: Mocked dependencies
        mock_view = Mock()
        mock_search_engine = Mock()
        mock_validator = Mock()
        mock_cache = Mock()
        
        presenter = SearchDialogPresenter(
            view=mock_view,
            search_engine=mock_search_engine,
            validator=mock_validator,
            cache=mock_cache
        )
        
        # WHEN: Valid search is performed
        presenter.perform_search("valid query")
        
        # THEN: Should coordinate properly
        mock_validator.validate.assert_called_once()
        mock_cache.get.assert_called_once()
        mock_search_engine.search.assert_called_once()
        mock_view.show_results.assert_called_once()
```

## Phase 3: TDD Implementation Cycle

### 3.1 Red Phase - Write Failing Tests
1. Run test → See it fail (no presenter exists)
2. Create minimal presenter class
3. Run test → See it fail (no methods)
4. Add method signatures
5. Run test → See it fail (no implementation)

### 3.2 Green Phase - Minimal Implementation
```python
class SearchDialogPresenter:
    def __init__(self, view, search_engine, validator, cache):
        self.view = view
        self.search_engine = search_engine
        self.validator = validator
        self.cache = cache
    
    def perform_search(self, query):
        # Minimal implementation to pass test
        validation = self.validator.validate(query)
        if validation.is_valid:
            self.cache.get(query)
            self.search_engine.search(query)
            self.view.show_results([])
```

### 3.3 Refactor Phase
- Extract methods
- Add error handling
- Improve code structure
- Keep tests passing!

## Phase 4: Connect to Actual UI

### 4.1 Adapter Pattern
Create adapters that wrap Qt/Calibre components:

```python
class QtViewAdapter:
    """Adapts Qt dialog to our interface"""
    def __init__(self, qt_dialog):
        self.qt_dialog = qt_dialog
    
    def show_results(self, results):
        # Translate to Qt calls
        self.qt_dialog.results_list.clear()
        for result in results:
            self.qt_dialog.add_result(result)
```

### 4.2 Dependency Injection
Modify actual UI to use presenter:

```python
class SemanticSearchDialog(QDialog):
    def __init__(self, gui, plugin):
        super().__init__(gui)
        
        # Create presenter with real dependencies
        self.presenter = SearchDialogPresenter(
            view=QtViewAdapter(self),
            search_engine=self._create_search_engine(),
            validator=SearchQueryValidator(),
            cache=SearchCacheManager()
        )
```

## Phase 5: Specific Test Scenarios

### 5.1 Search Flow Tests
- [ ] Empty query validation
- [ ] Cache hit scenario  
- [ ] Cache miss scenario
- [ ] Search error handling
- [ ] Async search coordination

### 5.2 Indexing Flow Tests  
- [ ] Single book indexing
- [ ] Batch indexing
- [ ] Progress reporting
- [ ] Error recovery

### 5.3 Navigation Tests
- [ ] View in book with position
- [ ] View in book fallback
- [ ] Find similar passages

## Key Principles

1. **Test First**: Always write test before implementation
2. **Run Tests**: Must see test fail before implementing
3. **Minimal Implementation**: Just enough to pass
4. **Refactor Safely**: Only when tests are green
5. **Mock External Dependencies**: No Qt/Calibre in tests

## Success Criteria

- [ ] All integration tests can run without Qt/Calibre
- [ ] Each test follows Red-Green-Refactor cycle
- [ ] Business logic remains separate and tested
- [ ] UI code is thin and delegates to presenter
- [ ] Integration is properly tested

## Next Immediate Steps

1. Revert UI implementation files
2. Create `test_search_integration.py` with first failing test
3. See test fail
4. Create minimal `SearchDialogPresenter` class
5. Implement just enough to pass test
6. Refactor and continue