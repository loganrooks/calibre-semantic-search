"""
Bug-First TDD: Large books only creating 4 chunks

BUG: Large books are being processed into very few chunks (e.g., 4 chunks for "super large books")

This suggests:
1. Text extraction is incomplete (only getting partial content)
2. Chunking algorithm is too aggressive (chunks too large)
3. Chunking parameters are misconfigured

This test should FAIL until we fix the chunking logic.
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add paths
plugin_path = os.path.join(os.path.dirname(__file__), '..', '..', 'calibre_plugins', 'semantic_search')
sys.path.insert(0, plugin_path)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from calibre_mocks import *


class TestChunkingIssues:
    """Test that captures chunking problems"""
    
    def test_large_book_creates_reasonable_number_of_chunks(self):
        """
        BUG: Large books only creating 4 chunks for "super large books"
        
        A large book (e.g., 100,000+ words) should create many more chunks
        than just 4. This suggests either:
        1. Text extraction is incomplete
        2. Chunk size is too large
        3. Chunking algorithm has bugs
        """
        try:
            from core.text_processor import TextProcessor
            
            processor = TextProcessor()
            
            # Create a large text (simulate a large book)
            # Average book has ~250-300 words per page
            # Large book might be 400+ pages = 100,000+ words
            large_text = "This is a test sentence with meaningful content. " * 10000  # ~100,000 words
            
            metadata = {
                "book_id": 1,
                "title": "Large Test Book",
                "authors": ["Test Author"]
            }
            
            # Chunk the text
            chunks = processor.chunk_text(large_text, metadata)
            
            print(f"Large text length: {len(large_text)} characters")
            print(f"Number of chunks created: {len(chunks)}")
            
            # For 100,000 words (~500,000 characters), we should get many more than 4 chunks
            # Assuming reasonable chunk size (1000-2000 chars), should be 250-500 chunks
            min_expected_chunks = 50  # Very conservative minimum
            
            assert len(chunks) >= min_expected_chunks, \
                f"Large book should create at least {min_expected_chunks} chunks, got {len(chunks)}"
            
            # Verify chunks have reasonable size
            for i, chunk in enumerate(chunks[:5]):  # Check first 5 chunks
                print(f"Chunk {i}: {len(chunk.text)} characters")
                assert len(chunk.text) > 0, f"Chunk {i} is empty"
                assert len(chunk.text) < 10000, f"Chunk {i} is too large: {len(chunk.text)} chars"
            
        except Exception as e:
            pytest.fail(f"Chunking large text failed: {e}")
    
    def test_chunking_parameters_are_reasonable(self):
        """
        Test that chunking parameters produce reasonable chunk sizes.
        """
        try:
            from core.text_processor import TextProcessor
            
            processor = TextProcessor()
            
            # Check chunking parameters
            # These might be configurable attributes
            if hasattr(processor, 'chunk_size'):
                print(f"Chunk size: {processor.chunk_size}")
                assert processor.chunk_size <= 2000, f"Chunk size too large: {processor.chunk_size}"
                assert processor.chunk_size >= 500, f"Chunk size too small: {processor.chunk_size}"
            
            if hasattr(processor, 'overlap'):
                print(f"Chunk overlap: {processor.overlap}")
                assert processor.overlap >= 0, "Overlap should be non-negative"
                assert processor.overlap < processor.chunk_size if hasattr(processor, 'chunk_size') else True
            
        except Exception as e:
            pytest.fail(f"Checking chunking parameters failed: {e}")
    
    def test_text_extraction_completeness(self):
        """
        Test that text extraction is getting complete book content, not just partial.
        
        This test checks if the "4 chunks for large book" issue is due to 
        incomplete text extraction.
        """
        try:
            from data.repositories import CalibreRepository
            import tempfile
            
            # Create a large test file (simulating large EPUB)
            large_content = b"""<?xml version="1.0" encoding="UTF-8"?>
            <html><body>""" + b"<p>This is a test paragraph with meaningful content. " * 5000 + b"</p></body></html>"
            
            print(f"Test file size: {len(large_content)} bytes")
            
            with tempfile.NamedTemporaryFile(suffix='.epub', delete=False) as f:
                f.write(large_content)
                test_path = f.name
            
            try:
                # Mock Calibre database API
                mock_calibre_db = Mock()
                mock_calibre_db.formats.return_value = ['EPUB']
                mock_calibre_db.format_abspath.return_value = test_path
                
                # Create repository
                repo = CalibreRepository(mock_calibre_db)
                
                # Extract text
                extracted_text = repo.get_book_text(1)
                
                print(f"Extracted text length: {len(extracted_text)} characters")
                
                # Text should be substantially extracted
                # Original was ~125,000 bytes, extracted should be significant portion
                assert len(extracted_text) > 10000, \
                    f"Extracted text too short: {len(extracted_text)} chars (might indicate incomplete extraction)"
                
                # Should contain the test content
                assert "test paragraph" in extracted_text.lower()
                
            finally:
                import os
                try:
                    os.unlink(test_path)
                except:
                    pass
            
        except Exception as e:
            pytest.fail(f"Text extraction completeness test failed: {e}")