"""
Pytest configuration and fixtures
"""

# CRITICAL: Import calibre mocks BEFORE any other imports
# This prevents ModuleNotFoundError for calibre modules
import tests.calibre_mocks

import pytest
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Add the plugin directory to sys.path for testing
plugin_dir = Path(__file__).parent.parent
sys.path.insert(0, str(plugin_dir))


# QApplication fixture moved to ui_conftest.py for UI tests only
    

@pytest.fixture
def tmp_library(tmp_path):
    """Create a temporary Calibre library for testing"""
    library_path = tmp_path / "test_library"
    library_path.mkdir()
    
    # Create basic library structure
    (library_path / "metadata.db").touch()
    (library_path / "semantic_search").mkdir()
    
    return library_path


@pytest.fixture
def mock_calibre_gui(tmp_library):
    """Mock Calibre GUI object for testing"""
    gui = Mock()
    gui.library_path = str(tmp_library)
    gui.current_db = Mock()
    gui.current_db.new_api = Mock()
    
    # Mock current view
    gui.current_view = Mock()
    gui.current_view.return_value.selectionModel.return_value.selectedRows.return_value = []
    
    # Mock library view
    gui.library_view = Mock()
    
    return gui


@pytest.fixture
def mock_config(tmp_path):
    """Create a mock configuration dict for testing"""
    return {
        'embedding_provider': 'mock',
        'embedding_model': 'mock-model',
        'api_keys': {},
        'performance': {
            'cache_enabled': True,
            'cache_size_mb': 10,
            'batch_size': 32,
            'max_concurrent_requests': 4
        },
        'search': {
            'default_limit': 20,
            'default_threshold': 0.7,
            'default_scope': 'library'
        },
        'chunking': {
            'strategy': 'philosophical',
            'chunk_size': 512,
            'overlap': 64
        }
    }


@pytest.fixture
def sample_text():
    """Sample philosophical text for testing"""
    return """
    Being and Time (German: Sein und Zeit) is the 1927 magnum opus of German 
    philosopher Martin Heidegger and a key document of existentialism. Being 
    and Time had a notable impact on subsequent philosophy, literary theory and 
    many other fields. Its controversial stature in intellectual history has 
    been favorably compared with several works by Kant and Hegel.
    
    The book attempts to revive ontology through an analysis of Dasein, or 
    "being-in-the-world." It is also noted for an array of neologisms and 
    complex language, as well as an extended treatment of "authenticity" as a 
    means to grasp and confront the unique and finite possibilities of the 
    individual.
    """


@pytest.fixture
def sample_embeddings():
    """Sample embeddings for testing"""
    import random
    
    # Create deterministic embeddings for testing
    random.seed(42)
    
    def create_embedding(size=768):
        return [random.random() for _ in range(size)]
    
    embeddings = {
        'being': create_embedding(),
        'time': create_embedding(),
        'dasein': create_embedding(),
        'existence': create_embedding(),
    }
    
    return embeddings


@pytest.fixture
def mock_embedding_provider():
    """Mock embedding provider for testing"""
    import random
    random.seed(42)
    
    provider = Mock()
    provider.get_dimensions.return_value = 768
    provider.generate_embedding.return_value = [random.random() for _ in range(768)]
    provider.generate_batch.return_value = [
        [random.random() for _ in range(768)] for _ in range(10)
    ]
    return provider


class MockCalibreDB:
    """Mock Calibre database API"""
    
    def __init__(self, books=None):
        self.books = books or {}
        
    def all_book_ids(self):
        return list(self.books.keys())
        
    def get_metadata(self, book_id):
        book = self.books.get(book_id, {})
        metadata = Mock()
        metadata.title = book.get('title', f'Book {book_id}')
        metadata.authors = book.get('authors', ['Unknown'])
        metadata.tags = book.get('tags', [])
        return metadata
        
    def format_abspath(self, book_id, fmt):
        return f"/fake/path/book_{book_id}.{fmt.lower()}"
        
    def formats(self, book_id):
        return self.books.get(book_id, {}).get('formats', ['EPUB'])


@pytest.fixture
def mock_calibre_db():
    """Create a mock Calibre database with test data"""
    books = {
        1: {
            'title': 'Being and Time',
            'authors': ['Martin Heidegger'],
            'tags': ['philosophy', 'existentialism'],
            'formats': ['EPUB', 'PDF']
        },
        2: {
            'title': 'The Republic',
            'authors': ['Plato'],
            'tags': ['philosophy', 'ancient'],
            'formats': ['EPUB']
        },
        3: {
            'title': 'Critique of Pure Reason',
            'authors': ['Immanuel Kant'],
            'tags': ['philosophy', 'epistemology'],
            'formats': ['PDF']
        }
    }
    
    return MockCalibreDB(books)