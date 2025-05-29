"""
Unit tests for text processing and chunking
"""

import pytest
import sys
from pathlib import Path

# Direct import without going through plugin __init__.py
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "calibre_plugins" / "semantic_search"))

from core.text_processor import (
    TextProcessor, Chunk, ParagraphChunker, SlidingWindowChunker, 
    PhilosophicalChunker
)


class TestChunk:
    """Test the Chunk dataclass"""
    
    def test_chunk_creation(self):
        """Test creating a chunk"""
        chunk = Chunk(
            text="This is a test chunk",
            index=0,
            book_id=1,
            start_pos=0,
            end_pos=20,
            metadata={'chapter': 1}
        )
        
        assert chunk.text == "This is a test chunk"
        assert chunk.index == 0
        assert chunk.book_id == 1
        assert chunk.metadata['chapter'] == 1
        
    def test_token_count_approximation(self):
        """Test token count approximation"""
        chunk = Chunk(
            text="This is a test chunk with several words",
            index=0,
            book_id=1,
            start_pos=0,
            end_pos=40,
            metadata={}
        )
        
        # Should be approximately word count * 1.3
        word_count = len(chunk.text.split())
        expected = int(word_count * 1.3)
        assert chunk.token_count == expected


class TestParagraphChunker:
    """Test paragraph-based chunking"""
    
    def test_simple_paragraphs(self):
        """Test chunking simple paragraphs"""
        text = """First paragraph here.

Second paragraph here.

Third paragraph here."""
        
        chunker = ParagraphChunker(min_size=5, max_size=50)
        chunks = chunker.chunk(text, {'book_id': 1})
        
        assert len(chunks) == 3
        assert chunks[0].text == "First paragraph here."
        assert chunks[1].text == "Second paragraph here."
        assert chunks[2].text == "Third paragraph here."
        
    def test_paragraph_merging(self):
        """Test merging small paragraphs"""
        text = """Short one.

Another short.

This is a longer paragraph that contains more words and should be kept separate.

Final short."""
        
        chunker = ParagraphChunker(min_size=10, max_size=50)
        chunks = chunker.chunk(text, {'book_id': 1})
        
        # Short paragraphs should be merged
        assert len(chunks) == 2
        assert "Short one" in chunks[0].text
        assert "Another short" in chunks[0].text
        
    def test_large_paragraph_splitting(self):
        """Test splitting large paragraphs"""
        # Create a large paragraph
        large_para = " ".join(["word"] * 100)
        text = f"Small intro.\n\n{large_para}\n\nSmall outro."
        
        chunker = ParagraphChunker(min_size=10, max_size=50)
        chunks = chunker.chunk(text, {'book_id': 1})
        
        # Large paragraph should be split
        assert len(chunks) > 3
        
    def test_chunk_metadata(self):
        """Test chunk metadata is preserved"""
        text = "Test paragraph."
        metadata = {'book_id': 42, 'chapter': 'Introduction'}
        
        chunker = ParagraphChunker()
        chunks = chunker.chunk(text, metadata)
        
        assert chunks[0].book_id == 42
        assert chunks[0].metadata['chapter'] == 'Introduction'
        assert chunks[0].metadata['type'] == 'paragraph'


class TestSlidingWindowChunker:
    """Test sliding window chunking"""
    
    def test_sliding_window(self):
        """Test basic sliding window operation"""
        text = " ".join([f"word{i}" for i in range(20)])
        
        chunker = SlidingWindowChunker(window_size=5, overlap=2)
        chunks = chunker.chunk(text, {'book_id': 1})
        
        # Check first chunk
        assert chunks[0].text == "word0 word1 word2 word3 word4"
        
        # Check overlap
        assert chunks[1].text == "word3 word4 word5 word6 word7"
        
    def test_no_overlap(self):
        """Test sliding window with no overlap"""
        text = " ".join([f"word{i}" for i in range(10)])
        
        chunker = SlidingWindowChunker(window_size=5, overlap=0)
        chunks = chunker.chunk(text, {'book_id': 1})
        
        assert len(chunks) == 2
        assert chunks[0].text == "word0 word1 word2 word3 word4"
        assert chunks[1].text == "word5 word6 word7 word8 word9"


class TestPhilosophicalChunker:
    """Test philosophy-aware chunking"""
    
    def test_preserve_argument(self):
        """Test preserving philosophical arguments"""
        text = """Let us consider the nature of being. First, we must acknowledge 
that existence precedes essence. Second, this existence is fundamentally 
free. Therefore, we are condemned to be free."""
        
        chunker = PhilosophicalChunker(max_size=100)
        chunks = chunker.chunk(text, {'book_id': 1})
        
        # Argument should be kept together
        assert len(chunks) == 1
        assert "First" in chunks[0].text
        assert "Therefore" in chunks[0].text
        assert chunks[0].metadata['type'] == 'argument'
        
    def test_split_long_argument(self):
        """Test splitting long arguments carefully"""
        text = """First, let us establish that """ + " ".join(["premise"] * 50) + """
Therefore, we can conclude that """ + " ".join(["conclusion"] * 50)
        
        chunker = PhilosophicalChunker(max_size=60)
        chunks = chunker.chunk(text, {'book_id': 1})
        
        # Should split but preserve structure
        assert len(chunks) > 1
        assert any("Therefore" in chunk.text for chunk in chunks)
        
    def test_section_detection(self):
        """Test detecting sections"""
        text = """Chapter 1: Introduction

Some introductory text here.

Section 2. Main Arguments

The main philosophical arguments go here.

§3. Conclusions

Final thoughts and conclusions."""
        
        chunker = PhilosophicalChunker()
        sections = chunker._identify_sections(text)
        
        assert len(sections) >= 3
        assert any("Chapter 1" in s[2] for s in sections)
        assert any("Section 2" in s[2] for s in sections)
        
    def test_overlap_addition(self):
        """Test adding overlap between chunks"""
        text = """First chunk content here.

Second chunk content here.

Third chunk content here."""
        
        chunker = PhilosophicalChunker(overlap=3)
        chunks = chunker.chunk(text, {'book_id': 1})
        
        if len(chunks) > 1:
            # Middle chunks should have overlap markers
            assert "[...]" in chunks[1].text


class TestTextProcessor:
    """Test the main TextProcessor class"""
    
    def test_strategy_selection(self):
        """Test selecting different strategies"""
        processor = TextProcessor(strategy='paragraph')
        assert isinstance(processor.strategy, ParagraphChunker)
        
        processor = TextProcessor(strategy='sliding_window')
        assert isinstance(processor.strategy, SlidingWindowChunker)
        
        processor = TextProcessor(strategy='philosophical')
        assert isinstance(processor.strategy, PhilosophicalChunker)
        
    def test_chunk_text_basic(self, sample_text):
        """Test basic text chunking"""
        processor = TextProcessor()
        chunks = processor.chunk_text(sample_text, metadata={'book_id': 1})
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, Chunk) for chunk in chunks)
        assert all(chunk.text.strip() for chunk in chunks)
        
    def test_chunk_cleaning(self):
        """Test chunk cleaning"""
        text = """Valid chunk here.

        

Too    many     spaces     here.


Very short.

Another valid chunk with enough words to be meaningful."""
        
        processor = TextProcessor()
        chunks = processor.chunk_text(text)
        
        # Should remove empty chunks and clean whitespace
        assert len(chunks) == 2
        assert "Too many spaces here" in chunks[0].text
        assert "Another valid chunk" in chunks[1].text
        
    def test_extract_quotes(self):
        """Test quote extraction"""
        text = """Heidegger writes: "Language is the house of being. In its home 
human beings dwell. Those who think and those who create with words are 
the guardians of this home."

A short quote: "Too short"

Another philosopher said: "The unexamined life is not worth living, for 
it would be a life without reflection, without philosophy." """
        
        processor = TextProcessor()
        quotes = processor.extract_quotes(text)
        
        assert len(quotes) == 2  # Only long quotes
        assert "Language is the house" in quotes[0]['text']
        assert "unexamined life" in quotes[1]['text']
        
    def test_extract_citations(self):
        """Test citation extraction"""
        text = """As Kant argues (Kant 1781, p. 123), the categories of understanding
are a priori. This view was later challenged by Hegel (1807). See also 
Heidegger 1927 for a phenomenological approach. Recent work [42] has 
expanded on these ideas."""
        
        processor = TextProcessor()
        citations = processor.extract_citations(text)
        
        assert len(citations) >= 4
        assert any("Kant 1781" in c['reference'] for c in citations)
        assert any("42" in c['reference'] for c in citations)
        
    def test_strategy_override(self):
        """Test overriding strategy per call"""
        processor = TextProcessor(strategy='paragraph')
        
        text = " ".join([f"word{i}" for i in range(20)])
        
        # Use sliding window despite default
        chunks = processor.chunk_text(text, strategy='sliding_window')
        
        # Should have overlap characteristic of sliding window
        assert len(chunks) > 1