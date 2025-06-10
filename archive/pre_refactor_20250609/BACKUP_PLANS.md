# Backup Plans: Alternative Approaches and Contingencies

**Document Version**: 1.0  
**Created**: 2025-06-04  
**Purpose**: Alternative strategies if primary implementation plan encounters issues  
**Reference**: COMPREHENSIVE_IMPLEMENTATION_PLAN.md

## 🎯 Overview

This document provides fallback strategies for each major implementation area. Each backup plan includes:
- Trigger conditions (when to switch)
- Alternative approach
- Trade-offs
- Implementation notes

## 🔄 Diagnosis-Related Backup Plans

### BP-1: Plugin Reference Chain (Issue #1)

**If Primary Fix Fails**: Passing actual_plugin_ to ConfigWidget doesn't work

#### Alternative A: Global Registry Pattern
```python
# Create a global plugin registry
class PluginRegistry:
    _instance = None
    _plugins = {}
    
    @classmethod
    def register(cls, name, plugin):
        cls._plugins[name] = plugin
    
    @classmethod
    def get(cls, name):
        return cls._plugins.get(name)

# In SemanticSearchInterface.__init__
PluginRegistry.register('semantic_search', self)

# In ConfigWidget._test_connection
plugin = PluginRegistry.get('semantic_search')
```

**Trade-offs**: 
- ✅ Works regardless of Calibre's internals
- ❌ Global state (less clean)
- ❌ Potential memory leaks if not cleaned up

#### Alternative B: Configuration-Based Testing
```python
# Skip plugin reference entirely
def _test_connection(self):
    """Test connection using config values directly"""
    # Read config values from UI
    provider = self.provider_combo.currentText()
    api_key = self.api_key_edit.text()
    
    # Create temporary service just for testing
    from calibre_plugins.semantic_search.core import create_embedding_service
    temp_config = {
        'embedding_provider': provider,
        'api_key': api_key,
        # ... other config
    }
    
    try:
        service = create_embedding_service(temp_config)
        service.test_connection()
    except Exception as e:
        # Handle error
```

**Trade-offs**:
- ✅ No dependency on plugin instance
- ✅ Simpler implementation
- ❌ Duplicates service creation logic
- ❌ May not test actual runtime configuration

#### Alternative C: Deferred Testing
```python
# Add test connection to main menu instead
class SemanticSearchInterface:
    def genesis(self):
        # Add to menu
        self.test_connection_action = QAction("Test Connection", self.gui)
        self.test_connection_action.triggered.connect(self.test_connection)
        self.menu.addAction(self.test_connection_action)
    
    def test_connection(self):
        # Has full access to self and services
        if self.embedding_service:
            self.embedding_service.test_connection()
```

**Trade-offs**:
- ✅ Full access to plugin instance
- ✅ Can test actual runtime service
- ❌ Less convenient UX (not in config dialog)
- ❌ Requires config save before testing

### BP-2: Configuration Conflicts (Issue #2)

**If Primary Fix Fails**: Removing model selection causes user confusion

#### Alternative A: Separate Configuration Keys
```python
# Use different keys for different purposes
'ai_provider_model': 'text-embedding-3-small',  # For AI Provider tab
'indexing_model': 'text-embedding-3-small',     # For display in Indexing tab

# Sync them on save
def save_settings(self):
    model = self.model_edit.text()
    self.config.set('ai_provider_model', model)
    self.config.set('indexing_model', model)  # Keep in sync
```

**Trade-offs**:
- ✅ No UI changes needed
- ✅ Backward compatible
- ❌ Data duplication
- ❌ Sync complexity

#### Alternative B: Read-Only Display
```python
# Make indexing tab model field read-only
self.model_display = QLineEdit()
self.model_display.setReadOnly(True)
self.model_display.setStyleSheet("background-color: #f0f0f0;")

# Update from config on tab change
def on_tab_changed(self, index):
    if index == INDEXING_TAB:
        model = self.config.get('embedding_model')
        self.model_display.setText(model)
```

**Trade-offs**:
- ✅ Clear which field is authoritative
- ✅ No data conflicts
- ❌ Still have two displays
- ❌ Potential user confusion

### BP-3: Service Initialization (Issue #4)

**If Primary Fix Fails**: Service Registry pattern too complex or causes issues

#### Alternative A: Simple Lazy Loading
```python
class SemanticSearchInterface:
    def __init__(self):
        self._embedding_service = None
    
    @property
    def embedding_service(self):
        if self._embedding_service is None:
            config = self.config.as_dict()
            self._embedding_service = create_embedding_service(config)
        return self._embedding_service
    
    def invalidate_services(self):
        self._embedding_service = None
```

**Trade-offs**:
- ✅ Simple implementation
- ✅ Easy to understand
- ❌ No automatic config change detection
- ❌ Manual invalidation needed

#### Alternative B: Event-Based Updates
```python
# Use Qt signals for configuration changes
class ConfigWidget(QWidget):
    config_changed = pyqtSignal(dict)
    
    def save_settings(self):
        # Save config
        new_config = self.get_config_dict()
        self.config_changed.emit(new_config)

class SemanticSearchInterface:
    def __init__(self):
        # Connect to config changes
        self.config_widget.config_changed.connect(self.update_services)
    
    def update_services(self, new_config):
        self.embedding_service = create_embedding_service(new_config)
```

**Trade-offs**:
- ✅ Automatic updates
- ✅ Clean separation
- ❌ Requires careful signal management
- ❌ Potential timing issues

## 🏗️ Architecture-Related Backup Plans

### BP-4: Database Migration Failures

**If Primary Issue**: Migration script corrupts data or fails

#### Alternative A: Side-by-Side Migration
```python
# Create new tables instead of modifying existing
CREATE TABLE indexes_v2 (
    -- All new fields
);

# Gradually migrate data
INSERT INTO indexes_v2 SELECT * FROM indexes WHERE ...;

# Switch over when ready
ALTER TABLE indexes RENAME TO indexes_old;
ALTER TABLE indexes_v2 RENAME TO indexes;
```

**Trade-offs**:
- ✅ Safe rollback
- ✅ Can run in parallel
- ❌ More disk space
- ❌ Complex switching logic

#### Alternative B: Virtual Columns
```python
# Add computed columns for missing data
ALTER TABLE indexes ADD COLUMN provider_computed TEXT 
    GENERATED ALWAYS AS (
        CASE 
            WHEN config_snapshot LIKE '%openai%' THEN 'openai'
            ELSE 'unknown'
        END
    ) VIRTUAL;
```

**Trade-offs**:
- ✅ No data migration needed
- ✅ Backward compatible
- ❌ Limited to derivable data
- ❌ Performance impact

### BP-5: Performance Issues

**If Primary Issue**: Optimizations don't meet performance targets

#### Alternative A: Aggressive Caching
```python
class AggressiveCache:
    def __init__(self):
        self.embedding_cache = {}  # book_id -> embeddings
        self.search_cache = {}     # query -> results
        
    def get_or_compute(self, key, compute_func):
        if key not in self.cache:
            self.cache[key] = compute_func()
        return self.cache[key]
```

**Trade-offs**:
- ✅ Dramatic speed improvement
- ❌ High memory usage
- ❌ Cache invalidation complexity

#### Alternative B: Background Processing
```python
class BackgroundIndexer:
    def __init__(self):
        self.queue = Queue()
        self.worker = Thread(target=self.process_queue)
        self.worker.start()
    
    def index_book_async(self, book_id):
        self.queue.put(book_id)
        # Return immediately, process in background
```

**Trade-offs**:
- ✅ UI remains responsive
- ✅ Can process during idle time
- ❌ Complex state management
- ❌ Progress tracking harder

### BP-6: Chunking Strategy Complexity

**If Primary Issue**: Full chunking implementation too complex/time-consuming

#### Alternative A: External Library
```python
# Use langchain or similar
from langchain.text_splitter import RecursiveCharacterTextSplitter

def create_chunks(text, strategy='hybrid'):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=512,
        chunk_overlap=50,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    return splitter.split_text(text)
```

**Trade-offs**:
- ✅ Battle-tested implementation
- ✅ Quick to implement
- ❌ External dependency
- ❌ Less control

#### Alternative B: Simplified Strategies
```python
# Implement only two strategies initially
class SimpleChunking:
    @staticmethod
    def fixed_size(text, size=512):
        # Basic implementation
        return [text[i:i+size] for i in range(0, len(text), size-50)]
    
    @staticmethod
    def paragraph_based(text):
        # Split on double newlines only
        return text.split('\n\n')
```

**Trade-offs**:
- ✅ Faster implementation
- ✅ Easier to test
- ❌ Less sophisticated
- ❌ May need rewrite later

## 🚨 Emergency Procedures

### EP-1: Complete Integration Failure

**Symptoms**: Nothing works after fixes, Calibre crashes, etc.

**Response**:
1. **Immediate**: Revert all changes
2. **Diagnostic**: Enable verbose logging
3. **Incremental**: Apply one fix at a time
4. **Alternative**: Create minimal working plugin first

### EP-2: Data Loss

**Symptoms**: Books disappear, indexes corrupted, etc.

**Response**:
1. **Stop**: Halt all operations
2. **Backup**: Copy entire Calibre directory
3. **Analyze**: Use SQLite tools to inspect
4. **Recover**: Use backup or rebuild indexes

### EP-3: Performance Degradation

**Symptoms**: Searches take minutes, UI freezes, etc.

**Response**:
1. **Profile**: Use cProfile to find bottlenecks
2. **Disable**: Turn off features one by one
3. **Optimize**: Focus on hot paths only
4. **Degrade**: Reduce functionality if needed

## 📊 Decision Matrix

### When to Switch to Backup Plan

| Condition | Primary Plan | Backup Plan | Decision Criteria |
|-----------|--------------|-------------|-------------------|
| Config access fails | Pass plugin reference | Global registry | 2+ hours debugging |
| Migration fails | Alter table | New tables | Any data loss |
| Performance miss | Optimize code | Add caching | >200ms search |
| Chunking too complex | Full implementation | Use library | >1 day effort |
| Service registry issues | Full pattern | Simple lazy load | >4 hours debugging |

## 🔄 Rollback Procedures

### Code Rollback
```bash
# Tag before major changes
git tag before-phase-1
git push --tags

# Rollback if needed
git checkout before-phase-1
git checkout -b hotfix/emergency-rollback
```

### Database Rollback
```sql
-- Always create backup
.backup /path/to/backup.db

-- Restore if needed
.restore /path/to/backup.db

-- Or use saved schema
DROP TABLE IF EXISTS indexes;
CREATE TABLE indexes AS SELECT * FROM indexes_backup;
```

### Configuration Rollback
```python
# Save configuration
import json
with open('config_backup.json', 'w') as f:
    json.dump(config.as_dict(), f)

# Restore if needed
with open('config_backup.json', 'r') as f:
    backup_config = json.load(f)
    config.restore(backup_config)
```

## 📝 Lessons Learned Integration

After using any backup plan:

1. **Document why** primary plan failed
2. **Update** main plan with lessons
3. **Create** test to prevent recurrence
4. **Share** knowledge with team
5. **Consider** making backup plan primary

---

**Remember**: The best backup plan is one you never need to use. But when you do need it, it should be clear, tested, and ready to go.