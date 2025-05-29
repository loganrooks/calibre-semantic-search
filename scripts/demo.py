#!/usr/bin/env python3
"""
Demo script showing how the semantic search components work together
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from calibre_plugins.semantic_search.core.text_processor import (
    TextProcessor, Chunk
)
from calibre_plugins.semantic_search.core.embedding_service import (
    EmbeddingService, MockProvider
)
from calibre_plugins.semantic_search.core.search_engine import (
    SearchEngine, SearchOptions, SearchMode
)


def demo_text_processing():
    """Demonstrate text processing capabilities"""
    print("=== Text Processing Demo ===\n")
    
    # Sample philosophical text
    text = """
    The question of Being has today been forgotten. Even though in our time we deem 
    it progressive to give our approval to 'metaphysics' again, it is held that we 
    have been exempted from the exertions of a newly rekindled gigantomachie peri 
    tes ousias. Yet the question we are touching upon is not just any question. It 
    is one which provided a stimulus for the researches of Plato and Aristotle, only 
    to subside from then on as a theme for actual investigation.
    
    What these two men achieved was to persist through many alterations and 
    'retouchings' down to the 'logic' of Hegel. And what they wrested with the utmost 
    intellectual effort from the phenomena, fragmentary and incipient though it was, 
    has long since become trivialized.
    
    Not only that. On the basis of the Greeks' initial contributions towards an 
    interpretation of Being, a dogma has been developed which not only declares the 
    question about the meaning of Being to be superfluous, but sanctions its complete 
    neglect.
    """
    
    # Create text processor
    processor = TextProcessor(strategy='philosophical')
    
    # Process text into chunks
    chunks = processor.chunk_text(text, metadata={
        'book_id': 1,
        'title': 'Being and Time',
        'authors': ['Martin Heidegger']
    })
    
    print(f"Text split into {len(chunks)} chunks:\n")
    
    for i, chunk in enumerate(chunks):
        print(f"Chunk {i + 1}:")
        print(f"  Text: {chunk.text[:100]}...")
        print(f"  Tokens: ~{chunk.token_count}")
        print(f"  Position: {chunk.start_pos}-{chunk.end_pos}")
        print()


def demo_embedding_service():
    """Demonstrate embedding service"""
    print("\n=== Embedding Service Demo ===\n")
    
    # Create mock providers
    primary = MockProvider(dimensions=768, fail=False)
    fallback = MockProvider(dimensions=768, fail=False)
    
    # Create service with fallback
    service = EmbeddingService(providers=[primary, fallback])
    
    # Generate embedding
    import asyncio
    
    async def generate():
        text = "What is the meaning of Being?"
        embedding = await service.generate_embedding(text)
        
        print(f"Generated embedding for: '{text}'")
        print(f"Embedding shape: {embedding.shape}")
        print(f"Embedding sample: {embedding[:5]}...")
        print(f"Used provider: {service.last_provider.get_model_name()}")
        
        # Test batch generation
        texts = [
            "Being and Time",
            "Dasein is being-in-the-world",
            "The ontological difference"
        ]
        
        embeddings = await service.generate_batch(texts)
        print(f"\nBatch generated {len(embeddings)} embeddings")
    
    # Run async function
    asyncio.run(generate())


def demo_search_modes():
    """Demonstrate different search modes"""
    print("\n=== Search Modes Demo ===\n")
    
    # Search modes available
    modes = [
        (SearchMode.SEMANTIC, "Find conceptually similar passages"),
        (SearchMode.DIALECTICAL, "Find opposing concepts"),
        (SearchMode.GENEALOGICAL, "Trace concept evolution"),
    ]
    
    for mode, description in modes:
        print(f"{mode.value}: {description}")
        
    print("\nExample dialectical pairs:")
    pairs = [
        ("Being", "Nothing"),
        ("Presence", "Absence"),
        ("Master", "Slave"),
        ("Self", "Other")
    ]
    
    for concept1, concept2 in pairs:
        print(f"  {concept1} ←→ {concept2}")


def demo_chunking_strategies():
    """Demonstrate different chunking strategies"""
    print("\n=== Chunking Strategies Demo ===\n")
    
    sample_text = """First, let us consider the nature of consciousness. 
    Second, we must examine how consciousness relates to being. 
    Therefore, consciousness and being are fundamentally intertwined.
    
    This is a separate paragraph discussing time and temporality."""
    
    strategies = ['paragraph', 'sliding_window', 'philosophical']
    
    for strategy in strategies:
        processor = TextProcessor(strategy=strategy)
        chunks = processor.chunk_text(sample_text)
        
        print(f"\n{strategy.upper()} Strategy:")
        print(f"  Number of chunks: {len(chunks)}")
        for i, chunk in enumerate(chunks):
            print(f"  Chunk {i+1}: {chunk.text[:50]}...")


if __name__ == "__main__":
    print("Calibre Semantic Search - Component Demo\n")
    
    demo_text_processing()
    demo_embedding_service()
    demo_search_modes()
    demo_chunking_strategies()
    
    print("\n✓ Demo complete!")
    print("\nThese components work together to enable:")
    print("- Intelligent text chunking that preserves philosophical arguments")
    print("- Robust embedding generation with fallback support")
    print("- Advanced search modes for philosophical research")
    print("- Flexible configuration for different use cases")