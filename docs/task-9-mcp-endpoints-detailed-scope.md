# Task #9: MCP Server Endpoints - Updated Scope with Security

**Date**: 2025-11-10  
**Status**: ⏳ Pending  
**Phase**: 5.5  
**Estimated Time**: 2-3 days  
**Priority**: HIGH (Core API feature + Security critical)

---

## Executive Summary

Task #9 now includes **two major components**:

1. **MCP Server Query Endpoints** (Read-only API for MCP server information)
2. **Secret Sanitization System** (Security feature to prevent secrets leaking to GitHub)

The sanitization system is **critical** and must be implemented alongside the endpoints to ensure no sensitive data ever leaves the system.

---

## Detailed Scope

### ✅ INCLUDED: MCP Server Query Endpoints

**REST API Endpoints (6 total):**

| Endpoint | Method | Purpose | Response |
|----------|--------|---------|----------|
| `/api/v1/mcp-servers` | GET | List all MCP servers | Array of server summaries |
| `/api/v1/mcp-servers/{id}` | GET | Get server details | Server object with full info |
| `/api/v1/mcp-servers/{id}/status` | GET | Operational status | Status, uptime, health |
| `/api/v1/mcp-servers/{id}/config` | GET | Configuration (REDACTED) | Config with secrets redacted |
| `/api/v1/mcp-servers/{id}/capabilities` | GET | Available tools/resources | List of tools, resources |
| `/api/v1/mcp-servers/{id}/logs` | GET | Recent logs (REDACTED) | Recent log lines, sanitized |

**Key Features:**
- Read-only (no modifications)
- Paginated list response
- Query filtering by status, name
- Comprehensive error handling
- Fast responses (<100ms)

**Example Response (Auto-sanitized):**
```json
{
  "id": 1,
  "name": "claude-code-search",
  "executable_path": "[REDACTED_PII]/bin/claude-code-search",
  "status": "active",
  "config": {
    "api_key": "[REDACTED_API_KEY]",
    "auth_token": "[REDACTED_AUTH_TOKEN]",
    "max_results": 100
  },
  "capabilities": ["search", "summarize", "explain"],
  "last_check": "2025-11-10T14:30:00Z"
}
```

---

### 🔐 INCLUDED: Secret Sanitization System

**Core Security Feature:**

**Purpose**: Automatically detect and redact ALL sensitive data before it leaves the system.

**What Gets Sanitized:**
- ✅ API keys and tokens (Bearer, OAuth, JWT)
- ✅ Passwords and credentials
- ✅ Connection strings with credentials
- ✅ File paths containing usernames (PII)
- ✅ Environment variables with secrets
- ✅ AWS/Azure credentials
- ✅ SSH keys and certificates
- ✅ Database passwords
- ✅ Authentication tokens
- ✅ Webhook URLs with tokens

**Sanitization Placeholder Format:**
```
[REDACTED_<TYPE>]

Examples:
- [REDACTED_API_KEY]
- [REDACTED_PASSWORD]
- [REDACTED_PII]
- [REDACTED_JWT_TOKEN]
- [REDACTED_CONNECTION_STRING]
```

**Integration Points:**
1. **MCP Server Endpoints** - All responses auto-sanitized
2. **Export Functions** - `export snapshot`, `export config` sanitized
3. **Logging System** - Log output sanitized
4. **CLI Output** - `config show`, etc. sanitized

**New File: `src/utils/sanitizer.py`**

Core functions:
- `redact_secrets(data, context)` - Main sanitization
- `is_likely_secret(value, key)` - Pattern detection
- `safe_export(data, format)` - Export-safe output
- `safe_log(message, context)` - Logging-safe output

**Testing:**
- Unit tests for all pattern types (>95% coverage)
- Integration tests with API, CLI, exports
- Negative tests for false positives
- Real data validation

---

## ❌ NOT INCLUDED (Out of Scope)

| Feature | Why Not | Alternative |
|---------|---------|-------------|
| Starting/stopping MCP servers | OS-level process management | Use Claude's built-in controls |
| Installing MCP packages | Complex package management | Manual installation |
| Modifying MCP configuration | Too risky - could break Claude | Manual config edits |
| Testing MCP connections | Beyond scope of config scanning | Manual testing |
| Executing MCP server tools | Claude's responsibility | N/A |
| Caching secrets | Would increase risk | No caching |
| Configurable redaction bypass | Security risk | Use raw files if needed |

---

## Implementation Breakdown

### Part 1: Secret Sanitization (2 days) 🔐

**Phase 1a: Core Module** (1 day)
- Create `src/utils/sanitizer.py`
- Implement pattern detection
- Implement redaction engine
- Add configuration system

**Phase 1b: Testing & Integration** (1 day)
- Write comprehensive unit tests (>95% coverage)
- Integrate with logging
- Integrate with export functions
- Test with real data

### Part 2: MCP Server Endpoints (1 day)

**Phase 2a: Endpoint Implementation** (0.5 days)
- Create `src/api/routes/mcp.py`
- Implement 6 endpoints
- Add query filtering
- Add error handling

**Phase 2b: Integration & Testing** (0.5 days)
- Integrate with database queries
- Apply sanitization middleware
- Write endpoint tests
- Performance testing

---

## Database Schemas Used

### McpServer Model
```python
class McpServer(Base):
    __tablename__ = "mcp_servers"
    
    id: Mapped[int]
    name: Mapped[str]
    executable_path: Mapped[str]
    status: Mapped[str]  # 'active', 'inactive'
    capabilities: Mapped[list[str]]  # JSON
    config: Mapped[dict]  # JSON (will be sanitized)
    last_check: Mapped[datetime]
    
    # Relationship
    snapshots: Mapped[list["Snapshot"]]
```

### Related Models
- `Snapshot` - Links to snapshots where detected
- `SnapshotMcpServer` - Join table for relationship

---

## API Response Examples

### 1. List MCP Servers

**Request:**
```
GET /api/v1/mcp-servers?status=active&limit=10
```

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "name": "claude-code-search",
      "status": "active",
      "capabilities": ["search", "summarize"],
      "last_check": "2025-11-10T14:30:00Z"
    },
    {
      "id": 2,
      "name": "claude-browser",
      "status": "inactive",
      "capabilities": ["visit", "screenshot"],
      "last_check": "2025-11-09T20:15:00Z"
    }
  ],
  "total": 2,
  "page": 1,
  "page_size": 10
}
```

### 2. Get Server Details (With Auto-Sanitization)

**Request:**
```
GET /api/v1/mcp-servers/1
```

**Response:**
```json
{
  "id": 1,
  "name": "claude-code-search",
  "executable_path": "[REDACTED_PII]/.local/bin/claude-code-search",
  "status": "active",
  "config": {
    "api_key": "[REDACTED_API_KEY]",
    "db_url": "[REDACTED_CONNECTION_STRING]",
    "timeout": 30,
    "retry_count": 3
  },
  "capabilities": ["search", "summarize", "explain"],
  "last_check": "2025-11-10T14:30:00Z"
}
```

### 3. Server Status

**Request:**
```
GET /api/v1/mcp-servers/1/status
```

**Response:**
```json
{
  "status": "active",
  "uptime_seconds": 45280,
  "health": "healthy",
  "last_error": null,
  "request_count": 245,
  "avg_response_ms": 42
}
```

---

## Security Considerations

### What Gets Redacted in MCP Endpoints

1. **Server Configuration**
   - ✅ API keys → `[REDACTED_API_KEY]`
   - ✅ Passwords → `[REDACTED_PASSWORD]`
   - ✅ Connection strings → `[REDACTED_CONNECTION_STRING]`
   - ✅ Auth tokens → `[REDACTED_AUTH_TOKEN]`

2. **File Paths**
   - ✅ Usernames in paths → `[REDACTED_PII]`
   - ✅ Email addresses → `[REDACTED_PII]`
   - ✅ Home directories → `[REDACTED_PII]`

3. **Logs**
   - ✅ Error messages with secrets → Redacted
   - ✅ Stack traces with credentials → Redacted
   - ✅ Debug output → Redacted

### Why This Matters

**Scenario 1: Export then Commit**
```
User: python -m src.cli.commands export snapshot 1
User: git add snapshot-export.json
User: git commit -m "Add snapshot data"
Result: ❌ PROTECTED - All secrets already redacted in export
```

**Scenario 2: View Config**
```
User: python -m src.cli.commands config show
User: Copy output to documentation
Result: ❌ PROTECTED - Config output automatically sanitized
```

**Scenario 3: API Usage**
```
Client: GET /api/v1/mcp-servers/1
Response: Contains [REDACTED_API_KEY] not real key
Result: ❌ PROTECTED - Never exposes real secrets
```

---

## Testing Strategy

### Unit Tests (sanitizer.py)
```python
✅ test_api_key_detection()
✅ test_password_redaction()
✅ test_connection_string_redaction()
✅ test_jwt_token_detection()
✅ test_aws_credentials()
✅ test_path_with_username()
✅ test_no_false_positives()
✅ test_case_insensitivity()
✅ test_multiple_types()
✅ test_custom_patterns()

# Coverage: >95%
```

### Integration Tests
```python
✅ test_mcp_list_sanitized()
✅ test_mcp_details_sanitized()
✅ test_export_snapshot_sanitized()
✅ test_export_config_sanitized()
✅ test_logs_sanitized()
✅ test_api_response_sanitized()
```

### Security Tests
```python
✅ test_no_real_keys_in_export()
✅ test_no_passwords_in_logs()
✅ test_no_tokens_in_responses()
✅ test_no_pii_in_output()
```

---

## Deliverables

### Code
- ✅ `src/utils/sanitizer.py` (~300 lines)
- ✅ `src/api/routes/mcp.py` (~250 lines)
- ✅ Middleware integration
- ✅ Logging integration

### Tests
- ✅ `tests/test_sanitizer.py` (~400 lines, >95% coverage)
- ✅ `tests/test_mcp_endpoints.py` (~300 lines)

### Documentation
- ✅ `docs/security-sanitization-design.md` (comprehensive)
- ✅ API endpoint documentation
- ✅ Security best practices guide

### Configuration
- ✅ `config/sanitization.yaml` (patterns and rules)
- ✅ Pre-commit hooks (optional)

---

## Success Criteria

✅ **Core Endpoints**
- All 6 MCP endpoints implemented
- All endpoints return <100ms
- All endpoints properly paginated
- All error cases handled

✅ **Sanitization**
- No API keys in any output
- No passwords in any output
- No connection strings with credentials
- No PII (usernames, emails) in paths
- >95% test coverage
- Zero false positives on normal values

✅ **Integration**
- All exports sanitized
- All logs sanitized
- All API responses sanitized
- All CLI output sanitized

✅ **Documentation**
- Design document complete
- API docs complete
- Security guide complete
- Developer guide updated

---

## Timeline

- **Day 1**: Sanitizer implementation & testing
- **Day 2**: Integration & comprehensive testing
- **Day 3**: MCP endpoints & final validation

**Total: 2-3 days**

---

## Blockers & Dependencies

**Depends On:**
- ✅ Phase 5.2 (Snapshot endpoints) - Already complete
- ✅ MCP Server model in database - Already created

**Blocks:**
- None directly (can work in parallel with other Phase 5 tasks)

**Related To:**
- Task #5.3 (Path endpoints) - Can use same sanitizer
- Task #5.6 (Claude config endpoints) - Can use same sanitizer
- Task #5.8 (Enhanced exports) - Can use same sanitizer

---

## Communication

This is a **security-critical** task. Key points:

1. **Zero tolerance for secrets in output** - All sensitive data must be redacted
2. **Comprehensive testing required** - >95% coverage for sanitizer
3. **All integration points must use sanitizer** - No exceptions
4. **Documentation is security** - Help developers use it correctly
