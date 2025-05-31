"""
Pure Python vector operations for Calibre plugin
Replaces numpy functionality with standard library implementations
"""

import math
import array
import struct
import operator
from typing import List, Union, Optional, Tuple

# Type alias for vectors
Vector = Union[List[float], array.array]


class VectorOps:
    """
    Pure Python implementation of vector operations
    optimized for performance and memory efficiency
    """
    
    @staticmethod
    def create_vector(data: List[float], dtype: str = 'd') -> array.array:
        """
        Create an efficient vector representation using array module
        
        Args:
            data: List of float values
            dtype: Array type code ('d' for double, 'f' for float)
            
        Returns:
            array.array object
        """
        return array.array(dtype, data)
    
    @staticmethod
    def zeros(size: int, dtype: str = 'd') -> array.array:
        """Create zero vector"""
        return array.array(dtype, [0.0] * size)
    
    @staticmethod
    def ones(size: int, dtype: str = 'd') -> array.array:
        """Create ones vector"""
        return array.array(dtype, [1.0] * size)
    
    @staticmethod
    def dot(v1: Vector, v2: Vector) -> float:
        """
        Optimized dot product of two vectors
        
        Args:
            v1: First vector
            v2: Second vector
            
        Returns:
            Dot product value
        """
        # Fast path for arrays
        if isinstance(v1, array.array) and isinstance(v2, array.array):
            return sum(map(operator.mul, v1, v2))
        
        # General case
        return sum(a * b for a, b in zip(v1, v2))
    
    @staticmethod
    def norm(v: Vector, ord: Union[int, float] = 2) -> float:
        """
        Vector norm (L1, L2, Linf)
        
        Args:
            v: Input vector
            ord: Order of norm (1, 2, inf)
            
        Returns:
            Norm value
        """
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
        """
        Normalize vector to unit length
        
        Args:
            v: Input vector
            
        Returns:
            Normalized vector as list
        """
        norm = VectorOps.norm(v)
        if norm == 0:
            return list(v)
        return [x / norm for x in v]
    
    @staticmethod
    def cosine_similarity(v1: Vector, v2: Vector) -> float:
        """
        Cosine similarity between two vectors
        
        Args:
            v1: First vector
            v2: Second vector
            
        Returns:
            Cosine similarity value between -1 and 1
        """
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
        """
        Compute mean vector from a list of vectors
        
        Args:
            vectors: List of vectors
            
        Returns:
            Mean vector
        """
        if not vectors:
            return []
        
        n = len(vectors)
        dim = len(vectors[0])
        
        result = [0.0] * dim
        for vec in vectors:
            for i, val in enumerate(vec):
                result[i] += val
        
        return [x / n for x in result]
    
    @staticmethod
    def pack_embedding(embedding: Vector) -> bytes:
        """
        Pack embedding vector to binary format for storage
        
        Args:
            embedding: Vector to pack
            
        Returns:
            Binary representation
        """
        # Use float32 (4 bytes) for compatibility with SQLite vec
        if isinstance(embedding, array.array):
            # Convert to float32 array first
            if embedding.typecode != 'f':
                embedding = array.array('f', embedding)
            return embedding.tobytes()
        else:
            # Convert list to binary using float32
            return struct.pack(f'{len(embedding)}f', *embedding)
    
    @staticmethod
    def unpack_embedding(data: bytes, dimension: int) -> List[float]:
        """
        Unpack binary data to embedding vector
        
        Args:
            data: Binary data
            dimension: Expected vector dimension
            
        Returns:
            List of float values
        """
        # Unpack as float32
        return list(struct.unpack(f'{dimension}f', data))
    
    @staticmethod
    def batch_cosine_similarity(query: Vector, embeddings: List[Vector]) -> List[float]:
        """
        Compute cosine similarity between query and multiple embeddings
        
        Args:
            query: Query vector
            embeddings: List of embedding vectors
            
        Returns:
            List of similarity scores
        """
        # Pre-normalize query for efficiency
        query_norm = VectorOps.norm(query)
        if query_norm == 0:
            return [0.0] * len(embeddings)
        
        normalized_query = [x / query_norm for x in query]
        
        similarities = []
        for embedding in embeddings:
            emb_norm = VectorOps.norm(embedding)
            if emb_norm == 0:
                similarities.append(0.0)
            else:
                # Since query is pre-normalized, just dot product and divide by embedding norm
                dot_prod = sum(q * e for q, e in zip(normalized_query, embedding))
                similarities.append(dot_prod / emb_norm)
        
        return similarities
    
    @staticmethod
    def top_k_similar(query: Vector, embeddings: List[Tuple[int, Vector]], k: int = 10) -> List[Tuple[int, float]]:
        """
        Find top-k most similar embeddings to query
        
        Args:
            query: Query vector
            embeddings: List of (id, vector) tuples
            k: Number of top results to return
            
        Returns:
            List of (id, similarity_score) tuples, sorted by similarity
        """
        # Compute similarities
        results = []
        for idx, embedding in embeddings:
            similarity = VectorOps.cosine_similarity(query, embedding)
            results.append((idx, similarity))
        
        # Sort by similarity (descending) and return top k
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:k]


# Convenience functions for backward compatibility
def cosine_similarity(v1: Vector, v2: Vector) -> float:
    """Convenience function for cosine similarity"""
    return VectorOps.cosine_similarity(v1, v2)


def normalize_vector(v: Vector) -> List[float]:
    """Convenience function for vector normalization"""
    return VectorOps.normalize(v)