"""
Vector search engine for semantic similarity search
"""

import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

# Use pure Python vector operations instead of numpy
from calibre_plugins.semantic_search.core.vector_ops import VectorOps

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

    SEMANTIC = "semantic"  # Pure vector similarity
    KEYWORD = "keyword"  # Traditional keyword search
    HYBRID = "hybrid"  # Combined semantic + keyword
    DIALECTICAL = "dialectical"  # Find oppositions
    GENEALOGICAL = "genealogical"  # Trace concept history
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
    
    # Scope-specific options
    book_ids: Optional[List[int]] = None
    excluded_book_ids: Optional[List[int]] = None
    author_filter: Optional[str] = None
    tag_filter: Optional[str] = None


class SearchEngine:
    """Main search engine for semantic search"""

    def __init__(self, repository, embedding_service, calibre_repository=None):
        """
        Initialize search engine

        Args:
            repository: Data repository for embeddings
            embedding_service: Service for generating embeddings
            calibre_repository: Calibre repository for book metadata
        """
        self.repository = repository
        self.embedding_service = embedding_service
        self.calibre_repository = calibre_repository
        self._metadata_cache = {}  # Cache for book metadata

    async def search(self, query: str, options: SearchOptions, timeout: Optional[float] = 30.0) -> List[SearchResult]:
        """
        Perform semantic search with timeout support

        Args:
            query: Search query text
            options: Search configuration
            timeout: Maximum time in seconds (None for no timeout)

        Returns:
            List of search results
            
        Raises:
            asyncio.TimeoutError: If search takes longer than timeout
            asyncio.CancelledError: If search is cancelled
        """
        # Validate query
        if not query or not query.strip():
            return []

        # Apply timeout if specified
        if timeout:
            return await asyncio.wait_for(self._search_internal(query, options), timeout=timeout)
        else:
            return await self._search_internal(query, options)

    async def _search_internal(self, query: str, options: SearchOptions) -> List[SearchResult]:
        """
        Internal search method that can be cancelled/timed out

        Args:
            query: Search query text
            options: Search configuration

        Returns:
            List of search results
        """
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

    async def search_with_progress(self, query: str, options: SearchOptions, 
                                 progress_callback=None, timeout: Optional[float] = 30.0) -> List[SearchResult]:
        """
        Perform search with progress feedback and early stopping capability
        
        Args:
            query: Search query text
            options: Search configuration  
            progress_callback: Function to call with progress updates
            timeout: Maximum time in seconds
            
        Returns:
            List of search results
        """
        def report_progress(message: str):
            if progress_callback:
                progress_callback(message)
        
        try:
            report_progress("Starting search...")
            
            # Apply timeout
            if timeout:
                return await asyncio.wait_for(
                    self._search_with_progress_internal(query, options, report_progress), 
                    timeout=timeout
                )
            else:
                return await self._search_with_progress_internal(query, options, report_progress)
                
        except asyncio.TimeoutError:
            report_progress("Search timed out")
            raise
        except asyncio.CancelledError:
            report_progress("Search cancelled")
            raise
    
    async def _search_with_progress_internal(self, query: str, options: SearchOptions, report_progress) -> List[SearchResult]:
        """Internal search with progress reporting"""
        
        report_progress("Generating query embedding...")
        
        # Generate query embedding  
        query_embedding = await self.embedding_service.generate_embedding(query)
        
        report_progress("Searching vector database...")
        
        # Build filters
        filters = self._build_scope_filters(options)
        
        # Perform search with early stopping potential
        raw_results = await self.repository.search_similar(
            embedding=query_embedding,
            limit=options.limit * 3,  # Get extra for quality filtering
            filters=filters,
        )
        
        report_progress(f"Found {len(raw_results)} potential matches...")
        
        # Filter and rank results
        report_progress("Filtering and ranking results...")
        
        results = []
        high_quality_count = 0
        
        for result in raw_results:
            # Check for cancellation periodically
            if not asyncio.current_task() or asyncio.current_task().cancelled():
                raise asyncio.CancelledError()
                
            # Enrich with metadata from Calibre
            book_id = result.get("book_id", 0)
            enriched_result = self._enrich_with_metadata(book_id, result)
            
            # Convert to SearchResult
            search_result = SearchResult(
                chunk_id=result.get("chunk_id", 0),
                book_id=book_id,
                book_title=enriched_result.get("title", "Unknown"),
                authors=enriched_result.get("authors", ["Unknown Author"]),
                chunk_text=result.get("chunk_text", ""),
                chunk_index=result.get("chunk_index", 0),
                similarity_score=result.get("similarity", 0.0),
                metadata=result.get("metadata", {})
            )
            
            results.append(search_result)
            
            # Early stopping: if we have enough high-quality results, stop processing
            if search_result.similarity_score > 0.8:
                high_quality_count += 1
                if high_quality_count >= options.limit and len(results) >= options.limit:
                    report_progress(f"Found {high_quality_count} high-quality matches, stopping early")
                    break
        
        # Sort by similarity score
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        
        # Limit results
        final_results = results[:options.limit]
        
        report_progress(f"Search complete: {len(final_results)} results")
        
        return final_results

    async def _semantic_search(
        self, query: str, options: SearchOptions
    ) -> List[SearchResult]:
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
            filters=filters,
        )

        # Convert to SearchResult objects
        results = []
        for row in raw_results:
            # Apply similarity threshold
            if row["similarity"] < options.similarity_threshold:
                continue

            # Validate chunk text isn't binary data
            chunk_text = row.get("chunk_text", "")
            if chunk_text.startswith('PK\x03\x04') or chunk_text.startswith('PK'):
                logger.warning(f"Skipping result with binary data for book {row['book_id']}, chunk {row['chunk_id']}")
                continue
            
            # Enrich with metadata from Calibre
            book_id = row["book_id"]
            enriched_row = self._enrich_with_metadata(book_id, row)
            
            result = SearchResult(
                chunk_id=row["chunk_id"],
                book_id=book_id,
                book_title=enriched_row.get("title", "Unknown"),
                authors=enriched_row.get("authors", ["Unknown Author"]),
                chunk_text=chunk_text,
                chunk_index=row.get("chunk_index", 0),
                similarity_score=row["similarity"],
                metadata=row.get("metadata", {}),
            )

            # Add context if requested
            if options.include_context:
                result.chunk_text = self._add_context(result, options.context_size)

            results.append(result)

            if len(results) >= options.limit:
                break

        return results

    async def _dialectical_search(
        self, query: str, options: SearchOptions
    ) -> List[SearchResult]:
        """Search for dialectical oppositions"""
        logger.info(f"Dialectical search for: {query[:50]}...")

        # First, get semantic results
        semantic_results = await self._semantic_search(query, options)

        # Known dialectical pairs
        dialectical_pairs = {
            "being": ["nothing", "nothingness", "non-being"],
            "presence": ["absence", "lack"],
            "master": ["slave", "servant"],
            "thesis": ["antithesis"],
            "self": ["other"],
            "subject": ["object"],
            "mind": ["body", "matter"],
            "freedom": ["necessity", "determinism"],
            "individual": ["collective", "society"],
            "reason": ["emotion", "passion"],
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
                    result.metadata["dialectical"] = True
                    result.metadata["opposition_to"] = query

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

        return unique_results[: options.limit]

    async def _genealogical_search(
        self, query: str, options: SearchOptions
    ) -> List[SearchResult]:
        """Search for concept genealogy across time"""
        logger.info(f"Genealogical search for: {query[:50]}...")

        # Get semantic results
        results = await self._semantic_search(query, options)

        # Sort by publication date if available
        def get_date(result):
            # Try to extract date from metadata
            if "pubdate" in result.metadata:
                return result.metadata["pubdate"]
            # Try to parse from book title (e.g., "Being and Time (1927)")
            import re

            match = re.search(r"\((\d{4})\)", result.book_title)
            if match:
                return int(match.group(1))
            return 9999  # Unknown dates last

        results.sort(key=get_date)

        # Add genealogical metadata
        for i, result in enumerate(results):
            result.metadata["genealogy_order"] = i
            result.metadata["genealogy_date"] = get_date(result)

        return results

    async def _hybrid_search(
        self, query: str, options: SearchOptions
    ) -> List[SearchResult]:
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
                "result": result,
                "semantic_score": result.similarity_score,
                "keyword_score": 0,
            }

        for result in keyword_results:
            if result.chunk_id in score_map:
                score_map[result.chunk_id]["keyword_score"] = result.similarity_score
            else:
                score_map[result.chunk_id] = {
                    "result": result,
                    "semantic_score": 0,
                    "keyword_score": result.similarity_score,
                }

        # Calculate combined scores
        combined_results = []
        for chunk_id, scores in score_map.items():
            result = scores["result"]
            result.similarity_score = (
                semantic_weight * scores["semantic_score"]
                + keyword_weight * scores["keyword_score"]
            )
            result.metadata["search_mode"] = "hybrid"
            combined_results.append(result)

        # Sort by combined score
        combined_results.sort(key=lambda x: x.similarity_score, reverse=True)

        return combined_results[: options.limit]

    async def _keyword_search(
        self, query: str, options: SearchOptions
    ) -> List[SearchResult]:
        """Traditional keyword search (placeholder)"""
        # This would integrate with Calibre's existing search
        # For now, return empty list
        return []

    def _build_scope_filters(self, options: SearchOptions) -> Dict[str, Any]:
        """Build database filters based on search scope"""
        filters = options.filters or {}

        # Handle scope-specific filtering
        if options.scope == SearchScope.CURRENT_BOOK:
            if "book_id" in filters:
                filters["book_ids"] = [filters["book_id"]]

        elif options.scope == SearchScope.SELECTED_BOOKS:
            if options.book_ids:
                filters["book_ids"] = options.book_ids
            elif "book_ids" not in filters:
                filters["book_ids"] = []

        elif options.scope == SearchScope.AUTHOR:
            if options.author_filter:
                filters["author"] = options.author_filter
            elif "author" not in filters:
                filters["author"] = []

        elif options.scope == SearchScope.TAG:
            if options.tag_filter:
                filters["tags"] = options.tag_filter
            elif "tags" not in filters:
                filters["tags"] = []

        # Handle excluded books (for similarity search)
        if options.excluded_book_ids:
            filters["excluded_book_ids"] = options.excluded_book_ids

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
            similarity_threshold=0.5,  # Lower threshold for similarity search
        )

        raw_results = await self.repository.search_similar(
            embedding=chunk_data["embedding"],
            limit=limit + 1,  # +1 to exclude self
            filters={},
        )

        # Convert to SearchResults, excluding self
        results = []
        for row in raw_results:
            if row["chunk_id"] == chunk_id:
                continue

            results.append(
                SearchResult(
                    chunk_id=row["chunk_id"],
                    book_id=row["book_id"],
                    book_title=row.get("title", "Unknown"),
                    authors=row.get("authors", []),
                    chunk_text=row["chunk_text"],
                    chunk_index=row.get("chunk_index", 0),
                    similarity_score=row["similarity"],
                    metadata=row.get("metadata", {}),
                )
            )

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
            explanation += (
                "Using semantic similarity to find conceptually related passages.\n"
            )
        elif options.mode == SearchMode.DIALECTICAL:
            explanation += "Looking for dialectical oppositions and tensions.\n"
        elif options.mode == SearchMode.GENEALOGICAL:
            explanation += "Tracing the historical development of concepts.\n"

        explanation += f"\nScope: {options.scope.value}\n"
        explanation += f"Similarity threshold: {options.similarity_threshold}\n"
        explanation += f"Maximum results: {options.limit}"

        return explanation

    def _enrich_with_metadata(self, book_id: int, raw_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich raw search result with metadata from Calibre repository
        
        Args:
            book_id: Book ID to fetch metadata for
            raw_result: Raw search result from embedding repository
            
        Returns:
            Enriched result with title, authors, and other metadata
        """
        # Start with the raw result
        enriched = raw_result.copy()
        
        # If we have a calibre repository, fetch metadata
        if self.calibre_repository:
            # Check cache first
            if book_id in self._metadata_cache:
                metadata = self._metadata_cache[book_id]
            else:
                try:
                    metadata = self.calibre_repository.get_book_metadata(book_id)
                    self._metadata_cache[book_id] = metadata  # Cache the result
                except Exception as e:
                    logger.warning(f"Failed to fetch metadata for book {book_id}: {e}")
                    metadata = None
                    self._metadata_cache[book_id] = None  # Cache the failure
            
            if metadata:
                enriched['title'] = metadata.get('title', 'Unknown')
                enriched['authors'] = metadata.get('authors', ['Unknown Author'])
                # Ensure authors is always a list
                if isinstance(enriched['authors'], str):
                    enriched['authors'] = [enriched['authors']]
                elif not enriched['authors']:
                    enriched['authors'] = ['Unknown Author']
            else:
                enriched['title'] = f'Book {book_id}'
                enriched['authors'] = ['Unknown Author']
        else:
            # No calibre repository available, use defaults
            if 'title' not in enriched:
                enriched['title'] = f'Book {book_id}'
            if 'authors' not in enriched:
                enriched['authors'] = ['Unknown Author']
                
        return enriched
