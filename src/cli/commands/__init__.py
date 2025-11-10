"""
Modular CLI commands for Claude Config Editor.

Organizes commands into logical modules for better maintainability.
"""

import typer

from src.cli.commands import config, database, export, import_cmd, serve, snapshot
from src.core.config import get_settings
from src.utils.logger import setup_logging

# Create main app
app = typer.Typer(
    name="claude-config",
    help="Version-controlled management for Claude Code and Claude Desktop configurations",
    add_completion=False,
    no_args_is_help=True,
)

# Add command modules
app.add_typer(snapshot.app, name="snapshot")
app.add_typer(database.app, name="db")
app.add_typer(export.app, name="export")
app.add_typer(import_cmd.app, name="import")
app.add_typer(config.app, name="config")
app.add_typer(serve.app, name="serve")


@app.callback()
def main_callback(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output (debug logging)",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Suppress all output except errors",
    ),
) -> None:
    """
    Claude Config Editor - Configuration management and version control.

    Manage Claude Code and Claude Desktop configurations with snapshot versioning,
    change tracking, and comprehensive configuration management.
    """
    settings = get_settings()

    # Determine log level
    if quiet:
        log_level = "ERROR"
    elif verbose:
        log_level = "DEBUG"
    else:
        log_level = settings.log_level

    # Setup logging
    setup_logging(
        log_level=log_level,
        log_file=settings.log_file,
        log_max_bytes=settings.log_max_bytes,
        log_backup_count=settings.log_backup_count,
    )


def get_app() -> typer.Typer:
    """Get the main CLI application."""
    return app


if __name__ == "__main__":
    app()
