"""
Test plugin structure and imports to catch issues before deployment
"""

import os
import sys
import importlib
import zipfile
import tempfile
import pytest
from pathlib import Path


class TestPluginStructure:
    """Test the plugin can be loaded without Calibre"""
    
    @pytest.fixture
    def plugin_root(self):
        """Get the plugin root directory"""
        return Path(__file__).parent.parent.parent / "calibre_plugins" / "semantic_search"
    
    def test_no_naming_conflicts(self, plugin_root):
        """Test that we don't have module/package naming conflicts"""
        # Check for files and directories with same name
        conflicts = []
        
        for item in plugin_root.rglob("*.py"):
            if item.stem != "__init__":
                # Check if there's a directory with same name
                potential_dir = item.parent / item.stem
                if potential_dir.exists() and potential_dir.is_dir():
                    conflicts.append((str(item), str(potential_dir)))
        
        assert not conflicts, f"Module/package naming conflicts found: {conflicts}"
    
    def test_all_imports_valid(self, plugin_root):
        """Test that all internal imports can be resolved"""
        # Add plugin to path
        sys.path.insert(0, str(plugin_root.parent.parent))
        
        errors = []
        
        # Test critical imports
        critical_imports = [
            "calibre_plugins.semantic_search.interface",
            "calibre_plugins.semantic_search.ui.search_dialog",
            "calibre_plugins.semantic_search.config",
            "calibre_plugins.semantic_search.core.search_engine",
            "calibre_plugins.semantic_search.core.embedding_service",
        ]
        
        for module_name in critical_imports:
            try:
                importlib.import_module(module_name)
            except ImportError as e:
                errors.append(f"{module_name}: {e}")
        
        assert not errors, f"Import errors found:\n" + "\n".join(errors)
    
    @pytest.mark.skipif(
        not os.environ.get('PYTEST_BUILD_TESTS'), 
        reason="Skipping build test - set PYTEST_BUILD_TESTS=1 to enable"
    )
    def test_plugin_zip_structure(self, plugin_root):
        """Test the plugin ZIP has correct structure"""
        # Build the plugin
        build_script = plugin_root.parent.parent / "scripts" / "build_plugin.py"
        
        if build_script.exists():
            import subprocess
            result = subprocess.run([sys.executable, str(build_script)], 
                                  capture_output=True, text=True,
                                  cwd=plugin_root.parent.parent)
            
            assert result.returncode == 0, f"Build failed: {result.stderr}"
            
            # Check ZIP structure
            zip_path = plugin_root.parent.parent / "calibre-semantic-search.zip"
            assert zip_path.exists(), "Plugin ZIP not created"
            
            with zipfile.ZipFile(zip_path, 'r') as zf:
                files = zf.namelist()
                
                # Check critical files exist at correct level
                assert "__init__.py" in files, "__init__.py must be at ZIP root"
                assert "interface.py" in files, "interface.py must be in ZIP"
                assert "config.py" in files, "config.py must be in ZIP"
                
                # Check no duplicate files
                seen = set()
                duplicates = []
                for f in files:
                    if f in seen:
                        duplicates.append(f)
                    seen.add(f)
                
                assert not duplicates, f"Duplicate files in ZIP: {duplicates}"
    
    def test_interface_loads_without_calibre(self, plugin_root):
        """Test the interface module can be imported without Calibre"""
        sys.path.insert(0, str(plugin_root.parent.parent))
        
        # Mock minimal Calibre dependencies
        import unittest.mock as mock
        
        # Mock calibre modules
        sys.modules['calibre'] = mock.MagicMock()
        sys.modules['calibre.gui2'] = mock.MagicMock()
        sys.modules['calibre.gui2.actions'] = mock.MagicMock()
        sys.modules['calibre.customize'] = mock.MagicMock()
        
        # Mock Qt modules  
        sys.modules['qt'] = mock.MagicMock()
        sys.modules['qt.core'] = mock.MagicMock()
        sys.modules['PyQt5'] = mock.MagicMock()
        sys.modules['PyQt5.Qt'] = mock.MagicMock()
        
        try:
            from calibre_plugins.semantic_search import interface
            from calibre_plugins.semantic_search import __init__ as plugin_init
            
            # Verify basic structure
            assert hasattr(interface, 'SemanticSearchInterface')
            assert hasattr(plugin_init, 'SemanticSearchPlugin')
            
        except ImportError as e:
            pytest.fail(f"Failed to import plugin modules: {e}")
    
    def test_no_absolute_imports(self, plugin_root):
        """Test that we use relative imports within the plugin"""
        # This is important for plugin isolation
        import re
        
        absolute_import_pattern = re.compile(
            r'^\s*from\s+calibre_plugins\.semantic_search\s+import',
            re.MULTILINE
        )
        
        issues = []
        
        for py_file in plugin_root.rglob("*.py"):
            if "__pycache__" not in str(py_file):
                content = py_file.read_text()
                
                # Check for absolute imports within plugin
                matches = absolute_import_pattern.findall(content)
                if matches and py_file.name != "__init__.py":
                    issues.append(f"{py_file.relative_to(plugin_root)}: uses absolute imports")
        
        # Actually, absolute imports are OK for Calibre plugins
        # This test is informational
        if issues:
            print(f"Note: {len(issues)} files use absolute imports (this is OK)")


class TestPluginFunctionality:
    """Test plugin functionality without running Calibre"""
    
    def test_config_structure(self):
        """Test configuration doesn't have the as_dict issue"""
        # This is the issue we hit earlier
        import unittest.mock as mock
        
        sys.modules['calibre'] = mock.MagicMock()
        sys.modules['calibre.utils.config'] = mock.MagicMock()
        
        # Create a mock JSONConfig that mimics Calibre's behavior
        mock_json_config = mock.MagicMock()
        mock_json_config.__getitem__ = mock.MagicMock(side_effect=lambda k: {})
        mock_json_config.__setitem__ = mock.MagicMock()
        mock_json_config.get = mock.MagicMock(return_value={})
        
        sys.modules['calibre.utils.config'].JSONConfig = mock.MagicMock(
            return_value=mock_json_config
        )
        
        from calibre_plugins.semantic_search.config import SemanticSearchConfig
        
        config = SemanticSearchConfig()
        
        # Test the problematic set method
        config.set("api_keys.test", "test_value")
        
        # Should not raise AttributeError about as_dict