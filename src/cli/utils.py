"""
Shared CLI utilities.

Common functions used across CLI commands.
"""

import sys
from typing import Any, Callable, Optional

import typer
from rich.console import Console

from src.core.config import get_settings
from src.core.database import close_database, get_db_manager, init_database
from src.utils.logger import get_logger, setup_logging

console = Console()
logger = get_logger(__name__)


async def get_initialized_database():
    """
    Get an initialized database manager.

    Returns:
        DatabaseManager instance
    """
    settings = get_settings()
    db = await init_database(settings.database_url, echo=False)
    return db


def setup_cli_logging(verbose: bool = False, quiet: bool = False):
    """
    Setup logging for CLI operations.

    Args:
        verbose: Enable debug logging
        quiet: Disable all logging except errors
    """
    settings = get_settings()

    if quiet:
        log_level = "ERROR"
    elif verbose:
        log_level = "DEBUG"
    else:
        log_level = settings.log_level

    setup_logging(
        log_level=log_level,
        log_file=settings.log_file,
        log_max_bytes=settings.log_max_bytes,
        log_backup_count=settings.log_backup_count,
    )


def handle_cli_error(error: Exception, verbose: bool = False):
    """
    Handle CLI errors with appropriate formatting.

    Args:
        error: The exception that occurred
        verbose: Whether to show full traceback
    """
    error_type = type(error).__name__
    error_message = str(error)

    console.print(f"\n[bold red]✗ Error:[/bold red] {error_message}\n")

    if verbose:
        console.print_exception(show_locals=True)
        logger.error(
            f"CLI error: {error_type}: {error_message}", exc_info=True)
    else:
        console.print(
            "[dim]Use --verbose flag for detailed error information.[/dim]\n"
        )
        logger.error(f"CLI error: {error_type}: {error_message}")

    sys.exit(1)


def confirm_action(message: str, default: bool = False) -> bool:
    """
    Ask user to confirm an action.

    Args:
        message: Confirmation message
        default: Default response if user just presses Enter

    Returns:
        True if user confirms, False otherwise
    """
    default_text = "[Y/n]" if default else "[y/N]"
    response = typer.confirm(f"{message} {default_text}", default=default)
    return response


def validate_snapshot_id(snapshot_id: int) -> bool:
    """
    Validate that a snapshot ID is positive.

    Args:
        snapshot_id: Snapshot ID to validate

    Returns:
        True if valid

    Raises:
        typer.BadParameter if invalid
    """
    if snapshot_id <= 0:
        raise typer.BadParameter("Snapshot ID must be a positive integer")
    return True


def format_cli_output(data: Any, format_type: str = "table") -> str:
    """
    Format data for CLI output.

    Args:
        data: Data to format
        format_type: Output format (table, json, yaml)

    Returns:
        Formatted string
    """
    if format_type == "json":
        import json
        return json.dumps(data, indent=2, default=str)

    elif format_type == "yaml":
        import yaml
        return yaml.dump(data, default_flow_style=False)

    else:
        # Default to string representation
        return str(data)


class AsyncTyper(typer.Typer):
    """
    Custom Typer class that supports async commands.

    Usage:
        app = AsyncTyper()

        @app.command()
        async def my_command():
            await some_async_operation()
    """

    def command(self, *args, **kwargs) -> Callable:
        """Wrap command to support async functions."""
        def decorator(func: Callable) -> Callable:
            # Check if function is async
            import asyncio
            import inspect

            if inspect.iscoroutinefunction(func):
                # Wrap async function
                def sync_wrapper(*func_args, **func_kwargs):
                    return asyncio.run(func(*func_args, **func_kwargs))

                sync_wrapper.__name__ = func.__name__
                sync_wrapper.__doc__ = func.__doc__
                return super(AsyncTyper, self).command(*args, **kwargs)(sync_wrapper)
            else:
                # Regular sync function
                return super(AsyncTyper, self).command(*args, **kwargs)(func)

        return decorator


def get_exit_code(success: bool) -> int:
    """
    Get appropriate exit code for scripting.

    Args:
        success: Whether operation was successful

    Returns:
        0 for success, 1 for failure
    """
    return 0 if success else 1
