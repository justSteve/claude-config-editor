# MCP Server API Reference

**Version**: v2.0
**Last Updated**: 2025-11-11
**Base Path**: `/api/v1`

---

## Overview

The MCP (Model Context Protocol) Server API provides endpoints for querying and analyzing MCP server configurations found in Claude Desktop snapshots. All responses containing sensitive data are automatically sanitized to prevent accidental exposure of secrets, credentials, and personal information.

### Security Features

**Automatic Sanitization** is applied to endpoints marked with 🔒:
- API keys, tokens, and credentials redacted
- Connection strings with passwords masked
- PII (usernames, emails) removed from file paths
- Sanitized responses include `sanitized: true` flag

### Authentication

Currently, no authentication is required. This API is designed for local-only use.

---

## Endpoints

### 1. List MCP Servers

List all MCP servers found across snapshots with pagination and filtering.

**Endpoint**: `GET /api/v1/mcp-servers`

**Query Parameters**:
- `page` (integer, default: 1) - Page number
- `limit` (integer, default: 20, max: 100) - Items per page
- `snapshot_id` (integer, optional) - Filter by snapshot ID
- `server_name` (string, optional) - Filter by server name (partial match, case-insensitive)

**Response**: `200 OK`

```json
{
  "items": [
    {
      "id": 1,
      "server_name": "filesystem",
      "command": "npx @modelcontextprotocol/server-filesystem",
      "snapshot_id": 5,
      "config_file": "claude_desktop_config.json",
      "first_seen": "2025-11-10T14:30:00",
      "last_seen": "2025-11-11T09:15:00"
    }
  ],
  "total": 3,
  "page": 1,
  "page_size": 20,
  "total_pages": 1,
  "has_next": false,
  "has_previous": false
}
```

**Example Usage**:

```bash
# List all MCP servers
curl http://localhost:8000/api/v1/mcp-servers

# Filter by snapshot
curl http://localhost:8000/api/v1/mcp-servers?snapshot_id=5

# Search by name
curl http://localhost:8000/api/v1/mcp-servers?server_name=filesystem

# Pagination
curl http://localhost:8000/api/v1/mcp-servers?page=2&limit=10
```

---

### 2. Get MCP Server Details 🔒

Get detailed information about a specific MCP server configuration.

**Endpoint**: `GET /api/v1/mcp-servers/{server_id}`

**Path Parameters**:
- `server_id` (integer, required) - MCP server ID

**Response**: `200 OK`

```json
{
  "id": 1,
  "server_name": "filesystem",
  "command": "npx @modelcontextprotocol/server-filesystem",
  "args": [
    "/Users/[REDACTED_PII]/projects"
  ],
  "env": {
    "NODE_ENV": "production",
    "API_KEY": "[REDACTED_API_KEY]"
  },
  "working_directory": "/Users/[REDACTED_PII]/claude-mcp",
  "snapshot_id": 5,
  "config_file": "claude_desktop_config.json",
  "file_path": "/Users/[REDACTED_PII]/Library/Application Support/Claude/claude_desktop_config.json",
  "created_at": "2025-11-10T14:30:00",
  "updated_at": "2025-11-11T09:15:00"
}
```

**Error Responses**:
- `404 Not Found` - Server ID does not exist

**Example Usage**:

```bash
curl http://localhost:8000/api/v1/mcp-servers/1
```

---

### 3. Get MCP Server Status

Get operational status and tracking information for an MCP server.

**Endpoint**: `GET /api/v1/mcp-servers/{server_id}/status`

**Path Parameters**:
- `server_id` (integer, required) - MCP server ID

**Response**: `200 OK`

```json
{
  "server_id": 1,
  "server_name": "filesystem",
  "status": "detected",
  "last_seen": "2025-11-11T09:15:00",
  "first_seen": "2025-11-10T14:30:00",
  "snapshot_count": 3,
  "config_locations": [
    "claude_desktop_config.json",
    "user_mcp_config.json"
  ]
}
```

**Status Values**:
- `detected` - Server found in recent snapshot
- `configured` - Server exists but not recently seen
- `unknown` - Status cannot be determined

**Error Responses**:
- `404 Not Found` - Server ID does not exist

**Example Usage**:

```bash
curl http://localhost:8000/api/v1/mcp-servers/1/status
```

---

### 4. Get MCP Server Configuration 🔒

Get the full configuration for an MCP server with automatic sanitization of sensitive data.

**Endpoint**: `GET /api/v1/mcp-servers/{server_id}/config`

**Path Parameters**:
- `server_id` (integer, required) - MCP server ID

**Response**: `200 OK`

```json
{
  "server_id": 1,
  "server_name": "github",
  "command": "npx @modelcontextprotocol/server-github",
  "args": {
    "owner": "myorg",
    "repo": "myrepo"
  },
  "env": {
    "GITHUB_TOKEN": "[REDACTED_TOKEN]",
    "GITHUB_API_URL": "https://api.github.com"
  },
  "working_directory": null,
  "sanitized": true
}
```

**Sanitization Applied**:
- API keys and tokens → `[REDACTED_API_KEY]`, `[REDACTED_TOKEN]`
- Passwords → `[REDACTED_PASSWORD]`
- Connection strings → `[REDACTED_CONNECTION_STRING]`
- AWS credentials → `[REDACTED_AWS_KEY]`
- PII in paths → `/Users/[REDACTED_PII]/...`

**Error Responses**:
- `404 Not Found` - Server ID does not exist

**Example Usage**:

```bash
curl http://localhost:8000/api/v1/mcp-servers/1/config
```

---

### 5. Get MCP Server Capabilities

Get detected capabilities based on server configuration analysis.

**Endpoint**: `GET /api/v1/mcp-servers/{server_id}/capabilities`

**Path Parameters**:
- `server_id` (integer, required) - MCP server ID

**Response**: `200 OK`

```json
{
  "server_id": 1,
  "server_name": "filesystem",
  "command_type": "node",
  "has_args": true,
  "has_env": false,
  "has_working_dir": true
}
```

**Command Types**:
- `node` - Node.js/NPX command
- `python` - Python script
- `binary` - Native binary executable
- `unknown` - Cannot determine type

**Error Responses**:
- `404 Not Found` - Server ID does not exist

**Example Usage**:

```bash
curl http://localhost:8000/api/v1/mcp-servers/1/capabilities
```

---

### 6. Get MCP Server Logs 🔒

Get information about log files associated with an MCP server.

**Endpoint**: `GET /api/v1/mcp-servers/{server_id}/logs`

**Path Parameters**:
- `server_id` (integer, required) - MCP server ID

**Response**: `200 OK`

```json
{
  "server_id": 1,
  "server_name": "filesystem",
  "log_files_found": 2,
  "log_locations": [
    "/Users/[REDACTED_PII]/Library/Logs/Claude/mcp-server-filesystem.log",
    "/Users/[REDACTED_PII]/Library/Logs/Claude/mcp-server-filesystem-error.log"
  ],
  "sanitized": true
}
```

**Note**: This endpoint returns log file locations (sanitized), not log contents.

**Error Responses**:
- `404 Not Found` - Server ID does not exist

**Example Usage**:

```bash
curl http://localhost:8000/api/v1/mcp-servers/1/logs
```

---

### 7. Get MCP Server Statistics

Get aggregated statistics about MCP servers across all snapshots.

**Endpoint**: `GET /api/v1/mcp-servers/stats`

**Response**: `200 OK`

```json
{
  "total_servers": 5,
  "total_configurations": 12,
  "servers_by_snapshot": {
    "Snapshot 1 (2025-11-10 14:30)": 3,
    "Snapshot 2 (2025-11-10 18:45)": 4,
    "Snapshot 3 (2025-11-11 09:15)": 5
  },
  "most_common_servers": [
    {
      "server_name": "filesystem",
      "count": 8
    },
    {
      "server_name": "github",
      "count": 3
    },
    {
      "server_name": "sqlite",
      "count": 1
    }
  ],
  "config_file_locations": [
    "claude_desktop_config.json",
    "user_mcp_config.json",
    "project_mcp_config.json"
  ]
}
```

**Example Usage**:

```bash
curl http://localhost:8000/api/v1/mcp-servers/stats
```

---

## Data Models

### McpServerSummary

```typescript
{
  id: integer,                    // Unique server ID
  server_name: string,            // Server name
  command: string | null,         // Command to run server
  snapshot_id: integer,           // Snapshot where found
  config_file: string,            // Configuration file name
  first_seen: string,             // ISO 8601 timestamp
  last_seen: string               // ISO 8601 timestamp
}
```

### McpServerDetail

```typescript
{
  id: integer,
  server_name: string,
  command: string | null,
  args: object | null,            // Command arguments
  env: object | null,             // Environment variables
  working_directory: string | null,
  snapshot_id: integer,
  config_file: string,
  file_path: string,              // Full path to config file
  created_at: string,             // ISO 8601 timestamp
  updated_at: string              // ISO 8601 timestamp
}
```

### McpServerStatusResponse

```typescript
{
  server_id: integer,
  server_name: string,
  status: "detected" | "configured" | "unknown",
  last_seen: string,              // ISO 8601 timestamp
  first_seen: string,             // ISO 8601 timestamp
  snapshot_count: integer,        // Number of snapshots containing this server
  config_locations: string[]      // Config file names
}
```

### McpServerConfigResponse

```typescript
{
  server_id: integer,
  server_name: string,
  command: string | null,
  args: object | null,
  env: object | null,
  working_directory: string | null,
  sanitized: boolean              // True if sanitization applied
}
```

### McpServerCapabilitiesResponse

```typescript
{
  server_id: integer,
  server_name: string,
  command_type: string | null,    // "node", "python", "binary", "unknown"
  has_args: boolean,
  has_env: boolean,
  has_working_dir: boolean
}
```

### McpServerLogsResponse

```typescript
{
  server_id: integer,
  server_name: string,
  log_files_found: integer,
  log_locations: string[],        // Sanitized paths
  sanitized: boolean
}
```

### McpServerStatsResponse

```typescript
{
  total_servers: integer,                      // Unique server count
  total_configurations: integer,               // Total configs across snapshots
  servers_by_snapshot: {[key: string]: integer}, // Snapshot → server count
  most_common_servers: Array<{                 // Top 10 most common
    server_name: string,
    count: integer
  }>,
  config_file_locations: string[]              // All config file locations
}
```

---

## Error Handling

### Standard Error Response

```json
{
  "detail": "Error message describing what went wrong"
}
```

### HTTP Status Codes

- `200 OK` - Request successful
- `400 Bad Request` - Invalid request parameters
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

---

## Security & Sanitization

### What Gets Sanitized?

**API Keys & Tokens**:
- Stripe-style keys (`sk_live_...`, `pk_test_...`)
- Generic API keys (24+ characters)
- Bearer tokens
- JWT tokens
- OAuth tokens

**Credentials**:
- Passwords in key-value pairs
- Connection strings with credentials
- AWS access keys and secret keys
- Azure credentials
- SSH private keys

**PII in Paths**:
- Usernames in `/Users/username/...`
- Usernames in `/home/username/...`
- Usernames in `C:\Users\username\...`
- Email addresses in paths

### Sanitization Patterns

Original values are replaced with descriptive placeholders:

```
sk_live_abc123... → [REDACTED_API_KEY]
mypassword123 → [REDACTED_PASSWORD]
postgresql://user:pass@host → [REDACTED_CONNECTION_STRING]
/Users/john/projects → /Users/[REDACTED_PII]/projects
AKIAIOSFODNN7EXAMPLE → [REDACTED_AWS_KEY]
```

### When Sanitization Applies

Sanitization is **automatic** for these endpoints:
- `GET /api/v1/mcp-servers/{id}` - Server details
- `GET /api/v1/mcp-servers/{id}/config` - Configuration
- `GET /api/v1/mcp-servers/{id}/logs` - Log file paths

Responses include `sanitized: true` when redaction has been applied.

---

## Use Cases

### 1. Audit MCP Server Configurations

List all MCP servers across snapshots to understand what's configured:

```bash
curl http://localhost:8000/api/v1/mcp-servers | jq '.items[] | {name: .server_name, command: .command}'
```

### 2. Track Server Changes Over Time

Compare server presence across snapshots:

```bash
# Get stats showing server distribution
curl http://localhost:8000/api/v1/mcp-servers/stats | jq '.servers_by_snapshot'

# Check server status
curl http://localhost:8000/api/v1/mcp-servers/1/status | jq '.snapshot_count'
```

### 3. Export Configurations Safely

Export server configurations with sensitive data redacted:

```bash
# Get all servers and their configs
for id in $(curl -s http://localhost:8000/api/v1/mcp-servers | jq -r '.items[].id'); do
  curl -s "http://localhost:8000/api/v1/mcp-servers/$id/config" | jq '.'
done
```

### 4. Identify Most Used Servers

Find which MCP servers are most commonly configured:

```bash
curl http://localhost:8000/api/v1/mcp-servers/stats | jq '.most_common_servers'
```

### 5. Debug Server Issues

Check server capabilities and logs:

```bash
# Get capabilities
curl http://localhost:8000/api/v1/mcp-servers/1/capabilities

# Find log locations
curl http://localhost:8000/api/v1/mcp-servers/1/logs
```

---

## Integration Examples

### Python

```python
import requests

# List all MCP servers
response = requests.get('http://localhost:8000/api/v1/mcp-servers')
servers = response.json()

for server in servers['items']:
    print(f"Server: {server['server_name']}")

    # Get detailed config (sanitized)
    config = requests.get(
        f'http://localhost:8000/api/v1/mcp-servers/{server["id"]}/config'
    ).json()

    if config['sanitized']:
        print("  ⚠️  Config contains redacted sensitive data")

    print(f"  Command: {config['command']}")
    print(f"  Env vars: {len(config.get('env', {}))}")
```

### JavaScript/TypeScript

```typescript
async function getMcpServers() {
  const response = await fetch('http://localhost:8000/api/v1/mcp-servers');
  const data = await response.json();

  for (const server of data.items) {
    console.log(`Server: ${server.server_name}`);

    // Get status
    const status = await fetch(
      `http://localhost:8000/api/v1/mcp-servers/${server.id}/status`
    ).then(r => r.json());

    console.log(`  Status: ${status.status}`);
    console.log(`  Seen in ${status.snapshot_count} snapshots`);
  }
}
```

### cURL + jq

```bash
#!/bin/bash

# Get all servers and their stats
echo "=== MCP Server Overview ==="

# Total stats
curl -s http://localhost:8000/api/v1/mcp-servers/stats | \
  jq -r '"Total servers: \(.total_servers)\nTotal configs: \(.total_configurations)"'

# List servers with details
curl -s "http://localhost:8000/api/v1/mcp-servers?limit=100" | \
  jq -r '.items[] | "\(.server_name) (ID: \(.id)) - Last seen: \(.last_seen)"'
```

---

## Testing

Run the integration test suite:

```bash
pytest tests/manual_test_mcp_endpoints.py -v -s
```

This tests all 7 MCP endpoints including:
- Listing with pagination
- Filtering by snapshot and name
- Server details retrieval
- Status, config, capabilities, logs
- Statistics endpoint
- Error handling (404 for invalid IDs)
- Sanitization verification

---

## Limitations

1. **Read-Only**: These endpoints only query snapshot data; they do not modify MCP server configurations
2. **Snapshot-Based**: Data reflects what was found during snapshot scans, not real-time server state
3. **No Authentication**: Designed for local use only; no auth/authz implemented
4. **No Pagination Limits**: Maximum 100 items per page
5. **Log Content**: The logs endpoint provides file locations, not log contents

---

## See Also

- [API Testing Guide](./API-TESTING-GUIDE.md) - How to test the API
- [Security Sanitization Design](./security-sanitization-design.md) - Sanitization details
- [Task 9 Scope](./task-9-mcp-endpoints-detailed-scope.md) - Implementation scope
- [Phase 5 API Plan](./phase-5-api-implementation-plan.md) - Overall API plan
