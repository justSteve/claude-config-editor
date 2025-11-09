# Scanner Migration Guide

## Overview

This guide helps you migrate from the legacy standalone scanner (`windows_scan.py`) to the integrated scanner system (`src/core/scanner.py`).

## Why Migrate?

The integrated scanner offers several advantages:

1. **Database Storage**: Results stored in SQLite for historical tracking
2. **Change Detection**: Automatic comparison with previous scans
3. **Configuration-Based**: Path definitions in `config/paths.yaml` for easy customization
4. **Better Error Handling**: Comprehensive logging and error recovery
5. **Rich Output**: Beautiful terminal output with progress indicators
6. **Version Control**: Track configuration changes over time
7. **API Integration**: Results accessible via API and CLI commands

## Quick Migration

### Old Command

```bash
python windows_scan.py
python windows_scan.py --json
```

### New Command

```bash
# Create a snapshot (equivalent to running the old scanner)
python -m src.cli.commands snapshot create

# List recent snapshots
python -m src.cli.commands snapshot list

# Show detailed snapshot information
python -m src.cli.commands snapshot show <id>

# Export snapshot as JSON
python -m src.cli.commands snapshot report <id> --format json --output snapshot.json
```

## Feature Comparison

| Feature | Legacy (`windows_scan.py`) | Integrated (`src.core.scanner`) |
|---------|----------------------------|--------------------------------|
| Scan paths | ✅ | ✅ |
| JSON export | ✅ | ✅ (via reports) |
| Console output | ✅ | ✅ (enhanced with Rich) |
| Database storage | ❌ | ✅ |
| Change detection | ❌ | ✅ |
| Version control | ❌ | ✅ |
| MCP log enumeration | ✅ | ✅ |
| Configuration file | ❌ | ✅ (config/paths.yaml) |
| API access | ❌ | ✅ (coming in Phase 5) |
| Progress tracking | ❌ | ✅ |
| Async execution | ❌ | ✅ |

## Detailed Migration Steps

### Step 1: Install Dependencies

Ensure all dependencies are installed:

```bash
pip install -r requirements.txt
```

### Step 2: Initialize Database

The database will be automatically initialized on first run, but you can also do it manually:

```python
from src.core.database import init_database
from src.core.config import get_settings

settings = get_settings()
await init_database(settings.database_url)
```

### Step 3: Configure Paths

The integrated scanner uses `config/paths.yaml` for path definitions. You can customize which paths to scan by editing this file:

```yaml
paths:
  - category: "Settings Files"
    name: "User Settings"
    template: "%USERPROFILE%/.claude/settings.json"
    enabled: true  # Set to false to disable scanning this path
```

### Step 4: Create Your First Snapshot

```bash
python -m src.cli.commands snapshot create --notes "Initial snapshot"
```

This will:
1. Load path definitions from `config/paths.yaml`
2. Scan all enabled paths
3. Store results in the database
4. Detect if this is the first snapshot (baseline)
5. Display summary information

### Step 5: View Results

```bash
# List all snapshots
python -m src.cli.commands snapshot list

# View specific snapshot details
python -m src.cli.commands snapshot show 1 --paths

# Compare two snapshots
python -m src.cli.commands snapshot compare 2 --previous 1
```

### Step 6: Export Data

```bash
# Export as JSON
python -m src.cli.commands snapshot report 1 --format json --output snapshot.json

# Export as HTML
python -m src.cli.commands snapshot report 1 --format html --output snapshot.html
```

## Configuration Customization

### Adding Custom Paths

Edit `config/paths.yaml` to add your own paths:

```yaml
paths:
  # ... existing paths ...
  
  - category: "Custom Category"
    name: "My Custom Path"
    template: "%USERPROFILE%/my-custom-path.json"
    description: "My custom configuration file"
    enabled: true
```

### Disabling Paths

To stop scanning a specific path, set `enabled: false`:

```yaml
paths:
  - category: "Settings Files"
    name: "Enterprise Managed Settings"
    template: "%ProgramData%/ClaudeCode/managed-settings.json"
    enabled: false  # This path will be skipped
```

### Platform-Specific Paths

The configuration supports platform-specific environment variable mappings:

```yaml
platform_mappings:
  Windows:
    "%USERPROFILE%": "~"
    "%APPDATA%": "~/AppData/Roaming"
  
  Darwin:  # macOS
    "%USERPROFILE%": "~"
    "%APPDATA%": "~/Library/Application Support"
  
  Linux:
    "%USERPROFILE%": "~"
    "%APPDATA%": "~/.config"
```

## API Usage (Programmatic)

If you were using `windows_scan.py` programmatically, here's how to use the integrated scanner:

### Old Way

```python
from windows_scan import scan_windows_paths

results = scan_windows_paths()
print(f"Found {results['total_found']} paths")
```

### New Way

```python
import asyncio
from src.core.scanner import PathScanner
from src.core.database import init_database, get_db_manager
from src.core.config import get_settings

async def scan():
    # Initialize
    settings = get_settings()
    db = await init_database(settings.database_url)
    
    # Create scanner and snapshot
    async with db.get_session() as session:
        scanner = PathScanner(session)
        snapshot = await scanner.create_snapshot(
            trigger_type="api",
            triggered_by="my_script",
            notes="Automated scan"
        )
        
        print(f"Snapshot created: ID={snapshot.id}")
        print(f"Files found: {snapshot.files_found}")
        print(f"Directories found: {snapshot.directories_found}")
    
    # Cleanup
    await db.close()

# Run
asyncio.run(scan())
```

## Common Issues

### Issue: "Path configuration file not found"

**Solution**: Ensure `config/paths.yaml` exists in the project root. If you've moved files, update the path in your code or set the `config_path` parameter.

### Issue: "Database locked"

**Solution**: SQLite has limitations with concurrent access. Ensure you're not running multiple scans simultaneously. The integrated scanner uses WAL mode to improve concurrency.

### Issue: "Legacy scanner produces different results"

**Solution**: The integrated scanner may produce slightly different results because:
- It stores additional metadata (created/accessed times)
- It performs content hashing for deduplication
- It enumerates MCP logs differently (stored in annotations)

These differences are intentional improvements.

## Backward Compatibility

### JSON Export Format

If you rely on the legacy JSON export format, you can use the report generator to produce similar output:

```bash
python -m src.cli.commands snapshot report 1 --format json
```

The output structure is similar but enhanced with additional fields:
- `snapshot_id`: Unique identifier
- `snapshot_time`: When the scan was performed
- `snapshot_hash`: Content hash for change detection
- `changes`: Changes from previous snapshot

### Console Output

The new console output is more feature-rich but follows a similar structure. If you parse the console output, consider using JSON export instead.

## Timeline

- **Current**: Legacy scanner marked as deprecated
- **Next Release**: Integrated scanner is primary method
- **Future Release**: Legacy scanner will be removed

## Getting Help

If you encounter issues during migration:

1. Check this guide
2. Review `doc/scanner-comparison-analysis.md` for detailed feature comparisons
3. Check the issue tracker
4. Ask in the community discussions

## Example: Complete Migration Script

Here's a complete example showing how to migrate a script that used the legacy scanner:

```python
# OLD: windows_scan.py
import json
from windows_scan import scan_windows_paths, export_results_json

results = scan_windows_paths()
export_results_json(results, 'scan_results.json')
print(f"Scanned {results['total_scanned']} paths")

# NEW: integrated scanner
import asyncio
import json
from src.core.scanner import PathScanner
from src.core.database import init_database
from src.core.config import get_settings

async def new_scan():
    settings = get_settings()
    db = await init_database(settings.database_url)
    
    try:
        async with db.get_session() as session:
            scanner = PathScanner(session)
            snapshot = await scanner.create_snapshot(
                trigger_type="script",
                notes="Automated scan"
            )
            
            print(f"Snapshot ID: {snapshot.id}")
            print(f"Scanned {snapshot.total_locations} paths")
            print(f"Found {snapshot.files_found} files")
            
            # Export to JSON (similar to legacy format)
            export_data = {
                "snapshot_id": snapshot.id,
                "snapshot_time": snapshot.snapshot_time.isoformat(),
                "total_locations": snapshot.total_locations,
                "files_found": snapshot.files_found,
                "directories_found": snapshot.directories_found,
            }
            
            with open('scan_results.json', 'w') as f:
                json.dump(export_data, f, indent=2)
    
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(new_scan())
```

## Benefits of Migration

After migrating, you'll be able to:

1. **Track Changes Over Time**: See what changed between scans
2. **Query History**: Search through historical scan data
3. **Generate Reports**: Create detailed reports comparing snapshots
4. **Automate Workflows**: Use the API to integrate with other tools
5. **Customize Paths**: Easily add/remove paths via configuration
6. **Better Performance**: Async scanning for faster results
7. **Rich UI**: Beautiful terminal output with progress indicators

Start migrating today to take advantage of these benefits!

