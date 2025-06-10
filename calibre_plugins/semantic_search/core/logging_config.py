"""
Core logging configuration for the Calibre Semantic Search plugin
"""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional


def setup_logging(plugin_name: str = "semantic_search", 
                 config_dir: Optional[str] = None) -> logging.Logger:
    """
    Set up rotating file logging for the plugin
    
    Args:
        plugin_name: Name of the plugin for logging
        config_dir: Plugin configuration directory (from Calibre)
        
    Returns:
        Configured logger instance
    """
    
    # Determine log directory
    if config_dir:
        log_dir = Path(config_dir) / "logs"
    else:
        # Fallback for test environment
        log_dir = Path.cwd() / "logs"
    
    # Ensure log directory exists
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Set up log file path
    log_file = log_dir / "plugin.log"
    
    # Configure root logger for the plugin
    logger_name = f"calibre_plugins.{plugin_name}"
    logger = logging.getLogger(logger_name)
    
    # Avoid duplicate handlers if already configured
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    # Create rotating file handler
    # Max 5MB per file, keep 3 backup files
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    
    # Create console handler for development
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Create detailed formatter
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create simple formatter for console
    simple_formatter = logging.Formatter(
        fmt='[%(name)s] %(levelname)s: %(message)s'
    )
    
    # Apply formatters
    file_handler.setFormatter(detailed_formatter)
    console_handler.setFormatter(simple_formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Log successful initialization
    logger.info(f"Logging initialized for {plugin_name}")
    logger.info(f"Log file: {log_file}")
    
    return logger


def get_logger(module_name: str) -> logging.Logger:
    """
    Get a logger for a specific module
    
    Args:
        module_name: Name of the module requesting logger
        
    Returns:
        Logger instance for the module
    """
    if not module_name.startswith('calibre_plugins.semantic_search'):
        module_name = f'calibre_plugins.semantic_search.{module_name}'
    
    return logging.getLogger(module_name)


def log_performance(logger: logging.Logger, operation: str):
    """
    Decorator for logging performance of operations
    
    Args:
        logger: Logger to use
        operation: Description of the operation
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                logger.info(f"{operation} completed in {elapsed:.2f}s")
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(f"{operation} failed after {elapsed:.2f}s: {e}")
                raise
                
        return wrapper
    return decorator