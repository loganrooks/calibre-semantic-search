"""
Integration test for EPUB text extraction with realistic book structure
"""

import pytest
import tempfile
import zipfile
import os
from pathlib import Path
from unittest.mock import Mock

# Add paths
import sys
plugin_path = Path(__file__).parent.parent.parent / "calibre_plugins" / "semantic_search"
sys.path.insert(0, str(plugin_path))

from data.repositories import CalibreRepository


class TestEPUBTextExtraction:
    """Integration tests for EPUB text extraction"""
    
    def create_realistic_epub(self) -> str:
        """Create a more realistic EPUB file with multiple chapters"""
        with tempfile.NamedTemporaryFile(suffix='.epub', delete=False) as tmp:
            with zipfile.ZipFile(tmp.name, 'w') as epub:
                # Add mimetype (must be first and uncompressed)
                epub.writestr('mimetype', 'application/epub+zip', compress_type=zipfile.ZIP_STORED)
                
                # Add container.xml
                container_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
    <rootfiles>
        <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
    </rootfiles>
</container>'''
                epub.writestr('META-INF/container.xml', container_xml)
                
                # Add content.opf
                content_opf = '''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="2.0" unique-identifier="uuid">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:title>Philosophy of Mind: A Comprehensive Guide</dc:title>
        <dc:creator>Dr. Jane Smith</dc:creator>
        <dc:language>en</dc:language>
    </metadata>
    <manifest>
        <item id="toc" href="toc.html" media-type="application/xhtml+xml"/>
        <item id="chapter1" href="chapter1.html" media-type="application/xhtml+xml"/>
        <item id="chapter2" href="chapter2.html" media-type="application/xhtml+xml"/>
        <item id="chapter3" href="chapter3.html" media-type="application/xhtml+xml"/>
    </manifest>
    <spine>
        <itemref idref="toc"/>
        <itemref idref="chapter1"/>
        <itemref idref="chapter2"/>
        <itemref idref="chapter3"/>
    </spine>
</package>'''
                epub.writestr('OEBPS/content.opf', content_opf)
                
                # Add table of contents
                toc_html = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>Table of Contents</title>
</head>
<body>
    <h1>Table of Contents</h1>
    <ul>
        <li><a href="chapter1.html">Chapter 1: Introduction to Philosophy of Mind</a></li>
        <li><a href="chapter2.html">Chapter 2: The Mind-Body Problem</a></li>
        <li><a href="chapter3.html">Chapter 3: Consciousness and Qualia</a></li>
    </ul>
</body>
</html>'''
                epub.writestr('OEBPS/toc.html', toc_html)
                
                # Add Chapter 1
                chapter1_html = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>Chapter 1: Introduction to Philosophy of Mind</title>
    <style type="text/css">
        body { font-family: serif; margin: 2em; }
        h1 { color: #333; }
    </style>
</head>
<body>
    <h1>Chapter 1: Introduction to Philosophy of Mind</h1>
    <p>The philosophy of mind is a branch of philosophy that studies the nature of the mind, 
    mental events, mental functions, mental properties, consciousness, and their relationship 
    to the physical body, particularly the brain.</p>
    
    <p>One of the central questions in philosophy of mind is the mind-body problem: 
    what is the relationship between mental states and physical states? This question has 
    puzzled philosophers for centuries and remains one of the most debated topics in 
    contemporary philosophy.</p>
    
    <h2>Historical Background</h2>
    <p>The modern discussion of the mind-body problem can be traced back to René Descartes 
    in the 17th century. Descartes proposed substance dualism, arguing that the mind and 
    body are two distinct substances that interact with each other.</p>
</body>
</html>'''
                epub.writestr('OEBPS/chapter1.html', chapter1_html)
                
                # Add Chapter 2
                chapter2_html = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>Chapter 2: The Mind-Body Problem</title>
</head>
<body>
    <h1>Chapter 2: The Mind-Body Problem</h1>
    <p>The mind-body problem concerns the relationship between thought and consciousness 
    in the human mind, and the brain as part of the physical body. The problem revolves 
    around the question of whether the mind is distinct from the body.</p>
    
    <h2>Major Positions</h2>
    <p><strong>Dualism:</strong> The view that mind and body are distinct kinds of substances 
    or natures. This position faces the challenge of explaining how two distinct substances 
    can interact.</p>
    
    <p><strong>Physicalism:</strong> The view that everything is physical, or as contemporary 
    philosophers sometimes put it, that everything supervenes on the physical. This includes 
    various forms such as behaviorism, identity theory, and functionalism.</p>
    
    <script type="text/javascript">
        // This should be removed during extraction
        console.log("This is a script that should not appear in extracted text");
    </script>
</body>
</html>'''
                epub.writestr('OEBPS/chapter2.html', chapter2_html)
                
                # Add Chapter 3
                chapter3_html = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>Chapter 3: Consciousness and Qualia</title>
</head>
<body>
    <h1>Chapter 3: Consciousness and Qualia</h1>
    <p>Consciousness is perhaps the most puzzling aspect of the mind. David Chalmers 
    distinguished between the "easy problems" and the "hard problem" of consciousness.</p>
    
    <p>The easy problems of consciousness include explaining cognitive functions such as:</p>
    <ul>
        <li>The ability to discriminate, categorize, and react to environmental stimuli</li>
        <li>The integration of information by a cognitive system</li>
        <li>The reportability of mental states</li>
        <li>The focus of attention</li>
    </ul>
    
    <p>The hard problem of consciousness is the problem of explaining how and why we have 
    qualitative, subjective experiences—how sensations acquire characteristics such as 
    colors and tastes.</p>
    
    <p>&nbsp;&nbsp;&nbsp;&nbsp;Qualia are the subjective or qualitative properties of experiences. 
    What it is like to see red, taste coffee, or feel pain are all examples of qualia.</p>
</body>
</html>'''
                epub.writestr('OEBPS/chapter3.html', chapter3_html)
                
            return tmp.name
    
    def test_extract_text_from_realistic_epub(self):
        """Test extraction from a realistic multi-chapter EPUB"""
        epub_path = self.create_realistic_epub()
        
        try:
            # Mock Calibre database
            mock_calibre_db = Mock()
            mock_calibre_db.formats.return_value = ['EPUB']
            mock_calibre_db.format_abspath.return_value = epub_path
            
            # Create repository
            repo = CalibreRepository(mock_calibre_db)
            
            # Extract text
            extracted_text = repo.get_book_text(1, 'EPUB')
            
            # Verify extraction quality
            assert extracted_text is not None
            assert len(extracted_text) > 1000, "Should extract substantial text"
            
            # Check that all chapters are included
            assert 'Introduction to Philosophy of Mind' in extracted_text
            assert 'The Mind-Body Problem' in extracted_text
            assert 'Consciousness and Qualia' in extracted_text
            
            # Check specific content
            assert 'René Descartes' in extracted_text
            assert 'substance dualism' in extracted_text
            assert 'David Chalmers' in extracted_text
            assert 'hard problem' in extracted_text
            
            # Verify HTML tags are removed
            assert '<html>' not in extracted_text
            assert '<body>' not in extracted_text
            assert '<h1>' not in extracted_text
            assert '</p>' not in extracted_text
            
            # Verify scripts and styles are removed
            assert 'console.log' not in extracted_text
            assert 'font-family' not in extracted_text
            assert 'text/css' not in extracted_text
            
            # Verify entities are decoded
            assert '&nbsp;' not in extracted_text
            assert '&lt;' not in extracted_text
            assert '&gt;' not in extracted_text
            
            # Print sample for manual verification
            print(f"\nExtracted text length: {len(extracted_text)} characters")
            print(f"First 500 characters:\n{extracted_text[:500]}...")
            
        finally:
            os.unlink(epub_path)
    
    def test_extract_preserves_reading_order(self):
        """Test that text is extracted in proper reading order"""
        epub_path = self.create_realistic_epub()
        
        try:
            # Mock Calibre database
            mock_calibre_db = Mock()
            mock_calibre_db.formats.return_value = ['EPUB']
            mock_calibre_db.format_abspath.return_value = epub_path
            
            # Create repository
            repo = CalibreRepository(mock_calibre_db)
            
            # Extract text
            extracted_text = repo.get_book_text(1, 'EPUB')
            
            # Check order: Chapter 1 should come before Chapter 2
            ch1_pos = extracted_text.find('Introduction to Philosophy of Mind')
            ch2_pos = extracted_text.find('The Mind-Body Problem')
            ch3_pos = extracted_text.find('Consciousness and Qualia')
            
            assert ch1_pos < ch2_pos, "Chapter 1 should come before Chapter 2"
            assert ch2_pos < ch3_pos, "Chapter 2 should come before Chapter 3"
            
        finally:
            os.unlink(epub_path)
    
    def test_handles_corrupt_epub_gracefully(self):
        """Test that corrupt EPUB files are handled gracefully"""
        # Create a corrupt EPUB (not a valid ZIP)
        with tempfile.NamedTemporaryFile(suffix='.epub', delete=False) as tmp:
            tmp.write(b"This is not a valid EPUB/ZIP file")
            corrupt_path = tmp.name
        
        try:
            # Mock Calibre database
            mock_calibre_db = Mock()
            mock_calibre_db.formats.return_value = ['EPUB']
            mock_calibre_db.format_abspath.return_value = corrupt_path
            
            # Create repository
            repo = CalibreRepository(mock_calibre_db)
            
            # Should handle gracefully without crashing
            extracted_text = repo.get_book_text(1, 'EPUB')
            
            # Should return empty string for corrupt file
            assert extracted_text == ""
            
        finally:
            os.unlink(corrupt_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])