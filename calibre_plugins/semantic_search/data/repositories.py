"""
Repository pattern implementations for data access
"""

import json
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path
import numpy as np
from abc import ABC, abstractmethod
import logging

from calibre_plugins.semantic_search.data.database import SemanticSearchDB
from calibre_plugins.semantic_search.core.text_processor import Chunk

logger = logging.getLogger(__name__)


class IEmbeddingRepository(ABC):
    """Interface for embedding storage"""
    
    @abstractmethod
    async def store_embedding(self, book_id: int, chunk: Chunk, 
                            embedding: np.ndarray) -> int:
        """Store embedding for a chunk"""
        pass
        
    @abstractmethod
    async def get_embeddings(self, book_id: int) -> List[Tuple[Chunk, np.ndarray]]:
        """Get all embeddings for a book"""
        pass
        
    @abstractmethod
    async def search_similar(self, embedding: np.ndarray, limit: int,
                           filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for similar embeddings"""
        pass
        
    @abstractmethod
    async def delete_book_embeddings(self, book_id: int):
        """Delete all embeddings for a book"""
        pass


class ICalibreRepository(ABC):
    """Interface for Calibre database access"""
    
    @abstractmethod
    def get_book_metadata(self, book_id: int) -> Dict[str, Any]:
        """Get book metadata"""
        pass
        
    @abstractmethod
    def get_book_text(self, book_id: int, format: Optional[str] = None) -> str:
        """Get book text content"""
        pass
        
    @abstractmethod
    def get_books_by_filter(self, filters: Dict[str, Any]) -> List[int]:
        """Get book IDs matching filters"""
        pass
        
    @abstractmethod
    def get_all_book_ids(self) -> List[int]:
        """Get all book IDs in library"""
        pass


class EmbeddingRepository(IEmbeddingRepository):
    """SQLite-based embedding repository"""
    
    def __init__(self, db_path: Path):
        """
        Initialize repository
        
        Args:
            db_path: Path to database file
        """
        self.db = SemanticSearchDB(db_path)
        
    async def store_embedding(self, book_id: int, chunk: Chunk, 
                            embedding: np.ndarray) -> int:
        """Store embedding for a chunk"""
        # Add book metadata to chunk if not present
        if 'book_id' not in chunk.metadata:
            chunk.metadata['book_id'] = book_id
            
        chunk_id = self.db.store_embedding(book_id, chunk, embedding)
        logger.debug(f"Stored embedding for chunk {chunk_id} of book {book_id}")
        
        return chunk_id
        
    async def get_embeddings(self, book_id: int) -> List[Tuple[Chunk, np.ndarray]]:
        """Get all embeddings for a book"""
        query = """
            SELECT 
                c.chunk_id,
                c.chunk_index,
                c.chunk_text,
                c.start_pos,
                c.end_pos,
                c.metadata
            FROM chunks c
            WHERE c.book_id = ?
            ORDER BY c.chunk_index
        """
        
        rows = self.db._conn.execute(query, (book_id,)).fetchall()
        
        results = []
        for row in rows:
            # Reconstruct chunk
            chunk = Chunk(
                text=row['chunk_text'],
                index=row['chunk_index'],
                book_id=book_id,
                start_pos=row['start_pos'],
                end_pos=row['end_pos'],
                metadata=json.loads(row['metadata']) if row['metadata'] else {}
            )
            
            # Get embedding
            embedding = self.db.get_embedding(row['chunk_id'])
            
            if embedding is not None:
                results.append((chunk, embedding))
                
        return results
        
    async def search_similar(self, embedding: np.ndarray, limit: int = 20,
                           filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search for similar embeddings"""
        return self.db.search_similar(embedding, limit, filters)
        
    async def delete_book_embeddings(self, book_id: int):
        """Delete all embeddings for a book"""
        self.db.clear_book_embeddings(book_id)
        logger.info(f"Deleted embeddings for book {book_id}")
        
    async def get_chunk(self, chunk_id: int) -> Optional[Dict[str, Any]]:
        """Get chunk data"""
        return self.db.get_chunk(chunk_id)
        
    def get_statistics(self) -> Dict[str, Any]:
        """Get repository statistics"""
        return self.db.get_statistics()
        
    def update_indexing_status(self, book_id: int, status: str, 
                             progress: float = 0.0, error: Optional[str] = None):
        """Update indexing status"""
        self.db.update_indexing_status(book_id, status, progress, error)
        
    def get_indexing_status(self, book_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get indexing status"""
        return self.db.get_indexing_status(book_id)


class CalibreRepository(ICalibreRepository):
    """Repository for accessing Calibre database"""
    
    def __init__(self, calibre_db):
        """
        Initialize repository
        
        Args:
            calibre_db: Calibre database API instance
        """
        self.db = calibre_db
        
    def get_book_metadata(self, book_id: int) -> Dict[str, Any]:
        """Get book metadata"""
        try:
            mi = self.db.get_metadata(book_id)
            
            return {
                'id': book_id,
                'title': mi.title,
                'authors': mi.authors if mi.authors else [],
                'tags': list(mi.tags) if mi.tags else [],
                'series': mi.series,
                'series_index': mi.series_index,
                'pubdate': mi.pubdate.isoformat() if mi.pubdate else None,
                'language': mi.language,
                'formats': list(mi.format_metadata.keys()) if mi.format_metadata else [],
                'identifiers': dict(mi.identifiers) if mi.identifiers else {},
                'comments': mi.comments,
                'publisher': mi.publisher
            }
        except Exception as e:
            logger.error(f"Error getting metadata for book {book_id}: {e}")
            return {
                'id': book_id,
                'title': f'Book {book_id}',
                'authors': [],
                'tags': [],
                'formats': []
            }
            
    def get_book_text(self, book_id: int, format: Optional[str] = None) -> str:
        """
        Get book text content
        
        Args:
            book_id: Book ID
            format: Specific format to extract (None = auto-select)
            
        Returns:
            Extracted text
        """
        try:
            # Get available formats
            formats = self.db.formats(book_id)
            
            if not formats:
                logger.warning(f"No formats available for book {book_id}")
                return ""
                
            # Select format
            if format and format in formats:
                selected_format = format
            else:
                # Prefer formats in this order
                format_preference = ['EPUB', 'AZW3', 'MOBI', 'PDF', 'TXT', 'HTML']
                selected_format = next(
                    (fmt for fmt in format_preference if fmt in formats),
                    formats[0]
                )
                
            # Get path to book file
            path = self.db.format_abspath(book_id, selected_format)
            
            if not path or not Path(path).exists():
                logger.error(f"Book file not found: {path}")
                return ""
                
            # Extract text based on format
            return self._extract_text_from_file(path, selected_format)
            
        except Exception as e:
            logger.error(f"Error extracting text from book {book_id}: {e}")
            return ""
            
    def _extract_text_from_file(self, path: str, format: str) -> str:
        """Extract text from book file"""
        try:
            if format == 'TXT':
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
                    
            elif format in ['EPUB', 'AZW3', 'MOBI']:
                # Use Calibre's ebook conversion tools
                from calibre.ebooks.oeb.reader import OEBReader
                from calibre.ebooks.conversion.plumber import Plumber
                from io import BytesIO
                
                # This is a simplified version - real implementation would be more robust
                plumber = Plumber(path, 'txt', BytesIO())
                plumber.run()
                
                return plumber.output.getvalue().decode('utf-8', errors='ignore')
                
            elif format == 'PDF':
                # Use Calibre's PDF tools
                from calibre.ebooks.pdf.pdftohtml import pdftotext
                
                return pdftotext(path)
                
            else:
                logger.warning(f"Unsupported format for text extraction: {format}")
                return ""
                
        except Exception as e:
            logger.error(f"Error extracting text from {path}: {e}")
            return ""
            
    def get_books_by_filter(self, filters: Dict[str, Any]) -> List[int]:
        """Get book IDs matching filters"""
        try:
            # Start with all books
            all_ids = set(self.db.all_book_ids())
            
            # Apply filters
            if 'author' in filters:
                author_ids = set()
                for book_id in all_ids:
                    mi = self.db.get_metadata(book_id)
                    if any(filters['author'].lower() in author.lower() 
                          for author in (mi.authors or [])):
                        author_ids.add(book_id)
                all_ids &= author_ids
                
            if 'tags' in filters:
                tag_ids = set()
                for book_id in all_ids:
                    mi = self.db.get_metadata(book_id)
                    book_tags = set(mi.tags) if mi.tags else set()
                    if any(tag in book_tags for tag in filters['tags']):
                        tag_ids.add(book_id)
                all_ids &= tag_ids
                
            if 'language' in filters:
                lang_ids = set()
                for book_id in all_ids:
                    mi = self.db.get_metadata(book_id)
                    if mi.language == filters['language']:
                        lang_ids.add(book_id)
                all_ids &= lang_ids
                
            return list(all_ids)
            
        except Exception as e:
            logger.error(f"Error filtering books: {e}")
            return []
            
    def get_all_book_ids(self) -> List[int]:
        """Get all book IDs in library"""
        try:
            return list(self.db.all_book_ids())
        except Exception as e:
            logger.error(f"Error getting book IDs: {e}")
            return []
            
    def get_author_names(self) -> List[str]:
        """Get all author names in library"""
        try:
            return list(self.db.all_author_names())
        except Exception as e:
            logger.error(f"Error getting author names: {e}")
            return []
            
    def get_tag_names(self) -> List[str]:
        """Get all tag names in library"""
        try:
            return list(self.db.all_tag_names())
        except Exception as e:
            logger.error(f"Error getting tag names: {e}")
            return []


class MockCalibreRepository(ICalibreRepository):
    """Mock repository for testing"""
    
    def __init__(self, books: Optional[Dict[int, Dict[str, Any]]] = None):
        self.books = books or {}
        
    def get_book_metadata(self, book_id: int) -> Dict[str, Any]:
        """Get book metadata"""
        if book_id in self.books:
            return self.books[book_id]
        return {
            'id': book_id,
            'title': f'Mock Book {book_id}',
            'authors': ['Mock Author'],
            'tags': ['test'],
            'formats': ['EPUB']
        }
        
    def get_book_text(self, book_id: int, format: Optional[str] = None) -> str:
        """Get book text"""
        if book_id in self.books:
            return self.books[book_id].get('text', f'Mock text for book {book_id}')
        return f'Mock text for book {book_id}'
        
    def get_books_by_filter(self, filters: Dict[str, Any]) -> List[int]:
        """Get filtered books"""
        results = []
        for book_id, book in self.books.items():
            if 'author' in filters:
                if not any(filters['author'] in author 
                          for author in book.get('authors', [])):
                    continue
            if 'tags' in filters:
                if not any(tag in book.get('tags', []) 
                          for tag in filters['tags']):
                    continue
            results.append(book_id)
        return results
        
    def get_all_book_ids(self) -> List[int]:
        """Get all book IDs"""
        return list(self.books.keys())