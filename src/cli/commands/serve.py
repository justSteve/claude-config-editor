"""
Serve command for starting the FastAPI API server.

Provides a CLI interface to start the Claude Config API server with
various configuration options for development and production use.
"""

import signal
import sys
import webbrowser
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
app = typer.Typer(help="Start the Claude Config API server")


def signal_handler(signum: int, frame) -> None:
    """Handle shutdown signals gracefully."""
    console.print("\n[yellow]Shutting down API server...[/yellow]")
    sys.exit(0)


@app.command()
def serve(
    host: str = typer.Option(
        "localhost",
        "--host",
        "-h",
        help="Host to bind the server to",
    ),
    port: int = typer.Option(
        8765,
        "--port",
        "-p",
        help="Port to bind the server to",
    ),
    reload: bool = typer.Option(
        False,
        "--reload",
        "-r",
        help="Enable auto-reload on code changes (development mode)",
    ),
    workers: Optional[int] = typer.Option(
        None,
        "--workers",
        "-w",
        help="Number of worker processes (production mode, not compatible with --reload)",
    ),
    log_level: str = typer.Option(
        "info",
        "--log-level",
        "-l",
        help="Logging level (debug, info, warning, error, critical)",
    ),
    open_browser: bool = typer.Option(
        False,
        "--open",
        "-o",
        help="Open browser to API documentation after starting",
    ),
) -> None:
    """
    Start the Claude Config API server.

    Examples:
        # Start server with defaults (localhost:8765)
        claude-config serve

        # Start with custom host and port
        claude-config serve --host 0.0.0.0 --port 8000

        # Development mode with auto-reload
        claude-config serve --reload

        # Production mode with multiple workers
        claude-config serve --workers 4

        # Open browser to docs after starting
        claude-config serve --open
    """
    # Validate options
    if reload and workers:
        console.print(
            "[red]Error: --reload and --workers cannot be used together[/red]"
        )
        console.print(
            "[yellow]Use --reload for development, --workers for production[/yellow]"
        )
        raise typer.Exit(code=1)

    # Validate log level
    valid_log_levels = ["debug", "info", "warning", "error", "critical"]
    log_level = log_level.lower()
    if log_level not in valid_log_levels:
        console.print(f"[red]Error: Invalid log level '{log_level}'[/red]")
        console.print(
            f"[yellow]Valid levels: {', '.join(valid_log_levels)}[/yellow]"
        )
        raise typer.Exit(code=1)

    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Display startup information
    _display_startup_info(host, port, reload, workers, log_level)

    # Build server URL
    server_url = f"http://{host}:{port}"
    docs_url = f"{server_url}/docs"

    # Open browser if requested
    if open_browser:
        console.print(f"\n[cyan]Opening browser to {docs_url}[/cyan]")
        try:
            webbrowser.open(docs_url)
        except Exception as e:
            console.print(f"[yellow]Could not open browser: {e}[/yellow]")

    # Start the server
    try:
        import uvicorn

        # Build uvicorn config
        uvicorn_config = {
            "app": "src.api.app:app",
            "host": host,
            "port": port,
            "log_level": log_level,
        }

        # Add reload or workers based on mode
        if reload:
            uvicorn_config["reload"] = True
            uvicorn_config["reload_dirs"] = ["src"]
        elif workers and workers > 1:
            uvicorn_config["workers"] = workers

        # Run the server
        console.print(f"\n[green]Starting server at {server_url}[/green]")
        console.print(f"[cyan]API Documentation: {docs_url}[/cyan]")
        console.print(
            f"[cyan]API Spec (OpenAPI): {server_url}/openapi.json[/cyan]")
        console.print(
            f"[cyan]Alternative Docs (ReDoc): {server_url}/redoc[/cyan]")
        console.print("\n[yellow]Press Ctrl+C to stop[/yellow]\n")

        uvicorn.run(**uvicorn_config)

    except ImportError:
        console.print("[red]Error: uvicorn is not installed[/red]")
        console.print("[yellow]Install it with: pip install uvicorn[/yellow]")
        raise typer.Exit(code=1) from None
    except Exception as e:
        console.print(f"[red]Error starting server: {e}[/red]")
        raise typer.Exit(code=1) from e


def _display_startup_info(
    host: str,
    port: int,
    reload: bool,
    workers: Optional[int],
    log_level: str,
) -> None:
    """Display formatted startup information."""
    # Create configuration table
    config_table = Table(show_header=False, box=None, padding=(0, 2))
    config_table.add_column("Setting", style="cyan")
    config_table.add_column("Value", style="white")

    config_table.add_row("Host", host)
    config_table.add_row("Port", str(port))
    config_table.add_row(
        "Mode", "Development (auto-reload)" if reload else "Production")

    if workers and workers > 1:
        config_table.add_row("Workers", str(workers))

    config_table.add_row("Log Level", log_level.upper())

    # Create panel
    panel = Panel(
        config_table,
        title="[bold]Claude Config API Server[/bold]",
        subtitle="Configuration",
        border_style="green",
    )

    console.print("\n")
    console.print(panel)


if __name__ == "__main__":
    app()
