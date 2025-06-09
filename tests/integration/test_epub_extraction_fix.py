"""
Test to verify EPUB extraction works correctly

This test verifies that:
1. EPUB files are properly extracted as text (not binary)
2. The extracted text is properly indexed
3. Search results contain actual text, not ZIP headers
"""

import pytest
import tempfile
import zipfile
import os
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

# Direct import to avoid Calibre dependencies
import sys
plugin_path = Path(__file__).parent.parent.parent / "calibre_plugins" / "semantic_search"
sys.path.insert(0, str(plugin_path))

from data.repositories import CalibreRepository
from core.indexing_service import IndexingService
from core.text_processor import TextProcessor
from core.embedding_service import MockProvider
from data.database import SemanticSearchDB


class TestEPUBExtractionFix:
    """Test that EPUB extraction properly extracts text"""
    
    def create_test_epub(self, content_html: str, filename: str = None) -> str:
        """Create a minimal EPUB file for testing"""
        # Create a temporary EPUB file
        if filename:
            tmp_file = filename
        else:
            tmp = tempfile.NamedTemporaryFile(suffix='.epub', delete=False)
            tmp_file = tmp.name
            tmp.close()
            
        with zipfile.ZipFile(tmp_file, 'w') as epub:
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
        <dc:title xmlns:dc="http://purl.org/dc/elements/1.1/">Being and Time</dc:title>
        <dc:creator xmlns:dc="http://purl.org/dc/elements/1.1/">Martin Heidegger</dc:creator>
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
            
        return tmp_file
    
    def test_epub_text_extraction(self):
        """Test that EPUB files are extracted as text, not binary data"""
        # Create test EPUB with philosophical content
        test_content = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>Chapter 1: The Question of Being</title>
</head>
<body>
    <h1>Chapter 1: The Question of Being</h1>
    <p>The question of Being has today been forgotten. Even though in our time we deem it progressive to give our approval to 'metaphysics' again, it is held that we have been exempted from the exertions of a newly rekindled gigantomachy peri tes ousias.</p>
    <p>Yet the question we are touching upon is not just any question. It is one which provided a stimulus for the researches of Plato and Aristotle, only to subside from then on as a theme for actual investigation.</p>
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
            
            # Verify extraction worked correctly
            assert extracted_text is not None
            assert len(extracted_text) > 0
            
            # Should NOT contain ZIP headers or binary data
            assert 'PK\x03\x04' not in extracted_text
            assert 'PK' not in extracted_text[:10]  # No ZIP header at start
            assert 'mimetypeapplication/epub+zip' not in extracted_text
            
            # Should contain actual philosophical content
            assert 'The question of Being' in extracted_text
            assert 'metaphysics' in extracted_text
            assert 'Plato and Aristotle' in extracted_text
            
            # Should NOT contain HTML tags
            assert '<html>' not in extracted_text
            assert '<body>' not in extracted_text
            assert '<p>' not in extracted_text
            
            print(f"SUCCESS: Extracted {len(extracted_text)} characters of clean text")
            print(f"First 200 chars: {extracted_text[:200]}")
            
        finally:
            os.unlink(epub_path)
    
    @pytest.mark.asyncio
    async def test_indexing_with_epub(self):
        """Test full indexing workflow with EPUB file"""
        # Create test EPUB
        content = '''<html><body>
            <h1>Introduction to Phenomenology</h1>
            <p>Phenomenology is the philosophical study of the structures of experience and consciousness.</p>
            <p>As a philosophical movement it was founded in the early years of the 20th century by Edmund Husserl.</p>
        </body></html>'''
        
        epub_path = self.create_test_epub(content, '/tmp/test_phenom.epub')
        
        try:
            # Set up test database
            with tempfile.TemporaryDirectory() as tmpdir:
                db_path = os.path.join(tmpdir, 'test_embeddings.db')
                
                # Create repositories - Use real embedding repository
                from data.repositories import EmbeddingRepository
                embedding_repo = EmbeddingRepository(db_path)
                
                # Mock Calibre repository
                mock_calibre_db = Mock()
                mock_calibre_db.formats.return_value = ['EPUB']
                mock_calibre_db.format_abspath.return_value = epub_path
                mock_calibre_db.get_metadata.return_value = Mock(
                    title="Introduction to Phenomenology",
                    authors=["Edmund Husserl"],
                    tags=["philosophy", "phenomenology"],
                    series=None,
                    series_index=None,
                    pubdate=None,
                    language="en",
                    format_metadata={'EPUB': {}},
                    identifiers={},
                    comments="",
                    publisher=""
                )
                
                calibre_repo = CalibreRepository(mock_calibre_db)
                
                # Create services
                text_processor = TextProcessor()
                embedding_service = MockProvider()
                
                indexing_service = IndexingService(
                    embedding_repo=embedding_repo,
                    calibre_repo=calibre_repo,
                    embedding_service=embedding_service,
                    text_processor=text_processor
                )
                
                # Index the book
                result = await indexing_service.index_books([1])
                
                # Verify indexing worked
                assert result['successful_books'] == 1
                assert result['failed_books'] == 0
                assert result['total_chunks'] > 0
                
                # Check what was stored
                chunks = embedding_repo.db._conn.execute(
                    "SELECT chunk_text FROM chunks WHERE book_id = 1"
                ).fetchall()
                
                assert len(chunks) > 0
                
                # Verify chunks contain actual text, not binary data
                for chunk in chunks:
                    chunk_text = chunk['chunk_text']
                    assert 'PK' not in chunk_text[:10]
                    assert 'Phenomenology' in chunk_text or 'Edmund Husserl' in chunk_text
                    
                print(f"SUCCESS: Indexed {len(chunks)} chunks with clean text")
                
        finally:
            if os.path.exists(epub_path):
                os.unlink(epub_path)


if __name__ == "__main__":
    # Run the tests
    test = TestEPUBExtractionFix()
    
    # Test 1: Basic extraction
    print("Testing EPUB text extraction...")
    test.test_epub_text_extraction()
    
    # Test 2: Full indexing
    print("\nTesting full indexing workflow...")
    asyncio.run(test.test_indexing_with_epub())
    
    print("\nAll tests passed!")