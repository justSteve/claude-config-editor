
Based on my understanding of the project, here's the objective definition formatted for CLAUDE.md:
## Project Objective

**Claude Config Version Control System** - A production-grade tool for tracking, analyzing, and managing Claude Code and Claude Desktop configurations with git-like version control capabilities.

### Core Mission

Provide developers with comprehensive visibility and control over their Claude configuration ecosystem by:

1. **Snapshot Management**: Capture complete point-in-time snapshots of all Claude configurations (17 tracked locations including settings, MCP servers, memory files, slash commands, and logs)

2. **Change Detection**: Track what changed between sessions with automatic diff generation, enabling users to understand configuration evolution and troubleshoot issues

3. **Content Deduplication**: Use SHA256-based storage optimization to reduce database size by ~97%, making long-term configuration history practical

4. **Rich Reporting**: Generate comprehensive reports in multiple formats (CLI, JSON, interactive HTML) with searchable file contents and detailed metadata

5. **Configuration Cleanup**: Clean bloated .claude.json files (17MB → 732KB typical) while preserving important project history

### Problem Statement

Claude Code and Claude Desktop store extensive configuration data including:
- Full conversation histories for every project
- MCP server configurations
- Project-specific settings and permissions
- Memory files (CLAUDE.md) and slash commands

This creates several challenges:
- **Bloat**: Configuration files grow to 10+ MB, slowing down Claude
- **Opacity**: Users can't easily see what changed between sessions
- **No History**: No version control for configuration changes
- **Manual Editing**: JSON files require careful manual editing with backup risks

### Solution Approach

A dual-interface system combining:

**1. Legacy Web GUI (v1.0)**
- Visual project history browser
- Bulk project deletion
- MCP server management
- JSON export capabilities
- System paths visualization

**2. Production Version Control System (v2.0+)**
- Git-like snapshot architecture with SQLite backend
- Async Python with Pydantic validation
- CLI commands for snapshot operations
- Multi-format report generation
- Interactive HTML search interface
- Windows environment variable resolution
- Automatic change tracking between snapshots

### Target Users

- **Claude Code (CLI) users**: Developers managing multiple projects with complex configurations
- **Claude Desktop users**: Users needing visibility into desktop configuration state
- **Power users**: Those requiring configuration history, rollback, and change analysis
- **Teams**: Groups needing to track and share Claude configuration changes

### Current Capabilities (Phase 1-2 Complete)

✅ Complete snapshot system capturing 17 configuration locations  
✅ SHA256 content deduplication with 97% storage savings  
✅ Automatic change detection between snapshots  
✅ Multi-format reporting (CLI/JSON/HTML)  
✅ Interactive HTML search across file contents  
✅ File type filtering and scope-based search  
✅ Database statistics and deduplication analysis  
✅ Windows path handling with environment variable expansion  
✅ Legacy GUI for visual configuration management  

### Planned Enhancements (Phase 3-7)

- **Phase 3**: Advanced search & query capabilities
- **Phase 4**: Tags, annotations, and custom metadata
- **Phase 5**: Configuration restoration and rollback
- **Phase 6**: Claude-specific intelligence (conversation analysis, prompt patterns)
- **Phase 7**: Unified GUI integrating version control with visual management

### Technical Stack

- **Backend**: Python 3.11+ with async/await
- **Database**: SQLite with WAL mode
- **ORM**: SQLAlchemy 2.0 (async)
- **Validation**: Pydantic v2
- **CLI**: Typer with Rich terminal formatting
- **Web GUI**: Vanilla HTML/CSS/JavaScript (legacy)
- **Platform**: Windows (primary), cross-platform compatible

### Success Metrics

- Configuration file size reduction (target: >90%)
- Snapshot creation time (<5 seconds for typical configs)
- Change detection accuracy (100% file-level)
- Report generation speed (<2 seconds for HTML)
- Storage efficiency (>95% deduplication for unchanged content)