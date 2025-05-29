"""
Text processing and chunking for philosophical texts
"""

import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod


@dataclass
class Chunk:
    """Represents a text chunk with metadata"""
    text: str
    index: int
    book_id: int
    start_pos: int
    end_pos: int
    metadata: Dict[str, any]
    
    @property
    def token_count(self) -> int:
        """Approximate token count (rough estimate)"""
        return len(self.text.split()) * 1.3  # Rough approximation


class ChunkingStrategy(ABC):
    """Abstract base class for chunking strategies"""
    
    @abstractmethod
    def chunk(self, text: str, metadata: Dict) -> List[Chunk]:
        """Split text into chunks"""
        pass


class ParagraphChunker(ChunkingStrategy):
    """Chunk text by paragraphs"""
    
    def __init__(self, min_size: int = 100, max_size: int = 512):
        self.min_size = min_size
        self.max_size = max_size
        
    def chunk(self, text: str, metadata: Dict) -> List[Chunk]:
        """Split text into paragraph-based chunks"""
        # Split by double newlines (paragraphs)
        paragraphs = re.split(r'\n\s*\n', text)
        
        chunks = []
        current_chunk = []
        current_size = 0
        chunk_index = 0
        current_pos = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
                
            para_size = len(para.split())
            
            # If paragraph is too large, split it
            if para_size > self.max_size:
                # Flush current chunk
                if current_chunk:
                    chunk_text = '\n\n'.join(current_chunk)
                    chunks.append(Chunk(
                        text=chunk_text,
                        index=chunk_index,
                        book_id=metadata.get('book_id', 0),
                        start_pos=current_pos,
                        end_pos=current_pos + len(chunk_text),
                        metadata={**metadata, 'type': 'paragraph'}
                    ))
                    chunk_index += 1
                    current_pos += len(chunk_text) + 2
                    current_chunk = []
                    current_size = 0
                
                # Split large paragraph by sentences
                sentences = re.split(r'(?<=[.!?])\s+', para)
                for sentence in sentences:
                    chunks.append(Chunk(
                        text=sentence,
                        index=chunk_index,
                        book_id=metadata.get('book_id', 0),
                        start_pos=current_pos,
                        end_pos=current_pos + len(sentence),
                        metadata={**metadata, 'type': 'sentence'}
                    ))
                    chunk_index += 1
                    current_pos += len(sentence) + 1
                    
            # If adding paragraph exceeds max size, start new chunk
            elif current_size + para_size > self.max_size and current_chunk:
                chunk_text = '\n\n'.join(current_chunk)
                chunks.append(Chunk(
                    text=chunk_text,
                    index=chunk_index,
                    book_id=metadata.get('book_id', 0),
                    start_pos=current_pos,
                    end_pos=current_pos + len(chunk_text),
                    metadata={**metadata, 'type': 'paragraph'}
                ))
                chunk_index += 1
                current_pos += len(chunk_text) + 2
                current_chunk = [para]
                current_size = para_size
                
            else:
                # Add to current chunk
                current_chunk.append(para)
                current_size += para_size
                
        # Don't forget the last chunk
        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            chunks.append(Chunk(
                text=chunk_text,
                index=chunk_index,
                book_id=metadata.get('book_id', 0),
                start_pos=current_pos,
                end_pos=current_pos + len(chunk_text),
                metadata={**metadata, 'type': 'paragraph'}
            ))
            
        return chunks


class SlidingWindowChunker(ChunkingStrategy):
    """Fixed-size sliding window chunker"""
    
    def __init__(self, window_size: int = 512, overlap: int = 128):
        self.window_size = window_size
        self.overlap = overlap
        
    def chunk(self, text: str, metadata: Dict) -> List[Chunk]:
        """Split text using sliding window"""
        words = text.split()
        chunks = []
        chunk_index = 0
        
        stride = self.window_size - self.overlap
        
        for i in range(0, len(words), stride):
            chunk_words = words[i:i + self.window_size]
            chunk_text = ' '.join(chunk_words)
            
            # Calculate positions (approximate)
            start_pos = len(' '.join(words[:i]))
            end_pos = start_pos + len(chunk_text)
            
            chunks.append(Chunk(
                text=chunk_text,
                index=chunk_index,
                book_id=metadata.get('book_id', 0),
                start_pos=start_pos,
                end_pos=end_pos,
                metadata={**metadata, 'type': 'sliding_window'}
            ))
            chunk_index += 1
            
            # Stop if we've processed all words
            if i + self.window_size >= len(words):
                break
                
        return chunks


class PhilosophicalChunker(ChunkingStrategy):
    """Philosophy-aware chunking that preserves arguments and concepts"""
    
    def __init__(self, min_size: int = 100, max_size: int = 512, overlap: int = 50):
        self.min_size = min_size
        self.max_size = max_size
        self.overlap = overlap
        
        # Patterns for philosophical text structures
        self.argument_markers = [
            r'(?:First|Second|Third|Finally|Therefore|Thus|Hence|Consequently)',
            r'(?:premise|conclusion|follows that|it follows|we can conclude)',
            r'(?:on the one hand|on the other hand|however|nevertheless|but)',
            r'(?:let us consider|suppose that|imagine|for example|for instance)',
        ]
        
        self.section_markers = [
            r'^\s*(?:Chapter|Section|Part|§)\s*\d+',
            r'^\s*\d+\.\s+\w+',  # Numbered sections
            r'^\s*[IVXLCDM]+\.\s+\w+',  # Roman numerals
        ]
        
    def chunk(self, text: str, metadata: Dict) -> List[Chunk]:
        """Split text while preserving philosophical structure"""
        # First, identify major sections
        sections = self._identify_sections(text)
        
        chunks = []
        chunk_index = 0
        
        for section_start, section_end, section_text in sections:
            # Check for arguments within section
            if self._contains_argument(section_text):
                # Keep argument together if possible
                if len(section_text.split()) <= self.max_size:
                    chunks.append(Chunk(
                        text=section_text,
                        index=chunk_index,
                        book_id=metadata.get('book_id', 0),
                        start_pos=section_start,
                        end_pos=section_end,
                        metadata={**metadata, 'type': 'argument', 'preserved': True}
                    ))
                    chunk_index += 1
                else:
                    # Split carefully to preserve argument structure
                    arg_chunks = self._split_argument(section_text, section_start, metadata)
                    for chunk in arg_chunks:
                        chunk.index = chunk_index
                        chunks.append(chunk)
                        chunk_index += 1
            else:
                # Use paragraph chunking for non-argument text
                para_chunker = ParagraphChunker(self.min_size, self.max_size)
                para_chunks = para_chunker.chunk(section_text, metadata)
                
                for chunk in para_chunks:
                    chunk.index = chunk_index
                    chunk.start_pos += section_start
                    chunk.end_pos += section_start
                    chunks.append(chunk)
                    chunk_index += 1
                    
        # Add overlap between chunks for context
        chunks = self._add_overlap(chunks)
        
        return chunks
        
    def _identify_sections(self, text: str) -> List[Tuple[int, int, str]]:
        """Identify logical sections in the text"""
        sections = []
        
        # Find section markers
        section_positions = []
        for pattern in self.section_markers:
            for match in re.finditer(pattern, text, re.MULTILINE):
                section_positions.append(match.start())
                
        # Sort positions
        section_positions = sorted(set(section_positions))
        
        # If no sections found, treat whole text as one section
        if not section_positions:
            return [(0, len(text), text)]
            
        # Create sections
        for i, start in enumerate(section_positions):
            end = section_positions[i + 1] if i + 1 < len(section_positions) else len(text)
            sections.append((start, end, text[start:end]))
            
        # Don't forget content before first section
        if section_positions[0] > 0:
            sections.insert(0, (0, section_positions[0], text[:section_positions[0]]))
            
        return sections
        
    def _contains_argument(self, text: str) -> bool:
        """Check if text contains philosophical argument markers"""
        for pattern in self.argument_markers:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
        
    def _split_argument(self, text: str, start_pos: int, metadata: Dict) -> List[Chunk]:
        """Carefully split an argument while preserving structure"""
        chunks = []
        
        # Try to split by premise/conclusion markers
        parts = re.split(r'(Therefore|Thus|Hence|Consequently)', text, flags=re.IGNORECASE)
        
        current_text = ""
        for i, part in enumerate(parts):
            if i % 2 == 1:  # This is a marker
                current_text += part
            else:
                if current_text and len((current_text + part).split()) > self.max_size:
                    # Create chunk
                    chunks.append(Chunk(
                        text=current_text.strip(),
                        index=0,  # Will be set by caller
                        book_id=metadata.get('book_id', 0),
                        start_pos=start_pos,
                        end_pos=start_pos + len(current_text),
                        metadata={**metadata, 'type': 'argument_part'}
                    ))
                    start_pos += len(current_text)
                    current_text = part
                else:
                    current_text += part
                    
        # Don't forget the last part
        if current_text.strip():
            chunks.append(Chunk(
                text=current_text.strip(),
                index=0,
                book_id=metadata.get('book_id', 0),
                start_pos=start_pos,
                end_pos=start_pos + len(current_text),
                metadata={**metadata, 'type': 'argument_part'}
            ))
            
        return chunks
        
    def _add_overlap(self, chunks: List[Chunk]) -> List[Chunk]:
        """Add overlap between chunks for context preservation"""
        if len(chunks) <= 1:
            return chunks
            
        overlapped_chunks = []
        
        for i, chunk in enumerate(chunks):
            if i == 0:
                # First chunk - add from next
                if i + 1 < len(chunks):
                    next_words = chunks[i + 1].text.split()[:self.overlap]
                    chunk.text += "\n[...]\n" + ' '.join(next_words)
            elif i == len(chunks) - 1:
                # Last chunk - add from previous
                prev_words = chunks[i - 1].text.split()[-self.overlap:]
                chunk.text = ' '.join(prev_words) + "\n[...]\n" + chunk.text
            else:
                # Middle chunks - add from both
                prev_words = chunks[i - 1].text.split()[-self.overlap//2:]
                next_words = chunks[i + 1].text.split()[:self.overlap//2]
                chunk.text = (' '.join(prev_words) + "\n[...]\n" + 
                             chunk.text + "\n[...]\n" + ' '.join(next_words))
                
            overlapped_chunks.append(chunk)
            
        return overlapped_chunks


class TextProcessor:
    """Main text processing class"""
    
    def __init__(self, strategy: str = 'philosophical'):
        self.strategies = {
            'paragraph': ParagraphChunker(),
            'sliding_window': SlidingWindowChunker(),
            'philosophical': PhilosophicalChunker(),
            'semantic': PhilosophicalChunker(),  # Alias
            'hybrid': PhilosophicalChunker()     # Alias
        }
        self.strategy = self.strategies.get(strategy, PhilosophicalChunker())
        
    def chunk_text(self, text: str, strategy: Optional[str] = None, 
                   metadata: Optional[Dict] = None) -> List[Chunk]:
        """
        Split text into chunks based on strategy
        
        Args:
            text: Text to chunk
            strategy: Override default strategy
            metadata: Additional metadata to include in chunks
            
        Returns:
            List of Chunk objects
        """
        if strategy and strategy in self.strategies:
            chunker = self.strategies[strategy]
        else:
            chunker = self.strategy
            
        metadata = metadata or {}
        chunks = chunker.chunk(text, metadata)
        
        # Post-process chunks
        chunks = self._clean_chunks(chunks)
        chunks = self._validate_chunks(chunks)
        
        return chunks
        
    def _clean_chunks(self, chunks: List[Chunk]) -> List[Chunk]:
        """Clean and normalize chunks"""
        cleaned = []
        
        for chunk in chunks:
            # Remove excessive whitespace
            chunk.text = ' '.join(chunk.text.split())
            
            # Skip empty chunks
            if not chunk.text.strip():
                continue
                
            # Skip chunks that are too small
            if len(chunk.text.split()) < 20:  # Minimum 20 words
                continue
                
            cleaned.append(chunk)
            
        return cleaned
        
    def _validate_chunks(self, chunks: List[Chunk]) -> List[Chunk]:
        """Validate chunk quality"""
        # Ensure indices are sequential
        for i, chunk in enumerate(chunks):
            chunk.index = i
            
        return chunks
        
    def extract_quotes(self, text: str) -> List[Dict[str, any]]:
        """Extract philosophical quotes from text"""
        quotes = []
        
        # Pattern for quoted text
        quote_pattern = r'"([^"]{50,})"'  # Quotes longer than 50 chars
        
        for match in re.finditer(quote_pattern, text):
            quotes.append({
                'text': match.group(1),
                'start': match.start(),
                'end': match.end()
            })
            
        return quotes
        
    def extract_citations(self, text: str) -> List[Dict[str, any]]:
        """Extract citations and references"""
        citations = []
        
        # Common citation patterns
        patterns = [
            r'\(([A-Z][a-z]+(?:\s+and\s+[A-Z][a-z]+)?\s+\d{4}(?:,\s*p+\.?\s*\d+)?)\)',
            r'\[(\d+)\]',  # Numbered references
            r'(?:see|cf\.)\s+([A-Z][a-z]+\s+\d{4})',
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, text):
                citations.append({
                    'text': match.group(0),
                    'reference': match.group(1),
                    'start': match.start(),
                    'end': match.end()
                })
                
        return citations