# Implementation Quick Start Guide

**Created**: 2025-06-04  
**Purpose**: Quick reference for starting implementation

## 📚 Document Hierarchy

1. **This Document** - Where to start
2. **UI_BACKEND_INTEGRATION_DIAGNOSIS.md** - The 5 critical issues to fix
3. **COMPREHENSIVE_IMPLEMENTATION_PLAN.md** - Detailed step-by-step plan
4. **BACKUP_PLANS.md** - Alternative approaches if primary plans fail
5. **semantic_docs/calibre-semantic-spec-02.md** - Original requirements

## 🚀 Day 1 Checklist

### Morning: Setup & Validation (Phase 0)
```bash
# 1. Create working branch
git checkout -b feature/fix-integration-phase-0

# 2. Run existing tests to establish baseline
pytest tests/ -v

# 3. Validate each issue from diagnosis
calibre-debug -g  # Test issue #1: Can't test connection
# Try to configure and save - verify model conflicts
# Open Index Manager - verify display issues

# 4. Create test file for validation
touch tests/integration/test_diagnosis_validation.py
```

### Afternoon: First Fix (Issue #1)
```bash
# 1. Write failing test
# In test_diagnosis_validation.py:
def test_config_widget_gets_plugin_interface():
    # Test that ConfigWidget can access embedding service
    
# 2. Implement fix
# - Modify __init__.py: Pass actual_plugin_ to ConfigWidget
# - Modify config.py: Use plugin_interface for test_connection

# 3. Verify in live Calibre
calibre-debug -g

# 4. Commit
git add -A
git commit -m "fix(config): implement proper plugin reference passing for test connection

- Pass actual_plugin_ instance to ConfigWidget as plugin_interface
- Update _test_connection to use plugin_interface
- Add fallback when interface not available

Fixes Issue #1 from UI_BACKEND_INTEGRATION_DIAGNOSIS"
```

## 🎯 Priority Order

### Phase 1 Must-Fix Issues (Day 1-2):
1. **Issue #1**: Test Connection broken ← Start here!
2. **Issue #2**: Configuration conflicts
3. **Issue #3**: Index Manager display issues
4. **Issue #4**: Service initialization
5. **Issue #5**: Database metadata

### Phase 2 Requirements (Day 3-5):
1. Chunking strategies (P0)
2. Provider fallback (P0)
3. Complete metadata (P0)
4. Search modes (P1)

## 🧪 TDD Rhythm

For EVERY change:
```python
# 1. RED - Write test that fails
def test_feature():
    assert feature() == expected  # Fails

# 2. GREEN - Make it pass
def feature():
    return expected  # Passes

# 3. REFACTOR - Improve
def feature():
    # Real implementation

# 4. VERIFY - In Calibre
calibre-debug -g
# Test manually

# 5. COMMIT - With context
git commit -m "type(scope): description

- What changed
- Why it changed
- References issue"
```

## 🛠️ Useful Commands

```bash
# Run specific test file
pytest tests/integration/test_diagnosis_validation.py -v

# Test in Calibre with debug output
calibre-debug -g 2>&1 | tee debug.log

# Check what will be committed
git diff --staged

# Run plugin build
python scripts/build_plugin.py

# Install updated plugin
calibre-customize -a calibre-semantic-search.zip

# See plugin output
calibre-debug -g | grep -i semantic
```

## ⚠️ Before You Code

1. **Read** the existing code first (use Read tool)
2. **Search** for similar patterns (use Grep tool)
3. **Test** your understanding with simple experiments
4. **Document** assumptions in SPARC format
5. **Check** BACKUP_PLANS.md if stuck

## 🎨 Code Patterns to Follow

### Getting Configuration
```python
# Good - Single source
config = self.plugin.config
value = config.get('key')

# Bad - Direct access
value = JSONConfig('plugins/semantic_search')['key']
```

### Service Access
```python
# Good - Through registry/property
service = self.get_embedding_service()

# Bad - Direct creation
service = EmbeddingService(config)
```

### Error Handling
```python
# Good - User-friendly
try:
    result = operation()
except SpecificError as e:
    error_dialog(self.gui, "Operation Failed", 
                 "Could not complete because: " + str(e))

# Bad - Silent failure
try:
    result = operation()
except:
    pass
```

## 🔍 When Stuck

1. Check BACKUP_PLANS.md for alternatives
2. Review Calibre plugin docs in semantic_docs/calibre_repo/
3. Look at similar code in Calibre built-in plugins
4. Test minimal example in isolation
5. Ask: "What would SPARC do?"

## 📈 Progress Tracking

### Before Every Commit (Feature/Requirement/Milestone Complete):
1. **Update PROJECT_STATUS.md** - Critical for workspace context tracking
   - Mark completed items as ✅ 
   - Update completion percentages
   - Note any blockers or issues discovered
   - Adjust priorities if needed

2. **Update CHANGELOG.md** - Document what was accomplished
   - Add entry for what was added/changed/fixed
   - Reference requirement IDs if applicable
   - Note any breaking changes or important updates

3. **Commit with both documentation updates**
   - Include both PROJECT_STATUS.md and CHANGELOG.md in commit
   - Use conventional commit format
   - Reference requirement/issue numbers

### At End of Each Day:
4. **Review PROJECT_STATUS.md** - Ensure it reflects current reality
5. **Note what worked/didn't work** - Learning capture
6. **Adjust timeline if needed** - Realistic planning
7. **Plan tomorrow's tasks** - Clear next steps
8. **Ensure all work is committed** - Clean git state

### Workspace Context Tracking Rules:
- **Both PROJECT_STATUS.md and CHANGELOG.md updated before every commit**
- PROJECT_STATUS.md is the **single source of truth** for current status
- CHANGELOG.md tracks the history of what was accomplished
- This ensures documentation is never out of sync with code
- Perfect traceability between commits and documentation
- Other developers/AI assistants can quickly understand current state

---

**Remember**: Start small, test everything, commit often. The diagnosis might be wrong - that's why we validate first and have backup plans!