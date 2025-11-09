"""
Path validation utilities.

Provides validation for file paths including existence checks,
traversal prevention, format validation, and sanitization.
"""

import os
import re
from pathlib import Path
from typing import Optional, Union

from src.utils.validators.base import ValidationResult, validate


# Windows path patterns
WINDOWS_DRIVE_PATTERN = re.compile(r"^[A-Za-z]:")
WINDOWS_UNC_PATTERN = re.compile(r"^\\\\[^\\]+\\[^\\]+")
WINDOWS_INVALID_CHARS = r'<>:"|?*'
WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
}

# Path traversal patterns
PATH_TRAVERSAL_PATTERNS = [
    "..",
    "..\\",
    "../",
    "..\\\\",
    "..//",
]


@validate(error_message="Path validation failed")
def validate_path_exists(
    path: Union[str, Path], must_exist: bool = True, check_type: Optional[str] = None
) -> ValidationResult:
    """
    Validate that a path exists and optionally check its type.

    Args:
        path: Path to validate
        must_exist: Whether path must exist
        check_type: Expected type ('file', 'directory', or None for any)

    Returns:
        ValidationResult with validated path
    """
    path_obj = Path(path)

    if not path_obj.exists():
        if must_exist:
            return ValidationResult.failure(
                f"Path does not exist: {path}",
                value=str(path_obj),
            )
        else:
            return ValidationResult.success(value=str(path_obj)).add_warning(
                f"Path does not exist: {path}", code="PATH_NOT_FOUND"
            )

    # Check type if specified
    if check_type:
        if check_type == "file" and not path_obj.is_file():
            return ValidationResult.failure(
                f"Path is not a file: {path}", value=str(path_obj)
            )
        elif check_type == "directory" and not path_obj.is_dir():
            return ValidationResult.failure(
                f"Path is not a directory: {path}", value=str(path_obj)
            )

    return ValidationResult.success(
        value=str(path_obj.resolve()),
        metadata={"exists": True, "type": "file" if path_obj.is_file() else "directory"},
    )


@validate(error_message="Path traversal check failed")
def validate_path_traversal(
    path: Union[str, Path], base_path: Optional[Union[str, Path]] = None
) -> ValidationResult:
    """
    Validate that a path does not contain traversal attempts.

    Args:
        path: Path to validate
        base_path: Optional base path that result must be within

    Returns:
        ValidationResult with sanitized path
    """
    path_str = str(path)

    # Check for path traversal patterns
    for pattern in PATH_TRAVERSAL_PATTERNS:
        if pattern in path_str:
            return ValidationResult.failure(
                f"Path contains traversal pattern: {pattern}",
                value=path_str,
                metadata={"pattern": pattern},
            )

    # If base_path provided, ensure resolved path is within it
    if base_path:
        try:
            path_obj = Path(path).resolve()
            base_obj = Path(base_path).resolve()

            if not str(path_obj).startswith(str(base_obj)):
                return ValidationResult.failure(
                    f"Path escapes base directory: {path} -> {base_path}",
                    value=path_str,
                )
        except (OSError, ValueError) as e:
            return ValidationResult.failure(
                f"Cannot resolve path: {e}", value=path_str
            )

    return ValidationResult.success(value=path_str)


@validate(error_message="Path format validation failed")
def validate_path_format(path: Union[str, Path], platform: Optional[str] = None) -> ValidationResult:
    """
    Validate path format for the specified platform.

    Args:
        path: Path to validate
        platform: Platform ('windows', 'linux', 'darwin') or None for current

    Returns:
        ValidationResult with validated path
    """
    path_str = str(path)
    platform = platform or os.name

    if platform == "nt" or platform == "windows":
        return _validate_windows_path_format(path_str)
    else:
        return _validate_posix_path_format(path_str)


def _validate_windows_path_format(path: str) -> ValidationResult:
    """Validate Windows path format."""
    result = ValidationResult.success(value=path)

    # Check for invalid characters
    for char in WINDOWS_INVALID_CHARS:
        if char in path:
            result.add_error(
                f"Path contains invalid Windows character: {char}",
                code="INVALID_CHAR",
            )

    # Check for reserved names
    path_parts = Path(path).parts
    for part in path_parts:
        name_without_ext = part.split(".")[0].upper()
        if name_without_ext in WINDOWS_RESERVED_NAMES:
            result.add_error(
                f"Path contains reserved Windows name: {part}",
                code="RESERVED_NAME",
            )

    # Check for valid drive letter or UNC path
    if len(path) >= 2:
        if not (
            WINDOWS_DRIVE_PATTERN.match(path) or WINDOWS_UNC_PATTERN.match(path)
        ):
            # Relative paths are okay
            if not path.startswith(("\\", "/")):
                pass  # Relative path
            else:
                result.add_warning(
                    "Path does not start with drive letter or UNC path",
                    code="NO_DRIVE",
                )

    # Check for trailing spaces/dots (invalid on Windows)
    for part in path_parts:
        if part.endswith((" ", ".")):
            result.add_error(
                f"Path component ends with space or dot: {part}",
                code="TRAILING_SPACE_DOT",
            )

    # Check path length (Windows MAX_PATH is 260)
    if len(path) > 260:
        result.add_warning(
            f"Path length ({len(path)}) exceeds Windows MAX_PATH (260)",
            code="PATH_TOO_LONG",
        )

    return result


def _validate_posix_path_format(path: str) -> ValidationResult:
    """Validate POSIX (Linux/Mac) path format."""
    result = ValidationResult.success(value=path)

    # Check for null bytes
    if "\0" in path:
        result.add_error("Path contains null byte", code="NULL_BYTE")

    # Check path length (most filesystems limit to 4096)
    if len(path) > 4096:
        result.add_warning(
            f"Path length ({len(path)}) exceeds typical limit (4096)",
            code="PATH_TOO_LONG",
        )

    return result


@validate(error_message="Permission check failed")
def validate_path_permissions(
    path: Union[str, Path],
    check_read: bool = False,
    check_write: bool = False,
    check_execute: bool = False,
) -> ValidationResult:
    """
    Validate that current user has required permissions on path.

    Args:
        path: Path to check
        check_read: Whether to check read permission
        check_write: Whether to check write permission
        check_execute: Whether to check execute permission

    Returns:
        ValidationResult with permission info
    """
    path_obj = Path(path)

    if not path_obj.exists():
        return ValidationResult.failure(f"Path does not exist: {path}")

    result = ValidationResult.success(value=str(path_obj))
    permissions = {"read": False, "write": False, "execute": False}

    try:
        if check_read:
            permissions["read"] = os.access(path_obj, os.R_OK)
            if not permissions["read"]:
                result.add_error("No read permission", code="NO_READ")

        if check_write:
            permissions["write"] = os.access(path_obj, os.W_OK)
            if not permissions["write"]:
                result.add_error("No write permission", code="NO_WRITE")

        if check_execute:
            permissions["execute"] = os.access(path_obj, os.X_OK)
            if not permissions["execute"]:
                result.add_error("No execute permission", code="NO_EXECUTE")

    except Exception as e:
        return ValidationResult.failure(
            f"Cannot check permissions: {e}", value=str(path_obj)
        )

    result.metadata["permissions"] = permissions
    return result


def normalize_path(path: Union[str, Path], resolve: bool = True) -> str:
    """
    Normalize a path to a consistent format.

    Args:
        path: Path to normalize
        resolve: Whether to resolve to absolute path

    Returns:
        Normalized path string
    """
    path_obj = Path(path)

    if resolve:
        try:
            return str(path_obj.resolve())
        except (OSError, ValueError):
            pass  # Fall through to non-resolved normalization

    return str(path_obj)


def sanitize_path(path: Union[str, Path], remove_traversal: bool = True) -> str:
    """
    Sanitize a path by removing dangerous components.

    Args:
        path: Path to sanitize
        remove_traversal: Whether to remove .. components

    Returns:
        Sanitized path string
    """
    path_str = str(path)

    # Remove null bytes
    path_str = path_str.replace("\0", "")

    # Remove traversal attempts if requested
    if remove_traversal:
        for pattern in PATH_TRAVERSAL_PATTERNS:
            path_str = path_str.replace(pattern, "")

    # Normalize slashes
    path_str = path_str.replace("\\", "/")

    # Remove duplicate slashes
    while "//" in path_str:
        path_str = path_str.replace("//", "/")

    return path_str


def is_valid_windows_path(path: Union[str, Path]) -> bool:
    """
    Quick check if path is valid for Windows.

    Args:
        path: Path to check

    Returns:
        True if valid Windows path format
    """
    result = validate_path_format(path, platform="windows")
    return result.is_valid


def is_safe_path(
    path: Union[str, Path], base_path: Optional[Union[str, Path]] = None
) -> bool:
    """
    Quick check if path is safe (no traversal, valid format).

    Args:
        path: Path to check
        base_path: Optional base path to check against

    Returns:
        True if path is safe
    """
    # Check format
    format_result = validate_path_format(path)
    if not format_result.is_valid:
        return False

    # Check traversal
    traversal_result = validate_path_traversal(path, base_path)
    if not traversal_result.is_valid:
        return False

    return True

