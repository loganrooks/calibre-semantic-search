"""
Bug-First TDD: Text extraction from EPUB files fails

BUG: Error extracting text from *.epub: '_io.BytesIO' object is not callable

From the error, the text extraction is treating a BytesIO object as if it were
a callable function. This suggests a bug in the get_book_text method where
we're trying to call a BytesIO object instead of reading from it.

This test should FAIL until we fix the text extraction logic.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import io

# Add paths
plugin_path = os.path.join(os.path.dirname(__file__), '..', '..', 'calibre_plugins', 'semantic_search')
sys.path.insert(0, plugin_path)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from calibre_mocks import *


class TestTextExtractionBug:
    """Test that captures text extraction bug"""
    
    def test_text_extraction_simplified_approach_works(self):
        """
        FIXED: Text extraction now uses simplified approach to avoid BytesIO issues.
        
        The fix replaced complex Calibre Plumber API with simple file reading
        and basic HTML tag removal, avoiding the BytesIO callable error.
        """
        try:
            from data.repositories import CalibreRepository
            import tempfile
            import zipfile
            
            # Create a proper EPUB file (ZIP structure)
            with tempfile.NamedTemporaryFile(suffix='.epub', delete=False) as f:
                test_path = f.name
                
            with zipfile.ZipFile(test_path, 'w') as epub:
                # Add mimetype
                epub.writestr('mimetype', 'application/epub+zip', compress_type=zipfile.ZIP_STORED)
                
                # Add content
                test_content = """<?xml version="1.0" encoding="UTF-8"?>
                <html><body><p>This is test content from an EPUB file.</p></body></html>"""
                epub.writestr('content.html', test_content)
            
            try:
                # Mock Calibre database API
                mock_calibre_db = Mock()
                mock_calibre_db.formats.return_value = ['EPUB']
                mock_calibre_db.format_abspath.return_value = test_path
                
                # Create repository
                repo = CalibreRepository(mock_calibre_db)
                
                # This should NOT raise "'_io.BytesIO' object is not callable"
                # With the fix, this should work with simplified text extraction
                text = repo.get_book_text(1)
                
                # Should return extracted text
                assert text is not None
                assert len(text) > 0
                assert "test content" in text.lower()
                
            finally:
                import os
                try:
                    os.unlink(test_path)
                except:
                    pass
            
        except Exception as e:
            pytest.fail(f"Text extraction should work with simplified approach: {e}")
    
    def test_get_book_text_handles_epub_format_correctly(self):
        """
        Test that get_book_text properly handles EPUB format extraction.
        
        EPUB files need special handling to extract text content from HTML/XML.
        """
        try:
            from data.repositories import CalibreRepository
            
            # Mock Calibre database API  
            mock_calibre_db = Mock()
            
            # Mock book with EPUB format
            mock_calibre_db.format_files.return_value = [
                ('EPUB', '/path/to/book.epub')
            ]
            
            # Mock EPUB data as BytesIO
            test_epub_content = b"""<?xml version="1.0" encoding="UTF-8"?>
            <html><body><p>This is test content from an EPUB file.</p></body></html>"""
            mock_bytesio = io.BytesIO(test_epub_content)
            mock_calibre_db.format.return_value = mock_bytesio
            
            # Create repository
            repo = CalibreRepository(mock_calibre_db)
            
            # Should extract text successfully
            text = repo.get_book_text(1)
            
            # Should contain the text content
            assert text is not None
            assert "test content" in text.lower()
            
        except Exception as e:
            pytest.fail(f"get_book_text should handle EPUB format correctly: {e}")
    
    def test_get_book_text_handles_missing_formats_gracefully(self):
        """
        Test that get_book_text handles books with no readable formats gracefully.
        """
        try:
            from data.repositories import CalibreRepository
            
            # Mock Calibre database API
            mock_calibre_db = Mock()
            
            # Mock book with no formats
            mock_calibre_db.format_files.return_value = []
            
            # Create repository
            repo = CalibreRepository(mock_calibre_db)
            
            # Should return empty string or None, not crash
            text = repo.get_book_text(1)
            
            # Should handle gracefully
            assert text is None or text == ""
            
        except Exception as e:
            pytest.fail(f"get_book_text should handle missing formats gracefully: {e}")
    
    def test_get_book_text_bytesio_reading_pattern(self):
        """
        Test the correct pattern for reading from BytesIO objects.
        
        BytesIO objects should be read with .read() or .getvalue(), not called directly.
        """
        try:
            # Demonstrate correct BytesIO usage
            test_data = b"Test content"
            bytesio_obj = io.BytesIO(test_data)
            
            # CORRECT: Read from BytesIO
            content = bytesio_obj.read()
            assert content == test_data
            
            # CORRECT: Get value from BytesIO
            bytesio_obj.seek(0)
            content2 = bytesio_obj.getvalue()
            assert content2 == test_data
            
            # INCORRECT: This would cause "'_io.BytesIO' object is not callable"
            # content3 = bytesio_obj()  # This fails!
            
        except Exception as e:
            pytest.fail(f"BytesIO reading pattern test failed: {e}")