#!/usr/bin/env python3
r"""
Comprehensive Windows Path Scanner for Claude Code & Claude Desktop
Replicates and extends the original scan from server.py to cover all documented locations

⚠️ DEPRECATED: This standalone scanner is being phased out in favor of the integrated
scanner in src/core/scanner.py which uses config/paths.yaml for path definitions
and stores results in the database for version control.

For new use cases, please use:
    python -m src.cli.commands snapshot create

This legacy scanner will be removed in a future version.

---

This scanner uses Windows environment variables that are automatically expanded:
- %USERPROFILE% → C:\Users\{username}
- %APPDATA% → C:\Users\{username}\AppData\Roaming
- %ProgramData% → C:\ProgramData

All scanned paths are displayed as fully qualified Windows paths (e.g., C:\Users\steve\...)
"""

import os
import platform
from pathlib import Path
import json
from datetime import datetime


def format_size(size_bytes):
    """Format bytes to human-readable size"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


def get_file_info(path):
    """Get detailed file information"""
    try:
        stat = path.stat()
        return {
            'exists': True,
            'size': stat.st_size,
            'size_formatted': format_size(stat.st_size),
            'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
            'type': 'directory' if path.is_dir() else 'file'
        }
    except Exception as e:
        return {
            'exists': False,
            'error': str(e)
        }


def count_items_in_dir(path):
    """Count items in a directory"""
    try:
        if not path.is_dir():
            return 0
        items = list(path.iterdir())
        return len(items)
    except Exception:
        return 0


def scan_windows_paths():
    """Scan all documented Windows paths for Claude Code and Claude Desktop"""

    if platform.system() != 'Windows':
        print(
            f"⚠️  This scanner is designed for Windows. Current OS: {platform.system()}")
        print("   Paths will be adapted but may not match Windows structure.\n")

    # Expand Windows environment variables to fully qualified paths
    # %USERPROFILE% → C:\Users\steve (example)
    # %APPDATA% → C:\Users\steve\AppData\Roaming (example)
    # %ProgramData% → C:\ProgramData (example)
    userprofile = Path(os.path.expandvars('%USERPROFILE%'))
    appdata = Path(os.path.expandvars('%APPDATA%'))
    programdata = Path(os.path.expandvars('%ProgramData%'))

    results = {}

    # Store environment variable mappings for reference
    results['_env_vars'] = {
        '%USERPROFILE%': str(userprofile),
        '%APPDATA%': str(appdata),
        '%ProgramData%': str(programdata)
    }

    # ==========================================
    # SETTINGS FILES
    # ==========================================
    results['Settings Files'] = {}

    settings_paths = {
        'User Settings': userprofile / '.claude' / 'settings.json',
        'Project Settings (Shared)': Path('.claude') / 'settings.json',
        'Project Settings (Local)': Path('.claude') / 'settings.local.json',
        'Enterprise Managed Settings': programdata / 'ClaudeCode' / 'managed-settings.json',
        'Original Claude Code Config': userprofile / '.claude.json'  # Original from server.py
    }

    for name, path in settings_paths.items():
        results['Settings Files'][name] = {
            'path': str(path),
            'info': get_file_info(path)
        }

    # ==========================================
    # MEMORY FILES (CLAUDE.md)
    # ==========================================
    results['Memory Files (CLAUDE.md)'] = {}

    memory_paths = {
        'User Memory': userprofile / '.claude' / 'CLAUDE.md',
        'Project Memory': Path('.') / 'CLAUDE.md',
        'Enterprise Memory': programdata / 'ClaudeCode' / 'CLAUDE.md'
    }

    for name, path in memory_paths.items():
        results['Memory Files (CLAUDE.md)'][name] = {
            'path': str(path),
            'info': get_file_info(path)
        }

    # ==========================================
    # SUBAGENTS
    # ==========================================
    results['Subagents'] = {}

    subagent_paths = {
        'User Subagents': userprofile / '.claude' / 'agents',
        'Project Subagents': Path('.claude') / 'agents'
    }

    for name, path in subagent_paths.items():
        info = get_file_info(path)
        if info['exists'] and info['type'] == 'directory':
            info['item_count'] = count_items_in_dir(path)
        results['Subagents'][name] = {
            'path': str(path),
            'info': info
        }

    # ==========================================
    # CLAUDE DESKTOP CONFIG
    # ==========================================
    results['Claude Desktop'] = {}

    desktop_config = appdata / 'Claude' / 'claude_desktop_config.json'
    results['Claude Desktop']['Config File'] = {
        'path': str(desktop_config),
        'info': get_file_info(desktop_config)
    }

    # ==========================================
    # SLASH COMMANDS
    # ==========================================
    results['Slash Commands'] = {}

    command_paths = {
        'Project Commands': Path('.claude') / 'commands',
        'Personal Commands': userprofile / '.claude' / 'commands'
    }

    for name, path in command_paths.items():
        info = get_file_info(path)
        if info['exists'] and info['type'] == 'directory':
            info['item_count'] = count_items_in_dir(path)
        results['Slash Commands'][name] = {
            'path': str(path),
            'info': info
        }

    # ==========================================
    # MCP SERVERS
    # ==========================================
    results['MCP Servers'] = {}

    mcp_paths = {
        'User Settings (Local Scope)': userprofile / '.claude' / 'settings.json',
        'Project Config': Path('.mcp.json'),
        'Claude Desktop MCP Config': appdata / 'Claude' / 'claude_desktop_config.json'
    }

    for name, path in mcp_paths.items():
        results['MCP Servers'][name] = {
            'path': str(path),
            'info': get_file_info(path)
        }

    # ==========================================
    # LOGS
    # ==========================================
    results['Logs'] = {}

    logs_dir = appdata / 'Claude' / 'Logs'
    logs_info = get_file_info(logs_dir)

    if logs_info['exists'] and logs_info['type'] == 'directory':
        try:
            # Find all mcp*.log files
            mcp_logs = list(logs_dir.glob('mcp*.log'))
            logs_info['mcp_log_count'] = len(mcp_logs)
            logs_info['mcp_logs'] = [str(log.name)
                                     for log in mcp_logs[:10]]  # First 10
            if len(mcp_logs) > 10:
                logs_info['mcp_logs'].append(
                    f"... and {len(mcp_logs) - 10} more")
        except Exception as e:
            logs_info['error'] = str(e)

    results['Logs']['MCP Logs Directory'] = {
        'path': str(logs_dir),
        'info': logs_info
    }

    return results


def print_results(results):
    """Print scan results in organized format"""

    print("=" * 80)
    print("COMPREHENSIVE CLAUDE CODE & DESKTOP PATH SCAN")
    print("=" * 80)
    print()

    # Display environment variable mappings first
    if '_env_vars' in results:
        print("=" * 80)
        print("🔧 WINDOWS ENVIRONMENT VARIABLE MAPPINGS")
        print("=" * 80)
        for placeholder, actual in results['_env_vars'].items():
            print(f"{placeholder:20} → {actual}")
        print()

    total_found = 0
    total_scanned = 0

    for category, items in results.items():
        # Skip the internal env_vars key
        if category == '_env_vars':
            continue
        print(f"\n{'=' * 80}")
        print(f"📂 {category.upper()}")
        print('=' * 80)

        for name, data in items.items():
            total_scanned += 1
            path = data['path']
            info = data['info']

            exists = info.get('exists', False)
            if exists:
                total_found += 1

            status = "✅ FOUND" if exists else "❌ NOT FOUND"
            print(f"\n{status} - {name}")
            print(f"  Path: {path}")

            if exists:
                file_type = info.get('type', 'unknown')
                print(f"  Type: {file_type}")

                if file_type == 'file':
                    print(f"  Size: {info.get('size_formatted', 'N/A')}")
                    print(f"  Modified: {info.get('modified', 'N/A')}")
                elif file_type == 'directory':
                    item_count = info.get('item_count')
                    if item_count is not None:
                        print(f"  Items: {item_count}")

                    # Special handling for logs
                    if 'mcp_log_count' in info:
                        print(f"  MCP Logs: {info['mcp_log_count']}")
                        if info.get('mcp_logs'):
                            print(f"  Log Files:")
                            for log in info['mcp_logs']:
                                print(f"    - {log}")
            else:
                error = info.get('error')
                if error:
                    print(f"  Error: {error}")

    # Summary
    print(f"\n{'=' * 80}")
    print("📊 SUMMARY")
    print('=' * 80)
    print(f"Total locations scanned: {total_scanned}")
    print(f"Found: {total_found}")
    print(f"Not found: {total_scanned - total_found}")
    print(f"Detection rate: {(total_found / total_scanned * 100):.1f}%")
    print()


def export_results_json(results, output_file='scan_results.json'):
    """Export results to JSON file"""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"✅ Results exported to: {output_file}")
        return True
    except Exception as e:
        print(f"❌ Failed to export results: {e}")
        return False


def main():
    """Main function"""
    import sys

    # Set UTF-8 encoding for Windows console
    if platform.system() == 'Windows':
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')

    # Check for command-line arguments
    export_json = '--json' in sys.argv or '-j' in sys.argv
    quiet = '--quiet' in sys.argv or '-q' in sys.argv

    if not quiet:
        # Show deprecation warning
        print("\n" + "=" * 80)
        print("⚠️  DEPRECATION WARNING")
        print("=" * 80)
        print("This standalone scanner (windows_scan.py) is deprecated and will be removed")
        print("in a future version. Please use the integrated scanner instead:")
        print("")
        print("  python -m src.cli.commands snapshot create")
        print("")
        print("The integrated scanner offers:")
        print("  • Database storage for version control")
        print("  • Change detection between scans")
        print("  • Configuration-based path definitions (config/paths.yaml)")
        print("  • Better error handling and logging")
        print("  • Rich terminal output")
        print("=" * 80)
        print("")

        print("\n🔍 Starting comprehensive Windows path scan...")
        print(f"📅 Scan time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

    # Perform scan
    results = scan_windows_paths()

    # Print results
    if not quiet:
        print_results(results)

    # Export if requested
    if export_json:
        export_results_json(results)

    if not quiet:
        print("\n" + "=" * 80)
        print("SCAN COMPLETE")
        print("=" * 80)
        print("\n💡 Tip: Use '--json' or '-j' flag to export results to JSON")
        print("   Example: python windows_scan.py --json")


if __name__ == '__main__':
    main()
