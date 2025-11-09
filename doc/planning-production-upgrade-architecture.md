# Production Upgrade Plan

## Project Structure

```text
claude-config-editor/
├── .venv/                          # Virtual environment (gitignored)
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py              # Configuration management
│   │   ├── database.py            # SQLite database manager
│   │   ├── scanner.py             # Path scanning logic
│   │   └── models.py              # Data models (dataclasses/pydantic)
│   ├── api/
│   │   ├── __init__.py
│   │   ├── server.py              # Web server
│   │   └── routes.py              # API routes
│   ├── cli/
│   │   ├── __init__.py
│   │   └── commands.py            # CLI commands
│   └── utils/
│       ├── __init__.py
│       ├── logger.py              # Logging setup
│       └── validators.py          # Path/data validators
├── tests/
│   ├── __init__.py
│   ├── test_scanner.py
│   ├── test_database.py
│   └── test_api.py
├── static/                         # Web UI files
│   ├── index.html
│   ├── css/
│   └── js/
├── data/
│   └── claude_config.db           # SQLite database
├── logs/                           # Application logs
├── config/
│   ├── development.yaml           # Dev config
│   ├── production.yaml            # Prod config
│   └── logging.yaml               # Logging config
├── docs/
│   ├── API.md
│   ├── DATABASE_SCHEMA.md
│   └── DEPLOYMENT.md
├── scripts/
│   ├── setup.sh                   # Setup script
│   └── migrate_db.py              # DB migrations
├── .env.example                    # Environment variables template
├── .gitignore
├── requirements.txt                # Production dependencies
├── requirements-dev.txt            # Development dependencies
├── setup.py                        # Package setup
├── pyproject.toml                  # Modern Python project config
├── pytest.ini                      # Test configuration
├── README.md
└── LICENSE
```

## Database Schema

```sql
-- Scans table: Store scan sessions
CREATE TABLE scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    os_type TEXT NOT NULL,
    os_version TEXT,
    username TEXT,
    total_scanned INTEGER,
    total_found INTEGER,
    detection_rate REAL
);

-- Environment variables table
CREATE TABLE env_vars (
    scan_id INTEGER NOT NULL,
    placeholder TEXT NOT NULL,
    resolved_path TEXT NOT NULL,
    FOREIGN KEY (scan_id) REFERENCES scans(id) ON DELETE CASCADE,
    PRIMARY KEY (scan_id, placeholder)
);

-- Paths table: Store individual path scan results
CREATE TABLE paths (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_id INTEGER NOT NULL,
    category TEXT NOT NULL,
    name TEXT NOT NULL,
    path_template TEXT NOT NULL,
    resolved_path TEXT NOT NULL,
    exists BOOLEAN NOT NULL,
    type TEXT,  -- 'file', 'directory', or NULL
    size_bytes INTEGER,
    modified_time TIMESTAMP,
    error_message TEXT,
    FOREIGN KEY (scan_id) REFERENCES scans(id) ON DELETE CASCADE
);

-- File contents table: Store actual file contents
CREATE TABLE file_contents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path_id INTEGER NOT NULL,
    content TEXT,  -- JSON or text content
    content_hash TEXT,  -- SHA256 hash for change detection
    captured_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (path_id) REFERENCES paths(id) ON DELETE CASCADE
);

-- Config history table: Track config changes
CREATE TABLE config_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_type TEXT NOT NULL,  -- 'code' or 'desktop'
    config_path TEXT NOT NULL,
    content TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    changed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    changed_by TEXT  -- 'scan', 'manual', 'api'
);

-- Indexes for performance
CREATE INDEX idx_scans_time ON scans(scan_time);
CREATE INDEX idx_paths_scan ON paths(scan_id);
CREATE INDEX idx_paths_exists ON paths(exists);
CREATE INDEX idx_contents_path ON file_contents(path_id);
CREATE INDEX idx_contents_captured ON file_contents(captured_at);
CREATE INDEX idx_history_type ON config_history(config_type);
CREATE INDEX idx_history_changed ON config_history(changed_at);
```

## Features to Add

### 1. Configuration Management

- YAML-based configuration
- Environment variable support
- Multiple environment profiles (dev/prod)
- Secrets management

### 2. Logging

- Structured logging (JSON format)
- Log rotation
- Different log levels per module
- Request logging for API
- Separate logs: access.log, error.log, app.log

### 3. Database Layer

- SQLAlchemy ORM or raw SQL with connection pooling
- Migration system (Alembic or custom)
- Automatic schema creation
- Backup and restore functionality
- Query optimization

### 4. CLI Enhancement

- Click or Typer for CLI framework
- Subcommands: scan, serve, db, export, import
- Progress bars for long operations
- Rich terminal output
- Configuration wizard

### 5. API Enhancement

- RESTful API design
- ~~Authentication/Authorization~~ (not needed - local-only tool)
- ~~Rate limiting~~ (not needed - single user)
- CORS configuration (if needed for local development)
- API versioning (/api/v1/)
- OpenAPI/Swagger documentation
- ~~WebSocket support for real-time updates~~ (not needed)

### 6. Testing

- Unit tests (pytest)
- Integration tests
- API tests
- Mock database for testing
- Coverage reports (>80% target)
- Test fixtures

### 7. Error Handling

- Custom exception classes
- Graceful degradation
- Retry logic with exponential backoff
- Detailed error messages
- Error reporting/monitoring

### 8. Performance

- Caching layer (in-memory only - no Redis needed for single user)
- Async I/O where applicable
- Batch operations
- Connection pooling (SQLite)
- Query optimization

### 9. Security

- Input validation
- SQL injection prevention
- XSS protection
- Path traversal prevention
- Secure defaults
- Security headers

### 10. Deployment

- ~~Docker support~~ (not needed - Windows single machine)
- ~~systemd service file~~ (not needed - Windows only)
- Windows service support (primary deployment target)
- Health check endpoints
- Graceful shutdown
- Environment-based configuration

## Implementation Phases

### Phase 1: Project Structure & Setup

- [x ] Create new directory structure
- [ x] Set up virtual environment
- [ x] Create requirements.txt
- [ x] Set up pyproject.toml
- [ x] Configure logging
- [ x] Create base configuration system

### Phase 2: Database Layer

- [x] Design database schema
- [x] Create database manager
- [x] Implement models
- [x] Add migration system (Alembic for SQLite-only)
- [x] Write database tests (temporary file SQLite, single-user scenarios)

### Phase 3: Core Refactoring

**📋 Detailed Plan**: See [Phase 3 Core Refactoring Plan](./phase-3-core-refactoring-plan.md)

- [ ] Extract scanner logic to core/scanner.py
- [ ] Add configuration management
- [ ] Implement logging throughout
- [ ] Add data models
- [ ] Add validators

**Status**: Detailed plan created. Implementation pending.

**Key Tasks**:
1. **Task 3.1**: Extract and consolidate scanner logic (2-3 days)
2. **Task 3.2**: Enhance configuration management with YAML support (2-3 days)
3. **Task 3.3**: Implement logging throughout application (2-3 days)
4. **Task 3.4**: Add Pydantic data models for API (2-3 days)
5. **Task 3.5**: Add validation utilities (2-3 days)

**Estimated Time**: 10-15 days (2-3 weeks)

### Phase 4: CLI Enhancement

- [ ] Implement Typer-based CLI (already partially implemented)
- [ ] Add scan command with options (enhance snapshot create with scan-specific options)
- [ ] Add database management commands
- [ ] Add export/import commands
- [ ] Add configuration commands
- [ ] Add serve command for web API
- [ ] Add progress bars for long operations
- [ ] Add configuration wizard
- [ ] Improve error handling and user feedback
- [ ] Add comprehensive CLI tests

#### Phase 4 Detailed Implementation Plan

**Current State:**
- Typer-based CLI already implemented in `src/cli/commands.py`
- Existing commands: `snapshot create|list|show|compare|report`, `stats`, `dedup`
- Uses Rich for terminal output
- Async database operations with proper error handling

**4.1: Enhance Snapshot/Scan Commands**

**Tasks:**
- [ ] Add scan-specific options to `snapshot create`:
  - `--categories`: Filter by specific categories (settings, memory, subagents, desktop)
  - `--include-missing`: Include paths that don't exist in scan results
  - `--skip-content`: Don't read file contents, only metadata
  - `--parallel`: Number of parallel file reads (default: 4)
  - `--verbose`: Detailed progress output
- [ ] Add progress bars using `rich.progress` for:
  - File scanning progress
  - Database operations
  - Content reading operations
- [ ] Add `snapshot delete` command:
  - Delete single snapshot by ID
  - Delete multiple snapshots (--ids flag)
  - Cascade delete with confirmation
  - Dry-run mode (--dry-run)
- [ ] Add `snapshot tag` command:
  - Add/remove tags from snapshots
  - List all tags
  - Filter snapshots by tag
- [ ] Add `snapshot annotate` command:
  - Add annotations to snapshots
  - Edit annotations
  - List annotations for a snapshot

**Implementation Details:**
- Create `src/cli/commands/snapshot.py` (refactor from current commands.py)
- Add progress tracking to `PathScanner.create_snapshot()`
- Implement confirmation prompts using `typer.confirm()`
- Add validation for snapshot IDs and tags

**4.2: Database Management Commands**

**Tasks:**
- [ ] Create `db` command group with subcommands:
  - `db init`: Initialize database (create schema)
  - `db migrate`: Run database migrations (Alembic integration)
  - `db backup`: Create database backup
  - `db restore`: Restore from backup
  - `db vacuum`: Optimize database (VACUUM)
  - `db stats`: Show database statistics (enhance existing stats command)
  - `db clean`: Clean old snapshots/data (with retention policy)
  - `db verify`: Verify database integrity
- [ ] Add backup/restore functionality:
  - Backup to timestamped file
  - Restore with confirmation
  - List available backups
  - Backup compression (optional)
- [ ] Add cleanup commands:
  - `db clean --older-than`: Remove snapshots older than N days
  - `db clean --keep-last`: Keep only last N snapshots
  - `db clean --orphaned`: Remove orphaned file contents
  - Dry-run mode for all cleanup operations

**Implementation Details:**
- Create `src/cli/commands/db.py`
- Create `src/core/backup.py` for backup/restore logic
- Integrate Alembic CLI commands
- Add database verification using `PRAGMA integrity_check`
- Implement retention policies in configuration

**4.3: Export/Import Commands**

**Tasks:**
- [ ] Create `export` command group:
  - `export snapshot <id> --format json|csv|html --output <file>`
  - `export all --format json --output <file>`
  - `export paths <snapshot-id> --format json|csv`
  - `export changes <snapshot-id> --format json|csv|html`
  - `export config <config-type> --format json|yaml`
- [ ] Create `import` command group:
  - `import snapshot <file> --format json`
  - `import config <file> --format json|yaml`
  - Validate imported data
  - Conflict resolution (skip/overwrite/rename)
- [ ] Support formats:
  - JSON: Full data export/import
  - CSV: Tabular data (paths, changes)
  - HTML: Human-readable reports
  - YAML: Configuration files

**Implementation Details:**
- Create `src/cli/commands/export.py`
- Create `src/cli/commands/import.py`
- Create `src/utils/exporters.py` for export logic
- Create `src/utils/importers.py` for import logic
- Add data validation using Pydantic models
- Implement conflict resolution strategies

**4.4: Configuration Commands**

**Tasks:**
- [ ] Create `config` command group:
  - `config show`: Display current configuration
  - `config set <key> <value>`: Set configuration value
  - `config get <key>`: Get configuration value
  - `config validate`: Validate configuration file
  - `config wizard`: Interactive configuration wizard
  - `config reset`: Reset to default configuration
- [ ] Configuration wizard features:
  - Interactive prompts for all settings
  - Database path selection
  - Logging configuration
  - Scan path configuration
  - Environment selection (dev/prod)
- [ ] Configuration management:
  - Support multiple config files (dev/prod)
  - Environment variable overrides
  - Configuration file validation
  - Configuration file templates

**Implementation Details:**
- Create `src/cli/commands/config.py`
- Create `src/cli/wizard.py` for interactive wizard
- Enhance `src/core/config.py` with setter/getter methods
- Add configuration validation using Pydantic
- Create configuration templates in `config/` directory

**4.5: Serve Command (Web API)**

**Tasks:**
- [ ] Create `serve` command:
  - `serve --host <host> --port <port>`
  - `serve --reload`: Development mode with auto-reload
  - `serve --workers <n>`: Number of workers (if using sync framework)
  - `serve --log-level <level>`: Logging level
- [ ] Server options:
  - Default host: localhost
  - Default port: 8765 (or from config)
  - Graceful shutdown on Ctrl+C
  - Health check endpoint access
  - Open browser automatically (--open flag)

**Implementation Details:**
- Create `src/cli/commands/serve.py`
- Integrate with `src/api/server.py`
- Add signal handlers for graceful shutdown
- Add startup/shutdown messages with Rich formatting
- Implement health check display

**4.6: Progress Bars and User Feedback**

**Tasks:**
- [ ] Add progress bars for:
  - File scanning (with file count and current file)
  - Database operations (inserts, updates)
  - Content reading (bytes read, files processed)
  - Export/import operations
- [ ] Add spinners for:
  - Database initialization
  - Configuration loading
  - Short operations (< 1 second)
- [ ] Improve error messages:
  - Color-coded error messages (red for errors, yellow for warnings)
  - Detailed error context
  - Suggestions for common errors
  - Stack traces in verbose mode only
- [ ] Add success messages:
  - Green checkmarks for successful operations
  - Summary statistics after operations
  - Clear indication of what was accomplished

**Implementation Details:**
- Use `rich.progress.Progress` for progress bars
- Use `rich.spinner.Spinner` for spinners
- Create `src/cli/formatters.py` for consistent message formatting
- Add `--quiet` flag for minimal output
- Add `--verbose` flag for detailed output

**4.7: Error Handling and Validation**

**Tasks:**
- [ ] Create custom exception classes:
  - `CLIError`: Base exception for CLI errors
  - `DatabaseError`: Database-related errors
  - `ValidationError`: Input validation errors
  - `ConfigurationError`: Configuration errors
- [ ] Add input validation:
  - Validate snapshot IDs exist
  - Validate file paths
  - Validate configuration values
  - Validate export/import formats
- [ ] Add error recovery:
  - Retry logic for transient errors
  - Rollback for failed operations
  - Clear error messages with recovery suggestions
- [ ] Add logging integration:
  - Log all CLI operations
  - Log errors with stack traces
  - Log user actions for audit trail

**Implementation Details:**
- Create `src/cli/exceptions.py` for custom exceptions
- Create `src/cli/validators.py` for input validation
- Add error handlers using Typer's exception handling
- Integrate with `src/utils/logger.py`

**4.8: CLI Structure Refactoring**

**Tasks:**
- [ ] Refactor `src/cli/commands.py` into modular structure:
  - `src/cli/commands/__init__.py`: Main CLI app
  - `src/cli/commands/snapshot.py`: Snapshot commands
  - `src/cli/commands/db.py`: Database commands
  - `src/cli/commands/export.py`: Export commands
  - `src/cli/commands/import.py`: Import commands
  - `src/cli/commands/config.py`: Configuration commands
  - `src/cli/commands/serve.py`: Serve command
- [ ] Create shared utilities:
  - `src/cli/utils.py`: Shared CLI utilities
  - `src/cli/formatters.py`: Output formatting
  - `src/cli/validators.py`: Input validation
  - `src/cli/exceptions.py`: Custom exceptions
- [ ] Add command aliases and shortcuts
- [ ] Add command completion (bash/zsh/fish)
- [ ] Add help text improvements:
  - Detailed command descriptions
  - Examples for each command
  - Link to documentation

**Implementation Details:**
- Refactor existing commands.py into modular structure
- Use Typer's command groups for organization
- Add command aliases using `@app.command()` with multiple names
- Generate completion scripts using Typer's completion feature
- Add rich help formatting using Rich's Markdown support

**4.9: Testing**

**Tasks:**
- [ ] Create comprehensive CLI tests:
  - `tests/test_cli_commands.py`: Test all commands
  - `tests/test_cli_validators.py`: Test input validation
  - `tests/test_cli_formatters.py`: Test output formatting
  - `tests/test_cli_wizard.py`: Test configuration wizard
- [ ] Test scenarios:
  - Happy path for all commands
  - Error handling (invalid inputs, missing files, etc.)
  - Edge cases (empty database, large datasets, etc.)
  - Progress bars and user feedback
  - Export/import round-trip testing
- [ ] Integration tests:
  - End-to-end command execution
  - Database operations through CLI
  - Configuration management through CLI
- [ ] Mock external dependencies:
  - Mock database operations
  - Mock file system operations
  - Mock user input (for wizard)

**Implementation Details:**
- Use `typer.testing.CliRunner` for testing CLI commands
- Use `pytest` fixtures for test setup/teardown
- Use `unittest.mock` for mocking external dependencies
- Create test fixtures for common scenarios
- Add test coverage target: >80% for CLI code

**4.10: Documentation**

**Tasks:**
- [ ] Update CLI documentation:
  - Add command reference to `docs/CLI.md`
  - Add usage examples
  - Add troubleshooting guide
  - Add configuration guide
- [ ] Add inline help:
  - Comprehensive docstrings for all commands
  - Parameter descriptions
  - Examples in help text
- [ ] Create quick reference:
  - Common commands cheat sheet
  - Command aliases reference
  - Configuration options reference

**Implementation Details:**
- Update `docs/CLI.md` with all commands
- Add examples to command docstrings
- Create `docs/CLI_QUICK_REF.md` for quick reference
- Add CLI usage to main README.md

**Dependencies:**
- Phase 2: Database layer must be complete
- Phase 3: Core refactoring (scanner, models, validators) must be complete
- Alembic must be set up for migration commands

**Timeline Estimate:**
- 4.1: Enhance Snapshot/Scan Commands - 0.5 days
- 4.2: Database Management Commands - 1 day
- 4.3: Export/Import Commands - 1 day
- 4.4: Configuration Commands - 0.5 days
- 4.5: Serve Command - 0.25 days
- 4.6: Progress Bars and User Feedback - 0.5 days
- 4.7: Error Handling and Validation - 0.5 days
- 4.8: CLI Structure Refactoring - 0.5 days
- 4.9: Testing - 1 day
- 4.10: Documentation - 0.25 days

**Total: ~5.5 days** (updated from original 2 days estimate)

**Success Criteria:**
- All commands implemented and tested
- Progress bars working for long operations
- Comprehensive error handling
- Configuration wizard functional
- Export/import round-trip working
- Database management commands working
- Test coverage >80%
- Documentation complete

### Phase 5: API Enhancement

- [ ] Refactor server to use new structure
- [ ] Add proper route organization
- [ ] Implement database-backed endpoints
- [ ] Add new endpoints for history
- [ ] Add API documentation

### Phase 6: Testing & Documentation

- [ ] Write comprehensive tests
- [ ] Add API documentation
- [ ] Add deployment guide
- [ ] Add developer guide
- [ ] Add user manual

### Phase 7: Deployment & DevOps

- [ ] Create Windows service installer/configuration
- [ ] Add health check endpoints
- [ ] Create deployment documentation for Windows
- [ ] Add graceful shutdown handling
- ~~Create Dockerfile~~ (not needed)
- ~~Add docker-compose~~ (not needed)
- ~~Create systemd service~~ (not needed - Windows only)
- ~~Add CI/CD configuration~~ (optional - local tool)
- ~~Add monitoring/health checks~~ (not needed - no monitoring)

## Technology Stack

### Core

- **Python**: 3.9+
- **Database**: SQLite3 (only - no multi-DB support)
- **ORM**: SQLAlchemy 2.0
- **Migrations**: Alembic (SQLite-only migrations)

### CLI

- **Framework**: Typer (already implemented)
- **Output**: Rich (for beautiful terminal output)
- **Progress**: rich.progress (integrated with Rich)

### API/Web

- **Framework**: FastAPI (async) or Flask (sync)
- **WSGI/ASGI**: Uvicorn (FastAPI) or Gunicorn (Flask)
- **Validation**: Pydantic
- **API Docs**: OpenAPI/Swagger (auto-generated)

### Configuration

- **Format**: YAML or TOML
- **Validation**: Pydantic or OmegaConf
- **Secrets**: python-dotenv

### Logging

- **Library**: structlog or python-logging
- **Format**: JSON
- **Rotation**: logging.handlers.RotatingFileHandler

### Testing

- **Framework**: pytest
- **Fixtures**: pytest-fixtures
- **Coverage**: pytest-cov
- **Mocking**: pytest-mock or unittest.mock
- **API Testing**: httpx or requests

### Development

- **Formatting**: black
- **Linting**: ruff or flake8
- **Type Checking**: mypy
- **Pre-commit**: pre-commit hooks

### Deployment

- **Platform**: Windows (single machine)
- **Process Management**: Windows Service or direct execution
- **No containerization needed** (local tool)

## Code Quality Standards

### Style Guide

- PEP 8 compliance
- Type hints for all functions
- Docstrings (Google or NumPy style)
- Max line length: 88 (Black default)

### Testing Standards

- Minimum 80% code coverage
- All public APIs tested
- Edge cases covered
- Performance tests for critical paths

### Documentation Standards

- README with quick start
- API documentation (OpenAPI)
- Code documentation (docstrings)
- Architecture decision records (ADRs)
- Changelog (Keep a Changelog format)

## Migration Strategy

### Option 1: Gradual Migration (Recommended)

1. Create new structure alongside existing code
2. Move one module at a time
3. Keep both versions working
4. Deprecate old version after testing
5. Remove old code

### Option 2: Clean Rewrite

1. Create new project structure
2. Reimplement features with new architecture
3. Migrate data/functionality
4. Switch over completely
5. Archive old version

## Breaking Changes

### For Users

- New command-line interface (old scripts deprecated)
- New configuration file format
- New database storage (migration tool provided)
- New API endpoints (old ones marked deprecated)

### For Developers

- New project structure
- New import paths
- New testing framework
- New deployment process

## Backward Compatibility

### Provide

- Data migration scripts
- API compatibility layer (temporary)
- Configuration converter
- Import/export tools

## Timeline Estimate

- **Phase 1**: 2-3 days
- **Phase 2**: 2-3 days
- **Phase 3**: 3-4 days
- **Phase 4**: 5.5 days (updated - see detailed plan)
- **Phase 5**: 2-3 days
- **Phase 6**: 3-4 days
- **Phase 7**: 2-3 days

**Total**: ~3.5-4.5 weeks for complete production-grade upgrade

## Next Steps

1. ~~**Clarify requirements**~~ ✅ **Done** (see "Questions to Answer - Decisions Made" section)
2. **Choose technology stack** (FastAPI vs Flask, etc.) - *Pending decision*
3. **Set up development environment**
4. ~~**Start with Phase 1**~~ ✅ **Completed** (structure & setup done)
5. **Work on Phase 2 remaining tasks**:
   - Add Alembic migration system for SQLite
   - Write comprehensive database tests
6. **Iterate based on feedback**

## Questions to Answer - Decisions Made

### Answered Questions

1. **Should we store file contents in database or just metadata?**  
   ✅ **Answer: File contents should be stored in database**  
   *Impact: Confirms `file_contents` table in schema is correct*

2. **Do we need authentication/authorization?**  
   ✅ **Answer: No, we don't need authentication/authorization - this is a local-only tool**  
   *Impact: Simplifies API design, no auth middleware needed*

3. **What's the deployment target? (Docker, systemd, Windows service?)**  
   ✅ **Answer: Presume this is running on a single Windows machine**  
   *Impact: Focus on Windows-specific deployment, no need for Docker/systemd*

4. **Do we need real-time features (WebSockets)?**  
   ✅ **Answer: No, we don't need real-time features**  
   *Impact: Standard REST API is sufficient, no WebSocket implementation needed*

5. **What's the expected scale? (single user vs multi-user)**  
   ✅ **Answer: Single user**  
   *Impact: No multi-tenancy needed, simplified database design*

6. **Should we support PostgreSQL in addition to SQLite?**  
   ✅ **Answer: No, we should only support SQLite**  
   *Impact: Simplifies migration system (Alembic with SQLite only), no multi-DB abstraction needed*

7. **Do we need a background job queue?**  
   ✅ **Answer: No, we don't need a background job queue**  
   *Impact: Synchronous operations are acceptable, no Celery/Redis needed*

8. **Should we add monitoring/metrics (Prometheus, etc.)?**  
   ✅ **Answer: No, we don't need monitoring/metrics**  
   *Impact: Focus on core functionality, no observability stack needed*

### Impact on Phase 2 Remaining Tasks

Based on the answers above, the remaining Phase 2 tasks can be simplified:

#### Add Migration System

- **Technology**: Alembic (works well with SQLite)
- **Scope**: SQLite-only migrations (no multi-DB support needed)
- **Complexity**: Simplified since we only need to support one database type
- **Considerations**:
  - SQLite has some limitations with ALTER TABLE, may need workarounds
  - Single-user means no concurrent migration concerns

#### Write Database Tests

- **Scope**: Test SQLite database operations
- **Test Database**: Use in-memory SQLite for fast tests
- **Focus Areas**:
  - File contents storage and retrieval
  - Single-user scenarios (no concurrency tests needed)
  - Schema migrations
  - Data integrity (foreign keys, constraints)
- **Test Data**: Single user, local Windows paths
