# Calibre Semantic Search Plugin - Architecture Design Document

## Document Information
- **Version**: 1.0
- **Status**: Draft
- **Audience**: Software Architects, Senior Developers, Technical Leads
- **Purpose**: Define the technical architecture for semantic search implementation

## Architecture Overview

### Design Philosophy
The architecture follows these core principles:
1. **Separation of Concerns**: Clear boundaries between components
2. **Plugin-First**: All functionality via Calibre's plugin system
3. **Extensibility**: Every major component is replaceable
4. **Resilience**: Graceful degradation at every level
5. **Performance**: Optimize for sub-100ms search latency

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface Layer                     │
│  ┌──────────────┐  ┌─────────────────┐  ┌──────────────────┐  │
│  │ Context Menu │  │  Search Dialog  │  │ Advanced UIs     │  │
│  │ Integration  │  │  (Qt Widgets)   │  │ (Comparison etc) │  │
│  └──────┬───────┘  └────────┬────────┘  └─────────┬────────┘  │
└─────────┼───────────────────┼─────────────────────┼────────────┘
          │                   │                     │
┌─────────┼───────────────────┼─────────────────────┼────────────┐
│         │          Application Service Layer       │            │
│  ┌──────▼────────┐  ┌───────▼────────┐  ┌────────▼─────────┐  │
│  │ Search        │  │ Index          │  │ Research         │  │
│  │ Coordinator   │  │ Manager        │  │ Analyzer         │  │
│  └──────┬────────┘  └───────┬────────┘  └────────┬─────────┘  │
└─────────┼───────────────────┼─────────────────────┼────────────┘
          │                   │                     │
┌─────────┼───────────────────┼─────────────────────┼────────────┐
│         │           Core Service Layer            │            │
│  ┌──────▼────────┐  ┌───────▼────────┐  ┌────────▼─────────┐  │
│  │ Embedding     │  │ Vector Search  │  │ Text Processing  │  │
│  │ Service       │  │ Engine         │  │ Service          │  │
│  └──────┬────────┘  └───────┬────────┘  └────────┬─────────┘  │
└─────────┼───────────────────┼─────────────────────┼────────────┘
          │                   │                     │
┌─────────┼───────────────────┼─────────────────────┼────────────┐
│         │              Data Access Layer          │            │
│  ┌──────▼────────┐  ┌───────▼────────┐  ┌────────▼─────────┐  │
│  │ Embedding     │  │ Calibre DB     │  │ Cache            │  │
│  │ Repository    │  │ Adapter        │  │ Manager          │  │
│  └──────┬────────┘  └───────┬────────┘  └────────┬─────────┘  │
└─────────┼───────────────────┼─────────────────────┼────────────┘
          │                   │                     │
┌─────────▼───────────────────▼─────────────────────▼────────────┐
│                        Storage Layer                            │
│  ┌──────────────┐  ┌─────────────────┐  ┌──────────────────┐  │
│  │ embeddings.db│  │  metadata.db    │  │ cache/           │  │
│  │ (sqlite-vec) │  │  (read-only)    │  │ (filesystem)     │  │
│  └──────────────┘  └─────────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Architecture

### 1. Plugin Core Component

#### Purpose
Central coordination point for all plugin functionality, managing lifecycle and Calibre integration.

#### Responsibilities
- Plugin initialization and shutdown
- Calibre hook management
- Service container/dependency injection
- Configuration management
- Event bus coordination

#### Interfaces
```python
class ISemanticSearchPlugin:
    def initialize(self) -> None:
        """Initialize all plugin components"""
        
    def shutdown(self) -> None:
        """Clean shutdown of all services"""
        
    def get_service(self, service_type: Type[T]) -> T:
        """Service locator pattern"""
        
    def handle_viewer_opened(self, viewer: Any) -> None:
        """Viewer integration hook"""
        
    def handle_library_changed(self, db: Any) -> None:
        """Library switch hook"""
```

#### Key Design Decisions
- **Service Container**: Use dependency injection for loose coupling
- **Event Bus**: Decouple components via events
- **Lazy Loading**: Initialize components only when needed
- **Configuration**: Centralized config management

### 2. User Interface Layer

#### 2.1 Search Dialog Component

##### Purpose
Primary user interface for semantic search operations.

##### Architecture Pattern
Model-View-Presenter (MVP) pattern for testability.

##### Component Structure
```
SearchDialog/
├── Models/
│   ├── SearchModel          # Search state and logic
│   ├── ResultsModel         # Results data management
│   └── FiltersModel         # Filter state
├── Views/
│   ├── SearchDialogView     # Main window
│   ├── ResultsListView      # Results display
│   └── FilterPanelView      # Filter controls
├── Presenters/
│   ├── SearchPresenter      # Coordinates search
│   └── ResultsPresenter     # Manages results
└── Widgets/
    ├── SimilaritySlider     # Custom threshold control
    ├── ResultCard           # Individual result display
    └── ScopeSelector        # Scope dropdown
```

##### State Management
```python
class SearchState:
    """Immutable search state"""
    query: str
    scope: SearchScope
    filters: SearchFilters
    results: List[SearchResult]
    is_searching: bool
    error: Optional[str]
    
class SearchStateManager:
    """Manages state transitions"""
    def update_state(self, action: Action) -> SearchState:
        """Pure function state updates"""
```

#### 2.2 Context Menu Integration

##### Purpose
Seamless integration with Calibre's viewer context menu.

##### Implementation Strategy
```python
class ViewerContextMenuHandler:
    def inject_menu_items(self, viewer: Any) -> None:
        """Add semantic search options to context menu"""
        
    def handle_selection(self, selected_text: str) -> None:
        """Process selected text for search"""
        
    def show_quick_search(self, text: str) -> None:
        """Show floating quick search window"""
```

##### Menu Structure
```
Right Click on Selected Text
├── Copy
├── Highlight
├── ─────────────
├── Semantic Search
│   ├── Search in This Book
│   ├── Search in Library
│   └── Find Similar Passages
└── ─────────────
```

### 3. Service Layer Architecture

#### 3.1 Search Coordinator Service

##### Purpose
Orchestrates the search process, coordinating between UI and core services.

##### Responsibilities
- Query validation and preprocessing
- Search strategy selection
- Result aggregation and ranking
- Performance monitoring
- Error handling and recovery

##### Interface Design
```python
class ISearchCoordinator:
    async def search(
        self,
        query: str,
        options: SearchOptions
    ) -> SearchResults:
        """Main search entry point"""
        
    async def search_similar(
        self,
        chunk_id: str,
        limit: int = 20
    ) -> List[SimilarChunk]:
        """Find similar chunks"""
        
    def validate_query(self, query: str) -> ValidationResult:
        """Pre-flight query validation"""
        
    def explain_search(self, query: str) -> SearchExplanation:
        """Explain how search will work"""
```

##### Search Pipeline
```
PSEUDOCODE: Search Pipeline

FUNCTION execute_search(query, options):
    // Phase 1: Preparation
    validated_query = validate_and_clean(query)
    embedding = generate_embedding(validated_query)
    
    // Phase 2: Retrieval
    candidates = vector_search(embedding, options.scope)
    
    // Phase 3: Filtering
    filtered = apply_filters(candidates, options.filters)
    
    // Phase 4: Ranking
    ranked = rank_results(filtered, embedding, query)
    
    // Phase 5: Enhancement
    enhanced = add_metadata(ranked)
    
    RETURN enhanced
```

#### 3.2 Index Manager Service

##### Purpose
Manages the indexing lifecycle for books in the library.

##### Responsibilities
- Book text extraction
- Chunking orchestration
- Embedding generation
- Progress tracking
- Incremental updates

##### Architecture
```python
class IndexManager:
    def __init__(
        self,
        text_processor: ITextProcessor,
        embedding_service: IEmbeddingService,
        repository: IEmbeddingRepository
    ):
        self.text_processor = text_processor
        self.embedding_service = embedding_service
        self.repository = repository
        
    async def index_books(
        self,
        book_ids: List[int],
        progress_callback: Callable
    ) -> IndexingResult:
        """Index multiple books with progress"""
```

##### Indexing Pipeline
```
PSEUDOCODE: Indexing Pipeline

FUNCTION index_book(book_id):
    // Extract text from book
    book_text = extract_text(book_id)
    
    // Chunk text intelligently
    chunks = chunk_text(book_text, strategy='hybrid')
    
    // Generate embeddings in batches
    FOR batch IN batch_chunks(chunks, size=100):
        embeddings = generate_embeddings(batch)
        store_embeddings(book_id, batch, embeddings)
        update_progress()
    
    // Update metadata
    mark_book_indexed(book_id)
```

### 4. Core Service Layer

#### 4.1 Embedding Service

##### Purpose
Abstracts embedding generation across multiple providers.

##### Design Pattern
Strategy pattern with fallback chain.

##### Provider Architecture
```python
class IEmbeddingProvider(ABC):
    @abstractmethod
    async def generate_embedding(self, text: str) -> np.ndarray:
        """Generate single embedding"""
        
    @abstractmethod
    async def generate_batch(self, texts: List[str]) -> List[np.ndarray]:
        """Batch generation for efficiency"""
        
    @abstractmethod
    def get_dimensions(self) -> int:
        """Embedding dimensions"""
        
class EmbeddingService:
    def __init__(self, providers: List[IEmbeddingProvider]):
        self.primary = providers[0]
        self.fallbacks = providers[1:]
        
    async def embed_with_fallback(self, text: str) -> np.ndarray:
        """Try primary, then fallbacks"""
        try:
            return await self.primary.generate_embedding(text)
        except ProviderError:
            for fallback in self.fallbacks:
                try:
                    return await fallback.generate_embedding(text)
                except ProviderError:
                    continue
            raise NoProvidersAvailable()
```

##### Provider Implementations
```
Providers/
├── VertexAIProvider      # Google Vertex AI
├── OpenAIProvider        # OpenAI API
├── CohereProvider        # Cohere API
├── OllamaProvider        # Local Ollama
└── MockProvider          # Testing
```

#### 4.2 Vector Search Engine

##### Purpose
Efficient similarity search using vector embeddings.

##### Architecture Decisions
- **Storage**: SQLite with sqlite-vec extension
- **Algorithm**: Approximate nearest neighbors
- **Optimization**: Memory-mapped indices for large datasets

##### Search Algorithm
```
PSEUDOCODE: Vector Search Algorithm

FUNCTION vector_search(query_embedding, scope, limit):
    // Build search query based on scope
    search_space = determine_search_space(scope)
    
    // Use sqlite-vec for similarity search
    results = []
    FOR chunk IN search_space:
        similarity = cosine_similarity(query_embedding, chunk.embedding)
        IF similarity > threshold:
            results.append((chunk, similarity))
    
    // Sort by similarity
    results.sort(by=similarity, descending=True)
    
    RETURN results[:limit]
```

##### Optimization Strategies
```python
class OptimizedVectorSearch:
    def __init__(self):
        self.index_cache = {}  # Memory-mapped indices
        self.query_cache = LRUCache(maxsize=1000)
        
    def search_with_optimization(self, query_vec, options):
        # Check query cache
        cache_key = hash(query_vec.tobytes())
        if cache_key in self.query_cache:
            return self.query_cache[cache_key]
            
        # Use pre-filtering to reduce search space
        candidates = self.pre_filter(options)
        
        # Perform vector search
        results = self.vector_search(query_vec, candidates)
        
        # Cache results
        self.query_cache[cache_key] = results
        return results
```

#### 4.3 Text Processing Service

##### Purpose
Intelligent text extraction and chunking for philosophical texts.

##### Chunking Strategies
```python
class ChunkingStrategy(ABC):
    @abstractmethod
    def chunk(self, text: str, metadata: Dict) -> List[Chunk]:
        """Split text into chunks"""
        
class HybridChunker(ChunkingStrategy):
    """Recommended for philosophical texts"""
    
    def chunk(self, text: str, metadata: Dict) -> List[Chunk]:
        # Respect paragraph boundaries
        paragraphs = self.split_paragraphs(text)
        
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for para in paragraphs:
            para_tokens = self.count_tokens(para)
            
            # Handle various cases
            if para_tokens > MAX_TOKENS:
                # Split large paragraph
                chunks.extend(self.split_large_paragraph(para))
            elif current_tokens + para_tokens > MAX_TOKENS:
                # Start new chunk
                chunks.append(self.create_chunk(current_chunk))
                current_chunk = [para]
                current_tokens = para_tokens
            else:
                # Add to current chunk
                current_chunk.append(para)
                current_tokens += para_tokens
                
        return chunks
```

##### Special Handling for Philosophy
```
PSEUDOCODE: Philosophy-Aware Chunking

FUNCTION chunk_philosophical_text(text):
    // Identify special elements
    quotes = extract_quotes(text)
    arguments = identify_arguments(text)
    citations = extract_citations(text)
    
    // Chunk with awareness
    chunks = []
    FOR section IN text.sections:
        IF section contains argument:
            // Keep argument together
            chunk = preserve_argument_structure(section)
        ELIF section contains long quote:
            // Handle quote specially
            chunk = handle_philosophical_quote(section)
        ELSE:
            // Normal chunking
            chunk = standard_chunk(section)
        
        chunks.append(chunk)
    
    RETURN chunks
```

### 5. Data Access Layer

#### 5.1 Repository Pattern Implementation

##### Purpose
Abstract data access with clean interfaces.

##### Repository Interfaces
```python
class IEmbeddingRepository(ABC):
    @abstractmethod
    async def store_embedding(
        self,
        book_id: int,
        chunk: Chunk,
        embedding: np.ndarray
    ) -> None:
        """Store single embedding"""
        
    @abstractmethod
    async def get_embeddings(
        self,
        book_id: int
    ) -> List[Tuple[Chunk, np.ndarray]]:
        """Retrieve embeddings for book"""
        
    @abstractmethod
    async def search_similar(
        self,
        embedding: np.ndarray,
        limit: int,
        filters: Dict
    ) -> List[SearchResult]:
        """Vector similarity search"""
        
class ICalibreRepository(ABC):
    @abstractmethod
    def get_book_metadata(self, book_id: int) -> BookMetadata:
        """Get book metadata"""
        
    @abstractmethod
    def get_book_text(self, book_id: int) -> str:
        """Extract book text"""
        
    @abstractmethod
    def get_books_by_filter(self, filter: Dict) -> List[int]:
        """Get book IDs matching filter"""
```

##### Repository Implementations
```python
class SqliteEmbeddingRepository(IEmbeddingRepository):
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_database()
        
    def _init_database(self):
        """Initialize sqlite-vec database"""
        conn = sqlite3.connect(self.db_path)
        conn.enable_load_extension(True)
        conn.load_extension("sqlite-vec")
        
        # Create schema
        conn.executescript("""
            CREATE VIRTUAL TABLE IF NOT EXISTS vec_embeddings
            USING vec0(embedding float[{dims}]);
            
            CREATE TABLE IF NOT EXISTS chunks (
                chunk_id INTEGER PRIMARY KEY,
                book_id INTEGER,
                chunk_text TEXT,
                chunk_index INTEGER,
                metadata JSON,
                FOREIGN KEY(chunk_id) REFERENCES vec_embeddings(rowid)
            );
        """)
```

#### 5.2 Cache Architecture

##### Purpose
Multi-level caching for performance optimization.

##### Cache Hierarchy
```
┌─────────────────────────┐
│   Query Cache (L1)      │  TTL: 1 hour
│   Size: 1000 queries    │  Hit rate: ~40%
├─────────────────────────┤
│   Embedding Cache (L2)  │  TTL: 24 hours  
│   Size: 10000 chunks    │  Hit rate: ~60%
├─────────────────────────┤
│   Metadata Cache (L3)   │  TTL: Until change
│   Size: All books       │  Hit rate: ~95%
└─────────────────────────┘
```

##### Cache Implementation
```python
class CacheManager:
    def __init__(self):
        self.query_cache = TTLCache(maxsize=1000, ttl=3600)
        self.embedding_cache = LRUCache(maxsize=10000)
        self.metadata_cache = {}
        
    def get_with_cache(self, key: str, loader: Callable):
        """Generic cache-aside pattern"""
        # Check L1
        if key in self.query_cache:
            return self.query_cache[key]
            
        # Load and cache
        value = loader()
        self.query_cache[key] = value
        return value
```

### 6. Cross-Cutting Concerns

#### 6.1 Error Handling Architecture

##### Error Hierarchy
```python
class SemanticSearchError(Exception):
    """Base exception"""
    
class EmbeddingError(SemanticSearchError):
    """Embedding generation failed"""
    
class SearchError(SemanticSearchError):
    """Search operation failed"""
    
class IndexingError(SemanticSearchError):
    """Indexing operation failed"""
    
class ConfigurationError(SemanticSearchError):
    """Configuration invalid"""
```

##### Error Handling Strategy
```
PSEUDOCODE: Resilient Error Handling

FUNCTION handle_with_resilience(operation):
    retries = 0
    backoff = 1
    
    WHILE retries < MAX_RETRIES:
        TRY:
            result = operation()
            RETURN result
            
        CATCH TemporaryError as e:
            // Exponential backoff
            WAIT(backoff * SECONDS)
            backoff *= 2
            retries += 1
            
        CATCH PermanentError as e:
            // Try fallback
            IF fallback_available():
                RETURN fallback_operation()
            ELSE:
                RAISE UserFriendlyError(e)
                
    RAISE MaxRetriesExceeded()
```

#### 6.2 Performance Monitoring

##### Metrics Collection
```python
class PerformanceMonitor:
    def __init__(self):
        self.metrics = defaultdict(list)
        
    def record_operation(self, operation: str, duration: float):
        """Record operation timing"""
        self.metrics[operation].append(duration)
        
    def get_statistics(self, operation: str) -> Dict:
        """Get performance statistics"""
        durations = self.metrics[operation]
        return {
            'count': len(durations),
            'mean': statistics.mean(durations),
            'p50': statistics.median(durations),
            'p95': np.percentile(durations, 95),
            'p99': np.percentile(durations, 99)
        }
```

##### Performance Targets
| Operation | Target | Maximum |
|-----------|--------|---------|
| Search query | 50ms | 100ms |
| Result navigation | 200ms | 500ms |
| Chunk indexing | 10ms | 50ms |
| UI update | 16ms | 33ms |

#### 6.3 Security Architecture

##### API Key Management
```python
class SecureConfigManager:
    def __init__(self):
        self.keyring = self._init_keyring()
        
    def store_api_key(self, provider: str, key: str):
        """Securely store API key"""
        encrypted = self.encrypt(key)
        self.keyring.set_password(
            "calibre-semantic-search",
            provider,
            encrypted
        )
        
    def get_api_key(self, provider: str) -> str:
        """Retrieve and decrypt API key"""
        encrypted = self.keyring.get_password(
            "calibre-semantic-search",
            provider
        )
        return self.decrypt(encrypted) if encrypted else None
```

### 7. Deployment Architecture

#### 7.1 Plugin Package Structure
```
calibre-semantic-search.zip
├── __init__.py              # Plugin metadata
├── plugin-import-name.txt   # Import name
├── images/                  # Icons and images
│   ├── icon.png
│   └── search.png
├── translations/            # I18n files
│   ├── messages.pot
│   └── de/
│       └── messages.mo
├── lib/                     # Dependencies
│   ├── sqlite_vec.so       # Platform specific
│   └── numpy/              # If needed
└── src/                    # Source code
    ├── ui/
    ├── services/
    ├── repositories/
    └── config/
```

#### 7.2 Configuration Architecture
```python
class Configuration:
    """Layered configuration system"""
    
    defaults = {
        'embedding_provider': 'vertex_ai',
        'embedding_dimensions': 768,
        'chunk_size': 512,
        'chunk_overlap': 50,
        'search_limit': 20,
        'cache_enabled': True
    }
    
    def __init__(self):
        self.user_config = JSONConfig('plugins/semantic_search')
        self.runtime_config = {}
        
    def get(self, key: str, default=None):
        """Layered lookup: runtime > user > defaults"""
        return (
            self.runtime_config.get(key) or
            self.user_config.get(key) or
            self.defaults.get(key) or
            default
        )
```

### 8. Testing Architecture

#### 8.1 Test Strategy
```
Tests/
├── Unit/                    # Component tests
│   ├── test_embedding_service.py
│   ├── test_search_engine.py
│   └── test_chunking.py
├── Integration/             # Integration tests
│   ├── test_search_pipeline.py
│   ├── test_indexing_pipeline.py
│   └── test_ui_integration.py
├── Performance/             # Performance tests
│   ├── test_search_latency.py
│   ├── test_memory_usage.py
│   └── test_scalability.py
└── Philosophical/           # Domain-specific tests
    ├── test_concept_search.py
    ├── test_dialectical_search.py
    └── test_genealogy.py
```

#### 8.2 Test Fixtures
```python
class PhilosophicalTestFixtures:
    @fixture
    def heidegger_texts(self):
        """Sample Heidegger texts for testing"""
        return [
            {
                'text': 'Dasein is an entity which...',
                'expected_concepts': ['Being', 'existence', 'temporality']
            }
        ]
        
    @fixture
    def dialectical_pairs(self):
        """Known dialectical relationships"""
        return [
            ('Being', 'Nothing'),
            ('Master', 'Slave'),
            ('Presence', 'Absence')
        ]
```

### 9. Future Architecture Considerations

#### 9.1 Scalability Path
```
Current (MVP): Single SQLite database
├── 10K books: Acceptable performance
├── 50K books: Needs optimization
└── 100K+ books: Requires sharding

Future Architecture:
├── Sharded SQLite databases
├── Optional PostgreSQL + pgvector
├── Distributed search (optional)
└── GPU acceleration (optional)
```

#### 9.2 Extension Points
1. **Custom Embedding Providers**: Plugin system for providers
2. **Search Algorithms**: Pluggable search strategies
3. **UI Components**: Additional research tools
4. **Export Formats**: New citation formats
5. **Analysis Methods**: Philosophical methodologies

### 10. Architecture Decision Records (ADRs)

#### ADR-001: Use Plugin Architecture
- **Status**: Accepted
- **Context**: Need to integrate with Calibre
- **Decision**: Implement as plugin, not fork
- **Consequences**: Limited viewer integration, easier maintenance

#### ADR-002: SQLite with sqlite-vec
- **Status**: Accepted
- **Context**: Need vector search capability
- **Decision**: Use sqlite-vec extension
- **Consequences**: Good performance <1M vectors, single file storage

#### ADR-003: Multi-Provider Embedding
- **Status**: Accepted
- **Context**: API reliability concerns
- **Decision**: Support multiple providers with fallback
- **Consequences**: Complex configuration, better reliability

This architecture provides a solid foundation for implementing semantic search while maintaining flexibility for future enhancements and philosophical research requirements.