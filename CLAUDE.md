# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Claude Config Editor is a dual-purpose tool:
1. **v2.0**: Production-grade version control system for Claude configurations with git-like snapshot management (Phase 1 complete)
2. **v1.0**: Simple web-based GUI for cleaning bloated Claude config files (legacy, still functional)

The v2.0 system provides snapshot-based version control with deduplication, change tracking, and comprehensive configuration management across 17 locations spanning Claude Code and Claude Desktop configurations.

## Common Commands

### Development Setup

```bash
# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux/Mac

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Install dev dependencies
pip install -r requirements-dev.txt
```

### Running the v2.0 CLI (Snapshot System)

```bash
# Create a snapshot
python -m src.cli.commands snapshot create
python -m src.cli.commands snapshot create --notes "Before cleanup"

# List snapshots
python -m src.cli.commands snapshot list
python -m src.cli.commands snapshot list --limit 5

# Show snapshot details
python -m src.cli.commands snapshot show 1
python -m src.cli.commands snapshot show 1 --paths    # Show all scanned paths
python -m src.cli.commands snapshot show 1 --changes  # Show changes from previous

# Database statistics
python -m src.cli.commands stats

# Compare snapshots (change detection)
python -m src.cli.commands snapshot compare 2  # Compare snapshot 2 with previous
python -m src.cli.commands snapshot compare 2 --previous 1  # Explicit comparison

# Generate snapshot report
python -m src.cli.commands snapshot report 2

# Deduplication statistics
python -m src.cli.commands dedup

# Note: CLI commands may have Windows console encoding issues
# Use test_reports.py script for reliable JSON/HTML output
python test_reports.py
```

### Running the v1.0 Web GUI (Legacy)

```bash
# Start the web server (auto-opens browser at localhost:8765)
python server.py

# Run comprehensive Windows path scanner
python windows_scan.py
```

### Testing

```bash
# Run tests with coverage
pytest

# Run specific test
pytest tests/test_scanner.py

# Run with verbose output
pytest -v
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type checking
mypy src/
```

### Database Inspection

```bash
# Inspect database contents
python inspect_db.py
```

## Architecture

### v2.0 Snapshot System (src/)

**Core Components:**

- **src/core/models.py**: SQLAlchemy 2.0 ORM models defining the database schema
  - `Snapshot`: Version metadata (like a git commit)
  - `FileContent`: Deduplicated file contents (SHA256-based)
  - `SnapshotPath`: File/directory state at snapshot time
  - `SnapshotChange`: Change tracking between snapshots
  - `ClaudeConfig`, `McpServer`: Parsed Claude-specific data
  - `SnapshotTag`, `Annotation`: Metadata and notes

- **src/core/database.py**: Async SQLite database management with WAL mode
  - `DatabaseManager`: Connection pooling and session management
  - Uses `aiosqlite` for async operations
  - Context managers for proper resource cleanup

- **src/core/scanner.py**: Path scanning and snapshot creation
  - `PathScanner`: Scans 17 configuration locations
  - Content hashing and deduplication
  - Change detection between snapshots
  - Metadata extraction (timestamps, sizes, permissions)

- **src/core/config.py**: Pydantic-based configuration with `.env` support
  - Database URL, logging settings, retention policies
  - Uses `pydantic-settings` for environment variable loading

- **src/cli/commands.py**: Typer-based CLI with Rich formatting
  - Commands: `snapshot create|list|show`, `stats`
  - Uses Rich for tables, panels, and colored output

- **src/utils/logger.py**: Centralized logging with file rotation

**Key Patterns:**

1. **Async/Await Throughout**: All database operations use `async`/`await`
2. **Content Deduplication**: Files with identical content share storage (~97% savings)
3. **Type Safety**: Comprehensive type hints, Pydantic models for validation
4. **Change Detection**: Automatic comparison between consecutive snapshots
5. **17 Tracked Locations**: Settings, memory files, subagents, MCP servers, slash commands, logs

### v1.0 Web GUI (Root Files)

- **server.py**: HTTP server (port 8765) with REST API for config management
  - Endpoints: `/api/config`, `/api/save`, `/api/export`
  - Auto-backup before saves (`.claude.backup.json`)

- **index.html**: Single-file web UI for cleaning project history and managing MCP servers

- **windows_scan.py**: Comprehensive Windows path scanner for Claude installations

### Database Schema Highlights

The SQLite database (`./data/claude_config.db`) uses:
- WAL mode for concurrent access
- Foreign keys with cascade deletes
- Indexes on: snapshot_time, content_hash, path queries
- Deduplication via `file_contents.content_hash` (SHA256)
- Reference counting for cleanup (`file_contents.reference_count`)

### Configuration Locations Tracked (17 total)

1. **Settings Files** (5): User/Project/Enterprise settings, original `.claude.json`
2. **Memory Files** (3): User/Project/Enterprise `CLAUDE.md`
3. **Subagents** (2): User/Project subagents
4. **Claude Desktop** (1): Desktop config
5. **Slash Commands** (2): User/Project commands
6. **MCP Servers** (3): Desktop/User/Project MCP configs
7. **Logs** (1): Claude Desktop logs

## Project Status

**Phase 1 (Complete)**: Core snapshot system with deduplication and change tracking

**Planned Phases**:
- Phase 2: Comparison views and diff generation
- Phase 3: Search and query capabilities
- Phase 4: Tags and annotations
- Phase 5: Restoration and rollback
- Phase 6: Claude-specific intelligence (MCP tracking, bloat detection)
- Phase 7: GUI integration

## Important Notes

- **Database Location**: `./data/claude_config.db` (configurable via `.env`)
- **Logs**: `./logs/app.log` (with rotation)
- **Python Version**: Requires Python 3.9+
- **Zero Network Dependencies**: All operations are local-only
- **Cross-Platform**: Works on Windows, macOS, Linux

## Development Workflow

When adding new features to the snapshot system:

1. Define models in `src/core/models.py` (SQLAlchemy ORM)
2. Update scanner logic in `src/core/scanner.py` if scanning changes
3. Add CLI commands in `src/cli/commands.py` (use Typer + Rich)
4. All database operations must be async
5. Use `get_db_manager()` context manager for sessions
6. Add type hints to all new functions
7. Update this CLAUDE.md if architecture changes significantly

## Testing Strategy

Tests go in `tests/` directory:
- `test_scanner.py`: Path scanning and snapshot creation
- `test_database.py`: Database operations and queries
- `test_models.py`: Model validation and relationships
- Use `pytest-asyncio` for async tests
- Use `pytest-mock` for mocking database operations

## Common Patterns

### Creating a Snapshot (Async)

```python
async with db.get_session() as session:
    scanner = PathScanner(session)
    snapshot = await scanner.create_snapshot(
        trigger_type="manual",
        notes="Optional description"
    )
```

### Querying Snapshots

```python
from sqlalchemy import select
stmt = select(Snapshot).order_by(Snapshot.snapshot_time.desc())
result = await session.execute(stmt)
snapshots = result.scalars().all()
```

### Working with Content Deduplication

Content hashing happens automatically in `PathScanner`. Files with identical SHA256 hashes share the same `FileContent` record, referenced by multiple `SnapshotPath` entries.
