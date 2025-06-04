"""
SQLite database with sqlite-vec extension for vector storage
"""

import json
import logging
import os
import sqlite3
import struct
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Use pure Python vector operations instead of numpy
from calibre_plugins.semantic_search.core.vector_ops import VectorOps

logger = logging.getLogger(__name__)


class SemanticSearchDB:
    """SQLite database for semantic search with vector support"""

    # Schema version for migrations
    SCHEMA_VERSION = 1

    def __init__(self, db_path: Path):
        """
        Initialize database

        Args:
            db_path: Path to database file
        """
        print(f"[SemanticSearchDB] Initializing with path: {db_path}")
        self.db_path = Path(db_path)
        print(f"[SemanticSearchDB] Resolved path: {self.db_path}")
        print(f"[SemanticSearchDB] File exists: {self.db_path.exists()}")
        
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"[SemanticSearchDB] Parent directory: {self.db_path.parent}")

        # Thread-local storage for connections
        self._local = threading.local()

        # Initialize database
        print("[SemanticSearchDB] Calling _init_database()")
        try:
            self._init_database()
            print("[SemanticSearchDB] Database initialization complete")
        except Exception as e:
            print(f"[SemanticSearchDB] ERROR: Database init failed: {e}")
            import traceback
            print(traceback.format_exc())
            raise

    @property
    def _conn(self) -> sqlite3.Connection:
        """Get thread-local connection"""
        if not hasattr(self._local, "conn"):
            self._local.conn = self._create_connection()
        return self._local.conn

    def _create_connection(self) -> sqlite3.Connection:
        """Create a new database connection"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row

        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")

        # Load sqlite-vec extension
        try:
            # Try to load sqlite-vec
            # Path may vary based on platform and installation
            vec_paths = [
                "sqlite-vec",  # System installed
                "./lib/sqlite-vec.so",  # Linux
                "./lib/sqlite-vec.dll",  # Windows
                "./lib/sqlite-vec.dylib",  # macOS
                os.path.join(os.path.dirname(__file__), "../lib/sqlite-vec.so"),
            ]

            conn.enable_load_extension(True)

            loaded = False
            for vec_path in vec_paths:
                try:
                    conn.load_extension(vec_path)
                    loaded = True
                    logger.info(f"Loaded sqlite-vec from: {vec_path}")
                    break
                except Exception:
                    continue

            if not loaded:
                logger.warning(
                    "sqlite-vec extension not found. Vector search will be limited."
                )

        except Exception as e:
            logger.warning(f"Could not load sqlite-vec: {e}")

        return conn

    @contextmanager
    def transaction(self):
        """Context manager for transactions"""
        conn = self._conn
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def _init_database(self):
        """Initialize database schema"""
        print("[SemanticSearchDB] Starting _init_database()")
        try:
            with self.transaction() as conn:
                print("[SemanticSearchDB] Got database connection")
                # Check if we need to create or migrate schema
                current_version = self._get_schema_version(conn)
                print(f"[SemanticSearchDB] Current schema version: {current_version}")

                if current_version == 0:
                    print("[SemanticSearchDB] Creating new database schema")
                    self._create_schema(conn)
                elif current_version < self.SCHEMA_VERSION:
                    print(f"[SemanticSearchDB] Migrating schema from {current_version} to {self.SCHEMA_VERSION}")
                    self._migrate_schema(conn, current_version)
                else:
                    print("[SemanticSearchDB] Database schema is up to date")
        except Exception as e:
            print(f"[SemanticSearchDB] ERROR in _init_database: {e}")
            import traceback
            print(traceback.format_exc())
            raise

    def _get_schema_version(self, conn: sqlite3.Connection) -> int:
        """Get current schema version"""
        try:
            result = conn.execute("SELECT version FROM schema_version").fetchone()
            return result[0] if result else 0
        except sqlite3.OperationalError:
            return 0

    def _create_schema(self, conn: sqlite3.Connection):
        """Create initial database schema"""
        print("[SemanticSearchDB] _create_schema() called")
        
        try:
            # Schema version tracking
            print("[SemanticSearchDB] Creating schema_version table")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY
                )
            """
            )
            print("[SemanticSearchDB] schema_version table created")

            # Books tracking table
            print("[SemanticSearchDB] Creating books table")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS books (
                    book_id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    authors TEXT,  -- JSON array
                    tags TEXT,     -- JSON array
                    language TEXT,
                    pubdate TEXT,
                    last_indexed TIMESTAMP,
                    embedding_model TEXT,
                    chunk_count INTEGER DEFAULT 0,
                    metadata TEXT  -- JSON
                )
            """
            )
            print("[SemanticSearchDB] books table created")

            # Indexes table for multiple embedding indexes per book
            print("[SemanticSearchDB] Creating indexes table")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS indexes (
                    index_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    book_id INTEGER NOT NULL,
                    provider TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    dimensions INTEGER NOT NULL,
                    chunk_size INTEGER NOT NULL,
                    chunk_overlap INTEGER DEFAULT 0,
                    total_chunks INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,  -- JSON field for extra settings
                    FOREIGN KEY (book_id) REFERENCES books(book_id) ON DELETE CASCADE,
                    UNIQUE(book_id, provider, model_name, dimensions, chunk_size, chunk_overlap)
                )
            """
            )
            print("[SemanticSearchDB] indexes table created")

            # Chunks table
            logger.info("Creating chunks table")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chunks (
                    chunk_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    book_id INTEGER NOT NULL,
                    index_id INTEGER NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    chunk_text TEXT NOT NULL,
                    start_pos INTEGER,
                    end_pos INTEGER,
                    metadata TEXT,  -- JSON
                    FOREIGN KEY (book_id) REFERENCES books(book_id) ON DELETE CASCADE,
                    FOREIGN KEY (index_id) REFERENCES indexes(index_id) ON DELETE CASCADE,
                    UNIQUE(index_id, chunk_index)
                )
            """
            )

            # Try to create vector table with sqlite-vec
            try:
                # Get embedding dimensions from somewhere (default 768)
                dimensions = 768

                conn.execute(
                    f"""
                    CREATE VIRTUAL TABLE IF NOT EXISTS vec_embeddings 
                    USING vec0(
                        chunk_id INTEGER,
                        index_id INTEGER,
                        embedding FLOAT[{dimensions}]
                    )
                """
                )
                logger.info("Created vec0 virtual table for embeddings")

            except sqlite3.OperationalError:
                # Fallback to regular table if vec0 not available
                logger.warning("vec0 not available, using fallback embedding storage")
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS embeddings (
                        chunk_id INTEGER,
                        index_id INTEGER NOT NULL,
                        embedding BLOB NOT NULL,
                        PRIMARY KEY (chunk_id, index_id),
                        FOREIGN KEY (chunk_id) REFERENCES chunks(chunk_id) ON DELETE CASCADE,
                        FOREIGN KEY (index_id) REFERENCES indexes(index_id) ON DELETE CASCADE
                    )
                """
                )

            # Search cache table
            logger.info("Creating search_cache table")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS search_cache (
                    query_hash TEXT PRIMARY KEY,
                    query_text TEXT NOT NULL,
                    embedding BLOB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Indexing status table
            logger.info("Creating indexing_status table")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS indexing_status (
                    book_id INTEGER PRIMARY KEY,
                    status TEXT NOT NULL,  -- 'pending', 'indexing', 'completed', 'error'
                    progress REAL DEFAULT 0.0,
                    error_message TEXT,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    FOREIGN KEY (book_id) REFERENCES books(book_id) ON DELETE CASCADE
                )
            """
            )

            # Create indices
            logger.info("Creating database indexes")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_book ON chunks(book_id)")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_books_indexed ON books(last_indexed)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_cache_created ON search_cache(created_at)"
            )

            # Set schema version
            conn.execute(
                "INSERT INTO schema_version (version) VALUES (?)", (self.SCHEMA_VERSION,)
            )

            # Verify tables were created
            tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            table_names = [table[0] for table in tables]
            logger.info(f"Created tables: {table_names}")
            
            if 'indexes' not in table_names:
                raise Exception("Critical: indexes table was not created!")
                
            logger.info("Database schema created successfully")
            
        except Exception as e:
            logger.error(f"Error creating database schema: {e}")
            raise

    def _migrate_schema(self, conn: sqlite3.Connection, from_version: int):
        """Migrate schema to current version"""
        logger.info(
            f"Migrating schema from version {from_version} to {self.SCHEMA_VERSION}"
        )

        # Add migration logic here as schema evolves

        # Update version
        conn.execute("UPDATE schema_version SET version = ?", (self.SCHEMA_VERSION,))

    def store_embedding(
        self, book_id: int, chunk: "Chunk", embedding: List[float]
    ) -> int:
        """
        Store a chunk and its embedding

        Args:
            book_id: Book ID
            chunk: Chunk object
            embedding: Embedding vector

        Returns:
            chunk_id
        """
        with self.transaction() as conn:
            # Insert or update book
            conn.execute(
                """
                INSERT OR IGNORE INTO books (book_id, title, authors, tags)
                VALUES (?, ?, ?, ?)
            """,
                (
                    book_id,
                    chunk.metadata.get("title", "Unknown"),
                    json.dumps(chunk.metadata.get("authors", [])),
                    json.dumps(chunk.metadata.get("tags", [])),
                ),
            )

            # Insert chunk
            cursor = conn.execute(
                """
                INSERT OR REPLACE INTO chunks 
                (book_id, chunk_index, chunk_text, start_pos, end_pos, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    book_id,
                    chunk.index,
                    chunk.text,
                    chunk.start_pos,
                    chunk.end_pos,
                    json.dumps(chunk.metadata),
                ),
            )

            chunk_id = cursor.lastrowid

            # Store embedding
            try:
                # Try vec0 table first
                conn.execute(
                    """
                    INSERT OR REPLACE INTO vec_embeddings (chunk_id, embedding)
                    VALUES (?, ?)
                """,
                    (chunk_id, VectorOps.pack_embedding(embedding)),
                )

            except sqlite3.OperationalError:
                # Fallback to blob storage
                conn.execute(
                    """
                    INSERT OR REPLACE INTO embeddings (chunk_id, embedding)
                    VALUES (?, ?)
                """,
                    (chunk_id, VectorOps.pack_embedding(embedding)),
                )

            # Update book chunk count
            conn.execute(
                """
                UPDATE books 
                SET chunk_count = (SELECT COUNT(*) FROM chunks WHERE book_id = ?),
                    last_indexed = CURRENT_TIMESTAMP
                WHERE book_id = ?
            """,
                (book_id, book_id),
            )

            return chunk_id

    def get_embedding(self, chunk_id: int) -> Optional[List[float]]:
        """Get embedding for a chunk"""
        try:
            # Try vec0 table first
            result = self._conn.execute(
                """
                SELECT embedding FROM vec_embeddings WHERE chunk_id = ?
            """,
                (chunk_id,),
            ).fetchone()

        except sqlite3.OperationalError:
            # Fallback to blob storage
            result = self._conn.execute(
                """
                SELECT embedding FROM embeddings WHERE chunk_id = ?
            """,
                (chunk_id,),
            ).fetchone()

        if result:
            # Convert blob back to list of floats
            # Assuming 4 bytes per float (float32)
            dimension = len(result[0]) // 4
            return VectorOps.unpack_embedding(result[0], dimension)

        return None

    def search_similar(
        self,
        embedding: List[float],
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar embeddings

        Args:
            embedding: Query embedding
            limit: Maximum results
            filters: Optional filters

        Returns:
            List of results with similarity scores
        """
        filters = filters or {}

        # Build filter conditions
        conditions = []
        params = []

        if "book_ids" in filters:
            placeholders = ",".join("?" * len(filters["book_ids"]))
            conditions.append(f"c.book_id IN ({placeholders})")
            params.extend(filters["book_ids"])

        if "excluded_book_ids" in filters:
            placeholders = ",".join("?" * len(filters["excluded_book_ids"]))
            conditions.append(f"c.book_id NOT IN ({placeholders})")
            params.extend(filters["excluded_book_ids"])

        if "author" in filters:
            conditions.append("b.authors LIKE ?")
            params.append(f'%{filters["author"]}%')

        if "tags" in filters:
            # Check if any tag matches
            tag_conditions = []
            for tag in filters["tags"]:
                tag_conditions.append("b.tags LIKE ?")
                params.append(f"%{tag}%")
            conditions.append(f"({' OR '.join(tag_conditions)})")

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        # Try vector search with vec0
        try:
            query = f"""
                SELECT 
                    c.chunk_id,
                    c.book_id,
                    c.chunk_text,
                    c.chunk_index,
                    c.metadata as chunk_metadata,
                    b.title,
                    b.authors,
                    b.metadata as book_metadata,
                    vec_distance(e.embedding, ?) as distance
                FROM vec_embeddings e
                JOIN chunks c ON e.chunk_id = c.chunk_id
                JOIN books b ON c.book_id = b.book_id
                WHERE {where_clause}
                ORDER BY distance ASC
                LIMIT ?
            """

            results = self._conn.execute(
                query, [VectorOps.pack_embedding(embedding)] + params + [limit]
            ).fetchall()

        except sqlite3.OperationalError:
            # Fallback to manual similarity calculation
            results = self._search_similar_fallback(embedding, limit, filters)

        # Convert to result format
        output = []
        for row in results:
            # Convert distance to similarity (1 - normalized_distance)
            # Assuming cosine distance in range [0, 2]
            similarity = (
                1.0 - (row["distance"] / 2.0)
                if "distance" in row
                else row.get("similarity", 0)
            )

            output.append(
                {
                    "chunk_id": row["chunk_id"],
                    "book_id": row["book_id"],
                    "chunk_text": row["chunk_text"],
                    "chunk_index": row["chunk_index"],
                    "title": row["title"],
                    "authors": json.loads(row["authors"]) if row["authors"] else [],
                    "similarity": similarity,
                    "metadata": (
                        json.loads(row["chunk_metadata"])
                        if row["chunk_metadata"]
                        else {}
                    ),
                }
            )

        return output

    def _search_similar_fallback(
        self, embedding: List[float], limit: int, filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Fallback similarity search without vec0"""
        # This is much slower but works without the extension

        # Get all embeddings matching filters
        conditions = []
        params = []

        if "book_ids" in filters:
            placeholders = ",".join("?" * len(filters["book_ids"]))
            conditions.append(f"c.book_id IN ({placeholders})")
            params.extend(filters["book_ids"])

        if "excluded_book_ids" in filters:
            placeholders = ",".join("?" * len(filters["excluded_book_ids"]))
            conditions.append(f"c.book_id NOT IN ({placeholders})")
            params.extend(filters["excluded_book_ids"])

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        query = f"""
            SELECT 
                c.chunk_id,
                c.book_id,
                c.chunk_text,
                c.chunk_index,
                c.metadata as chunk_metadata,
                b.title,
                b.authors,
                b.metadata as book_metadata,
                e.embedding
            FROM embeddings e
            JOIN chunks c ON e.chunk_id = c.chunk_id
            JOIN books b ON c.book_id = b.book_id
            WHERE {where_clause}
        """

        rows = self._conn.execute(query, params).fetchall()

        # Calculate similarities
        results = []
        query_norm = VectorOps.normalize(embedding)

        for row in rows:
            # Unpack stored embedding
            dimension = len(row["embedding"]) // 4  # 4 bytes per float32
            stored_embedding = VectorOps.unpack_embedding(row["embedding"], dimension)
            
            # Cosine similarity
            similarity = VectorOps.cosine_similarity(query_norm, stored_embedding)

            # Parse authors JSON string
            try:
                authors = json.loads(row["authors"]) if row["authors"] else []
            except (json.JSONDecodeError, TypeError):
                authors = []
            
            results.append(
                {
                    "chunk_id": row["chunk_id"],
                    "book_id": row["book_id"],
                    "chunk_text": row["chunk_text"],
                    "chunk_index": row["chunk_index"],
                    "chunk_metadata": row["chunk_metadata"],
                    "title": row["title"],
                    "authors": authors,
                    "book_metadata": row["book_metadata"],
                    "similarity": float(similarity),
                }
            )

        # Sort by similarity and limit
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:limit]

    def get_chunk(self, chunk_id: int) -> Optional[Dict[str, Any]]:
        """Get chunk data including embedding"""
        row = self._conn.execute(
            """
            SELECT 
                c.*,
                b.title,
                b.authors
            FROM chunks c
            JOIN books b ON c.book_id = b.book_id
            WHERE c.chunk_id = ?
        """,
            (chunk_id,),
        ).fetchone()

        if not row:
            return None

        # Get embedding
        embedding = self.get_embedding(chunk_id)

        return {
            "chunk_id": row["chunk_id"],
            "book_id": row["book_id"],
            "chunk_text": row["chunk_text"],
            "chunk_index": row["chunk_index"],
            "title": row["title"],
            "authors": json.loads(row["authors"]) if row["authors"] else [],
            "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
            "embedding": embedding,
        }

    def get_indexing_status(
        self, book_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get indexing status for books"""
        if book_id:
            query = """
                SELECT * FROM indexing_status WHERE book_id = ?
            """
            params = (book_id,)
        else:
            query = """
                SELECT * FROM indexing_status ORDER BY started_at DESC
            """
            params = ()

        rows = self._conn.execute(query, params).fetchall()

        return [dict(row) for row in rows]

    def update_indexing_status(
        self,
        book_id: int,
        status: str,
        progress: float = 0.0,
        error: Optional[str] = None,
    ):
        """Update indexing status for a book"""
        with self.transaction() as conn:
            # Ensure book exists in books table before updating status
            # (Foreign key constraint requires book_id to exist in books table)
            conn.execute(
                """
                INSERT OR IGNORE INTO books (book_id, title, authors, tags)
                VALUES (?, ?, ?, ?)
                """,
                (book_id, "Unknown", "[]", "[]")
            )
            
            if status == "indexing":
                conn.execute(
                    """
                    INSERT OR REPLACE INTO indexing_status 
                    (book_id, status, progress, started_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """,
                    (book_id, status, progress),
                )

            elif status == "completed":
                conn.execute(
                    """
                    UPDATE indexing_status 
                    SET status = ?, progress = 1.0, completed_at = CURRENT_TIMESTAMP
                    WHERE book_id = ?
                """,
                    (status, book_id),
                )

            elif status == "error":
                conn.execute(
                    """
                    UPDATE indexing_status 
                    SET status = ?, error_message = ?
                    WHERE book_id = ?
                """,
                    (status, error, book_id),
                )

            else:
                conn.execute(
                    """
                    UPDATE indexing_status 
                    SET status = ?, progress = ?
                    WHERE book_id = ?
                """,
                    (status, progress, book_id),
                )

    def clear_book_embeddings(self, book_id: int):
        """Clear all embeddings for a book"""
        with self.transaction() as conn:
            # Get chunk IDs
            chunk_ids = [
                row[0]
                for row in conn.execute(
                    "SELECT chunk_id FROM chunks WHERE book_id = ?", (book_id,)
                ).fetchall()
            ]

            if chunk_ids:
                placeholders = ",".join("?" * len(chunk_ids))

                # Delete from embeddings
                try:
                    conn.execute(
                        f"DELETE FROM vec_embeddings WHERE chunk_id IN ({placeholders})",
                        chunk_ids,
                    )
                except sqlite3.OperationalError:
                    conn.execute(
                        f"DELETE FROM embeddings WHERE chunk_id IN ({placeholders})",
                        chunk_ids,
                    )

            # Delete chunks
            conn.execute("DELETE FROM chunks WHERE book_id = ?", (book_id,))

            # Update book
            conn.execute(
                """
                UPDATE books SET chunk_count = 0, last_indexed = NULL 
                WHERE book_id = ?
            """,
                (book_id,),
            )

    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        stats = {}

        # Book statistics
        stats["total_books"] = self._conn.execute(
            "SELECT COUNT(*) FROM books"
        ).fetchone()[0]

        stats["indexed_books"] = self._conn.execute(
            "SELECT COUNT(*) FROM books WHERE last_indexed IS NOT NULL"
        ).fetchone()[0]

        # Chunk statistics
        stats["total_chunks"] = self._conn.execute(
            "SELECT COUNT(*) FROM chunks"
        ).fetchone()[0]

        # Database size
        stats["database_size"] = (
            os.path.getsize(self.db_path) if self.db_path.exists() else 0
        )

        return stats

    def clear_all(self):
        """Clear all data from the database"""
        with self.transaction() as conn:
            # Delete all embeddings
            try:
                conn.execute("DELETE FROM vec_embeddings")
            except sqlite3.OperationalError:
                conn.execute("DELETE FROM embeddings")
            
            # Delete all chunks
            conn.execute("DELETE FROM chunks")
            
            # Delete all indexing status
            conn.execute("DELETE FROM indexing_status")
            
            # Delete all books
            conn.execute("DELETE FROM books")
            
            # Reset SQLite sequence counters
            conn.execute("DELETE FROM sqlite_sequence")
        
        # Vacuum outside transaction to reclaim space
        conn = self._create_connection()
        try:
            conn.execute("VACUUM")
        finally:
            conn.close()

    def force_create_tables(self):
        """Force creation of all tables - for debugging"""
        print("[SemanticSearchDB] FORCE creating all tables")
        try:
            conn = self._conn
            
            # Create all tables without checking if they exist
            print("[SemanticSearchDB] Force creating indexes table...")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS indexes (
                    index_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    book_id INTEGER NOT NULL,
                    provider TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    dimensions INTEGER NOT NULL,
                    chunk_size INTEGER NOT NULL,
                    chunk_overlap INTEGER DEFAULT 0,
                    total_chunks INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """)
            conn.commit()
            print("[SemanticSearchDB] indexes table force-created")
            
            # Verify it was created
            tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='indexes'").fetchall()
            print(f"[SemanticSearchDB] indexes table exists: {len(tables) > 0}")
            
        except Exception as e:
            print(f"[SemanticSearchDB] ERROR in force_create_tables: {e}")
            import traceback
            print(traceback.format_exc())
    
    def verify_schema(self) -> Dict[str, Any]:
        """Verify database schema and return status"""
        try:
            conn = self._conn
            
            # Check tables exist
            tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            table_names = [table[0] for table in tables]
            
            # Check schema version
            try:
                version = conn.execute("SELECT version FROM schema_version").fetchone()
                schema_version = version[0] if version else 0
            except sqlite3.OperationalError:
                schema_version = 0
            
            return {
                'schema_version': schema_version,
                'expected_version': self.SCHEMA_VERSION,
                'tables': table_names,
                'indexes_table_exists': 'indexes' in table_names,
                'books_table_exists': 'books' in table_names,
                'chunks_table_exists': 'chunks' in table_names,
                'db_path': str(self.db_path),
                'db_exists': self.db_path.exists()
            }
        except Exception as e:
            return {
                'error': str(e),
                'db_path': str(self.db_path),
                'db_exists': self.db_path.exists()
            }

    def close(self):
        """Close database connection"""
        if hasattr(self._local, "conn"):
            self._local.conn.close()
            delattr(self._local, "conn")
