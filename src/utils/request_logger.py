"""
Request logging utilities for API endpoints.

Provides middleware and utilities for logging HTTP requests and responses.
"""

import logging
import time
import uuid
from typing import Optional

logger = logging.getLogger(__name__)


class RequestContext:
    """
    Request context for tracking request-specific information.

    Stores request ID, user info, and timing information for logging.
    """

    def __init__(self, request_id: Optional[str] = None) -> None:
        """
        Initialize request context.

        Args:
            request_id: Unique request ID (auto-generated if not provided)
        """
        self.request_id = request_id or self._generate_request_id()
        self.start_time = time.time()
        self.user_id: Optional[str] = None
        self.method: Optional[str] = None
        self.path: Optional[str] = None
        self.status_code: Optional[int] = None
        self.metadata: dict[str, any] = {}

    @staticmethod
    def _generate_request_id() -> str:
        """Generate a unique request ID."""
        return str(uuid.uuid4())[:8]

    def set_user(self, user_id: str) -> None:
        """Set user ID for this request."""
        self.user_id = user_id

    def set_request_info(self, method: str, path: str) -> None:
        """Set request method and path."""
        self.method = method
        self.path = path

    def set_response_status(self, status_code: int) -> None:
        """Set response status code."""
        self.status_code = status_code

    def add_metadata(self, key: str, value: any) -> None:
        """Add metadata to the request context."""
        self.metadata[key] = value

    def get_duration_ms(self) -> float:
        """Get request duration in milliseconds."""
        return (time.time() - self.start_time) * 1000

    def to_dict(self) -> dict:
        """Convert context to dictionary for logging."""
        return {
            "request_id": self.request_id,
            "user_id": self.user_id,
            "method": self.method,
            "path": self.path,
            "status_code": self.status_code,
            "duration_ms": round(self.get_duration_ms(), 2),
            "metadata": self.metadata,
        }


def log_request_start(
    context: RequestContext,
    logger_instance: Optional[logging.Logger] = None,
) -> None:
    """
    Log the start of a request.

    Args:
        context: Request context
        logger_instance: Logger to use (defaults to module logger)
    """
    log = logger_instance or logger

    log.info(
        f"Request started: {context.request_id} {context.method} {context.path}",
        extra={
            "request_id": context.request_id,
            "method": context.method,
            "path": context.path,
        },
    )


def log_request_end(
    context: RequestContext,
    logger_instance: Optional[logging.Logger] = None,
) -> None:
    """
    Log the end of a request.

    Args:
        context: Request context
        logger_instance: Logger to use (defaults to module logger)
    """
    log = logger_instance or logger

    duration_ms = context.get_duration_ms()
    level = logging.INFO if context.status_code and context.status_code < 400 else logging.WARNING

    log.log(
        level,
        f"Request completed: {context.request_id} {context.method} {context.path} "
        f"[{context.status_code}] ({duration_ms:.2f}ms)",
        extra={
            "request_id": context.request_id,
            "method": context.method,
            "path": context.path,
            "status_code": context.status_code,
            "duration_ms": round(duration_ms, 2),
            "user_id": context.user_id,
        },
    )


def log_request_error(
    context: RequestContext,
    error: Exception,
    logger_instance: Optional[logging.Logger] = None,
) -> None:
    """
    Log a request error.

    Args:
        context: Request context
        error: Exception that occurred
        logger_instance: Logger to use (defaults to module logger)
    """
    log = logger_instance or logger

    duration_ms = context.get_duration_ms()

    log.error(
        f"Request failed: {context.request_id} {context.method} {context.path} "
        f"({duration_ms:.2f}ms) - {error}",
        exc_info=True,
        extra={
            "request_id": context.request_id,
            "method": context.method,
            "path": context.path,
            "duration_ms": round(duration_ms, 2),
            "user_id": context.user_id,
            "error": str(error),
            "error_type": type(error).__name__,
        },
    )


class AccessLogger:
    """
    Access logger for logging HTTP requests in Apache/Nginx style.

    Usage:
        access_logger = AccessLogger(logger)
        access_logger.log(method, path, status_code, duration_ms)
    """

    def __init__(self, logger_instance: logging.Logger) -> None:
        """Initialize access logger."""
        self.logger = logger_instance

    def log(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """
        Log an access entry.

        Args:
            method: HTTP method
            path: Request path
            status_code: HTTP status code
            duration_ms: Request duration in milliseconds
            user_id: User ID (optional)
            ip_address: Client IP address (optional)
            user_agent: User agent string (optional)
        """
        # Format similar to Apache combined log format
        user_str = user_id or "-"
        ip_str = ip_address or "-"

        self.logger.info(
            f'{ip_str} {user_str} "{method} {path}" {status_code} {duration_ms:.2f}ms',
            extra={
                "ip_address": ip_address,
                "user_id": user_id,
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration_ms": round(duration_ms, 2),
                "user_agent": user_agent,
            },
        )
