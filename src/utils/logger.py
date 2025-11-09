"""
Logging configuration for Claude Config version control system.

Provides structured logging with:
- Multiple log levels
- File rotation
- Console and file handlers
- Rich formatting for terminal output
- JSON structured logging
- Separate log files (app, error, access)
- Context managers and decorators
- Performance logging
"""

import json
import logging
import sys
import time
from contextlib import contextmanager
from functools import wraps
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Callable, Optional

from rich.console import Console
from rich.logging import RichHandler


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    log_max_bytes: int = 10 * 1024 * 1024,  # 10MB
    log_backup_count: int = 5,
) -> None:
    """
    Configure application logging.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        log_max_bytes: Maximum size of each log file before rotation
        log_backup_count: Number of backup log files to keep
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Create logger
    logger = logging.getLogger()
    logger.setLevel(numeric_level)

    # Remove existing handlers
    logger.handlers.clear()

    # Console handler with Rich formatting
    console = Console(stderr=True)
    console_handler = RichHandler(
        console=console,
        show_time=True,
        show_path=False,
        markup=True,
        rich_tracebacks=True,
        tracebacks_show_locals=False,
    )
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(
        logging.Formatter(
            "%(message)s",
            datefmt="[%X]",
        )
    )
    logger.addHandler(console_handler)

    # File handler with rotation (if log_file specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=log_max_bytes,
            backupCount=log_backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(file_handler)

    logger.info(f"Logging configured: level={log_level}, file={log_file}")


class JsonFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.
    
    Outputs log records as JSON for easy parsing by log aggregators.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms
        
        return json.dumps(log_data)


def setup_logging_advanced(
    log_level: str = "INFO",
    log_dir: str = "logs",
    log_max_bytes: int = 10 * 1024 * 1024,  # 10MB
    log_backup_count: int = 5,
    use_json: bool = False,
    console_output: bool = True,
    separate_error_log: bool = True,
) -> None:
    """
    Advanced logging configuration with multiple handlers.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files
        log_max_bytes: Maximum size of each log file before rotation
        log_backup_count: Number of backup log files to keep
        use_json: Use JSON formatter for structured logging
        console_output: Enable console output
        separate_error_log: Create separate error log file
    """
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create log directory
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(numeric_level)
    logger.handlers.clear()
    
    # Choose formatter
    if use_json:
        formatter = JsonFormatter(datefmt="%Y-%m-%dT%H:%M:%S")
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    
    # Console handler with Rich formatting
    if console_output:
        console = Console(stderr=True)
        console_handler = RichHandler(
            console=console,
            show_time=True,
            show_path=False,
            markup=True,
            rich_tracebacks=True,
            tracebacks_show_locals=False,
        )
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(
            logging.Formatter("%(message)s", datefmt="[%X]")
        )
        logger.addHandler(console_handler)
    
    # Main application log file
    app_log = log_path / "app.log"
    app_handler = RotatingFileHandler(
        app_log,
        maxBytes=log_max_bytes,
        backupCount=log_backup_count,
        encoding="utf-8",
    )
    app_handler.setLevel(numeric_level)
    app_handler.setFormatter(formatter)
    logger.addHandler(app_handler)
    
    # Separate error log file
    if separate_error_log:
        error_log = log_path / "error.log"
        error_handler = RotatingFileHandler(
            error_log,
            maxBytes=log_max_bytes,
            backupCount=log_backup_count,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        logger.addHandler(error_handler)
    
    logger.info(
        f"Advanced logging configured: level={log_level}, dir={log_dir}, json={use_json}"
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_function_call(logger: Optional[logging.Logger] = None) -> Callable:
    """
    Decorator to log function calls with arguments and execution time.
    
    Args:
        logger: Logger to use (defaults to function's module logger)
        
    Usage:
        @log_function_call()
        def my_function(arg1, arg2):
            return arg1 + arg2
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get logger
            log = logger or logging.getLogger(func.__module__)
            
            # Log function call
            log.debug(
                f"Calling {func.__name__}(args={args!r}, kwargs={kwargs!r})"
            )
            
            # Execute function and measure time
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                log.debug(
                    f"{func.__name__} completed in {duration_ms:.2f}ms"
                )
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                log.error(
                    f"{func.__name__} failed after {duration_ms:.2f}ms: {e}",
                    exc_info=True,
                )
                raise
        
        return wrapper
    return decorator


def log_async_function_call(logger: Optional[logging.Logger] = None) -> Callable:
    """
    Decorator to log async function calls with arguments and execution time.
    
    Args:
        logger: Logger to use (defaults to function's module logger)
        
    Usage:
        @log_async_function_call()
        async def my_async_function(arg1, arg2):
            return arg1 + arg2
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get logger
            log = logger or logging.getLogger(func.__module__)
            
            # Log function call
            log.debug(
                f"Calling async {func.__name__}(args={args!r}, kwargs={kwargs!r})"
            )
            
            # Execute function and measure time
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                log.debug(
                    f"Async {func.__name__} completed in {duration_ms:.2f}ms"
                )
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                log.error(
                    f"Async {func.__name__} failed after {duration_ms:.2f}ms: {e}",
                    exc_info=True,
                )
                raise
        
        return wrapper
    return decorator


@contextmanager
def log_context(
    operation: str,
    logger: Optional[logging.Logger] = None,
    level: int = logging.INFO,
):
    """
    Context manager for logging operations with timing.
    
    Args:
        operation: Description of the operation
        logger: Logger to use (defaults to root logger)
        level: Log level to use
        
    Usage:
        with log_context("database_query", logger=log):
            result = db.query()
    """
    log = logger or logging.getLogger()
    
    log.log(level, f"Starting: {operation}")
    start_time = time.time()
    
    try:
        yield
        duration_ms = (time.time() - start_time) * 1000
        log.log(level, f"Completed: {operation} ({duration_ms:.2f}ms)")
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log.error(
            f"Failed: {operation} ({duration_ms:.2f}ms) - {e}",
            exc_info=True,
        )
        raise


class PerformanceLogger:
    """
    Performance logger for tracking operation times.
    
    Usage:
        perf_logger = PerformanceLogger(logger)
        perf_logger.start("operation_name")
        # ... do work ...
        perf_logger.stop("operation_name")
    """
    
    def __init__(self, logger: logging.Logger) -> None:
        """Initialize performance logger."""
        self.logger = logger
        self.timers: dict[str, float] = {}
    
    def start(self, operation: str) -> None:
        """Start timing an operation."""
        self.timers[operation] = time.time()
        self.logger.debug(f"Performance tracking started: {operation}")
    
    def stop(self, operation: str) -> float:
        """Stop timing an operation and log the duration."""
        if operation not in self.timers:
            self.logger.warning(f"No timer found for operation: {operation}")
            return 0.0
        
        start_time = self.timers.pop(operation)
        duration_ms = (time.time() - start_time) * 1000
        
        self.logger.info(
            f"Performance: {operation} completed in {duration_ms:.2f}ms"
        )
        
        return duration_ms
    
    def checkpoint(self, operation: str, checkpoint_name: str) -> None:
        """Log a checkpoint without stopping the timer."""
        if operation not in self.timers:
            self.logger.warning(f"No timer found for operation: {operation}")
            return
        
        start_time = self.timers[operation]
        elapsed_ms = (time.time() - start_time) * 1000
        
        self.logger.debug(
            f"Performance checkpoint: {operation}.{checkpoint_name} "
            f"at {elapsed_ms:.2f}ms"
        )
