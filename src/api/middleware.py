"""
Custom middleware for the FastAPI application.

Provides request logging, performance tracking, and other cross-cutting concerns.
"""

import logging
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all incoming requests and responses.

    Logs:
    - Request method, path, and client IP
    - Response status code
    - Request duration
    - Any errors that occur
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and log details.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            HTTP response
        """
        # Start timing
        start_time = time.time()

        # Get client info
        client_host = request.client.host if request.client else "unknown"
        method = request.method
        path = request.url.path
        query = str(request.url.query) if request.url.query else ""

        # Log request
        logger.info(
            f"Request started",
            extra={
                "method": method,
                "path": path,
                "query": query,
                "client": client_host,
            },
        )

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Log response
            logger.info(
                f"Request completed",
                extra={
                    "method": method,
                    "path": path,
                    "status": response.status_code,
                    "duration_ms": round(duration * 1000, 2),
                    "client": client_host,
                },
            )

            return response

        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time

            # Log error
            logger.error(
                f"Request failed: {str(e)}",
                extra={
                    "method": method,
                    "path": path,
                    "duration_ms": round(duration * 1000, 2),
                    "client": client_host,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )

            # Re-raise to be handled by exception handlers
            raise

