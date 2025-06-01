"""
Test AutoCompleteScope widget using TDD

This test verifies autocomplete functionality for author/tag/book selection
instead of dropdowns.
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os

# Mock calibre before importing anything
sys.modules['calibre'] = Mock()
sys.modules['calibre.gui2'] = Mock()

# Add path for modules
project_path = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_path)


class TestAutoCompleteScope:
    """Test autocomplete scope selector functionality"""
    
    def test_autocomplete_scope_shows_author_suggestions(self):
        """
        Test that AutoCompleteScope shows author suggestions
        when user types in author field
        """
        # GIVEN: Mock GUI with author data
        mock_gui = Mock()
        mock_db = Mock()
        mock_gui.current_db.new_api = mock_db
        
        # Mock author data from library
        mock_db.all_field_names.return_value = {
            'authors': ['Aristotle', 'Plato', 'Kant', 'Hegel', 'Nietzsche']
        }
        
        # Import and create AutoCompleteScope widget (this will fail initially!)
        from calibre_plugins.semantic_search.ui.widgets import AutoCompleteScope
        
        scope_widget = AutoCompleteScope(mock_gui)
        
        # WHEN: User types "Ar" in author field
        scope_widget.set_scope_type("authors")
        suggestions = scope_widget.get_completions("Ar")
        
        # THEN: Should show matching authors
        assert "Aristotle" in suggestions
        assert "Plato" not in suggestions  # Doesn't match "Ar"
        assert len(suggestions) >= 1
    
    def test_autocomplete_scope_shows_tag_suggestions(self):
        """
        Test that AutoCompleteScope shows tag suggestions
        when user types in tag field
        """
        # GIVEN: Mock GUI with tag data
        mock_gui = Mock()
        mock_db = Mock()
        mock_gui.current_db.new_api = mock_db
        
        # Mock tag data from library
        mock_db.all_field_names.return_value = {
            'tags': ['Philosophy', 'Ethics', 'Metaphysics', 'Logic', 'Political']
        }
        
        from calibre_plugins.semantic_search.ui.widgets import AutoCompleteScope
        scope_widget = AutoCompleteScope(mock_gui)
        
        # WHEN: User types "phil" in tag field
        scope_widget.set_scope_type("tags")
        suggestions = scope_widget.get_completions("phil")
        
        # THEN: Should show matching tags (case insensitive)
        assert "Philosophy" in suggestions
        assert "Political" not in suggestions  # Doesn't match "phil"
    
    def test_autocomplete_scope_handles_multi_selection(self):
        """
        Test that AutoCompleteScope allows selecting multiple items
        """
        # GIVEN: AutoCompleteScope widget
        mock_gui = Mock()
        mock_db = Mock()
        mock_gui.current_db.new_api = mock_db
        mock_db.all_field_names.return_value = {
            'authors': ['Aristotle', 'Plato', 'Kant']
        }
        
        from calibre_plugins.semantic_search.ui.widgets import AutoCompleteScope
        scope_widget = AutoCompleteScope(mock_gui)
        scope_widget.set_scope_type("authors")
        
        # WHEN: User selects multiple authors
        scope_widget.add_selection("Aristotle")
        scope_widget.add_selection("Plato")
        
        # THEN: Should track multiple selections
        selections = scope_widget.get_selected_items()
        assert "Aristotle" in selections
        assert "Plato" in selections
        assert len(selections) == 2
    
    def test_autocomplete_scope_prevents_invalid_input(self):
        """
        Test that AutoCompleteScope prevents arbitrary text input
        """
        # GIVEN: AutoCompleteScope with known data
        mock_gui = Mock()
        mock_db = Mock()
        mock_gui.current_db.new_api = mock_db
        mock_db.all_field_names.return_value = {
            'authors': ['Aristotle', 'Plato']
        }
        
        from calibre_plugins.semantic_search.ui.widgets import AutoCompleteScope
        scope_widget = AutoCompleteScope(mock_gui)
        scope_widget.set_scope_type("authors")
        
        # WHEN: User tries to add invalid/arbitrary text
        result = scope_widget.add_selection("NonExistentAuthor")
        
        # THEN: Should reject invalid input
        assert result is False
        selections = scope_widget.get_selected_items()
        assert "NonExistentAuthor" not in selections
    
    def test_autocomplete_scope_returns_scope_data(self):
        """
        Test that AutoCompleteScope returns proper scope data
        for search engine consumption
        """
        # GIVEN: AutoCompleteScope with selections
        mock_gui = Mock()
        mock_db = Mock()
        mock_gui.current_db.new_api = mock_db
        mock_db.all_field_names.return_value = {
            'authors': ['Aristotle', 'Plato']
        }
        
        from calibre_plugins.semantic_search.ui.widgets import AutoCompleteScope
        scope_widget = AutoCompleteScope(mock_gui)
        scope_widget.set_scope_type("authors")
        scope_widget.add_selection("Aristotle")
        scope_widget.add_selection("Plato")
        
        # WHEN: Get scope data for search
        scope_data = scope_widget.get_scope_data()
        
        # THEN: Should return proper format for search engine
        assert scope_data['scope_type'] == 'authors'
        assert 'Aristotle' in scope_data['selected_items']
        assert 'Plato' in scope_data['selected_items']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])