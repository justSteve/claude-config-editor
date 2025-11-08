# Version-Controlled Claude Config Management

## Goal
Git-like version control for Claude Code and Claude Desktop configurations, capturing full snapshots with metadata on each scan.

## Core Concept
Every scan creates a complete snapshot (version) that includes:
- All file contents found
- Complete metadata (size, timestamps, permissions)
- Environment context (OS, user, paths)
- Relationships between files
- Diffs from previous version

## Database Schema (Enhanced for Version Control)

```sql
-- Snapshots: Each scan creates a new snapshot (version)
CREATE TABLE snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    snapshot_hash TEXT UNIQUE NOT NULL,  -- SHA256 of entire snapshot state
    trigger_type TEXT NOT NULL,  -- 'manual', 'scheduled', 'api', 'cli'
    triggered_by TEXT,  -- username or system
    notes TEXT,  -- optional user notes

    -- System context
    os_type TEXT NOT NULL,
    os_version TEXT,
    hostname TEXT,
    username TEXT,
    working_directory TEXT,

    -- Scan statistics
    total_locations INTEGER NOT NULL,
    files_found INTEGER NOT NULL,
    directories_found INTEGER NOT NULL,
    total_size_bytes INTEGER NOT NULL,

    -- Change detection
    changed_from_previous INTEGER,  -- number of changes
    is_baseline BOOLEAN DEFAULT FALSE,  -- first snapshot or marked baseline

    -- Relationships
    parent_snapshot_id INTEGER,  -- previous snapshot for diffing
    FOREIGN KEY (parent_snapshot_id) REFERENCES snapshots(id)
);

-- Environment variables captured during snapshot
CREATE TABLE snapshot_env_vars (
    snapshot_id INTEGER NOT NULL,
    placeholder TEXT NOT NULL,
    resolved_path TEXT NOT NULL,
    PRIMARY KEY (snapshot_id, placeholder),
    FOREIGN KEY (snapshot_id) REFERENCES snapshots(id) ON DELETE CASCADE
);

-- Discovered paths and their state at snapshot time
CREATE TABLE snapshot_paths (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id INTEGER NOT NULL,

    -- Path identification
    category TEXT NOT NULL,  -- 'Settings Files', 'MCP Servers', etc.
    name TEXT NOT NULL,
    path_template TEXT NOT NULL,
    resolved_path TEXT NOT NULL,

    -- File/directory state
    exists BOOLEAN NOT NULL,
    type TEXT,  -- 'file', 'directory', 'symlink', NULL if not exists

    -- File metadata (NULL if directory or not exists)
    size_bytes INTEGER,
    modified_time TIMESTAMP,
    created_time TIMESTAMP,
    accessed_time TIMESTAMP,
    permissions TEXT,  -- e.g., '0644' or 'rw-r--r--'

    -- Directory metadata (NULL if file or not exists)
    item_count INTEGER,  -- number of items in directory

    -- Content tracking
    content_hash TEXT,  -- SHA256 of file content (NULL if directory)
    content_id INTEGER,  -- FK to file_contents

    -- Error handling
    error_message TEXT,  -- if scan failed for this path

    FOREIGN KEY (snapshot_id) REFERENCES snapshots(id) ON DELETE CASCADE,
    FOREIGN KEY (content_id) REFERENCES file_contents(id)
);

-- Actual file contents (deduplicated by hash)
CREATE TABLE file_contents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_hash TEXT UNIQUE NOT NULL,  -- SHA256 for deduplication
    content_text TEXT,  -- UTF-8 text content
    content_binary BLOB,  -- Binary content if not UTF-8
    content_type TEXT,  -- 'json', 'text', 'binary', 'markdown'
    size_bytes INTEGER NOT NULL,
    compression TEXT,  -- 'none', 'gzip', 'zlib'
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Reference counting for cleanup
    reference_count INTEGER DEFAULT 1
);

-- Parsed JSON content for queryability (for .json files)
CREATE TABLE json_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_id INTEGER NOT NULL,
    snapshot_path_id INTEGER NOT NULL,

    -- JSON structure flattened for querying
    json_path TEXT NOT NULL,  -- e.g., '$.projects[0].name'
    json_value TEXT,
    json_type TEXT,  -- 'string', 'number', 'boolean', 'array', 'object', 'null'

    FOREIGN KEY (content_id) REFERENCES file_contents(id) ON DELETE CASCADE,
    FOREIGN KEY (snapshot_path_id) REFERENCES snapshot_paths(id) ON DELETE CASCADE
);

-- Track specific Claude config structures
CREATE TABLE claude_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_path_id INTEGER NOT NULL,
    config_type TEXT NOT NULL,  -- 'code', 'desktop'

    -- Extracted metadata
    num_projects INTEGER,
    num_mcp_servers INTEGER,
    num_startups INTEGER,

    -- Size analysis
    total_size_bytes INTEGER,
    largest_project_path TEXT,
    largest_project_size INTEGER,

    FOREIGN KEY (snapshot_path_id) REFERENCES snapshot_paths(id) ON DELETE CASCADE
);

-- MCP server configurations extracted
CREATE TABLE mcp_servers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_path_id INTEGER NOT NULL,

    server_name TEXT NOT NULL,
    command TEXT,
    args TEXT,  -- JSON array
    env TEXT,  -- JSON object
    working_directory TEXT,

    FOREIGN KEY (snapshot_path_id) REFERENCES snapshot_paths(id) ON DELETE CASCADE
);

-- Change tracking between snapshots
CREATE TABLE snapshot_changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id INTEGER NOT NULL,  -- current snapshot
    previous_snapshot_id INTEGER NOT NULL,  -- what we're comparing to

    path_template TEXT NOT NULL,
    change_type TEXT NOT NULL,  -- 'added', 'deleted', 'modified', 'unchanged'

    -- For modified files
    old_content_hash TEXT,
    new_content_hash TEXT,
    old_size_bytes INTEGER,
    new_size_bytes INTEGER,
    old_modified_time TIMESTAMP,
    new_modified_time TIMESTAMP,

    -- Change details
    diff_summary TEXT,  -- brief description of changes

    FOREIGN KEY (snapshot_id) REFERENCES snapshots(id) ON DELETE CASCADE,
    FOREIGN KEY (previous_snapshot_id) REFERENCES snapshots(id)
);

-- Tags/labels for snapshots (like git tags)
CREATE TABLE snapshot_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id INTEGER NOT NULL,
    tag_name TEXT NOT NULL,
    tag_type TEXT,  -- 'manual', 'auto', 'release', 'backup'
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    description TEXT,

    UNIQUE(tag_name),
    FOREIGN KEY (snapshot_id) REFERENCES snapshots(id) ON DELETE CASCADE
);

-- Annotations/notes on specific files or snapshots
CREATE TABLE annotations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id INTEGER NOT NULL,
    snapshot_path_id INTEGER,  -- NULL for snapshot-level annotations

    annotation_text TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    annotation_type TEXT,  -- 'note', 'warning', 'issue', 'fix'

    FOREIGN KEY (snapshot_id) REFERENCES snapshots(id) ON DELETE CASCADE,
    FOREIGN KEY (snapshot_path_id) REFERENCES snapshot_paths(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX idx_snapshots_time ON snapshots(snapshot_time DESC);
CREATE INDEX idx_snapshots_hash ON snapshots(snapshot_hash);
CREATE INDEX idx_snapshot_paths_snapshot ON snapshot_paths(snapshot_id);
CREATE INDEX idx_snapshot_paths_template ON snapshot_paths(path_template);
CREATE INDEX idx_snapshot_paths_exists ON snapshot_paths(exists);
CREATE INDEX idx_snapshot_paths_hash ON snapshot_paths(content_hash);
CREATE INDEX idx_file_contents_hash ON file_contents(content_hash);
CREATE INDEX idx_file_contents_refs ON file_contents(reference_count);
CREATE INDEX idx_changes_snapshot ON snapshot_changes(snapshot_id);
CREATE INDEX idx_changes_type ON snapshot_changes(change_type);
CREATE INDEX idx_tags_snapshot ON snapshot_tags(snapshot_id);
CREATE INDEX idx_tags_name ON snapshot_tags(tag_name);
CREATE INDEX idx_json_path ON json_data(json_path);
CREATE INDEX idx_mcp_snapshot ON mcp_servers(snapshot_path_id);

-- Full-text search on file contents (optional, for searching through configs)
CREATE VIRTUAL TABLE file_contents_fts USING fts5(
    content_text,
    content_id UNINDEXED
);
```

## Key Features

### 1. Complete Snapshots
Every scan captures:
- ✅ All file contents (deduplicated by hash)
- ✅ Complete metadata (timestamps, sizes, permissions)
- ✅ Environment context (OS, user, paths)
- ✅ System state at scan time
- ✅ Relationships between files

### 2. Smart Deduplication
- Files with same content stored once
- Reference counting for cleanup
- Hash-based deduplication (SHA256)
- Compression support for large files

### 3. Change Tracking
- Automatic diff between versions
- Track: added, deleted, modified, unchanged
- Store change summaries
- Link to parent snapshot

### 4. Queryable History
- Search by date range
- Find when specific changes occurred
- Compare any two snapshots
- Track specific config values over time

### 5. Tags & Annotations
- Tag important snapshots (like git tags)
- Add notes to snapshots or files
- Mark baselines/releases
- Track issues/fixes

### 6. Claude-Specific Intelligence
- Parse and track project count
- Track MCP server changes
- Monitor config size growth
- Identify bloat automatically

## API Endpoints (New)

### Version Control Operations

```
GET  /api/v1/snapshots                    # List all snapshots
GET  /api/v1/snapshots/{id}                # Get snapshot details
POST /api/v1/snapshots                     # Create new snapshot (trigger scan)
DELETE /api/v1/snapshots/{id}              # Delete snapshot

GET  /api/v1/snapshots/{id}/paths          # List all paths in snapshot
GET  /api/v1/snapshots/{id}/contents/{path_id}  # Get file content
GET  /api/v1/snapshots/{id}/export         # Export snapshot as archive

GET  /api/v1/compare/{id1}/{id2}           # Compare two snapshots
GET  /api/v1/diff/{id1}/{id2}/{path}       # Diff specific file between versions

GET  /api/v1/timeline                      # Get change timeline
GET  /api/v1/timeline/{path}               # Get timeline for specific file

POST /api/v1/snapshots/{id}/tag            # Tag a snapshot
GET  /api/v1/tags                          # List all tags
POST /api/v1/snapshots/{id}/annotate       # Add annotation

GET  /api/v1/search?q=...                  # Search across all snapshots
GET  /api/v1/search/content?q=...          # Full-text search in file contents

POST /api/v1/restore/{id}                  # Restore files from snapshot
POST /api/v1/rollback/{id}                 # Rollback to previous snapshot
```

### Analysis Endpoints

```
GET  /api/v1/stats                         # Overall statistics
GET  /api/v1/stats/growth                  # Size growth over time
GET  /api/v1/stats/changes                 # Change frequency analysis

GET  /api/v1/claude/projects/history       # Project count over time
GET  /api/v1/claude/mcp/history            # MCP server changes
GET  /api/v1/claude/bloat                  # Identify bloat candidates
```

## CLI Commands (New)

```bash
# Snapshot management
claude-config snapshot                     # Create new snapshot
claude-config snapshot list                # List all snapshots
claude-config snapshot show <id>           # Show snapshot details
claude-config snapshot delete <id>         # Delete snapshot
claude-config snapshot tag <id> <name>     # Tag snapshot

# Comparison & Diffing
claude-config compare <id1> <id2>          # Compare snapshots
claude-config diff <id1> <id2> <path>      # Diff specific file
claude-config timeline                     # Show change timeline
claude-config timeline <path>              # Show timeline for file

# Search & Query
claude-config search <query>               # Search across snapshots
claude-config search --content <query>     # Search file contents
claude-config find-when <path> <change>    # Find when change occurred

# Restoration
claude-config restore <id>                 # Restore from snapshot
claude-config restore <id> <path>          # Restore specific file
claude-config export <id>                  # Export snapshot to archive

# Analysis
claude-config stats                        # Show statistics
claude-config stats --growth               # Show growth analysis
claude-config bloat                        # Find bloat candidates

# Annotations
claude-config annotate <id> <note>         # Add note to snapshot
claude-config annotate <id> <path> <note>  # Add note to file
```

## Workflow Examples

### Daily Development Workflow

```bash
# Morning: Capture baseline
claude-config snapshot --tag "start-of-day"

# Make some changes to MCP configs...
# Then capture changes
claude-config snapshot --note "Added new MCP server for testing"

# Compare what changed
claude-config compare latest previous

# End of day: capture final state
claude-config snapshot --tag "end-of-day"
```

### Before Major Changes

```bash
# Create backup snapshot
claude-config snapshot --tag "pre-cleanup" --note "Before deleting old projects"

# Do cleanup in GUI...

# Create post-cleanup snapshot
claude-config snapshot --tag "post-cleanup"

# Compare to see what was removed
claude-config compare post-cleanup pre-cleanup

# If something went wrong, restore
claude-config restore pre-cleanup
```

### Tracking Down When Something Changed

```bash
# Find when a specific MCP server was added
claude-config search --content "brave-search"

# See full timeline of MCP config
claude-config timeline "%APPDATA%\Claude\claude_desktop_config.json"

# Compare specific versions
claude-config diff v123 v145 mcp-config
```

## Implementation Priority

### Phase 1: Core Snapshot System (Week 1)
- [ ] Database schema creation
- [ ] Snapshot creation with full metadata
- [ ] Content deduplication (hash-based)
- [ ] Basic CLI (snapshot, list, show)
- [ ] File content storage

### Phase 2: Change Tracking (Week 1-2)
- [ ] Auto-detect changes between snapshots
- [ ] Change type classification (add/delete/modify)
- [ ] Diff generation
- [ ] Timeline queries
- [ ] Comparison views

### Phase 3: Search & Query (Week 2)
- [ ] Full-text search
- [ ] Path-based queries
- [ ] Date range filters
- [ ] Content search
- [ ] Advanced filtering

### Phase 4: Tags & Annotations (Week 2)
- [ ] Tag system
- [ ] Annotation system
- [ ] Baseline marking
- [ ] Custom metadata

### Phase 5: Restoration (Week 3)
- [ ] Restore full snapshot
- [ ] Restore specific files
- [ ] Rollback capability
- [ ] Export/import

### Phase 6: Claude-Specific (Week 3)
- [ ] Project tracking
- [ ] MCP server tracking
- [ ] Bloat detection
- [ ] Size analysis
- [ ] JSON parsing & indexing

### Phase 7: GUI Integration (Week 3-4)
- [ ] Snapshot browser
- [ ] Visual diff viewer
- [ ] Timeline visualization
- [ ] Comparison interface
- [ ] Restore interface

## Technology Choices

### Recommended Stack
- **Database**: SQLite with FTS5 (full-text search)
- **ORM**: SQLAlchemy 2.0 (with async support)
- **CLI**: Click or Typer (rich terminal output)
- **API**: FastAPI (async, auto-docs, modern)
- **Hashing**: hashlib (SHA256 for content)
- **Compression**: zlib or gzip for large files
- **Diff**: difflib (Python stdlib) or python-diff-match-patch
- **JSON Parsing**: jq-like queries with jmespath or jsonpath-ng

## Storage Efficiency

### Deduplication Strategy
```python
# Example: 100 snapshots of similar configs
# Without deduplication: 100 × 40MB = 4GB
# With deduplication: ~100MB (most content unchanged)
# Savings: ~97%
```

### Compression
- JSON configs compress well (~70-80% reduction)
- Only compress files > 1MB
- Store compression type in metadata

### Cleanup Strategy
- Automatic cleanup of unreferenced contents
- Configurable retention policy
- Keep tagged snapshots longer
- Compact database periodically

## Next Steps

1. **Confirm design** - Is this the version control you envisioned?
2. **Choose tech stack** - FastAPI vs Flask? SQLAlchemy vs raw SQL?
3. **Start Phase 1** - Implement core snapshot system
4. **Iterate** - Add features based on usage

## Questions for You

1. **Retention policy**: How long to keep snapshots? (30 days? 90 days? Forever?)
2. **Auto-snapshots**: Should we auto-snapshot on detected changes? Or manual only?
3. **Size limits**: Max snapshot size? Max total storage?
4. **Compression**: Always compress? Or only large files?
5. **Binary files**: Should we track binary files (logs, etc.) or text only?

This design gives you git-like version control specifically tailored for Claude configs. Ready to start implementing?
