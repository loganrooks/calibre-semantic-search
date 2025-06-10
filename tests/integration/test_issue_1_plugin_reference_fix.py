#!/usr/bin/env python3
"""
TDD tests for Issue #1: Test Connection Plugin Reference Chain fix

RED-GREEN-REFACTOR approach:
1. RED: Write failing test
2. GREEN: Make minimal fix to pass
3. REFACTOR: Improve implementation
"""

import pytest
from unittest.mock import Mock, patch

def test_plugin_config_widget_gets_plugin_interface():
    """Test that config_widget() passes plugin interface to ConfigWidget"""
    
    # Mock the actual plugin interface
    mock_interface = Mock()
    mock_interface.get_embedding_service.return_value = Mock()
    
    # Mock the plugin class
    from calibre_plugins.semantic_search import SemanticSearchPlugin
    plugin = SemanticSearchPlugin()
    plugin.actual_plugin_ = mock_interface
    
    # This should pass plugin interface to ConfigWidget
    with patch('calibre_plugins.semantic_search.config.ConfigWidget') as MockConfigWidget:
        mock_widget = Mock()
        MockConfigWidget.return_value = mock_widget
        
        # Call config_widget - this should pass plugin_interface
        widget = plugin.config_widget()
        
        # Test that plugin interface was passed
        assert hasattr(mock_widget, 'plugin_interface'), \
            "ConfigWidget should have plugin_interface attribute set"
        assert mock_widget.plugin_interface == mock_interface, \
            "plugin_interface should be the actual plugin interface"

def test_config_widget_test_connection_uses_plugin_interface():
    """Test that _test_connection uses plugin_interface instead of parent chain"""
    
    from calibre_plugins.semantic_search.config import ConfigWidget
    
    # Create ConfigWidget with plugin interface
    config_widget = ConfigWidget()
    
    # Mock plugin interface with embedding service
    mock_interface = Mock()
    mock_service = Mock()
    mock_service.test_connection.return_value = "Connection successful"
    mock_interface.get_embedding_service.return_value = mock_service
    
    # Set plugin interface directly (this is what the fix should enable)
    config_widget.plugin_interface = mock_interface
    
    # Mock QMessageBox to avoid GUI
    with patch('calibre_plugins.semantic_search.config.QMessageBox') as mock_msg_box:
        with patch('asyncio.new_event_loop') as mock_loop:
            mock_loop_instance = Mock()
            mock_loop.return_value = mock_loop_instance
            mock_loop_instance.run_until_complete.return_value = "Success"
            
            # This should use plugin_interface, not parent chain
            if hasattr(config_widget, '_test_connection'):
                config_widget._test_connection()
                
                # Verify it used the plugin interface
                mock_interface.get_embedding_service.assert_called_once()
                
                # Should not show error message
                mock_msg_box.critical.assert_not_called()

def test_config_widget_without_plugin_interface_shows_error():
    """Test that ConfigWidget shows error when plugin_interface not available"""
    
    from calibre_plugins.semantic_search.config import ConfigWidget
    
    config_widget = ConfigWidget()
    # Don't set plugin_interface - this should trigger fallback error
    
    with patch('calibre_plugins.semantic_search.config.QMessageBox') as mock_msg_box:
        if hasattr(config_widget, '_test_connection'):
            config_widget._test_connection()
            
            # Should show error message when plugin_interface not available
            mock_msg_box.critical.assert_called_once()
            
            # Error message should mention plugin interface not available
            call_args = mock_msg_box.critical.call_args[0]
            error_message = call_args[2]  # Third argument is the message
            assert 'interface not available' in error_message.lower()

if __name__ == '__main__':
    print("🔴 RED Phase: Running tests for Issue #1 fix")
    print("These should FAIL initially, then PASS after implementing fix")
    
    pytest.main([__file__, '-v'])