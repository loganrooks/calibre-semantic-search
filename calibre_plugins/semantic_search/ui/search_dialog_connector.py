"""
Search Dialog Connector - Connects Qt dialog to presenter without Qt dependencies

This module provides the connection logic that can be tested
without importing Qt/Calibre modules.
"""

from typing import Any, Dict


class SearchDialogConnector:
    """Connects search dialog to presenter pattern"""
    
    def __init__(self, gui: Any, plugin: Any, config: Any):
        """
        Initialize connector with GUI dependencies
        
        Args:
            gui: Calibre GUI object
            plugin: Plugin instance  
            config: Configuration object
        """
        self.gui = gui
        self.plugin = plugin
        self.config = config
        self.presenter = None
        self.search_engine = None
        
    def initialize_presenter(self) -> None:
        """Initialize presenter with all dependencies"""
        # Import here to avoid Qt dependencies in tests
        from search_presenter import SearchEngineFactory, SearchDialogPresenter
        from qt_view_adapter import QtViewAdapter  
        from search_business_logic import SearchQueryValidator, SearchCacheManager
        
        # Create search engine factory
        factory = SearchEngineFactory(
            library_path=self.gui.library_path,
            calibre_api=self.gui.current_db.new_api,
            config=self.config.as_dict()
        )
        
        # Create search engine
        self.search_engine = factory.create_search_engine()
        
        # Create view adapter (will be set by dialog)
        self.view_adapter = None
        
        # Create validator and cache
        validator = SearchQueryValidator()
        cache = SearchCacheManager()
        
        # Create presenter
        self.presenter = SearchDialogPresenter(
            view=self.view_adapter,  # Will be set later
            search_engine=self.search_engine,
            validator=validator,
            cache=cache
        )
    
    def set_view_adapter(self, view_adapter: Any) -> None:
        """Set the view adapter after dialog is created"""
        self.view_adapter = view_adapter
        if self.presenter:
            self.presenter.view = view_adapter
    
    def build_search_options(self, ui_state: Dict[str, Any]) -> Any:
        """
        Build search options from UI state
        
        Args:
            ui_state: Dictionary with UI values
            
        Returns:
            SearchOptions object
        """
        # For now, create a mock options object since we can't import the real one
        # This will be replaced when we connect to real implementation
        from unittest.mock import Mock
        
        class MockSearchOptions:
            def __init__(self, mode, scope, limit, similarity_threshold, include_context):
                self.mode = mode
                self.scope = scope
                self.limit = limit
                self.similarity_threshold = similarity_threshold
                self.include_context = include_context
        
        # Map UI indices to string values for now (minimal implementation)
        mode_map = {
            0: "semantic",
            1: "dialectical", 
            2: "genealogical",
            3: "hybrid"
        }
        
        scope_map = {
            0: "library",
            1: "current_book",
            2: "selected_books",
            3: "author",
            4: "tag"
        }
        
        return MockSearchOptions(
            mode=mode_map.get(ui_state.get('mode_index', 0), "semantic"),
            scope=scope_map.get(ui_state.get('scope_index', 0), "library"),
            limit=ui_state.get('limit', 20),
            similarity_threshold=ui_state.get('threshold', 70) / 100,
            include_context=ui_state.get('include_context', True)
        )
    
    def perform_search(self, query: str, ui_state: Dict[str, Any]) -> None:
        """
        Perform search by delegating to presenter
        
        Args:
            query: Search query text
            ui_state: Current UI state
        """
        if not self.presenter:
            raise RuntimeError("Presenter not initialized")
            
        options = self.build_search_options(ui_state)
        self.presenter.perform_search(query, options)