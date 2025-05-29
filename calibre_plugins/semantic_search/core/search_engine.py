"""
Vector search engine for semantic similarity search
"""

import numpy as np
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SearchScope(Enum):
    """Search scope options"""
    LIBRARY = "library"
    CURRENT_BOOK = "current_book"
    SELECTED_BOOKS = "selected_books"
    COLLECTION = "collection"
    AUTHOR = "author"
    TAG = "tag"


class SearchMode(Enum):
    """Search mode options"""
    SEMANTIC = "semantic"           # Pure vector similarity
    KEYWORD = "keyword"             # Traditional keyword search
    HYBRID = "hybrid"               # Combined semantic + keyword
    DIALECTICAL = "dialectical"     # Find oppositions
    GENEALOGICAL = "genealogical"   # Trace concept history
    PHENOMENOLOGICAL = "phenomenological"  # Essence-focused


@dataclass
class SearchResult:
    """Represents a single search result"""
    chunk_id: int
    book_id: int
    book_title: str
    authors: List[str]
    chunk_text: str
    chunk_index: int
    similarity_score: float
    metadata: Dict[str, Any]
    
    @property
    def citation(self) -> str:
        """Generate citation for this result"""
        author_str = ", ".join(self.authors) if self.authors else "Unknown"
        return f"{author_str}. {self.book_title}."


@dataclass
class SearchOptions:
    """Search configuration options"""
    scope: SearchScope = SearchScope.LIBRARY
    mode: SearchMode = SearchMode.SEMANTIC
    limit: int = 20
    similarity_threshold: float = 0.7
    filters: Optional[Dict[str, Any]] = None
    include_context: bool = True
    context_size: int = 500  # characters before/after


class SearchEngine:
    """Main search engine for semantic search"""
    
    def __init__(self, repository, embedding_service):
        """
        Initialize search engine
        
        Args:
            repository: Data repository for embeddings
            embedding_service: Service for generating embeddings
        """
        self.repository = repository
        self.embedding_service = embedding_service
        
    async def search(self, query: str, options: SearchOptions) -> List[SearchResult]:
        """
        Perform semantic search
        
        Args:
            query: Search query text
            options: Search configuration
            
        Returns:
            List of search results
        """
        # Validate query
        if not query or not query.strip():
            return []
            
        # Route to appropriate search method
        if options.mode == SearchMode.SEMANTIC:
            return await self._semantic_search(query, options)
        elif options.mode == SearchMode.DIALECTICAL:
            return await self._dialectical_search(query, options)
        elif options.mode == SearchMode.GENEALOGICAL:
            return await self._genealogical_search(query, options)
        elif options.mode == SearchMode.HYBRID:
            return await self._hybrid_search(query, options)
        else:
            # Default to semantic
            return await self._semantic_search(query, options)
            
    async def _semantic_search(self, query: str, options: SearchOptions) -> List[SearchResult]:
        """Pure semantic similarity search"""
        logger.info(f"Semantic search for: {query[:50]}...")
        
        # Generate query embedding
        query_embedding = await self.embedding_service.generate_embedding(query)
        
        # Build filters based on scope
        filters = self._build_scope_filters(options)
        
        # Perform vector search
        raw_results = await self.repository.search_similar(
            embedding=query_embedding,
            limit=options.limit * 2,  # Get extra for filtering
            filters=filters
        )
        
        # Convert to SearchResult objects
        results = []
        for row in raw_results:
            # Apply similarity threshold
            if row['similarity'] < options.similarity_threshold:
                continue
                
            result = SearchResult(
                chunk_id=row['chunk_id'],
                book_id=row['book_id'],
                book_title=row.get('title', 'Unknown'),
                authors=row.get('authors', []),
                chunk_text=row['chunk_text'],
                chunk_index=row.get('chunk_index', 0),
                similarity_score=row['similarity'],
                metadata=row.get('metadata', {})
            )
            
            # Add context if requested
            if options.include_context:
                result.chunk_text = self._add_context(result, options.context_size)
                
            results.append(result)
            
            if len(results) >= options.limit:
                break
                
        return results
        
    async def _dialectical_search(self, query: str, options: SearchOptions) -> List[SearchResult]:
        """Search for dialectical oppositions"""
        logger.info(f"Dialectical search for: {query[:50]}...")
        
        # First, get semantic results
        semantic_results = await self._semantic_search(query, options)
        
        # Known dialectical pairs
        dialectical_pairs = {
            'being': ['nothing', 'nothingness', 'non-being'],
            'presence': ['absence', 'lack'],
            'master': ['slave', 'servant'],
            'thesis': ['antithesis'],
            'self': ['other'],
            'subject': ['object'],
            'mind': ['body', 'matter'],
            'freedom': ['necessity', 'determinism'],
            'individual': ['collective', 'society'],
            'reason': ['emotion', 'passion'],
        }
        
        # Check if query matches known pairs
        query_lower = query.lower()
        opposites = []
        
        for concept, oppositions in dialectical_pairs.items():
            if concept in query_lower:
                opposites.extend(oppositions)
            elif any(opp in query_lower for opp in oppositions):
                opposites.append(concept)
                
        # Search for opposites
        if opposites:
            for opposite in opposites[:3]:  # Limit to avoid too many searches
                opp_results = await self._semantic_search(opposite, options)
                
                # Mark as dialectical results
                for result in opp_results:
                    result.metadata['dialectical'] = True
                    result.metadata['opposition_to'] = query
                    
                semantic_results.extend(opp_results)
                
        # Re-sort by relevance
        semantic_results.sort(key=lambda x: x.similarity_score, reverse=True)
        
        # Remove duplicates
        seen = set()
        unique_results = []
        for result in semantic_results:
            if result.chunk_id not in seen:
                seen.add(result.chunk_id)
                unique_results.append(result)
                
        return unique_results[:options.limit]
        
    async def _genealogical_search(self, query: str, options: SearchOptions) -> List[SearchResult]:
        """Search for concept genealogy across time"""
        logger.info(f"Genealogical search for: {query[:50]}...")
        
        # Get semantic results
        results = await self._semantic_search(query, options)
        
        # Sort by publication date if available
        def get_date(result):
            # Try to extract date from metadata
            if 'pubdate' in result.metadata:
                return result.metadata['pubdate']
            # Try to parse from book title (e.g., "Being and Time (1927)")
            import re
            match = re.search(r'\((\d{4})\)', result.book_title)
            if match:
                return int(match.group(1))
            return 9999  # Unknown dates last
            
        results.sort(key=get_date)
        
        # Add genealogical metadata
        for i, result in enumerate(results):
            result.metadata['genealogy_order'] = i
            result.metadata['genealogy_date'] = get_date(result)
            
        return results
        
    async def _hybrid_search(self, query: str, options: SearchOptions) -> List[SearchResult]:
        """Combined semantic and keyword search"""
        logger.info(f"Hybrid search for: {query[:50]}...")
        
        # Get semantic results
        semantic_results = await self._semantic_search(query, options)
        
        # Get keyword results
        keyword_results = await self._keyword_search(query, options)
        
        # Merge results with weighting
        semantic_weight = 0.7
        keyword_weight = 0.3
        
        # Create combined score map
        score_map = {}
        
        for result in semantic_results:
            score_map[result.chunk_id] = {
                'result': result,
                'semantic_score': result.similarity_score,
                'keyword_score': 0
            }
            
        for result in keyword_results:
            if result.chunk_id in score_map:
                score_map[result.chunk_id]['keyword_score'] = result.similarity_score
            else:
                score_map[result.chunk_id] = {
                    'result': result,
                    'semantic_score': 0,
                    'keyword_score': result.similarity_score
                }
                
        # Calculate combined scores
        combined_results = []
        for chunk_id, scores in score_map.items():
            result = scores['result']
            result.similarity_score = (
                semantic_weight * scores['semantic_score'] +
                keyword_weight * scores['keyword_score']
            )
            result.metadata['search_mode'] = 'hybrid'
            combined_results.append(result)
            
        # Sort by combined score
        combined_results.sort(key=lambda x: x.similarity_score, reverse=True)
        
        return combined_results[:options.limit]
        
    async def _keyword_search(self, query: str, options: SearchOptions) -> List[SearchResult]:
        """Traditional keyword search (placeholder)"""
        # This would integrate with Calibre's existing search
        # For now, return empty list
        return []
        
    def _build_scope_filters(self, options: SearchOptions) -> Dict[str, Any]:
        """Build database filters based on search scope"""
        filters = options.filters or {}
        
        if options.scope == SearchScope.CURRENT_BOOK:
            if 'book_id' in filters:
                filters['book_ids'] = [filters['book_id']]
                
        elif options.scope == SearchScope.SELECTED_BOOKS:
            if 'book_ids' not in filters:
                filters['book_ids'] = []
                
        elif options.scope == SearchScope.AUTHOR:
            if 'author' not in filters:
                filters['author'] = []
                
        elif options.scope == SearchScope.TAG:
            if 'tags' not in filters:
                filters['tags'] = []
                
        # LIBRARY scope has no additional filters
        
        return filters
        
    def _add_context(self, result: SearchResult, context_size: int) -> str:
        """Add surrounding context to chunk text"""
        # This would fetch surrounding text from the book
        # For now, just return the chunk text
        return result.chunk_text
        
    async def find_similar(self, chunk_id: int, limit: int = 10) -> List[SearchResult]:
        """Find chunks similar to a given chunk"""
        # Get the chunk's embedding
        chunk_data = await self.repository.get_chunk(chunk_id)
        if not chunk_data:
            return []
            
        # Search for similar
        options = SearchOptions(
            limit=limit,
            similarity_threshold=0.5  # Lower threshold for similarity search
        )
        
        raw_results = await self.repository.search_similar(
            embedding=chunk_data['embedding'],
            limit=limit + 1,  # +1 to exclude self
            filters={}
        )
        
        # Convert to SearchResults, excluding self
        results = []
        for row in raw_results:
            if row['chunk_id'] == chunk_id:
                continue
                
            results.append(SearchResult(
                chunk_id=row['chunk_id'],
                book_id=row['book_id'],
                book_title=row.get('title', 'Unknown'),
                authors=row.get('authors', []),
                chunk_text=row['chunk_text'],
                chunk_index=row.get('chunk_index', 0),
                similarity_score=row['similarity'],
                metadata=row.get('metadata', {})
            ))
            
        return results
        
    def validate_query(self, query: str) -> Tuple[bool, Optional[str]]:
        """
        Validate search query
        
        Returns:
            (is_valid, error_message)
        """
        if not query or not query.strip():
            return False, "Query cannot be empty"
            
        if len(query) < 3:
            return False, "Query too short (minimum 3 characters)"
            
        if len(query) > 5000:
            return False, "Query too long (maximum 5000 characters)"
            
        return True, None
        
    def explain_search(self, query: str, options: SearchOptions) -> str:
        """Explain how the search will work"""
        explanation = f"Searching for: '{query}'\n\n"
        
        if options.mode == SearchMode.SEMANTIC:
            explanation += "Using semantic similarity to find conceptually related passages.\n"
        elif options.mode == SearchMode.DIALECTICAL:
            explanation += "Looking for dialectical oppositions and tensions.\n"
        elif options.mode == SearchMode.GENEALOGICAL:
            explanation += "Tracing the historical development of concepts.\n"
            
        explanation += f"\nScope: {options.scope.value}\n"
        explanation += f"Similarity threshold: {options.similarity_threshold}\n"
        explanation += f"Maximum results: {options.limit}"
        
        return explanation