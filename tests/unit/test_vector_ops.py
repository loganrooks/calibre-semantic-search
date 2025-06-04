"""
Test vector operations module
Following TDD principles - these tests verify VectorOps functionality
"""

import math
import struct
import array
import pytest
from typing import List

# Import VectorOps directly without going through the plugin hierarchy
import sys
from pathlib import Path
import importlib.util

# Load the module directly to avoid circular imports
vector_ops_path = Path(__file__).parent.parent.parent / "calibre_plugins" / "semantic_search" / "core" / "vector_ops.py"
spec = importlib.util.spec_from_file_location("vector_ops", vector_ops_path)
vector_ops_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vector_ops_module)

# Extract what we need
VectorOps = vector_ops_module.VectorOps
Vector = vector_ops_module.Vector


class TestVectorOps:
    """Test pure Python vector operations"""
    
    def test_create_vector(self):
        """Test vector creation from list"""
        data = [1.0, 2.0, 3.0]
        vec = VectorOps.create_vector(data)
        
        assert isinstance(vec, array.array)
        assert vec.typecode == 'd'  # double precision
        assert list(vec) == data
    
    def test_zeros_vector(self):
        """Test creating zero vector"""
        vec = VectorOps.zeros(5)
        
        assert len(vec) == 5
        assert all(x == 0.0 for x in vec)
    
    def test_ones_vector(self):
        """Test creating ones vector"""
        vec = VectorOps.ones(5)
        
        assert len(vec) == 5
        assert all(x == 1.0 for x in vec)
    
    def test_dot_product(self):
        """Test dot product calculation"""
        v1 = [1.0, 2.0, 3.0]
        v2 = [4.0, 5.0, 6.0]
        
        result = VectorOps.dot(v1, v2)
        expected = 1*4 + 2*5 + 3*6  # 32.0
        
        assert result == expected
    
    def test_dot_product_with_arrays(self):
        """Test dot product with array.array objects"""
        v1 = array.array('d', [1.0, 2.0, 3.0])
        v2 = array.array('d', [4.0, 5.0, 6.0])
        
        result = VectorOps.dot(v1, v2)
        assert result == 32.0
    
    def test_norm_l2(self):
        """Test L2 (Euclidean) norm"""
        vec = [3.0, 4.0]  # 3-4-5 triangle
        
        result = VectorOps.norm(vec, ord=2)
        assert result == 5.0
    
    def test_norm_l1(self):
        """Test L1 (Manhattan) norm"""
        vec = [3.0, -4.0]
        
        result = VectorOps.norm(vec, ord=1)
        assert result == 7.0  # |3| + |-4|
    
    def test_norm_linf(self):
        """Test L-infinity norm"""
        vec = [3.0, -4.0, 2.0]
        
        result = VectorOps.norm(vec, ord=float('inf'))
        assert result == 4.0  # max(|3|, |-4|, |2|)
    
    def test_normalize_vector(self):
        """Test vector normalization"""
        vec = [3.0, 4.0]
        
        result = VectorOps.normalize(vec)
        
        # Should have unit length
        assert math.isclose(VectorOps.norm(result), 1.0, rel_tol=1e-9)
        # Direction preserved
        assert math.isclose(result[0], 0.6, rel_tol=1e-9)
        assert math.isclose(result[1], 0.8, rel_tol=1e-9)
    
    def test_normalize_zero_vector(self):
        """Test normalizing zero vector"""
        vec = [0.0, 0.0, 0.0]
        
        result = VectorOps.normalize(vec)
        
        # Should return unchanged
        assert result == vec
    
    def test_cosine_similarity_orthogonal(self):
        """Test cosine similarity of orthogonal vectors"""
        v1 = [1.0, 0.0, 0.0]
        v2 = [0.0, 1.0, 0.0]
        
        result = VectorOps.cosine_similarity(v1, v2)
        
        assert math.isclose(result, 0.0, abs_tol=1e-9)
    
    def test_cosine_similarity_parallel(self):
        """Test cosine similarity of parallel vectors"""
        v1 = [1.0, 2.0, 3.0]
        v2 = [2.0, 4.0, 6.0]  # Same direction, different magnitude
        
        result = VectorOps.cosine_similarity(v1, v2)
        
        assert math.isclose(result, 1.0, rel_tol=1e-9)
    
    def test_cosine_similarity_opposite(self):
        """Test cosine similarity of opposite vectors"""
        v1 = [1.0, 2.0, 3.0]
        v2 = [-1.0, -2.0, -3.0]
        
        result = VectorOps.cosine_similarity(v1, v2)
        
        assert math.isclose(result, -1.0, rel_tol=1e-9)
    
    def test_cosine_similarity_zero_vector(self):
        """Test cosine similarity with zero vector"""
        v1 = [1.0, 2.0, 3.0]
        v2 = [0.0, 0.0, 0.0]
        
        result = VectorOps.cosine_similarity(v1, v2)
        
        assert result == 0.0
    
    def test_euclidean_distance(self):
        """Test Euclidean distance calculation"""
        v1 = [1.0, 2.0]
        v2 = [4.0, 6.0]
        
        result = VectorOps.euclidean_distance(v1, v2)
        expected = 5.0  # 3-4-5 triangle
        
        assert math.isclose(result, expected, rel_tol=1e-9)
    
    def test_manhattan_distance(self):
        """Test Manhattan distance calculation"""
        v1 = [1.0, 2.0]
        v2 = [4.0, 6.0]
        
        result = VectorOps.manhattan_distance(v1, v2)
        expected = 7.0  # |4-1| + |6-2|
        
        assert result == expected
    
    def test_vector_addition(self):
        """Test vector addition"""
        v1 = [1.0, 2.0, 3.0]
        v2 = [4.0, 5.0, 6.0]
        
        result = VectorOps.add(v1, v2)
        expected = [5.0, 7.0, 9.0]
        
        assert result == expected
    
    def test_vector_subtraction(self):
        """Test vector subtraction"""
        v1 = [4.0, 5.0, 6.0]
        v2 = [1.0, 2.0, 3.0]
        
        result = VectorOps.subtract(v1, v2)
        expected = [3.0, 3.0, 3.0]
        
        assert result == expected
    
    def test_scalar_multiplication(self):
        """Test scalar multiplication"""
        vec = [1.0, 2.0, 3.0]
        scalar = 2.5
        
        result = VectorOps.multiply(vec, scalar)
        expected = [2.5, 5.0, 7.5]
        
        assert result == expected
    
    def test_mean_vector(self):
        """Test mean vector calculation"""
        vectors = [
            [1.0, 2.0, 3.0],
            [4.0, 5.0, 6.0],
            [7.0, 8.0, 9.0]
        ]
        
        result = VectorOps.mean(vectors)
        expected = [4.0, 5.0, 6.0]
        
        assert result == expected
    
    def test_mean_vector_empty(self):
        """Test mean of empty vector list"""
        result = VectorOps.mean([])
        assert result == []
    
    def test_pack_embedding_list(self):
        """Test packing list to binary"""
        embedding = [1.0, 2.0, 3.0]
        
        packed = VectorOps.pack_embedding(embedding)
        
        # Should be 3 floats * 4 bytes each = 12 bytes
        assert len(packed) == 12
        assert isinstance(packed, bytes)
    
    def test_pack_embedding_array(self):
        """Test packing array to binary"""
        embedding = array.array('d', [1.0, 2.0, 3.0])
        
        packed = VectorOps.pack_embedding(embedding)
        
        # Converted to float32, so 12 bytes
        assert len(packed) == 12
        assert isinstance(packed, bytes)
    
    def test_unpack_embedding(self):
        """Test unpacking binary to list"""
        # Pack some data first
        original = [1.0, 2.0, 3.0]
        packed = struct.pack('3f', *original)
        
        unpacked = VectorOps.unpack_embedding(packed, 3)
        
        assert len(unpacked) == 3
        assert all(math.isclose(a, b, rel_tol=1e-6) for a, b in zip(unpacked, original))
    
    def test_pack_unpack_roundtrip(self):
        """Test packing and unpacking preserves values"""
        original = [1.5, 2.7, 3.9, 4.2, 5.1]
        
        packed = VectorOps.pack_embedding(original)
        unpacked = VectorOps.unpack_embedding(packed, len(original))
        
        # Float32 has less precision than float64
        assert all(math.isclose(a, b, rel_tol=1e-6) for a, b in zip(unpacked, original))
    
    def test_batch_cosine_similarity(self):
        """Test batch cosine similarity calculation"""
        query = [1.0, 0.0, 0.0]
        embeddings = [
            [1.0, 0.0, 0.0],  # Same as query
            [0.0, 1.0, 0.0],  # Orthogonal
            [-1.0, 0.0, 0.0], # Opposite
        ]
        
        results = VectorOps.batch_cosine_similarity(query, embeddings)
        
        assert len(results) == 3
        assert math.isclose(results[0], 1.0, rel_tol=1e-9)   # Same
        assert math.isclose(results[1], 0.0, abs_tol=1e-9)   # Orthogonal
        assert math.isclose(results[2], -1.0, rel_tol=1e-9)  # Opposite
    
    def test_batch_cosine_similarity_zero_query(self):
        """Test batch similarity with zero query"""
        query = [0.0, 0.0, 0.0]
        embeddings = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]
        
        results = VectorOps.batch_cosine_similarity(query, embeddings)
        
        assert all(x == 0.0 for x in results)
    
    def test_top_k_similar(self):
        """Test finding top-k similar vectors"""
        query = [1.0, 0.0, 0.0]
        embeddings = [
            (1, [0.0, 1.0, 0.0]),    # Orthogonal
            (2, [1.0, 0.0, 0.0]),    # Same
            (3, [0.8, 0.6, 0.0]),    # Similar
            (4, [-1.0, 0.0, 0.0]),   # Opposite
        ]
        
        results = VectorOps.top_k_similar(query, embeddings, k=2)
        
        assert len(results) == 2
        assert results[0][0] == 2  # ID of most similar
        assert math.isclose(results[0][1], 1.0, rel_tol=1e-9)
        assert results[1][0] == 3  # ID of second most similar
        assert math.isclose(results[1][1], 0.8, rel_tol=1e-9)
    
    def test_top_k_similar_exceeds_available(self):
        """Test top-k when k exceeds available vectors"""
        query = [1.0, 0.0, 0.0]
        embeddings = [(1, [1.0, 0.0, 0.0]), (2, [0.0, 1.0, 0.0])]
        
        results = VectorOps.top_k_similar(query, embeddings, k=5)
        
        assert len(results) == 2  # Only 2 available


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])