# Windows Path Scanner for Claude Code & Claude Desktop

## Overview

This script replicates and extends the original configuration detection logic from `server.py` to comprehensively scan ALL documented Windows paths for Claude Code and Claude Desktop settings, configs, and related files.

## Windows Environment Variables

This scanner uses Windows environment variables that are automatically expanded to their actual paths:

| Placeholder | Typical Resolved Path | Description |
|-------------|----------------------|-------------|
| `%USERPROFILE%` | `C:\Users\{username}` | Current user's profile directory |
| `%APPDATA%` | `C:\Users\{username}\AppData\Roaming` | Application data folder |
| `%ProgramData%` | `C:\ProgramData` | Shared program data for all users |

**Note:** All paths below use placeholder notation (`%VARIABLE%`) in documentation, but the scanner automatically expands them to fully qualified paths (e.g., `C:\Users\steve\...`) when running.

## What It Does

The `windows_scan.py` script scans **17 different locations** across your Windows system to detect:

### 1. Settings Files (5 locations)

| Setting | Path Template | Example Resolved Path |
|---------|--------------|----------------------|
| User Settings | `%USERPROFILE%\.claude\settings.json` | `C:\Users\steve\.claude\settings.json` |
| Project Settings (Shared) | `.claude\settings.json` | `{current_dir}\.claude\settings.json` |
| Project Settings (Local) | `.claude\settings.local.json` | `{current_dir}\.claude\settings.local.json` |
| Enterprise Managed Settings | `%ProgramData%\ClaudeCode\managed-settings.json` | `C:\ProgramData\ClaudeCode\managed-settings.json` |
| Original Claude Code Config | `%USERPROFILE%\.claude.json` | `C:\Users\steve\.claude.json` |

### 2. Memory Files (CLAUDE.md) (3 locations)

| Memory File | Path Template | Example Resolved Path |
|-------------|--------------|----------------------|
| User Memory | `%USERPROFILE%\.claude\CLAUDE.md` | `C:\Users\steve\.claude\CLAUDE.md` |
| Project Memory | `.\CLAUDE.md` | `{current_dir}\CLAUDE.md` |
| Enterprise Memory | `%ProgramData%\ClaudeCode\CLAUDE.md` | `C:\ProgramData\ClaudeCode\CLAUDE.md` |

### 3. Subagents (2 locations)

| Subagent Directory | Path Template | Example Resolved Path |
|--------------------|--------------|----------------------|
| User Subagents | `%USERPROFILE%\.claude\agents\` | `C:\Users\steve\.claude\agents\` |
| Project Subagents | `.claude\agents\` | `{current_dir}\.claude\agents\` |

### 4. Claude Desktop (1 location)

| Config | Path Template | Example Resolved Path |
|--------|--------------|----------------------|
| Config File | `%APPDATA%\Claude\claude_desktop_config.json` | `C:\Users\steve\AppData\Roaming\Claude\claude_desktop_config.json` |

### 5. Slash Commands (2 locations)

| Command Directory | Path Template | Example Resolved Path |
|-------------------|--------------|----------------------|
| Project Commands | `.claude\commands\` | `{current_dir}\.claude\commands\` |
| Personal Commands | `%USERPROFILE%\.claude\commands\` | `C:\Users\steve\.claude\commands\` |

### 6. MCP Servers (3 locations)

| MCP Config | Path Template | Example Resolved Path |
|------------|--------------|----------------------|
| User Settings (Local Scope) | `%USERPROFILE%\.claude\settings.json` | `C:\Users\steve\.claude\settings.json` |
| Project Config | `.mcp.json` | `{current_dir}\.mcp.json` |
| Claude Desktop MCP Config | `%APPDATA%\Claude\claude_desktop_config.json` | `C:\Users\steve\AppData\Roaming\Claude\claude_desktop_config.json` |

### 7. Logs (1 location)

| Log Directory | Path Template | Example Resolved Path |
|---------------|--------------|----------------------|
| MCP Logs Directory | `%APPDATA%\Claude\Logs\mcp*.log` | `C:\Users\steve\AppData\Roaming\Claude\Logs\mcp*.log` |

## Usage

### Basic Scan
```bash
python windows_scan.py
```

This will:
- Scan all 17 locations
- Display detailed results with file sizes, modification dates, and item counts
- Show a summary with detection rate

### Export to JSON
```bash
python windows_scan.py --json
# or
python windows_scan.py -j
```

This will:
- Perform the scan
- Display results to console
- Export results to `scan_results.json`

### Quiet Mode
```bash
python windows_scan.py --quiet
# or
python windows_scan.py -q
```

This will suppress all output (useful for automation).

## Sample Output

```
================================================================================
COMPREHENSIVE CLAUDE CODE & DESKTOP PATH SCAN
================================================================================

================================================================================
🔧 WINDOWS ENVIRONMENT VARIABLE MAPPINGS
================================================================================
%USERPROFILE%        → C:\Users\steve
%APPDATA%            → C:\Users\steve\AppData\Roaming
%ProgramData%        → C:\ProgramData

================================================================================
📂 SETTINGS FILES
================================================================================

✅ FOUND - User Settings
  Path: C:\Users\steve\.claude\settings.json
  Type: file
  Size: 78 B
  Modified: 2025-11-01 13:04:13

❌ NOT FOUND - Project Settings (Shared)
  Path: .claude\settings.json

...

================================================================================
📊 SUMMARY
================================================================================
Total locations scanned: 17
Found: 7
Not found: 10
Detection rate: 41.2%
```

**Note:** The scanner now displays the environment variable mappings at the top of the output, showing exactly what each placeholder resolves to on your system.

## Comparison with Original `server.py`

### Original `server.py` (lines 19-47)
**Scans 2 locations:**
- `~/.claude.json` (Claude Code)
- Platform-specific Claude Desktop config

### New `windows_scan.py`
**Scans 17 locations:**
- All original locations PLUS:
- New Claude Code structure (`~/.claude/settings.json`)
- Enterprise managed settings
- Memory files (CLAUDE.md)
- Subagents directories
- Slash commands directories
- Project-level MCP configs
- Log directories with MCP log enumeration

## Key Features

1. **Comprehensive Coverage**: Scans all documented Windows paths from the official Claude Code docs
2. **Detailed Information**: Shows file sizes, modification dates, item counts for directories
3. **MCP Log Detection**: Lists all MCP server log files
4. **JSON Export**: Machine-readable output for automation
5. **Cross-platform Safe**: Detects OS and warns if not Windows
6. **Non-destructive**: Read-only operations, no modifications
7. **UTF-8 Support**: Handles Windows console encoding properly

## Requirements

- Python 3.7+
- No external dependencies (uses only stdlib)

## Source Documentation

Based on the transcript in `windowsPaths.txt` which documents the official Windows paths for:
- Claude Code settings and configurations
- Claude Desktop configurations
- MCP server configurations
- Slash commands
- Subagents
- Memory files
- Logs

## Results on This System

From the latest scan:
- **Total locations scanned**: 17
- **Found**: 7 (41.2%)
- **Not found**: 10 (58.8%)

### Found on This System:
1. User Settings (`C:\Users\steve\.claude\settings.json`) - 78 B
2. Project Settings Local (`.claude\settings.local.json`) - 139 B
3. Original Claude Code Config (`C:\Users\steve\.claude.json`) - 41.35 KB
4. Claude Desktop Config - 1.13 KB
5. MCP Logs Directory - 17 log files

### Not Found:
- Project Settings (Shared)
- Enterprise Managed Settings
- All Memory Files (CLAUDE.md)
- Subagent directories
- Slash command directories
- Project MCP config (.mcp.json)

This indicates a standard user installation without enterprise management or certain advanced features activated.
