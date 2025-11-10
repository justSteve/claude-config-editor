# Phase 5: API Quick Reference Guide

**Last Updated**: 2025-11-09

---

## 🚀 Quick Start

### Start the API Server

```bash
# Development mode (with auto-reload)
uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8765

# Production mode
uvicorn src.api.app:app --host 0.0.0.0 --port 8765
```

### Access Points

- **API Documentation**: http://localhost:8765/docs
- **ReDoc**: http://localhost:8765/redoc
- **Health Check**: http://localhost:8765/health
- **OpenAPI JSON**: http://localhost:8765/openapi.json

---

## 📋 API Endpoints

### Snapshot Management

#### Create Snapshot
```http
POST /api/v1/snapshots
Content-Type: application/json

{
  "trigger_type": "api",
  "triggered_by": "user@example.com",
  "notes": "Production backup",
  "tags": ["production", "backup"]
}
```

#### List Snapshots
```http
GET /api/v1/snapshots?page=1&page_size=20&trigger_type=api&has_changes=true
```

**Query Parameters**:
- `page` - Page number (default: 1)
- `page_size` - Items per page (default: 50, max: 1000)
- `sort_by` - Field to sort by (default: snapshot_time)
- `sort_order` - Sort order: asc or desc (default: desc)
- `trigger_type` - Filter by trigger type
- `triggered_by` - Filter by triggered_by
- `os_type` - Filter by OS type
- `is_baseline` - Filter by baseline status
- `has_changes` - Filter by change status
- `search` - Search in notes and triggered_by
- `tags` - Filter by tags (ANY)
- `tags_all` - Filter by tags (ALL)

#### Get Snapshot Details
```http
GET /api/v1/snapshots/{snapshot_id}
```

#### Delete Snapshot
```http
DELETE /api/v1/snapshots/{snapshot_id}
```

#### Get Snapshot Statistics
```http
GET /api/v1/snapshots/{snapshot_id}/stats
```

#### Export Snapshot
```http
POST /api/v1/snapshots/{snapshot_id}/export?format=json
```

### Tag Management

#### Add Tag
```http
POST /api/v1/snapshots/{snapshot_id}/tags
Content-Type: application/json

{
  "tag_name": "production",
  "tag_type": "environment",
  "description": "Production environment",
  "created_by": "admin"
}
```

#### Remove Tag
```http
DELETE /api/v1/snapshots/{snapshot_id}/tags/{tag_id}
```

### Annotation Management

#### Add Annotation
```http
POST /api/v1/snapshots/{snapshot_id}/annotations
Content-Type: application/json

{
  "annotation_text": "Important backup before update",
  "annotation_type": "note",
  "created_by": "user@example.com"
}
```

#### List Annotations
```http
GET /api/v1/snapshots/{snapshot_id}/annotations
```

#### Remove Annotation
```http
DELETE /api/v1/snapshots/{snapshot_id}/annotations/{annotation_id}
```

### Health Check

#### Health Check
```http
GET /health
```

---

## 🧪 Testing Examples

### Using curl

```bash
# Create snapshot
curl -X POST "http://localhost:8765/api/v1/snapshots" \
  -H "Content-Type: application/json" \
  -d '{
    "trigger_type": "api",
    "triggered_by": "test-user",
    "notes": "Test snapshot",
    "tags": ["test"]
  }'

# List snapshots
curl "http://localhost:8765/api/v1/snapshots?page=1&page_size=10"

# Get snapshot details
curl "http://localhost:8765/api/v1/snapshots/1"

# Add tag
curl -X POST "http://localhost:8765/api/v1/snapshots/1/tags" \
  -H "Content-Type: application/json" \
  -d '{
    "tag_name": "production",
    "tag_type": "environment",
    "created_by": "admin"
  }'

# Export snapshot
curl "http://localhost:8765/api/v1/snapshots/1/export?format=json"

# Delete snapshot
curl -X DELETE "http://localhost:8765/api/v1/snapshots/1"
```

### Using Python

```python
import requests

BASE_URL = "http://localhost:8765/api/v1"

# Create snapshot
response = requests.post(
    f"{BASE_URL}/snapshots",
    json={
        "trigger_type": "api",
        "triggered_by": "test-user",
        "notes": "Test snapshot",
        "tags": ["test"]
    }
)
snapshot = response.json()
print(f"Created snapshot: {snapshot['snapshot_id']}")

# List snapshots
response = requests.get(
    f"{BASE_URL}/snapshots",
    params={"page": 1, "page_size": 10}
)
snapshots = response.json()
print(f"Total snapshots: {snapshots['total']}")

# Get snapshot details
response = requests.get(f"{BASE_URL}/snapshots/{snapshot['snapshot_id']}")
details = response.json()
print(f"Files found: {details['files_found']}")

# Add tag
response = requests.post(
    f"{BASE_URL}/snapshots/{snapshot['snapshot_id']}/tags",
    json={
        "tag_name": "production",
        "tag_type": "environment",
        "created_by": "admin"
    }
)
tag = response.json()
print(f"Added tag: {tag['tag_name']}")

# Export snapshot
response = requests.post(
    f"{BASE_URL}/snapshots/{snapshot['snapshot_id']}/export",
    params={"format": "json"}
)
export_data = response.json()
print(f"Exported snapshot with {len(export_data['paths'])} paths")
```

### Using Swagger UI

1. Start the server:
   ```bash
   uvicorn src.api.app:app --reload
   ```

2. Open browser:
   ```
   http://localhost:8765/docs
   ```

3. Try endpoints:
   - Click on endpoint
   - Click "Try it out"
   - Fill in parameters
   - Click "Execute"
   - See response

---

## 📊 Response Examples

### Create Snapshot Response

```json
{
  "snapshot_id": 1,
  "snapshot_hash": "a1b2c3d4e5f6...",
  "snapshot_time": "2025-11-09T12:00:00",
  "files_found": 15,
  "directories_found": 3,
  "total_size_bytes": 524288,
  "changes_detected": false,
  "changed_from_previous": null,
  "scan_duration_seconds": 0.0,
  "content_captured": 0,
  "errors_encountered": 0,
  "message": "Snapshot 1 created successfully"
}
```

### List Snapshots Response

```json
{
  "items": [
    {
      "id": 1,
      "snapshot_hash": "a1b2c3d4...",
      "snapshot_time": "2025-11-09T12:00:00",
      "trigger_type": "api",
      "triggered_by": "test-user",
      "files_found": 15,
      "directories_found": 3,
      "total_size_bytes": 524288,
      "changed_from_previous": null,
      "tags": ["test", "production"]
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "total_pages": 1,
  "has_next": false,
  "has_previous": false,
  "total_size_all_bytes": 524288,
  "date_range_start": "2025-11-09T12:00:00",
  "date_range_end": "2025-11-09T12:00:00"
}
```

### Snapshot Details Response

```json
{
  "id": 1,
  "snapshot_hash": "a1b2c3d4...",
  "snapshot_time": "2025-11-09T12:00:00",
  "trigger_type": "api",
  "triggered_by": "test-user",
  "notes": "Test snapshot",
  "os_type": "Windows",
  "os_version": "10.0.26200",
  "hostname": "DESKTOP-ABC123",
  "username": "user",
  "working_directory": "C:\\Users\\user\\project",
  "total_locations": 17,
  "files_found": 15,
  "directories_found": 3,
  "total_size_bytes": 524288,
  "changed_from_previous": null,
  "is_baseline": false,
  "tags": [
    {
      "id": 1,
      "tag_name": "test",
      "tag_type": null,
      "description": null,
      "created_at": "2025-11-09T12:00:00",
      "created_by": null
    }
  ],
  "annotations": [],
  "env_vars": [
    {
      "placeholder": "%USERPROFILE%",
      "resolved_path": "C:\\Users\\user"
    }
  ]
}
```

### Error Response

```json
{
  "error": "Snapshot 1 not found",
  "error_type": "NotFoundException",
  "details": {}
}
```

---

## 🔍 Filtering Examples

### Filter by Trigger Type

```http
GET /api/v1/snapshots?trigger_type=api
```

### Filter by Tags (ANY)

```http
GET /api/v1/snapshots?tags=production&tags=backup
```

### Filter by Tags (ALL)

```http
GET /api/v1/snapshots?tags_all=production&tags_all=backup
```

### Search in Notes

```http
GET /api/v1/snapshots?search=production
```

### Filter by Changes

```http
GET /api/v1/snapshots?has_changes=true
```

### Time Range Filter

```http
GET /api/v1/snapshots?time_range_start=2025-11-01T00:00:00&time_range_end=2025-11-09T23:59:59
```

### Sort by Size

```http
GET /api/v1/snapshots?sort_by=total_size_bytes&sort_order=desc
```

---

## 🎯 Common Use Cases

### Use Case 1: Create Backup Snapshot

```python
response = requests.post(
    "http://localhost:8765/api/v1/snapshots",
    json={
        "trigger_type": "api",
        "triggered_by": "backup-script",
        "notes": "Daily backup - 2025-11-09",
        "tags": ["backup", "daily", "production"]
    }
)
snapshot = response.json()
print(f"Backup snapshot created: {snapshot['snapshot_id']}")
```

### Use Case 2: Find Changed Snapshots

```python
response = requests.get(
    "http://localhost:8765/api/v1/snapshots",
    params={
        "has_changes": True,
        "sort_by": "snapshot_time",
        "sort_order": "desc",
        "page_size": 10
    }
)
changed_snapshots = response.json()
print(f"Found {changed_snapshots['total']} snapshots with changes")
```

### Use Case 3: Export Snapshot for Backup

```python
response = requests.post(
    f"http://localhost:8765/api/v1/snapshots/{snapshot_id}/export",
    params={"format": "json"}
)
export_data = response.json()

# Save to file
import json
with open(f"snapshot_{snapshot_id}.json", "w") as f:
    json.dump(export_data, f, indent=2)

print(f"Exported snapshot {snapshot_id} to file")
```

### Use Case 4: Tag Production Snapshots

```python
# Get all snapshots
response = requests.get("http://localhost:8765/api/v1/snapshots")
snapshots = response.json()

# Tag production snapshots
for snapshot in snapshots['items']:
    if snapshot['trigger_type'] == 'api':
        requests.post(
            f"http://localhost:8765/api/v1/snapshots/{snapshot['id']}/tags",
            json={
                "tag_name": "production",
                "tag_type": "environment",
                "created_by": "admin"
            }
        )
```

---

## 🐛 Troubleshooting

### Issue: Database Connection Error

**Error**: `Database error occurred`

**Solution**:
1. Check database file exists
2. Check database permissions
3. Check database URL in configuration

### Issue: Snapshot Creation Fails

**Error**: `Validation failed`

**Solution**:
1. Check request body format
2. Check required fields
3. Check field types

### Issue: Snapshot Not Found

**Error**: `Snapshot 1 not found`

**Solution**:
1. Check snapshot ID exists
2. Check database has snapshots
3. Check snapshot wasn't deleted

---

## 📚 Additional Resources

### Documentation

- **Full Review**: `doc/phase-5-review.md`
- **Progress Summary**: `doc/phase-5-progress-summary.md`
- **Implementation Plan**: `doc/phase-5-api-implementation-plan.md`

### Code

- **API App**: `src/api/app.py`
- **Snapshot Routes**: `src/api/routes/snapshots.py`
- **Snapshot Service**: `src/api/services/snapshot_service.py`
- **Exceptions**: `src/api/exceptions.py`

### Schemas

- **Request Models**: `src/core/schemas/requests.py`
- **Response Models**: `src/core/schemas/responses.py`
- **Converters**: `src/core/schemas/converters.py`

---

## 🎉 Summary

**Status**: ✅ **Functional and Ready for Use**

**What Works**:
- ✅ Snapshot creation (with real file scanning)
- ✅ Snapshot listing (with filtering and pagination)
- ✅ Snapshot details
- ✅ Tag management
- ✅ Annotation management
- ✅ Export functionality
- ✅ Error handling
- ✅ API documentation

**What's Next**:
- 🟡 Path endpoints
- 🟡 Change endpoints
- 🟡 Enhanced export/import

---

**Last Updated**: 2025-11-09

