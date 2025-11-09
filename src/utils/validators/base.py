"""
Base validation utilities and result types.

Provides the foundation for all validators including result types,
error handling, and validation decorators.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import Any, Callable, Optional, TypeVar, Union

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ValidationSeverity(str, Enum):
    """Severity levels for validation issues."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationError:
    """Represents a validation error or warning."""

    message: str
    field: Optional[str] = None
    severity: ValidationSeverity = ValidationSeverity.ERROR
    code: Optional[str] = None
    details: Optional[dict[str, Any]] = None


@dataclass
class ValidationResult:
    """
    Result of a validation operation.

    Attributes:
        is_valid: Whether validation passed
        errors: List of validation errors/warnings
        value: The validated value (potentially sanitized)
        metadata: Additional metadata about validation
    """

    is_valid: bool
    errors: list[ValidationError] = field(default_factory=list)
    value: Optional[Any] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def success(
        cls, value: Optional[Any] = None, metadata: Optional[dict[str, Any]] = None
    ) -> "ValidationResult":
        """Create a successful validation result."""
        return cls(
            is_valid=True, value=value, metadata=metadata or {}
        )

    @classmethod
    def failure(
        cls,
        error: Union[str, ValidationError, list[ValidationError]],
        value: Optional[Any] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> "ValidationResult":
        """Create a failed validation result."""
        if isinstance(error, str):
            errors = [ValidationError(message=error)]
        elif isinstance(error, ValidationError):
            errors = [error]
        else:
            errors = error

        return cls(
            is_valid=False, errors=errors, value=value, metadata=metadata or {}
        )

    def add_error(
        self,
        message: str,
        field: Optional[str] = None,
        severity: ValidationSeverity = ValidationSeverity.ERROR,
        code: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> "ValidationResult":
        """Add an error to this result."""
        self.errors.append(
            ValidationError(
                message=message,
                field=field,
                severity=severity,
                code=code,
                details=details,
            )
        )
        self.is_valid = False
        return self

    def add_warning(
        self,
        message: str,
        field: Optional[str] = None,
        code: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> "ValidationResult":
        """Add a warning to this result."""
        self.errors.append(
            ValidationError(
                message=message,
                field=field,
                severity=ValidationSeverity.WARNING,
                code=code,
                details=details,
            )
        )
        # Warnings don't make validation fail
        return self

    def get_error_messages(
        self, severity: Optional[ValidationSeverity] = None
    ) -> list[str]:
        """Get all error messages, optionally filtered by severity."""
        if severity:
            return [e.message for e in self.errors if e.severity == severity]
        return [e.message for e in self.errors]

    def get_errors_by_field(self, field: str) -> list[ValidationError]:
        """Get all errors for a specific field."""
        return [e for e in self.errors if e.field == field]

    def has_errors(self) -> bool:
        """Check if there are any errors (not warnings)."""
        return any(
            e.severity in {ValidationSeverity.ERROR,
                           ValidationSeverity.CRITICAL}
            for e in self.errors
        )

    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return any(e.severity == ValidationSeverity.WARNING for e in self.errors)


def validate(
    error_message: Optional[str] = None, logger_instance: Optional[logging.Logger] = None
) -> Callable:
    """
    Decorator for validation functions.

    Automatically wraps exceptions and logs validation attempts.

    Args:
        error_message: Custom error message for exceptions
        logger_instance: Logger to use (defaults to module logger)

    Returns:
        Decorated function that returns ValidationResult

    Example:
        @validate(error_message="Invalid path")
        def validate_path(path: str) -> ValidationResult:
            if not path:
                return ValidationResult.failure("Path cannot be empty")
            return ValidationResult.success(value=path)
    """
    log = logger_instance or logger

    def decorator(func: Callable[..., ValidationResult]) -> Callable[..., ValidationResult]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> ValidationResult:
            try:
                log.debug(
                    f"Validating with {func.__name__}(*{args}, **{kwargs})")
                result = func(*args, **kwargs)

                if not result.is_valid:
                    log.warning(
                        f"Validation failed in {func.__name__}: "
                        f"{result.get_error_messages()}"
                    )
                else:
                    log.debug(f"Validation succeeded in {func.__name__}")

                return result

            except Exception as e:
                log.error(
                    f"Validation error in {func.__name__}: {e}", exc_info=True)
                msg = error_message or f"Validation failed: {str(e)}"
                return ValidationResult.failure(
                    ValidationError(
                        message=msg,
                        severity=ValidationSeverity.ERROR,
                        code="VALIDATION_EXCEPTION",
                        details={"exception": str(
                            e), "type": type(e).__name__},
                    )
                )

        return wrapper

    return decorator


def validate_async(
    error_message: Optional[str] = None, logger_instance: Optional[logging.Logger] = None
) -> Callable:
    """
    Decorator for async validation functions.

    Same as @validate but for async functions.

    Args:
        error_message: Custom error message for exceptions
        logger_instance: Logger to use (defaults to module logger)

    Returns:
        Decorated async function that returns ValidationResult
    """
    log = logger_instance or logger

    def decorator(
        func: Callable[..., Any]
    ) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> ValidationResult:
            try:
                log.debug(
                    f"Validating with {func.__name__}(*{args}, **{kwargs})")
                result = await func(*args, **kwargs)

                if not result.is_valid:
                    log.warning(
                        f"Validation failed in {func.__name__}: "
                        f"{result.get_error_messages()}"
                    )
                else:
                    log.debug(f"Validation succeeded in {func.__name__}")

                return result

            except Exception as e:
                log.error(
                    f"Validation error in {func.__name__}: {e}", exc_info=True)
                msg = error_message or f"Validation failed: {str(e)}"
                return ValidationResult.failure(
                    ValidationError(
                        message=msg,
                        severity=ValidationSeverity.ERROR,
                        code="VALIDATION_EXCEPTION",
                        details={"exception": str(
                            e), "type": type(e).__name__},
                    )
                )

        return wrapper

    return decorator


def combine_results(*results: ValidationResult) -> ValidationResult:
    """
    Combine multiple validation results into one.

    Args:
        *results: Variable number of ValidationResult objects

    Returns:
        Combined ValidationResult (invalid if any result is invalid)
    """
    combined = ValidationResult(is_valid=True)

    for result in results:
        if not result.is_valid:
            combined.is_valid = False
        combined.errors.extend(result.errors)
        combined.metadata.update(result.metadata)

    return combined


def validate_all(
    validators: list[tuple[Callable, tuple, dict]],
    stop_on_first_error: bool = False
) -> ValidationResult:
    """
    Run multiple validators and combine results.

    Args:
        validators: List of (validator_func, args, kwargs) tuples
        stop_on_first_error: Whether to stop on first validation failure

    Returns:
        Combined ValidationResult

    Example:
        result = validate_all([
            (validate_path, ("./test",), {}),
            (validate_file_size, (1024,), {"max_size": 10000}),
        ])
    """
    results = []

    for validator_func, args, kwargs in validators:
        result = validator_func(*args, **kwargs)
        results.append(result)

        if stop_on_first_error and not result.is_valid:
            break

    return combine_results(*results)
