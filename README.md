# Calibre Semantic Search Plugin

AI-powered semantic search for Calibre that enables searching by meaning and concepts rather than just keywords. Optimized for philosophical and academic texts.

## Features

- 🔍 **Semantic Search**: Find passages by meaning, not just exact words
- 🎯 **Philosophy-Optimized**: Special modes for dialectical and genealogical search
- 📚 **Smart Chunking**: Preserves argument structure and context
- 🌐 **Multi-Language**: Search across languages for the same concepts
- ⚡ **Fast Performance**: Sub-100ms search on 10,000+ book libraries
- 🔄 **Multiple Providers**: Vertex AI, OpenAI, Cohere, and local models

## Requirements

- Calibre 5.0 or higher
- Python 3.8 or higher
- 500MB RAM (typical usage)
- ~4.4GB storage per 1,000 books indexed

## Installation

1. Download the latest release from the [Releases](https://github.com/yourusername/calibre-semantic-search/releases) page
2. In Calibre, go to Preferences → Plugins
3. Click "Load plugin from file" and select the downloaded ZIP
4. Restart Calibre

## Quick Start

1. **Configure API Key**: 
   - Go to Preferences → Plugins → Semantic Search → Customize
   - Enter your API key for your chosen embedding provider

2. **Index Your Library**:
   - Click the Semantic Search button in the toolbar
   - Select "Index All Books" or select specific books to index

3. **Search**:
   - Click the Semantic Search button
   - Enter your query (a concept, phrase, or passage)
   - Browse results ranked by semantic similarity

## Usage

### Basic Search
Simply type a concept or phrase to find semantically similar passages:
- "consciousness and phenomenology"
- "the nature of being"
- "power and knowledge"

### Advanced Features

#### Dialectical Search
Find conceptual oppositions and tensions:
- Searching "Being" also finds "Nothing" and "Becoming"
- Searching "Master" finds "Slave" dialectic

#### Genealogical Search
Trace concepts through history:
- Track how "substance" evolves from Aristotle through Heidegger
- See transformations of "power" from Machiavelli to Foucault

#### Viewer Integration
- Select text in the Calibre viewer
- Right-click and choose "Semantic Search"
- Find similar passages instantly

## Configuration

### Embedding Providers
Choose from multiple providers (in order of recommendation):
1. **Vertex AI** - Best quality, requires Google Cloud account
2. **OpenAI** - Good quality, easy setup
3. **Cohere** - Good alternative
4. **Local Models** - Privacy-focused, no API needed

### Performance Tuning
- **Chunk Size**: Smaller chunks (256) for precision, larger (512) for context
- **Cache Size**: Increase for frequently searched libraries
- **Batch Size**: Larger batches for faster indexing (if API allows)

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

### Building from Source
```bash
git clone https://github.com/yourusername/calibre-semantic-search.git
cd calibre-semantic-search
python scripts/build_plugin.py
```

### Running Tests
```bash
pytest
pytest --cov=calibre_plugins.semantic_search
```

## Troubleshooting

### Plugin Won't Load
- Ensure Calibre version is 5.0+
- Check the error log in Preferences → Plugins → Semantic Search → Debug

### Search is Slow
- Enable caching in settings
- Reduce similarity threshold
- Consider using a local embedding model

### Indexing Fails
- Check API key is valid
- Verify internet connection
- Try a different embedding provider

## Philosophy

This plugin is designed with philosophical research in mind:
- Preserves conceptual nuance across languages
- Understands dialectical relationships
- Maintains argumentative structure
- Respects the genealogy of ideas

## License

GPL v3 - See [LICENSE](LICENSE) file for details

## Acknowledgments

- Calibre development team for the excellent plugin system
- sqlite-vec for efficient vector storage
- The philosophical community for inspiration and testing

## Support

- [Documentation](docs/)
- [Issue Tracker](https://github.com/yourusername/calibre-semantic-search/issues)
- [Discussions](https://github.com/yourusername/calibre-semantic-search/discussions)