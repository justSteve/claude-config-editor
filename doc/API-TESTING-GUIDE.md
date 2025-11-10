# API Testing Guide

**Last Updated**: 2025-11-09

---

## 🚀 Quick Start

### Step 1: Start the API Server

**On Windows**:
```bash
start_api.bat
```

**On Linux/Mac**:
```bash
chmod +x start_api.sh
./start_api.sh
```

**Or manually**:
```bash
uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8765
```

### Step 2: Verify Server is Running

Open your browser and navigate to:
- **API Documentation**: http://localhost:8765/docs
- **Health Check**: http://localhost:8765/health

You should see:
- ✅ Swagger UI with all endpoints
- ✅ Health check returning `{"status": "healthy"}`

### Step 3: Run Tests

**Option 1: Automated Test Script**
```bash
python test_api.py
```

**Option 2: Manual Testing with Swagger UI**
1. Go to http://localhost:8765/docs
2. Click on an endpoint
3. Click "Try it out"
4. Fill in parameters
5. Click "Execute"
6. See the response

**Option 3: Manual Testing with curl**
See examples below.

---

## 🧪 Test Cases

### Test 1: Health Check

```bash
curl http://localhost:8765/health
```

**Expected Response**:
```json
{
  "status": "healthy",
  "service": "Claude Config API",
  "version": "1.0.0"
}
```

---

### Test 2: Create Snapshot

```bash
curl -X POST "http://localhost:8765/api/v1/snapshots" \
  -H "Content-Type: application/json" \
  -d '{
    "trigger_type": "api",
    "triggered_by": "test-user",
    "notes": "Test snapshot from API",
    "tags": ["test", "api"]
  }'
```

**Expected Response**:
```json
{
  "snapshot_id": 1,
  "snapshot_hash": "a1b2c3d4...",
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

**What Happens**:
- ✅ Scans all Claude configuration paths (17+ locations)
- ✅ Stores file metadata and content
- ✅ Detects changes from previous snapshot
- ✅ Creates snapshot record in database
- ✅ Adds tags if provided

---

### Test 3: List Snapshots

```bash
curl "http://localhost:8765/api/v1/snapshots?page=1&page_size=10"
```

**Expected Response**:
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
      "tags": ["test", "api"]
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10,
  "total_pages": 1,
  "has_next": false,
  "has_previous": false,
  "total_size_all_bytes": 524288,
  "date_range_start": "2025-11-09T12:00:00",
  "date_range_end": "2025-11-09T12:00:00"
}
```

---

### Test 4: Get Snapshot Details

```bash
curl "http://localhost:8765/api/v1/snapshots/1"
```

**Expected Response**:
```json
{
  "id": 1,
  "snapshot_hash": "a1b2c3d4...",
  "snapshot_time": "2025-11-09T12:00:00",
  "trigger_type": "api",
  "triggered_by": "test-user",
  "notes": "Test snapshot from API",
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
    },
    {
      "id": 2,
      "tag_name": "api",
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
    },
    {
      "placeholder": "%APPDATA%",
      "resolved_path": "C:\\Users\\user\\AppData\\Roaming"
    },
    {
      "placeholder": "%ProgramData%",
      "resolved_path": "C:\\ProgramData"
    }
  ]
}
```

---

### Test 5: Get Snapshot Statistics

```bash
curl "http://localhost:8765/api/v1/snapshots/1/stats"
```

**Expected Response**:
```json
{
  "snapshot_id": 1,
  "snapshot_hash": "a1b2c3d4...",
  "snapshot_time": "2025-11-09T12:00:00",
  "total_locations": 17,
  "files_found": 15,
  "directories_found": 3,
  "total_size_bytes": 524288,
  "paths_count": 17,
  "changes_count": 0,
  "tags_count": 2,
  "annotations_count": 0
}
```

---

### Test 6: Add Tag

```bash
curl -X POST "http://localhost:8765/api/v1/snapshots/1/tags" \
  -H "Content-Type: application/json" \
  -d '{
    "tag_name": "production",
    "tag_type": "environment",
    "description": "Production environment snapshot",
    "created_by": "admin"
  }'
```

**Expected Response**:
```json
{
  "id": 3,
  "tag_name": "production",
  "tag_type": "environment",
  "description": "Production environment snapshot",
  "created_at": "2025-11-09T12:00:00",
  "created_by": "admin"
}
```

---

### Test 7: List Annotations

```bash
curl "http://localhost:8765/api/v1/snapshots/1/annotations"
```

**Expected Response**:
```json
[]
```

---

### Test 8: Add Annotation

```bash
curl -X POST "http://localhost:8765/api/v1/snapshots/1/annotations" \
  -H "Content-Type: application/json" \
  -d '{
    "annotation_text": "This is a test annotation",
    "annotation_type": "note",
    "created_by": "test-user"
  }'
```

**Expected Response**:
```json
{
  "id": 1,
  "annotation_text": "This is a test annotation",
  "annotation_type": "note",
  "created_at": "2025-11-09T12:00:00",
  "created_by": "test-user"
}
```

---

### Test 9: Export Snapshot

```bash
curl "http://localhost:8765/api/v1/snapshots/1/export?format=json"
```

**Expected Response**:
```json
{
  "version": "1.0",
  "exported_at": "2025-11-09T12:00:00",
  "snapshot": {
    "id": 1,
    "snapshot_hash": "a1b2c3d4...",
    ...
  },
  "paths": [
    {
      "id": 1,
      "category": "Settings Files",
      "name": "User Settings",
      "path_template": "%USERPROFILE%\\.claude\\settings.json",
      "resolved_path": "C:\\Users\\user\\.claude\\settings.json",
      "exists": true,
      "type": "file",
      "size_bytes": 1024,
      ...
    },
    ...
  ],
  "tags": [
    {
      "id": 1,
      "tag_name": "test",
      ...
    },
    ...
  ],
  "annotations": [
    {
      "id": 1,
      "annotation_text": "This is a test annotation",
      ...
    }
  ]
}
```

---

### Test 10: Delete Snapshot

```bash
curl -X DELETE "http://localhost:8765/api/v1/snapshots/1"
```

**Expected Response**:
```json
{
  "message": "Snapshot 1 deleted successfully",
  "success": true
}
```

---

## 🐛 Troubleshooting

### Issue: Server Won't Start

**Error**: `ModuleNotFoundError: No module named 'src'`

**Solution**:
```bash
# Make sure you're in the project root directory
cd C:\Users\steve\OneDrive\Code\myClaude\tooling\claude-config-editor

# Install dependencies
pip install -r requirements.txt

# Try again
uvicorn src.api.app:app --reload
```

### Issue: Database Connection Error

**Error**: `Database error occurred`

**Solution**:
1. Check if database file exists: `data/claude_config.db`
2. Check database permissions
3. Check configuration: `config/development.yaml`

### Issue: Port Already in Use

**Error**: `Address already in use`

**Solution**:
```bash
# Use a different port
uvicorn src.api.app:app --reload --port 8766

# Or find and kill the process using port 8765
# On Windows:
netstat -ano | findstr :8765
taskkill /PID <PID> /F
```

### Issue: Snapshot Creation Fails

**Error**: `Validation failed`

**Solution**:
1. Check request body format
2. Check required fields: `trigger_type`, `triggered_by`
3. Check field types match schema

### Issue: Snapshot Not Found

**Error**: `Snapshot 1 not found`

**Solution**:
1. Check if snapshot exists in database
2. Check snapshot ID is correct
3. Verify database has snapshots

---

## 📊 Expected Results

### First Snapshot Creation

When you create the first snapshot:
- ✅ **Files Found**: 0-17 (depends on what Claude config files exist)
- ✅ **Directories Found**: 0-3 (depends on directory structure)
- ✅ **Total Size**: Varies based on file sizes
- ✅ **Changes Detected**: `false` (no previous snapshot)
- ✅ **Changed From Previous**: `null` (no previous snapshot)

### Subsequent Snapshots

When you create additional snapshots:
- ✅ **Changes Detected**: `true` if files changed
- ✅ **Changed From Previous**: Number of changes detected
- ✅ **Files Found**: May differ from previous snapshot

---

## 🎯 Testing Checklist

### Basic Functionality
- [ ] Health check returns 200
- [ ] Create snapshot succeeds
- [ ] List snapshots returns data
- [ ] Get snapshot details returns data
- [ ] Get snapshot statistics returns data

### Tag Management
- [ ] Add tag succeeds
- [ ] List tags shows added tag
- [ ] Remove tag succeeds

### Annotation Management
- [ ] Add annotation succeeds
- [ ] List annotations shows added annotation
- [ ] Remove annotation succeeds

### Export/Import
- [ ] Export snapshot returns data
- [ ] Export format is valid JSON
- [ ] Export includes all snapshot data

### Error Handling
- [ ] Invalid snapshot ID returns 404
- [ ] Invalid request body returns 422
- [ ] Duplicate tag returns error
- [ ] Missing required fields returns 422

---

## 🔍 Advanced Testing

### Test Filtering

```bash
# Filter by trigger type
curl "http://localhost:8765/api/v1/snapshots?trigger_type=api"

# Filter by tags
curl "http://localhost:8765/api/v1/snapshots?tags=test"

# Filter by changes
curl "http://localhost:8765/api/v1/snapshots?has_changes=true"

# Search in notes
curl "http://localhost:8765/api/v1/snapshots?search=test"
```

### Test Pagination

```bash
# First page
curl "http://localhost:8765/api/v1/snapshots?page=1&page_size=10"

# Second page
curl "http://localhost:8765/api/v1/snapshots?page=2&page_size=10"
```

### Test Sorting

```bash
# Sort by time (descending)
curl "http://localhost:8765/api/v1/snapshots?sort_by=snapshot_time&sort_order=desc"

# Sort by size (ascending)
curl "http://localhost:8765/api/v1/snapshots?sort_by=total_size_bytes&sort_order=asc"
```

---

## 📝 Notes

### Database State

- Snapshots are stored in SQLite database: `data/claude_config.db`
- Each snapshot creation scans files and stores results
- Previous snapshots are not automatically deleted
- Use DELETE endpoint to remove snapshots

### Performance

- **Snapshot Creation**: ~1-2 seconds (scans 17+ paths)
- **List Snapshots**: <100ms (with pagination)
- **Get Snapshot**: <50ms (with relationships)
- **Export Snapshot**: <200ms (depends on data size)

### Limitations

- Export only returns JSON (YAML not yet implemented)
- File download not yet implemented
- Path endpoints not yet implemented
- Change comparison not yet implemented

---

## 🎉 Success Criteria

### ✅ API is Working If:

1. Health check returns 200
2. Can create snapshots
3. Can list snapshots
4. Can get snapshot details
5. Can add/remove tags
6. Can add/remove annotations
7. Can export snapshots
8. Error handling works correctly

### ✅ Scanner is Working If:

1. Snapshot creation actually scans files
2. Files found count > 0 (if files exist)
3. Paths are stored in database
4. Content hashes are calculated
5. Changes are detected between snapshots

---

## 📚 Additional Resources

- **API Documentation**: http://localhost:8765/docs
- **ReDoc**: http://localhost:8765/redoc
- **Quick Reference**: `doc/phase-5-quick-reference.md`
- **Full Review**: `doc/phase-5-review.md`

---

**Last Updated**: 2025-11-09
