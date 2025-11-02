# Path Handling Summary

## Overview

This document clarifies how Windows paths are handled throughout the scanner, distinguishing between placeholder notation and fully qualified paths.

## Key Concepts

### 1. Placeholder Notation (Documentation)

Used in documentation and the source transcript ([windowsPaths.txt](windowsPaths.txt)) for portability:

- `%USERPROFILE%` - User profile directory
- `%APPDATA%` - Application data directory
- `%ProgramData%` - Program data for all users
- `{current_dir}` - Current working directory (relative paths)

**Example:**
```
%USERPROFILE%\.claude\settings.json
%APPDATA%\Claude\claude_desktop_config.json
```

### 2. Fully Qualified Paths (Runtime)

Used in scanner output and results - actual paths on your Windows system:

- `C:\Users\steve` - Resolved from %USERPROFILE%
- `C:\Users\steve\AppData\Roaming` - Resolved from %APPDATA%
- `C:\ProgramData` - Resolved from %ProgramData%
- `C:\myClaude\tooling\claude-config-editor` - Resolved from relative paths

**Example:**
```
C:\Users\steve\.claude\settings.json
C:\Users\steve\AppData\Roaming\Claude\claude_desktop_config.json
```

## How the Scanner Works

### Step 1: Environment Variable Expansion

The scanner automatically expands Windows environment variables to fully qualified paths:

```python
# Code from windows_scan.py (lines 63-69)
# Expand Windows environment variables to fully qualified paths
# %USERPROFILE% → C:\Users\steve (example)
# %APPDATA% → C:\Users\steve\AppData\Roaming (example)
# %ProgramData% → C:\ProgramData (example)
userprofile = Path(os.path.expandvars('%USERPROFILE%'))
appdata = Path(os.path.expandvars('%APPDATA%'))
programdata = Path(os.path.expandvars('%ProgramData%'))
```

### Step 2: Display Mappings

The scanner shows you the actual mappings at the top of output:

```
================================================================================
🔧 WINDOWS ENVIRONMENT VARIABLE MAPPINGS
================================================================================
%USERPROFILE%        → C:\Users\steve
%APPDATA%            → C:\Users\steve\AppData\Roaming
%ProgramData%        → C:\ProgramData
```

### Step 3: Scan with Fully Qualified Paths

All scanned paths are displayed as fully qualified Windows paths:

```
✅ FOUND - User Settings
  Path: C:\Users\steve\.claude\settings.json
  Type: file
  Size: 78 B
  Modified: 2025-11-01 13:04:13
```

### Step 4: Export to JSON

JSON export includes both mappings and fully qualified paths:

```json
{
    "_env_vars": {
        "%USERPROFILE%": "C:\\Users\\steve",
        "%APPDATA%": "C:\\Users\\steve\\AppData\\Roaming",
        "%ProgramData%": "C:\\ProgramData"
    },
    "Settings Files": {
        "User Settings": {
            "path": "C:\\Users\\steve\\.claude\\settings.json",
            "info": {
                "exists": true,
                "size": 78,
                "size_formatted": "78 B",
                "modified": "2025-11-01 13:04:13",
                "type": "file"
            }
        }
    }
}
```

## Documentation Standards

### In README and Docs

Use **placeholder notation** with examples:

| Path Template | Example Resolved Path |
|--------------|----------------------|
| `%USERPROFILE%\.claude\settings.json` | `C:\Users\steve\.claude\settings.json` |

### In Code Comments

Use **both** for clarity:

```python
# %USERPROFILE% → C:\Users\steve (example)
userprofile = Path(os.path.expandvars('%USERPROFILE%'))
```

### In Scanner Output

Always use **fully qualified paths**:

```
Path: C:\Users\steve\.claude\settings.json
```

## Why This Matters

1. **Portability**: Placeholder notation works across different Windows users
2. **Clarity**: Users see exactly where files are on their system
3. **Debugging**: Fully qualified paths make troubleshooting easier
4. **Documentation**: Consistent format across all docs

## Quick Reference

| Context | Format | Example |
|---------|--------|---------|
| Documentation | Placeholder | `%USERPROFILE%\.claude\settings.json` |
| Scanner Output | Fully Qualified | `C:\Users\steve\.claude\settings.json` |
| JSON Export | Fully Qualified | `C:\\Users\\steve\\.claude\\settings.json` |
| Error Messages | Fully Qualified | `C:\\Users\\steve\\.claude\\settings.json` |

## Environment Variables by OS

While this scanner is Windows-focused, here's how these paths work across platforms:

| Windows | macOS/Linux | Description |
|---------|-------------|-------------|
| `%USERPROFILE%` | `~` or `$HOME` | User home directory |
| `%APPDATA%` | `~/Library/Application Support` (macOS)<br>`~/.config` (Linux) | App data |
| `%ProgramData%` | `/Library/Application Support` (macOS)<br>`/etc` (Linux) | System-wide data |

## Testing Path Resolution

To check what your environment variables resolve to:

```bash
# PowerShell
echo $env:USERPROFILE
echo $env:APPDATA
echo $env:ProgramData

# Python
python -c "import os; print(os.path.expandvars('%USERPROFILE%'))"
python -c "import os; print(os.path.expandvars('%APPDATA%'))"
python -c "import os; print(os.path.expandvars('%ProgramData%'))"
```

## Summary

- **Documentation uses placeholders** (`%USERPROFILE%`) for portability
- **Scanner always shows fully qualified paths** (`C:\Users\steve\...`) for clarity
- **Mappings are displayed** at the start of scan output
- **JSON export includes both** mapping reference and fully qualified paths
- **No ambiguity** - you always know exactly which file the scanner is checking
