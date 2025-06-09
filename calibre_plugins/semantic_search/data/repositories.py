"""
Repository pattern implementations for data access
"""

import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Use pure Python vector operations instead of numpy
from calibre_plugins.semantic_search.core.vector_ops import VectorOps

from calibre_plugins.semantic_search.core.text_processor import Chunk
from calibre_plugins.semantic_search.data.database import SemanticSearchDB

logger = logging.getLogger(__name__)


class IEmbeddingRepository(ABC):
    """Interface for embedding storage"""

    @abstractmethod
    async def store_embedding(
        self, book_id: int, chunk: Chunk, embedding: List[float]
    ) -> int:
        """Store embedding for a chunk"""
        pass

    @abstractmethod
    async def get_embeddings(self, book_id: int) -> List[Tuple[Chunk, List[float]]]:
        """Get all embeddings for a book"""
        pass

    @abstractmethod
    async def search_similar(
        self, embedding: List[float], limit: int, filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
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
        print(f"[EmbeddingRepository] Initializing with path: {db_path}")
        print(f"[EmbeddingRepository] Path type: {type(db_path)}")
        
        # Ensure we have a Path object
        if isinstance(db_path, str):
            db_path = Path(db_path)
            print(f"[EmbeddingRepository] Converted to Path: {db_path}")
            
        print("[EmbeddingRepository] Creating SemanticSearchDB...")
        self.db = SemanticSearchDB(db_path)
        print("[EmbeddingRepository] SemanticSearchDB created successfully")

    async def store_embedding(
        self, book_id: int, chunk: Chunk, embedding: List[float]
    ) -> int:
        """Store embedding for a chunk"""
        # Add book metadata to chunk if not present
        if "book_id" not in chunk.metadata:
            chunk.metadata["book_id"] = book_id

        # Find or create an appropriate index for this book
        # Use default parameters that match the embedding service
        dimensions = len(embedding)
        provider = "default"  # This should ideally come from the embedding service
        model_name = "default"
        
        # Check if an index already exists for this book with these parameters
        existing_indexes = self.get_indexes_for_book(book_id)
        index_id = None
        
        for idx in existing_indexes:
            if (idx['provider'] == provider and 
                idx['model_name'] == model_name and 
                idx['dimensions'] == dimensions):
                index_id = idx['index_id']
                break
        
        # Create new index if none exists
        if index_id is None:
            index_id = self.create_index(
                book_id=book_id,
                provider=provider,
                model_name=model_name,
                dimensions=dimensions,
                chunk_size=512,  # Default chunk size
                chunk_overlap=0
            )
        
        # Store using the index-aware method
        chunk_id = self.store_embedding_for_index(index_id, chunk, embedding)
        logger.debug(f"Stored embedding for chunk {chunk_id} of book {book_id} in index {index_id}")

        return chunk_id

    async def get_embeddings(self, book_id: int) -> List[Tuple[Chunk, List[float]]]:
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
                text=row["chunk_text"],
                index=row["chunk_index"],
                book_id=book_id,
                start_pos=row["start_pos"],
                end_pos=row["end_pos"],
                metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            )

            # Get embedding
            embedding = self.db.get_embedding(row["chunk_id"])

            if embedding is not None:
                results.append((chunk, embedding))

        return results

    async def search_similar(
        self,
        embedding: List[float],
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
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

    def update_indexing_status(
        self,
        book_id: int,
        status: str,
        progress: float = 0.0,
        error: Optional[str] = None,
    ):
        """Update indexing status"""
        self.db.update_indexing_status(book_id, status, progress, error)

    def get_indexing_status(
        self, book_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get indexing status"""
        return self.db.get_indexing_status(book_id)

    def create_index(
        self, 
        book_id: int, 
        provider: str, 
        model_name: str = "default", 
        dimensions: int = 768, 
        chunk_size: int = 512, 
        chunk_overlap: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """Create a new index for a book"""
        metadata_json = json.dumps(metadata or {})
        
        with self.db.transaction() as conn:
            # Ensure book exists before creating index (foreign key constraint)
            conn.execute(
                """
                INSERT OR IGNORE INTO books (book_id, title, authors, tags)
                VALUES (?, ?, ?, ?)
                """,
                (book_id, "Unknown", "[]", "[]")
            )
            
            # Create the index
            cursor = conn.execute(
                """
                INSERT INTO indexes (
                    book_id, provider, model_name, dimensions, 
                    chunk_size, chunk_overlap, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (book_id, provider, model_name, dimensions, chunk_size, chunk_overlap, metadata_json)
            )
            return cursor.lastrowid

    def get_indexes_for_book(self, book_id: int) -> List[Dict[str, Any]]:
        """Get all indexes for a book"""
        query = """
            SELECT 
                index_id, book_id, provider, model_name, dimensions,
                chunk_size, chunk_overlap, total_chunks, created_at, updated_at, metadata
            FROM indexes 
            WHERE book_id = ?
            ORDER BY created_at DESC
        """
        
        rows = self.db._conn.execute(query, (book_id,)).fetchall()
        
        indexes = []
        for row in rows:
            index_dict = {
                'index_id': row[0],
                'book_id': row[1], 
                'provider': row[2],
                'model_name': row[3],
                'dimensions': row[4],
                'chunk_size': row[5],
                'chunk_overlap': row[6],
                'total_chunks': row[7],
                'created_at': row[8],
                'updated_at': row[9],
                'metadata': json.loads(row[10]) if row[10] else {}
            }
            indexes.append(index_dict)
        
        return indexes

    def store_embedding_for_index(self, index_id: int, chunk: Chunk, embedding: List[float]) -> int:
        """Store chunk and embedding for a specific index"""
        # First store the chunk with the index_id
        chunk_query = """
            INSERT INTO chunks (
                book_id, index_id, chunk_index, chunk_text, 
                start_pos, end_pos, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        metadata_json = json.dumps(chunk.metadata or {})
        
        with self.db.transaction() as conn:
            # Store chunk
            cursor = conn.execute(
                chunk_query,
                (chunk.book_id, index_id, chunk.index, chunk.text, 
                 chunk.start_pos, chunk.end_pos, metadata_json)
            )
            chunk_id = cursor.lastrowid
            
            # Store embedding
            embedding_blob = VectorOps.pack_embedding(embedding)
            conn.execute(
                """
                INSERT INTO embeddings (chunk_id, index_id, embedding)
                VALUES (?, ?, ?)
                """,
                (chunk_id, index_id, embedding_blob)
            )
            
            return chunk_id

    def get_chunk_with_index(self, chunk_id: int) -> Optional[Dict[str, Any]]:
        """Get chunk information including index association"""
        query = """
            SELECT 
                c.chunk_id, c.book_id, c.index_id, c.chunk_index, c.chunk_text,
                c.start_pos, c.end_pos, c.metadata,
                i.provider, i.model_name, i.dimensions
            FROM chunks c
            JOIN indexes i ON c.index_id = i.index_id
            WHERE c.chunk_id = ?
        """
        
        row = self.db._conn.execute(query, (chunk_id,)).fetchone()
        if not row:
            return None
            
        return {
            'chunk_id': row[0],
            'book_id': row[1],
            'index_id': row[2],
            'chunk_index': row[3],
            'chunk_text': row[4],
            'start_pos': row[5],
            'end_pos': row[6],
            'metadata': json.loads(row[7]) if row[7] else {},
            'provider': row[8],
            'model_name': row[9],
            'dimensions': row[10]
        }

    def search_similar_in_index(self, index_id: int, query_embedding: List[float], limit: int = 10) -> List[Dict[str, Any]]:
        """Search for similar embeddings within a specific index"""
        query = """
            SELECT 
                c.chunk_id, c.book_id, c.index_id, c.chunk_index, c.chunk_text,
                c.start_pos, c.end_pos, c.metadata,
                e.embedding
            FROM chunks c
            JOIN embeddings e ON c.chunk_id = e.chunk_id
            WHERE c.index_id = ?
            LIMIT ?
        """
        
        rows = self.db._conn.execute(query, (index_id, limit)).fetchall()
        
        results = []
        for row in rows:
            # Unpack embedding and calculate similarity
            embedding_blob = row[8]
            stored_embedding = VectorOps.unpack_embedding(embedding_blob, len(query_embedding))
            similarity = VectorOps.cosine_similarity(query_embedding, stored_embedding)
            
            result = {
                'chunk_id': row[0],
                'book_id': row[1],
                'index_id': row[2],
                'chunk_index': row[3],
                'chunk_text': row[4],
                'start_pos': row[5],
                'end_pos': row[6],
                'metadata': json.loads(row[7]) if row[7] else {},
                'similarity': similarity
            }
            results.append(result)
        
        # Sort by similarity score (highest first)
        results.sort(key=lambda x: x['similarity'], reverse=True)
        
        return results

    def delete_index(self, index_id: int) -> bool:
        """Delete a specific index and all its associated chunks and embeddings"""
        with self.db.transaction() as conn:
            # Delete embeddings first (foreign key constraint)
            conn.execute("DELETE FROM embeddings WHERE index_id = ?", (index_id,))
            
            # Delete chunks associated with this index
            conn.execute("DELETE FROM chunks WHERE index_id = ?", (index_id,))
            
            # Delete the index itself
            cursor = conn.execute("DELETE FROM indexes WHERE index_id = ?", (index_id,))
            
            # Return True if index was deleted, False if it didn't exist
            return cursor.rowcount > 0

    def get_books_with_indexes(self) -> List[int]:
        """Get list of book IDs that have indexes"""
        try:
            # First try indexes table
            query = """
                SELECT DISTINCT book_id 
                FROM indexes 
                ORDER BY book_id
            """
            rows = self.db._conn.execute(query).fetchall()
            book_ids = [row[0] for row in rows]
            
            # If no results from indexes table, try books table
            if not book_ids:
                query = """
                    SELECT DISTINCT book_id 
                    FROM books 
                    ORDER BY book_id
                """
                rows = self.db._conn.execute(query).fetchall()
                book_ids = [row[0] for row in rows]
            
            return book_ids
            
        except Exception as e:
            logger.error(f"Error getting books with indexes: {e}")
            return []

    def get_index_statistics(self, index_id: int) -> Optional[Dict[str, Any]]:
        """Get statistics for a specific index"""
        # Get basic index info
        index_query = """
            SELECT 
                index_id, book_id, provider, model_name, dimensions,
                chunk_size, chunk_overlap, created_at, updated_at, metadata
            FROM indexes 
            WHERE index_id = ?
        """
        
        index_row = self.db._conn.execute(index_query, (index_id,)).fetchone()
        if not index_row:
            return None
        
        # Count chunks for this index
        chunk_count_query = "SELECT COUNT(*) FROM chunks WHERE index_id = ?"
        chunk_count = self.db._conn.execute(chunk_count_query, (index_id,)).fetchone()[0]
        
        # Calculate storage size (approximate)
        storage_query = """
            SELECT SUM(LENGTH(c.chunk_text) + LENGTH(e.embedding))
            FROM chunks c
            JOIN embeddings e ON c.chunk_id = e.chunk_id
            WHERE c.index_id = ?
        """
        storage_size = self.db._conn.execute(storage_query, (index_id,)).fetchone()[0] or 0
        
        return {
            'index_id': index_row[0],
            'book_id': index_row[1],
            'provider': index_row[2],
            'model_name': index_row[3],
            'dimensions': index_row[4],
            'chunk_size': index_row[5],
            'chunk_overlap': index_row[6],
            'created_at': index_row[7],
            'updated_at': index_row[8],
            'metadata': json.loads(index_row[9]) if index_row[9] else {},
            'total_chunks': chunk_count,
            'storage_size': storage_size
        }

    def get_indexes_by_provider(self, provider: str) -> List[Dict[str, Any]]:
        """Get all indexes for a specific provider"""
        query = """
            SELECT 
                index_id, book_id, provider, model_name, dimensions,
                chunk_size, chunk_overlap, total_chunks, created_at, updated_at, metadata
            FROM indexes 
            WHERE provider = ?
            ORDER BY created_at DESC
        """
        
        rows = self.db._conn.execute(query, (provider,)).fetchall()
        
        indexes = []
        for row in rows:
            index_dict = {
                'index_id': row[0],
                'book_id': row[1], 
                'provider': row[2],
                'model_name': row[3],
                'dimensions': row[4],
                'chunk_size': row[5],
                'chunk_overlap': row[6],
                'total_chunks': row[7],
                'created_at': row[8],
                'updated_at': row[9],
                'metadata': json.loads(row[10]) if row[10] else {}
            }
            indexes.append(index_dict)
        
        return indexes

    def search_across_indexes(self, indexes: List[Dict[str, Any]], query_embedding: List[float], limit: int = 10) -> List[Dict[str, Any]]:
        """Search for similar embeddings across multiple indexes"""
        all_results = []
        
        for index_info in indexes:
            index_id = index_info['index_id']
            # Get results from this index
            index_results = self.search_similar_in_index(index_id, query_embedding, limit)
            all_results.extend(index_results)
        
        # Sort all results by similarity and limit
        all_results.sort(key=lambda x: x['similarity'], reverse=True)
        return all_results[:limit]


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
                "id": book_id,
                "title": mi.title,
                "authors": mi.authors if mi.authors else [],
                "tags": list(mi.tags) if mi.tags else [],
                "series": mi.series,
                "series_index": mi.series_index,
                "pubdate": mi.pubdate.isoformat() if mi.pubdate else None,
                "language": mi.language,
                "formats": (
                    list(mi.format_metadata.keys()) if mi.format_metadata else []
                ),
                "identifiers": dict(mi.identifiers) if mi.identifiers else {},
                "comments": mi.comments,
                "publisher": mi.publisher,
            }
        except Exception as e:
            logger.error(f"Error getting metadata for book {book_id}: {e}")
            return {
                "id": book_id,
                "title": f"Book {book_id}",
                "authors": [],
                "tags": [],
                "formats": [],
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
                format_preference = ["EPUB", "AZW3", "MOBI", "PDF", "TXT", "HTML"]
                selected_format = next(
                    (fmt for fmt in format_preference if fmt in formats), formats[0]
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

    def _validate_extracted_text(self, text: str, format: str) -> tuple:
        """
        Validate that extracted text is actually text, not binary data
        
        Returns:
            (is_valid, cleaned_text)
        """
        if not text:
            return False, ""
            
        # Check for common binary signatures at the start
        if text.startswith('PK\x03\x04') or text.startswith('PK\x05\x06'):
            logger.error(f"Text contains ZIP header - {format} file was read as binary!")
            return False, ""
            
        # Check if text has reasonable amount of printable characters
        sample = text[:1000]  # Check first 1000 chars
        printable_chars = sum(1 for c in sample if c.isprintable() or c.isspace())
        
        if len(sample) > 0 and printable_chars / len(sample) < 0.8:
            logger.warning(f"Text from {format} appears to contain too many non-printable characters")
            return False, ""
        
        return True, text

    def _extract_text_from_file(self, path: str, format: str) -> str:
        """Extract text from book file"""
        try:
            if format == "TXT":
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
                    is_valid, _ = self._validate_extracted_text(text, format)
                    return text if is_valid else ""

            elif format == "EPUB":
                # EPUB files are ZIP archives containing HTML/XHTML files
                try:
                    import zipfile
                    import re
                    
                    # First, verify it's a valid ZIP file
                    if not zipfile.is_zipfile(path):
                        logger.error(f"Invalid EPUB file (not a ZIP): {path}")
                        return ""
                    
                    text_parts = []
                    
                    with zipfile.ZipFile(path, 'r') as epub:
                        # Get all files in the EPUB
                        for filename in epub.namelist():
                            # Extract text from HTML/XHTML files
                            if filename.endswith(('.html', '.xhtml', '.htm')):
                                try:
                                    content = epub.read(filename).decode('utf-8', errors='ignore')
                                    
                                    # Remove HTML tags
                                    content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL)
                                    content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
                                    content = re.sub(r'<[^>]+>', ' ', content)
                                    
                                    # Clean up entities and whitespace
                                    content = content.replace('&nbsp;', ' ')
                                    content = content.replace('&lt;', '<')
                                    content = content.replace('&gt;', '>')
                                    content = content.replace('&amp;', '&')
                                    content = re.sub(r'\s+', ' ', content)
                                    
                                    text_parts.append(content.strip())
                                except Exception as e:
                                    logger.debug(f"Could not extract text from {filename}: {e}")
                    
                    # Combine all text parts
                    combined_text = ' '.join(text_parts)
                    
                    # Validate the extracted text
                    is_valid, validated_text = self._validate_extracted_text(combined_text.strip(), format)
                    if not is_valid:
                        logger.error(f"EPUB text extraction failed validation for {path}")
                        return ""
                    
                    return validated_text
                    
                except Exception as e:
                    logger.warning(f"Failed to extract text from EPUB: {e}")
                    return ""
                    
            elif format in ["AZW3", "MOBI"]:
                # For AZW3/MOBI, try Calibre's conversion tools if available
                try:
                    # Try to use Calibre's ebook conversion
                    from calibre.ebooks.conversion.plumber import Plumber
                    from calibre.customize.conversion import DummyReporter
                    from io import BytesIO
                    
                    # Create a plumber instance
                    plumber = Plumber(path, 'txt', DummyReporter())
                    
                    # Extract text to a BytesIO object
                    output = BytesIO()
                    plumber.run()
                    
                    # Get the text content
                    text = output.getvalue().decode('utf-8', errors='ignore')
                    return text.strip()
                    
                except ImportError:
                    # Fallback to basic extraction if Calibre tools not available
                    logger.warning("Calibre conversion tools not available, using basic extraction")
                    try:
                        with open(path, "rb") as f:
                            data = f.read()
                        
                        # Try to decode as UTF-8 text (very basic, may not work well)
                        text = data.decode("utf-8", errors="ignore")
                        
                        # Do basic HTML tag removal if present
                        if "<" in text and ">" in text:
                            import re
                            text = re.sub(r'<[^>]+>', ' ', text)
                            text = re.sub(r'\s+', ' ', text)
                        
                        return text.strip()
                        
                    except Exception as e:
                        logger.warning(f"Failed to extract text from {format}: {e}")
                        return ""
                        
                except Exception as e:
                    logger.warning(f"Failed to extract text from {format}: {e}")
                    return ""

            elif format == "PDF":
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
            if "author" in filters:
                author_ids = set()
                for book_id in all_ids:
                    mi = self.db.get_metadata(book_id)
                    if any(
                        filters["author"].lower() in author.lower()
                        for author in (mi.authors or [])
                    ):
                        author_ids.add(book_id)
                all_ids &= author_ids

            if "tags" in filters:
                tag_ids = set()
                for book_id in all_ids:
                    mi = self.db.get_metadata(book_id)
                    book_tags = set(mi.tags) if mi.tags else set()
                    if any(tag in book_tags for tag in filters["tags"]):
                        tag_ids.add(book_id)
                all_ids &= tag_ids

            if "language" in filters:
                lang_ids = set()
                for book_id in all_ids:
                    mi = self.db.get_metadata(book_id)
                    if mi.language == filters["language"]:
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
            "id": book_id,
            "title": f"Mock Book {book_id}",
            "authors": ["Mock Author"],
            "tags": ["test"],
            "formats": ["EPUB"],
        }

    def get_book_text(self, book_id: int, format: Optional[str] = None) -> str:
        """Get book text"""
        if book_id in self.books:
            return self.books[book_id].get("text", f"Mock text for book {book_id}")
        return f"Mock text for book {book_id}"

    def get_books_by_filter(self, filters: Dict[str, Any]) -> List[int]:
        """Get filtered books"""
        results = []
        for book_id, book in self.books.items():
            if "author" in filters:
                if not any(
                    filters["author"].lower() in author.lower()
                    for author in book.get("authors", [])
                ):
                    continue
            if "tags" in filters:
                if not any(tag in book.get("tags", []) for tag in filters["tags"]):
                    continue
            results.append(book_id)
        return results

    def get_all_book_ids(self) -> List[int]:
        """Get all book IDs"""
        return list(self.books.keys())
