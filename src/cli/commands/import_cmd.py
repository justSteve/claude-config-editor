"""
Import commands for snapshots and configuration.

Commands for importing snapshots and configurations from exported files.
Note: Named import_cmd.py to avoid conflict with Python's 'import' keyword.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from src.cli.formatters import format_size, print_error, print_success, print_warning
from src.cli.progress import ExportProgress, show_status
from src.cli.utils import confirm_action, get_initialized_database, handle_cli_error
from src.core.config import get_settings, reload_settings
from src.core.database import close_database
from src.utils.logger import get_logger
from src.utils.validators import validate_json_data, validate_snapshot_data

app = typer.Typer(help="Import commands for data restoration")
console = Console()
logger = get_logger(__name__)


@app.command("snapshot")
def import_snapshot(
    input_file: Path = typer.Argument(..., help="Input file to import from"),
    format: str = typer.Option(
        None,
        "--format",
        "-f",
        help="Input format: json, yaml (auto-detected if not specified)",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Validate without importing",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Skip confirmation prompt",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed import information",
    ),
) -> None:
    """Import a snapshot from JSON or YAML file."""

    # Check if file exists
    if not input_file.exists():
        print_error(f"Input file not found: {input_file}")
        return

    # Auto-detect format if not specified
    if format is None:
        if input_file.suffix in [".json", ".gz"]:
            format = "json"
        elif input_file.suffix in [".yaml", ".yml"]:
            format = "yaml"
        else:
            print_error(
                f"Cannot auto-detect format from extension: {input_file.suffix}. "
                "Please specify --format json or --format yaml"
            )
            return

    # Validate format
    valid_formats = ["json", "yaml"]
    if format not in valid_formats:
        print_error(
            f"Invalid format: {format}. Must be one of: {', '.join(valid_formats)}")
        return

    async def _import() -> None:
        try:
            file_size = input_file.stat().st_size

            if verbose:
                console.print(f"\n[cyan]Importing snapshot...[/cyan]")
                console.print(f"  File: {input_file}")
                console.print(f"  Size: {format_size(file_size)}")
                console.print(f"  Format: {format}")
                console.print()

            # Read and parse file
            with show_status("Reading import file..."):
                data = await _read_import_file(input_file, format)

            # Validate data structure
            with show_status("Validating data..."):
                validation_errors = await _validate_snapshot_import(data)

            if validation_errors:
                print_error(
                    "Validation failed",
                    "\n".join(f"  • {error}" for error in validation_errors)
                )
                return

            # Show what will be imported
            snapshot_data = data.get("snapshot", {})
            paths_data = data.get("paths", [])

            console.print("\n[bold]Import Summary:[/bold]")
            console.print(f"  Snapshot ID: {snapshot_data.get('id', 'N/A')}")
            console.print(
                f"  Snapshot Time: {snapshot_data.get('snapshot_time', 'N/A')}")
            console.print(f"  Files: {snapshot_data.get('files_found', 0):,}")
            console.print(f"  Paths: {len(paths_data):,}")
            console.print()

            # Dry run mode
            if dry_run:
                print_success(
                    "Validation successful (dry-run mode)",
                    "Import was not performed. Remove --dry-run to import."
                )
                return

            # Confirm import
            if not force:
                if not confirm_action(
                    "This will import the snapshot into the database. Continue?",
                    default=False
                ):
                    console.print("\n[yellow]Import cancelled[/yellow]\n")
                    return

            # Perform import
            db = await get_initialized_database()

            try:
                async with db.get_session() as session:
                    with ExportProgress(
                        total_items=len(paths_data) + 1,
                        operation="Importing"
                    ) as progress:
                        # Import logic would go here
                        # This is a placeholder - full implementation would:
                        # 1. Create snapshot record
                        # 2. Import paths
                        # 3. Import content if included
                        # 4. Create relationships

                        await asyncio.sleep(0.1)  # Placeholder
                        progress.update(advance=len(paths_data) + 1)

                        print_warning(
                            "Import functionality is under development",
                            "This is a preview. Full import will be implemented in the next update."
                        )

            finally:
                await close_database()

        except Exception as e:
            handle_cli_error(e, verbose=verbose)

    asyncio.run(_import())


async def _read_import_file(file_path: Path, format: str) -> dict:
    """Read and parse import file."""
    if format == "json":
        # Handle gzipped files
        if file_path.suffix == ".gz":
            import gzip
            with gzip.open(file_path, "rt", encoding="utf-8") as f:
                data = json.load(f)
        else:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

    elif format == "yaml":
        import yaml
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

    return data


async def _validate_snapshot_import(data: dict) -> list[str]:
    """Validate imported snapshot data."""
    errors = []

    # Check version
    if "version" not in data:
        errors.append("Missing 'version' field")

    # Check snapshot data
    if "snapshot" not in data:
        errors.append("Missing 'snapshot' field")
    else:
        snapshot = data["snapshot"]

        # Use validator from Phase 3
        result = validate_snapshot_data(snapshot)
        if not result.is_valid:
            errors.extend(result.get_error_messages())

    # Check paths data
    if "paths" not in data:
        errors.append("Missing 'paths' field")
    elif not isinstance(data["paths"], list):
        errors.append("'paths' must be a list")

    return errors


@app.command("config")
def import_config(
    input_file: Path = typer.Argument(...,
                                      help="Configuration file to import"),
    validate_only: bool = typer.Option(
        False,
        "--validate",
        help="Validate without importing",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Skip confirmation prompt",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed information",
    ),
) -> None:
    """Import configuration from YAML file."""

    # Check if file exists
    if not input_file.exists():
        print_error(f"Configuration file not found: {input_file}")
        return

    try:
        file_size = input_file.stat().st_size

        if verbose:
            console.print(f"\n[cyan]Importing configuration...[/cyan]")
            console.print(f"  File: {input_file}")
            console.print(f"  Size: {format_size(file_size)}")
            console.print()

        # Read configuration file
        with show_status("Reading configuration file..."):
            import yaml
            with open(input_file, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)

        # Validate configuration
        with show_status("Validating configuration..."):
            from src.utils.validators import validate_configuration

            result = validate_configuration(
                config_data,
                required_fields=[
                    "environment",
                    "database.url",
                    "api.host",
                    "api.port",
                ]
            )

        if not result.is_valid:
            print_error(
                "Configuration validation failed",
                "\n".join(
                    f"  • {error}" for error in result.get_error_messages())
            )
            return

        # Show configuration summary
        console.print("\n[bold]Configuration Summary:[/bold]")
        console.print(
            f"  Environment: {config_data.get('environment', 'N/A')}")
        console.print(
            f"  Database URL: {config_data.get('database', {}).get('url', 'N/A')}")
        console.print(
            f"  API Host: {config_data.get('api', {}).get('host', 'N/A')}")
        console.print(
            f"  API Port: {config_data.get('api', {}).get('port', 'N/A')}")
        console.print()

        # Validate-only mode
        if validate_only:
            print_success(
                "Configuration is valid",
                "Import was not performed. Remove --validate to import."
            )
            return

        # Confirm import
        if not force:
            if not confirm_action(
                "This will update the current configuration. Continue?",
                default=False
            ):
                console.print("\n[yellow]Import cancelled[/yellow]\n")
                return

        # Save configuration
        with show_status("Saving configuration...", "Configuration imported successfully!"):
            # Determine output path based on environment
            env = config_data.get("environment", "development")
            output_path = Path(f"config/{env}.yaml")

            # Ensure config directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write configuration
            with open(output_path, "w", encoding="utf-8") as f:
                yaml.dump(config_data, f, default_flow_style=False,
                          sort_keys=False)

        print_success(
            "Configuration imported",
            f"Saved to: {output_path}\n\n"
            "⚠ Note: Restart the application for changes to take effect"
        )

        # Reload settings
        if verbose:
            console.print("\n[dim]Reloading settings...[/dim]")
            reload_settings()
            console.print("[dim]Settings reloaded[/dim]\n")

    except Exception as e:
        handle_cli_error(e, verbose=verbose)


if __name__ == "__main__":
    app()
