"""
Data validation utilities.

Provides validation for various data types including JSON, configuration,
snapshots, and file hashes.
"""

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Optional, Union

from src.utils.validators.base import ValidationResult, ValidationSeverity, validate


@validate(error_message="JSON validation failed")
def validate_json_data(
    data: Union[str, dict, Any], schema: Optional[dict] = None
) -> ValidationResult:
    """
    Validate JSON data structure.

    Args:
        data: JSON data as string or dict
        schema: Optional JSON schema to validate against

    Returns:
        ValidationResult with parsed JSON
    """
    # Parse if string
    if isinstance(data, str):
        try:
            parsed = json.loads(data)
        except json.JSONDecodeError as e:
            return ValidationResult.failure(
                f"Invalid JSON: {e}", metadata={"error": str(e)}
            )
    else:
        parsed = data

    # Validate against schema if provided
    if schema:
        try:
            # Try to import jsonschema if available
            import jsonschema

            jsonschema.validate(instance=parsed, schema=schema)
        except ImportError:
            # jsonschema not installed, skip schema validation
            result = ValidationResult.success(value=parsed)
            result.add_warning(
                "jsonschema not installed, skipping schema validation",
                code="NO_JSONSCHEMA",
            )
            return result
        except jsonschema.ValidationError as e:
            return ValidationResult.failure(
                f"JSON schema validation failed: {e.message}",
                value=parsed,
                metadata={"schema_path": list(e.path), "error": e.message},
            )

    return ValidationResult.success(value=parsed)


@validate(error_message="JSON schema validation failed")
def validate_json_schema(schema: Union[str, dict]) -> ValidationResult:
    """
    Validate that a JSON schema itself is valid.

    Args:
        schema: JSON schema to validate

    Returns:
        ValidationResult with validated schema
    """
    # Parse if string
    if isinstance(schema, str):
        try:
            schema_dict = json.loads(schema)
        except json.JSONDecodeError as e:
            return ValidationResult.failure(f"Invalid JSON schema: {e}")
    else:
        schema_dict = schema

    # Check for required schema fields
    if not isinstance(schema_dict, dict):
        return ValidationResult.failure("Schema must be a dictionary")

    # Validate schema structure using jsonschema if available
    try:
        import jsonschema

        jsonschema.Draft7Validator.check_schema(schema_dict)
    except ImportError:
        result = ValidationResult.success(value=schema_dict)
        result.add_warning(
            "jsonschema not installed, skipping schema validation",
            code="NO_JSONSCHEMA",
        )
        return result
    except jsonschema.SchemaError as e:
        return ValidationResult.failure(f"Invalid JSON schema: {e.message}")

    return ValidationResult.success(value=schema_dict)


@validate(error_message="Configuration validation failed")
def validate_configuration(
    config: dict[str, Any],
    required_fields: Optional[list[str]] = None,
    allowed_fields: Optional[list[str]] = None,
) -> ValidationResult:
    """
    Validate configuration dictionary.

    Args:
        config: Configuration dictionary
        required_fields: List of required field names (supports dot notation)
        allowed_fields: List of allowed field names (None = all allowed)

    Returns:
        ValidationResult with validated config
    """
    result = ValidationResult.success(value=config)

    # Check required fields
    if required_fields:
        for field in required_fields:
            if not _get_nested_value(config, field):
                result.add_error(
                    f"Required field missing: {field}", field=field, code="MISSING_FIELD"
                )

    # Check allowed fields
    if allowed_fields:
        config_fields = _get_all_field_paths(config)
        for field in config_fields:
            if field not in allowed_fields:
                result.add_warning(
                    f"Unknown configuration field: {field}",
                    field=field,
                    code="UNKNOWN_FIELD",
                )

    return result


@validate(error_message="Snapshot data validation failed")
def validate_snapshot_data(snapshot_data: dict[str, Any]) -> ValidationResult:
    """
    Validate snapshot data structure.

    Args:
        snapshot_data: Snapshot data dictionary

    Returns:
        ValidationResult with validated data
    """
    result = ValidationResult.success(value=snapshot_data)

    # Check required snapshot fields
    required_fields = ["trigger_type", "os_type"]
    for field in required_fields:
        if field not in snapshot_data:
            result.add_error(
                f"Required snapshot field missing: {field}",
                field=field,
                code="MISSING_FIELD",
            )

    # Validate trigger_type
    valid_triggers = {"manual", "scheduled", "api", "cli"}
    trigger = snapshot_data.get("trigger_type")
    if trigger and trigger not in valid_triggers:
        result.add_error(
            f"Invalid trigger_type: {trigger}. Must be one of {valid_triggers}",
            field="trigger_type",
            code="INVALID_VALUE",
        )

    # Validate numeric fields
    numeric_fields = ["files_found", "directories_found", "total_size_bytes"]
    for field in numeric_fields:
        value = snapshot_data.get(field)
        if value is not None:
            if not isinstance(value, (int, float)) or value < 0:
                result.add_error(
                    f"Field {field} must be a non-negative number",
                    field=field,
                    code="INVALID_TYPE",
                )

    # Validate hash if present
    snapshot_hash = snapshot_data.get("snapshot_hash")
    if snapshot_hash:
        hash_result = validate_file_hash(snapshot_hash, algorithm="sha256")
        if not hash_result.is_valid:
            result.add_error(
                "Invalid snapshot_hash format",
                field="snapshot_hash",
                code="INVALID_HASH",
            )

    return result


@validate(error_message="File hash validation failed")
def validate_file_hash(
    hash_value: str,
    algorithm: str = "sha256",
    verify_file: Optional[Union[str, Path]] = None,
) -> ValidationResult:
    """
    Validate file hash format and optionally verify against file.

    Args:
        hash_value: Hash string to validate
        algorithm: Hash algorithm (md5, sha1, sha256, sha512)
        verify_file: Optional file path to verify hash against

    Returns:
        ValidationResult with validation info
    """
    # Expected hash lengths for different algorithms
    expected_lengths = {
        "md5": 32,
        "sha1": 40,
        "sha256": 64,
        "sha512": 128,
    }

    if algorithm not in expected_lengths:
        return ValidationResult.failure(
            f"Unsupported hash algorithm: {algorithm}",
            metadata={"supported": list(expected_lengths.keys())},
        )

    # Check hash format (hexadecimal)
    if not re.match(r"^[a-fA-F0-9]+$", hash_value):
        return ValidationResult.failure(
            "Hash must be hexadecimal", metadata={"hash": hash_value}
        )

    # Check hash length
    expected_len = expected_lengths[algorithm]
    if len(hash_value) != expected_len:
        return ValidationResult.failure(
            f"Invalid {algorithm} hash length: expected {expected_len}, got {len(hash_value)}",
            metadata={"expected": expected_len, "actual": len(hash_value)},
        )

    result = ValidationResult.success(
        value=hash_value.lower(), metadata={"algorithm": algorithm}
    )

    # Verify against file if provided
    if verify_file:
        file_path = Path(verify_file)
        if not file_path.exists():
            result.add_error(
                f"File does not exist: {verify_file}", code="FILE_NOT_FOUND"
            )
            return result

        try:
            computed_hash = _compute_file_hash(file_path, algorithm)
            if computed_hash.lower() != hash_value.lower():
                result.add_error(
                    f"Hash mismatch: expected {hash_value}, got {computed_hash}",
                    code="HASH_MISMATCH",
                    details={"expected": hash_value, "actual": computed_hash},
                )
        except Exception as e:
            result.add_error(
                f"Cannot compute file hash: {e}", code="HASH_COMPUTE_ERROR"
            )

    return result


def _compute_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """Compute hash of file contents."""
    hash_obj = hashlib.new(algorithm)

    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            hash_obj.update(chunk)

    return hash_obj.hexdigest()


def _get_nested_value(data: dict, key_path: str) -> Optional[Any]:
    """
    Get nested dictionary value using dot notation.

    Example: _get_nested_value({"a": {"b": 1}}, "a.b") -> 1
    """
    keys = key_path.split(".")
    value = data

    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return None

    return value


def _get_all_field_paths(data: dict, prefix: str = "") -> list[str]:
    """
    Get all field paths in nested dictionary using dot notation.

    Example: _get_all_field_paths({"a": {"b": 1, "c": 2}}) -> ["a.b", "a.c"]
    """
    paths = []

    for key, value in data.items():
        current_path = f"{prefix}.{key}" if prefix else key

        if isinstance(value, dict):
            paths.extend(_get_all_field_paths(value, current_path))
        else:
            paths.append(current_path)

    return paths


@validate(error_message="String length validation failed")
def validate_string_length(
    value: str,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    field_name: Optional[str] = None,
) -> ValidationResult:
    """
    Validate string length constraints.

    Args:
        value: String to validate
        min_length: Minimum length (inclusive)
        max_length: Maximum length (inclusive)
        field_name: Name of field for error messages

    Returns:
        ValidationResult
    """
    result = ValidationResult.success(value=value)
    length = len(value)
    field = field_name or "value"

    if min_length is not None and length < min_length:
        result.add_error(
            f"{field} must be at least {min_length} characters (got {length})",
            field=field_name,
            code="TOO_SHORT",
        )

    if max_length is not None and length > max_length:
        result.add_error(
            f"{field} must be at most {max_length} characters (got {length})",
            field=field_name,
            code="TOO_LONG",
        )

    return result


@validate(error_message="Numeric range validation failed")
def validate_numeric_range(
    value: Union[int, float],
    min_value: Optional[Union[int, float]] = None,
    max_value: Optional[Union[int, float]] = None,
    field_name: Optional[str] = None,
) -> ValidationResult:
    """
    Validate numeric value is within range.

    Args:
        value: Number to validate
        min_value: Minimum value (inclusive)
        max_value: Maximum value (inclusive)
        field_name: Name of field for error messages

    Returns:
        ValidationResult
    """
    result = ValidationResult.success(value=value)
    field = field_name or "value"

    if min_value is not None and value < min_value:
        result.add_error(
            f"{field} must be at least {min_value} (got {value})",
            field=field_name,
            code="TOO_SMALL",
        )

    if max_value is not None and value > max_value:
        result.add_error(
            f"{field} must be at most {max_value} (got {value})",
            field=field_name,
            code="TOO_LARGE",
        )

    return result

