# TDD Implementation Plan: Multiple Indexes Per Book

## Overview

This document outlines the Test-Driven Development approach for implementing multiple indexes per book in the Calibre Semantic Search plugin. Each book can have multiple indexes with different embedding providers, models, dimensions, and chunking parameters.

## Requirements Analysis

### 1. Multiple Indexes Per Book
- **Need**: Support different embedding providers (OpenAI, Vertex, Cohere, Local)
- **Need**: Support different model versions (e.g., text-embedding-3-small vs text-embedding-3-large)
- **Need**: Support different vector dimensions (768, 1024, 1536, etc.)
- **Need**: Support different chunking strategies (size, overlap)
- **Use Case**: User upgrades from old model to new model but wants to keep old index
- **Use Case**: User wants to compare search quality between different providers

### 2. UI Index Detection
- **Need**: Show index status in book list (has index, which providers)
- **Need**: Visual indicators for indexed vs non-indexed books
- **Need**: Show index count and details on hover/click
- **Use Case**: User selects books and wants to know which need indexing

### 3. Index Management
- **Need**: View all indexes for a book
- **Need**: Delete specific indexes
- **Need**: View index metadata (created date, chunk count, storage size)
- **Need**: Bulk operations (delete all indexes for provider X)
- **Use Case**: User wants to clean up old indexes to save space

### 4. Search Index Selection
- **Need**: Choose which index to use for search
- **Need**: Auto-select compatible index based on current embedding provider
- **Need**: Show warning if no compatible index exists
- **Use Case**: User changes embedding provider and needs to search with matching index

### 5. Auto-Generate Missing Indexes
- **Need**: Detect books without compatible index before search
- **Need**: Prompt to generate missing indexes
- **Need**: Background indexing with progress tracking
- **Use Case**: User searches and some books don't have indexes for current provider

## Database Schema Design

### New Tables

```sql
-- Main indexes table
CREATE TABLE indexes (
    index_id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL,
    provider TEXT NOT NULL,      -- 'openai', 'vertex', 'cohere', 'local'
    model_name TEXT NOT NULL,    -- 'text-embedding-3-small', etc.
    dimensions INTEGER NOT NULL,  -- 768, 1024, 1536, etc.
    chunk_size INTEGER NOT NULL,
    chunk_overlap INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_chunks INTEGER DEFAULT 0,
    metadata TEXT,               -- JSON for extra settings
    FOREIGN KEY (book_id) REFERENCES books(book_id) ON DELETE CASCADE,
    UNIQUE(book_id, provider, model_name, dimensions, chunk_size, chunk_overlap)
);

-- Index for quick lookups
CREATE INDEX idx_indexes_book ON indexes(book_id);
CREATE INDEX idx_indexes_provider ON indexes(provider);
```

### Modified Tables

```sql
-- Modify chunks table to reference index
ALTER TABLE chunks ADD COLUMN index_id INTEGER;
ALTER TABLE chunks ADD FOREIGN KEY (index_id) REFERENCES indexes(index_id) ON DELETE CASCADE;

-- Modify embeddings tables
ALTER TABLE embeddings ADD COLUMN index_id INTEGER;
ALTER TABLE embeddings ADD FOREIGN KEY (index_id) REFERENCES indexes(index_id) ON DELETE CASCADE;

-- For vec_embeddings virtual table, we'll need to recreate it
-- or use a junction table since virtual tables don't support ALTER
CREATE TABLE vec_embeddings_index (
    chunk_id INTEGER PRIMARY KEY,
    index_id INTEGER NOT NULL,
    FOREIGN KEY (chunk_id) REFERENCES chunks(chunk_id) ON DELETE CASCADE,
    FOREIGN KEY (index_id) REFERENCES indexes(index_id) ON DELETE CASCADE
);
```

## Migration Strategy

### Phase 1: Schema Migration
1. Create new tables
2. Add new columns to existing tables
3. Create migration script to populate index_id for existing data

### Phase 2: Data Migration
```python
def migrate_existing_embeddings(db):
    """Migrate existing embeddings to new multi-index schema"""
    
    # 1. Create default index for existing embeddings
    # Assume existing embeddings are OpenAI text-embedding-ada-002
    default_index_config = {
        'provider': 'openai',
        'model_name': 'text-embedding-ada-002',
        'dimensions': 1536,
        'chunk_size': 1000,  # Default from config
        'chunk_overlap': 200  # Default from config
    }
    
    # 2. Get all books with embeddings
    books_with_embeddings = db.execute("""
        SELECT DISTINCT book_id FROM chunks
    """).fetchall()
    
    # 3. Create indexes for each book
    for book_id in books_with_embeddings:
        index_id = create_index(book_id, **default_index_config)
        
        # 4. Update chunks to reference the index
        db.execute("""
            UPDATE chunks SET index_id = ? WHERE book_id = ?
        """, (index_id, book_id))
        
        # 5. Update embeddings references
        # ... similar updates for embeddings table
```

## TDD Test Categories

### 1. Schema Tests (✓ Written)
- Test new tables exist
- Test columns and constraints
- Test foreign key relationships
- Test unique constraints

### 2. Repository Tests (✓ Written)
- Test CRUD operations for indexes
- Test embedding storage with index reference
- Test search within specific index
- Test cross-index operations

### 3. UI Component Tests (✓ Written)
- Test index detection in book list
- Test index manager dialog
- Test search dialog index selector
- Test auto-generation prompts

### 4. Migration Tests (✓ Written)
- Test data integrity during migration
- Test rollback capability
- Test performance with large datasets

### 5. Integration Tests (To Write)
- Test complete workflow scenarios
- Test compatibility checks
- Test error handling

## Implementation Order (Following TDD)

### Step 1: Database Layer (2 days)
1. ❌ Run schema tests → See them fail
2. ❌ Implement schema changes
3. ❌ Run tests → Make them pass
4. ❌ Implement migration logic
5. ❌ Run migration tests → Make them pass

### Step 2: Repository Layer (2 days)
1. ❌ Run repository tests → See them fail
2. ❌ Implement repository methods
3. ❌ Run tests → Make them pass
4. ❌ Refactor for performance

### Step 3: UI Components (3 days)
1. ❌ Run UI tests → See them fail
2. ❌ Implement index detector
3. ❌ Implement index manager dialog
4. ❌ Implement search dialog changes
5. ❌ Run tests → Make them pass

### Step 4: Integration (2 days)
1. ❌ Write integration tests
2. ❌ Run tests → See them fail
3. ❌ Fix integration issues
4. ❌ Run all tests → Ensure everything passes

### Step 5: User Testing (1 day)
1. ❌ Manual testing in Calibre
2. ❌ Performance testing
3. ❌ Edge case testing
4. ❌ Documentation updates

## API Design

### Repository Methods

```python
class EmbeddingRepository:
    # Index management
    def create_index(self, book_id: int, provider: str, model_name: str, 
                    dimensions: int, chunk_size: int, chunk_overlap: int) -> int:
        """Create a new index for a book"""
        
    def get_indexes_for_book(self, book_id: int) -> List[Dict[str, Any]]:
        """Get all indexes for a specific book"""
        
    def get_indexes_by_provider(self, provider: str) -> List[Dict[str, Any]]:
        """Get all indexes for a specific provider"""
        
    def delete_index(self, index_id: int):
        """Delete a specific index and all its data"""
        
    def get_books_with_indexes(self) -> List[int]:
        """Get list of book IDs that have at least one index"""
        
    # Embedding operations
    def store_embedding_for_index(self, index_id: int, chunk: Chunk, 
                                 embedding: List[float]) -> int:
        """Store embedding for specific index"""
        
    def search_similar_in_index(self, index_id: int, embedding: List[float], 
                               limit: int) -> List[Dict[str, Any]]:
        """Search within a specific index"""
        
    def search_across_indexes(self, index_ids: List[int], embedding: List[float], 
                            limit: int) -> List[Dict[str, Any]]:
        """Search across multiple compatible indexes"""
```

### UI Components

```python
class IndexDetector:
    """Detects and displays index status for books"""
    def get_index_status(self, book_ids: List[int]) -> Dict[int, Dict[str, Any]]:
        """Get index status for multiple books"""

class IndexManagerDialog(QDialog):
    """Dialog for managing indexes for a book"""
    def load_indexes_for_book(self, book_id: int):
        """Load and display all indexes for a book"""
    
    def delete_selected_indexes(self):
        """Delete user-selected indexes"""

class IndexSelector(QWidget):
    """Widget for selecting which index to use in search"""
    def populate_indexes(self, indexes: List[Dict[str, Any]]):
        """Populate selector with available indexes"""
    
    def get_selected_index(self) -> Optional[Dict[str, Any]]:
        """Get currently selected index"""
```

## Error Handling

### Validation Errors
- Invalid index configuration (mismatched provider/dimensions)
- Incompatible search query (wrong dimensions for index)
- Missing required index

### Migration Errors
- Corrupted data during migration
- Insufficient disk space
- Foreign key constraint violations

### User Errors
- Attempting to search without compatible index
- Deleting last index for a book
- Creating duplicate indexes

## Performance Considerations

### Index Storage
- Each index adds ~35MB per 1000 chunks (768-dim)
- Need UI to show storage usage per index
- Implement index compression options

### Search Performance
- Searching specific index is faster than all embeddings
- Cache index metadata to avoid repeated queries
- Implement index statistics for optimization

### Migration Performance
- Batch operations for large libraries
- Progress reporting during migration
- Ability to pause/resume migration

## Success Criteria

1. **All tests pass** (220 existing + ~50 new tests)
2. **No regression** in existing functionality
3. **Migration completes** without data loss
4. **Performance targets** maintained:
   - Search latency <100ms
   - Index detection <50ms
   - UI responsive during operations
5. **User experience** improved:
   - Clear indication of index status
   - Easy index management
   - Smooth upgrade path

## Risk Mitigation

### Risk: Migration fails mid-process
**Mitigation**: Implement transaction-based migration with rollback

### Risk: UI becomes too complex
**Mitigation**: Progressive disclosure - basic mode hides index details

### Risk: Storage requirements increase significantly  
**Mitigation**: Index compression, cleanup tools, storage warnings

### Risk: Search performance degrades
**Mitigation**: Index-specific search, query optimization, caching

## Next Steps

1. ✅ Create failing tests (DONE)
2. ❌ Review tests with team/user
3. ❌ Begin implementation following TDD
4. ❌ Regular test runs to track progress
5. ❌ Documentation as we implement