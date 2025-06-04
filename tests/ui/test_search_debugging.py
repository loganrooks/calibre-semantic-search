"""
Debug utilities for search issues

These tests help debug the actual issues reported:
1. "4 chunks for large books" - investigate real chunking behavior  
2. "Nonsense random symbols" - investigate result encoding issues
3. Search performance and user experience issues
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os
import tempfile

# Add paths
plugin_path = os.path.join(os.path.dirname(__file__), '..', '..', 'calibre_plugins', 'semantic_search')
sys.path.insert(0, plugin_path)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from calibre_mocks import *


class TestSearchDebugging:
    """Debug utilities for search issues"""
    
    def test_get_indexing_statistics_for_debugging(self):
        """
        Utility to get detailed statistics about indexing for debugging the "4 chunks" issue.
        
        This helps understand why large books might only produce few chunks.
        """
        try:
            from data.database import SemanticSearchDB
            from core.text_processor import Chunk
            
            # Create temporary database
            with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
                test_db_path = f.name
            
            try:
                db = SemanticSearchDB(test_db_path)
                
                # Simulate indexing a book with various chunk sizes
                book_id = 1
                chunk_sizes = [500, 1000, 2000, 5000]  # Different size chunks
                
                for i, size in enumerate(chunk_sizes):
                    text = "Test content. " * (size // 13)  # Approximately 'size' characters
                    chunk = Chunk(
                        text=text,
                        index=i,
                        book_id=book_id,
                        start_pos=i * size,
                        end_pos=(i + 1) * size,
                        metadata={
                            "title": "Debug Test Book",
                            "authors": ["Debug Author"]
                        }
                    )
                    
                    # Simple embedding
                    embedding = [0.1 * (i + 1)] * 768
                    db.store_embedding(book_id, chunk, embedding)
                
                # Get detailed statistics
                stats = db.get_statistics()
                print("=== INDEXING DEBUG STATISTICS ===")
                print(f"Database statistics: {stats}")
                
                # Get book-specific statistics
                with db.transaction() as conn:
                    # Count chunks for this book
                    cursor = conn.execute("SELECT COUNT(*) FROM chunks WHERE book_id = ?", (book_id,))
                    chunk_count = cursor.fetchone()[0]
                    print(f"Chunks for book {book_id}: {chunk_count}")
                    
                    # Get chunk size distribution
                    cursor = conn.execute("""
                        SELECT chunk_index, LENGTH(chunk_text), chunk_text 
                        FROM chunks WHERE book_id = ? 
                        ORDER BY chunk_index
                    """, (book_id,))
                    
                    chunks_info = cursor.fetchall()
                    print("\n=== CHUNK SIZE ANALYSIS ===")
                    for chunk_index, text_length, text_preview in chunks_info:
                        print(f"Chunk {chunk_index}: {text_length} chars - '{text_preview[:50]}...'")
                    
                    # Check if text is being stored correctly
                    cursor = conn.execute("""
                        SELECT book_id, title, chunk_count, last_indexed 
                        FROM books WHERE book_id = ?
                    """, (book_id,))
                    book_info = cursor.fetchone()
                    if book_info:
                        print(f"\n=== BOOK INFO ===")
                        print(f"Book ID: {book_info[0]}")
                        print(f"Title: {book_info[1]}")
                        print(f"Chunk count: {book_info[2]}")
                        print(f"Last indexed: {book_info[3]}")
                
                # Verify expected results
                assert chunk_count == len(chunk_sizes), f"Expected {len(chunk_sizes)} chunks, got {chunk_count}"
                
            finally:
                try:
                    os.unlink(test_db_path)
                except:
                    pass
                    
        except Exception as e:
            pytest.fail(f"Indexing statistics debug failed: {e}")
    
    def test_search_result_encoding_debug(self):
        """
        Debug utility to investigate the "nonsense random symbols" issue.
        
        This tests various text encodings and search result formats.
        """
        try:
            from data.database import SemanticSearchDB
            from core.text_processor import Chunk
            
            # Create temporary database
            with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
                test_db_path = f.name
            
            try:
                db = SemanticSearchDB(test_db_path)
                
                # Test various text types that might cause encoding issues
                test_texts = [
                    # Normal text
                    "This is normal readable English text about philosophy and knowledge.",
                    # Unicode text
                    "Philosophical concepts: être, Dasein, φρόνησις (phronesis), 智慧 (wisdom)",
                    # Text with special characters  
                    'Quotes: "Hello" \'world\' – em-dash — and... ellipsis',
                    # Mixed content
                    "Mathematical: ∀x∃y (P(x) → Q(y)) and logical symbols ¬∧∨→↔",
                    # Long text
                    "Philosophy " * 100 + " is the study of fundamental questions."
                ]
                
                chunk_ids = []
                for i, text in enumerate(test_texts):
                    chunk = Chunk(
                        text=text,
                        index=i,
                        book_id=1,
                        start_pos=0,
                        end_pos=len(text),
                        metadata={
                            "title": f"Debug Book {i}",
                            "test_type": f"encoding_test_{i}"
                        }
                    )
                    
                    embedding = [0.1] * 768
                    chunk_id = db.store_embedding(1, chunk, embedding)
                    chunk_ids.append(chunk_id)
                
                print("\n=== SEARCH RESULT ENCODING DEBUG ===")
                
                # Test search results
                query_embedding = [0.1] * 768
                results = db.search_similar(query_embedding, limit=10)
                
                print(f"Search returned {len(results)} results")
                
                for i, result in enumerate(results):
                    print(f"\n--- Result {i} ---")
                    print(f"Type: {type(result)}")
                    print(f"Keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
                    
                    if isinstance(result, dict):
                        text = result.get("chunk_text", "NO TEXT FOUND")
                        print(f"Text length: {len(text)}")
                        print(f"Text type: {type(text)}")
                        print(f"Text encoding check: {text.encode('utf-8', errors='replace')[:100]}")
                        print(f"Text preview: '{text[:100]}...'")
                        
                        # Check for common corruption indicators
                        if "�" in text:
                            print("⚠️  WARNING: Contains Unicode replacement characters")
                        if any(ord(c) > 127 and ord(c) < 160 for c in text):
                            print("⚠️  WARNING: Contains suspicious control characters")
                        if len(text) == 0:
                            print("⚠️  WARNING: Empty text")
                        if not any(c.isalpha() for c in text):
                            print("⚠️  WARNING: No alphabetic characters found")
                    else:
                        print(f"⚠️  ERROR: Result is not a dict: {result}")
                
                # Test direct database retrieval
                print("\n=== DIRECT DATABASE RETRIEVAL TEST ===")
                for chunk_id in chunk_ids[:3]:  # Test first 3
                    retrieved = db.get_chunk(chunk_id)
                    if retrieved:
                        text = retrieved.get("chunk_text", "")
                        print(f"Chunk {chunk_id}: '{text[:50]}...' (length: {len(text)})")
                    else:
                        print(f"Chunk {chunk_id}: NOT FOUND")
                
            finally:
                try:
                    os.unlink(test_db_path)
                except:
                    pass
                    
        except Exception as e:
            pytest.fail(f"Search result encoding debug failed: {e}")
    
    def test_real_text_extraction_debug(self):
        """
        Debug utility to test text extraction with real-like EPUB content.
        
        This helps investigate if the "4 chunks" issue is due to text extraction problems.
        """
        try:
            from data.repositories import CalibreRepository
            from core.text_processor import TextProcessor
            import tempfile
            
            # Create a realistic EPUB-like file structure
            epub_base = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>Test Philosophy Book</title>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
</head>
<body>
    <h1>Chapter 1: Introduction to Philosophy</h1>
    <p>Philosophy is the study of fundamental questions about existence, knowledge, values, reason, mind, and language. Such questions are often posed as problems to be studied or resolved.</p>
    
    <p>Some sources claim the term was coined by Pythagoras (c. 570 – c. 495 BCE), though others dispute this story. Philosophical methods include questioning, critical discussion, rational argument, and systematic presentation.</p>
    
    <h2>Major Philosophical Questions</h2>
    <p>What is the meaning of life? What is reality? What is consciousness? How should we live? What can we know? These questions have puzzled humans for millennia.</p>
    
    ''' + '<p>This is additional content. ' * 1000 + '''</p>
    
    <h1>Chapter 2: Epistemology</h1>
    <p>Epistemology is the branch of philosophy concerned with the theory of knowledge, especially with regard to its methods, validity, and scope, and the distinction between justified belief and opinion.</p>
    
    ''' + '<p>More epistemological content here. ' * 500 + '''</p>
    
    <h1>Chapter 3: Ethics</h1>
    <p>Ethics, also called moral philosophy, is the branch of philosophy that involves systematizing, defending, and recommending concepts of right and wrong conduct.</p>
    
    ''' + '<p>Ethical considerations and moral philosophy. ' * 800 + '''</p>
</body>
</html>'''

            epub_content = epub_base.encode('utf-8')

            print(f"\n=== TEXT EXTRACTION DEBUG ===")
            print(f"Original EPUB content size: {len(epub_content)} bytes")
            
            with tempfile.NamedTemporaryFile(suffix='.epub', delete=False) as f:
                f.write(epub_content)
                test_path = f.name
            
            try:
                # Mock Calibre database API
                mock_calibre_db = Mock()
                mock_calibre_db.formats.return_value = ['EPUB']
                mock_calibre_db.format_abspath.return_value = test_path
                
                # Test text extraction
                repo = CalibreRepository(mock_calibre_db)
                extracted_text = repo.get_book_text(1)
                
                print(f"Extracted text length: {len(extracted_text)} characters")
                print(f"Extraction ratio: {len(extracted_text) / len(epub_content):.2%}")
                print(f"Text preview: '{extracted_text[:200]}...'")
                
                # Test chunking
                processor = TextProcessor()
                metadata = {
                    "book_id": 1,
                    "title": "Debug Philosophy Book",
                    "authors": ["Debug Author"]
                }
                
                chunks = processor.chunk_text(extracted_text, metadata)
                
                print(f"\n=== CHUNKING DEBUG ===")
                print(f"Number of chunks created: {len(chunks)}")
                print(f"Average chunk size: {len(extracted_text) / len(chunks) if chunks else 0:.0f} characters")
                
                for i, chunk in enumerate(chunks[:5]):  # Show first 5 chunks
                    print(f"Chunk {i}: {len(chunk.text)} chars - '{chunk.text[:50]}...'")
                
                # Analysis
                if len(chunks) < 10:
                    print(f"⚠️  WARNING: Only {len(chunks)} chunks for {len(extracted_text)} characters")
                    print("This might indicate:")
                    print("- Chunking parameters too large")
                    print("- Text extraction incomplete") 
                    print("- Content mostly metadata/markup")
                    
                # Verify chunks contain actual content
                content_chunks = 0
                for chunk in chunks:
                    if any(word in chunk.text.lower() for word in ["philosophy", "knowledge", "ethics", "epistemology"]):
                        content_chunks += 1
                
                print(f"Chunks with philosophical content: {content_chunks}/{len(chunks)}")
                
            finally:
                try:
                    os.unlink(test_path)
                except:
                    pass
                    
        except Exception as e:
            pytest.fail(f"Text extraction debug failed: {e}")