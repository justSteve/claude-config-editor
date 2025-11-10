# CLI Usage Documentation

## Running the CLI

Due to the editable installation and module path resolution, use one of these methods:

### Method 1: Using Python Module (Recommended)

From the project directory:

```bash
python -m src.cli.commands [COMMAND] [OPTIONS]
```

Examples:
```bash
python -m src.cli.commands --help
python -m src.cli.commands config init
python -m src.cli.commands snapshot create
python -m src.cli.commands snapshot list
```

### Method 2: Using the Installed Entry Point

First, ensure you're in the virtual environment, then:

```bash
claude-config [COMMAND] [OPTIONS]
```

**Note:** This method works best after activating the virtual environment:
```bash
# PowerShell
.\.venv\Scripts\Activate.ps1

# Or CMD
.venv\Scripts\activate.bat
```

### Method 3: Direct Python Invocation

```bash
python -c "from src.cli.commands import app; app()" [OPTIONS] [COMMAND]
```

## Project Structure

The CLI is implemented in a modular structure:

```
src/cli/
├── __init__.py              # Exports app from commands
├── __main__.py              # Module entry point
├── commands/                # Modular commands package
│   ├── __init__.py          # Main app definition
│   ├── __main__.py          # Package entry point
│   ├── config.py            # Configuration commands
│   ├── snapshot.py          # Snapshot commands
│   ├── database.py          # Database commands
│   ├── export.py            # Export commands
│   └── import_cmd.py        # Import commands
├── commands_legacy.py       # Legacy monolithic commands (deprecated)
├── formatters.py            # Output formatting utilities
├── progress.py              # Progress indicators
└── utils.py                 # CLI utilities
```

## Notes

- The old `commands.py` file was renamed to `commands_legacy.py` to avoid namespace conflicts with the new modular `commands/` package
- The entry point script has some compatibility issues with the virtual environment path resolution on Windows
- Using `python -m src.cli.commands` is the most reliable method for development
- Once deployed, the entry point should work correctly

## Troubleshooting

If you see `ModuleNotFoundError: No module named 'src'`:

1. Ensure you're running from the project directory
2. Use the `python -m` method
3. Or activate the virtual environment first and use the entry point script
