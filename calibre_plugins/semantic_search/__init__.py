"""
Semantic Search Plugin for Calibre
Enables AI-powered similarity search for philosophical texts
"""

from calibre.customize import InterfaceActionBase

__license__ = "GPL v3"
__copyright__ = "2024"
__docformat__ = "restructuredtext en"


class SemanticSearchPlugin(InterfaceActionBase):
    """
    Main plugin class that Calibre loads
    """

    name = "Semantic Search"
    description = "AI-powered semantic search for philosophical texts"
    supported_platforms = ["windows", "osx", "linux"]
    author = "Calibre Semantic Search Contributors"
    version = (1, 0, 0)  # Version 1.0.0 - Initial Release
    minimum_calibre_version = (5, 0, 0)

    # This points to our actual implementation
    actual_plugin = "calibre_plugins.semantic_search.interface:SemanticSearchInterface"

    def is_customizable(self):
        """Allow user configuration"""
        return True

    def config_widget(self):
        """Return configuration widget"""
        # Import here to avoid loading Qt at startup
        from calibre_plugins.semantic_search.config import ConfigWidget

        cw = ConfigWidget()
        
        # Pass the actual interface action if it exists
        # actual_plugin_ is the SemanticSearchInterface instance
        if hasattr(self, 'actual_plugin_') and self.actual_plugin_:
            cw.plugin_interface = self.actual_plugin_
        
        return cw

    def save_settings(self, config_widget):
        """Save configuration settings"""
        config_widget.save_settings()

    def about(self):
        """Return information about the plugin"""
        text = """
        <p>Semantic Search enables AI-powered search capabilities in Calibre,
        allowing you to find books and passages by meaning rather than just keywords.</p>
        
        <p>Features:</p>
        <ul>
            <li>Search by concepts and meaning</li>
            <li>Find similar passages across books</li>
            <li>Philosophy-optimized search modes</li>
            <li>Multi-language concept mapping</li>
        </ul>
        
        <p>For more information, visit the 
        <a href="https://github.com/yourusername/calibre-semantic-search">project page</a>.</p>
        """
        return text
