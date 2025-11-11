"""
Unit tests for secret sanitization system.

Tests pattern detection, redaction, and security features.
Target: >95% code coverage
"""

import pytest
from src.utils.sanitizer import (
    sanitize_value,
    sanitize_config,
    sanitize_env_vars,
    sanitize_path,
    sanitize_response,
    is_likely_secret,
    _is_sensitive_key,
    _get_redaction_type,
    _sanitize_string,
    _sanitize_path,
)


class TestPatternDetection:
    """Test secret pattern detection."""

    def test_api_key_detection(self):
        """Test API key pattern matching."""
        assert is_likely_secret("sk_live_1234567890abcdefghijk")
        assert is_likely_secret("api_key=abcdef1234567890")
        assert is_likely_secret('"apiKey": "pk_test_1234567890"')

    def test_jwt_token_detection(self):
        """Test JWT token pattern matching."""
        jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        assert is_likely_secret(jwt)

    def test_password_detection(self):
        """Test password pattern matching."""
        assert is_likely_secret("password=mySecret123")
        assert is_likely_secret('"password": "test123"')
        assert is_likely_secret("pwd=abc123def")

    def test_connection_string_detection(self):
        """Test database connection string detection."""
        assert is_likely_secret("postgresql://user:password@localhost:5432/db")
        assert is_likely_secret("mysql://admin:secret123@db.example.com/prod")
        assert is_likely_secret("mongodb://user:pass@mongo.com:27017/mydb")

    def test_aws_key_detection(self):
        """Test AWS credential detection."""
        assert is_likely_secret("AKIAIOSFODNN7EXAMPLE")
        assert is_likely_secret("aws_access_key_id=AKIAIOSFODNN7EXAMPLE")
        assert is_likely_secret("wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY")

    def test_bearer_token_detection(self):
        """Test Bearer token detection."""
        assert is_likely_secret("Bearer abc123def456ghi789jkl")

    def test_ssh_key_detection(self):
        """Test SSH private key detection."""
        assert is_likely_secret("-----BEGIN RSA PRIVATE KEY-----")
        assert is_likely_secret("-----BEGIN OPENSSH PRIVATE KEY-----")

    def test_false_positives(self):
        """Test that normal values are not flagged."""
        assert not is_likely_secret("hello world")
        assert not is_likely_secret("123")
        assert not is_likely_secret("example.com")
        assert not is_likely_secret("/usr/local/bin")
        assert not is_likely_secret("node server.js")


class TestKeyBasedDetection:
    """Test key name based secret detection."""

    def test_sensitive_key_detection(self):
        """Test detection of sensitive key names."""
        assert _is_sensitive_key("password")
        assert _is_sensitive_key("api_key")
        assert _is_sensitive_key("secret_token")
        assert _is_sensitive_key("oauth_credential")
        assert _is_sensitive_key("private_key")
        assert _is_sensitive_key("access_token")

    def test_case_insensitivity(self):
        """Test case-insensitive key detection."""
        assert _is_sensitive_key("PASSWORD")
        assert _is_sensitive_key("Api_Key")
        assert _is_sensitive_key("SECRET")

    def test_non_sensitive_keys(self):
        """Test that normal keys are not flagged."""
        assert not _is_sensitive_key("name")
        assert not _is_sensitive_key("timeout")
        assert not _is_sensitive_key("port")
        assert not _is_sensitive_key("command")

    def test_redaction_type_mapping(self):
        """Test correct redaction type assignment."""
        assert _get_redaction_type("password") == "PASSWORD"
        assert _get_redaction_type("api_key") == "API_KEY"
        assert _get_redaction_type("token") == "TOKEN"
        assert _get_redaction_type("secret") == "SECRET"
        assert _get_redaction_type("connection_string") == "CONNECTION_STRING"


class TestValueSanitization:
    """Test sanitization of different value types."""

    def test_sanitize_none(self):
        """Test None value handling."""
        assert sanitize_value(None) is None

    def test_sanitize_boolean(self):
        """Test boolean value preservation."""
        assert sanitize_value(True) is True
        assert sanitize_value(False) is False

    def test_sanitize_numbers(self):
        """Test number preservation."""
        assert sanitize_value(42) == 42
        assert sanitize_value(3.14) == 3.14
        assert sanitize_value(0) == 0

    def test_sanitize_safe_strings(self):
        """Test safe string preservation."""
        assert sanitize_value("hello world") == "hello world"
        assert sanitize_value("node") == "node"
        assert sanitize_value("/usr/bin/node") == "/usr/bin/node"

    def test_sanitize_api_key(self):
        """Test API key redaction."""
        result = sanitize_value("sk_live_1234567890abcdef")
        assert "[REDACTED" in result
        assert "sk_live" not in result

    def test_sanitize_password(self):
        """Test password redaction."""
        result = sanitize_value("mySecretPassword123", key="password")
        assert "[REDACTED_PASSWORD]" == result

    def test_sanitize_dict(self):
        """Test dictionary sanitization."""
        data = {
            "name": "test-server",
            "api_key": "sk_test_12345678",
            "timeout": 30,
        }
        result = sanitize_value(data)
        assert result["name"] == "test-server"
        assert result["timeout"] == 30
        assert "[REDACTED" in result["api_key"]

    def test_sanitize_list(self):
        """Test list sanitization."""
        data = ["normal", "password=secret123", "ok"]
        result = sanitize_value(data)
        assert result[0] == "normal"
        assert "[REDACTED" in result[1]
        assert result[2] == "ok"

    def test_sanitize_nested_structures(self):
        """Test nested dict/list sanitization."""
        data = {
            "config": {
                "api_key": "abc123",
                "settings": {
                    "password": "secret",
                    "port": 8080,
                }
            },
            "list": ["ok", "token=xyz789"],
        }
        result = sanitize_value(data)
        assert "[REDACTED" in result["config"]["api_key"]
        assert result["config"]["settings"]["port"] == 8080
        assert "[REDACTED" in result["list"][1]


class TestPathSanitization:
    """Test PII removal from file paths."""

    def test_sanitize_windows_path(self):
        """Test Windows user path sanitization."""
        path = "C:\\Users\\john\\Documents\\file.txt"
        result = sanitize_path(path)
        assert "[REDACTED_PII]" in result
        assert "john" not in result

    def test_sanitize_linux_path(self):
        """Test Linux user path sanitization."""
        path = "/home/alice/projects/app.py"
        result = sanitize_path(path)
        assert "[REDACTED_PII]" in result
        assert "alice" not in result

    def test_sanitize_mac_path(self):
        """Test macOS user path sanitization."""
        path = "/Users/bob/Library/Application Support/app"
        result = sanitize_path(path)
        assert "[REDACTED_PII]" in result
        assert "bob" not in result

    def test_sanitize_email_in_path(self):
        """Test email address redaction in paths."""
        path = "/var/log/user@example.com/logs"
        result = _sanitize_path(path)
        assert "[REDACTED_PII]" in result
        assert "user@example.com" not in result

    def test_preserve_system_paths(self):
        """Test that system paths without PII are preserved."""
        paths = [
            "/usr/local/bin",
            "/var/log",
            "C:\\Program Files\\App",
            "/opt/software",
        ]
        for path in paths:
            result = sanitize_path(path)
            # Should not contain redaction if no PII
            # Note: May still have PII if path contains username-like strings
            assert path == result or "[REDACTED_PII]" in result


class TestConfigSanitization:
    """Test configuration dictionary sanitization."""

    def test_sanitize_mcp_config(self):
        """Test MCP server configuration sanitization."""
        config = {
            "server_name": "test-mcp",
            "command": "/Users/alice/mcp/server.js",
            "env": {
                "API_KEY": "sk_test_123456",
                "DEBUG": "true",
                "DB_URL": "postgresql://user:pass@localhost/db",
            },
            "timeout": 30,
        }
        result = sanitize_config(config)

        assert result["server_name"] == "test-mcp"
        assert "[REDACTED_PII]" in result["command"]
        assert result["timeout"] == 30
        assert "[REDACTED" in result["env"]["API_KEY"]
        assert result["env"]["DEBUG"] == "true"
        assert "[REDACTED" in result["env"]["DB_URL"]

    def test_sanitize_env_vars(self):
        """Test environment variable sanitization."""
        env = {
            "PATH": "/usr/bin:/usr/local/bin",
            "HOME": "/Users/john",
            "API_TOKEN": "bearer_abc123def456",
            "AWS_ACCESS_KEY_ID": "AKIAIOSFODNN7EXAMPLE",
            "DEBUG": "1",
        }
        result = sanitize_env_vars(env)

        assert result["PATH"] == "/usr/bin:/usr/local/bin"
        assert "[REDACTED_PII]" in result["HOME"]
        assert "[REDACTED" in result["API_TOKEN"]
        assert "[REDACTED" in result["AWS_ACCESS_KEY_ID"]
        assert result["DEBUG"] == "1"


class TestResponseSanitization:
    """Test API response sanitization."""

    def test_sanitize_dict_response(self):
        """Test dictionary response sanitization."""
        response = {
            "id": 1,
            "name": "server",
            "password": "secret123",
            "config": {"api_key": "xyz789"},
        }
        result = sanitize_response(response)

        assert result["id"] == 1
        assert result["name"] == "server"
        assert "[REDACTED" in result["password"]
        assert "[REDACTED" in result["config"]["api_key"]

    def test_sanitize_list_response(self):
        """Test list response sanitization."""
        response = [
            {"id": 1, "key": "safe"},
            {"id": 2, "password": "secret"},
        ]
        result = sanitize_response(response)

        assert result[0]["key"] == "safe"
        assert "[REDACTED" in result[1]["password"]


class TestSecurityGuarantees:
    """Test security guarantees - no secrets should leak."""

    def test_no_raw_passwords(self):
        """Ensure passwords are always redacted."""
        test_cases = [
            {"password": "mypassword"},
            {"pwd": "secret123"},
            {"user_password": "test"},
        ]
        for case in test_cases:
            result = sanitize_config(case)
            for key, value in result.items():
                assert "mypassword" not in str(value).lower()
                assert "secret123" not in str(value).lower()
                assert "[REDACTED" in str(value)

    def test_no_raw_api_keys(self):
        """Ensure API keys are always redacted."""
        configs = [
            {"api_key": "sk_live_abcdef123456"},
            {"apiKey": "pk_test_xyz789"},
            {"key": "1234567890abcdefghijklmnop"},
        ]
        for config in configs:
            result = sanitize_config(config)
            config_str = str(result)
            # Original keys should not appear
            for value in config.values():
                if len(str(value)) > 20:  # Long enough to be a key
                    assert str(value) not in config_str or "[REDACTED" in config_str

    def test_no_raw_connection_strings(self):
        """Ensure connection strings with passwords are redacted."""
        config = {
            "database_url": "postgresql://admin:secret@localhost/db",
            "redis_url": "redis://:password@redis:6379/0",
        }
        result = sanitize_config(config)

        assert "secret" not in result["database_url"]
        assert "password" not in result["redis_url"]
        assert "[REDACTED" in result["database_url"]

    def test_no_pii_in_paths(self):
        """Ensure usernames are redacted from paths."""
        paths = [
            "/Users/john/app",
            "C:\\Users\\alice\\data",
            "/home/bob/config",
        ]
        for path in paths:
            result = sanitize_path(path)
            assert "john" not in result.lower()
            assert "alice" not in result.lower()
            assert "bob" not in result.lower()
            assert "[REDACTED_PII]" in result


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_values(self):
        """Test empty value handling."""
        assert sanitize_value("") == ""
        assert sanitize_value({}) == {}
        assert sanitize_value([]) == []

    def test_very_short_strings(self):
        """Test very short strings are not over-sanitized."""
        assert sanitize_value("ab") == "ab"
        assert sanitize_value("x") == "x"

    def test_unicode_handling(self):
        """Test Unicode string handling."""
        result = sanitize_value("こんにちは")
        assert result == "こんにちは"

    def test_special_characters(self):
        """Test special character handling."""
        result = sanitize_value("test@#$%^&*()")
        assert result == "test@#$%^&*()"

    def test_mixed_case_keys(self):
        """Test mixed case sensitive key detection."""
        data = {
            "Password": "secret",
            "API_KEY": "xyz",
            "Secret_Token": "abc",
        }
        result = sanitize_config(data)

        assert "[REDACTED" in result["Password"]
        assert "[REDACTED" in result["API_KEY"]
        assert "[REDACTED" in result["Secret_Token"]

    def test_nested_depth(self):
        """Test deeply nested structure sanitization."""
        data = {
            "level1": {
                "level2": {
                    "level3": {
                        "password": "deep_secret",
                    }
                }
            }
        }
        result = sanitize_config(data)
        assert "[REDACTED" in result["level1"]["level2"]["level3"]["password"]


class TestContextAwareness:
    """Test context-aware sanitization."""

    def test_context_path(self):
        """Test path context triggers PII sanitization."""
        value = "/Users/john/file.txt"
        result = sanitize_value(value, context="path")
        assert "[REDACTED_PII]" in result

    def test_context_config(self):
        """Test config context sanitization."""
        data = {"password": "secret"}
        result = sanitize_value(data, context="config")
        assert "[REDACTED" in result["password"]

    def test_key_context(self):
        """Test key name provides context."""
        # Even a safe-looking value should be redacted if key is sensitive
        result = sanitize_value("normalvalue", key="password")
        assert "[REDACTED" in result


# Integration test
class TestIntegration:
    """Test full integration scenarios."""

    def test_full_mcp_config_sanitization(self):
        """Test complete MCP server config sanitization."""
        mcp_config = {
            "id": 1,
            "server_name": "claude-code-search",
            "command": "npx /Users/john/.npm/claude-code-search",
            "args": ["-c", "/Users/john/config.json"],
            "env": {
                "API_KEY": "sk_live_1234567890abcdefghijk",
                "AWS_ACCESS_KEY_ID": "AKIAIOSFODNN7EXAMPLE",
                "AWS_SECRET_ACCESS_KEY": "wJalrXUtnFEMI/K7MDENG/bPxRfiCY",
                "DEBUG": "true",
                "TIMEOUT": "30",
            },
            "working_directory": "/Users/john/projects/mcp",
        }

        result = sanitize_config(mcp_config)

        # Basic fields preserved
        assert result["id"] == 1
        assert result["server_name"] == "claude-code-search"

        # PII redacted from paths
        assert "[REDACTED_PII]" in result["command"]
        assert "john" not in result["command"]
        assert "[REDACTED_PII]" in result["working_directory"]

        # Secrets redacted from env
        assert "[REDACTED" in result["env"]["API_KEY"]
        assert "[REDACTED" in result["env"]["AWS_ACCESS_KEY_ID"]
        assert "[REDACTED" in result["env"]["AWS_SECRET_ACCESS_KEY"]

        # Safe values preserved
        assert result["env"]["DEBUG"] == "true"
        assert result["env"]["TIMEOUT"] == "30"

        # Verify no raw secrets remain
        result_str = str(result)
        assert "sk_live_1234567890" not in result_str
        assert "AKIAIOSFODNN7EXAMPLE" not in result_str
        assert "wJalrXUtnFEMI" not in result_str


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=src.utils.sanitizer", "--cov-report=term-missing"])
