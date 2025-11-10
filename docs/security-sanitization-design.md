# Secret Sanitization Security Design

**Document Status**: 🔐 **SECURITY CRITICAL**  
**Date**: 2025-11-10  
**Purpose**: Ensure no sensitive data (secrets, credentials, PII) is ever exposed in exports, logs, API responses, or Git history

---

## Overview

The Claude Config Editor scans system paths and configuration files that may contain sensitive information such as:
- API keys and tokens
- Database credentials
- File paths with user information (PII)
- Authentication tokens (Bearer, OAuth, JWT)
- Connection strings with passwords
- Environment variable values with secrets

This design document defines a comprehensive sanitization system to automatically detect and redact sensitive data before it leaves the system.

---

## Problem Statement

**Risk**: Accidentally committing sensitive data to Git/GitHub

**Examples**:
- Export a snapshot → GitHub → Exposed API keys
- Log file shows credentials → Committed to version control
- Export config → Contains database passwords
- API response includes environment variables with secrets

**Solution**: Implement automatic redaction system that:
1. Detects likely secrets using pattern matching
2. Replaces sensitive data with placeholder strings
3. Applies globally to exports, logs, and API responses
4. Cannot be bypassed without explicit developer action

---

## Architecture

### Module: `src/utils/sanitizer.py`

**Responsibilities:**
1. Pattern-based secret detection
2. Safe redaction with placeholder strings
3. Integration points for export, logging, and API
4. Configuration for redaction rules

**Core Functions:**

```python
def redact_secrets(data: str | dict | list, context: str = "general") -> str | dict | list:
    """
    Redact sensitive information from data.
    
    Args:
        data: String, dict, or list containing potential secrets
        context: "general", "log", "export", "api" (controls sensitivity level)
    
    Returns:
        Data with secrets replaced by placeholder strings
    """

def is_likely_secret(value: str, key: str = "") -> tuple[bool, str]:
    """
    Detect if a value is likely a secret.
    
    Args:
        value: String value to check
        key: Variable name/key (helps with heuristics)
    
    Returns:
        (is_secret: bool, secret_type: str) - e.g., (True, "API_KEY")
    """

def safe_export(data: dict | str, format: str = "json") -> str:
    """
    Prepare data for export with full sanitization.
    
    Args:
        data: Data to export
        format: "json", "yaml", "html", "csv"
    
    Returns:
        Sanitized export string
    """

def safe_log(message: str, secrets_context: dict | None = None) -> str:
    """
    Prepare message for logging with redaction.
    
    Args:
        message: Log message
        secrets_context: Additional values to treat as secrets
    
    Returns:
        Sanitized message safe for logging
    """

def get_sanitization_report() -> dict:
    """
    Get report of sanitized items for debugging.
    
    Returns:
        Dict with counts by type and sample redactions
    """
```

---

## Detection Patterns

### Pattern Categories

#### 1. **API Keys & Authentication Tokens**
```python
patterns = [
    r'api[_-]?key["\']?\s*[:=]\s*["\']?([a-zA-Z0-9\-_.]{20,})["\']?',
    r'api[_-]?secret["\']?\s*[:=]\s*["\']?([a-zA-Z0-9\-_.]{20,})["\']?',
    r'bearer\s+([a-zA-Z0-9\-_.]+)',
    r'token["\']?\s*[:=]\s*["\']?([a-zA-Z0-9\-_.]{20,})["\']?',
    r'access[_-]?token["\']?\s*[:=]\s*["\']?([a-zA-Z0-9\-_.]{20,})["\']?',
]
TYPE = "API_KEY"
PLACEHOLDER = "[REDACTED_API_KEY]"
```

#### 2. **Passwords & Credentials**
```python
patterns = [
    r'password["\']?\s*[:=]\s*["\']?([^"\'\s]{6,})["\']?',
    r'passwd["\']?\s*[:=]\s*["\']?([^"\'\s]{6,})["\']?',
    r'pwd["\']?\s*[:=]\s*["\']?([^"\'\s]{6,})["\']?',
    r'secret["\']?\s*[:=]\s*["\']?([^"\'\s]{6,})["\']?',
    r'credential["\']?\s*[:=]\s*["\']?([^"\'\s]{6,})["\']?',
]
TYPE = "PASSWORD"
PLACEHOLDER = "[REDACTED_PASSWORD]"
```

#### 3. **Connection Strings**
```python
patterns = [
    r'(mongodb|mysql|postgresql|sqlite)://[^@]*:[^@]+@[^\s"\']+',
    r'(Server=.*?;.*?Password=.*?;)',
    r'(connection[_-]?string["\']?\s*[:=]\s*["\']?[^"\'\s]+)',
]
TYPE = "CONNECTION_STRING"
PLACEHOLDER = "[REDACTED_CONNECTION_STRING]"
```

#### 4. **AWS Credentials**
```python
patterns = [
    r'AKIA[0-9A-Z]{16}',  # AWS Access Key ID
    r'aws[_-]?secret[_-]?access[_-]?key["\']?\s*[:=]\s*["\']?([a-zA-Z0-9/+=]{40})["\']?',
]
TYPE = "AWS_CREDENTIAL"
PLACEHOLDER = "[REDACTED_AWS_CREDENTIAL]"
```

#### 5. **JWT Tokens**
```python
patterns = [
    r'eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}',
]
TYPE = "JWT_TOKEN"
PLACEHOLDER = "[REDACTED_JWT_TOKEN]"
```

#### 6. **Personal Information in Paths**
```python
patterns = [
    r'C:\\Users\\([^\\"]+)',  # Windows username in path
    r'/home/([^\\/]+)',        # Linux username in path
    r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',  # Email
]
TYPE = "PII"
PLACEHOLDER = "[REDACTED_PII]"
```

#### 7. **OAuth & Social Media Tokens**
```python
patterns = [
    r'oauth[_-]?token["\']?\s*[:=]\s*["\']?([a-zA-Z0-9\-_.]{20,})["\']?',
    r'github[_-]?token["\']?\s*[:=]\s*["\']?ghp_[a-zA-Z0-9]{36}',
    r'slack[_-]?token["\']?\s*[:=]\s*["\']?xox[a-z]-[0-9]+-[0-9]+-[a-zA-Z0-9]+',
]
TYPE = "OAUTH_TOKEN"
PLACEHOLDER = "[REDACTED_OAUTH_TOKEN]"
```

#### 8. **SSH Keys & Certificates**
```python
patterns = [
    r'-----BEGIN (RSA|DSA|EC|OPENSSH|PGP) PRIVATE KEY-----',
    r'-----BEGIN CERTIFICATE-----',
]
TYPE = "PRIVATE_KEY"
PLACEHOLDER = "[REDACTED_PRIVATE_KEY]"
```

---

## Integration Points

### 1. **API Responses** (`src/api/routes/`)

```python
# In route handlers before returning response
from src.utils.sanitizer import safe_export

@router.get("/mcp-servers/{server_id}/config")
async def get_mcp_config(server_id: int):
    config_data = await service.get_config(server_id)
    sanitized = safe_export(config_data, context="api")
    return sanitized
```

### 2. **Export Functions** (`src/cli/commands/export.py`)

```python
# Before writing to file
from src.utils.sanitizer import safe_export

async def _export_json(snapshot, paths, output, include_content, compress):
    export_data = {
        "snapshot": snapshot_data.model_dump(),
        "paths": [p.to_dict() for p in paths]
    }
    
    sanitized = safe_export(export_data, format="json")
    
    with open(output, "w") as f:
        f.write(sanitized)
```

### 3. **Logging** (`src/utils/logger.py`)

```python
# In logging configuration
from src.utils.sanitizer import safe_log

class SanitizingFormatter(logging.Formatter):
    def format(self, record):
        record.msg = safe_log(record.msg)
        return super().format(record)
```

### 4. **CLI Output** (`src/cli/commands/config.py`)

```python
# Before printing config show
from src.utils.sanitizer import safe_export

def show_config():
    config = get_settings()
    sanitized = safe_export(config.model_dump(), context="cli")
    console.print_json(data=sanitized)
```

---

## Configuration

### Sensitivity Levels

**General** (Default - Most Strict)
- Redacts: API keys, passwords, tokens, PII, connection strings

**Log** (Careful)
- Redacts: Passwords, tokens, API keys
- Preserves: Non-sensitive config values

**Export** (Very Strict)
- Redacts: Everything (API keys, passwords, tokens, PII, paths with usernames)
- Use for: Public exports, GitHub commits

**API** (Moderate)
- Redacts: Passwords, tokens, raw API keys
- Preserves: Host information, port numbers
- Use for: API responses to local client

### Custom Rules

```python
# In config/sanitization.yaml
redaction_rules:
  strict: true  # Always redact secrets
  
custom_patterns:
  - pattern: 'my_custom_secret_\d+'
    placeholder: '[REDACTED_CUSTOM]'
    type: 'CUSTOM'
  
always_redact:
  - 'PRIVATE_TOKEN'
  - 'SECRET_KEY'
  - 'DB_PASSWORD'

never_redact:
  - 'LOG_LEVEL'
  - 'PORT'
  - 'HOST'
```

---

## Testing Strategy

### Unit Tests (`tests/test_sanitizer.py`)

```python
def test_api_key_detection():
    """API keys are detected and redacted"""
    text = 'api_key: "sk_live_abc123def456ghi789"'
    result = redact_secrets(text)
    assert "[REDACTED_API_KEY]" in result
    assert "sk_live_abc123def456ghi789" not in result

def test_password_redaction():
    """Passwords are detected regardless of format"""
    # test password="secret123"
    # test PASSWORD='MySecretPassword'
    # test passwd:=mysecretpassword
    
def test_path_with_username():
    """File paths with usernames are redacted"""
    path = "C:\\Users\\john.smith\\AppData\\...\\claude_config"
    result = redact_secrets(path)
    assert "[REDACTED_PII]" in result
    assert "john.smith" not in result

def test_connection_string():
    """Database connection strings redacted"""
    connstr = "postgresql://user:password@localhost:5432/db"
    result = redact_secrets(connstr)
    assert "[REDACTED_CONNECTION_STRING]" in result

def test_jwt_token():
    """JWT tokens are detected and redacted"""
    jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIn0.TJVA95OrM7E2cBab30RMHrHDcEfxjoYZgeFONFh7HgQ"
    result = redact_secrets(jwt)
    assert "[REDACTED_JWT_TOKEN]" in result

def test_no_false_positives():
    """Normal values not redacted"""
    normal_text = "host: localhost, port: 8765, log_level: INFO"
    result = redact_secrets(normal_text)
    assert result == normal_text  # Unchanged

def test_export_json_sanitizes():
    """JSON export sanitizes secrets"""
    data = {
        "config": {"api_key": "sk_test_123", "host": "localhost"},
        "paths": ["/Users/bob/config/file.json"]
    }
    result = safe_export(data, format="json")
    assert "[REDACTED_API_KEY]" in result
    assert "[REDACTED_PII]" in result

def test_export_yaml_sanitizes():
    """YAML export sanitizes secrets"""
    # Similar to JSON test
    
def test_sanitization_report():
    """Sanitization report tracks redactions"""
    data = "api_key: sk_123, password: pwd_456"
    redact_secrets(data)
    report = get_sanitization_report()
    assert report["total_redacted"] == 2
    assert "API_KEY" in report["by_type"]
```

**Coverage Goal**: >95% for sanitizer module

---

## Error Handling

### What NOT to Do
```python
# ❌ DON'T log the full error with secrets
logger.error(f"Failed to connect: {connection_string}")

# ❌ DON'T print raw config
print(config)

# ❌ DON'T return full traceback with secrets
raise Exception(f"Error with token: {token}")
```

### What TO Do
```python
# ✅ DO sanitize before logging
logger.error(f"Failed to connect: {safe_log(connection_string)}")

# ✅ DO sanitize before printing
print(safe_export(config))

# ✅ DO sanitize error messages
logger.error(safe_log(f"Error with token: {token}"))
```

---

## Implementation Phases

### Phase 1: Core Sanitizer (2-3 days)
- [x] Create `src/utils/sanitizer.py`
- [x] Implement detection patterns
- [x] Implement redaction functions
- [x] Add unit tests (>95% coverage)
- [x] Integration with logger

### Phase 2: Integration (1-2 days)
- [x] Integrate with API routes
- [x] Integrate with export commands
- [x] Integrate with CLI output
- [x] Test all integration points

### Phase 3: Verification (1 day)
- [x] Audit all export paths
- [x] Audit all log outputs
- [x] Audit all API responses
- [x] Ensure no secrets reach Git

---

## Pre-commit Hooks (Bonus)

Add Git pre-commit hook to catch secrets:
```bash
#!/bin/bash
# .git/hooks/pre-commit

python -c "
from src.utils.sanitizer import redact_secrets
import sys

# Check for common secret patterns in staged files
# If found, prevent commit
"
```

---

## Compliance Checklist

- [ ] No API keys in exports
- [ ] No passwords in logs
- [ ] No database credentials in responses
- [ ] No PII (usernames, emails) in paths
- [ ] No tokens in configuration files
- [ ] No secrets in Git history
- [ ] >95% test coverage for sanitizer
- [ ] All export formats tested
- [ ] All integration points tested
- [ ] Documentation complete

---

## Monitoring & Validation

### Periodic Audits
```python
def audit_for_secrets():
    """Scan logs and exports for accidentally committed secrets"""
    # Check log files
    # Check exported files
    # Report findings
```

### Developer Warnings
- Warn if exporting with verbose mode
- Warn if logging at DEBUG level (extra verbose)
- Warn before committing if sanitizer ran recently

---

## References

- OWASP Secrets Management: https://owasp.org/www-community/
- Python Regex Security: https://docs.python.org/3/library/re.html
- Git Secret Detection: https://help.github.com/articles/about-git-large-file-storage
