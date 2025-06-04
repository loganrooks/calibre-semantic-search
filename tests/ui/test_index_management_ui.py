"""
TDD Tests for Index Management UI Components

These tests define the behavior for UI components that manage multiple indexes:
- Index detection and display
- Index management dialog
- Search dialog index selection
- Auto-generation prompts
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any


class TestIndexDetectorUI:
    """Test index detection and status display"""
    
    def test_get_index_status_for_multiple_books(self):
        """Test getting index status for a list of books"""
        from calibre_plugins.semantic_search.ui.index_detector import IndexDetector
        
        detector = IndexDetector()
        book_ids = [1, 2, 3, 4, 5]
        
        # Mock repository returns
        with patch.object(detector, '_get_repository') as mock_repo:
            mock_repo.return_value.get_indexes_for_book.side_effect = [
                [{'index_id': 1, 'provider': 'openai'}],  # Book 1: 1 index
                [],                                       # Book 2: 0 indexes
                [                                         # Book 3: 2 indexes
                    {'index_id': 2, 'provider': 'vertex'},
                    {'index_id': 3, 'provider': 'cohere'}
                ],
                [],                                       # Book 4: 0 indexes
                [{'index_id': 4, 'provider': 'openai'}], # Book 5: 1 index
            ]
            
            status = detector.get_index_status(book_ids)
        
        assert len(status) == 5
        assert status[1]['has_index'] is True
        assert status[1]['index_count'] == 1
        assert status[1]['providers'] == ['openai']
        
        assert status[2]['has_index'] is False
        assert status[2]['index_count'] == 0
        assert status[2]['providers'] == []
        
        assert status[3]['has_index'] is True
        assert status[3]['index_count'] == 2
        assert set(status[3]['providers']) == {'vertex', 'cohere'}
    
    def test_index_status_formatting_for_display(self):
        """Test formatting index status for UI display"""
        from calibre_plugins.semantic_search.ui.index_detector import IndexDetector
        
        detector = IndexDetector()
        
        # Test various status scenarios
        test_cases = [
            # No indexes
            {
                'input': {'has_index': False, 'index_count': 0, 'providers': []},
                'expected': 'No indexes'
            },
            # Single index
            {
                'input': {'has_index': True, 'index_count': 1, 'providers': ['openai']},
                'expected': '1 index (OpenAI)'
            },
            # Multiple indexes
            {
                'input': {'has_index': True, 'index_count': 3, 'providers': ['openai', 'vertex', 'cohere']},
                'expected': '3 indexes (OpenAI, Vertex, Cohere)'
            },
        ]
        
        for case in test_cases:
            formatted = detector.format_status_for_display(case['input'])
            assert formatted == case['expected']
    
    def test_index_status_icons(self):
        """Test appropriate icons are returned for different status"""
        from calibre_plugins.semantic_search.ui.index_detector import IndexDetector
        
        detector = IndexDetector()
        
        # No indexes - should show warning icon
        no_index_icon = detector.get_status_icon({'has_index': False})
        assert 'warning' in no_index_icon.lower() or 'no' in no_index_icon.lower()
        
        # Has indexes - should show check/success icon
        has_index_icon = detector.get_status_icon({'has_index': True, 'index_count': 1})
        assert 'check' in has_index_icon.lower() or 'yes' in has_index_icon.lower()
        
        # Multiple indexes - should show special icon
        multi_index_icon = detector.get_status_icon({'has_index': True, 'index_count': 3})
        assert 'multi' in multi_index_icon.lower() or 'check' in multi_index_icon.lower()


class TestIndexManagerDialog:
    """Test index management dialog functionality"""
    
    def test_load_indexes_for_book(self):
        """Test loading and displaying indexes for a specific book"""
        from calibre_plugins.semantic_search.ui.index_manager_dialog import IndexManagerDialog
        
        # Mock dialog creation (since we can't create real Qt widgets in tests)
        with patch('calibre_plugins.semantic_search.ui.index_manager_dialog.QDialog'):
            dialog = IndexManagerDialog()
            
            # Mock indexes data
            mock_indexes = [
                {
                    'index_id': 1,
                    'provider': 'openai',
                    'model_name': 'text-embedding-3-small',
                    'dimensions': 1536,
                    'total_chunks': 150,
                    'created_at': '2024-01-01T12:00:00Z',
                    'storage_size': '12.5MB'
                },
                {
                    'index_id': 2,
                    'provider': 'vertex',
                    'model_name': 'textembedding-gecko',
                    'dimensions': 768,
                    'total_chunks': 200,
                    'created_at': '2024-01-02T14:30:00Z',
                    'storage_size': '8.3MB'
                }
            ]
            
            # Mock repository
            with patch.object(dialog, '_get_repository') as mock_repo:
                mock_repo.return_value.get_indexes_for_book.return_value = mock_indexes
                
                dialog.load_indexes_for_book(book_id=1)
            
            # Verify indexes were loaded
            assert dialog.get_loaded_indexes() == mock_indexes
            assert len(dialog.get_loaded_indexes()) == 2
    
    def test_select_indexes_for_deletion(self):
        """Test selecting multiple indexes for deletion"""
        from calibre_plugins.semantic_search.ui.index_manager_dialog import IndexManagerDialog
        
        with patch('calibre_plugins.semantic_search.ui.index_manager_dialog.QDialog'):
            dialog = IndexManagerDialog()
            
            # Load some indexes first
            mock_indexes = [
                {'index_id': 1, 'provider': 'openai'},
                {'index_id': 2, 'provider': 'vertex'},
                {'index_id': 3, 'provider': 'cohere'}
            ]
            
            dialog._loaded_indexes = mock_indexes
            
            # Select indexes 0 and 2 (first and third)
            dialog.select_index(0)
            dialog.select_index(2)
            
            selected = dialog.get_selected_indexes()
            
            assert len(selected) == 2
            assert selected[0]['index_id'] == 1
            assert selected[1]['index_id'] == 3
    
    def test_delete_selected_indexes(self):
        """Test deleting selected indexes"""
        from calibre_plugins.semantic_search.ui.index_manager_dialog import IndexManagerDialog
        
        with patch('calibre_plugins.semantic_search.ui.index_manager_dialog.QDialog'):
            dialog = IndexManagerDialog()
            
            # Mock selected indexes
            selected_indexes = [
                {'index_id': 1, 'provider': 'openai'},
                {'index_id': 3, 'provider': 'cohere'}
            ]
            
            with patch.object(dialog, 'get_selected_indexes', return_value=selected_indexes):
                with patch.object(dialog, '_get_repository') as mock_repo:
                    with patch.object(dialog, '_confirm_deletion', return_value=True):
                        dialog.delete_selected_indexes()
                    
                    # Verify repository delete_index was called for each selected index
                    mock_repo.return_value.delete_index.assert_any_call(1)
                    mock_repo.return_value.delete_index.assert_any_call(3)
                    assert mock_repo.return_value.delete_index.call_count == 2
    
    def test_index_details_display(self):
        """Test displaying detailed information about an index"""
        from calibre_plugins.semantic_search.ui.index_manager_dialog import IndexManagerDialog
        
        with patch('calibre_plugins.semantic_search.ui.index_manager_dialog.QDialog'):
            dialog = IndexManagerDialog()
            
            index_data = {
                'index_id': 1,
                'provider': 'openai',
                'model_name': 'text-embedding-3-small',
                'dimensions': 1536,
                'total_chunks': 150,
                'created_at': '2024-01-01T12:00:00Z',
                'storage_size': '12.5MB',
                'chunk_size': 1000,
                'chunk_overlap': 200
            }
            
            details = dialog.format_index_details(index_data)
            
            # Check that all important details are included
            assert 'OpenAI' in details
            assert 'text-embedding-3-small' in details
            assert '1536' in details
            assert '150' in details
            assert '12.5MB' in details


class TestSearchDialogIndexSelector:
    """Test index selection in search dialog"""
    
    def test_populate_index_selector(self):
        """Test populating index selector with available indexes"""
        from calibre_plugins.semantic_search.ui.search_dialog import SearchDialog
        
        with patch('calibre_plugins.semantic_search.ui.search_dialog.QDialog'):
            dialog = SearchDialog()
            
            available_indexes = [
                {
                    'index_id': 1,
                    'provider': 'openai',
                    'model_name': 'text-embedding-3-small',
                    'book_count': 10
                },
                {
                    'index_id': 2,
                    'provider': 'vertex',
                    'model_name': 'textembedding-gecko',
                    'book_count': 8
                },
                {
                    'index_id': 3,
                    'provider': 'cohere',
                    'model_name': 'embed-english-v3.0',
                    'book_count': 5
                }
            ]
            
            dialog.populate_index_selector(available_indexes)
            
            # Verify all indexes are available for selection
            selector_items = dialog.get_index_selector_items()
            assert len(selector_items) == 3
            
            # Check that display names are properly formatted
            display_names = [item['display_name'] for item in selector_items]
            assert 'OpenAI (text-embedding-3-small) - 10 books' in display_names
            assert 'Vertex (textembedding-gecko) - 8 books' in display_names
            assert 'Cohere (embed-english-v3.0) - 5 books' in display_names
    
    def test_auto_select_compatible_index(self):
        """Test auto-selecting index compatible with current provider"""
        from calibre_plugins.semantic_search.ui.search_dialog import SearchDialog
        
        with patch('calibre_plugins.semantic_search.ui.search_dialog.QDialog'):
            dialog = SearchDialog()
            
            # Current embedding provider is OpenAI
            dialog.set_current_embedding_provider('openai')
            
            available_indexes = [
                {'index_id': 1, 'provider': 'vertex', 'model_name': 'textembedding-gecko'},
                {'index_id': 2, 'provider': 'openai', 'model_name': 'text-embedding-3-small'},
                {'index_id': 3, 'provider': 'cohere', 'model_name': 'embed-english-v3.0'}
            ]
            
            dialog.populate_index_selector(available_indexes)
            dialog.auto_select_compatible_index()
            
            # Should auto-select the OpenAI index
            selected = dialog.get_selected_index()
            assert selected['index_id'] == 2
            assert selected['provider'] == 'openai'
    
    def test_warn_no_compatible_index(self):
        """Test warning when no compatible index exists"""
        from calibre_plugins.semantic_search.ui.search_dialog import SearchDialog
        
        with patch('calibre_plugins.semantic_search.ui.search_dialog.QDialog'):
            dialog = SearchDialog()
            
            # Current provider is OpenAI
            dialog.set_current_embedding_provider('openai')
            
            # But only non-OpenAI indexes available
            available_indexes = [
                {'index_id': 1, 'provider': 'vertex', 'model_name': 'textembedding-gecko'},
                {'index_id': 3, 'provider': 'cohere', 'model_name': 'embed-english-v3.0'}
            ]
            
            dialog.populate_index_selector(available_indexes)
            
            # Should show warning about incompatible indexes
            with patch.object(dialog, 'show_warning') as mock_warning:
                compatible_found = dialog.auto_select_compatible_index()
                
                assert compatible_found is False
                mock_warning.assert_called_once()
                assert 'incompatible' in mock_warning.call_args[0][0].lower()
    
    def test_get_selected_index_for_search(self):
        """Test getting the selected index for performing search"""
        from calibre_plugins.semantic_search.ui.search_dialog import SearchDialog
        
        with patch('calibre_plugins.semantic_search.ui.search_dialog.QDialog'):
            dialog = SearchDialog()
            
            # Select an index
            test_index = {
                'index_id': 2,
                'provider': 'vertex',
                'model_name': 'textembedding-gecko',
                'dimensions': 768
            }
            
            dialog.set_selected_index(test_index)
            
            # Get selected index for search
            selected = dialog.get_selected_index_for_search()
            
            assert selected is not None
            assert selected['index_id'] == 2
            assert selected['provider'] == 'vertex'
            assert selected['dimensions'] == 768


class TestAutoIndexGenerationDialog:
    """Test auto-generation of missing indexes"""
    
    def test_show_missing_index_prompt(self):
        """Test showing prompt when compatible index is missing"""
        from calibre_plugins.semantic_search.ui.auto_index_dialog import AutoIndexDialog
        
        with patch('calibre_plugins.semantic_search.ui.auto_index_dialog.QDialog'):
            dialog = AutoIndexDialog()
            
            missing_config = {
                'provider': 'openai',
                'model_name': 'text-embedding-3-small',
                'dimensions': 1536,
                'books_without_index': [1, 2, 3, 4, 5],
                'estimated_time': '5-10 minutes',
                'estimated_storage': '25MB'
            }
            
            # Show the prompt
            dialog.show_missing_index_prompt(missing_config)
            
            # Verify prompt was configured correctly
            prompt_text = dialog.get_prompt_text()
            assert 'OpenAI' in prompt_text
            assert 'text-embedding-3-small' in prompt_text
            assert '5 books' in prompt_text
            assert '5-10 minutes' in prompt_text
            assert '25MB' in prompt_text
    
    def test_user_accepts_index_generation(self):
        """Test when user accepts to generate missing index"""
        from calibre_plugins.semantic_search.ui.auto_index_dialog import AutoIndexDialog
        
        with patch('calibre_plugins.semantic_search.ui.auto_index_dialog.QDialog'):
            dialog = AutoIndexDialog()
            
            # User clicks "Generate Index"
            dialog.set_user_choice('generate')
            
            assert dialog.should_generate_index() is True
            
            # Should provide list of books to index
            books_to_index = dialog.get_books_to_index()
            assert isinstance(books_to_index, list)
    
    def test_user_rejects_index_generation(self):
        """Test when user rejects index generation"""
        from calibre_plugins.semantic_search.ui.auto_index_dialog import AutoIndexDialog
        
        with patch('calibre_plugins.semantic_search.ui.auto_index_dialog.QDialog'):
            dialog = AutoIndexDialog()
            
            # User clicks "Search Anyway" or "Cancel"
            dialog.set_user_choice('cancel')
            
            assert dialog.should_generate_index() is False
    
    def test_selective_book_indexing(self):
        """Test selecting subset of books for indexing"""
        from calibre_plugins.semantic_search.ui.auto_index_dialog import AutoIndexDialog
        
        with patch('calibre_plugins.semantic_search.ui.auto_index_dialog.QDialog'):
            dialog = AutoIndexDialog()
            
            # Show books that could be indexed
            available_books = [
                {'book_id': 1, 'title': 'Philosophy of Mind'},
                {'book_id': 2, 'title': 'Consciousness Studies'},
                {'book_id': 3, 'title': 'Qualia Theory'},
                {'book_id': 4, 'title': 'Intentionality'},
                {'book_id': 5, 'title': 'Free Will'}
            ]
            
            dialog.set_available_books(available_books)
            
            # User selects only books 1, 3, and 5
            dialog.select_books([1, 3, 5])
            
            selected_books = dialog.get_selected_books()
            assert set(selected_books) == {1, 3, 5}
    
    def test_index_generation_progress_tracking(self):
        """Test tracking progress of index generation"""
        from calibre_plugins.semantic_search.ui.auto_index_dialog import AutoIndexDialog
        
        with patch('calibre_plugins.semantic_search.ui.auto_index_dialog.QDialog'):
            dialog = AutoIndexDialog()
            
            # Start index generation
            dialog.start_index_generation([1, 2, 3])
            
            # Simulate progress updates
            dialog.update_progress(book_id=1, progress=0.5, status='Processing chunks')
            dialog.update_progress(book_id=1, progress=1.0, status='Completed')
            
            # Check progress tracking
            progress = dialog.get_generation_progress()
            assert progress['total_books'] == 3
            assert progress['completed_books'] == 1
            assert progress['current_book'] == 2  # Should move to next book
            
            # Test completion
            dialog.update_progress(book_id=2, progress=1.0, status='Completed')
            dialog.update_progress(book_id=3, progress=1.0, status='Completed')
            
            assert dialog.is_generation_complete() is True


class TestIndexStatusIndicators:
    """Test visual indicators for index status"""
    
    def test_book_list_index_indicators(self):
        """Test index status indicators in book list"""
        from calibre_plugins.semantic_search.ui.book_list_indicators import IndexStatusIndicator
        
        indicator = IndexStatusIndicator()
        
        # Test different status scenarios
        test_cases = [
            {
                'status': {'has_index': False, 'index_count': 0},
                'expected_icon': 'no_index',
                'expected_tooltip': 'No indexes available'
            },
            {
                'status': {'has_index': True, 'index_count': 1, 'providers': ['openai']},
                'expected_icon': 'single_index',
                'expected_tooltip': '1 index (OpenAI)'
            },
            {
                'status': {'has_index': True, 'index_count': 3, 'providers': ['openai', 'vertex', 'cohere']},
                'expected_icon': 'multiple_indexes',
                'expected_tooltip': '3 indexes (OpenAI, Vertex, Cohere)'
            }
        ]
        
        for case in test_cases:
            icon = indicator.get_icon_for_status(case['status'])
            tooltip = indicator.get_tooltip_for_status(case['status'])
            
            assert case['expected_icon'] in icon
            assert case['expected_tooltip'] == tooltip
    
    def test_search_dialog_index_warnings(self):
        """Test warnings in search dialog about index compatibility"""
        from calibre_plugins.semantic_search.ui.search_dialog import SearchDialog
        
        with patch('calibre_plugins.semantic_search.ui.search_dialog.QDialog'):
            dialog = SearchDialog()
            
            # Test incompatible index warning
            selected_index = {'provider': 'vertex', 'dimensions': 768}
            current_provider = 'openai'
            
            warning = dialog.get_compatibility_warning(selected_index, current_provider)
            
            assert warning is not None
            assert 'incompatible' in warning.lower()
            assert 'vertex' in warning.lower()
            assert 'openai' in warning.lower()
            
            # Test compatible index (no warning)
            compatible_index = {'provider': 'openai', 'dimensions': 1536}
            warning = dialog.get_compatibility_warning(compatible_index, current_provider)
            
            assert warning is None