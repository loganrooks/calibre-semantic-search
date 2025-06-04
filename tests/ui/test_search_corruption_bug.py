"""
Bug-First TDD: Search results are nonsense random symbols

BUG: Search results return "nonsense random symbols" instead of readable text

This suggests:
1. Text encoding issues during storage/retrieval
2. Vector similarity search returning wrong data
3. Database corruption or wrong data association
4. Text is being corrupted during chunking/storage process

This test should FAIL until we fix the text storage/retrieval corruption.
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os
import tempfile
import sqlite3

# Add paths
plugin_path = os.path.join(os.path.dirname(__file__), '..', '..', 'calibre_plugins', 'semantic_search')
sys.path.insert(0, plugin_path)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from calibre_mocks import *


class TestSearchCorruptionBug:
    """Test that captures search result corruption"""
    
    def test_stored_text_is_not_corrupted(self):
        """
        BUG: Search results show "nonsense random symbols"
        
        This test verifies that text is stored and retrieved correctly
        without corruption during the embedding storage process.
        """
        try:
            from data.database import SemanticSearchDB
            from core.text_processor import Chunk
            
            # Create temporary database
            with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
                test_db_path = f.name
            
            try:
                db = SemanticSearchDB(test_db_path)
                
                # Create test chunk with normal readable text
                test_text = "This is a normal readable sentence with clear English words."
                chunk = Chunk(
                    text=test_text,
                    index=0,
                    book_id=1,
                    start_pos=0,
                    end_pos=len(test_text),
                    metadata={
                        "title": "Test Book",
                        "authors": ["Test Author"]
                    }
                )
                
                # Store embedding
                test_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
                chunk_id = db.store_embedding(1, chunk, test_embedding)
                
                # Retrieve the chunk
                retrieved_chunk = db.get_chunk(chunk_id)
                
                print(f"Original text: {test_text}")
                print(f"Retrieved text: {retrieved_chunk.get('chunk_text', 'NOT FOUND')}")
                
                # Text should be identical, not corrupted
                assert retrieved_chunk is not None
                assert "chunk_text" in retrieved_chunk
                
                retrieved_text = retrieved_chunk["chunk_text"]
                assert retrieved_text == test_text, \
                    f"Text corruption detected!\nOriginal: {test_text}\nRetrieved: {retrieved_text}"
                
                # Should not contain random symbols or corruption
                assert "�" not in retrieved_text, "Text contains Unicode replacement characters"
                assert len(retrieved_text) == len(test_text), "Text length changed during storage"
                
            finally:
                try:
                    os.unlink(test_db_path)
                except:
                    pass
                    
        except Exception as e:
            pytest.fail(f"Text storage/retrieval corruption test failed: {e}")
    
    def test_search_results_return_correct_text_chunks(self):
        """
        Test that search results return the actual stored text chunks,
        not corrupted or random data.
        """
        try:
            from data.database import SemanticSearchDB
            from core.text_processor import Chunk
            
            # Create temporary database
            with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
                test_db_path = f.name
            
            try:
                db = SemanticSearchDB(test_db_path)
                
                # Store multiple chunks with readable text
                test_chunks = [
                    "Philosophy is the study of fundamental questions about existence.",
                    "Epistemology examines the nature of knowledge and justified belief.",
                    "Ethics investigates concepts of right and wrong behavior."
                ]
                
                chunk_ids = []
                for i, text in enumerate(test_chunks):
                    chunk = Chunk(
                        text=text,
                        index=i,
                        book_id=1,
                        start_pos=i * 100,
                        end_pos=(i + 1) * 100,
                        metadata={"title": "Philosophy Book"}
                    )
                    # Simple embedding (in reality would be from embedding service)
                    embedding = [0.1 * (i + 1)] * 5
                    chunk_id = db.store_embedding(1, chunk, embedding)
                    chunk_ids.append(chunk_id)
                
                # Perform search (simple similarity)
                query_embedding = [0.1] * 5  # Similar to first chunk
                results = db.search_similar(query_embedding, limit=3)
                
                print(f"Number of search results: {len(results)}")
                for i, result in enumerate(results):
                    print(f"Result {i}: {result}")
                
                # Results should contain readable text, not random symbols
                assert len(results) > 0, "Search should return results"
                
                for result in results:
                    # Check that result contains text
                    assert "chunk_text" in result or "text" in result, f"Result missing text: {result}"
                    
                    # Get the text from result
                    text = result.get("chunk_text") or result.get("text", "")
                    print(f"Result text: '{text}'")
                    
                    # Should not be empty or random symbols
                    assert len(text) > 0, "Result text is empty"
                    assert any(word in text.lower() for word in ["philosophy", "epistemology", "ethics"]), \
                        f"Result text appears corrupted or random: '{text}'"
                    
                    # Should not contain unicode replacement chars or binary data
                    assert "�" not in text, f"Result contains corruption characters: '{text}'"
                    assert not any(ord(c) > 127 and ord(c) < 160 for c in text), \
                        f"Result contains suspicious non-printable characters: '{text}'"
                
            finally:
                try:
                    os.unlink(test_db_path)
                except:
                    pass
                    
        except Exception as e:
            pytest.fail(f"Search results corruption test failed: {e}")
    
    def test_embedding_storage_retrieval_integrity(self):
        """
        Test that embeddings are stored and retrieved correctly
        without corruption affecting associated text.
        """
        try:
            from data.database import SemanticSearchDB
            from core.text_processor import Chunk
            
            # Create temporary database
            with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
                test_db_path = f.name
            
            try:
                db = SemanticSearchDB(test_db_path)
                
                # Test with various text encodings that might cause issues
                test_texts = [
                    "Simple ASCII text",
                    "Text with émojis and ñ characters",
                    "Unicode: café, naïve, Москва",
                    "Special chars: !@#$%^&*()_+-=[]{}|;':\",./<>?"
                ]
                
                for i, text in enumerate(test_texts):
                    chunk = Chunk(
                        text=text,
                        index=i,
                        book_id=1,
                        start_pos=0,
                        end_pos=len(text),
                        metadata={"title": f"Test Book {i}"}
                    )
                    
                    # Store with embedding
                    embedding = [float(i + 1)] * 768  # Standard embedding size
                    chunk_id = db.store_embedding(1, chunk, embedding)
                    
                    # Immediately retrieve and verify
                    retrieved = db.get_chunk(chunk_id)
                    retrieved_text = retrieved["chunk_text"]
                    
                    print(f"Original: '{text}'")
                    print(f"Retrieved: '{retrieved_text}'")
                    
                    assert retrieved_text == text, \
                        f"Text encoding corruption: '{text}' -> '{retrieved_text}'"
                    
                    # Verify embedding is also correct
                    retrieved_embedding = db.get_embedding(chunk_id)
                    assert retrieved_embedding is not None
                    assert len(retrieved_embedding) == 768
                    assert retrieved_embedding[0] == float(i + 1)
                
            finally:
                try:
                    os.unlink(test_db_path)
                except:
                    pass
                    
        except Exception as e:
            pytest.fail(f"Embedding storage integrity test failed: {e}")