# Scanner Implementation Comparison

## Overview

This document compares the two scanner implementations in the codebase:
1. `windows_scan.py` - Legacy standalone scanner
2. `src/core/scanner.py` - New production scanner with database integration

## Feature Comparison

| Feature | windows_scan.py | src/core/scanner.py | Status |
|---------|----------------|---------------------|---------|
| Path Scanning | ✅ Yes | ✅ Yes | Same paths |
| Database Integration | ❌ No | ✅ Yes | |
| Async/Await | ❌ Sync | ✅ Async | |
| File Content Storage | ❌ No | ✅ Yes | |
| Content Deduplication | ❌ No | ✅ Yes | |
| Change Detection | ❌ No | ✅ Yes | |
| MCP Log Enumeration | ✅ Yes | ❌ **MISSING** | **Needs Integration** |
| Directory Item Counting | ✅ Yes | ✅ Yes | Both implement |
| Environment Variable Tracking | ✅ Yes (display) | ✅ Yes (stored in DB) | |
| JSON Export | ✅ Yes | ❌ No | |
| CLI Interface | ✅ Yes | ❌ No (via commands.py) | |
| Formatted Output | ✅ Yes | ❌ No (via commands.py) | |
| Platform Detection | ✅ Yes | ❌ No | |
| Error Handling | ✅ Basic | ✅ Enhanced | |
| Logging | ❌ Print statements | ✅ Python logging | |

## Architecture Comparison

### windows_scan.py Architecture

```
main()
├── scan_windows_paths() → returns dict
│   ├── get_file_info(path) → file metadata
│   └── count_items_in_dir(path) → item count
├── print_results(results) → console output
└── export_results_json(results) → JSON file
```

**Characteristics**:
- Simple, procedural design
- Standalone script
- No external dependencies (beyond stdlib)
- Immediate results (not persisted)
- Synchronous execution

### src/core/scanner.py Architecture

```
PathScanner(session: AsyncSession)
├── get_path_definitions() → list[dict]
├── create_snapshot() → Snapshot
│   ├── _scan_path(path_def) → SnapshotPath
│   ├── _get_or_create_content() → FileContent (deduplication)
│   └── _detect_changes() → SnapshotChange[]
```

**Characteristics**:
- Object-oriented, async design
- Database-integrated
- Requires SQLAlchemy, async stack
- Persistent results (database)
- Asynchronous execution
- Change tracking between snapshots

## Detailed Feature Analysis

### 1. MCP Log Enumeration

**windows_scan.py** (lines 187-204):
```python
logs_dir = appdata / 'Claude' / 'Logs'
logs_info = get_file_info(logs_dir)

if logs_info['exists'] and logs_info['type'] == 'directory':
    try:
        # Find all mcp*.log files
        mcp_logs = list(logs_dir.glob('mcp*.log'))
        logs_info['mcp_log_count'] = len(mcp_logs)
        logs_info['mcp_logs'] = [str(log.name) for log in mcp_logs[:10]]
        if len(mcp_logs) > 10:
            logs_info['mcp_logs'].append(f"... and {len(mcp_logs) - 10} more")
    except Exception as e:
        logs_info['error'] = str(e)
```

**src/core/scanner.py**:
- ❌ Does NOT enumerate MCP logs
- Only detects if logs directory exists
- Missing: log file listing, count

**Action Required**: Integrate MCP log enumeration into production scanner

### 2. Directory Item Counting

**windows_scan.py** (lines 46-54):
```python
def count_items_in_dir(path):
    try:
        if not path.is_dir():
            return 0
        items = list(path.iterdir())
        return len(items)
    except Exception:
        return 0
```

**src/core/scanner.py** (lines 336-339):
```python
elif path.is_dir():
    snapshot_path.type = "directory"
    items = list(path.iterdir())
    snapshot_path.item_count = len(items)
```

**Status**: ✅ Both implement this feature, production scanner stores it in `item_count` field

### 3. File Information Collection

**windows_scan.py** (lines 29-44):
```python
def get_file_info(path):
    try:
        stat = path.stat()
        return {
            'exists': True,
            'size': stat.st_size,
            'size_formatted': format_size(stat.st_size),
            'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
            'type': 'directory' if path.is_dir() else 'file'
        }
    except Exception as e:
        return {'exists': False, 'error': str(e)}
```

**src/core/scanner.py** (lines 317-324):
```python
if path.is_file():
    snapshot_path.type = "file"
    stat = path.stat()
    snapshot_path.size_bytes = stat.st_size
    snapshot_path.modified_time = datetime.fromtimestamp(stat.st_mtime)
    snapshot_path.created_time = datetime.fromtimestamp(stat.st_ctime)
    snapshot_path.accessed_time = datetime.fromtimestamp(stat.st_atime)
```

**Status**: Production scanner captures MORE metadata (created, accessed times)

### 4. Path Definitions

**Both implementations have IDENTICAL path definitions**:
- Same 17 locations
- Same 7 categories
- Same environment variable usage
- Same path templates

**Problem**: Path definitions are hardcoded in both files (DRY violation)

**Action Required**: Extract to configuration file

## Missing Features in Production Scanner

### Critical Missing Features

1. **MCP Log Enumeration** (Priority: HIGH)
   - Need to add glob pattern matching for `mcp*.log`
   - Store log file list in database or annotation
   - Consider: Should log files be tracked individually or as metadata?

2. **JSON Export** (Priority: MEDIUM)
   - Legacy scanner has built-in JSON export
   - Production scanner could use report generators
   - Already partially implemented via CLI `--format json`

3. **Platform Detection Warning** (Priority: LOW)
   - Legacy scanner warns if not on Windows
   - Production scanner assumes Windows
   - Could add to configuration validation

### Extra Features in Production Scanner

1. **Content Deduplication**
   - Stores file contents with SHA256 hash
   - References same content from multiple snapshots
   - Saves disk space

2. **Change Detection**
   - Compares with previous snapshot
   - Tracks added/modified/deleted files
   - Historical tracking

3. **Database Persistence**
   - All scan results stored in SQLite
   - Queryable history
   - Support for reports and analysis

## Migration Strategy

### Phase 1: Extract Common Code (Task 3.1.2)
- [ ] Create `config/paths.yaml` with path definitions
- [ ] Update production scanner to load from config
- [ ] Keep legacy scanner working (read from config too)

### Phase 2: Integrate Missing Features (Task 3.1.3)
- [ ] Add MCP log enumeration to production scanner
- [ ] Add platform detection (optional)
- [ ] Test integrated features

### Phase 3: Refactor Architecture (Task 3.1.4)
- [ ] Create `PathResolver` class for env var expansion
- [ ] Separate concerns (scanning vs. snapshot creation)
- [ ] Improve testability

### Phase 4: Deprecate Legacy (Task 3.1.5)
- [ ] Add deprecation warning to `windows_scan.py`
- [ ] Update documentation
- [ ] Create migration guide for users

## Recommendations

### Immediate Actions (Task 3.1.2-3.1.3)

1. **Extract Path Definitions**
   ```yaml
   # config/paths.yaml
   paths:
     - category: "Settings Files"
       name: "User Settings"
       template: "%USERPROFILE%\\.claude\\settings.json"
       # ...
   ```

2. **Add MCP Log Enumeration**
   ```python
   # In _scan_path method, when handling Logs directory:
   if path_def["name"] == "Claude Desktop Logs" and path.is_dir():
       mcp_logs = list(path.glob("mcp*.log"))
       # Store in annotation or separate field
   ```

3. **Add Configuration Loader**
   ```python
   # src/core/path_loader.py
   def load_path_definitions(config_file: Path) -> list[dict]:
       # Load from YAML
       # Expand environment variables
       # Return path definitions
   ```

### Future Enhancements

1. **Path Filtering**
   - Allow users to specify which categories to scan
   - Support custom path additions via config

2. **Progress Tracking**
   - Add progress callbacks for long scans
   - Support cancellation

3. **Parallel Scanning**
   - Scan multiple paths concurrently
   - Use async/await effectively

4. **Validation**
   - Validate path definitions on load
   - Detect invalid or inaccessible paths early

## Conclusion

The production scanner (`src/core/scanner.py`) is more sophisticated and suitable for production use, but it's **missing MCP log enumeration** from the legacy scanner. 

The consolidation should:
1. ✅ Keep production scanner as primary implementation
2. ✅ Extract path definitions to configuration
3. ✅ Add missing MCP log enumeration feature
4. ✅ Deprecate legacy scanner
5. ✅ Improve architecture and testability

**Next Steps**: Proceed with Task 3.1.2 (Extract path definitions to config/paths.yaml)

