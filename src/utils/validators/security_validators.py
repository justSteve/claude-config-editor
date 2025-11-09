"""
Security validation utilities.

Provides validation for security concerns including SQL injection prevention,
XSS prevention, file type/size validation, and input sanitization.
"""

import mimetypes
import re
from pathlib import Path
from typing import Optional, Union

from src.utils.validators.base import ValidationResult, validate


# SQL injection patterns (common attack patterns)
SQL_INJECTION_PATTERNS = [
    r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
    r"(--|;|\/\*|\*\/)",
    r"(\bOR\b.*=.*)",
    r"(\bAND\b.*=.*)",
    r"('|(--)|;|\/\*|\*\/|xp_)",
    r"(\bUNION\b.*\bSELECT\b)",
]

# XSS patterns (common XSS vectors)
XSS_PATTERNS = [
    r"<script[^>]*>.*?</script>",
    r"javascript:",
    r"on\w+\s*=",  # Event handlers like onclick=
    r"<iframe[^>]*>",
    r"<object[^>]*>",
    r"<embed[^>]*>",
    r"<applet[^>]*>",
]

# Dangerous file extensions
DANGEROUS_EXTENSIONS = {
    # Executables
    ".exe",
    ".dll",
    ".bat",
    ".cmd",
    ".com",
    ".ps1",
    ".vbs",
    ".vbe",
    ".js",
    ".jse",
    ".wsf",
    ".wsh",
    ".msi",
    # Scripts
    ".sh",
    ".bash",
    ".zsh",
    ".csh",
    # Other dangerous
    ".scr",
    ".pif",
    ".application",
    ".gadget",
    ".msp",
    ".hta",
    ".cpl",
    ".jar",
}

# Safe file extensions for common use cases
SAFE_TEXT_EXTENSIONS = {
    ".txt",
    ".md",
    ".json",
    ".yaml",
    ".yml",
    ".xml",
    ".csv",
    ".log",
    ".ini",
    ".conf",
    ".cfg",
}

# Default max file size (100 MB)
DEFAULT_MAX_FILE_SIZE = 100 * 1024 * 1024


@validate(error_message="SQL injection check failed")
def validate_no_sql_injection(value: str, field_name: Optional[str] = None) -> ValidationResult:
    """
    Validate that input doesn't contain SQL injection patterns.

    Note: This is a basic check and should not replace proper parameterized queries.

    Args:
        value: Input string to validate
        field_name: Name of field for error messages

    Returns:
        ValidationResult
    """
    result = ValidationResult.success(value=value)
    field = field_name or "input"

    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, value, re.IGNORECASE):
            result.add_error(
                f"{field} contains potential SQL injection pattern",
                field=field_name,
                code="SQL_INJECTION",
                details={"pattern": pattern},
            )

    return result


@validate(error_message="XSS check failed")
def validate_no_xss(value: str, field_name: Optional[str] = None) -> ValidationResult:
    """
    Validate that input doesn't contain XSS patterns.

    Note: This is a basic check and should not replace proper output encoding.

    Args:
        value: Input string to validate
        field_name: Name of field for error messages

    Returns:
        ValidationResult
    """
    result = ValidationResult.success(value=value)
    field = field_name or "input"

    for pattern in XSS_PATTERNS:
        if re.search(pattern, value, re.IGNORECASE):
            result.add_error(
                f"{field} contains potential XSS pattern",
                field=field_name,
                code="XSS_DETECTED",
                details={"pattern": pattern},
            )

    return result


@validate(error_message="File type validation failed")
def validate_file_type(
    file_path: Union[str, Path],
    allowed_extensions: Optional[set[str]] = None,
    disallowed_extensions: Optional[set[str]] = None,
) -> ValidationResult:
    """
    Validate file type based on extension.

    Args:
        file_path: Path to file
        allowed_extensions: Set of allowed extensions (e.g., {'.txt', '.json'})
        disallowed_extensions: Set of disallowed extensions

    Returns:
        ValidationResult
    """
    path = Path(file_path)
    ext = path.suffix.lower()

    result = ValidationResult.success(
        value=str(path), metadata={"extension": ext}
    )

    # Check disallowed extensions first (more restrictive)
    if disallowed_extensions and ext in disallowed_extensions:
        result.add_error(
            f"File extension not allowed: {ext}",
            code="DISALLOWED_EXTENSION",
            details={"extension": ext},
        )

    # Check allowed extensions
    if allowed_extensions and ext not in allowed_extensions:
        result.add_error(
            f"File extension not in allowed list: {ext}",
            code="EXTENSION_NOT_ALLOWED",
            details={"extension": ext, "allowed": list(allowed_extensions)},
        )

    # Check for dangerous extensions
    if ext in DANGEROUS_EXTENSIONS:
        result.add_warning(
            f"File has potentially dangerous extension: {ext}",
            code="DANGEROUS_EXTENSION",
            details={"extension": ext},
        )

    return result


@validate(error_message="File size validation failed")
def validate_file_size(
    file_path: Union[str, Path],
    max_size: Optional[int] = None,
    min_size: Optional[int] = None,
) -> ValidationResult:
    """
    Validate file size constraints.

    Args:
        file_path: Path to file
        max_size: Maximum size in bytes
        min_size: Minimum size in bytes

    Returns:
        ValidationResult with file size info
    """
    path = Path(file_path)

    if not path.exists():
        return ValidationResult.failure(f"File does not exist: {file_path}")

    if not path.is_file():
        return ValidationResult.failure(f"Path is not a file: {file_path}")

    try:
        size = path.stat().st_size
    except OSError as e:
        return ValidationResult.failure(f"Cannot get file size: {e}")

    result = ValidationResult.success(value=str(path), metadata={"size": size})

    if min_size is not None and size < min_size:
        result.add_error(
            f"File too small: {size} bytes (minimum: {min_size})",
            code="FILE_TOO_SMALL",
            details={"size": size, "min_size": min_size},
        )

    if max_size is not None and size > max_size:
        result.add_error(
            f"File too large: {size} bytes (maximum: {max_size})",
            code="FILE_TOO_LARGE",
            details={"size": size, "max_size": max_size},
        )

    return result


@validate(error_message="Content type validation failed")
def validate_content_type(
    file_path: Union[str, Path], allowed_types: Optional[list[str]] = None
) -> ValidationResult:
    """
    Validate file content type (MIME type).

    Args:
        file_path: Path to file
        allowed_types: List of allowed MIME types (e.g., ['text/plain', 'application/json'])

    Returns:
        ValidationResult with content type info
    """
    path = Path(file_path)

    # Guess content type from extension
    content_type, _ = mimetypes.guess_type(str(path))

    if content_type is None:
        result = ValidationResult.success(value=str(path))
        result.add_warning(
            "Cannot determine content type",
            code="UNKNOWN_CONTENT_TYPE",
        )
        return result

    result = ValidationResult.success(
        value=str(path), metadata={"content_type": content_type}
    )

    # Check against allowed types
    if allowed_types and content_type not in allowed_types:
        result.add_error(
            f"Content type not allowed: {content_type}",
            code="CONTENT_TYPE_NOT_ALLOWED",
            details={"content_type": content_type, "allowed": allowed_types},
        )

    return result


def sanitize_input(
    value: str,
    max_length: Optional[int] = None,
    strip_html: bool = True,
    strip_sql: bool = True,
    allow_newlines: bool = True,
) -> str:
    """
    Sanitize user input by removing potentially dangerous content.

    Args:
        value: Input string to sanitize
        max_length: Maximum length to truncate to
        strip_html: Whether to strip HTML tags
        strip_sql: Whether to strip SQL patterns
        allow_newlines: Whether to allow newline characters

    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        value = str(value)

    # Strip leading/trailing whitespace
    sanitized = value.strip()

    # Remove null bytes
    sanitized = sanitized.replace("\0", "")

    # Remove or escape HTML if requested
    if strip_html:
        sanitized = _strip_html_tags(sanitized)

    # Remove SQL patterns if requested
    if strip_sql:
        sanitized = _strip_sql_patterns(sanitized)

    # Remove newlines if not allowed
    if not allow_newlines:
        sanitized = sanitized.replace("\n", " ").replace("\r", " ")

    # Truncate to max length
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]

    return sanitized


def sanitize_filename(filename: str, replace_spaces: bool = True) -> str:
    """
    Sanitize filename by removing dangerous characters.

    Args:
        filename: Filename to sanitize
        replace_spaces: Whether to replace spaces with underscores

    Returns:
        Sanitized filename
    """
    # Remove path separators
    sanitized = filename.replace("/", "_").replace("\\", "_")

    # Remove dangerous characters
    dangerous_chars = '<>:"|?*\0'
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, "")

    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip(". ")

    # Replace spaces if requested
    if replace_spaces:
        sanitized = sanitized.replace(" ", "_")

    # Remove multiple underscores
    while "__" in sanitized:
        sanitized = sanitized.replace("__", "_")

    # Ensure filename is not empty
    if not sanitized:
        sanitized = "unnamed"

    # Ensure filename is not a reserved name
    name_without_ext = sanitized.split(".")[0].upper()
    reserved_names = {
        "CON", "PRN", "AUX", "NUL",
        "COM1", "COM2", "COM3", "COM4", "COM5",
        "LPT1", "LPT2", "LPT3", "LPT4", "LPT5",
    }
    if name_without_ext in reserved_names:
        sanitized = f"file_{sanitized}"

    return sanitized


def _strip_html_tags(text: str) -> str:
    """Remove HTML tags from text."""
    # Simple HTML tag removal
    return re.sub(r"<[^>]+>", "", text)


def _strip_sql_patterns(text: str) -> str:
    """Remove common SQL injection patterns."""
    # Remove SQL comments
    text = re.sub(r"--.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)

    # Remove common SQL keywords at start of string
    sql_keywords = ["SELECT", "INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER"]
    for keyword in sql_keywords:
        text = re.sub(rf"^\s*{keyword}\b", "", text, flags=re.IGNORECASE)

    return text


@validate(error_message="Input sanitization check failed")
def validate_sanitized_input(
    value: str,
    original: str,
    field_name: Optional[str] = None,
) -> ValidationResult:
    """
    Validate that input matches its sanitized version.

    Useful for detecting if user input contains dangerous content.

    Args:
        value: Current value
        original: Original unsanitized value
        field_name: Name of field for error messages

    Returns:
        ValidationResult
    """
    sanitized = sanitize_input(original)

    if value != sanitized:
        return ValidationResult.failure(
            f"{field_name or 'Input'} contains potentially dangerous content",
            value=sanitized,
            metadata={"original": original, "sanitized": sanitized},
        )

    return ValidationResult.success(value=value)


@validate(error_message="Safe string check failed")
def validate_safe_string(
    value: str,
    allow_special_chars: bool = False,
    field_name: Optional[str] = None,
) -> ValidationResult:
    """
    Validate that string contains only safe characters.

    Args:
        value: String to validate
        allow_special_chars: Whether to allow special characters
        field_name: Name of field for error messages

    Returns:
        ValidationResult
    """
    result = ValidationResult.success(value=value)

    # Check for null bytes
    if "\0" in value:
        result.add_error(
            f"{field_name or 'String'} contains null bytes",
            field=field_name,
            code="NULL_BYTE",
        )

    # Check for control characters
    if re.search(r"[\x00-\x1f\x7f]", value):
        result.add_warning(
            f"{field_name or 'String'} contains control characters",
            field=field_name,
            code="CONTROL_CHARS",
        )

    # If not allowing special chars, check for alphanumeric only
    if not allow_special_chars:
        if not re.match(r"^[a-zA-Z0-9_\-. ]*$", value):
            result.add_error(
                f"{field_name or 'String'} contains special characters",
                field=field_name,
                code="SPECIAL_CHARS",
            )

    return result

