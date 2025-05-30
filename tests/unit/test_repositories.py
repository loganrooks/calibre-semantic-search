"""
Unit tests for repositories following TDD approach
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import numpy as np
import json
from unittest.mock import Mock, AsyncMock, patch

# Direct import to avoid Calibre dependencies
import sys
plugin_path = Path(__file__).parent.parent.parent / "calibre_plugins" / "semantic_search"
sys.path.insert(0, str(plugin_path))

# Import repositories module directly
import importlib.util
spec = importlib.util.spec_from_file_location(
    "repositories", 
    plugin_path / "data" / "repositories.py"
)
repositories_module = importlib.util.module_from_spec(spec)

# Mock all Calibre-related imports
mock_database = Mock()
mock_text_processor = Mock()

# Create mock classes that we need
class MockSemanticSearchDB:
    def __init__(self, db_path):
        self.db_path = db_path

class MockChunk:
    def __init__(self, text, index, book_id, start_pos, end_pos, metadata):
        self.text = text
        self.index = index
        self.book_id = book_id
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.metadata = metadata

mock_database.SemanticSearchDB = MockSemanticSearchDB
mock_text_processor.Chunk = MockChunk

with patch.dict('sys.modules', {
    'calibre_plugins.semantic_search.data.database': mock_database,
    'calibre_plugins.semantic_search.core.text_processor': mock_text_processor,
    'calibre_plugins': Mock(),
    'calibre_plugins.semantic_search': Mock(),
    'calibre': Mock()
}):
    spec.loader.exec_module(repositories_module)

EmbeddingRepository = repositories_module.EmbeddingRepository
CalibreRepository = repositories_module.CalibreRepository
MockCalibreRepository = repositories_module.MockCalibreRepository

# Import text processor for Chunk class
spec2 = importlib.util.spec_from_file_location(
    "text_processor",
    plugin_path / "core" / "text_processor.py"
)
text_processor_module = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(text_processor_module)
Chunk = text_processor_module.Chunk


@pytest.fixture
def temp_db_path():
    """Create temporary database path"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir) / "test.db"
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_db():
    """Create mock database"""
    db = Mock()
    db.store_embedding.return_value = 1
    db.get_embedding.return_value = np.random.rand(768).astype(np.float32)
    db.search_similar.return_value = [
        {
            'chunk_id': 1,
            'book_id': 1,
            'chunk_text': 'Test chunk',
            'similarity': 0.9,
            'title': 'Test Book',
            'authors': ['Test Author']
        }
    ]
    db.clear_book_embeddings.return_value = None
    db.get_chunk.return_value = {
        'chunk_id': 1,
        'book_id': 1,
        'chunk_text': 'Test chunk',
        'embedding': np.random.rand(768).astype(np.float32)
    }
    db.get_statistics.return_value = {
        'total_books': 10,
        'total_chunks': 100
    }
    db.get_indexing_status.return_value = [
        {'book_id': 1, 'status': 'completed', 'progress': 1.0}
    ]
    db.update_indexing_status.return_value = None
    
    # Mock connection for direct queries
    mock_conn = Mock()
    mock_conn.execute.return_value.fetchall.return_value = [
        {
            'chunk_id': 1,
            'chunk_index': 0,
            'chunk_text': 'Test chunk text',
            'start_pos': 0,
            'end_pos': 15,
            'metadata': '{"test": "data"}'
        }
    ]
    db._conn = mock_conn
    
    return db


@pytest.fixture
def sample_chunk():
    """Create sample chunk for testing"""
    return MockChunk(
        text="This is a test chunk for semantic search.",
        index=0,
        book_id=1,
        start_pos=0,
        end_pos=42,
        metadata={
            "title": "Test Book",
            "authors": ["Test Author"],
            "chapter": "Chapter 1"
        }
    )


@pytest.fixture
def sample_embedding():
    """Create sample embedding vector"""
    return np.random.rand(768).astype(np.float32)


class TestEmbeddingRepository:
    """Test EmbeddingRepository class"""
    
    @pytest.fixture
    def repository(self, mock_db):
        """Create repository with mock database"""
        # Directly create repository and replace its db
        repo = EmbeddingRepository(Path("/tmp/test.db"))
        repo.db = mock_db
        return repo
    
    @pytest.mark.asyncio
    async def test_store_embedding_basic(self, repository, sample_chunk, sample_embedding):
        """Test storing a basic embedding"""
        chunk_id = await repository.store_embedding(1, sample_chunk, sample_embedding)
        
        assert chunk_id == 1
        repository.db.store_embedding.assert_called_once_with(1, sample_chunk, sample_embedding)
        
    @pytest.mark.asyncio
    async def test_store_embedding_adds_book_id_to_metadata(self, repository, sample_embedding):
        """Test that book_id is added to chunk metadata if not present"""
        chunk = MockChunk(
            text="Test chunk",
            index=0,
            book_id=1,
            start_pos=0,
            end_pos=10,
            metadata={}  # No book_id in metadata
        )
        
        await repository.store_embedding(1, chunk, sample_embedding)
        
        # Check that book_id was added to metadata
        assert chunk.metadata['book_id'] == 1
        
    @pytest.mark.asyncio
    async def test_store_embedding_preserves_existing_book_id(self, repository, sample_embedding):
        """Test that existing book_id in metadata is preserved"""
        chunk = MockChunk(
            text="Test chunk",
            index=0,
            book_id=1,
            start_pos=0,
            end_pos=10,
            metadata={'book_id': 2}  # Different book_id in metadata
        )
        
        await repository.store_embedding(1, chunk, sample_embedding)
        
        # Should preserve the existing book_id in metadata
        assert chunk.metadata['book_id'] == 2
        
    @pytest.mark.asyncio
    async def test_get_embeddings(self, repository):
        """Test retrieving embeddings for a book"""
        results = await repository.get_embeddings(1)
        
        assert len(results) == 1
        chunk, embedding = results[0]
        
        assert isinstance(chunk, MockChunk)
        assert chunk.text == "Test chunk text"
        assert chunk.index == 0
        assert chunk.book_id == 1
        assert chunk.metadata == {"test": "data"}
        
        assert isinstance(embedding, np.ndarray)
        assert embedding.dtype == np.float32
        
    @pytest.mark.asyncio
    async def test_get_embeddings_with_invalid_json(self, repository, mock_db):
        """Test get_embeddings handles invalid JSON metadata"""
        mock_db._conn.execute.return_value.fetchall.return_value = [
            {
                'chunk_id': 1,
                'chunk_index': 0,
                'chunk_text': 'Test chunk',
                'start_pos': 0,
                'end_pos': 10,
                'metadata': 'invalid json'
            }
        ]
        
        with pytest.raises(json.JSONDecodeError):
            await repository.get_embeddings(1)
            
    @pytest.mark.asyncio
    async def test_get_embeddings_with_null_metadata(self, repository, mock_db):
        """Test get_embeddings handles null metadata"""
        mock_db._conn.execute.return_value.fetchall.return_value = [
            {
                'chunk_id': 1,
                'chunk_index': 0,
                'chunk_text': 'Test chunk',
                'start_pos': 0,
                'end_pos': 10,
                'metadata': None
            }
        ]
        
        results = await repository.get_embeddings(1)
        
        chunk, _ = results[0]
        assert chunk.metadata == {}
        
    @pytest.mark.asyncio
    async def test_search_similar(self, repository, sample_embedding):
        """Test searching for similar embeddings"""
        filters = {'book_ids': [1, 2]}
        
        results = await repository.search_similar(sample_embedding, limit=10, filters=filters)
        
        assert len(results) == 1
        assert results[0]['chunk_id'] == 1
        assert results[0]['similarity'] == 0.9
        
        repository.db.search_similar.assert_called_once_with(sample_embedding, 10, filters)
        
    @pytest.mark.asyncio
    async def test_search_similar_default_params(self, repository, sample_embedding):
        """Test search_similar with default parameters"""
        results = await repository.search_similar(sample_embedding)
        
        repository.db.search_similar.assert_called_once_with(sample_embedding, 20, None)
        
    @pytest.mark.asyncio
    async def test_delete_book_embeddings(self, repository):
        """Test deleting embeddings for a book"""
        await repository.delete_book_embeddings(1)
        
        repository.db.clear_book_embeddings.assert_called_once_with(1)
        
    @pytest.mark.asyncio
    async def test_get_chunk(self, repository):
        """Test getting chunk data"""
        result = await repository.get_chunk(1)
        
        assert result['chunk_id'] == 1
        assert result['book_id'] == 1
        assert result['chunk_text'] == 'Test chunk'
        
        repository.db.get_chunk.assert_called_once_with(1)
        
    def test_get_statistics(self, repository):
        """Test getting repository statistics"""
        stats = repository.get_statistics()
        
        assert stats['total_books'] == 10
        assert stats['total_chunks'] == 100
        
        repository.db.get_statistics.assert_called_once()
        
    def test_update_indexing_status(self, repository):
        """Test updating indexing status"""
        repository.update_indexing_status(1, 'indexing', 0.5, None)
        
        repository.db.update_indexing_status.assert_called_once_with(1, 'indexing', 0.5, None)
        
    def test_get_indexing_status(self, repository):
        """Test getting indexing status"""
        status = repository.get_indexing_status(1)
        
        assert len(status) == 1
        assert status[0]['book_id'] == 1
        assert status[0]['status'] == 'completed'
        
        repository.db.get_indexing_status.assert_called_once_with(1)
        
    def test_get_indexing_status_all_books(self, repository):
        """Test getting indexing status for all books"""
        repository.get_indexing_status()
        
        repository.db.get_indexing_status.assert_called_once_with(None)


class TestCalibreRepository:
    """Test CalibreRepository class"""
    
    @pytest.fixture
    def mock_calibre_db(self):
        """Create mock Calibre database"""
        db = Mock()
        
        # Mock metadata object
        mock_metadata = Mock()
        mock_metadata.title = "Test Book"
        mock_metadata.authors = ["Test Author", "Co-Author"]
        mock_metadata.tags = ["Fiction", "Science"]
        mock_metadata.series = "Test Series"
        mock_metadata.series_index = 1
        mock_metadata.pubdate = Mock()
        mock_metadata.pubdate.isoformat.return_value = "2023-01-01"
        mock_metadata.language = "en"
        mock_metadata.format_metadata = {"EPUB": {}, "PDF": {}}
        mock_metadata.identifiers = {"isbn": "1234567890"}
        mock_metadata.comments = "Test description"
        mock_metadata.publisher = "Test Publisher"
        
        db.get_metadata.return_value = mock_metadata
        db.formats.return_value = ["EPUB", "PDF"]
        db.format_abspath.return_value = "/path/to/book.epub"
        db.all_book_ids.return_value = [1, 2, 3]
        db.all_author_names.return_value = ["Author 1", "Author 2"]
        db.all_tag_names.return_value = ["Tag 1", "Tag 2"]
        
        return db
        
    @pytest.fixture
    def repository(self, mock_calibre_db):
        """Create CalibreRepository with mock database"""
        return CalibreRepository(mock_calibre_db)
        
    def test_get_book_metadata_success(self, repository, mock_calibre_db):
        """Test successfully getting book metadata"""
        metadata = repository.get_book_metadata(1)
        
        assert metadata['id'] == 1
        assert metadata['title'] == "Test Book"
        assert metadata['authors'] == ["Test Author", "Co-Author"]
        assert metadata['tags'] == ["Fiction", "Science"]
        assert metadata['series'] == "Test Series"
        assert metadata['series_index'] == 1
        assert metadata['pubdate'] == "2023-01-01"
        assert metadata['language'] == "en"
        assert metadata['formats'] == ["EPUB", "PDF"]
        assert metadata['identifiers'] == {"isbn": "1234567890"}
        assert metadata['comments'] == "Test description"
        assert metadata['publisher'] == "Test Publisher"
        
        mock_calibre_db.get_metadata.assert_called_once_with(1)
        
    def test_get_book_metadata_missing_fields(self, repository, mock_calibre_db):
        """Test getting metadata with missing fields"""
        mock_metadata = Mock()
        mock_metadata.title = "Test Book"
        mock_metadata.authors = None
        mock_metadata.tags = None
        mock_metadata.series = None
        mock_metadata.series_index = None
        mock_metadata.pubdate = None
        mock_metadata.language = None
        mock_metadata.format_metadata = None
        mock_metadata.identifiers = None
        mock_metadata.comments = None
        mock_metadata.publisher = None
        
        mock_calibre_db.get_metadata.return_value = mock_metadata
        
        metadata = repository.get_book_metadata(1)
        
        assert metadata['authors'] == []
        assert metadata['tags'] == []
        assert metadata['pubdate'] is None
        assert metadata['formats'] == []
        assert metadata['identifiers'] == {}
        
    def test_get_book_metadata_error(self, repository, mock_calibre_db):
        """Test error handling in get_book_metadata"""
        mock_calibre_db.get_metadata.side_effect = Exception("Database error")
        
        metadata = repository.get_book_metadata(1)
        
        assert metadata['id'] == 1
        assert metadata['title'] == 'Book 1'
        assert metadata['authors'] == []
        assert metadata['tags'] == []
        assert metadata['formats'] == []
        
    def test_get_book_text_epub_format(self, repository, mock_calibre_db):
        """Test extracting text from EPUB format"""
        # Directly mock the module's Path attribute
        original_path = repositories_module.Path
        
        # Create mock Path class
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        MockPath = Mock(return_value=mock_path_instance)
        
        # Temporarily replace Path in the module
        repositories_module.Path = MockPath
        
        try:
            with patch.object(repository, '_extract_text_from_file', return_value="Extracted text"):
                text = repository.get_book_text(1, "EPUB")
                
                assert text == "Extracted text"
                mock_calibre_db.formats.assert_called_once_with(1)
                mock_calibre_db.format_abspath.assert_called_once_with(1, "EPUB")
                repository._extract_text_from_file.assert_called_once_with("/path/to/book.epub", "EPUB")
        finally:
            # Restore original Path
            repositories_module.Path = original_path
            
    def test_get_book_text_auto_format_selection(self, repository, mock_calibre_db):
        """Test automatic format selection"""
        mock_calibre_db.formats.return_value = ["PDF", "MOBI", "EPUB"]
        
        with patch('pathlib.Path') as MockPath:
            mock_path_instance = Mock()
            mock_path_instance.exists.return_value = True
            MockPath.return_value = mock_path_instance
            
            with patch.object(repository, '_extract_text_from_file', return_value="Text"):
                repository.get_book_text(1)
                
                # Should select EPUB (highest preference)
                mock_calibre_db.format_abspath.assert_called_once_with(1, "EPUB")
                
    def test_get_book_text_no_formats(self, repository, mock_calibre_db):
        """Test when no formats are available"""
        mock_calibre_db.formats.return_value = []
        
        text = repository.get_book_text(1)
        
        assert text == ""
        
    def test_get_book_text_file_not_found(self, repository, mock_calibre_db):
        """Test when book file doesn't exist"""
        with patch('pathlib.Path') as MockPath:
            mock_path_instance = Mock()
            mock_path_instance.exists.return_value = False
            MockPath.return_value = mock_path_instance
            
            text = repository.get_book_text(1)
            
            assert text == ""
        
    def test_get_book_text_error(self, repository, mock_calibre_db):
        """Test error handling in get_book_text"""
        mock_calibre_db.formats.side_effect = Exception("Database error")
        
        text = repository.get_book_text(1)
        
        assert text == ""
        
    def test_extract_text_from_txt_file(self, repository):
        """Test extracting text from TXT file"""
        with patch('builtins.open') as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = "Text content"
            
            text = repository._extract_text_from_file("/path/to/book.txt", "TXT")
            
            assert text == "Text content"
            mock_open.assert_called_once_with("/path/to/book.txt", 'r', encoding='utf-8', errors='ignore')
            
    def test_extract_text_unsupported_format(self, repository):
        """Test extracting text from unsupported format"""
        text = repository._extract_text_from_file("/path/to/book.xyz", "XYZ")
        
        assert text == ""
        
    def test_extract_text_error(self, repository):
        """Test error handling in text extraction"""
        with patch('builtins.open', side_effect=IOError("File error")):
            text = repository._extract_text_from_file("/path/to/book.txt", "TXT")
            
            assert text == ""
            
    def test_get_books_by_filter_author(self, repository, mock_calibre_db):
        """Test filtering books by author"""
        # Mock metadata for different books
        metadata_1 = Mock()
        metadata_1.authors = ["John Doe", "Jane Smith"]
        metadata_2 = Mock()
        metadata_2.authors = ["Bob Wilson"]  # Changed to not contain "John"
        metadata_3 = Mock()
        metadata_3.authors = ["John Adams"]
        
        mock_calibre_db.get_metadata.side_effect = [metadata_1, metadata_2, metadata_3]
        
        book_ids = repository.get_books_by_filter({'author': 'John'})
        
        assert set(book_ids) == {1, 3}  # Books with authors containing "John" (case-insensitive)
        
    def test_get_books_by_filter_tags(self, repository, mock_calibre_db):
        """Test filtering books by tags"""
        metadata_1 = Mock()
        metadata_1.tags = ["Fiction", "Mystery"]
        metadata_2 = Mock()
        metadata_2.tags = ["Non-fiction", "Science"]
        metadata_3 = Mock()
        metadata_3.tags = ["Fiction", "Romance"]
        
        mock_calibre_db.get_metadata.side_effect = [metadata_1, metadata_2, metadata_3]
        
        book_ids = repository.get_books_by_filter({'tags': ['Fiction']})
        
        assert set(book_ids) == {1, 3}  # Books with Fiction tag
        
    def test_get_books_by_filter_language(self, repository, mock_calibre_db):
        """Test filtering books by language"""
        metadata_1 = Mock()
        metadata_1.language = "en"
        metadata_2 = Mock()
        metadata_2.language = "fr"
        metadata_3 = Mock()
        metadata_3.language = "en"
        
        mock_calibre_db.get_metadata.side_effect = [metadata_1, metadata_2, metadata_3]
        
        book_ids = repository.get_books_by_filter({'language': 'en'})
        
        assert set(book_ids) == {1, 3}  # Books in English
        
    def test_get_books_by_filter_multiple(self, repository, mock_calibre_db):
        """Test filtering books by multiple criteria"""
        metadata_1 = Mock()
        metadata_1.authors = ["John Doe"]
        metadata_1.tags = ["Fiction"]
        metadata_1.language = "en"
        
        metadata_2 = Mock()
        metadata_2.authors = ["John Smith"]
        metadata_2.tags = ["Non-fiction"]
        metadata_2.language = "en"
        
        metadata_3 = Mock()
        metadata_3.authors = ["Jane Doe"]
        metadata_3.tags = ["Fiction"]
        metadata_3.language = "fr"
        
        # Mock to return metadata based on book_id
        def get_metadata_by_id(book_id):
            if book_id == 1:
                return metadata_1
            elif book_id == 2:
                return metadata_2
            elif book_id == 3:
                return metadata_3
        
        mock_calibre_db.get_metadata.side_effect = get_metadata_by_id
        
        book_ids = repository.get_books_by_filter({
            'author': 'John',
            'tags': ['Fiction'],
            'language': 'en'
        })
        
        assert book_ids == [1]  # Only first book matches all criteria
        
    def test_get_books_by_filter_error(self, repository, mock_calibre_db):
        """Test error handling in get_books_by_filter"""
        mock_calibre_db.all_book_ids.side_effect = Exception("Database error")
        
        book_ids = repository.get_books_by_filter({'author': 'Test'})
        
        assert book_ids == []
        
    def test_get_all_book_ids(self, repository, mock_calibre_db):
        """Test getting all book IDs"""
        book_ids = repository.get_all_book_ids()
        
        assert book_ids == [1, 2, 3]
        mock_calibre_db.all_book_ids.assert_called_once()
        
    def test_get_all_book_ids_error(self, repository, mock_calibre_db):
        """Test error handling in get_all_book_ids"""
        mock_calibre_db.all_book_ids.side_effect = Exception("Database error")
        
        book_ids = repository.get_all_book_ids()
        
        assert book_ids == []
        
    def test_get_author_names(self, repository, mock_calibre_db):
        """Test getting all author names"""
        authors = repository.get_author_names()
        
        assert authors == ["Author 1", "Author 2"]
        mock_calibre_db.all_author_names.assert_called_once()
        
    def test_get_author_names_error(self, repository, mock_calibre_db):
        """Test error handling in get_author_names"""
        mock_calibre_db.all_author_names.side_effect = Exception("Database error")
        
        authors = repository.get_author_names()
        
        assert authors == []
        
    def test_get_tag_names(self, repository, mock_calibre_db):
        """Test getting all tag names"""
        tags = repository.get_tag_names()
        
        assert tags == ["Tag 1", "Tag 2"]
        mock_calibre_db.all_tag_names.assert_called_once()
        
    def test_get_tag_names_error(self, repository, mock_calibre_db):
        """Test error handling in get_tag_names"""
        mock_calibre_db.all_tag_names.side_effect = Exception("Database error")
        
        tags = repository.get_tag_names()
        
        assert tags == []


class TestMockCalibreRepository:
    """Test MockCalibreRepository class"""
    
    def test_init_empty(self):
        """Test initializing with no books"""
        repo = MockCalibreRepository()
        
        assert repo.books == {}
        
    def test_init_with_books(self):
        """Test initializing with books"""
        books = {
            1: {
                'id': 1,
                'title': 'Test Book',
                'authors': ['Test Author'],
                'tags': ['test']
            }
        }
        
        repo = MockCalibreRepository(books)
        
        assert repo.books == books
        
    def test_get_book_metadata_existing(self):
        """Test getting metadata for existing book"""
        books = {
            1: {
                'id': 1,
                'title': 'Test Book',
                'authors': ['Test Author'],
                'tags': ['test'],
                'formats': ['EPUB']
            }
        }
        
        repo = MockCalibreRepository(books)
        metadata = repo.get_book_metadata(1)
        
        assert metadata == books[1]
        
    def test_get_book_metadata_non_existing(self):
        """Test getting metadata for non-existing book"""
        repo = MockCalibreRepository()
        metadata = repo.get_book_metadata(999)
        
        assert metadata['id'] == 999
        assert metadata['title'] == 'Mock Book 999'
        assert metadata['authors'] == ['Mock Author']
        assert metadata['tags'] == ['test']
        assert metadata['formats'] == ['EPUB']
        
    def test_get_book_text_existing(self):
        """Test getting text for existing book"""
        books = {
            1: {
                'text': 'Custom book text'
            }
        }
        
        repo = MockCalibreRepository(books)
        text = repo.get_book_text(1)
        
        assert text == 'Custom book text'
        
    def test_get_book_text_non_existing(self):
        """Test getting text for non-existing book"""
        repo = MockCalibreRepository()
        text = repo.get_book_text(999)
        
        assert text == 'Mock text for book 999'
        
    def test_get_books_by_filter_author(self):
        """Test filtering by author"""
        books = {
            1: {'authors': ['John Doe', 'Jane Smith']},
            2: {'authors': ['Bob Wilson']},
            3: {'authors': ['John Adams']}
        }
        
        repo = MockCalibreRepository(books)
        results = repo.get_books_by_filter({'author': 'John'})
        
        assert set(results) == {1, 3}  # "John" matches "John Doe" and "John Adams"
        
    def test_get_books_by_filter_tags(self):
        """Test filtering by tags"""
        books = {
            1: {'tags': ['Fiction', 'Mystery']},
            2: {'tags': ['Non-fiction']},
            3: {'tags': ['Fiction', 'Romance']}
        }
        
        repo = MockCalibreRepository(books)
        results = repo.get_books_by_filter({'tags': ['Fiction']})
        
        assert set(results) == {1, 3}
        
    def test_get_books_by_filter_multiple(self):
        """Test filtering by multiple criteria"""
        books = {
            1: {
                'authors': ['John Doe'],
                'tags': ['Fiction']
            },
            2: {
                'authors': ['John Smith'],
                'tags': ['Non-fiction']
            },
            3: {
                'authors': ['Jane Doe'],
                'tags': ['Fiction']
            }
        }
        
        repo = MockCalibreRepository(books)
        results = repo.get_books_by_filter({
            'author': 'John',
            'tags': ['Fiction']
        })
        
        assert results == [1]
        
    def test_get_all_book_ids(self):
        """Test getting all book IDs"""
        books = {1: {}, 5: {}, 10: {}}
        
        repo = MockCalibreRepository(books)
        book_ids = repo.get_all_book_ids()
        
        assert set(book_ids) == {1, 5, 10}


class TestIntegration:
    """Integration tests for repositories"""
    
    @pytest.mark.asyncio
    async def test_embedding_repository_lifecycle(self, temp_db_path, sample_chunk, sample_embedding):
        """Test complete lifecycle of embedding operations"""
        # This would test with actual database if we could avoid Calibre deps
        # For now, just test the mock integration
        
        mock_db = Mock()
        mock_db.store_embedding.return_value = 1
        mock_db.get_embedding.return_value = sample_embedding
        mock_db.search_similar.return_value = []
        mock_db._conn.execute.return_value.fetchall.return_value = []
        
        repo = EmbeddingRepository(temp_db_path)
        repo.db = mock_db
        
        # Store
        chunk_id = await repo.store_embedding(1, sample_chunk, sample_embedding)
        assert chunk_id == 1
        
        # Retrieve
        embeddings = await repo.get_embeddings(1)
        assert isinstance(embeddings, list)
        
        # Search
        results = await repo.search_similar(sample_embedding)
        assert isinstance(results, list)
        
        # Delete
        await repo.delete_book_embeddings(1)
        mock_db.clear_book_embeddings.assert_called_with(1)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])