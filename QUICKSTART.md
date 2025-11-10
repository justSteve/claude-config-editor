# Quick Start Guide - Claude Config Version Control

## Overview

Claude Config Editor v2.0 is a production-grade version control system for Claude Code and Claude Desktop configurations. It provides git-like snapshot management with complete history tracking, deduplication, and change detection.

## Installation

### 1. Clone or Update Repository

```bash
git clone https://github.com/justSteve/claude-config-editor.git
cd claude-config-editor
```

### 2. Create Virtual Environment

```bash
python -m venv .venv
```

### 3. Activate Virtual Environment

**Windows:**
```bash
.venv\Scripts\activate
```

**Linux/Mac:**
```bash
source .venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
pip install -e .
```

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

## Example Workflow

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
