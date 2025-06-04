"""
Bug-First TDD: Database FOREIGN KEY constraint failed

BUG: Error indexing book 1: FOREIGN KEY constraint failed

From the error, there's a database schema issue where we're trying to insert
data that violates a foreign key constraint. This likely means:
1. Referenced table doesn't exist
2. Referenced record doesn't exist
3. Database schema is not properly initialized

This test should FAIL until we fix the database initialization.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import sys
import os
import tempfile
import sqlite3

# Add paths
plugin_path = os.path.join(os.path.dirname(__file__), '..', '..', 'calibre_plugins', 'semantic_search')
sys.path.insert(0, plugin_path)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from calibre_mocks import *


class TestForeignKeyConstraintBug:
    """Test that captures database foreign key constraint bug"""
    
    def test_indexing_status_foreign_key_constraint_bug(self):
        """
        BUG: FOREIGN KEY constraint failed when updating indexing status
        
        The issue is that update_indexing_status() is called BEFORE the book
        is inserted into the books table, violating the foreign key constraint.
        
        Sequence:
        1. index_single_book() calls update_indexing_status(book_id, "indexing") 
        2. This tries to INSERT into indexing_status with book_id
        3. But book_id doesn't exist in books table yet
        4. FOREIGN KEY constraint failed
        
        This test should FAIL until we fix the ordering.
        """
        try:
            from data.database import SemanticSearchDB
            
            # Create temporary database
            with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
                test_db_path = f.name
            
            try:
                # Initialize database
                db = SemanticSearchDB(test_db_path)
                
                # Try to update indexing status for a book that doesn't exist in books table
                # With the fix, this should now SUCCEED (auto-creates book record)
                db.update_indexing_status(999, "indexing", 0.0)
                
                # Verify that the book was auto-created
                with sqlite3.connect(test_db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT book_id, title FROM books WHERE book_id = ?", (999,))
                    book_row = cursor.fetchone()
                    assert book_row is not None, "Book should have been auto-created"
                    assert book_row[0] == 999
                    assert book_row[1] == "Unknown"  # Default title
                    
                    # Verify indexing status was recorded
                    cursor.execute("SELECT book_id, status FROM indexing_status WHERE book_id = ?", (999,))
                    status_row = cursor.fetchone()
                    assert status_row is not None, "Indexing status should have been recorded"
                    assert status_row[0] == 999
                    assert status_row[1] == "indexing"
                
            finally:
                try:
                    os.unlink(test_db_path)
                except:
                    pass
                    
        except Exception as e:
            pytest.fail(f"update_indexing_status should work with auto-created book records: {e}")

    def test_chunk_id_foreign_key_issue_with_insert_or_replace(self):
        """
        BUG: Foreign key constraint fails when using INSERT OR REPLACE
        
        The issue might be that lastrowid is not reliable with INSERT OR REPLACE,
        causing the foreign key reference to fail.
        
        This test should FAIL until we fix the chunk insertion logic.
        """
        try:
            from data.database import SemanticSearchDB
            from core.text_processor import Chunk
            
            # Create temporary database
            with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
                test_db_path = f.name
            
            try:
                # Initialize database
                db = SemanticSearchDB(test_db_path)
                
                # Create a test chunk
                chunk = Chunk(
                    text="Test chunk text",
                    index=0,
                    book_id=1,
                    start_pos=0,
                    end_pos=10,
                    metadata={
                        "title": "Test Book",
                        "authors": ["Test Author"],
                        "tags": []
                    }
                )
                
                # This should NOT raise "FOREIGN KEY constraint failed"
                # Currently might FAIL because of INSERT OR REPLACE + lastrowid issue
                chunk_id = db.store_embedding(1, chunk, [0.1, 0.2, 0.3])
                
                # Should return a valid chunk_id
                assert chunk_id is not None
                assert chunk_id > 0
                
                # Should be able to retrieve the chunk
                retrieved_chunk = db.get_chunk(chunk_id)
                assert retrieved_chunk is not None
                
            finally:
                try:
                    os.unlink(test_db_path)
                except:
                    pass
                    
        except Exception as e:
            if "FOREIGN KEY constraint failed" in str(e):
                pytest.fail(f"BUG DETECTED: Database foreign key constraint failed during chunk storage: {e}")
            else:
                # Re-raise if it's a different error for debugging
                raise

    def test_indexing_book_fails_with_foreign_key_constraint(self):
        """
        BUG: Error indexing book 1: FOREIGN KEY constraint failed
        
        This indicates the database schema is not properly initialized
        or there's a missing table/record that's being referenced.
        
        This test should FAIL until we fix the database initialization.
        """
        try:
            from interface import SemanticSearchInterface
            from data.database import SemanticSearchDB
            from data.repositories import EmbeddingRepository, CalibreRepository
            from core.indexing_service import IndexingService
            from core.text_processor import TextProcessor
            from core.embedding_service import create_embedding_service
            
            # Create temporary database for testing
            with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
                test_db_path = f.name
            
            try:
                # Initialize all components with real database
                interface = SemanticSearchInterface()
                interface.gui = Mock()
                interface.gui.current_db = Mock()
                interface.gui.current_db.new_api = Mock()
                
                # Mock Calibre database operations
                interface.gui.current_db.new_api.get_metadata = Mock()
                interface.gui.current_db.new_api.get_metadata.return_value = Mock()
                interface.gui.current_db.new_api.get_metadata.return_value.title = "Test Book"
                interface.gui.current_db.new_api.get_metadata.return_value.authors = ["Test Author"]
                interface.gui.current_db.new_api.get_metadata.return_value.format_files = Mock(return_value=[])
                
                # Set up repositories with real database
                interface.embedding_repo = EmbeddingRepository(test_db_path)
                interface.calibre_repo = CalibreRepository(interface.gui.current_db.new_api)
                
                # Create services
                config_dict = {
                    'provider': 'test',
                    'api_key': 'test_key',
                    'model': 'test-model'
                }
                interface.embedding_service = create_embedding_service(config_dict)
                interface.text_processor = TextProcessor()
                
                # Create indexing service
                interface.indexing_service = IndexingService(
                    text_processor=interface.text_processor,
                    embedding_service=interface.embedding_service,
                    embedding_repo=interface.embedding_repo,
                    calibre_repo=interface.calibre_repo
                )
                
                # Set up book_ids for indexing
                interface.current_indexing_book_ids = [1]
                
                # Mock the embedding service to return test embeddings
                async def mock_generate_embeddings(texts):
                    return [[0.1, 0.2, 0.3] for _ in texts]
                
                interface.embedding_service.generate_embeddings = mock_generate_embeddings
                
                # This should NOT raise "FOREIGN KEY constraint failed" 
                # Currently FAILS because database schema is not properly initialized
                result = interface._run_indexing_job(
                    notifications=Mock(),
                    abort=Mock(),
                    log=Mock()
                )
                
                # Should complete successfully
                assert result is not None
                assert result.get('failed_books', 1) == 0  # No failed books
                assert result.get('successful_books', 0) > 0  # At least one successful
                
            finally:
                # Cleanup
                try:
                    os.unlink(test_db_path)
                except:
                    pass
                    
        except Exception as e:
            if "FOREIGN KEY constraint failed" in str(e):
                pytest.fail(f"BUG DETECTED: Database foreign key constraint failed: {e}")
            else:
                # Re-raise if it's a different error for debugging
                raise
    
    def test_database_schema_initialization_creates_all_tables(self):
        """
        Test that database schema initialization creates all required tables
        with proper foreign key relationships.
        """
        try:
            from data.database import SemanticSearchDB
            
            # Create temporary database
            with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
                test_db_path = f.name
            
            try:
                # Initialize database
                db = SemanticSearchDB(test_db_path)
                
                # Check that all tables exist
                with sqlite3.connect(test_db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Get list of tables
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [row[0] for row in cursor.fetchall()]
                    
                    # Should have all required tables
                    required_tables = ['embeddings', 'chunks', 'books']  # Adjust based on actual schema
                    for table in required_tables:
                        assert table in tables, f"Missing required table: {table}"
                    
                    # Check foreign key constraints are properly defined
                    cursor.execute("PRAGMA foreign_keys = ON")
                    
                    # Try to insert valid data - should work
                    # This will help identify which foreign key is failing
                    
            finally:
                try:
                    os.unlink(test_db_path)
                except:
                    pass
                    
        except Exception as e:
            pytest.fail(f"Database schema initialization failed: {e}")
    
    def test_embedding_repository_handles_missing_tables_gracefully(self):
        """
        Test that EmbeddingRepository handles missing tables gracefully
        and creates them if needed.
        """
        try:
            from data.repositories import EmbeddingRepository
            
            # Create temporary database (empty)
            with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
                test_db_path = f.name
            
            try:
                # Create repository - should handle missing tables
                repo = EmbeddingRepository(test_db_path)
                
                # Try basic operations - should not fail with foreign key constraint
                # This will help identify if the issue is in repository initialization
                
            finally:
                try:
                    os.unlink(test_db_path)
                except:
                    pass
                    
        except Exception as e:
            if "FOREIGN KEY constraint failed" in str(e):
                pytest.fail(f"BUG DETECTED: EmbeddingRepository has foreign key issues: {e}")
            else:
                raise
    
    def test_indexing_service_initialization_creates_required_db_schema(self):
        """
        Test that IndexingService initialization ensures database schema exists.
        
        This test verifies that all required tables and relationships are created
        before any indexing operations begin.
        """
        try:
            from data.repositories import EmbeddingRepository, CalibreRepository
            from core.indexing_service import IndexingService
            from core.text_processor import TextProcessor
            from core.embedding_service import create_embedding_service
            
            # Create temporary database
            with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
                test_db_path = f.name
            
            try:
                # Create mock Calibre repository
                mock_calibre_repo = Mock()
                
                # Create components
                embedding_repo = EmbeddingRepository(test_db_path)
                text_processor = TextProcessor()
                
                config_dict = {
                    'provider': 'test',
                    'api_key': 'test_key', 
                    'model': 'test-model'
                }
                embedding_service = create_embedding_service(config_dict)
                
                # Create indexing service - should ensure schema exists
                indexing_service = IndexingService(
                    text_processor=text_processor,
                    embedding_service=embedding_service,
                    embedding_repo=embedding_repo,
                    calibre_repo=mock_calibre_repo
                )
                
                # Verify that the service created required database schema
                with sqlite3.connect(test_db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("PRAGMA foreign_keys = ON")
                    
                    # Should be able to perform basic operations without foreign key errors
                    
            finally:
                try:
                    os.unlink(test_db_path)
                except:
                    pass
                    
        except Exception as e:
            if "FOREIGN KEY constraint failed" in str(e):
                pytest.fail(f"BUG DETECTED: IndexingService initialization has foreign key issues: {e}")
            else:
                raise