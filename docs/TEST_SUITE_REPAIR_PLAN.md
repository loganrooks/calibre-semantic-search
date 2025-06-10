# Test Suite Repair Plan

**Created:** 2025-06-09  
**Objective:** Restore test suite to reliable state where all failures are meaningful

## Priority Matrix

| Priority | Category | Root Cause | Impact |
|----------|----------|------------|---------|
| **CRITICAL** | EPUB Integration | AsyncMock issue | Core functionality broken |
| **HIGH** | Calibre Integration | ThreadedJob import | Plugin won't load |
| **HIGH** | Index Management | Missing module | UI features unavailable |
| **HIGH** | Focus Bug | Known active bug | User experience degraded |
| **MEDIUM** | Config UI | TDD placeholders | Features not implemented |
| **LOW** | Delayed Init | Qt initialization | Test infrastructure only |

## Detailed Repair Instructions

### 1. EPUB INTEGRATION (CRITICAL)
**File:** `tests/integration/test_epub_extraction_fix.py`  
**Error:** `object Mock can't be used in 'await' expression`  
**Root Cause:** Using `Mock()` instead of `AsyncMock()` for async methods

**Fix Steps:**
1. Import `AsyncMock` from `unittest.mock`
2. Replace `embedding_service = Mock()` with `embedding_service = AsyncMock()`
3. Ensure `generate_embedding` returns appropriate async response
4. Verify all async methods are properly mocked

**Verification:**
```bash
pytest tests/integration/test_epub_extraction_fix.py -v
# Should see actual indexing logic execute and store embeddings
```

### 2. CALIBRE INTEGRATION (HIGH)
**File:** `tests/ui/test_actual_calibre_integration.py`  
**Error:** `AssertionError: interface.py still imports ThreadedJob`  
**Root Cause:** Direct import of ThreadedJob violates test expectations

**Fix Steps:**
1. Open `calibre_plugins/semantic_search/interface.py`
2. Remove line: `from calibre.gui2.threaded_jobs import ThreadedJob`
3. Ensure all threading handled via BackgroundJobManager
4. Update any code that directly uses ThreadedJob

**Verification:**
```bash
pytest tests/ui/test_actual_calibre_integration.py::test_interface_does_not_import_threaded_job_at_all -v
```

### 3. INDEX MANAGEMENT (HIGH)
**File:** `tests/ui/test_index_management_ui.py`  
**Error:** `ModuleNotFoundError: No module named 'calibre_plugins.semantic_search.ui.index_detector'`  
**Root Cause:** Missing module that tests expect

**Fix Steps:**
1. Search codebase for `IndexDetector` references
2. If found elsewhere, fix import path
3. If not found, create `calibre_plugins/semantic_search/ui/index_detector.py`:
```python
# Placeholder implementation based on test expectations
class IndexDetector:
    def __init__(self, embedding_repo):
        self.embedding_repo = embedding_repo
    
    def get_index_status(self, book_ids):
        # Return status dict for each book
        return {book_id: self._check_status(book_id) for book_id in book_ids}
    
    def _check_status(self, book_id):
        # Implementation based on test requirements
        pass
```

**Verification:**
```bash
pytest tests/ui/test_index_management_ui.py -v
```

### 4. FOCUS BUG (HIGH)
**Files:** `tests/ui/test_focus_stealing_bug_BUG_FOCUS_STEAL_20250607.py`  
**Status:** These are EXPECTED FAILURES - tests designed to catch the bug

**Fix Steps:**
1. This requires application fix, not test fix
2. Create detailed UI_REWORK_PLAN.md for MVP refactoring
3. Fix will involve:
   - Separating UI logic from view
   - Proper event handling without focus loss
   - Eliminating timer-based updates during typing

**Note:** These tests should REMAIN FAILING until bug is fixed

### 5. CONFIG UI (MEDIUM)  
**File:** `tests/ui/test_config_ui_redesign_tdd.py`  
**Status:** TDD placeholders with `assert False`

**Fix Steps:**
1. These are not bugs but unimplemented features
2. Use test descriptions as specifications
3. Implement:
   - Provider selection UI sections
   - Searchable model dropdown with metadata
   - Progressive disclosure patterns

**Note:** Follow TDD - tests guide implementation

### 6. DELAYED INIT (LOW)
**File:** `tests/integration/test_delayed_initialization.py`  
**Error:** Test collection timeout

**Fix Steps:**
1. Check for top-level Qt imports in test file
2. Move Qt imports inside test functions
3. Use pytest-qt fixtures appropriately:
```python
def test_something(qtbot):  # qtbot manages Qt event loop
    from qt.core import QWidget  # Import inside function
    widget = QWidget()
    qtbot.addWidget(widget)
```

**Verification:**
```bash
pytest tests/integration/test_delayed_initialization.py -v --timeout=10
```

## Execution Order

1. **First:** Fix AsyncMock in EPUB tests (blocks core functionality)
2. **Second:** Remove ThreadedJob import (blocks plugin loading)
3. **Third:** Create missing IndexDetector (blocks UI features)
4. **Fourth:** Document focus bug fix plan (active user issue)
5. **Fifth:** Begin implementing config UI features (enhancement)
6. **Last:** Fix test infrastructure issues (developer convenience)

## Success Criteria

- All tests either PASS or FAIL with meaningful errors
- No infrastructure failures (timeouts, import errors)
- No mock/async errors
- Focus bug tests remain failing (expected)
- Config UI tests guide feature implementation