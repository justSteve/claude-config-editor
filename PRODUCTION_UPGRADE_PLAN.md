# Production Upgrade Plan

## Project Structure

```
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
- Authentication/Authorization (optional)
- Rate limiting
- CORS configuration
- API versioning (/api/v1/)
- OpenAPI/Swagger documentation
- WebSocket support for real-time updates

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
- Caching layer (in-memory or Redis)
- Async I/O where applicable
- Batch operations
- Connection pooling
- Query optimization

### 9. Security
- Input validation
- SQL injection prevention
- XSS protection
- Path traversal prevention
- Secure defaults
- Security headers

### 10. Deployment
- Docker support (Dockerfile, docker-compose)
- systemd service file
- Windows service support
- Health check endpoints
- Graceful shutdown
- Environment-based configuration

## Implementation Phases

### Phase 1: Project Structure & Setup
- [ ] Create new directory structure
- [ ] Set up virtual environment
- [ ] Create requirements.txt
- [ ] Set up pyproject.toml
- [ ] Configure logging
- [ ] Create base configuration system

### Phase 2: Database Layer
- [ ] Design database schema
- [ ] Create database manager
- [ ] Implement models
- [ ] Add migration system
- [ ] Write database tests

### Phase 3: Core Refactoring
- [ ] Extract scanner logic to core/scanner.py
- [ ] Add configuration management
- [ ] Implement logging throughout
- [ ] Add data models
- [ ] Add validators

### Phase 4: CLI Enhancement
- [ ] Implement Click-based CLI
- [ ] Add scan command with options
- [ ] Add database management commands
- [ ] Add export/import commands
- [ ] Add configuration commands

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
- [ ] Create Dockerfile
- [ ] Add docker-compose
- [ ] Create systemd service
- [ ] Add CI/CD configuration
- [ ] Add monitoring/health checks

## Technology Stack

### Core
- **Python**: 3.9+
- **Database**: SQLite3 (with option to upgrade to PostgreSQL)
- **ORM**: SQLAlchemy 2.0
- **Migrations**: Alembic

### CLI
- **Framework**: Click or Typer
- **Output**: Rich (for beautiful terminal output)
- **Progress**: tqdm or rich.progress

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
- **Containerization**: Docker
- **Orchestration**: docker-compose
- **Process Management**: systemd or supervisord

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
- **Phase 4**: 2 days
- **Phase 5**: 2-3 days
- **Phase 6**: 3-4 days
- **Phase 7**: 2-3 days

**Total**: ~3-4 weeks for complete production-grade upgrade

## Next Steps

1. **Clarify requirements** (storage strategy, API behavior)
2. **Choose technology stack** (FastAPI vs Flask, etc.)
3. **Set up development environment**
4. **Start with Phase 1** (structure & setup)
5. **Iterate based on feedback**

## Questions to Answer

1. Should we store file contents in database or just metadata?
2. Do we need authentication/authorization?
3. What's the deployment target? (Docker, systemd, Windows service?)
4. Do we need real-time features (WebSockets)?
5. What's the expected scale? (single user vs multi-user)
6. Should we support PostgreSQL in addition to SQLite?
7. Do we need a background job queue?
8. Should we add monitoring/metrics (Prometheus, etc.)?
