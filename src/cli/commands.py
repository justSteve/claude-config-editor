"""
CLI commands for Claude Config version control system.

Provides command-line interface using Typer with Rich formatting.

Usage:
    claude-config snapshot                  # Create new snapshot
    claude-config snapshot list             # List all snapshots
    claude-config snapshot show <id>        # Show snapshot details
"""

import asyncio
from datetime import datetime
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from src.core.config import get_settings
from src.core.database import init_database, close_database, get_db_manager
from src.core.scanner import PathScanner
from src.utils.logger import setup_logging, get_logger
from sqlalchemy import select
from src.core.models import Snapshot, SnapshotPath, SnapshotChange

app = typer.Typer(
    name="claude-config",
    help="Version-controlled management for Claude Code and Claude Desktop configurations",
    add_completion=False,
)
snapshot_app = typer.Typer(help="Snapshot management commands")
app.add_typer(snapshot_app, name="snapshot")

console = Console()
logger = get_logger(__name__)


@app.callback()
def main_callback() -> None:
    """Initialize application."""
    settings = get_settings()
    setup_logging(
        log_level=settings.log_level,
        log_file=settings.log_file,
        log_max_bytes=settings.log_max_bytes,
        log_backup_count=settings.log_backup_count,
    )


@snapshot_app.command("create")
def create_snapshot(
    notes: Optional[str] = typer.Option(
        None,
        "--notes",
        "-n",
        help="Optional notes about this snapshot",
    ),
    tag: Optional[str] = typer.Option(
        None,
        "--tag",
        "-t",
        help="Optional tag name for this snapshot",
    ),
) -> None:
    """Create a new snapshot of Claude configurations."""
    console.print("\n[bold cyan]Creating snapshot...[/bold cyan]\n")

    async def _create() -> None:
        settings = get_settings()

        # Initialize database
        db = await init_database(settings.database_url, echo=False)

        try:
            # Get session and create scanner
            async with db.get_session() as session:
                scanner = PathScanner(session)

                # Create snapshot
                snapshot = await scanner.create_snapshot(
                    trigger_type="cli",
                    triggered_by=settings.environment,
                    notes=notes,
                )

                # Display results
                console.print(
                    Panel(
                        f"[green]SUCCESS[/green] Snapshot created successfully!\n\n"
                        f"[bold]ID:[/bold] {snapshot.id}\n"
                        f"[bold]Hash:[/bold] {snapshot.snapshot_hash[:16]}...\n"
                        f"[bold]Time:[/bold] {snapshot.snapshot_time}\n"
                        f"[bold]Files:[/bold] {snapshot.files_found}\n"
                        f"[bold]Directories:[/bold] {snapshot.directories_found}\n"
                        f"[bold]Total Size:[/bold] {snapshot.total_size_bytes:,} bytes",
                        title="Snapshot Created",
                        border_style="green",
                    )
                )

                if snapshot.changed_from_previous is not None:
                    console.print(
                        f"\n[yellow]Changes from previous:[/yellow] {snapshot.changed_from_previous}"
                    )

        finally:
            await close_database()

    asyncio.run(_create())


@snapshot_app.command("list")
def list_snapshots(
    limit: int = typer.Option(
        10,
        "--limit",
        "-l",
        help="Maximum number of snapshots to show",
    ),
) -> None:
    """List recent snapshots."""
    console.print("\n[bold cyan]Recent Snapshots[/bold cyan]\n")

    async def _list() -> None:
        settings = get_settings()
        db = await init_database(settings.database_url, echo=False)

        try:
            async with db.get_session() as session:
                # Query snapshots
                stmt = (
                    select(Snapshot)
                    .order_by(Snapshot.snapshot_time.desc())
                    .limit(limit)
                )
                result = await session.execute(stmt)
                snapshots = result.scalars().all()

                if not snapshots:
                    console.print("[yellow]No snapshots found[/yellow]")
                    return

                # Create table
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
                    # Format size
                    if snapshot.total_size_bytes < 1024:
                        size_str = f"{snapshot.total_size_bytes}B"
                    elif snapshot.total_size_bytes < 1024 * 1024:
                        size_str = f"{snapshot.total_size_bytes / 1024:.1f}KB"
                    else:
                        size_str = f"{snapshot.total_size_bytes / (1024 * 1024):.1f}MB"

                    # Format changes
                    changes_str = (
                        str(snapshot.changed_from_previous)
                        if snapshot.changed_from_previous is not None
                        else "-"
                    )

                    table.add_row(
                        str(snapshot.id),
                        snapshot.snapshot_time.strftime("%Y-%m-%d %H:%M:%S"),
                        snapshot.snapshot_hash[:8] + "...",
                        str(snapshot.files_found),
                        str(snapshot.directories_found),
                        size_str,
                        changes_str,
                        snapshot.notes or "",
                    )

                console.print(table)

        finally:
            await close_database()

    asyncio.run(_list())


@snapshot_app.command("show")
def show_snapshot(
    snapshot_id: int = typer.Argument(..., help="Snapshot ID to display"),
    show_paths: bool = typer.Option(
        False,
        "--paths",
        "-p",
        help="Show all scanned paths",
    ),
    show_changes: bool = typer.Option(
        False,
        "--changes",
        "-c",
        help="Show changes from previous snapshot",
    ),
) -> None:
    """Show detailed information about a snapshot."""
    console.print(f"\n[bold cyan]Snapshot {snapshot_id} Details[/bold cyan]\n")

    async def _show() -> None:
        settings = get_settings()
        db = await init_database(settings.database_url, echo=False)

        try:
            async with db.get_session() as session:
                # Get snapshot
                stmt = select(Snapshot).where(Snapshot.id == snapshot_id)
                result = await session.execute(stmt)
                snapshot = result.scalar_one_or_none()

                if not snapshot:
                    console.print(f"[red]Snapshot {snapshot_id} not found[/red]")
                    return

                # Display snapshot info
                info_lines = [
                    f"[bold]Hash:[/bold] {snapshot.snapshot_hash}",
                    f"[bold]Time:[/bold] {snapshot.snapshot_time}",
                    f"[bold]Trigger:[/bold] {snapshot.trigger_type}",
                    f"[bold]Triggered By:[/bold] {snapshot.triggered_by or 'N/A'}",
                    f"[bold]OS:[/bold] {snapshot.os_type} {snapshot.os_version or ''}",
                    f"[bold]Hostname:[/bold] {snapshot.hostname or 'N/A'}",
                    f"[bold]Username:[/bold] {snapshot.username or 'N/A'}",
                    "",
                    f"[bold]Total Locations:[/bold] {snapshot.total_locations}",
                    f"[bold]Files Found:[/bold] {snapshot.files_found}",
                    f"[bold]Directories Found:[/bold] {snapshot.directories_found}",
                    f"[bold]Total Size:[/bold] {snapshot.total_size_bytes:,} bytes",
                ]

                if snapshot.changed_from_previous is not None:
                    info_lines.append(
                        f"[bold]Changes from Previous:[/bold] {snapshot.changed_from_previous}"
                    )

                if snapshot.notes:
                    info_lines.extend(["", f"[bold]Notes:[/bold] {snapshot.notes}"])

                console.print(Panel("\n".join(info_lines), border_style="cyan"))

                # Show paths if requested
                if show_paths:
                    console.print("\n[bold cyan]Scanned Paths:[/bold cyan]\n")

                    stmt = select(SnapshotPath).where(
                        SnapshotPath.snapshot_id == snapshot_id
                    )
                    result = await session.execute(stmt)
                    paths = result.scalars().all()

                    table = Table(show_header=True, header_style="bold cyan", box=box.ROUNDED)
                    table.add_column("Category", style="cyan")
                    table.add_column("Name", style="white")
                    table.add_column("Exists", justify="center")
                    table.add_column("Type", justify="center")
                    table.add_column("Size", justify="right")

                    for path in paths:
                        exists_str = "[green]YES[/green]" if path.exists else "[dim]NO[/dim]"
                        type_str = path.type or "-"

                        if path.size_bytes:
                            if path.size_bytes < 1024:
                                size_str = f"{path.size_bytes}B"
                            elif path.size_bytes < 1024 * 1024:
                                size_str = f"{path.size_bytes / 1024:.1f}KB"
                            else:
                                size_str = f"{path.size_bytes / (1024 * 1024):.1f}MB"
                        else:
                            size_str = "-"

                        table.add_row(
                            path.category,
                            path.name,
                            exists_str,
                            type_str,
                            size_str,
                        )

                    console.print(table)

                # Show changes if requested
                if show_changes and snapshot.parent_snapshot_id:
                    console.print("\n[bold cyan]Changes from Previous Snapshot:[/bold cyan]\n")

                    stmt = select(SnapshotChange).where(
                        SnapshotChange.snapshot_id == snapshot_id
                    )
                    result = await session.execute(stmt)
                    changes = result.scalars().all()

                    if changes:
                        table = Table(show_header=True, header_style="bold cyan", box=box.ROUNDED)
                        table.add_column("Type", style="cyan", justify="center")
                        table.add_column("Path", style="white")
                        table.add_column("Old Size", justify="right")
                        table.add_column("New Size", justify="right")

                        for change in changes:
                            old_size = (
                                f"{change.old_size_bytes:,}" if change.old_size_bytes else "-"
                            )
                            new_size = (
                                f"{change.new_size_bytes:,}" if change.new_size_bytes else "-"
                            )

                            # Color code by change type
                            change_type = change.change_type
                            if change_type == "added":
                                type_str = "[green]Added[/green]"
                            elif change_type == "deleted":
                                type_str = "[red]Deleted[/red]"
                            elif change_type == "modified":
                                type_str = "[yellow]Modified[/yellow]"
                            else:
                                type_str = change_type

                            table.add_row(
                                type_str,
                                change.path_template,
                                old_size,
                                new_size,
                            )

                        console.print(table)
                    else:
                        console.print("[dim]No changes detected[/dim]")

        finally:
            await close_database()

    asyncio.run(_show())


@app.command("stats")
def show_stats() -> None:
    """Show database statistics."""
    console.print("\n[bold cyan]Database Statistics[/bold cyan]\n")

    async def _stats() -> None:
        settings = get_settings()
        db = await init_database(settings.database_url, echo=False)

        try:
            stats = await db.get_database_stats()

            table = Table(show_header=True, header_style="bold cyan", box=box.ROUNDED)
            table.add_column("Metric", style="white")
            table.add_column("Count", justify="right", style="cyan")

            table.add_row("Snapshots", f"{stats.get('snapshots_count', 0):,}")
            table.add_row("File Contents", f"{stats.get('file_contents_count', 0):,}")
            table.add_row("Snapshot Paths", f"{stats.get('snapshot_paths_count', 0):,}")
            table.add_row("Changes Tracked", f"{stats.get('snapshot_changes_count', 0):,}")
            table.add_row("Tags", f"{stats.get('snapshot_tags_count', 0):,}")
            table.add_row("Annotations", f"{stats.get('annotations_count', 0):,}")

            if "database_size_bytes" in stats:
                size_mb = stats["database_size_bytes"] / (1024 * 1024)
                table.add_row("Database Size", f"{size_mb:.2f} MB")

            console.print(table)

        finally:
            await close_database()

    asyncio.run(_stats())


if __name__ == "__main__":
    app()
