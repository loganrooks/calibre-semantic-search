"""
Book indexing service for generating embeddings
"""

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from calibre_plugins.semantic_search.core.embedding_service import EmbeddingService
from calibre_plugins.semantic_search.core.text_processor import TextProcessor
from calibre_plugins.semantic_search.data.repositories import (
    CalibreRepository,
    EmbeddingRepository,
)

logger = logging.getLogger(__name__)


class IndexingService:
    """Service for indexing books and generating embeddings"""

    def __init__(
        self,
        text_processor: TextProcessor,
        embedding_service: EmbeddingService,
        embedding_repo: EmbeddingRepository,
        calibre_repo: CalibreRepository,
        batch_size: int = 100,
        max_concurrent: int = 3,
    ):
        """
        Initialize indexing service

        Args:
            text_processor: Text processing service
            embedding_service: Embedding generation service
            embedding_repo: Repository for storing embeddings
            calibre_repo: Repository for accessing Calibre data
            batch_size: Number of chunks to process in batch
            max_concurrent: Maximum concurrent embedding requests
        """
        self.text_processor = text_processor
        self.embedding_service = embedding_service
        self.embedding_repo = embedding_repo
        self.calibre_repo = calibre_repo
        self.batch_size = batch_size
        self.max_concurrent = max_concurrent

        # Progress tracking
        self._progress_callbacks = []
        self._cancel_requested = False

    def add_progress_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Add callback for progress updates"""
        self._progress_callbacks.append(callback)

    def remove_progress_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Remove progress callback"""
        if callback in self._progress_callbacks:
            self._progress_callbacks.remove(callback)

    def request_cancel(self):
        """Request cancellation of indexing"""
        self._cancel_requested = True

    def _report_progress(self, **kwargs):
        """Report progress to callbacks"""
        for callback in self._progress_callbacks:
            try:
                callback(kwargs)
            except Exception as e:
                logger.error(f"Progress callback error: {e}")

    async def index_books(
        self, book_ids: List[int], reindex: bool = False
    ) -> Dict[str, Any]:
        """
        Index multiple books

        Args:
            book_ids: List of book IDs to index
            reindex: Whether to reindex already indexed books

        Returns:
            Indexing statistics
        """
        logger.info(f"Starting indexing for {len(book_ids)} books")

        self._cancel_requested = False
        stats = {
            "total_books": len(book_ids),
            "processed_books": 0,
            "successful_books": 0,
            "failed_books": 0,
            "total_chunks": 0,
            "total_time": 0,
            "errors": [],
        }

        start_time = time.time()

        for i, book_id in enumerate(book_ids):
            if self._cancel_requested:
                logger.info("Indexing cancelled by user")
                break

            # Report progress
            self._report_progress(
                current_book=i + 1,
                total_books=len(book_ids),
                book_id=book_id,
                status="starting",
            )

            try:
                # Check if already indexed
                if not reindex:
                    existing = await self.embedding_repo.get_embeddings(book_id)
                    if existing:
                        logger.info(f"Book {book_id} already indexed, skipping")
                        stats["processed_books"] += 1
                        continue

                # Index the book
                result = await self.index_single_book(book_id)

                stats["processed_books"] += 1
                stats["successful_books"] += 1
                stats["total_chunks"] += result["chunk_count"]

                # Report success
                self._report_progress(
                    current_book=i + 1,
                    total_books=len(book_ids),
                    book_id=book_id,
                    status="completed",
                    chunks=result["chunk_count"],
                )

            except Exception as e:
                logger.error(f"Error indexing book {book_id}: {e}")
                stats["failed_books"] += 1
                stats["errors"].append({"book_id": book_id, "error": str(e)})

                # Report error
                self._report_progress(
                    current_book=i + 1,
                    total_books=len(book_ids),
                    book_id=book_id,
                    status="error",
                    error=str(e),
                )

                # Update indexing status
                self.embedding_repo.update_indexing_status(
                    book_id, "error", error=str(e)
                )

        stats["total_time"] = time.time() - start_time

        logger.info(
            f"Indexing complete: {stats['successful_books']} successful, "
            f"{stats['failed_books']} failed, {stats['total_chunks']} chunks, "
            f"{stats['total_time']:.1f}s"
        )

        return stats

    async def index_single_book(self, book_id: int) -> Dict[str, Any]:
        """
        Index a single book

        Args:
            book_id: Book ID to index

        Returns:
            Indexing result
        """
        logger.info(f"Indexing book {book_id}")

        # Update status
        self.embedding_repo.update_indexing_status(book_id, "indexing", 0.0)

        try:
            # Get book metadata
            metadata = self.calibre_repo.get_book_metadata(book_id)

            # Get book text
            book_text = self.calibre_repo.get_book_text(book_id)

            if not book_text:
                raise ValueError("No text content found in book")

            # Update progress - text extracted
            self.embedding_repo.update_indexing_status(book_id, "indexing", 0.1)

            # Chunk the text
            chunks = self.text_processor.chunk_text(
                book_text,
                metadata={
                    "book_id": book_id,
                    "title": metadata.get("title"),
                    "authors": metadata.get("authors", []),
                    "tags": metadata.get("tags", []),
                    "language": metadata.get("language"),
                    "pubdate": metadata.get("pubdate"),
                },
            )

            logger.info(f"Created {len(chunks)} chunks for book {book_id}")

            # Update progress - chunking complete
            self.embedding_repo.update_indexing_status(book_id, "indexing", 0.2)

            # Clear existing embeddings if any
            await self.embedding_repo.delete_book_embeddings(book_id)

            # Generate embeddings in batches
            total_chunks = len(chunks)
            processed_chunks = 0

            for batch_start in range(0, total_chunks, self.batch_size):
                if self._cancel_requested:
                    raise Exception("Indexing cancelled")

                batch_end = min(batch_start + self.batch_size, total_chunks)
                batch_chunks = chunks[batch_start:batch_end]

                # Extract texts for batch embedding
                batch_texts = [chunk.text for chunk in batch_chunks]

                # Generate embeddings
                embeddings = await self.embedding_service.generate_batch(batch_texts)

                # Store embeddings
                for chunk, embedding in zip(batch_chunks, embeddings):
                    await self.embedding_repo.store_embedding(book_id, chunk, embedding)

                processed_chunks += len(batch_chunks)

                # Update progress
                progress = 0.2 + (0.8 * processed_chunks / total_chunks)
                self.embedding_repo.update_indexing_status(
                    book_id, "indexing", progress
                )

            # Mark as completed
            self.embedding_repo.update_indexing_status(book_id, "completed", 1.0)

            return {"book_id": book_id, "chunk_count": len(chunks), "status": "success"}

        except Exception as e:
            logger.error(f"Error indexing book {book_id}: {e}")
            self.embedding_repo.update_indexing_status(book_id, "error", error=str(e))
            raise

    async def get_indexing_status(self) -> List[Dict[str, Any]]:
        """Get status of all indexing operations"""
        return self.embedding_repo.get_indexing_status()

    async def get_library_statistics(self) -> Dict[str, Any]:
        """Get statistics about the indexed library"""
        # Get basic stats from repository
        stats = self.embedding_repo.get_statistics()

        # Add Calibre library stats
        all_book_ids = self.calibre_repo.get_all_book_ids()
        stats["total_library_books"] = len(all_book_ids)
        stats["indexing_percentage"] = (
            (stats["indexed_books"] / stats["total_library_books"] * 100)
            if stats["total_library_books"] > 0
            else 0
        )

        return stats

    def estimate_indexing_time(self, book_count: int) -> float:
        """
        Estimate time to index books

        Args:
            book_count: Number of books to index

        Returns:
            Estimated time in seconds
        """
        # Rough estimates based on typical performance
        # Adjust based on actual measurements

        # Time per book depends on:
        # - Book size (assume average 300 pages = 100k words)
        # - Chunking time (~1 second)
        # - Embedding generation (~0.5 seconds per chunk)
        # - Network latency for API calls

        avg_chunks_per_book = 200  # Typical for 100k word book
        time_per_chunk = 0.5  # Including API call overhead
        time_per_book = avg_chunks_per_book * time_per_chunk + 1  # +1 for processing

        # Account for batching efficiency
        if book_count > 10:
            time_per_book *= 0.8  # 20% faster with batching

        return book_count * time_per_book


class IndexingJob:
    """Background job for indexing books"""

    def __init__(
        self,
        indexing_service: IndexingService,
        book_ids: List[int],
        reindex: bool = False,
    ):
        """
        Initialize indexing job

        Args:
            indexing_service: The indexing service
            book_ids: Books to index
            reindex: Whether to reindex existing books
        """
        self.indexing_service = indexing_service
        self.book_ids = book_ids
        self.reindex = reindex
        self.loop = asyncio.new_event_loop()

    def run(self) -> Dict[str, Any]:
        """Run the indexing job"""
        try:
            # Run async indexing in the event loop
            result = self.loop.run_until_complete(
                self.indexing_service.index_books(self.book_ids, self.reindex)
            )
            return result
        finally:
            self.loop.close()

    def cancel(self):
        """Request cancellation"""
        self.indexing_service.request_cancel()
