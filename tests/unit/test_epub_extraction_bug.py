"""
Bug-First TDD: EPUB text extraction returns raw ZIP data instead of text

BUG: EPUB files are being read as raw binary data, showing ZIP headers like:
'PK\x03\x04\x14\x00\x16\x08\x00\x004QVoa,\x14\x00\x00\x00\x14\x00\x00\x00\x08\x00\x00\x00mimetypeapplication/epub+zip...'

This test should FAIL until we properly extract text from EPUB files.
"""

import pytest
import tempfile
import zipfile
import os
from pathlib import Path
from unittest.mock import Mock, patch

# Direct import to avoid Calibre dependencies
import sys
plugin_path = Path(__file__).parent.parent.parent / "calibre_plugins" / "semantic_search"
sys.path.insert(0, str(plugin_path))

from data.repositories import CalibreRepository


class TestEPUBExtractionBug:
    """Test that captures EPUB text extraction bug"""
    
    def create_test_epub(self, content_html: str) -> str:
        """Create a minimal EPUB file for testing"""
        # Create a temporary EPUB file
        with tempfile.NamedTemporaryFile(suffix='.epub', delete=False) as tmp:
            with zipfile.ZipFile(tmp.name, 'w') as epub:
                # Add mimetype (must be first and uncompressed)
                epub.writestr('mimetype', 'application/epub+zip', compress_type=zipfile.ZIP_STORED)
                
                # Add container.xml
                container_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
    <rootfiles>
        <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
    </rootfiles>
</container>'''
                epub.writestr('META-INF/container.xml', container_xml)
                
                # Add content.opf
                content_opf = '''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="2.0">
    <metadata>
        <dc:title xmlns:dc="http://purl.org/dc/elements/1.1/">Test Book</dc:title>
    </metadata>
    <manifest>
        <item id="content" href="content.html" media-type="application/xhtml+xml"/>
    </manifest>
    <spine>
        <itemref idref="content"/>
    </spine>
</package>'''
                epub.writestr('content.opf', content_opf)
                
                # Add the actual content
                epub.writestr('content.html', content_html)
                
            return tmp.name
    
    def test_epub_extraction_returns_text_not_zip_data(self):
        """
        BUG: EPUB extraction returns raw ZIP data instead of text content.
        This test should FAIL until we fix the extraction logic.
        """
        # Create test EPUB with known content
        test_content = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>Test Chapter</title>
</head>
<body>
    <h1>Chapter 1: The Beginning</h1>
    <p>This is a test paragraph with some philosophical content about the nature of existence.</p>
    <p>Another paragraph discussing dialectical reasoning and its implications.</p>
</body>
</html>'''
        
        epub_path = self.create_test_epub(test_content)
        
        try:
            # Mock Calibre database
            mock_calibre_db = Mock()
            mock_calibre_db.formats.return_value = ['EPUB']
            mock_calibre_db.format_abspath.return_value = epub_path
            
            # Create repository
            repo = CalibreRepository(mock_calibre_db)
            
            # Extract text
            extracted_text = repo.get_book_text(1, 'EPUB')
            
            # ASSERTIONS: What the text should contain
            assert extracted_text is not None
            assert len(extracted_text) > 0
            
            # Should NOT contain ZIP headers
            assert 'PK\x03\x04' not in extracted_text, "Text contains ZIP header - raw binary data!"
            assert 'mimetypeapplication/epub+zip' not in extracted_text, "Text contains EPUB mimetype - raw data!"
            
            # Should contain actual text content
            assert 'Chapter 1: The Beginning' in extracted_text, "Missing chapter title"
            assert 'philosophical content' in extracted_text, "Missing paragraph content"
            assert 'dialectical reasoning' in extracted_text, "Missing second paragraph"
            
            # Should NOT contain HTML tags (should be stripped)
            assert '<html>' not in extracted_text, "HTML tags not stripped"
            assert '<body>' not in extracted_text, "HTML tags not stripped"
            assert '<p>' not in extracted_text, "HTML tags not stripped"
            
        finally:
            # Clean up
            os.unlink(epub_path)
    
    def test_epub_extraction_fix_verified(self):
        """
        Verify that the EPUB extraction bug has been fixed.
        This test confirms proper text extraction without ZIP headers.
        """
        # Create test EPUB
        epub_path = self.create_test_epub('<html><body><p>Test content for verification</p></body></html>')
        
        try:
            # Mock Calibre database
            mock_calibre_db = Mock()
            mock_calibre_db.formats.return_value = ['EPUB']
            mock_calibre_db.format_abspath.return_value = epub_path
            
            # Create repository
            repo = CalibreRepository(mock_calibre_db)
            
            # Extract text with fixed implementation
            extracted_text = repo.get_book_text(1, 'EPUB')
            
            # Verify fix: No ZIP headers, contains actual content
            assert 'PK' not in extracted_text[:10], "ZIP header should not be present"
            assert 'Test content for verification' in extracted_text, "Should contain actual text content"
            assert len(extracted_text) < 100, "Should be just the text, not raw file data"
            
            print(f"SUCCESS: EPUB extraction working correctly. Extracted: '{extracted_text}'")
                
        finally:
            os.unlink(epub_path)
    
    def test_chunk_count_issue(self):
        """
        Test that text extraction affects chunk count.
        600-page book should create more than 38 chunks.
        """
        # Create a larger EPUB with multiple chapters
        chapters = []
        for i in range(20):  # Simulate 20 chapters
            chapter_html = f'''<html><body>
                <h1>Chapter {i+1}</h1>
                <p>{'Lorem ipsum dolor sit amet. ' * 100}</p>
                <p>{'Consectetur adipiscing elit. ' * 100}</p>
                <p>{'Sed do eiusmod tempor incididunt. ' * 100}</p>
            </body></html>'''
            chapters.append(chapter_html)
        
        # Create EPUB with all chapters
        full_content = '<html><body>' + ''.join(chapters) + '</body></html>'
        epub_path = self.create_test_epub(full_content)
        
        try:
            # Mock Calibre database
            mock_calibre_db = Mock()
            mock_calibre_db.formats.return_value = ['EPUB']
            mock_calibre_db.format_abspath.return_value = epub_path
            
            # Create repository
            repo = CalibreRepository(mock_calibre_db)
            
            # Extract text
            extracted_text = repo.get_book_text(1, 'EPUB')
            
            # Calculate expected chunks (assuming ~500 chars per chunk)
            expected_min_chunks = len(extracted_text) // 500
            
            # For a 600-page book, we expect significantly more than 38 chunks
            assert expected_min_chunks > 50, f"Large book should create >50 chunks, not {expected_min_chunks}"
            
        finally:
            os.unlink(epub_path)


if __name__ == "__main__":
    # Run the test to see it fail
    pytest.main([__file__, "-v"])