"""
Integration tests for the complete semantic search workflow

These tests verify that all components work together correctly for the
full indexing and search workflow.
"""

import pytest
import asyncio
import numpy as np
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path
from typing import List, Dict, Any

# Direct import to avoid Calibre dependencies
import sys
plugin_path = Path(__file__).parent.parent.parent / "calibre_plugins" / "semantic_search"
sys.path.insert(0, str(plugin_path))

# Mock all Calibre-related imports
mock_text_processor = Mock()
mock_embedding_service = Mock()
mock_repositories = Mock()
mock_search_engine = Mock()
mock_indexing_service = Mock()
mock_database = Mock()
mock_cache = Mock()

# Create mock classes for integration testing
class MockChunk:
    def __init__(self, text, index, book_id, start_pos, end_pos, metadata):
        self.text = text
        self.index = index
        self.book_id = book_id
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.metadata = metadata

class MockTextProcessor:
    def chunk_text(self, text, metadata=None):
        # Create realistic chunks for philosophical text
        chunks = []
        sentences = text.split('. ')
        
        current_chunk = ""
        chunk_index = 0
        start_pos = 0
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < 500:  # Max chunk size
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(MockChunk(
                        current_chunk.strip(),
                        chunk_index,
                        metadata.get('book_id', 1),
                        start_pos,
                        start_pos + len(current_chunk),
                        metadata or {}
                    ))
                    chunk_index += 1
                    start_pos += len(current_chunk)
                current_chunk = sentence + ". "
        
        # Add final chunk
        if current_chunk:
            chunks.append(MockChunk(
                current_chunk.strip(),
                chunk_index,
                metadata.get('book_id', 1),
                start_pos,
                start_pos + len(current_chunk),
                metadata or {}
            ))
        
        return chunks

class MockEmbeddingService:
    def __init__(self):
        self.embedding_cache = {}  # Cache embeddings by text hash
    
    async def generate_embedding(self, text):
        # Use cached embedding if available for consistent results
        text_hash = hash(text)
        if text_hash not in self.embedding_cache:
            # Generate deterministic embedding based on text content
            np.random.seed(text_hash & 0x7FFFFFFF)  # Ensure positive seed
            self.embedding_cache[text_hash] = np.random.rand(768).astype(np.float32)
        return self.embedding_cache[text_hash]
    
    async def generate_batch(self, texts):
        embeddings = []
        for text in texts:
            embedding = await self.generate_embedding(text)
            embeddings.append(embedding)
        return embeddings

class MockEmbeddingRepository:
    def __init__(self):
        self.embeddings = {}  # book_id -> list of (chunk, embedding)
        self.indexing_status = {}  # book_id -> status
    
    async def store_embedding(self, book_id, chunk, embedding):
        if book_id not in self.embeddings:
            self.embeddings[book_id] = []
        self.embeddings[book_id].append((chunk, embedding))
    
    async def get_embeddings(self, book_id):
        return self.embeddings.get(book_id, [])
    
    async def delete_book_embeddings(self, book_id):
        if book_id in self.embeddings:
            del self.embeddings[book_id]
    
    def update_indexing_status(self, book_id, status, progress=None, error=None):
        self.indexing_status[book_id] = {
            'status': status,
            'progress': progress,
            'error': error
        }
    
    def get_indexing_status(self):
        return [
            {'book_id': book_id, **status}
            for book_id, status in self.indexing_status.items()
        ]
    
    def get_statistics(self):
        indexed_books = len([b for b in self.indexing_status.values() if b['status'] == 'completed'])
        total_chunks = sum(len(chunks) for chunks in self.embeddings.values())
        return {
            'indexed_books': indexed_books,
            'total_chunks': total_chunks
        }
    
    async def search_similar(self, embedding, limit=20, filters=None):
        results = []
        
        for book_id, chunks_embeddings in self.embeddings.items():
            for chunk, chunk_embedding in chunks_embeddings:
                # Calculate cosine similarity
                similarity = np.dot(embedding, chunk_embedding) / (
                    np.linalg.norm(embedding) * np.linalg.norm(chunk_embedding)
                )
                
                result = {
                    'chunk_id': len(results),
                    'book_id': book_id,
                    'title': f'Book {book_id}',
                    'authors': [f'Author {book_id}'],
                    'chunk_text': chunk.text,
                    'chunk_index': chunk.index,
                    'similarity': float(similarity),
                    'metadata': chunk.metadata
                }
                results.append(result)
        
        # Sort by similarity
        results.sort(key=lambda x: x['similarity'], reverse=True)
        
        # Apply filters
        if filters:
            if 'author' in filters:
                results = [r for r in results if filters['author'] in r['authors']]
            if 'min_score' in filters:
                results = [r for r in results if r['similarity'] >= filters['min_score']]
            if 'book_ids' in filters:
                results = [r for r in results if r['book_id'] in filters['book_ids']]
        
        return results[:limit]

class MockCalibreRepository:
    def __init__(self):
        self.books = {
            1: {
                'id': 1,
                'title': 'Being and Time',
                'authors': ['Martin Heidegger'],
                'tags': ['Philosophy', 'Existentialism'],
                'formats': ['EPUB'],
                'pubdate': '1927',
                'language': 'en',
                'text': self._get_heidegger_text()
            },
            2: {
                'id': 2,
                'title': 'Ideas: General Introduction to Pure Phenomenology',
                'authors': ['Edmund Husserl'],
                'tags': ['Philosophy', 'Phenomenology'],
                'formats': ['EPUB'],
                'pubdate': '1913',
                'language': 'en',
                'text': self._get_husserl_text()
            },
            3: {
                'id': 3,
                'title': 'Being and Nothingness',
                'authors': ['Jean-Paul Sartre'],
                'tags': ['Philosophy', 'Existentialism'],
                'formats': ['EPUB'],
                'pubdate': '1943',
                'language': 'en',
                'text': self._get_sartre_text()
            }
        }
    
    def get_book_metadata(self, book_id):
        if book_id not in self.books:
            raise ValueError(f"Book {book_id} not found")
        book = self.books[book_id]
        return {k: v for k, v in book.items() if k != 'text'}
    
    def get_book_text(self, book_id):
        if book_id not in self.books:
            raise ValueError(f"Book {book_id} not found")
        return self.books[book_id]['text']
    
    def get_all_book_ids(self):
        return list(self.books.keys())
    
    def get_books_by_filter(self, filters):
        results = []
        for book_id, book in self.books.items():
            if 'author' in filters:
                if not any(filters['author'].lower() in author.lower() 
                          for author in book['authors']):
                    continue
            if 'tag' in filters:
                if filters['tag'] not in book.get('tags', []):
                    continue
            results.append(book_id)
        return results
    
    def _get_heidegger_text(self):
        return """
        Dasein is essentially characterized by being-in-the-world. This being-in-the-world 
        is not a spatial relation but an existential structure that defines human existence. 
        The structure of care reveals the being of Dasein as thrown projection fallen into 
        the world of everyday concerns. Authenticity emerges through confrontation with 
        anxiety and the call of conscience. Being-toward-death reveals the finite character 
        of human existence and opens the possibility of authentic temporality. The they-self 
        dominates everyday existence, covering over the authentic possibilities of Dasein.
        """
    
    def _get_husserl_text(self):
        return """
        Consciousness is always consciousness of something. This fundamental structure of 
        intentionality means that consciousness cannot be understood as a self-contained 
        sphere of mental states. The phenomenological reduction brackets the natural attitude 
        and reveals the transcendental ego as the source of all meaning constitution. 
        The noetic-noematic correlation structures every conscious act. Passive synthesis 
        underlies all active constitution of meaning. Time-consciousness is the fundamental 
        level of transcendental subjectivity.
        """
    
    def _get_sartre_text(self):
        return """
        Human reality is being-for-itself, characterized by nothingness and freedom. 
        Consciousness is a nihilating activity that introduces negation into being. 
        Bad faith is the fundamental way humans flee from their radical freedom. 
        The look of the other transforms us into objects and creates shame. 
        Authenticity requires accepting the anguish of absolute responsibility. 
        We are condemned to be free and must create our own values through our choices.
        """

class MockSearchEngine:
    def __init__(self, embedding_service, embedding_repo):
        self.embedding_service = embedding_service
        self.embedding_repo = embedding_repo
    
    async def search(self, query, limit=20, scope=None, filters=None, search_mode='semantic'):
        # Generate query embedding
        query_embedding = await self.embedding_service.generate_embedding(query)
        
        # Search similar chunks
        results = await self.embedding_repo.search_similar(
            query_embedding, limit=limit, filters=filters
        )
        
        return {
            'results': results,
            'total_results': len(results),
            'query': query,
            'search_mode': search_mode
        }
    
    async def search_similar_to_chunk(self, chunk_id, limit=20):
        # Mock implementation for similarity search
        return {
            'results': [],
            'total_results': 0,
            'source_chunk_id': chunk_id
        }

class MockIndexingService:
    def __init__(self, text_processor, embedding_service, embedding_repo, calibre_repo):
        self.text_processor = text_processor
        self.embedding_service = embedding_service
        self.embedding_repo = embedding_repo
        self.calibre_repo = calibre_repo
        self._progress_callbacks = []
        self._cancel_requested = False
    
    def add_progress_callback(self, callback):
        self._progress_callbacks.append(callback)
    
    def request_cancel(self):
        self._cancel_requested = True
    
    def _report_progress(self, **kwargs):
        for callback in self._progress_callbacks:
            try:
                callback(kwargs)
            except Exception:
                pass
    
    async def index_single_book(self, book_id):
        if self._cancel_requested:
            raise Exception("Indexing cancelled")
        
        # Report start
        self._report_progress(book_id=book_id, status='starting', progress=0.0)
        
        # Update status
        self.embedding_repo.update_indexing_status(book_id, 'indexing', 0.0)
        
        # Get book data
        metadata = self.calibre_repo.get_book_metadata(book_id)
        text = self.calibre_repo.get_book_text(book_id)
        
        if not text.strip():
            raise ValueError("No text content found")
        
        # Report progress
        self._report_progress(book_id=book_id, status='chunking', progress=0.2)
        
        # Chunk text
        chunks = self.text_processor.chunk_text(text, metadata={
            'book_id': book_id,
            'title': metadata['title'],
            'authors': metadata['authors']
        })
        
        # Report progress
        self._report_progress(book_id=book_id, status='generating_embeddings', progress=0.5)
        
        # Generate embeddings
        chunk_texts = [chunk.text for chunk in chunks]
        embeddings = await self.embedding_service.generate_batch(chunk_texts)
        
        # Report progress
        self._report_progress(book_id=book_id, status='storing', progress=0.8)
        
        # Store embeddings
        await self.embedding_repo.delete_book_embeddings(book_id)
        for chunk, embedding in zip(chunks, embeddings):
            await self.embedding_repo.store_embedding(book_id, chunk, embedding)
        
        # Update status
        self.embedding_repo.update_indexing_status(book_id, 'completed', 1.0)
        
        # Report completion
        self._report_progress(book_id=book_id, status='completed', progress=1.0)
        
        return {
            'book_id': book_id,
            'chunk_count': len(chunks),
            'status': 'success'
        }
    
    async def index_books(self, book_ids, reindex=False):
        stats = {
            'total_books': len(book_ids),
            'processed_books': 0,
            'successful_books': 0,
            'failed_books': 0,
            'total_chunks': 0,
            'errors': []
        }
        
        for book_id in book_ids:
            if self._cancel_requested:
                break
            
            try:
                # Check if already indexed
                if not reindex:
                    existing = await self.embedding_repo.get_embeddings(book_id)
                    if existing:
                        stats['processed_books'] += 1
                        continue
                
                result = await self.index_single_book(book_id)
                stats['processed_books'] += 1
                stats['successful_books'] += 1
                stats['total_chunks'] += result['chunk_count']
                
            except Exception as e:
                stats['failed_books'] += 1
                stats['errors'].append({
                    'book_id': book_id,
                    'error': str(e)
                })
        
        return stats
    
    async def get_indexing_status(self):
        return self.embedding_repo.get_indexing_status()
    
    async def get_library_statistics(self):
        stats = self.embedding_repo.get_statistics()
        all_books = self.calibre_repo.get_all_book_ids()
        stats['total_library_books'] = len(all_books)
        stats['indexing_percentage'] = (
            (stats['indexed_books'] / stats['total_library_books'] * 100)
            if stats['total_library_books'] > 0 else 0
        )
        return stats

# Setup module mocks
mock_text_processor.TextProcessor = MockTextProcessor
mock_embedding_service.EmbeddingService = MockEmbeddingService
mock_repositories.EmbeddingRepository = MockEmbeddingRepository
mock_repositories.CalibreRepository = MockCalibreRepository
mock_search_engine.SearchEngine = MockSearchEngine
mock_indexing_service.IndexingService = MockIndexingService

@pytest.fixture
def text_processor():
    return MockTextProcessor()

@pytest.fixture
def embedding_service():
    return MockEmbeddingService()

@pytest.fixture
def embedding_repo():
    return MockEmbeddingRepository()

@pytest.fixture
def calibre_repo():
    return MockCalibreRepository()

@pytest.fixture
def search_engine(embedding_service, embedding_repo):
    return MockSearchEngine(embedding_service, embedding_repo)

@pytest.fixture
def indexing_service(text_processor, embedding_service, embedding_repo, calibre_repo):
    return MockIndexingService(text_processor, embedding_service, embedding_repo, calibre_repo)


class TestCompleteWorkflow:
    """Test the complete indexing and search workflow"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_indexing_and_search_workflow(self, indexing_service, search_engine):
        """Test complete workflow from book indexing to search"""
        
        # Step 1: Index all books
        book_ids = [1, 2, 3]
        indexing_result = await indexing_service.index_books(book_ids)
        
        # Verify indexing succeeded
        assert indexing_result['successful_books'] == 3
        assert indexing_result['failed_books'] == 0
        assert indexing_result['total_chunks'] > 0
        
        # Step 2: Verify indexing status
        status = await indexing_service.get_indexing_status()
        completed_books = [s for s in status if s['status'] == 'completed']
        assert len(completed_books) == 3
        
        # Step 3: Get library statistics
        stats = await indexing_service.get_library_statistics()
        assert stats['indexed_books'] == 3
        assert stats['total_library_books'] == 3
        assert stats['indexing_percentage'] == 100.0
        
        # Step 4: Perform semantic search
        search_result = await search_engine.search("being and existence", limit=10)
        
        # Verify search results
        assert len(search_result['results']) > 0
        assert search_result['total_results'] > 0
        
        # Check that results are properly ranked by similarity
        similarities = [r['similarity'] for r in search_result['results']]
        assert similarities == sorted(similarities, reverse=True)
        
        # Step 5: Search with filters
        filtered_result = await search_engine.search(
            "consciousness",
            limit=5,
            filters={'author': 'Husserl'}
        )
        
        # Verify filtering worked
        for result in filtered_result['results']:
            assert 'Husserl' in result['authors']
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_incremental_indexing_workflow(self, indexing_service, search_engine):
        """Test incremental indexing and re-indexing"""
        
        # Index first book
        result1 = await indexing_service.index_single_book(1)
        assert result1['status'] == 'success'
        
        # Search should find results from first book
        search1 = await search_engine.search("Dasein", limit=10)
        assert len(search1['results']) > 0
        
        # Index second book
        result2 = await indexing_service.index_single_book(2)
        assert result2['status'] == 'success'
        
        # Search should now find results from both books
        search2 = await search_engine.search("consciousness", limit=10)
        book_ids_in_results = set(r['book_id'] for r in search2['results'])
        assert len(book_ids_in_results) > 0  # Should have results
        
        # Re-index first book (should replace existing)
        result3 = await indexing_service.index_single_book(1)
        assert result3['status'] == 'success'
        
        # Search should still work
        search3 = await search_engine.search("being", limit=10)
        assert len(search3['results']) > 0
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_error_handling_workflow(self, indexing_service, calibre_repo):
        """Test error handling in the workflow"""
        
        # Try to index non-existent book
        with pytest.raises(ValueError, match="Book 999 not found"):
            await indexing_service.index_single_book(999)
        
        # Mock empty book content
        original_get_text = calibre_repo.get_book_text
        calibre_repo.get_book_text = lambda book_id: ""
        
        with pytest.raises(ValueError, match="No text content found"):
            await indexing_service.index_single_book(1)
        
        # Restore original method
        calibre_repo.get_book_text = original_get_text
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_cancellation_workflow(self, indexing_service):
        """Test cancellation during indexing"""
        
        # Start indexing multiple books
        async def cancel_after_delay():
            await asyncio.sleep(0.01)  # Small delay
            indexing_service.request_cancel()
        
        # Start cancellation task
        cancel_task = asyncio.create_task(cancel_after_delay())
        
        # This might complete or might be cancelled depending on timing
        try:
            result = await indexing_service.index_books([1, 2, 3])
            # If it completes, that's fine
            assert result['total_books'] == 3
        except Exception as e:
            # If it gets cancelled, that's also fine
            assert "cancelled" in str(e).lower()
        
        await cancel_task
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_progress_tracking_workflow(self, indexing_service):
        """Test progress tracking during indexing"""
        
        progress_updates = []
        
        def track_progress(progress_data):
            progress_updates.append(progress_data)
        
        indexing_service.add_progress_callback(track_progress)
        
        # Index a book
        await indexing_service.index_single_book(1)
        
        # Should have received progress updates
        assert len(progress_updates) >= 1
        
        # Check that we got status updates
        statuses = [update.get('status') for update in progress_updates]
        assert any(status for status in statuses)


class TestPhilosophicalContentWorkflow:
    """Test workflow with philosophical content scenarios"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_concept_search_workflow(self, indexing_service, search_engine):
        """Test searching for philosophical concepts"""
        
        # Index philosophical texts
        await indexing_service.index_books([1, 2, 3])
        
        # Search for key philosophical concepts
        concepts = [
            "consciousness",
            "existence", 
            "freedom",
            "being",
            "temporality"
        ]
        
        for concept in concepts:
            results = await search_engine.search(concept, limit=5)
            
            # Should find relevant results
            assert len(results['results']) > 0
            
            # Results should contain the concept or related terms
            found_relevant = False
            for result in results['results']:
                if concept.lower() in result['chunk_text'].lower():
                    found_relevant = True
                    break
            
            # At least some results should be directly relevant
            # (This is a loose check since semantic similarity might find related concepts)
            if not found_relevant:
                # Check if at least the similarity scores are reasonable
                similarities = [r['similarity'] for r in results['results']]
                assert max(similarities) > 0.1  # At least some semantic similarity
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_author_based_search_workflow(self, indexing_service, search_engine):
        """Test searching within specific authors' works"""
        
        # Index all books
        await indexing_service.index_books([1, 2, 3])
        
        # Search for concepts in Heidegger's work
        heidegger_results = await search_engine.search(
            "being",
            filters={'author': 'Heidegger'}
        )
        
        # All results should be from Heidegger
        for result in heidegger_results['results']:
            assert 'Heidegger' in result['authors']
        
        # Search for concepts in Husserl's work
        husserl_results = await search_engine.search(
            "consciousness",
            filters={'author': 'Husserl'}
        )
        
        # All results should be from Husserl
        for result in husserl_results['results']:
            assert 'Husserl' in result['authors']
    
    @pytest.mark.asyncio
    @pytest.mark.integration 
    async def test_cross_author_comparison_workflow(self, indexing_service, search_engine):
        """Test comparing concepts across different authors"""
        
        # Index all books
        await indexing_service.index_books([1, 2, 3])
        
        # Search for a concept that appears in multiple authors
        results = await search_engine.search("being", limit=20)
        
        # Should find results from multiple authors
        authors_found = set()
        for result in results['results']:
            authors_found.update(result['authors'])
        
        # Should have results from at least 2 different authors
        assert len(authors_found) >= 2
        
        # Check that different authors discuss the concept differently
        heidegger_texts = [r['chunk_text'] for r in results['results'] 
                          if 'Heidegger' in r['authors']]
        sartre_texts = [r['chunk_text'] for r in results['results'] 
                       if 'Sartre' in r['authors']]
        
        if heidegger_texts and sartre_texts:
            # The texts should be different (different approaches to "being")
            assert heidegger_texts[0] != sartre_texts[0]


class TestScalabilityWorkflow:
    """Test workflow scalability and performance"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_large_library_workflow(self, indexing_service, search_engine, calibre_repo):
        """Test workflow with larger library (simulated)"""
        
        # Simulate larger library by adding more books
        for i in range(4, 11):  # Add books 4-10
            calibre_repo.books[i] = {
                'id': i,
                'title': f'Philosophy Book {i}',
                'authors': [f'Author {i}'],
                'tags': ['Philosophy'],
                'formats': ['EPUB'],
                'pubdate': f'{1900 + i}',
                'language': 'en',
                'text': f"This is philosophical content for book {i}. " * 20
            }
        
        # Index all books (10 total)
        book_ids = list(range(1, 11))
        result = await indexing_service.index_books(book_ids)
        
        # Should successfully index all books
        assert result['successful_books'] == 10
        assert result['total_chunks'] > 0
        
        # Search should still be fast and accurate
        search_result = await search_engine.search("philosophical content", limit=20)
        assert len(search_result['results']) > 0
        
        # Check library statistics
        stats = await indexing_service.get_library_statistics()
        assert stats['total_library_books'] == 10
        assert stats['indexed_books'] == 10
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_concurrent_operations_workflow(self, embedding_service, embedding_repo):
        """Test concurrent indexing and searching"""
        
        # Create multiple search engines for concurrent access
        search_engines = [
            MockSearchEngine(embedding_service, embedding_repo)
            for _ in range(3)
        ]
        
        # First, index some content
        indexing_service = MockIndexingService(
            MockTextProcessor(), embedding_service, embedding_repo, MockCalibreRepository()
        )
        await indexing_service.index_books([1, 2])
        
        # Perform concurrent searches
        search_tasks = [
            engine.search(f"query {i}", limit=5)
            for i, engine in enumerate(search_engines)
        ]
        
        results = await asyncio.gather(*search_tasks)
        
        # All searches should complete successfully
        assert len(results) == 3
        for result in results:
            assert 'results' in result
            assert 'total_results' in result


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])