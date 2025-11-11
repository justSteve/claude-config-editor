"""
Secret sanitization utility.

Automatically detects and redacts sensitive data to prevent accidental
exposure of secrets, credentials, and personal information.

This module provides comprehensive pattern matching for:
- API keys and tokens
- Passwords and credentials
- Connection strings
- File paths with PII
- Environment variables with secrets
- Cloud provider credentials

All sensitive values are replaced with placeholders like [REDACTED_API_KEY].
"""

import re
import logging
from typing import Any, Optional, Union
from pathlib import Path

logger = logging.getLogger(__name__)

# Placeholder format for redacted values
REDACTED_PLACEHOLDER = "[REDACTED_{type}]"

# Patterns for detecting secrets
SECRET_PATTERNS = {
    # API keys and tokens (with and without key names)
    "api_key": [
        # Stripe-style keys (anchored - for standalone values)
        r"^sk_(?:live|test)_[a-zA-Z0-9]{16,}$",
        r"^pk_(?:live|test)_[a-zA-Z0-9]{16,}$",
        # Stripe-style keys (non-anchored - for embedded in JSON/strings)
        r"sk_(?:live|test)_[a-zA-Z0-9]{16,}",
        r"pk_(?:live|test)_[a-zA-Z0-9]{16,}",
        # Generic API keys (standalone, must be long to avoid false positives)
        r"^[a-zA-Z0-9_\-]{24,}$",
        # Key-value patterns (can be shorter since key name provides context)
        r"(?:api[_-]?key|apikey)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-]{16,})['\"]?",
        r"['\"](?:api[_-]?key|secret[_-]?key)['\"]?\s*[:=]\s*['\"]?([a-zA-Z0-9_\-]{16,})['\"]?",
    ],
    "auth_token": [
        # Standalone Bearer tokens
        r"Bearer\s+[a-zA-Z0-9_\-\.]{20,}",
        # Key-value patterns (shorter minimum since we have key context)
        r"['\"]?(?:auth[_-]?token|token)['\"]?\s*[:=]\s*['\"]?([a-zA-Z0-9_\-\.]{6,})['\"]?",
    ],
    "jwt_token": [
        # JWT format (standalone)
        r"eyJ[a-zA-Z0-9_\-]+\.eyJ[a-zA-Z0-9_\-]+\.[a-zA-Z0-9_\-]+",
    ],
    "password": [
        # Key-value patterns
        r"['\"]?(?:password|passwd|pwd)['\"]?\s*[:=]\s*['\"]?([^\s'\"]{6,})['\"]?",
    ],
    "connection_string": [
        # Database connection strings with credentials (username optional)
        r"(?:mysql|postgresql|mongodb|redis|sqlite)://[^:]*:[^@]+@",
        r"(?:Server|HOST)=[^;]+;(?:Database|DB)=[^;]+;(?:User ID|UID)=[^;]+;(?:Password|PWD)=[^;]+",
    ],
    "aws_key": [
        # AWS Access Key ID (standalone)
        r"^AKIA[0-9A-Z]{16}$",
        # AWS Secret Access Key (standalone, 40 chars base64)
        r"^[A-Za-z0-9/+=]{40}$",
        # Key-value patterns
        r"['\"]?(?:aws[_-]?access[_-]?key[_-]?id)['\"]?\s*[:=]\s*['\"]?([A-Z0-9]{20})['\"]?",
        r"['\"]?(?:aws[_-]?secret[_-]?access[_-]?key)['\"]?\s*[:=]\s*['\"]?([A-Za-z0-9/+=]{40})['\"]?",
    ],
    "azure_key": [
        # Key-value patterns
        r"['\"]?(?:azure[_-]?key|azure[_-]?credential)['\"]?\s*[:=]\s*['\"]?([a-zA-Z0-9+/=]{40,})['\"]?",
    ],
    "ssh_key": [
        # SSH private key markers
        r"-----BEGIN (?:RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----",
    ],
    "certificate": [
        # Certificate markers
        r"-----BEGIN CERTIFICATE-----",
    ],
}

# Keywords that suggest a value might be sensitive
SENSITIVE_KEYWORDS = {
    "password", "passwd", "pwd", "secret", "token", "api_key", "apikey",
    "auth", "credential", "credentials", "private", "access", "session",
    "oauth", "bearer", "jwt", "certificate", "cert", "pem", "ssh",
    "connection", "conn_str", "database_url", "db_url",
    "private_key", "secret_key", "access_key",  # Compound key forms
}

# Keywords that suggest a value contains a path
PATH_KEYWORDS = {
    "path", "dir", "directory", "folder", "file", "location",
    "command", "executable", "binary", "working_directory", "home",
}

# Path patterns that may contain PII
PII_PATH_PATTERNS = [
    r"[/\\]Users[/\\]([^/\\]+)",  # /Users/username
    r"[/\\]home[/\\]([^/\\]+)",   # /home/username
    r"C:\\Users\\([^\\]+)",        # C:\Users\username
    r"[/\\].*[/\\]([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",  # email addresses
]


def sanitize_value(
    value: Any,
    key: Optional[str] = None,
    context: Optional[str] = None
) -> Any:
    """
    Sanitize a single value.

    Args:
        value: Value to sanitize
        key: Optional key name (helps with context)
        context: Optional context (e.g., "env_var", "config", "path")

    Returns:
        Sanitized value (original type preserved when possible)
    """
    if value is None:
        return None

    # Handle different types
    if isinstance(value, bool):
        return value
    elif isinstance(value, (int, float)):
        # Don't sanitize numbers unless key suggests it's sensitive
        if key and any(kw in key.lower() for kw in ["port", "timeout", "size", "count", "length"]):
            return value
        elif key and any(kw in key.lower() for kw in SENSITIVE_KEYWORDS):
            return REDACTED_PLACEHOLDER.format(type="NUMBER")
        return value
    elif isinstance(value, str):
        return _sanitize_string(value, key, context)
    elif isinstance(value, dict):
        return {k: sanitize_value(v, k, context) for k, v in value.items()}
    elif isinstance(value, list):
        return [sanitize_value(item, key, context) for item in value]
    else:
        # Unknown type, convert to string and sanitize
        return _sanitize_string(str(value), key, context)


def _sanitize_string(
    value: str,
    key: Optional[str] = None,
    context: Optional[str] = None
) -> str:
    """
    Sanitize a string value.

    Args:
        value: String to sanitize
        key: Optional key name
        context: Optional context

    Returns:
        Sanitized string
    """
    if not value or len(value) < 3:
        return value

    original = value

    # Check if key suggests this is sensitive
    if key and _is_sensitive_key(key):
        return REDACTED_PLACEHOLDER.format(type=_get_redaction_type(key))

    # Apply pattern-based detection
    for secret_type, patterns in SECRET_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, value, re.IGNORECASE):
                logger.debug(f"Detected {secret_type} pattern in value")
                return REDACTED_PLACEHOLDER.format(type=secret_type.upper())

    # Check for PII in paths
    if context == "path" or (key and any(kw in key.lower() for kw in PATH_KEYWORDS)):
        value = _sanitize_path(value)
    # Also check if value looks like a path (contains slashes and common path markers)
    elif "/" in value or "\\" in value:
        if any(marker in value for marker in ["/Users/", "/home/", "C:\\Users\\", "/usr/"]):
            value = _sanitize_path(value)

    return value


def _is_sensitive_key(key: str) -> bool:
    """
    Check if a key name suggests sensitive content.

    Args:
        key: Key name to check

    Returns:
        True if key appears to be sensitive
    """
    key_lower = key.lower()
    return any(kw in key_lower for kw in SENSITIVE_KEYWORDS)


def _get_redaction_type(key: str) -> str:
    """
    Determine the type of redaction based on key name.

    Args:
        key: Key name

    Returns:
        Redaction type string
    """
    key_lower = key.lower()

    if "password" in key_lower or "passwd" in key_lower or "pwd" in key_lower:
        return "PASSWORD"
    elif "token" in key_lower:
        return "TOKEN"
    elif "key" in key_lower and "api" in key_lower:
        return "API_KEY"
    elif "secret" in key_lower:
        return "SECRET"
    elif "credential" in key_lower:
        return "CREDENTIAL"
    elif "connection" in key_lower or "conn" in key_lower:
        return "CONNECTION_STRING"
    elif "cert" in key_lower or "certificate" in key_lower:
        return "CERTIFICATE"
    else:
        return "SENSITIVE_DATA"


def _sanitize_path(path: str) -> str:
    """
    Sanitize a file path to remove PII.

    Args:
        path: File path to sanitize

    Returns:
        Sanitized path
    """
    for pattern in PII_PATH_PATTERNS:
        match = re.search(pattern, path)
        if match:
            # Replace the captured group (username/email) with placeholder
            username = match.group(1)
            path = path.replace(username, "[REDACTED_PII]")
            logger.debug(f"Sanitized PII from path: {username}")

    return path


def sanitize_config(config: dict[str, Any]) -> dict[str, Any]:
    """
    Sanitize a configuration dictionary.

    Args:
        config: Configuration dictionary

    Returns:
        Sanitized configuration dictionary
    """
    return sanitize_value(config, context="config")


def sanitize_env_vars(env: dict[str, str]) -> dict[str, str]:
    """
    Sanitize environment variables.

    Args:
        env: Environment variables dictionary

    Returns:
        Sanitized environment variables
    """
    return sanitize_value(env, context="env_var")


def sanitize_path(path: Union[str, Path]) -> str:
    """
    Sanitize a file path.

    Args:
        path: File path to sanitize

    Returns:
        Sanitized path string
    """
    path_str = str(path)
    return _sanitize_path(path_str)


def sanitize_response(response: Any) -> Any:
    """
    Sanitize an API response object.

    This is the main entry point for sanitizing API responses.
    It handles Pydantic models, dicts, lists, and primitive types.

    Args:
        response: Response object to sanitize

    Returns:
        Sanitized response (same type as input)
    """
    # Handle Pydantic models
    if hasattr(response, "model_dump"):
        # Convert to dict, sanitize, then reconstruct
        data = response.model_dump()
        sanitized_data = sanitize_value(data, context="response")
        # Update the model in-place
        for key, value in sanitized_data.items():
            setattr(response, key, value)
        return response
    else:
        # Handle dicts, lists, and primitives
        return sanitize_value(response, context="response")


def is_likely_secret(value: str, key: Optional[str] = None) -> bool:
    """
    Check if a value is likely to be a secret.

    This is useful for testing and validation.

    Args:
        value: Value to check
        key: Optional key name for context

    Returns:
        True if value appears to be a secret
    """
    if not value or not isinstance(value, str):
        return False

    # Check key first
    if key and _is_sensitive_key(key):
        return True

    # Check patterns
    for patterns in SECRET_PATTERNS.values():
        for pattern in patterns:
            if re.search(pattern, value, re.IGNORECASE):
                return True

    return False
