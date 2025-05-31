# Agent 3: Dependency Management Specialist Report
## Comprehensive Guide to Managing Dependencies in Calibre Plugins

### Executive Summary

Dependency management in Calibre plugins requires a fundamentally different approach than standard Python development. Since Calibre's embedded Python environment cannot access pip-installed packages, plugins must either bundle pure-Python dependencies or implement functionality from scratch. This report provides detailed strategies, patterns, and solutions for handling dependencies effectively.

### 1. Understanding Calibre's Dependency Constraints

#### The Fundamental Challenge

```python
# What DOESN'T work in Calibre plugins:
import numpy  # ImportError: No module named 'numpy'
import requests  # ImportError: No module named 'requests'
import pandas  # ImportError: No module named 'pandas'

# What DOES work:
import math  # Standard library
import json  # Standard library
from calibre.utils import browser  # Calibre built-in
```

#### Available Dependency Categories

```python
DEPENDENCY_CATEGORIES = {
    "standard_library": {
        "always_available": True,
        "examples": ["math", "json", "csv", "sqlite3", "urllib"],
    },
    "calibre_builtins": {
        "always_available": True,
        "examples": ["lxml", "beautifulsoup4", "html5-parser", "Pillow"],
    },
    "bundled_pure_python": {
        "always_available": False,
        "method": "Include in plugin ZIP",
        "restrictions": "Pure Python only, no C extensions",
    },
    "reimplemented": {
        "always_available": False,
        "method": "Rewrite functionality",
        "examples": "Vector operations, HTTP clients",
    },
}
```

### 2. Bundling Pure Python Dependencies

#### Step-by-Step Bundling Process

```python
# Directory structure for bundling dependencies
"""
my_plugin/
├── __init__.py
├── plugin-import-name-my_plugin.txt  # Enable imports
├── deps/                             # Bundled dependencies
│   ├── __init__.py
│   ├── pure_library1/
│   │   ├── __init__.py
│   │   ├── module1.py
│   │   └── module2.py
│   └── pure_library2/
│       ├── __init__.py
│       └── core.py
└── my_module.py
"""

# Example: Bundling a pure Python library
# 1. Download the pure Python package
# 2. Extract only the Python files (no tests, docs, etc.)
# 3. Place in deps/ folder
# 4. Import in your plugin:

from calibre_plugins.my_plugin.deps.pure_library1 import something
```

#### Practical Example: Bundling python-Levenshtein

```python
# Structure after bundling
"""
semantic_search_plugin/
├── __init__.py
├── plugin-import-name-semantic_search.txt
├── deps/
│   └── Levenshtein/
│       ├── __init__.py
│       └── _levenshtein.py  # Pure Python implementation
└── search.py
"""

# In search.py:
from calibre_plugins.semantic_search.deps.Levenshtein import distance

def fuzzy_match(s1, s2, threshold=0.8):
    """Fuzzy string matching using bundled Levenshtein"""
    max_len = max(len(s1), len(s2))
    if max_len == 0:
        return 1.0
    
    dist = distance(s1, s2)
    similarity = 1.0 - (dist / max_len)
    return similarity >= threshold
```

### 3. Implementing NumPy-like Functionality

#### Complete Vector Operations Library

```python
import math
import array
import struct
import operator
from typing import List, Union, Tuple, Optional

class VectorOps:
    """
    Pure Python implementation of vector operations
    optimized for performance and memory efficiency
    """
    
    # Type definitions
    Vector = Union[List[float], array.array]
    
    @staticmethod
    def create_vector(data: List[float], dtype='d') -> array.array:
        """Create an efficient vector representation"""
        return array.array(dtype, data)
    
    @staticmethod
    def zeros(size: int, dtype='d') -> array.array:
        """Create zero vector"""
        return array.array(dtype, [0.0] * size)
    
    @staticmethod
    def ones(size: int, dtype='d') -> array.array:
        """Create ones vector"""
        return array.array(dtype, [1.0] * size)
    
    @staticmethod
    def dot(v1: Vector, v2: Vector) -> float:
        """Optimized dot product"""
        # Fast path for arrays
        if isinstance(v1, array.array) and isinstance(v2, array.array):
            return sum(map(operator.mul, v1, v2))
        
        # General case
        return sum(a * b for a, b in zip(v1, v2))
    
    @staticmethod
    def norm(v: Vector, ord: int = 2) -> float:
        """Vector norm (L1, L2, Linf)"""
        if ord == 1:  # L1 norm
            return sum(abs(x) for x in v)
        elif ord == 2:  # L2 norm (Euclidean)
            return math.sqrt(sum(x * x for x in v))
        elif ord == float('inf'):  # L-infinity norm
            return max(abs(x) for x in v)
        else:
            # General p-norm
            return sum(abs(x) ** ord for x in v) ** (1.0 / ord)
    
    @staticmethod
    def normalize(v: Vector) -> List[float]:
        """Normalize vector to unit length"""
        norm = VectorOps.norm(v)
        if norm == 0:
            return list(v)
        return [x / norm for x in v]
    
    @staticmethod
    def cosine_similarity(v1: Vector, v2: Vector) -> float:
        """Cosine similarity between vectors"""
        dot_product = VectorOps.dot(v1, v2)
        norm1 = VectorOps.norm(v1)
        norm2 = VectorOps.norm(v2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    @staticmethod
    def euclidean_distance(v1: Vector, v2: Vector) -> float:
        """Euclidean distance between vectors"""
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(v1, v2)))
    
    @staticmethod
    def manhattan_distance(v1: Vector, v2: Vector) -> float:
        """Manhattan (L1) distance"""
        return sum(abs(a - b) for a, b in zip(v1, v2))
    
    @staticmethod
    def add(v1: Vector, v2: Vector) -> List[float]:
        """Vector addition"""
        return [a + b for a, b in zip(v1, v2)]
    
    @staticmethod
    def subtract(v1: Vector, v2: Vector) -> List[float]:
        """Vector subtraction"""
        return [a - b for a, b in zip(v1, v2)]
    
    @staticmethod
    def multiply(v: Vector, scalar: float) -> List[float]:
        """Scalar multiplication"""
        return [x * scalar for x in v]
    
    @staticmethod
    def mean(vectors: List[Vector]) -> List[float]:
        """Compute mean vector"""
        if not vectors:
            return []
        
        n = len(vectors)
        dim = len(vectors[0])
        
        result = [0.0] * dim
        for vec in vectors:
            for i, val in enumerate(vec):
                result[i] += val
        
        return [x / n for x in result]
```

#### Matrix Operations for Advanced Use Cases

```python
class MatrixOps:
    """Pure Python matrix operations"""
    
    Matrix = List[List[float]]
    
    @staticmethod
    def multiply(A: Matrix, B: Matrix) -> Matrix:
        """Matrix multiplication"""
        rows_A, cols_A = len(A), len(A[0])
        rows_B, cols_B = len(B), len(B[0])
        
        if cols_A != rows_B:
            raise ValueError("Incompatible dimensions")
        
        # Initialize result matrix
        C = [[0.0] * cols_B for _ in range(rows_A)]
        
        # Perform multiplication
        for i in range(rows_A):
            for j in range(cols_B):
                for k in range(cols_A):
                    C[i][j] += A[i][k] * B[k][j]
        
        return C
    
    @staticmethod
    def transpose(A: Matrix) -> Matrix:
        """Matrix transpose"""
        return list(map(list, zip(*A)))
    
    @staticmethod
    def identity(n: int) -> Matrix:
        """Identity matrix"""
        return [[1.0 if i == j else 0.0 for j in range(n)] 
                for i in range(n)]
```

### 4. Efficient Storage Solutions

#### Binary Storage for Embeddings

```python
import struct
import sqlite3
import json
from typing import Dict, List, Optional, Tuple

class EmbeddingStorage:
    """
    Efficient storage system for high-dimensional embeddings
    using binary formats and SQLite
    """
    
    def __init__(self, db_path: str, dimension: int = 768):
        self.db_path = db_path
        self.dimension = dimension
        self.conn = sqlite3.connect(db_path)
        self._create_tables()
    
    def _create_tables(self):
        """Create storage tables"""
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS embeddings (
                book_id INTEGER PRIMARY KEY,
                dimension INTEGER,
                embedding BLOB,
                metadata TEXT
            )
        ''')
        
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS embedding_index (
                book_id INTEGER,
                chunk_id INTEGER,
                start_pos INTEGER,
                end_pos INTEGER,
                embedding BLOB,
                PRIMARY KEY (book_id, chunk_id)
            )
        ''')
        
        self.conn.commit()
    
    def store_embedding(self, book_id: int, embedding: List[float], 
                       metadata: Optional[Dict] = None):
        """Store embedding efficiently"""
        # Convert to 32-bit floats for space efficiency
        packed = struct.pack(f'{len(embedding)}f', *embedding)
        
        meta_json = json.dumps(metadata) if metadata else '{}'
        
        self.conn.execute(
            'INSERT OR REPLACE INTO embeddings VALUES (?, ?, ?, ?)',
            (book_id, len(embedding), packed, meta_json)
        )
        self.conn.commit()
    
    def get_embedding(self, book_id: int) -> Optional[Tuple[List[float], Dict]]:
        """Retrieve embedding"""
        cursor = self.conn.execute(
            'SELECT dimension, embedding, metadata FROM embeddings WHERE book_id = ?',
            (book_id,)
        )
        row = cursor.fetchone()
        
        if not row:
            return None
        
        dimension, packed, meta_json = row
        embedding = list(struct.unpack(f'{dimension}f', packed))
        metadata = json.loads(meta_json)
        
        return embedding, metadata
    
    def batch_store(self, embeddings: Dict[int, List[float]]):
        """Efficiently store multiple embeddings"""
        data = []
        for book_id, embedding in embeddings.items():
            packed = struct.pack(f'{len(embedding)}f', *embedding)
            data.append((book_id, len(embedding), packed, '{}'))
        
        self.conn.executemany(
            'INSERT OR REPLACE INTO embeddings VALUES (?, ?, ?, ?)',
            data
        )
        self.conn.commit()
    
    def search_similar(self, query_embedding: List[float], 
                      top_k: int = 10) -> List[Tuple[int, float]]:
        """Find similar embeddings (requires pre-computation)"""
        # Note: For production, consider using sqlite-vec extension
        cursor = self.conn.execute(
            'SELECT book_id, embedding FROM embeddings'
        )
        
        similarities = []
        for book_id, packed in cursor:
            stored = list(struct.unpack(f'{self.dimension}f', packed))
            similarity = VectorOps.cosine_similarity(query_embedding, stored)
            similarities.append((book_id, similarity))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
```

### 5. HTTP Client Implementation

#### Pure Python HTTP Client

```python
import urllib.request
import urllib.parse
import urllib.error
import json
import ssl
from typing import Dict, Optional, Union, Any

class SimpleHTTPClient:
    """
    Pure Python HTTP client for plugins
    Alternative to requests library
    """
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.headers = {
            'User-Agent': 'Calibre Plugin/1.0'
        }
        
        # SSL context for HTTPS
        self.ssl_context = ssl.create_default_context()
    
    def get(self, url: str, params: Optional[Dict] = None, 
            headers: Optional[Dict] = None) -> Dict[str, Any]:
        """HTTP GET request"""
        if params:
            query_string = urllib.parse.urlencode(params)
            url = f"{url}?{query_string}"
        
        return self._request('GET', url, headers=headers)
    
    def post(self, url: str, data: Optional[Union[Dict, str]] = None,
             json_data: Optional[Dict] = None, 
             headers: Optional[Dict] = None) -> Dict[str, Any]:
        """HTTP POST request"""
        if json_data:
            data = json.dumps(json_data).encode('utf-8')
            headers = headers or {}
            headers['Content-Type'] = 'application/json'
        elif isinstance(data, dict):
            data = urllib.parse.urlencode(data).encode('utf-8')
        
        return self._request('POST', url, data=data, headers=headers)
    
    def _request(self, method: str, url: str, 
                 data: Optional[bytes] = None,
                 headers: Optional[Dict] = None) -> Dict[str, Any]:
        """Perform HTTP request"""
        # Prepare headers
        req_headers = self.headers.copy()
        if headers:
            req_headers.update(headers)
        
        # Create request
        request = urllib.request.Request(
            url, 
            data=data, 
            headers=req_headers,
            method=method
        )
        
        try:
            # Perform request
            with urllib.request.urlopen(
                request, 
                timeout=self.timeout,
                context=self.ssl_context
            ) as response:
                # Read response
                content = response.read()
                
                # Parse JSON if applicable
                content_type = response.headers.get('Content-Type', '')
                if 'application/json' in content_type:
                    content = json.loads(content.decode('utf-8'))
                
                return {
                    'status_code': response.status,
                    'headers': dict(response.headers),
                    'content': content,
                    'url': response.url
                }
                
        except urllib.error.HTTPError as e:
            return {
                'status_code': e.code,
                'error': str(e),
                'content': e.read().decode('utf-8', errors='ignore')
            }
        except Exception as e:
            return {
                'status_code': 0,
                'error': str(e),
                'content': None
            }

# Alternative: Use Calibre's built-in browser
from calibre.utils.browser import Browser

class CalibreHTTPClient:
    """HTTP client using Calibre's browser"""
    
    def __init__(self):
        self.browser = Browser()
    
    def get(self, url: str, headers: Optional[Dict] = None) -> str:
        """GET request using Calibre browser"""
        if headers:
            for key, value in headers.items():
                self.browser.set_header(key, value)
        
        return self.browser.open(url).read()
```

### 6. Handling Binary Dependencies

#### Strategy for Binary Dependencies

```python
class BinaryDependencyHandler:
    """
    Strategies for handling binary dependencies
    that cannot be bundled
    """
    
    @staticmethod
    def check_system_binary(binary_name: str) -> bool:
        """Check if system binary is available"""
        import subprocess
        import shutil
        
        # Method 1: Using shutil
        return shutil.which(binary_name) is not None
    
    @staticmethod
    def use_ctypes_for_system_libraries():
        """Example: Using system libraries via ctypes"""
        import ctypes
        import platform
        
        system = platform.system()
        
        if system == 'Windows':
            # Load Windows DLL
            lib = ctypes.windll.LoadLibrary('kernel32.dll')
        elif system == 'Darwin':
            # Load macOS dylib
            lib = ctypes.CDLL('/usr/lib/libc.dylib')
        else:
            # Load Linux shared library
            lib = ctypes.CDLL('libc.so.6')
        
        return lib
    
    @staticmethod
    def pure_python_alternatives():
        """Registry of pure Python alternatives"""
        return {
            'cryptography': 'Use pycryptodome (included in Calibre)',
            'pillow': 'Already included in Calibre',
            'lxml': 'Already included in Calibre',
            'numpy': 'Use custom VectorOps implementation',
            'requests': 'Use urllib or calibre.utils.browser',
            'sqlite3': 'Use standard library sqlite3',
        }
```

### 7. Dependency Compatibility Checking

#### Version Compatibility System

```python
import sys
from typing import Tuple, List, Optional

class DependencyChecker:
    """Check and validate dependencies"""
    
    def __init__(self):
        self.python_version = sys.version_info
        self.calibre_version = self._get_calibre_version()
    
    def _get_calibre_version(self) -> Tuple[int, int, int]:
        """Get Calibre version"""
        try:
            from calibre.constants import numeric_version
            return numeric_version
        except:
            return (0, 0, 0)
    
    def check_python_compatibility(self, min_version: Tuple[int, int]) -> bool:
        """Check Python version compatibility"""
        return self.python_version >= min_version
    
    def check_calibre_compatibility(self, min_version: Tuple[int, int, int]) -> bool:
        """Check Calibre version compatibility"""
        return self.calibre_version >= min_version
    
    def validate_pure_python_module(self, module_path: str) -> bool:
        """Validate that a module is pure Python"""
        import os
        import ast
        
        # Check file extension
        if not module_path.endswith('.py'):
            return False
        
        # Parse and check for imports of C extensions
        try:
            with open(module_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
            
            # Look for suspicious imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in ['numpy', 'scipy', 'pandas']:
                            return False
            
            return True
        except:
            return False
    
    def generate_compatibility_report(self) -> Dict[str, Any]:
        """Generate compatibility report"""
        return {
            'python_version': f"{self.python_version.major}.{self.python_version.minor}.{self.python_version.micro}",
            'calibre_version': f"{self.calibre_version[0]}.{self.calibre_version[1]}.{self.calibre_version[2]}",
            'platform': sys.platform,
            'available_stdlib': self._check_stdlib_modules(),
            'calibre_modules': self._check_calibre_modules(),
        }
    
    def _check_stdlib_modules(self) -> List[str]:
        """Check available standard library modules"""
        available = []
        for module in ['json', 'csv', 'sqlite3', 'urllib', 'xml', 'html']:
            try:
                __import__(module)
                available.append(module)
            except ImportError:
                pass
        return available
    
    def _check_calibre_modules(self) -> List[str]:
        """Check available Calibre modules"""
        available = []
        for module in ['calibre.utils', 'calibre.ebooks', 'calibre.library']:
            try:
                __import__(module)
                available.append(module)
            except ImportError:
                pass
        return available
```

### 8. Optimization Strategies

#### Memory-Efficient Implementations

```python
class OptimizedDependencies:
    """Memory and performance optimized implementations"""
    
    @staticmethod
    def streaming_json_parser(file_path: str):
        """Parse large JSON files without loading entirely into memory"""
        import json
        
        def parse_array():
            with open(file_path, 'r', encoding='utf-8') as f:
                # Skip initial [
                f.read(1)
                
                buffer = ''
                in_string = False
                brace_count = 0
                
                while True:
                    char = f.read(1)
                    if not char:
                        break
                    
                    buffer += char
                    
                    if char == '"' and buffer[-2:] != '\\"':
                        in_string = not in_string
                    elif not in_string:
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            
                            if brace_count == 0:
                                # Complete object
                                yield json.loads(buffer.strip().rstrip(','))
                                buffer = ''
        
        return parse_array()
    
    @staticmethod
    def lazy_import_system():
        """Lazy import system for large dependencies"""
        class LazyImporter:
            def __init__(self, module_name):
                self.module_name = module_name
                self._module = None
            
            def __getattr__(self, name):
                if self._module is None:
                    self._module = __import__(self.module_name)
                return getattr(self._module, name)
        
        return LazyImporter
```

### 9. Fallback Strategies

#### Graceful Degradation

```python
class FallbackSystem:
    """Implement fallback strategies for missing dependencies"""
    
    def __init__(self):
        self.available_features = {}
        self._check_features()
    
    def _check_features(self):
        """Check which features are available"""
        # Check for advanced math
        try:
            import scipy
            self.available_features['scipy'] = True
        except ImportError:
            self.available_features['scipy'] = False
        
        # Check for ML libraries
        try:
            import sklearn
            self.available_features['ml'] = True
        except ImportError:
            self.available_features['ml'] = False
    
    def get_implementation(self, feature: str):
        """Get appropriate implementation based on availability"""
        implementations = {
            'vector_ops': {
                'optimal': 'numpy',
                'fallback': VectorOps,
            },
            'http_client': {
                'optimal': 'requests',
                'fallback': SimpleHTTPClient,
            },
            'image_processing': {
                'optimal': 'pillow',
                'fallback': 'calibre.utils.img',
            }
        }
        
        impl = implementations.get(feature, {})
        
        # Try optimal first
        if impl.get('optimal'):
            try:
                return __import__(impl['optimal'])
            except ImportError:
                pass
        
        # Return fallback
        return impl.get('fallback')
```

### 10. Best Practices Summary

#### Dependency Management Checklist

```python
class DependencyBestPractices:
    """Best practices for dependency management in Calibre plugins"""
    
    CHECKLIST = [
        # 1. Assess Dependencies
        "List all required external dependencies",
        "Identify which are pure Python vs binary",
        "Check if Calibre already includes them",
        
        # 2. Choose Strategy
        "Use standard library when possible",
        "Bundle pure Python dependencies",
        "Reimplement critical functionality",
        "Provide graceful degradation",
        
        # 3. Optimize Performance
        "Use array module for numeric data",
        "Implement caching for expensive operations",
        "Use generators for memory efficiency",
        
        # 4. Test Thoroughly
        "Test with minimal Calibre installation",
        "Test on all supported platforms",
        "Profile memory usage",
        
        # 5. Document Requirements
        "List all dependencies in README",
        "Provide installation instructions",
        "Document fallback behavior",
    ]
    
    @staticmethod
    def validate_plugin_dependencies(plugin_path: str) -> List[str]:
        """Validate plugin dependencies"""
        issues = []
        
        # Check for common problematic imports
        problematic_imports = [
            'numpy', 'scipy', 'pandas', 'tensorflow',
            'requests', 'flask', 'django'
        ]
        
        import ast
        import os
        
        for root, dirs, files in os.walk(plugin_path):
            for file in files:
                if file.endswith('.py'):
                    path = os.path.join(root, file)
                    with open(path, 'r', encoding='utf-8') as f:
                        try:
                            tree = ast.parse(f.read())
                            for node in ast.walk(tree):
                                if isinstance(node, ast.Import):
                                    for alias in node.names:
                                        if alias.name in problematic_imports:
                                            issues.append(
                                                f"{file}: imports {alias.name}"
                                            )
                        except:
                            issues.append(f"{file}: parse error")
        
        return issues
```

### Conclusions and Recommendations

1. **Pure Python First**: Always prefer pure Python implementations
2. **Bundle Wisely**: Only bundle what you need, minimize size
3. **Implement Core Features**: Don't depend on external libraries for core functionality
4. **Use Calibre Built-ins**: Leverage included libraries like lxml, BeautifulSoup
5. **Optimize for Memory**: High-dimensional data requires careful memory management
6. **Plan for Fallbacks**: Always have a fallback strategy
7. **Test Extensively**: Test on minimal Calibre installations
8. **Document Dependencies**: Be transparent about requirements and limitations

The key to successful dependency management in Calibre plugins is understanding that less is more - fewer dependencies mean fewer potential issues and broader compatibility.