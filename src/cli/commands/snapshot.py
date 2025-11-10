"""
Snapshot management commands.

Commands for creating, listing, viewing, and comparing snapshots.
"""

import asyncio
from typing import Optional

import typer
from rich.console import Console
from sqlalchemy import select

from src.cli.formatters import (
    create_snapshot_list_table,
    create_snapshot_panel,
    format_datetime,
    format_hash,
    format_size,
    print_error,
    print_success,
)
from src.cli.progress import ScanProgress, show_status
from src.cli.utils import (
    get_initialized_database,
    handle_cli_error,
    validate_snapshot_id,
)
from src.core.config import get_settings
from src.core.database import close_database
from src.core.models import Snapshot, SnapshotChange, SnapshotPath
from src.core.scanner import PathScanner
from src.utils.logger import get_logger

app = typer.Typer(help="Snapshot management commands")
console = Console()
logger = get_logger(__name__)


@app.command("create")
def create_snapshot(
    notes: Optional[str] = typer.Option(
        None,
        "--notes",
        help="Optional notes about this snapshot",
    ),
    tag: Optional[str] = typer.Option(
        None,
        "--tag",
        help="Optional tag name for this snapshot",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed progress",
    ),
) -> None:
    """Create a new snapshot of Claude configurations."""

    async def _create() -> None:
        try:
            with show_status("Initializing database..."):
                db = await get_initialized_database()

            async with db.get_session() as session:
                scanner = PathScanner(session)

                # Get path definitions for progress tracking
                path_defs = scanner.get_path_definitions()

                if verbose:
                    console.print(
                        f"\n[cyan]Scanning {len(path_defs)} configured paths...[/cyan]\n"
                    )

                # Create snapshot with progress tracking
                with show_status("Creating snapshot...", "Snapshot created successfully!"):
                    snapshot = await scanner.create_snapshot(
                        trigger_type="cli",
                        triggered_by=get_settings().environment,
                        notes=notes,
                    )

                # Display results
                console.print(
                    "\n"
                    + str(
                        create_snapshot_panel(
                            snapshot_id=snapshot.id,
                            snapshot_hash=snapshot.snapshot_hash,
                            snapshot_time=snapshot.snapshot_time,
                            files_found=snapshot.files_found,
                            directories_found=snapshot.directories_found,
                            total_size_bytes=snapshot.total_size_bytes,
                            changed_from_previous=snapshot.changed_from_previous,
                        )
                    )
                )

                if snapshot.changed_from_previous is not None and snapshot.changed_from_previous > 0:
                    console.print(
                        f"\n[yellow]⚠ {snapshot.changed_from_previous} changes detected from previous snapshot[/yellow]"
                    )

                # Add tag if provided
                if tag:
                    console.print(f"\n[dim]Tagged as: {tag}[/dim]")

        except Exception as e:
            handle_cli_error(e, verbose=verbose)
        finally:
            await close_database()

    asyncio.run(_create())


@app.command("list")
def list_snapshots(
    limit: int = typer.Option(
        10,
        "--limit",
        "-l",
        help="Maximum number of snapshots to show",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show additional details",
    ),
) -> None:
    """List recent snapshots."""

    async def _list() -> None:
        try:
            db = await get_initialized_database()

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
                    console.print("\n[yellow]No snapshots found[/yellow]\n")
                    return

                console.print(
                    f"\n[bold cyan]Recent Snapshots[/bold cyan] (showing {len(snapshots)} of {limit})\n")

                # Create and display table
                table = create_snapshot_list_table(snapshots)
                console.print(table)
                console.print()

        except Exception as e:
            handle_cli_error(e, verbose=verbose)
        finally:
            await close_database()

    asyncio.run(_list())


@app.command("show")
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
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed information",
    ),
) -> None:
    """Show detailed information about a snapshot."""
    validate_snapshot_id(snapshot_id)

    async def _show() -> None:
        try:
            db = await get_initialized_database()

            async with db.get_session() as session:
                # Get snapshot
                stmt = select(Snapshot).where(Snapshot.id == snapshot_id)
                result = await session.execute(stmt)
                snapshot = result.scalar_one_or_none()

                if not snapshot:
                    print_error(f"Snapshot {snapshot_id} not found")
                    return

                # Display snapshot info
                console.print(
                    "\n"
                    + str(
                        create_snapshot_panel(
                            snapshot_id=snapshot.id,
                            snapshot_hash=snapshot.snapshot_hash,
                            snapshot_time=snapshot.snapshot_time,
                            files_found=snapshot.files_found,
                            directories_found=snapshot.directories_found,
                            total_size_bytes=snapshot.total_size_bytes,
                            changed_from_previous=snapshot.changed_from_previous,
                            title=f"Snapshot {snapshot_id}",
                            border_style="cyan",
                        )
                    )
                )

                # Show paths if requested
                if show_paths:
                    stmt = select(SnapshotPath).where(
                        SnapshotPath.snapshot_id == snapshot_id
                    )
                    result = await session.execute(stmt)
                    paths = result.scalars().all()

                    console.print(
                        f"\n[bold]Scanned Paths ({len(paths)}):[/bold]\n")
                    for path in paths[:20]:  # Limit to first 20
                        status = "✓" if path.exists else "✗"
                        console.print(
                            f"  [{'' if path.exists else 'dim'}]{status} {path.name}[/]"
                        )

                    if len(paths) > 20:
                        console.print(
                            f"\n  [dim]... and {len(paths) - 20} more[/dim]")

                # Show changes if requested
                if show_changes and snapshot.changed_from_previous:
                    stmt = select(SnapshotChange).where(
                        SnapshotChange.snapshot_id == snapshot_id
                    )
                    result = await session.execute(stmt)
                    changes = result.scalars().all()

                    console.print(
                        f"\n[bold]Changes ({len(changes)}):[/bold]\n")
                    for change in changes[:20]:  # Limit to first 20
                        color = {
                            "added": "green",
                            "modified": "yellow",
                            "deleted": "red",
                        }.get(change.change_type, "white")

                        console.print(
                            f"  [{color}]{change.change_type.upper():8}[/] {change.path_template}"
                        )

                    if len(changes) > 20:
                        console.print(
                            f"\n  [dim]... and {len(changes) - 20} more[/dim]")

                console.print()

        except Exception as e:
            handle_cli_error(e, verbose=verbose)
        finally:
            await close_database()

    asyncio.run(_show())


@app.command("compare")
def compare_snapshots(
    snapshot_id: int = typer.Argument(..., help="Current snapshot ID"),
    previous_id: Optional[int] = typer.Option(
        None,
        "--previous",
        "-p",
        help="Previous snapshot ID (auto-detected if not specified)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed comparison",
    ),
) -> None:
    """Compare two snapshots and show differences."""
    validate_snapshot_id(snapshot_id)
    if previous_id is not None:
        validate_snapshot_id(previous_id)

    async def _compare() -> None:
        try:
            db = await get_initialized_database()

            async with db.get_session() as session:
                # Get snapshots
                stmt = select(Snapshot).where(Snapshot.id == snapshot_id)
                result = await session.execute(stmt)
                current = result.scalar_one_or_none()

                if not current:
                    print_error(f"Snapshot {snapshot_id} not found")
                    return

                # Get previous snapshot
                if previous_id:
                    stmt = select(Snapshot).where(Snapshot.id == previous_id)
                    result = await session.execute(stmt)
                    previous = result.scalar_one_or_none()

                    if not previous:
                        print_error(f"Snapshot {previous_id} not found")
                        return
                else:
                    # Auto-detect previous
                    stmt = (
                        select(Snapshot)
                        .where(Snapshot.id < snapshot_id)
                        .order_by(Snapshot.id.desc())
                        .limit(1)
                    )
                    result = await session.execute(stmt)
                    previous = result.scalar_one_or_none()

                    if not previous:
                        print_error(
                            "No previous snapshot found for comparison")
                        return

                # Get changes
                stmt = select(SnapshotChange).where(
                    SnapshotChange.snapshot_id == snapshot_id,
                    SnapshotChange.previous_snapshot_id == previous.id,
                )
                result = await session.execute(stmt)
                changes = result.scalars().all()

                # Display comparison
                console.print(
                    f"\n[bold cyan]Comparing Snapshots[/bold cyan]\n")
                console.print(
                    f"[bold]Previous:[/bold] {previous.id} ({format_datetime(previous.snapshot_time)})")
                console.print(
                    f"[bold]Current:[/bold]  {current.id} ({format_datetime(current.snapshot_time)})")
                console.print()

                if not changes:
                    print_success("No changes detected between snapshots")
                    return

                # Group changes by type
                added = [c for c in changes if c.change_type == "added"]
                modified = [c for c in changes if c.change_type == "modified"]
                deleted = [c for c in changes if c.change_type == "deleted"]

                console.print(f"[bold]Summary:[/bold]")
                console.print(f"  [green]Added:[/green] {len(added)}")
                console.print(f"  [yellow]Modified:[/yellow] {len(modified)}")
                console.print(f"  [red]Deleted:[/red] {len(deleted)}")
                console.print()

                # Show changes
                if added:
                    console.print(
                        f"[bold green]Added ({len(added)}):[/bold green]")
                    for change in added[:10]:
                        console.print(f"  + {change.path_template}")
                    if len(added) > 10:
                        console.print(
                            f"  [dim]... and {len(added) - 10} more[/dim]")
                    console.print()

                if modified:
                    console.print(
                        f"[bold yellow]Modified ({len(modified)}):[/bold yellow]")
                    for change in modified[:10]:
                        size_change = ""
                        if change.old_size_bytes and change.new_size_bytes:
                            delta = change.new_size_bytes - change.old_size_bytes
                            size_change = f" ({format_size(abs(delta))} {'+' if delta > 0 else '-'})"
                        console.print(
                            f"  * {change.path_template}{size_change}")
                    if len(modified) > 10:
                        console.print(
                            f"  [dim]... and {len(modified) - 10} more[/dim]")
                    console.print()

                if deleted:
                    console.print(
                        f"[bold red]Deleted ({len(deleted)}):[/bold red]")
                    for change in deleted[:10]:
                        console.print(f"  - {change.path_template}")
                    if len(deleted) > 10:
                        console.print(
                            f"  [dim]... and {len(deleted) - 10} more[/dim]")
                    console.print()

        except Exception as e:
            handle_cli_error(e, verbose=verbose)
        finally:
            await close_database()

    asyncio.run(_compare())


if __name__ == "__main__":
    app()
