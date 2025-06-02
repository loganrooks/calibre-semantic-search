"""
Test-Driven Development for Multiple Indexes Database Schema

Tests the database schema changes required for multiple indexes per book.
Focuses on table structure, foreign keys, and constraints.

Part of comprehensive multiple indexes implementation following SPARC+TDD.
"""

import pytest
from pathlib import Path

from calibre_plugins.semantic_search.data.database import SemanticSearchDB


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

    def test_unique_constraint_on_index_config(self, tmp_path):
        """Test unique constraint prevents duplicate index configurations"""
        db_path = tmp_path / "test.db"
        db = SemanticSearchDB(db_path)
        
        # Insert a book first (foreign key requirement)
        with db.transaction() as conn:
            conn.execute(
                "INSERT INTO books (book_id, title, authors, tags) VALUES (?, ?, ?, ?)",
                (1, "Test Book", "[]", "[]")
            )
            
            # Insert first index configuration
            conn.execute("""
                INSERT INTO indexes (book_id, provider, model_name, dimensions, chunk_size, chunk_overlap)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (1, 'openai', 'text-embedding-3-small', 1536, 1000, 200))
            
            # Try to insert duplicate configuration - should fail
            with pytest.raises(Exception):  # Should violate unique constraint
                conn.execute("""
                    INSERT INTO indexes (book_id, provider, model_name, dimensions, chunk_size, chunk_overlap)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (1, 'openai', 'text-embedding-3-small', 1536, 1000, 200))

    def test_foreign_key_constraints_enforced(self, tmp_path):
        """Test foreign key constraints are properly enforced"""
        db_path = tmp_path / "test.db"
        db = SemanticSearchDB(db_path)
        
        with db.transaction() as conn:
            # Try to insert index for non-existent book
            with pytest.raises(Exception):  # Should fail foreign key constraint
                conn.execute("""
                    INSERT INTO indexes (book_id, provider, model_name, dimensions, chunk_size)
                    VALUES (?, ?, ?, ?, ?)
                """, (999, 'openai', 'test-model', 768, 512))

    def test_cascade_deletion_behavior(self, tmp_path):
        """Test that deleting book cascades to indexes and related data"""
        db_path = tmp_path / "test.db"
        db = SemanticSearchDB(db_path)
        
        with db.transaction() as conn:
            # Insert book and index
            conn.execute(
                "INSERT INTO books (book_id, title, authors, tags) VALUES (?, ?, ?, ?)",
                (1, "Test Book", "[]", "[]")
            )
            
            conn.execute("""
                INSERT INTO indexes (book_id, provider, model_name, dimensions, chunk_size)
                VALUES (?, ?, ?, ?, ?)
            """, (1, 'openai', 'test-model', 768, 512))
            
            # Get the index_id
            index_row = conn.execute("SELECT index_id FROM indexes WHERE book_id = 1").fetchone()
            index_id = index_row[0]
            
            # Insert chunk and embedding
            conn.execute("""
                INSERT INTO chunks (book_id, index_id, chunk_index, chunk_text, start_pos, end_pos, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (1, index_id, 0, "Test chunk", 0, 10, "{}"))
            
            chunk_row = conn.execute("SELECT chunk_id FROM chunks WHERE index_id = ?", (index_id,)).fetchone()
            chunk_id = chunk_row[0]
            
            # Try to add embedding (handle both table types)
            try:
                conn.execute("""
                    INSERT INTO embeddings (chunk_id, index_id, embedding)
                    VALUES (?, ?, ?)
                """, (chunk_id, index_id, b'test_embedding_data'))
            except:
                # Might be vec_embeddings table
                pass
        
        # Now delete the book
        with db.transaction() as conn:
            conn.execute("DELETE FROM books WHERE book_id = 1")
            
            # Verify cascading deletion
            indexes = conn.execute("SELECT * FROM indexes WHERE book_id = 1").fetchall()
            chunks = conn.execute("SELECT * FROM chunks WHERE book_id = 1").fetchall()
            
            assert len(indexes) == 0, "Indexes should be deleted when book is deleted"
            assert len(chunks) == 0, "Chunks should be deleted when book is deleted"

    def test_metadata_json_field_handling(self, tmp_path):
        """Test that metadata JSON field handles complex data properly"""
        db_path = tmp_path / "test.db"
        db = SemanticSearchDB(db_path)
        
        import json
        
        complex_metadata = {
            'custom_settings': {
                'temperature': 0.7,
                'max_tokens': 1000,
                'special_instructions': ['preserve context', 'focus on philosophy']
            },
            'created_by': 'user_test',
            'version': '1.0.0'
        }
        
        with db.transaction() as conn:
            # Insert book first
            conn.execute(
                "INSERT INTO books (book_id, title, authors, tags) VALUES (?, ?, ?, ?)",
                (1, "Test Book", "[]", "[]")
            )
            
            # Insert index with complex metadata
            conn.execute("""
                INSERT INTO indexes (book_id, provider, model_name, dimensions, chunk_size, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (1, 'openai', 'test-model', 768, 512, json.dumps(complex_metadata)))
            
            # Retrieve and verify metadata
            row = conn.execute("SELECT metadata FROM indexes WHERE book_id = 1").fetchone()
            retrieved_metadata = json.loads(row[0])
            
            assert retrieved_metadata == complex_metadata
            assert retrieved_metadata['custom_settings']['temperature'] == 0.7
            assert 'preserve context' in retrieved_metadata['custom_settings']['special_instructions']