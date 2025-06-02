"""
Index Management Dialog for Semantic Search
"""

import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

from PyQt5.Qt import (
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    Qt,
    pyqtSignal,
)

from calibre.gui2 import error_dialog, info_dialog, question_dialog
from calibre_plugins.semantic_search.ui.theme_manager import ThemeManager

logger = logging.getLogger(__name__)


class IndexManagerDialog(QDialog):
    """Dialog for managing the semantic search index"""
    
    # Signals
    indexCleared = pyqtSignal()
    indexRebuilt = pyqtSignal()
    
    def __init__(self, plugin, parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self.setWindowTitle("Semantic Search Index Manager")
        self.setMinimumSize(800, 600)
        
        self._setup_ui()
        self._load_index_info()
    
    def _setup_ui(self):
        """Create the dialog UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Index Statistics
        stats_group = QGroupBox("Index Statistics")
        stats_layout = QVBoxLayout()
        stats_group.setLayout(stats_layout)
        
        self.stats_label = QLabel("Loading index statistics...")
        self.stats_label.setWordWrap(True)
        stats_layout.addWidget(self.stats_label)
        
        layout.addWidget(stats_group)
        
        # Storage Information
        storage_group = QGroupBox("Storage Information")
        storage_layout = QVBoxLayout()
        storage_group.setLayout(storage_layout)
        
        self.storage_label = QLabel("Calculating storage usage...")
        storage_layout.addWidget(self.storage_label)
        
        layout.addWidget(storage_group)
        
        # Indexed Books Table
        books_group = QGroupBox("Indexed Books")
        books_layout = QVBoxLayout()
        books_group.setLayout(books_layout)
        
        # Table controls
        controls_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self._load_index_info)
        controls_layout.addWidget(self.refresh_btn)
        
        controls_layout.addStretch()
        
        self.clear_selected_btn = QPushButton("Clear Selected")
        self.clear_selected_btn.clicked.connect(self._clear_selected_books)
        controls_layout.addWidget(self.clear_selected_btn)
        
        books_layout.addLayout(controls_layout)
        
        # Books table
        self.books_table = QTableWidget()
        self.books_table.setColumnCount(6)
        self.books_table.setHorizontalHeaderLabels([
            "Book ID", "Title", "Authors", "Chunks", "Status", "Last Indexed"
        ])
        self.books_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.books_table.setAlternatingRowColors(True)
        
        # Adjust column widths
        header = self.books_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Title
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # Authors
        
        books_layout.addWidget(self.books_table)
        
        layout.addWidget(books_group)
        
        # Action buttons
        action_layout = QHBoxLayout()
        
        self.clear_all_btn = QPushButton("Clear Entire Index")
        self.clear_all_btn.setStyleSheet("QPushButton { color: red; }")
        self.clear_all_btn.clicked.connect(self._clear_entire_index)
        action_layout.addWidget(self.clear_all_btn)
        
        self.rebuild_btn = QPushButton("Rebuild Index")
        self.rebuild_btn.clicked.connect(self._rebuild_index)
        action_layout.addWidget(self.rebuild_btn)
        
        action_layout.addStretch()
        
        self.export_btn = QPushButton("Export Index")
        self.export_btn.clicked.connect(self._export_index)
        action_layout.addWidget(self.export_btn)
        
        self.import_btn = QPushButton("Import Index")
        self.import_btn.clicked.connect(self._import_index)
        action_layout.addWidget(self.import_btn)
        
        layout.addLayout(action_layout)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _load_index_info(self):
        """Load and display index information"""
        try:
            # Get indexing service
            indexing_service = self.plugin.get_indexing_service()
            if not indexing_service:
                self.stats_label.setText("Indexing service not initialized")
                self.storage_label.setText("Unable to calculate storage")
                return
            
            # Get statistics
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                stats = loop.run_until_complete(
                    indexing_service.get_library_statistics()
                )
            finally:
                loop.close()
            
            # Update statistics display
            stats_text = f"""
Total Books in Library: {stats.get('total_books', 0)}
Indexed Books: {stats.get('indexed_books', 0)}
Total Chunks: {stats.get('total_chunks', 0)}
Average Chunks per Book: {stats.get('avg_chunks_per_book', 0):.1f}
Books with Errors: {stats.get('error_count', 0)}
Index Coverage: {stats.get('coverage_percent', 0):.1f}%
"""
            self.stats_label.setText(stats_text.strip())
            
            # Update storage information
            storage_info = self._calculate_storage()
            storage_text = f"""
Database Location: {storage_info['db_path']}
Database Size: {self._format_size(storage_info['db_size'])}
Embedding Dimensions: {storage_info['embedding_dims']}
Estimated Storage per Book: {self._format_size(storage_info['avg_book_size'])}
"""
            self.storage_label.setText(storage_text.strip())
            
            # Load indexed books
            self._load_indexed_books(stats.get('books', []))
            
        except Exception as e:
            logger.error(f"Error loading index info: {e}")
            self.stats_label.setText(f"Error loading statistics: {str(e)}")
    
    def _calculate_storage(self) -> Dict:
        """Calculate storage usage"""
        try:
            # Get database path
            library_path = self.plugin.gui.library_path
            db_path = os.path.join(library_path, 'semantic_search', 'embeddings.db')
            
            # Get database size
            db_size = 0
            if os.path.exists(db_path):
                db_size = os.path.getsize(db_path)
            
            # Get embedding dimensions from config
            config = self.plugin.config
            embedding_dims = 768  # Default for most models
            
            # Calculate average size per book
            indexing_service = self.plugin.get_indexing_service()
            if indexing_service and hasattr(indexing_service, 'embedding_repo'):
                stats = indexing_service.embedding_repo.get_statistics()
                indexed_books = stats.get('book_count', 1)
                avg_book_size = db_size / max(indexed_books, 1)
            else:
                avg_book_size = 0
            
            return {
                'db_path': db_path,
                'db_size': db_size,
                'embedding_dims': embedding_dims,
                'avg_book_size': avg_book_size
            }
            
        except Exception as e:
            logger.error(f"Error calculating storage: {e}")
            return {
                'db_path': 'Unknown',
                'db_size': 0,
                'embedding_dims': 768,
                'avg_book_size': 0
            }
    
    def _format_size(self, bytes_size: int) -> str:
        """Format byte size to human readable"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.1f} TB"
    
    def _load_indexed_books(self, books: List[Dict]):
        """Load indexed books into table"""
        self.books_table.setRowCount(0)
        
        for book in books:
            row = self.books_table.rowCount()
            self.books_table.insertRow(row)
            
            # Book ID
            self.books_table.setItem(row, 0, QTableWidgetItem(str(book.get('book_id', ''))))
            
            # Title
            self.books_table.setItem(row, 1, QTableWidgetItem(book.get('title', 'Unknown')))
            
            # Authors
            authors = book.get('authors', [])
            authors_str = ', '.join(authors) if authors else 'Unknown'
            self.books_table.setItem(row, 2, QTableWidgetItem(authors_str))
            
            # Chunks
            self.books_table.setItem(row, 3, QTableWidgetItem(str(book.get('chunk_count', 0))))
            
            # Status
            status = book.get('status', 'unknown')
            status_item = QTableWidgetItem(status.title())
            if status == 'error':
                status_item.setForeground(Qt.red)
            elif status == 'completed':
                status_item.setForeground(Qt.darkGreen)
            self.books_table.setItem(row, 4, status_item)
            
            # Last indexed
            last_indexed = book.get('last_indexed', '')
            if last_indexed:
                try:
                    dt = datetime.fromisoformat(last_indexed)
                    last_indexed = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    pass
            self.books_table.setItem(row, 5, QTableWidgetItem(last_indexed))
    
    def _clear_selected_books(self):
        """Clear index for selected books"""
        selected_rows = set()
        for item in self.books_table.selectedItems():
            selected_rows.add(item.row())
        
        if not selected_rows:
            info_dialog(
                self,
                "No Selection",
                "Please select books to clear from the index.",
                show=True
            )
            return
        
        # Get book IDs
        book_ids = []
        for row in selected_rows:
            book_id_item = self.books_table.item(row, 0)
            if book_id_item:
                book_ids.append(int(book_id_item.text()))
        
        # Confirm
        if not question_dialog(
            self,
            "Clear Selected Books",
            f"Are you sure you want to clear {len(book_ids)} books from the index?",
            det_msg="This will remove all embeddings for the selected books."
        ):
            return
        
        # Clear books
        try:
            indexing_service = self.plugin.get_indexing_service()
            if indexing_service:
                for book_id in book_ids:
                    indexing_service.embedding_repo.delete_book_embeddings(book_id)
                
                info_dialog(
                    self,
                    "Books Cleared",
                    f"Successfully cleared {len(book_ids)} books from the index.",
                    show=True
                )
                
                # Reload
                self._load_index_info()
                
        except Exception as e:
            error_dialog(
                self,
                "Clear Failed",
                f"Failed to clear books: {str(e)}",
                show=True
            )
    
    def _clear_entire_index(self):
        """Clear the entire index"""
        if not question_dialog(
            self,
            "Clear Entire Index",
            "Are you sure you want to clear the ENTIRE search index?",
            det_msg="This will remove all embeddings and you'll need to re-index your library."
        ):
            return
        
        # Double confirm for safety
        if not question_dialog(
            self,
            "Confirm Clear",
            "This action cannot be undone. Continue?",
            det_msg="All semantic search data will be permanently deleted."
        ):
            return
        
        try:
            # Clear via repository
            indexing_service = self.plugin.get_indexing_service()
            if indexing_service:
                # Get all book IDs
                stats = indexing_service.embedding_repo.get_statistics()
                
                # Clear database
                if hasattr(indexing_service.embedding_repo, 'db'):
                    indexing_service.embedding_repo.db.clear_all()
                
                info_dialog(
                    self,
                    "Index Cleared",
                    "The entire search index has been cleared.",
                    show=True
                )
                
                self.indexCleared.emit()
                self._load_index_info()
                
        except Exception as e:
            error_dialog(
                self,
                "Clear Failed",
                f"Failed to clear index: {str(e)}",
                show=True
            )
    
    def _rebuild_index(self):
        """Rebuild the entire index"""
        if not question_dialog(
            self,
            "Rebuild Index",
            "Rebuild the entire search index?",
            det_msg="This will re-index all books in your library. It may take a while."
        ):
            return
        
        # Clear first
        self._clear_entire_index()
        
        # Then trigger indexing of all books
        if hasattr(self.plugin, '_start_indexing'):
            # Get all book IDs
            db = self.plugin.gui.current_db.new_api
            book_ids = list(db.all_book_ids())
            
            # Start indexing
            self.plugin._start_indexing(book_ids)
            
            self.indexRebuilt.emit()
            self.close()
    
    def _export_index(self):
        """Export index to file"""
        info_dialog(
            self,
            "Export Index",
            "Index export functionality will be implemented in a future version.",
            show=True
        )
    
    def _import_index(self):
        """Import index from file"""
        info_dialog(
            self,
            "Import Index",
            "Index import functionality will be implemented in a future version.",
            show=True
        )