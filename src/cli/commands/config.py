"""
Configuration management commands.

Commands for viewing, modifying, and managing application configuration.
"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from src.cli.formatters import print_error, print_success, print_warning
from src.cli.progress import show_status
from src.cli.utils import confirm_action, handle_cli_error
from src.core.config import get_settings, reload_settings
from src.utils.logger import get_logger
from src.utils.validators import validate_configuration

app = typer.Typer(help="Configuration management commands")
console = Console()
logger = get_logger(__name__)


@app.command("show")
def show_config(
    environment: Optional[str] = typer.Option(
        None,
        "--environment",
        "-e",
        help="Environment to show (current if not specified)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show all configuration values including sensitive",
    ),
) -> None:
    """Show current configuration settings."""

    try:
        settings = get_settings()

        if environment and environment != settings.environment:
            console.print(
                f"\n[yellow]Note: Showing {environment} config, "
                f"but current environment is {settings.environment}[/yellow]\n"
            )

        # Create configuration display
        table = Table(
            show_header=True,
            header_style="bold cyan",
            box=box.ROUNDED,
            title=f"Configuration ({settings.environment})",
        )
        table.add_column("Setting", style="white")
        table.add_column("Value", style="cyan")

        # Core settings
        table.add_row("Environment", settings.environment)
        table.add_row("Debug Mode", str(settings.debug))

        # Database settings
        db_url = settings.database_url
        if not verbose and ":" in db_url:
            # Mask sensitive parts
            db_url = db_url.split("://")[0] + "://***"
        table.add_row("Database URL", db_url)

        # API settings
        table.add_row("API Host", settings.api_host)
        table.add_row("API Port", str(settings.api_port))

        # Logging settings
        table.add_row("Log Level", settings.log_level)
        table.add_row("Log File", str(settings.log_file))
        table.add_row("Log Max Size", f"{settings.log_max_bytes:,} bytes")
        table.add_row("Log Backups", str(settings.log_backup_count))

        console.print("\n")
        console.print(table)
        console.print()

        if not verbose:
            console.print(
                "[dim]Use --verbose to show all values including sensitive data[/dim]\n"
            )

    except Exception as e:
        handle_cli_error(e, verbose=verbose)


@app.command("get")
def get_value(
    key: str = typer.Argument(..., help="Configuration key to get (e.g., 'api.host')"),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed information",
    ),
) -> None:
    """Get a specific configuration value."""

    try:
        settings = get_settings()

        # Use dot notation to access nested values
        keys = key.split(".")
        value = settings

        for k in keys:
            if hasattr(value, k):
                value = getattr(value, k)
            else:
                print_error(f"Configuration key not found: {key}")
                return

        console.print(f"\n[bold]{key}:[/bold] {value}\n")

    except Exception as e:
        handle_cli_error(e, verbose=verbose)


@app.command("set")
def set_value(
    key: str = typer.Argument(..., help="Configuration key to set (e.g., 'log_level')"),
    value: str = typer.Argument(..., help="Value to set"),
    persist: bool = typer.Option(
        True,
        "--persist/--no-persist",
        help="Persist to configuration file",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed information",
    ),
) -> None:
    """Set a configuration value."""

    try:
        settings = get_settings()

        # Check if key exists
        if not hasattr(settings, key):
            print_error(
                f"Configuration key not found: {key}",
                f"Use 'claude-config config show' to see available keys"
            )
            return

        # Get old value
        old_value = getattr(settings, key)

        # Show what will change
        console.print(f"\n[bold]Configuration Change:[/bold]")
        console.print(f"  Key: {key}")
        console.print(f"  Old value: [red]{old_value}[/red]")
        console.print(f"  New value: [green]{value}[/green]")
        console.print()

        if not confirm_action(
            "Apply this change?",
            default=False
        ):
            console.print("\n[yellow]Change cancelled[/yellow]\n")
            return

        # Set value (would need to implement actual setting logic)
        print_warning(
            "Configuration modification is under development",
            "This is a preview. Full implementation will persist changes to config files."
        )

        if persist:
            console.print("\n[dim]Changes will be persisted to configuration file[/dim]\n")
        else:
            console.print("\n[dim]Changes are temporary (current session only)[/dim]\n")

    except Exception as e:
        handle_cli_error(e, verbose=verbose)


@app.command("validate")
def validate_config(
    config_file: Optional[Path] = typer.Option(
        None,
        "--file",
        "-f",
        help="Configuration file to validate (validates current if not specified)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed validation information",
    ),
) -> None:
    """Validate configuration file or current configuration."""

    try:
        if config_file:
            # Validate specific file
            if not config_file.exists():
                print_error(f"Configuration file not found: {config_file}")
                return

            with show_status("Validating configuration file..."):
                import yaml
                with open(config_file, "r", encoding="utf-8") as f:
                    config_data = yaml.safe_load(f)

            # Validate using validator from Phase 3
            result = validate_configuration(
                config_data,
                required_fields=[
                    "environment",
                    "database.url",
                    "api.host",
                    "api.port",
                    "logging.level",
                ]
            )

            if result.is_valid:
                print_success(
                    f"Configuration is valid: {config_file}",
                    f"All required fields present and valid"
                )
            else:
                print_error(
                    "Configuration validation failed",
                    "\n".join(f"  • {error}" for error in result.get_error_messages())
                )

        else:
            # Validate current configuration
            with show_status("Validating current configuration..."):
                settings = get_settings()
                config_dict = settings.model_dump()

            result = validate_configuration(
                config_dict,
                required_fields=[
                    "environment",
                    "database_url",
                    "api_host",
                    "api_port",
                    "log_level",
                ]
            )

            if result.is_valid:
                print_success(
                    "Current configuration is valid",
                    f"Environment: {settings.environment}"
                )
            else:
                print_error(
                    "Current configuration has issues",
                    "\n".join(f"  • {error}" for error in result.get_error_messages())
                )

    except Exception as e:
        handle_cli_error(e, verbose=verbose)


@app.command("init")
def init_wizard(
    output: Path = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file for configuration (default: config/{environment}.yaml)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed information",
    ),
) -> None:
    """Interactive configuration wizard to create a new configuration."""

    try:
        console.print("\n[bold cyan]Configuration Wizard[/bold cyan]\n")
        console.print("Create a new configuration by answering a few questions.\n")

        # Environment
        environment = typer.prompt(
            "Environment (development/production/testing)",
            default="development"
        )

        # Validate environment
        if environment not in ["development", "production", "testing"]:
            print_error(f"Invalid environment: {environment}")
            return

        # Database
        console.print("\n[bold]Database Configuration:[/bold]")
        db_path = typer.prompt(
            "  Database path",
            default="data/claude_config.db"
        )
        database_url = f"sqlite+aiosqlite:///{db_path}"

        # API
        console.print("\n[bold]API Configuration:[/bold]")
        api_host = typer.prompt("  API host", default="localhost")
        api_port = typer.prompt("  API port", default=8765, type=int)

        # Logging
        console.print("\n[bold]Logging Configuration:[/bold]")
        log_level = typer.prompt(
            "  Log level (DEBUG/INFO/WARNING/ERROR)",
            default="INFO"
        )

        # Build configuration
        config = {
            "environment": environment,
            "debug": environment == "development",
            "database": {
                "url": database_url,
            },
            "api": {
                "host": api_host,
                "port": api_port,
            },
            "logging": {
                "level": log_level.upper(),
                "file": f"logs/{environment}.log",
                "max_bytes": 10485760,
                "backup_count": 5,
            },
        }

        # Show summary
        console.print("\n[bold]Configuration Summary:[/bold]\n")
        import yaml
        console.print(Panel(
            yaml.dump(config, default_flow_style=False, sort_keys=False),
            title="Configuration",
            border_style="cyan",
        ))

        if not confirm_action("\nSave this configuration?", default=True):
            console.print("\n[yellow]Configuration not saved[/yellow]\n")
            return

        # Determine output file
        if output is None:
            output = Path(f"config/{environment}.yaml")

        # Create directory if needed
        output.parent.mkdir(parents=True, exist_ok=True)

        # Save configuration
        with open(output, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        print_success(
            "Configuration created successfully",
            f"Saved to: {output}\n\n"
            f"Set CLAUDE_CONFIG_ENV={environment} to use this configuration"
        )

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Wizard cancelled[/yellow]\n")
    except Exception as e:
        handle_cli_error(e, verbose=verbose)


if __name__ == "__main__":
    app()

