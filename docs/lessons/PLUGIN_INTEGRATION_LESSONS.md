# Calibre Plugin Integration Lessons Learned

## Key Issues Encountered and Solutions

### 1. **Module/Package Naming Conflict**
**Issue**: Had both `ui.py` (module) and `ui/` (directory) which caused:
```
ModuleNotFoundError: 'calibre_plugins.semantic_search.ui' is not a package
```

**Solution**: Renamed `ui.py` to `interface.py` to avoid conflict.

**Lesson**: Never have a module and package with the same name in Python.

### 2. **Qt Import Compatibility**
**Issue**: Using `Qt.ToolButtonTextBesideIcon` caused TypeError in toolbar customization.

**Solution**: 
- Use `qt.core` imports instead of `PyQt5`
- Use proper enum: `QToolButton.ToolButtonPopupMode.MenuButtonPopup`

**Lesson**: Calibre uses its own Qt wrapper; always import from `qt.core`.

### 3. **Icon Loading**
**Issue**: Plugin appeared without icon in toolbar.

**Solution**: 
- Set icon in `action_spec` tuple: `("Name", "icon.png", "Tooltip", None)`
- Use Calibre's built-in icons when possible

### 4. **Configuration JSONConfig**
**Issue**: `JSONConfig` doesn't have `as_dict()` method in Calibre 8.3.

**Solution**: Iterate over keys manually instead of using `as_dict()`.

### 5. **Viewer Integration** 
**Issue**: `viewer_opened` signal doesn't exist in all Calibre versions.

**Solution**: Check if signal exists before connecting:
```python
if hasattr(self.gui, 'viewer_opened'):
    self.gui.viewer_opened.connect(self.viewer_opened)
```

## Better Development Practices

### 1. **Create Integration Tests**
```python
# Test plugin structure before deployment
def test_no_naming_conflicts():
    # Check for module/package conflicts
    
def test_plugin_zip_structure():
    # Verify ZIP has correct structure
```

### 2. **Use Debug Scripts**
- `test_api_direct.py` - Test embedding providers without UI
- `check_plugin_compatibility.py` - Analyze code for common issues
- `test_plugin_structure.py` - Automated tests for plugin integrity

### 3. **Debugging in Calibre**
```bash
# Run with debug output
calibre-debug -g 

# Check logs
~/.config/calibre/plugins/

# Add debug prints
print(f"[Semantic Search] Debug: {message}")
```

### 4. **Common Calibre Plugin Patterns**
```python
# Correct InterfaceAction structure
class MyPlugin(InterfaceAction):
    name = 'Plugin Name'
    action_spec = ('Text', 'icon.png', 'Tooltip', None)
    popup_type = QToolButton.ToolButtonPopupMode.MenuButtonPopup
    allowed_in_toolbar = True
    allowed_in_menu = True
    
    def genesis(self):
        # One-time setup
        self.qaction.triggered.connect(self.show_dialog)
```

### 5. **Testing Without Constant Reinstalls**
1. Create unit tests that mock Calibre dependencies
2. Use standalone test scripts for API testing
3. Build automated checks into CI/CD pipeline
4. Test imports and structure before building ZIP

## Root Cause Analysis

Most issues stemmed from:
1. **Lack of automated testing** - Manual testing is slow and error-prone
2. **Assumptions about Calibre's API** - Need to check actual Calibre source
3. **Python import system complexity** - Module/package conflicts are subtle
4. **Version compatibility** - Calibre's API changes between versions

## Recommendations

1. **Always test with automated scripts first**
2. **Check Calibre source code** (~/Code/calibre-src/) for correct patterns
3. **Create regression tests** for each bug fixed
4. **Use proper Python package structure** (no naming conflicts)
5. **Mock dependencies** for faster testing cycles

## Next Steps

1. Complete viewer context menu integration
2. Add more comprehensive integration tests
3. Create CI/CD pipeline with automated testing
4. Document all Calibre API dependencies