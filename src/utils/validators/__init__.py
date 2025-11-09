"""
Validation utilities for Claude Config Editor.

Provides comprehensive validation for paths, data, and security concerns.
All validators follow a consistent pattern and return ValidationResult objects.
"""

from src.utils.validators.base import (
    ValidationError,
    ValidationResult,
    ValidationSeverity,
    validate,
    validate_async,
)
from src.utils.validators.path_validators import (
    is_safe_path,
    is_valid_windows_path,
    normalize_path,
    sanitize_path,
    validate_path_exists,
    validate_path_format,
    validate_path_permissions,
    validate_path_traversal,
)
from src.utils.validators.data_validators import (
    validate_configuration,
    validate_file_hash,
    validate_json_data,
    validate_json_schema,
    validate_snapshot_data,
)
from src.utils.validators.security_validators import (
    sanitize_filename,
    sanitize_input,
    validate_content_type,
    validate_file_size,
    validate_file_type,
    validate_no_sql_injection,
    validate_no_xss,
)

__all__ = [
    # Base
    "ValidationError",
    "ValidationResult",
    "ValidationSeverity",
    "validate",
    "validate_async",
    # Path validators
    "is_safe_path",
    "is_valid_windows_path",
    "normalize_path",
    "sanitize_path",
    "validate_path_exists",
    "validate_path_format",
    "validate_path_permissions",
    "validate_path_traversal",
    # Data validators
    "validate_configuration",
    "validate_file_hash",
    "validate_json_data",
    "validate_json_schema",
    "validate_snapshot_data",
    # Security validators
    "sanitize_filename",
    "sanitize_input",
    "validate_content_type",
    "validate_file_size",
    "validate_file_type",
    "validate_no_sql_injection",
    "validate_no_xss",
]
