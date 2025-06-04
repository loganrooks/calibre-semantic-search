# UI-Backend Integration Pseudocode
## SPARC Step 2: Pseudocode Design
### Architecture Compliance

Based on spec-03 (Architecture Design Document), this integration follows:
- **Service Layer Pattern**: SearchCoordinator orchestrates between UI and core services
- **Repository Pattern**: Clean data access abstractions
- **MVP Pattern**: Model-View-Presenter for UI testability
- **Plugin-First**: All functionality via Calibre's InterfaceAction

### 1. Search Dialog Integration (MVP Pattern)

```pseudocode
// MODEL: Search state management
CLASS SearchModel:
    FUNCTION __init__():
        self.state = SearchState(empty)
        self.observers = []
    
    FUNCTION update_state(action: Action) -> SearchState:
        new_state = reduce_state(self.state, action)
        self.state = new_state
        notify_observers(new_state)
        RETURN new_state

// PRESENTER: Coordinates between View and Services  
CLASS SearchPresenter:
    FUNCTION __init__(view, search_coordinator):
        self.view = view
        self.search_coordinator = search_coordinator
        self.model = SearchModel()
    
    FUNCTION initialize_search_coordinator():
        // Following Service Layer Architecture (spec-03)
        IF search_coordinator already exists:
            RETURN existing coordinator
        
        library_path = get_calibre_library_path()
        db_path = library_path + "/semantic_search/embeddings.db"
        
        // Create repositories (Repository Pattern)
        embedding_repo = EmbeddingRepository(db_path)
        calibre_repo = CalibreRepository(calibre_db_api)
        
        // Create core services
        config = SemanticSearchConfig()
        embedding_service = create_embedding_service(config.as_dict())
        vector_search_engine = VectorSearchEngine(embedding_repo)
        
        // Create search coordinator (Service Layer)
        search_coordinator = SearchCoordinator(
            embedding_service,
            vector_search_engine,
            embedding_repo,
            calibre_repo
        )
        
        // Start async event loop in background thread
        event_loop_thread = start_background_thread(run_event_loop)
        
        RETURN search_coordinator

    FUNCTION perform_search(query_text, search_options):
        // Update model state
        self.model.update_state(StartSearchAction(query_text, search_options))
        
        // Validate input (following Search Coordinator pattern)
        validation_result = self.search_coordinator.validate_query(query_text)
        IF NOT validation_result.is_valid:
            self.model.update_state(SearchErrorAction(validation_result.error))
            RETURN
        
        // Show progress UI
        self.view.show_progress_indicator()
        self.view.disable_search_button()
        
        // Execute async search via coordinator
        search_future = async_call(
            self.search_coordinator.search,
            query_text,
            search_options
        )
        
        // Schedule result handling
        schedule_callback(self.check_search_complete, search_future, 100ms)

    FUNCTION check_search_complete(search_future):
        IF search_future.is_complete():
            TRY:
                results = search_future.get_result()
                self.model.update_state(SearchCompleteAction(results))
                self.view.hide_progress_indicator()
                self.view.enable_search_button()
            CATCH Exception as e:
                self.model.update_state(SearchErrorAction(str(e)))
                self.view.show_error_message(str(e))
        ELSE:
            // Check again later
            schedule_callback(self.check_search_complete, search_future, 100ms)

// VIEW: UI component (following MVP pattern)
CLASS SearchDialogView:
    FUNCTION __init__(gui, plugin):
        self.gui = gui
        self.plugin = plugin
        self.presenter = SearchPresenter(self, NULL)  // Injected later
        setup_ui()
    
    FUNCTION on_search_button_clicked():
        query = self.query_input.get_text()
        options = self.build_search_options()
        self.presenter.perform_search(query, options)
```

### 2. Search Result Actions (Following Calibre Integration Patterns)

```pseudocode
FUNCTION view_in_book(book_id, chunk_data):
    // Get search result context
    result_card = get_sender_result_card()
    
    IF result_card has chunk_position:
        // Navigate to specific position
        calibre_viewer.view_book_at_position(
            book_id, 
            chunk_data.start_position,
            highlight_text=chunk_data.text[0:100]
        )
    ELSE:
        // Fallback: just open book
        calibre_viewer.view_book(book_id)

FUNCTION find_similar_passages(chunk_id):
    IF search_engine is NULL:
        search_engine = initialize_search_engine()
    
    // Clear current results
    clear_results_display()
    show_status("Finding similar passages...")
    
    // Execute similarity search
    similarity_future = async_find_similar(search_engine, chunk_id, limit=20)
    
    // Handle results
    schedule_callback(check_search_complete, similarity_future, 100ms)
```

### 3. Indexing Integration

```pseudocode
FUNCTION start_indexing_job(book_ids):
    // Create background indexing job
    indexing_job = CREATE IndexingJob:
        FUNCTION run():
            // Initialize all services
            library_path = get_library_path()
            db_path = library_path + "/semantic_search/embeddings.db"
            
            embedding_repo = EmbeddingRepository(db_path)
            calibre_repo = CalibreRepository(calibre_db_api)
            text_processor = TextProcessor()
            embedding_service = create_embedding_service(config)
            
            indexing_service = IndexingService(
                text_processor, embedding_service,
                embedding_repo, calibre_repo
            )
            
            // Run async indexing
            event_loop = create_event_loop()
            result = event_loop.run_until_complete(
                indexing_service.index_books(book_ids)
            )
            event_loop.close()
            
            RETURN result
    
    // Show progress dialog
    progress_dialog = ProgressDialog(
        title="Semantic Search Indexing",
        message="Indexing books...",
        max_value=length(book_ids),
        job=indexing_job
    )
    
    progress_dialog.execute()
```

### 4. Viewer Context Menu Integration

```pseudocode
FUNCTION inject_viewer_menu(viewer):
    viewer_integration = get_or_create_viewer_integration()
    viewer_integration.inject_into_viewer(viewer)

FUNCTION handle_text_selection(viewer, selected_text, menu_position):
    IF selected_text is empty:
        RETURN
    
    context_menu = create_context_menu()
    
    // Add semantic search action
    search_action = create_action("Semantic Search: " + truncate(selected_text, 30))
    search_action.on_triggered = LAMBDA: open_search_dialog_with_text(selected_text)
    context_menu.add_action(search_action)
    
    // Add search in book action  
    search_book_action = create_action("Search in This Book")
    search_book_action.on_triggered = LAMBDA: search_in_current_book(selected_text)
    context_menu.add_action(search_book_action)
    
    // Show menu
    context_menu.show_at_position(menu_position)
```

### 5. Error Handling Patterns

```pseudocode
FUNCTION safe_initialize_search_engine():
    TRY:
        RETURN initialize_search_engine()
    CATCH DatabaseError as e:
        show_error_dialog("Database initialization failed: " + e.message)
        RETURN NULL
    CATCH ConfigurationError as e:
        show_error_dialog("Configuration error: " + e.message) 
        RETURN NULL
    CATCH Exception as e:
        log_error("Unexpected error initializing search engine", e)
        show_error_dialog("Search engine initialization failed")
        RETURN NULL

FUNCTION safe_perform_search(query, options):
    TRY:
        RETURN perform_search(query, options)
    CATCH ValidationError as e:
        show_warning_dialog(e.message)
    CATCH SearchError as e:
        show_error_dialog("Search failed: " + e.message)
    CATCH Exception as e:
        log_error("Unexpected search error", e)
        show_error_dialog("An unexpected error occurred during search")
```

### 6. Resource Management

```pseudocode
FUNCTION cleanup_search_dialog():
    IF event_loop_thread is running:
        request_thread_stop()
        wait_for_thread_completion(timeout=5s)
    
    IF search_engine exists:
        search_engine.cleanup()
    
    clear_cached_resources()
```

## Testing Strategy

Each pseudocode function above will have corresponding unit tests:

1. **Mock Dependencies**: Create mocks for all external dependencies
2. **Test Isolation**: Each test focuses on single function behavior
3. **Error Scenarios**: Test all error conditions and edge cases
4. **Performance**: Verify async operations complete within time limits
5. **UI Integration**: Test UI state changes and user interactions

## Implementation Priority

1. **Phase 1**: Search engine initialization and basic search
2. **Phase 2**: Search result actions (view in book, find similar)
3. **Phase 3**: Indexing job integration
4. **Phase 4**: Viewer context menu integration
5. **Phase 5**: Error handling and resource cleanup