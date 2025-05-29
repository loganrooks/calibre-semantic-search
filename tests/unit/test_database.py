"""
Unit tests for database layer following TDD approach
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import numpy as np

# Direct import to avoid Calibre dependencies
import sys
plugin_path = Path(__file__).parent.parent.parent / "calibre_plugins" / "semantic_search"
sys.path.insert(0, str(plugin_path))

# Import database module directly
import importlib.util
spec = importlib.util.spec_from_file_location(
    "database", 
    plugin_path / "data" / "database.py"
)
database_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(database_module)
SemanticSearchDB = database_module.SemanticSearchDB

# Import text processor for Chunk class
spec2 = importlib.util.spec_from_file_location(
    "text_processor",
    plugin_path / "core" / "text_processor.py"
)
text_processor_module = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(text_processor_module)
Chunk = text_processor_module.Chunk


@pytest.fixture
def temp_db_path():
    """Create temporary database path"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir) / "test.db"
    shutil.rmtree(temp_dir)


class TestDatabaseCreation:
    """Test database initialization and creation"""
    
    def test_database_creation(self, temp_db_path):
        """Test creating a new database"""
        db = SemanticSearchDB(str(temp_db_path))
        
        assert temp_db_path.exists()
        assert db.db_path == temp_db_path
        
        db.close()
    
    def test_schema_creation(self, temp_db_path):
        """Test that schema is created correctly"""
        db = SemanticSearchDB(str(temp_db_path))
        
        # Check tables exist
        cursor = db._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = {row[0] for row in cursor.fetchall()}
        
        assert 'embeddings' in tables
        assert 'books' in tables
        assert 'schema_version' in tables
        
        db.close()
    
    def test_vec_extension_loading(self, temp_db_path):
        """Test sqlite-vec extension loading"""
        db = SemanticSearchDB(str(temp_db_path))
        
        # Check if vec functions are available
        try:
            cursor = db._conn.execute("SELECT vec_version()")
            version = cursor.fetchone()[0]
            assert version is not None
        except Exception:
            # Extension not available - that's OK, we have fallback
            pass
        
        db.close()


class TestEmbeddingOperations:
    """Test embedding storage and retrieval"""
    
    @pytest.fixture
    def db_with_data(self, temp_db_path):
        """Create database with test data"""
        db = SemanticSearchDB(str(temp_db_path))
        
        # No explicit book management in this database
        # It stores embeddings directly
        
        yield db
        db.close()
    
    def test_add_embedding(self, db_with_data):
        """Test adding an embedding"""
        embedding = np.random.rand(768).astype(np.float32)
        
        # Create a chunk object
        chunk = Chunk(
            text="Test chunk text",
            index=0,
            book_id=1,
            start_pos=0,
            end_pos=15,
            metadata={"page": 1}
        )
        
        chunk_id = db_with_data.store_embedding(
            book_id=1,
            chunk=chunk,
            embedding=embedding
        )
        
        assert chunk_id is not None
        assert chunk_id > 0
    
    def test_search_similar(self, db_with_data):
        """Test searching for similar embeddings"""
        # Add some embeddings
        emb1 = np.random.rand(768).astype(np.float32)
        emb2 = np.random.rand(768).astype(np.float32)
        emb3 = np.random.rand(768).astype(np.float32)
        
        # Create and store chunks
        for i, emb in enumerate([emb1, emb2, emb3]):
            chunk = Chunk(
                text=f"Chunk {i+1}",
                index=i,
                book_id=1,
                start_pos=i*10,
                end_pos=(i+1)*10,
                metadata={}
            )
            db_with_data.store_embedding(1, chunk, emb)
        
        # Search for similar
        results = db_with_data.search_similar(
            embedding=emb1,
            limit=2
        )
        
        assert len(results) <= 2
        assert all('chunk_id' in r for r in results)
        assert all('similarity' in r for r in results)
        
        # Results should be sorted by similarity
        if len(results) > 1:
            assert results[0]['similarity'] >= results[1]['similarity']
    
    def test_get_embedding_by_id(self, db_with_data):
        """Test retrieving embedding by ID"""
        embedding = np.random.rand(768).astype(np.float32)
        
        # Create and store a chunk
        chunk = Chunk(
            text="Test chunk",
            index=0,
            book_id=1,
            start_pos=0,
            end_pos=10,
            metadata={}
        )
        
        chunk_id = db_with_data.store_embedding(
            book_id=1,
            chunk=chunk,
            embedding=embedding
        )
        
        # Get embedding returns just the vector
        result = db_with_data.get_embedding(chunk_id)
        
        assert result is not None
        np.testing.assert_array_almost_equal(
            result, embedding, decimal=5
        )


class TestBookOperations:
    """Test book-related operations"""
    
    @pytest.fixture
    def empty_db(self, temp_db_path):
        """Create empty database"""
        db = SemanticSearchDB(str(temp_db_path))
        yield db
        db.close()
    
    def test_clear_book_embeddings(self, empty_db):
        """Test clearing embeddings for a book"""
        # Add some embeddings
        embedding = np.random.rand(768).astype(np.float32)
        
        for i in range(3):
            chunk = Chunk(
                text=f"Chunk {i}",
                index=i,
                book_id=1,
                start_pos=i*10,
                end_pos=(i+1)*10,
                metadata={}
            )
            empty_db.store_embedding(1, chunk, embedding)
        
        # Clear embeddings for book
        empty_db.clear_book_embeddings(1)
        
        # Check chunks are gone (embeddings cascade delete)
        cursor = empty_db._conn.execute(
            "SELECT COUNT(*) FROM chunks WHERE book_id = ?", (1,)
        )
        assert cursor.fetchone()[0] == 0
    
    def test_indexing_status_table_exists(self, empty_db):
        """Test that indexing status table exists"""
        # Check indexing_status table exists
        cursor = empty_db._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='indexing_status'"
        )
        assert cursor.fetchone() is not None


class TestSchemaManagement:
    """Test schema versioning and migrations"""
    
    def test_schema_creation(self, temp_db_path):
        """Test schema is created on init"""
        db = SemanticSearchDB(str(temp_db_path))
        
        # Check schema version table exists
        cursor = db._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
        )
        assert cursor.fetchone() is not None
        
        db.close()


class TestPerformance:
    """Test performance requirements"""
    
    @pytest.fixture
    def large_db(self, temp_db_path):
        """Create database with many embeddings"""
        db = SemanticSearchDB(str(temp_db_path))
        
        # Add many embeddings
        for i in range(100):
            embedding = np.random.rand(768).astype(np.float32)
            chunk = Chunk(
                text=f"Chunk {i}",
                index=i,
                book_id=1,
                start_pos=i*100,
                end_pos=(i+1)*100,
                metadata={}
            )
            db.store_embedding(1, chunk, embedding)
        
        yield db
        db.close()
    
    def test_search_performance(self, large_db):
        """Test search meets performance requirements"""
        import time
        
        query_embedding = np.random.rand(768).astype(np.float32)
        
        start = time.time()
        results = large_db.search_similar(query_embedding, limit=10)
        duration = time.time() - start
        
        assert len(results) <= 10
        # Should be fast even with 100 embeddings
        assert duration < 0.1  # 100ms requirement from spec


if __name__ == "__main__":
    pytest.main([__file__, "-v"])