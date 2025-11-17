# Quick Start Guide - Claude Config Version Control

## Overview

Claude Config Editor captures **point-in-time snapshots of your Claude configuration files** across 17 locations:

- `.claude.json` (conversation histories, MCP servers)
- `settings.json` (user/project/enterprise settings)
- `CLAUDE.md` files (memory/instructions)
- MCP server configs
- Slash commands
- Desktop logs

This enables you to track how your Claude configurations evolve over time, detect what changed between sessions, and restore previous states.

## Prerequisites

- **Docker Desktop** installed and running
  - Download: <https://www.docker.com/products/docker-desktop>
- **Git** for version control

## Installation (One-Time Setup)

```cmd
# 1. Clone repository
git clone https://github.com/justSteve/claude-config-editor.git
cd claude-config-editor

# 2. Build and start development container
setup-dev-env.bat
```

This creates a containerized environment with:

- Python 3.11.7 (exact version locked)
- All dependencies pre-installed
- Identical environment for you and AI agents
- Persistent SQLite database for config snapshots

## Daily Workflow

### Start Your Session

```cmd
session-start.bat
```

This automated script:

1. Starts Docker container (if not running)
2. Shows last 5 git commits (project code changes)
3. Displays last commit details
4. Shows working tree status
5. **Creates Claude config snapshot** (captures current state of all 17 config locations)
6. Runs test suite health check

**Example output:**

```text
[1/5] LAST SESSION SUMMARY
----------------------------------------
e5b405a restored legacy function
ac87d0b feat(docker): Add containerized development environment

[4/5] CREATING BASELINE SNAPSHOT
----------------------------------------
Snapshot #42 created successfully
  - Scanned 17 configuration locations
  - Found 12 files (3 new, 2 modified since last snapshot)
  - Deduplicated storage: 97% savings
```

### During Development

```cmd
# Run any command in the container
runin "pytest"
runin "python -m src.cli.commands snapshot list"
runin "python -m src.api.app"

# Enter container shell for interactive work
docker exec -it claude-config-dev bash

# Create config snapshot after Claude settings change
runin "python -m src.cli.commands snapshot create --notes 'Added new MCP server'"

# See what changed in your Claude configs
runin "python -m src.cli.commands snapshot show LATEST --changes"
```

### End Your Session

```cmd
session-end.bat
```

This automated script:

1. **Creates final Claude config snapshot** with your summary
2. Shows working tree status (git)
3. Guides commit workflow (optional)
4. Prompts for next-steps documentation
5. Saves notes to `SESSION_NOTES.md`

## Quick Reference

| Command | Description |
|---------|-------------|
| `session-start.bat` | Initialize session, snapshot configs |
| `session-end.bat` | Final config snapshot, commit code |
| `runin "command"` | Execute command in container |
| `docker-compose down` | Stop container |
| `docker-compose up -d dev-env` | Start container |

## What Are Config Snapshots?

**Config snapshots capture your Claude configuration files** - NOT your project code (that's git).

Each snapshot stores:

- Complete file contents from 17 config locations
- SHA256 hashes for deduplication
- Timestamps and metadata
- Change detection from previous snapshot

**Use cases:**

- "What MCP servers did I have configured last week?"
- "Why is my .claude.json suddenly 15MB?"
- "Which CLAUDE.md file changed my agent's behavior?"
- "Restore my settings from before I broke something"

## Basic Usage

### Create a Snapshot

Capture the current state of all Claude configurations:

```bash
python -m src.cli.commands snapshot list
```

With optional notes:

```bash
python -m src.cli.commands snapshot create --notes "Before cleanup"
```

### List Snapshots

View all snapshots:

```bash
python -m src.cli.commands snapshot list
```

Limit results:

```bash
python -m src.cli.commands snapshot list --limit 5
```

### View Snapshot Details

Show full details of a specific snapshot:

```bash
python -m src.cli.commands snapshot show 1
```

Show all scanned paths:

```bash
python -m src.cli.commands snapshot show 1 --paths
```

Show changes from previous snapshot:

```bash
python -m src.cli.commands snapshot show 1 --changes
```

### Database Statistics

View database statistics:

```bash
python -m src.cli.commands stats
```

## What Gets Tracked?

The system tracks 17 configuration locations across 7 categories:

1. **Settings Files** (5 locations)
   - User settings
   - Project settings
   - Enterprise settings
   - Original .claude.json

2. **Memory Files** (3 locations)
   - User CLAUDE.md
   - Project CLAUDE.md
   - Enterprise CLAUDE.md

3. **Subagents** (2 locations)
   - User subagents
   - Project subagents

4. **Claude Desktop** (1 location)
   - Desktop config

5. **Slash Commands** (2 locations)
   - User commands
   - Project commands

6. **MCP Servers** (3 locations)
   - Desktop MCP config
   - User MCP config
   - Project MCP config

7. **Logs** (1 location)
   - Claude Desktop logs

## Features

### ✅ Complete Snapshots
- Full file contents captured
- Complete metadata (timestamps, sizes, permissions)
- Environment context (OS, user, paths)
- System state at scan time

### ✅ Smart Deduplication
- Files with same content stored once
- SHA256 hash-based deduplication
- Reference counting for cleanup
- ~97% storage savings

### ✅ Change Tracking
- Automatic diff between snapshots
- Track: added, deleted, modified files
- Store change summaries
- Link to parent snapshot

### ✅ Production-Grade
- Async SQLite with WAL mode
- Proper logging and configuration
- Type hints and documentation
- Error handling throughout

## Automated Session Management

The daily workflow is automated via `session-start.bat` and `session-end.bat` (see [Daily Workflow](#daily-workflow) above).

These scripts handle:

- Environment initialization
- Git history review
- Snapshot creation
- Test verification
- Commit workflow
- Next-steps documentation

---

## Example Workflows

### Daily Backup

```bash
# Morning snapshot
python -m src.cli.commands snapshot create --notes "Start of day"

# After changes
python -m src.cli.commands snapshot create --notes "Added new MCP server"

# View what changed
python -m src.cli.commands snapshot show 2 --changes
```

### Before Major Changes

```bash
# Create baseline
python -m src.cli.commands snapshot create --notes "Before cleanup"

# Make changes...

# Verify
python -m src.cli.commands snapshot create --notes "After cleanup"
python -m src.cli.commands snapshot show 2 --changes
```

## Database Location

By default, snapshots are stored in:
```
./data/claude_config.db
```

Configure via environment variable:
```bash
export DATABASE_URL=sqlite+aiosqlite:///path/to/your/database.db
```

## Configuration

Create a `.env` file for custom configuration (copy from `.env.example`):

```bash
cp .env.example .env
```

Edit `.env` to configure:
- Database location
- Logging settings
- Snapshot retention
- Auto-compression settings

## Next Steps

- **Phase 2**: Comparison views and diff generation
- **Phase 3**: Search and query capabilities
- **Phase 4**: Tags and annotations
- **Phase 5**: Restoration and rollback
- **Phase 6**: Claude-specific intelligence (MCP tracking, bloat detection)
- **Phase 7**: GUI integration

## Need Help?

- Check logs in `./logs/app.log`
- See documentation in `./docs/`
- Report issues: https://github.com/justSteve/claude-config-editor/issues

## Legacy Tools

The original scanner tools are still available:

```bash
# Comprehensive Windows path scanner
python windows_scan.py

# Original web GUI
python server.py
```

## Version

**Current Version**: 2.0.0 (Phase 1 Complete)

**What's New in 2.0**:
- Complete rewrite with production architecture
- Git-like version control for configurations
- Database-backed snapshot system
- SHA256 content deduplication
- Async operations throughout
- Comprehensive logging and error handling
- Type-safe with Pydantic models
