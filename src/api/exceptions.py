"""
Custom exceptions and exception handlers for the FastAPI application.

Provides consistent error responses across all endpoints.
"""

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from src.core.schemas import ErrorResponse

logger = logging.getLogger(__name__)


class APIException(Exception):
    """Base exception for API errors."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_type: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_type = error_type or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)


class NotFoundException(APIException):
    """Resource not found exception."""

    def __init__(self, message: str = "Resource not found", details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_type="NotFoundException",
            details=details,
        )


class ValidationException(APIException):
    """Validation error exception."""

    def __init__(self, message: str = "Validation failed", details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_type="ValidationException",
            details=details,
        )


class ConflictException(APIException):
    """Resource conflict exception."""

    def __init__(self, message: str = "Resource conflict", details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            error_type="ConflictException",
            details=details,
        )


class DatabaseException(APIException):
    """Database error exception."""

    def __init__(self, message: str = "Database error", details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_type="DatabaseException",
            details=details,
        )


def add_exception_handlers(app: FastAPI) -> None:
    """
    Add exception handlers to FastAPI application.

    Args:
        app: FastAPI application instance
    """

    @app.exception_handler(APIException)
    async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
        """Handle custom API exceptions."""
        error_response = ErrorResponse(
            error=exc.message,
            error_type=exc.error_type,
            details=exc.details,
        )

        logger.warning(
            f"API exception: {exc.message}",
            extra={
                "path": request.url.path,
                "error_type": exc.error_type,
                "status_code": exc.status_code,
            },
        )

        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.model_dump(mode="json"),
        )

    @app.exception_handler(ValidationError)
    async def validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
        """Handle Pydantic validation errors."""
        error_response = ErrorResponse(
            error="Validation failed",
            error_type="ValidationError",
            details={"errors": exc.errors()},
        )

        logger.warning(
            f"Validation error: {exc}",
            extra={
                "path": request.url.path,
                "errors": exc.errors(),
            },
        )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_response.model_dump(mode="json"),
        )

    @app.exception_handler(SQLAlchemyError)
    async def database_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
        """Handle database errors."""
        error_response = ErrorResponse(
            error="Database error occurred",
            error_type="DatabaseError",
            details={"message": str(exc)},
        )

        logger.error(
            f"Database error: {exc}",
            extra={
                "path": request.url.path,
            },
            exc_info=True,
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.model_dump(mode="json"),
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle all other exceptions."""
        error_response = ErrorResponse(
            error="Internal server error",
            error_type=type(exc).__name__,
            details={"message": str(exc)},
        )

        logger.error(
            f"Unhandled exception: {exc}",
            extra={
                "path": request.url.path,
                "error_type": type(exc).__name__,
            },
            exc_info=True,
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.model_dump(mode="json"),
        )
