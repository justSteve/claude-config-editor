"""
Output formatting utilities for CLI.

Provides consistent formatting for tables, panels, and other CLI output using Rich.
"""

from datetime import datetime
from typing import Any, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()


def format_size(bytes_value: int) -> str:
    """Format byte size in human-readable format."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"


def format_datetime(dt: Optional[datetime]) -> str:
    """Format datetime in consistent format."""
    if dt is None:
        return "N/A"
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def format_hash(hash_value: str, length: int = 16) -> str:
    """Format hash to show first N characters with ellipsis."""
    if len(hash_value) <= length:
        return hash_value
    return f"{hash_value[:length]}..."


def create_snapshot_panel(
    snapshot_id: int,
    snapshot_hash: str,
    snapshot_time: datetime,
    files_found: int,
    directories_found: int,
    total_size_bytes: int,
    changed_from_previous: Optional[int] = None,
    title: str = "Snapshot Created",
    border_style: str = "green",
) -> Panel:
    """Create a formatted panel for snapshot information."""
    content = (
        f"[bold]ID:[/bold] {snapshot_id}\n"
        f"[bold]Hash:[/bold] {format_hash(snapshot_hash)}\n"
        f"[bold]Time:[/bold] {format_datetime(snapshot_time)}\n"
        f"[bold]Files:[/bold] {files_found:,}\n"
        f"[bold]Directories:[/bold] {directories_found:,}\n"
        f"[bold]Total Size:[/bold] {format_size(total_size_bytes)}"
    )

    if changed_from_previous is not None:
        content += f"\n[bold]Changes:[/bold] {changed_from_previous:,}"

    return Panel(
        content,
        title=title,
        border_style=border_style,
    )


def create_stats_table(stats: dict[str, Any]) -> Table:
    """Create a formatted table for database statistics."""
    table = Table(show_header=True, header_style="bold cyan", box=box.ROUNDED)
    table.add_column("Metric", style="white")
    table.add_column("Count", justify="right", style="cyan")

    table.add_row("Snapshots", f"{stats.get('snapshots_count', 0):,}")
    table.add_row("File Contents", f"{stats.get('file_contents_count', 0):,}")
    table.add_row("Snapshot Paths",
                  f"{stats.get('snapshot_paths_count', 0):,}")
    table.add_row("Changes Tracked",
                  f"{stats.get('snapshot_changes_count', 0):,}")
    table.add_row("Tags", f"{stats.get('snapshot_tags_count', 0):,}")
    table.add_row("Annotations", f"{stats.get('annotations_count', 0):,}")

    if "database_size_bytes" in stats:
        table.add_row("Database Size", format_size(
            stats["database_size_bytes"]))

    return table


def create_snapshot_list_table(snapshots: list) -> Table:
    """Create a formatted table for snapshot list."""
    table = Table(
        show_header=True,
        header_style="bold cyan",
        box=box.ROUNDED,
    )
    table.add_column("ID", style="cyan", justify="right")
    table.add_column("Time", style="white")
    table.add_column("Hash", style="dim")
    table.add_column("Files", justify="right")
    table.add_column("Dirs", justify="right")
    table.add_column("Size", justify="right")
    table.add_column("Changes", justify="right")
    table.add_column("Notes", style="dim")

    for snapshot in snapshots:
        table.add_row(
            str(snapshot.id),
            format_datetime(snapshot.snapshot_time),
            format_hash(snapshot.snapshot_hash, 12),
            f"{snapshot.files_found:,}",
            f"{snapshot.directories_found:,}",
            format_size(snapshot.total_size_bytes),
            str(snapshot.changed_from_previous) if snapshot.changed_from_previous is not None else "-",
            snapshot.notes[:30] + "..." if snapshot.notes and len(
                snapshot.notes) > 30 else snapshot.notes or "",
        )

    return table


def create_error_panel(message: str, details: Optional[str] = None) -> Panel:
    """Create a formatted error panel."""
    content = f"[bold red]ERROR:[/bold red] {message}"
    if details:
        content += f"\n\n[dim]{details}[/dim]"

    return Panel(
        content,
        title="Error",
        border_style="red",
    )


def create_warning_panel(message: str, details: Optional[str] = None) -> Panel:
    """Create a formatted warning panel."""
    content = f"[bold yellow]WARNING:[/bold yellow] {message}"
    if details:
        content += f"\n\n[dim]{details}[/dim]"

    return Panel(
        content,
        title="Warning",
        border_style="yellow",
    )


def create_success_panel(message: str, details: Optional[str] = None) -> Panel:
    """Create a formatted success panel."""
    content = f"[bold green]SUCCESS:[/bold green] {message}"
    if details:
        content += f"\n\n{details}"

    return Panel(
        content,
        title="Success",
        border_style="green",
    )


def print_error(message: str, details: Optional[str] = None) -> None:
    """Print an error message."""
    console.print(create_error_panel(message, details))


def print_warning(message: str, details: Optional[str] = None) -> None:
    """Print a warning message."""
    console.print(create_warning_panel(message, details))


def print_success(message: str, details: Optional[str] = None) -> None:
    """Print a success message."""
    console.print(create_success_panel(message, details))
