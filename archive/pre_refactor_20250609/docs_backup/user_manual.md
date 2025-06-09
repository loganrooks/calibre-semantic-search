# Calibre Semantic Search Plugin - User Manual

## Table of Contents
1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Getting Started](#getting-started)
5. [Search Features](#search-features)
6. [Philosophical Research Tools](#philosophical-research-tools)
7. [Tips and Best Practices](#tips-and-best-practices)
8. [Troubleshooting](#troubleshooting)

## Introduction

The Calibre Semantic Search Plugin transforms your ebook library into an AI-powered research platform. Unlike traditional keyword search, semantic search understands meaning and concepts, making it ideal for philosophical and academic research.

### Key Features
- **Semantic Search**: Find passages by meaning, not just exact words
- **Philosophy-Optimized**: Special modes for dialectical and genealogical research
- **Multi-Language**: Search across languages for the same concepts
- **Smart Chunking**: Preserves philosophical arguments and context
- **Fast Performance**: Sub-second searches on libraries with 10,000+ books

## Installation

### Requirements
- Calibre 5.0 or higher
- Python 3.8 or higher (included with Calibre)
- 500MB RAM for normal operation
- ~4.4GB storage per 1,000 indexed books

### Installation Steps

1. **Download the Plugin**
   - Download `calibre-semantic-search.zip` from the releases page

2. **Install via Calibre**
   - Open Calibre
   - Go to Preferences → Plugins
   - Click "Load plugin from file"
   - Select the downloaded ZIP file
   - Click "Apply"

3. **Restart Calibre**
   - Close and reopen Calibre to activate the plugin

4. **Verify Installation**
   - Look for the "Semantic Search" button in the toolbar
   - Check the Plugins menu for "Semantic Search"

## Configuration

### Initial Setup

1. **Open Settings**
   - Click the Semantic Search button → Settings
   - Or go to Preferences → Plugins → Semantic Search → Customize

2. **Configure Embedding Provider**
   
   The plugin supports multiple AI providers for generating embeddings:

   #### Vertex AI (Recommended)
   - Best quality embeddings for philosophical texts
   - Requires Google Cloud account
   - Set project ID in configuration
   
   #### OpenAI
   - Easy to set up
   - Good quality embeddings
   - Requires API key from OpenAI
   
   #### Cohere
   - Alternative provider
   - Good for multi-language texts
   - Requires Cohere API key
   
   #### Local Models
   - Privacy-focused (no data sent to cloud)
   - Requires local model setup (Ollama)
   - May be slower than cloud providers

3. **Enter API Credentials**
   - Select your provider
   - Enter API key or project details
   - Click "Test Connection" to verify

### Search Options

Configure default search behavior:

- **Default Result Limit**: Number of results to show (10-100)
- **Similarity Threshold**: How similar results must be (0.5-1.0)
  - 0.5 = Loosely related
  - 0.7 = Moderately similar (default)
  - 0.9 = Very similar
- **Default Scope**: Where to search (library, current book, etc.)

### Performance Settings

- **Enable Caching**: Speed up repeated searches
- **Cache Size**: Memory allocated for caching (MB)
- **Batch Size**: Number of chunks to process at once
- **Concurrent Requests**: Parallel API calls (1-10)

## Getting Started

### Indexing Your Library

Before searching, you need to index your books:

1. **Index Selected Books**
   - Select books in library view
   - Right-click → "Index for Semantic Search"
   - Or use Semantic Search → Indexing → Index Selected Books

2. **Index Entire Library**
   - Semantic Search → Indexing → Index All Books
   - This may take several hours for large libraries
   - You can continue using Calibre while indexing

3. **Monitor Progress**
   - A progress dialog shows indexing status
   - You can cancel at any time
   - Partially indexed books can still be searched

### Your First Search

1. **Open Search Dialog**
   - Click the Semantic Search button
   - Or press Ctrl+Shift+S (customizable)

2. **Enter a Query**
   - Type a concept, phrase, or passage
   - Examples:
     - "the nature of consciousness"
     - "freedom and responsibility"
     - "time and temporality in human existence"

3. **Review Results**
   - Results show as cards with:
     - Book title and author
     - Matching passage
     - Similarity score (percentage)
   - Click "View in Book" to open at that location

## Search Features

### Search Modes

#### Semantic Search (Default)
Finds conceptually similar passages based on meaning:
- Query: "existential anxiety"
- Finds: Passages about angst, dread, existential crisis, etc.

#### Dialectical Search
Finds opposing concepts and tensions:
- Query: "freedom"
- Also finds: Passages about necessity, determinism, constraint

#### Genealogical Search
Traces concept development through history:
- Query: "substance"
- Results ordered chronologically showing evolution from Aristotle to modern philosophy

#### Hybrid Search
Combines semantic and keyword matching for comprehensive results.

### Search Scope

Control where to search:

- **Entire Library**: Search all indexed books
- **Current Book**: Search only the book open in viewer
- **Selected Books**: Search specific books selected in library
- **By Author**: Search books by specific authors
- **By Tag**: Search books with certain tags
- **Custom Collection**: Search saved collections

### Advanced Options

- **Include Context**: Show surrounding text for better understanding
- **Filter by Language**: Limit to specific languages
- **Date Range**: Search books from specific time periods
- **Minimum Score**: Only show highly relevant results

## Philosophical Research Tools

### Concept Mapping

The plugin understands philosophical concepts across languages:
- Searches for "Being" also find "Sein" (German), "être" (French)
- Recognizes untranslatable terms (e.g., "Dasein", "différance")
- Maps ancient terms to modern equivalents

### Argument Detection

Smart chunking preserves philosophical arguments:
- Keeps premises and conclusions together
- Recognizes argument markers ("therefore", "hence", "it follows")
- Maintains dialectical structure

### Citation Support

Export results in academic formats:
- BibTeX for LaTeX
- Chicago/MLA/APA styles
- Include page numbers and editions
- Batch export multiple citations

### Research Collections

Save and organize search sessions:
- Create named collections of results
- Add notes and annotations
- Share collections with colleagues
- Track research progress

## Tips and Best Practices

### Effective Queries

1. **Be Conceptual**: Think in terms of ideas, not just keywords
2. **Use Natural Language**: "What is the meaning of existence?" works well
3. **Try Variations**: Different phrasings may yield different insights
4. **Explore Opposites**: Use dialectical search to find tensions

### Optimizing Results

1. **Adjust Similarity Threshold**: 
   - Lower for exploratory research
   - Higher for precise matching

2. **Use Appropriate Scope**:
   - Start broad, then narrow
   - Use author/tag filters for focused research

3. **Leverage Search Modes**:
   - Semantic for general concepts
   - Dialectical for philosophical analysis
   - Genealogical for historical research

### Performance Tips

1. **Index Strategically**:
   - Start with most important books
   - Index by collection or author
   - Re-index after major updates

2. **Manage Cache**:
   - Clear cache if results seem stale
   - Increase cache size for large libraries
   - Disable cache for testing

## Troubleshooting

### Common Issues

#### "No results found"
- Check if books are indexed
- Lower similarity threshold
- Try different query phrasing
- Verify search scope

#### Slow searches
- Enable caching
- Reduce result limit
- Check internet connection (for cloud providers)
- Consider local embedding model

#### Indexing failures
- Check API key/credentials
- Verify internet connection
- Check available disk space
- Review error in indexing status

#### Plugin won't load
- Verify Calibre version ≥ 5.0
- Check plugin installation
- Review Calibre's error log
- Reinstall plugin

### Getting Help

1. **Check Documentation**:
   - This manual
   - README.md in plugin folder
   - Specification documents

2. **Debug Mode**:
   - Enable in plugin settings
   - Check logs in Calibre's configuration folder

3. **Community Support**:
   - GitHub issues
   - Calibre forums
   - Philosophy research communities

## Appendix: Search Examples

### Philosophy Examples

**Phenomenology**:
- "intentionality of consciousness"
- "being-in-the-world"
- "phenomenological reduction"

**Ethics**:
- "categorical imperative"
- "virtue and human flourishing"
- "moral responsibility and free will"

**Metaphysics**:
- "substance and accidents"
- "possibility and actuality"
- "mind-body problem"

**Epistemology**:
- "justified true belief"
- "skepticism and certainty"
- "a priori knowledge"

### Multi-Language Concepts

The plugin recognizes concepts across languages:
- Being: Sein, être, essere, ser
- Truth: Wahrheit, vérité, verità, verdad
- Knowledge: Wissen, savoir, sapere, saber

---

*For technical documentation and development information, see the project repository.*