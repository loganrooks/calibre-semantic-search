"""
Test-driven development for ConfigPresenter - MVP pattern implementation
Following DEVELOPMENT_GUIDE.md TDD mandate: "No implementation code is written until a failing unit test that defines the feature's behavior has been written and run."
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

# Mock the config import to avoid Calibre dependencies in tests
with patch('calibre_plugins.semantic_search.presenters.config_presenter.SemanticSearchConfig'):
    from calibre_plugins.semantic_search.presenters.config_presenter import ConfigPresenter


class TestConfigPresenter:
    """Test ConfigPresenter for MVP pattern compliance"""
    
    def test_presenter_has_no_qt_imports(self):
        """MANDATORY: Presenter must not contain any Qt imports (ARCHITECTURE.md System Invariant)"""
        # This will fail until we create the presenter
        presenter = ConfigPresenter(Mock())
        
        # Verify presenter module has no Qt imports
        import calibre_plugins.semantic_search.presenters.config_presenter as presenter_module
        import sys
        
        # Check that no Qt modules are imported
        qt_modules = [name for name in sys.modules.keys() if 'qt' in name.lower() or 'pyqt' in name.lower()]
        presenter_imports = getattr(presenter_module, '__dict__', {})
        
        for qt_module in qt_modules:
            assert qt_module not in presenter_imports, f"Presenter illegally imports Qt module: {qt_module}"
    
    @patch('calibre_plugins.semantic_search.presenters.config_presenter.SemanticSearchConfig')
    def test_presenter_initializes_with_view(self, mock_config_class):
        """Presenter should initialize with view reference and config"""
        mock_view = Mock()
        mock_config_instance = Mock()
        mock_config_class.return_value = mock_config_instance
        
        presenter = ConfigPresenter(mock_view)
        
        assert presenter.view == mock_view
        assert hasattr(presenter, 'config')
        assert presenter.config == mock_config_instance
    
    def test_presenter_handles_provider_change(self):
        """Presenter should handle provider selection changes and update view"""
        mock_view = Mock()
        presenter = ConfigPresenter(mock_view)
        
        # Handle provider change
        presenter.on_provider_changed("openai")
        
        # View should be updated with provider-specific settings
        mock_view.show_provider_section.assert_called_with("openai")
        mock_view.update_model_list.assert_called()
        mock_view.set_model_placeholder.assert_called()
    
    def test_presenter_updates_models_for_provider(self):
        """Presenter should provide correct model lists for each provider"""
        mock_view = Mock()
        presenter = ConfigPresenter(mock_view)
        
        # Test OpenAI models
        presenter.on_provider_changed("openai")
        call_args = mock_view.update_model_list.call_args[0][0]  # Get first argument
        assert any("text-embedding-3-large" in model for model in call_args)
        assert any("⭐" in model for model in call_args)  # Should have recommended models
        
        # Test Vertex AI models  
        mock_view.reset_mock()
        presenter.on_provider_changed("vertex_ai")
        call_args = mock_view.update_model_list.call_args[0][0]
        assert any("text-embedding-004" in model for model in call_args)
    
    def test_presenter_validates_provider_config(self):
        """Presenter should validate provider-specific configurations"""
        mock_view = Mock()
        presenter = ConfigPresenter(mock_view)
        
        # Test OpenAI validation
        result = presenter.validate_provider_config("openai", "", "text-embedding-3-small")
        assert not result['valid']
        assert "API key is required" in result['error']
        
        result = presenter.validate_provider_config("openai", "sk-test123", "text-embedding-3-small")
        assert result['valid']
        
        # Test invalid API key format
        result = presenter.validate_provider_config("openai", "invalid-key", "text-embedding-3-small")
        assert not result['valid']
        assert "should start with" in result['error']
    
    def test_presenter_handles_connection_testing(self):
        """Presenter should orchestrate connection testing without blocking UI"""
        mock_view = Mock()
        presenter = ConfigPresenter(mock_view)
        
        # Mock the connection test
        with patch.object(presenter, '_test_connection_async') as mock_test:
            presenter.test_connection("openai", "sk-test123", "text-embedding-3-small")
            
            # Should show progress in view
            mock_view.show_connection_progress.assert_called_with(True)
            
            # Should start async test
            mock_test.assert_called_once()
    
    def test_presenter_loads_configuration(self):
        """Presenter should load configuration and update view"""
        mock_view = Mock()
        
        # Mock config with test data
        mock_config = Mock()
        mock_config.get.side_effect = lambda key, default=None: {
            "embedding_provider": "openai",
            "embedding_model": "text-embedding-3-small",
            "api_keys.openai": "sk-test123",
            "search_options.default_limit": 20,
            "search_options.similarity_threshold": 0.7
        }.get(key, default)
        
        with patch('calibre_plugins.semantic_search.presenters.config_presenter.SemanticSearchConfig', return_value=mock_config):
            presenter = ConfigPresenter(mock_view)
            presenter.load_configuration()
            
            # View should be updated with loaded values
            mock_view.set_provider.assert_called_with("openai")
            mock_view.set_model.assert_called_with("text-embedding-3-small")
            mock_view.set_api_key.assert_called_with("sk-test123")
    
    def test_presenter_saves_configuration(self):
        """Presenter should save configuration from view values"""
        mock_view = Mock()
        mock_view.get_provider.return_value = "openai"
        mock_view.get_model.return_value = "text-embedding-3-large ⭐ (3072 dims, best quality)"
        mock_view.get_api_key.return_value = "sk-test123"
        mock_view.get_result_limit.return_value = 25
        
        presenter = ConfigPresenter(mock_view)
        presenter.save_configuration()
        
        # Config should be updated with clean values
        presenter.config.set.assert_any_call("embedding_provider", "openai")
        presenter.config.set.assert_any_call("embedding_model", "text-embedding-3-large")  # Clean model name
        presenter.config.set.assert_any_call("api_keys.openai", "sk-test123")
    
    def test_presenter_handles_model_selection(self):
        """Presenter should handle model selection and show model info"""
        mock_view = Mock()
        presenter = ConfigPresenter(mock_view)
        
        # Test model with metadata
        presenter.on_model_changed("text-embedding-3-large ⭐ (3072 dims, best quality)")
        
        # View should show helpful model info
        mock_view.set_model_info.assert_called()
        call_args = mock_view.set_model_info.call_args[0][0]
        assert "⭐ Recommended" in call_args
        assert "3072 dims" in call_args
    
    def test_presenter_cleans_model_names(self):
        """Presenter should clean model names for configuration storage"""
        mock_view = Mock()
        presenter = ConfigPresenter(mock_view)
        
        # Test cleaning various model name formats
        assert presenter._clean_model_name("text-embedding-3-large ⭐ (3072 dims, best quality)") == "text-embedding-3-large"
        assert presenter._clean_model_name("embed-english-v3.0 ⭐ (1024 dims, latest)") == "embed-english-v3.0"
        assert presenter._clean_model_name("simple-model") == "simple-model"
    
    def test_presenter_mock_provider_handling(self):
        """Presenter should handle mock provider specially (no validation needed)"""
        mock_view = Mock()
        presenter = ConfigPresenter(mock_view)
        
        # Mock provider should always validate successfully
        result = presenter.validate_provider_config("mock", "", "mock-embedding")
        assert result['valid']
        
        # Connection test should succeed immediately
        presenter.test_connection("mock", "", "mock-embedding")
        mock_view.show_connection_result.assert_called_with(True, "Mock provider - no real connection needed")
    
    def test_presenter_handles_vertex_ai_specifics(self):
        """Presenter should handle Vertex AI specific configuration"""
        mock_view = Mock()
        presenter = ConfigPresenter(mock_view)
        
        # Vertex AI requires project ID
        result = presenter.validate_provider_config("vertex_ai", "", "text-embedding-004", project_id="")
        assert not result['valid']
        assert "Project ID is required" in result['error']
        
        result = presenter.validate_provider_config("vertex_ai", "", "text-embedding-004", project_id="my-project")
        assert result['valid']
    
    def test_presenter_separation_of_concerns(self):
        """Presenter should delegate UI updates to view, not handle Qt directly"""
        mock_view = Mock()
        presenter = ConfigPresenter(mock_view)
        
        # Presenter should not directly manipulate Qt widgets
        assert not hasattr(presenter, 'widget')
        assert not hasattr(presenter, 'combo')
        assert not hasattr(presenter, 'layout')
        
        # All UI updates should go through view methods
        presenter.on_provider_changed("openai")
        
        # Verify view methods were called (not direct Qt manipulation)
        assert mock_view.show_provider_section.called
        assert mock_view.update_model_list.called