"""
Test-Driven Development for Multiple Indexes Per Book Feature

Requirements:
1. Multiple indexes per book (by provider, dimensionality, settings)
2. UI to detect if selected books have indexes
3. Ability to manage/delete specific indexes
4. Search dialog to choose which index to use
5. Auto-generate missing indexes before search

TDD Approach:
- Write failing tests FIRST
- Design new database schema
- Create migration path
- Implement UI components
- Verify all tests pass
"""

import pytest
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from calibre_plugins.semantic_search.data.database import SemanticSearchDB
from calibre_plugins.semantic_search.data.repositories import EmbeddingRepository
from calibre_plugins.semantic_search.core.text_processor import Chunk


class TestMultipleIndexesSchema:
    """Test database schema changes for multiple indexes"""
    
    def test_indexes_table_exists(self, tmp_path):
        """Test that indexes table is created with proper schema"""
        db_path = tmp_path / "test.db"
        db = SemanticSearchDB(db_path)
        
        # Check if indexes table exists
        result = db._conn.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='indexes'
        """).fetchone()
        
        assert result is not None, "indexes table should exist"
    
    def test_indexes_table_schema(self, tmp_path):
        """Test indexes table has all required columns"""
        db_path = tmp_path / "test.db"
        db = SemanticSearchDB(db_path)
        
        # Get table info
        columns = db._conn.execute("PRAGMA table_info(indexes)").fetchall()
        column_names = {col[1] for col in columns}
        
        expected_columns = {
            'index_id',           # Primary key
            'book_id',            # Foreign key to books
            'provider',           # embedding provider (openai, vertex, cohere, etc)
            'model_name',         # specific model used
            'dimensions',         # vector dimensions (768, 1536, etc)
            'created_at',         # when index was created
            'updated_at',         # last update time
            'chunk_size',         # chunking parameters
            'chunk_overlap',      # chunking parameters
            'total_chunks',       # number of chunks indexed
            'metadata'            # JSON field for extra settings
        }
        
        assert expected_columns.issubset(column_names), \
            f"Missing columns: {expected_columns - column_names}"
    
    def test_chunks_table_references_index(self, tmp_path):
        """Test chunks table has index_id foreign key"""
        db_path = tmp_path / "test.db"
        db = SemanticSearchDB(db_path)
        
        columns = db._conn.execute("PRAGMA table_info(chunks)").fetchall()
        column_names = {col[1] for col in columns}
        
        assert 'index_id' in column_names, "chunks table should have index_id column"
    
    def test_embeddings_table_references_index(self, tmp_path):
        """Test embeddings table properly references indexes"""
        db_path = tmp_path / "test.db"
        db = SemanticSearchDB(db_path)
        
        # Check what tables exist
        tables = db._conn.execute("SELECT name FROM sqlite_master WHERE type='table' OR type='table'").fetchall()
        table_names = [t[0] for t in tables]
        
        # Check if vec_embeddings or embeddings table has index reference
        if 'embeddings' in table_names:
            columns = db._conn.execute("PRAGMA table_info(embeddings)").fetchall()
        elif 'vec_embeddings' in table_names:
            columns = db._conn.execute("PRAGMA table_info(vec_embeddings)").fetchall()
        else:
            assert False, f"No embeddings table found. Tables: {table_names}"
        
        column_names = {col[1] for col in columns}
        assert 'index_id' in column_names, f"embeddings should reference index_id. Columns: {column_names}"


class TestMultipleIndexesRepository:
    """Test repository methods for multiple indexes"""
    
    @pytest.fixture
    def repo(self, tmp_path):
        db_path = tmp_path / "test.db"
        return EmbeddingRepository(db_path)
    
    def test_create_index_for_book(self, repo):
        """Test creating a new index for a book"""
        book_id = 1
        index_config = {
            'provider': 'openai',
            'model_name': 'text-embedding-3-small',
            'dimensions': 1536,
            'chunk_size': 1000,
            'chunk_overlap': 200
        }
        
        # This should create a new index and return its ID
        index_id = repo.create_index(book_id, **index_config)
        
        assert index_id is not None
        assert isinstance(index_id, int)
    
    def test_get_indexes_for_book(self, repo):
        """Test retrieving all indexes for a book"""
        book_id = 1
        
        # Create multiple indexes with different configurations
        configs = [
            {'provider': 'openai', 'model_name': 'text-embedding-3-small', 'dimensions': 1536},
            {'provider': 'vertex', 'model_name': 'textembedding-gecko', 'dimensions': 768},
            {'provider': 'cohere', 'model_name': 'embed-english-v3.0', 'dimensions': 1024}
        ]
        
        for config in configs:
            repo.create_index(book_id, **config)
        
        # Get all indexes for the book
        indexes = repo.get_indexes_for_book(book_id)
        
        assert len(indexes) == 3
        assert all(idx['book_id'] == book_id for idx in indexes)
        assert {idx['provider'] for idx in indexes} == {'openai', 'vertex', 'cohere'}
    
    def test_store_embedding_with_index(self, repo):
        """Test storing embeddings associated with specific index"""
        book_id = 1
        index_id = repo.create_index(
            book_id, 
            provider='openai',
            model_name='text-embedding-3-small',
            dimensions=1536
        )
        
        chunk = Chunk(
            text="Test philosophical content",
            index=0,
            book_id=book_id,
            start_pos=0,
            end_pos=100,
            metadata={'title': 'Test Book'}
        )
        
        embedding = [0.1] * 1536  # Mock embedding
        
        # Store embedding with specific index
        chunk_id = repo.store_embedding_for_index(index_id, chunk, embedding)
        
        assert chunk_id is not None
        
        # Verify it's associated with the correct index
        stored = repo.get_chunk_with_index(chunk_id)
        assert stored['index_id'] == index_id
    
    def test_search_using_specific_index(self, repo):
        """Test searching within a specific index"""
        book_id = 1
        
        # Create two different indexes
        index1 = repo.create_index(book_id, provider='openai', dimensions=1536)
        index2 = repo.create_index(book_id, provider='vertex', dimensions=768)
        
        # Add embeddings to each index
        chunk1 = Chunk(text="Philosophy content", index=0, book_id=book_id, start_pos=0, end_pos=100, metadata={})
        chunk2 = Chunk(text="Different content", index=0, book_id=book_id, start_pos=0, end_pos=100, metadata={})
        
        repo.store_embedding_for_index(index1, chunk1, [0.1] * 1536)
        repo.store_embedding_for_index(index2, chunk2, [0.2] * 768)
        
        # Search using specific index
        query_embedding = [0.15] * 1536
        results = repo.search_similar_in_index(index1, query_embedding, limit=10)
        
        assert len(results) > 0
        assert all(r['index_id'] == index1 for r in results)
    
    def test_delete_specific_index(self, repo):
        """Test deleting a specific index while preserving others"""
        book_id = 1
        
        # Create multiple indexes
        index1 = repo.create_index(book_id, provider='openai', dimensions=1536)
        index2 = repo.create_index(book_id, provider='vertex', dimensions=768)
        
        # Delete only index1
        repo.delete_index(index1)
        
        # Verify index1 is gone but index2 remains
        indexes = repo.get_indexes_for_book(book_id)
        assert len(indexes) == 1
        assert indexes[0]['index_id'] == index2
    
    def test_get_books_with_indexes(self, repo):
        """Test getting list of books that have indexes"""
        # Create indexes for some books
        repo.create_index(1, provider='openai', dimensions=1536)
        repo.create_index(3, provider='vertex', dimensions=768)
        repo.create_index(3, provider='cohere', dimensions=1024)  # Book 3 has 2 indexes
        
        books_with_indexes = repo.get_books_with_indexes()
        
        assert set(books_with_indexes) == {1, 3}
    
    def test_index_statistics(self, repo):
        """Test getting statistics for each index"""
        book_id = 1
        index_id = repo.create_index(book_id, provider='openai', dimensions=1536)
        
        # Add some chunks
        for i in range(5):
            chunk = Chunk(text=f"Chunk {i}", index=i, book_id=book_id, start_pos=i*100, end_pos=(i+1)*100, metadata={})
            repo.store_embedding_for_index(index_id, chunk, [0.1] * 1536)
        
        stats = repo.get_index_statistics(index_id)
        
        assert stats['total_chunks'] == 5
        assert stats['book_id'] == book_id
        assert stats['provider'] == 'openai'
        assert 'created_at' in stats
        assert 'storage_size' in stats


class TestMultipleIndexesUI:
    """Test UI components for multiple indexes"""
    
    def test_index_detection_in_book_list(self):
        """Test UI can detect which books have indexes"""
        from calibre_plugins.semantic_search.ui.index_detector import IndexDetector
        
        detector = IndexDetector()
        
        # Mock some books with indexes
        book_ids = [1, 2, 3, 4, 5]
        indexed_books = {
            1: [{'provider': 'openai', 'model': 'text-embedding-3-small'}],
            3: [
                {'provider': 'vertex', 'model': 'textembedding-gecko'},
                {'provider': 'cohere', 'model': 'embed-english-v3.0'}
            ]
        }
        
        # Get index status for books
        status = detector.get_index_status(book_ids)
        
        assert status[1]['has_index'] is True
        assert status[1]['index_count'] == 1
        assert status[2]['has_index'] is False
        assert status[3]['has_index'] is True
        assert status[3]['index_count'] == 2
    
    def test_index_manager_dialog(self):
        """Test index management dialog"""
        from calibre_plugins.semantic_search.ui.index_manager_dialog import IndexManagerDialog
        
        dialog = IndexManagerDialog()
        
        # Test loading indexes for a book
        book_id = 1
        dialog.load_indexes_for_book(book_id)
        
        # Test getting selected indexes for deletion
        dialog.select_index(0)  # Select first index
        selected = dialog.get_selected_indexes()
        
        assert len(selected) > 0
        assert all('index_id' in idx for idx in selected)
    
    def test_search_dialog_index_selector(self):
        """Test index selection in search dialog"""
        from calibre_plugins.semantic_search.ui.search_dialog import SearchDialog
        
        dialog = SearchDialog()
        
        # Test populating index selector
        available_indexes = [
            {'index_id': 1, 'provider': 'openai', 'model': 'text-embedding-3-small'},
            {'index_id': 2, 'provider': 'vertex', 'model': 'textembedding-gecko'}
        ]
        
        dialog.populate_index_selector(available_indexes)
        
        # Test getting selected index
        dialog.select_index(0)
        selected_index = dialog.get_selected_index()
        
        assert selected_index is not None
        assert selected_index['index_id'] in [1, 2]
    
    def test_auto_index_generation_prompt(self):
        """Test prompting user to generate missing index"""
        from calibre_plugins.semantic_search.ui.auto_index_dialog import AutoIndexDialog
        
        dialog = AutoIndexDialog()
        
        # Test showing missing index prompt
        missing_config = {
            'provider': 'openai',
            'model': 'text-embedding-3-small',
            'books_without_index': [1, 2, 3]
        }
        
        dialog.show_missing_index_prompt(missing_config)
        
        # Test user choice
        if dialog.should_generate_index():
            selected_books = dialog.get_selected_books()
            assert len(selected_books) > 0
            assert all(book_id in [1, 2, 3] for book_id in selected_books)


class TestIndexMigration:
    """Test migration from single to multiple indexes"""
    
    def test_migrate_existing_embeddings(self, tmp_path):
        """Test migrating existing single-index embeddings to new schema"""
        from calibre_plugins.semantic_search.data.migration import IndexMigration
        
        db_path = tmp_path / "test.db"
        db = SemanticSearchDB(db_path)
        
        # Create some old-style embeddings (before migration)
        # Simulate existing data...
        
        # Run migration
        migration = IndexMigration(db)
        migration.migrate_to_multiple_indexes()
        
        # Verify all old embeddings now have index associations
        result = db._conn.execute("""
            SELECT COUNT(*) FROM chunks 
            WHERE index_id IS NULL
        """).fetchone()
        
        assert result[0] == 0, "All chunks should have index_id after migration"
    
    def test_migration_preserves_data_integrity(self, tmp_path):
        """Test that migration doesn't lose any data"""
        db_path = tmp_path / "test.db"
        
        # Count data before migration
        # ... setup and count ...
        
        # Run migration
        # ... migrate ...
        
        # Count data after migration
        # ... verify counts match ...
        
        assert True  # Placeholder - implement actual data integrity checks


class TestIndexConfiguration:
    """Test index configuration and settings"""
    
    def test_index_config_validation(self):
        """Test validation of index configurations"""
        from calibre_plugins.semantic_search.core.index_config import IndexConfig
        
        # Valid config
        valid_config = IndexConfig(
            provider='openai',
            model_name='text-embedding-3-small',
            dimensions=1536,
            chunk_size=1000,
            chunk_overlap=200
        )
        
        assert valid_config.is_valid()
        
        # Invalid config (mismatched dimensions)
        with pytest.raises(ValueError):
            IndexConfig(
                provider='openai',
                model_name='text-embedding-3-small',
                dimensions=768,  # Wrong dimensions for this model
                chunk_size=1000,
                chunk_overlap=200
            )
    
    def test_index_compatibility_check(self):
        """Test checking if query is compatible with index"""
        from calibre_plugins.semantic_search.core.index_config import IndexConfig
        
        index_config = IndexConfig(
            provider='openai',
            model_name='text-embedding-3-small',
            dimensions=1536
        )
        
        # Compatible query
        assert index_config.is_compatible_with_query(
            provider='openai',
            dimensions=1536
        )
        
        # Incompatible query (different provider)
        assert not index_config.is_compatible_with_query(
            provider='vertex',
            dimensions=768
        )


class TestIndexUsageWorkflow:
    """Test complete workflows with multiple indexes"""
    
    @pytest.fixture
    def repo(self, tmp_path):
        db_path = tmp_path / "test.db"
        return EmbeddingRepository(db_path)
    
    def test_complete_indexing_workflow(self, repo):
        """Test complete workflow from creating index to searching"""
        # 1. Create index for a book
        book_id = 1
        index_id = repo.create_index(
            book_id,
            provider='openai',
            model_name='text-embedding-3-small',
            dimensions=1536,
            chunk_size=1000,
            chunk_overlap=200
        )
        
        # 2. Process and store chunks
        chunks = [
            Chunk(text="Philosophy of mind", index=0, book_id=book_id, start_pos=0, end_pos=100, metadata={}),
            Chunk(text="Consciousness studies", index=1, book_id=book_id, start_pos=100, end_pos=200, metadata={}),
            Chunk(text="Qualia and experience", index=2, book_id=book_id, start_pos=200, end_pos=300, metadata={})
        ]
        
        for chunk in chunks:
            embedding = [0.1] * 1536  # Mock embedding
            repo.store_embedding_for_index(index_id, chunk, embedding)
        
        # 3. Search using the index
        query_embedding = [0.1] * 1536
        results = repo.search_similar_in_index(index_id, query_embedding, limit=5)
        
        assert len(results) == 3
        assert all(r['book_id'] == book_id for r in results)
    
    def test_mixed_index_search_workflow(self, repo):
        """Test searching across multiple indexes with different providers"""
        # Create books with different indexes
        books_indexes = [
            (1, 'openai', 'text-embedding-3-small', 1536),
            (2, 'vertex', 'textembedding-gecko', 768),
            (3, 'cohere', 'embed-english-v3.0', 1024),
            (3, 'openai', 'text-embedding-3-small', 1536),  # Book 3 has 2 indexes
        ]
        
        index_ids = []
        for book_id, provider, model, dims in books_indexes:
            idx = repo.create_index(
                book_id, 
                provider=provider,
                model_name=model,
                dimensions=dims
            )
            index_ids.append((idx, dims))
        
        # Search across all OpenAI indexes
        openai_indexes = repo.get_indexes_by_provider('openai')
        
        assert len(openai_indexes) == 2
        
        # Search in compatible indexes
        query_embedding = [0.1] * 1536
        results = repo.search_across_indexes(
            openai_indexes,
            query_embedding,
            limit=10
        )
        
        assert isinstance(results, list)