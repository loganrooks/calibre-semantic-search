"""
Indexing Manager - Handles indexing job creation and progress tracking

This module provides functionality to manage indexing operations,
track progress, and coordinate between UI and indexing service.
"""

from typing import Any, List, Optional, Callable
import logging
import uuid

logger = logging.getLogger(__name__)


class IndexingJobManager:
    """Manages indexing jobs and coordinates with indexing service"""
    
    def __init__(self, indexing_service: Any, gui: Any):
        """
        Initialize job manager
        
        Args:
            indexing_service: Indexing service instance
            gui: Calibre GUI object
        """
        self.indexing_service = indexing_service
        self.gui = gui
        self.progress_callback: Optional[Callable] = None
        self.completion_callback: Optional[Callable] = None
        self.error_callback: Optional[Callable] = None
    
    def start_single_book_indexing(self, book_id: int) -> str:
        """
        Start indexing job for single book
        
        Args:
            book_id: ID of book to index
            
        Returns:
            Job ID for tracking
        """
        job_id = str(uuid.uuid4())
        
        try:
            # Start indexing the book
            self.indexing_service.index_book(book_id)
            logger.info(f"Started indexing book {book_id} with job {job_id}")
            return job_id
            
        except Exception as e:
            logger.error(f"Failed to start indexing book {book_id}: {e}")
            if self.error_callback:
                self.error_callback(job_id, str(e))
            return job_id
    
    def start_batch_indexing(self, book_ids: List[int]) -> str:
        """
        Start batch indexing job for multiple books
        
        Args:
            book_ids: List of book IDs to index
            
        Returns:
            Job ID for tracking
        """
        job_id = str(uuid.uuid4())
        
        try:
            # Start batch indexing
            self.indexing_service.index_books_batch(book_ids)
            logger.info(f"Started batch indexing {len(book_ids)} books with job {job_id}")
            return job_id
            
        except Exception as e:
            logger.error(f"Failed to start batch indexing: {e}")
            if self.error_callback:
                self.error_callback(job_id, str(e))
            return job_id
    
    def set_progress_callback(self, callback: Callable[[str, int, int, str], None]) -> None:
        """Set callback for progress updates"""
        self.progress_callback = callback
    
    def set_completion_callback(self, callback: Callable[[str, bool, str], None]) -> None:
        """Set callback for job completion"""
        self.completion_callback = callback
    
    def set_error_callback(self, callback: Callable[[str, str], None]) -> None:
        """Set callback for job errors"""
        self.error_callback = callback
    
    def _on_progress_update(self, job_id: str, current: int, total: int, message: str) -> None:
        """Handle progress update from indexing service"""
        if self.progress_callback:
            self.progress_callback(job_id, current, total, message)
    
    def _on_job_completion(self, job_id: str, success: bool, message: str) -> None:
        """Handle job completion from indexing service"""
        if self.completion_callback:
            self.completion_callback(job_id, success, message)
    
    def _on_job_error(self, job_id: str, error_message: str) -> None:
        """Handle job error from indexing service"""
        if self.error_callback:
            self.error_callback(job_id, error_message)


class IndexingProgressTracker:
    """Tracks and displays indexing progress in UI"""
    
    def __init__(self, progress_bar: Any, status_label: Any, details_text: Any):
        """
        Initialize progress tracker
        
        Args:
            progress_bar: Qt progress bar widget
            status_label: Qt label for status text
            details_text: Qt text widget for detailed progress
        """
        self.progress_bar = progress_bar
        self.status_label = status_label
        self.details_text = details_text
    
    def update_progress(self, current: int, total: int, message: str) -> None:
        """
        Update progress display
        
        Args:
            current: Current progress value
            total: Total progress value
            message: Progress message to display
        """
        # Update progress bar
        self.progress_bar.setValue(current)
        self.progress_bar.setMaximum(total)
        
        # Update status label
        self.status_label.setText(message)
    
    def show_completion(self, total_indexed: int, message: str) -> None:
        """
        Show completion status
        
        Args:
            total_indexed: Number of books successfully indexed
            message: Completion message
        """
        # Set progress to 100%
        self.progress_bar.setValue(100)
        
        # Update status
        self.status_label.setText(message)
        
        # Add to details
        self.details_text.append(f"✓ {message}")
    
    def show_error(self, error_message: str) -> None:
        """
        Show error status
        
        Args:
            error_message: Error message to display
        """
        # Update status with error
        self.status_label.setText(error_message)
        
        # Add to details
        self.details_text.append(f"✗ {error_message}")


class IndexingUIConnector:
    """Connects indexing UI to indexing services"""
    
    def __init__(self, gui: Any):
        """
        Initialize UI connector
        
        Args:
            gui: Calibre GUI object
        """
        self.gui = gui
        self.job_manager: Optional[IndexingJobManager] = None
        self.error_callback: Optional[Callable] = None
    
    def set_error_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback for error handling"""
        self.error_callback = callback
    
    def index_selected_books(self) -> None:
        """Start indexing for currently selected books"""
        # Get selected books
        rows = self.gui.current_view().selectionModel().selectedRows()
        
        if not rows:
            if self.error_callback:
                self.error_callback("No books selected. Please select books to index.")
            return
        
        # Extract book IDs
        book_ids = [self.gui.current_view().model().id(row) for row in rows]
        
        # Start batch indexing
        if self.job_manager:
            self.job_manager.start_batch_indexing(book_ids)
    
    def index_all_books(self) -> None:
        """Start indexing for all books in library"""
        # Get all book IDs
        book_ids = list(self.gui.current_db.new_api.all_book_ids())
        
        # Confirm large indexing operation
        if confirm_large_indexing(len(book_ids)):
            if self.job_manager:
                self.job_manager.start_batch_indexing(book_ids)


def confirm_large_indexing(num_books: int) -> bool:
    """
    Confirm large indexing operation with user
    
    Args:
        num_books: Number of books to be indexed
        
    Returns:
        True if user confirms, False otherwise
    """
    # For now, always return True (minimal implementation)
    # In real implementation, this would show a confirmation dialog
    return True