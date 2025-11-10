# Phase 4: CLI Enhancement - Detailed Plan

**Status**: In Progress  
**Start Date**: 2025-11-09  
**Estimated Duration**: 1-2 weeks

## Overview

Phase 4 focuses on enhancing the existing Typer-based CLI to provide a professional, user-friendly command-line interface with comprehensive functionality, excellent UX, and proper error handling.

## Current State Analysis

### Existing Commands
✅ Already implemented in `src/cli/commands.py`:
- `snapshot create` - Create new snapshot
- `snapshot list` - List recent snapshots
- `snapshot show <id>` - Show snapshot details
- `snapshot compare <id>` - Compare snapshots
- `stats` - Show database statistics
- `dedup` - Show deduplication info

### Strengths
- ✅ Typer framework with Rich formatting
- ✅ Async database operations
- ✅ Good table formatting with Rich
- ✅ Basic error handling
- ✅ Panel and table layouts

### Areas for Improvement
- ❌ Single large file (544 lines)
- ❌ No progress bars for long operations
- ❌ Limited error messages
- ❌ No export/import commands
- ❌ No configuration commands
- ❌ No serve command
- ❌ No tests
- ❌ No command completion

## Phase 4 Tasks

### Task 4.1: Refactor CLI Structure ⭐ **START HERE**

**Goal**: Modular, maintainable CLI structure

**Files to Create**:
- `src/cli/commands/__init__.py` - Main CLI app
- `src/cli/commands/snapshot.py` - Snapshot commands
- `src/cli/commands/database.py` - Database commands
- `src/cli/commands/export_import.py` - Export/import commands
- `src/cli/commands/config.py` - Configuration commands
- `src/cli/commands/serve.py` - Serve command
- `src/cli/utils.py` - Shared CLI utilities
- `src/cli/formatters.py` - Output formatting
- `src/cli/progress.py` - Progress bars and spinners

**Subtasks**:
1. Create commands directory structure
2. Move snapshot commands to `snapshot.py`
3. Move stats/dedup to `database.py`
4. Create shared utilities module
5. Create formatters module
6. Update main `commands.py` to import from modules

**Estimated Time**: 0.5 days

---

### Task 4.2: Add Progress Indicators

**Goal**: Visual feedback for long-running operations

**Features**:
- Progress bars for file scanning
- Progress bars for database operations
- Spinners for quick operations
- Step indicators for multi-step operations

**Commands to Enhance**:
- `snapshot create` - Progress during scan
- `snapshot compare` - Progress during comparison
- `export` - Progress during export
- `import` - Progress during import

**Implementation**:
- Use `rich.progress.Progress`
- Use `rich.spinner.Spinner`
- Create reusable progress context managers

**Estimated Time**: 0.5 days

---

### Task 4.3: Add Export Commands

**Goal**: Export snapshots and data in various formats

**Commands**:
```bash
claude-config export snapshot <id> [--format json|yaml|html|csv]
claude-config export config [--output file.yaml]
claude-config export database [--output backup.sql]
```

**Features**:
- Export snapshot to JSON/YAML/HTML/CSV
- Export configuration to YAML
- Export database (SQLite backup)
- Progress indicators
- Compression option

**Estimated Time**: 1 day

---

### Task 4.4: Add Import Commands

**Goal**: Import snapshots and configurations

**Commands**:
```bash
claude-config import snapshot <file> [--format json|yaml]
claude-config import config <file>
```

**Features**:
- Import snapshot from JSON/YAML
- Import configuration from YAML
- Validation before import
- Dry-run mode
- Progress indicators

**Estimated Time**: 1 day

---

### Task 4.5: Add Configuration Commands

**Goal**: Manage configuration via CLI

**Commands**:
```bash
claude-config config show [--environment dev|prod|test]
claude-config config set <key> <value>
claude-config config get <key>
claude-config config init  # Configuration wizard
claude-config config validate
```

**Features**:
- Show current configuration
- Set configuration values
- Get configuration values
- Interactive configuration wizard
- Validation

**Estimated Time**: 1 day

---

### Task 4.6: Add Database Management Commands

**Goal**: Database maintenance and management

**Commands**:
```bash
claude-config db init  # Initialize database
claude-config db migrate  # Run migrations
claude-config db vacuum  # Vacuum database
claude-config db backup [--output file.db]
claude-config db restore <file.db>
claude-config db health  # Health check
```

**Features**:
- Database initialization
- Migration management
- Vacuum and optimization
- Backup and restore
- Health checks

**Estimated Time**: 1 day

---

### Task 4.7: Add Serve Command

**Goal**: Start API server from CLI

**Command**:
```bash
claude-config serve [--host 0.0.0.0] [--port 8765] [--reload]
```

**Features**:
- Start FastAPI server
- Development mode with auto-reload
- Production mode
- Open browser automatically
- Graceful shutdown

**Note**: Requires Phase 5 (API) to be started

**Estimated Time**: 0.5 days (after Phase 5)

---

### Task 4.8: Enhance Snapshot Commands

**Goal**: Add more options and features

**Enhancements**:
```bash
# Enhanced create
claude-config snapshot create \
    --notes "Production backup" \
    --tags prod,backup,v1.2.3 \
    --categories settings,memory \
    --skip-content  # Metadata only
    --parallel 8  # Parallel file reads

# Enhanced list
claude-config snapshot list \
    --filter trigger_type=api \
    --tags prod \
    --since "2025-01-01" \
    --until "2025-12-31" \
    --sort time|size|files

# Enhanced show
claude-config snapshot show <id> \
    --format json|yaml|table \
    --output file.json

# New commands
claude-config snapshot delete <id>
claude-config snapshot tag <id> <tag>
claude-config snapshot annotate <id> "Note text"
claude-config snapshot report <id>  # Detailed report
```

**Estimated Time**: 1 day

---

### Task 4.9: Improve Error Handling

**Goal**: Better error messages and recovery

**Features**:
- Custom exception classes for CLI
- Colored error messages (red)
- Helpful error recovery suggestions
- Stack traces in verbose mode only
- Exit codes for scripting

**Implementation**:
- Create `src/cli/exceptions.py`
- Add error handlers to all commands
- Add `--verbose` flag for debugging
- Add `--quiet` flag for scripting

**Estimated Time**: 0.5 days

---

### Task 4.10: Add Help and Examples

**Goal**: Comprehensive help and examples

**Features**:
- Detailed command descriptions
- Usage examples for each command
- Link to online documentation
- Interactive help with `--help`
- Command aliases (shortcuts)

**Implementation**:
- Enhance docstrings
- Add examples to help text
- Create `claude-config examples` command
- Add command completion (bash/zsh)

**Estimated Time**: 0.5 days

---

### Task 4.11: Add Logging Commands

**Goal**: View and manage logs

**Commands**:
```bash
claude-config logs show [--level info|debug|warning|error]
claude-config logs tail [-n 100]
claude-config logs clear
```

**Features**:
- Show logs with filtering
- Tail logs in real-time
- Clear old logs
- Export logs

**Estimated Time**: 0.5 days

---

### Task 4.12: Add CLI Tests

**Goal**: Comprehensive CLI testing

**Tests**:
- Unit tests for each command
- Integration tests for command flows
- Test error handling
- Test progress indicators
- Test formatters

**Files to Create**:
- `tests/cli/test_snapshot_commands.py`
- `tests/cli/test_database_commands.py`
- `tests/cli/test_export_import.py`
- `tests/cli/test_config_commands.py`
- `tests/cli/test_formatters.py`

**Estimated Time**: 2 days

---

## Implementation Order

### Week 1: Core Enhancements
1. **Task 4.1**: Refactor CLI structure (0.5 days) ⭐ **START HERE**
2. **Task 4.2**: Add progress indicators (0.5 days)
3. **Task 4.3**: Add export commands (1 day)
4. **Task 4.4**: Add import commands (1 day)
5. **Task 4.5**: Add configuration commands (1 day)
6. **Task 4.6**: Add database commands (1 day)

**Week 1 Total**: 5.5 days

### Week 2: Polish and Testing
7. **Task 4.8**: Enhance snapshot commands (1 day)
8. **Task 4.9**: Improve error handling (0.5 days)
9. **Task 4.10**: Add help and examples (0.5 days)
10. **Task 4.11**: Add logging commands (0.5 days)
11. **Task 4.12**: Add CLI tests (2 days)
12. **Task 4.7**: Add serve command (0.5 days) - After Phase 5 starts

**Week 2 Total**: 5 days

**Total Phase 4**: 10.5 days (1.5-2 weeks)

---

## Success Criteria

### Functionality
- [ ] All planned commands implemented
- [ ] Export/import working for all formats
- [ ] Configuration management working
- [ ] Database management working
- [ ] Progress indicators on long operations

### Quality
- [ ] No lint errors
- [ ] 80%+ test coverage
- [ ] All commands documented
- [ ] Examples provided
- [ ] Error handling comprehensive

### User Experience
- [ ] Fast command execution
- [ ] Clear progress feedback
- [ ] Helpful error messages
- [ ] Good command discoverability
- [ ] Professional formatting

---

## Dependencies

### External Dependencies
None! All required packages already installed:
- `typer` - CLI framework
- `rich` - Terminal formatting
- `click` - Typer dependency

### Internal Dependencies
- Phase 2 (Database) - Complete ✅
- Phase 3 (Core) - Complete ✅
- Phase 5 (API) - Only for `serve` command

---

## Testing Strategy

### Manual Testing
- Test all commands manually
- Test error scenarios
- Test help text
- Test examples

### Automated Testing
- Unit tests for each command
- Integration tests for workflows
- Test fixtures for database
- Mock user input

### User Acceptance Testing
- Get feedback on UX
- Test with real-world scenarios
- Iterate on error messages
- Improve help text

---

## Documentation

### To Create
- [ ] CLI reference guide
- [ ] Command examples
- [ ] Configuration guide (CLI-specific)
- [ ] Troubleshooting guide
- [ ] Migration guide (from old CLI)

### To Update
- [ ] README.md - Add CLI usage
- [ ] Installation guide
- [ ] Quick start guide

---

## Risk Assessment

### Low Risk ✅
- Refactoring existing working code
- Adding new commands (additive)
- Progress indicators (cosmetic)

### Medium Risk ⚠️
- Import/export (data integrity)
- Database commands (backup/restore)
- Configuration changes (validation)

### Mitigation
- Comprehensive testing
- Dry-run modes for dangerous operations
- Validation before destructive operations
- Clear confirmation prompts

---

## Future Enhancements (Post-Phase 4)

- [ ] Interactive TUI mode (textual)
- [ ] Auto-completion for all shells
- [ ] Plugins/extensions system
- [ ] Scheduled snapshots via CLI
- [ ] Email notifications
- [ ] Slack/Discord integrations
- [ ] Snapshot diff viewer
- [ ] Configuration version control
- [ ] Multi-machine synchronization

---

## Getting Started

**Next Step**: Begin Task 4.1 - Refactor CLI Structure

1. Create `src/cli/commands/` directory
2. Split `commands.py` into modules
3. Create shared utilities
4. Update imports
5. Test all existing commands still work

**Command to start**:
```bash
# Create directory structure
mkdir -p src/cli/commands

# Start with snapshot commands module
# (Implementation in next steps)
```

---

**Document Created**: 2025-11-09  
**Status**: Ready to begin  
**First Task**: 4.1 - Refactor CLI Structure

