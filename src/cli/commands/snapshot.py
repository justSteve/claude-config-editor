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
from src.cli.progress import show_status
from src.cli.utils import (
    get_initialized_database,
    handle_cli_error,
    validate_snapshot_id,
)
from src.core.config import get_settings
from src.core.database import close_database
from src.core.models import Annotation, Snapshot, SnapshotChange, SnapshotPath, SnapshotTag
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
    categories: Optional[str] = typer.Option(
        None,
        "--categories",
        "-c",
        help="Comma-separated list of categories to scan (settings, memory, subagents, desktop)",
    ),
    include_missing: bool = typer.Option(
        False,
        "--include-missing",
        help="Include paths that don't exist in scan results",
    ),
    skip_content: bool = typer.Option(
        False,
        "--skip-content",
        help="Don't read file contents, only metadata",
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

                # Parse category filter if provided
                category_filter = None
                if categories:
                    category_filter = [c.strip()
                                       for c in categories.split(",")]
                    valid_categories = {"settings",
                                        "memory", "subagents", "desktop"}
                    invalid = set(category_filter) - valid_categories
                    if invalid:
                        print_error(
                            f"Invalid categories: {', '.join(invalid)}")
                        console.print(
                            f"[yellow]Valid categories: {', '.join(valid_categories)}[/yellow]")
                        return

                # Get path definitions for progress tracking
                path_defs = scanner.get_path_definitions()

                # Filter by categories if specified
                if category_filter:
                    path_defs = [p for p in path_defs if p.get(
                        "category") in category_filter]

                if verbose:
                    filter_msg = f" (filtered to: {', '.join(category_filter)})" if category_filter else ""
                    console.print(
                        f"\n[cyan]Scanning {len(path_defs)} configured paths{filter_msg}...[/cyan]\n"
                    )

                # Create snapshot with progress tracking
                with show_status("Creating snapshot...", "Snapshot created successfully!"):
                    # Note: Scanner doesn't currently support all these options
                    # They would need to be added to PathScanner.create_snapshot()
                    snapshot = await scanner.create_snapshot(
                        trigger_type="cli",
                        triggered_by=get_settings().environment,
                        notes=notes,
                    )

                # Display results
                console.print("\n")
                console.print(
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
                console.print("\n")
                console.print(
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
                    "\n[bold cyan]Comparing Snapshots[/bold cyan]\n")
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

                console.print("[bold]Summary:[/bold]")
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


@app.command("delete")
def delete_snapshot(
    snapshot_id: int = typer.Argument(..., help="Snapshot ID to delete"),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Skip confirmation prompt",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed information",
    ),
) -> None:
    """Delete a snapshot and all associated data."""
    validate_snapshot_id(snapshot_id)

    async def _delete() -> None:
        try:
            db = await get_initialized_database()

            async with db.get_session() as session:
                # Get snapshot to verify it exists
                stmt = select(Snapshot).where(Snapshot.id == snapshot_id)
                result = await session.execute(stmt)
                snapshot = result.scalar_one_or_none()

                if not snapshot:
                    print_error(f"Snapshot {snapshot_id} not found")
                    return

                # Confirm deletion unless --force is used
                if not force:
                    console.print(
                        "\n[yellow]⚠ Warning:[/yellow] You are about to delete:")
                    console.print(f"  Snapshot ID: {snapshot.id}")
                    console.print(
                        f"  Created: {format_datetime(snapshot.snapshot_time)}")
                    console.print(f"  Files: {snapshot.files_found}")
                    console.print(
                        f"  Hash: {format_hash(snapshot.snapshot_hash)}")
                    console.print("\nThis will also delete:")
                    console.print("  - All associated paths")
                    console.print("  - All file contents")
                    console.print("  - All changes")
                    console.print("  - All tags")
                    console.print("  - All annotations")

                    confirm = typer.confirm(
                        "\nAre you sure you want to delete this snapshot?")
                    if not confirm:
                        console.print(
                            "\n[yellow]Deletion cancelled[/yellow]\n")
                        return

                # Delete the snapshot (cascade will handle related records)
                with show_status(
                    f"Deleting snapshot {snapshot_id}...",
                    f"Snapshot {snapshot_id} deleted successfully"
                ):
                    await session.delete(snapshot)
                    await session.commit()

        except Exception as e:
            handle_cli_error(e, verbose=verbose)
        finally:
            await close_database()

    asyncio.run(_delete())


@app.command("tag")
def manage_tags(
    snapshot_id: int = typer.Argument(..., help="Snapshot ID to tag"),
    tag_name: Optional[str] = typer.Option(
        None,
        "--add",
        "-a",
        help="Add a tag to the snapshot",
    ),
    remove: Optional[str] = typer.Option(
        None,
        "--remove",
        "-r",
        help="Remove a tag from the snapshot",
    ),
    list_tags: bool = typer.Option(
        False,
        "--list",
        "-l",
        help="List all tags for the snapshot",
    ),
    description: Optional[str] = typer.Option(
        None,
        "--description",
        "-d",
        help="Description for the tag (when adding)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed information",
    ),
) -> None:
    """Manage tags for a snapshot."""
    validate_snapshot_id(snapshot_id)

    async def _manage_tags() -> None:
        try:
            db = await get_initialized_database()

            async with db.get_session() as session:
                # Verify snapshot exists
                stmt = select(Snapshot).where(Snapshot.id == snapshot_id)
                result = await session.execute(stmt)
                snapshot = result.scalar_one_or_none()

                if not snapshot:
                    print_error(f"Snapshot {snapshot_id} not found")
                    return

                # Add tag
                if tag_name:
                    # Check if tag already exists
                    stmt = select(SnapshotTag).where(
                        SnapshotTag.snapshot_id == snapshot_id,
                        SnapshotTag.tag_name == tag_name,
                    )
                    result = await session.execute(stmt)
                    existing_tag = result.scalar_one_or_none()

                    if existing_tag:
                        console.print(
                            f"\n[yellow]Tag '{tag_name}' already exists on snapshot {snapshot_id}[/yellow]\n")
                        return

                    # Create new tag
                    new_tag = SnapshotTag(
                        snapshot_id=snapshot_id,
                        tag_name=tag_name,
                        description=description,
                        created_by="cli",
                    )
                    session.add(new_tag)
                    await session.commit()
                    print_success(
                        f"Tag '{tag_name}' added to snapshot {snapshot_id}")

                # Remove tag
                elif remove:
                    stmt = select(SnapshotTag).where(
                        SnapshotTag.snapshot_id == snapshot_id,
                        SnapshotTag.tag_name == remove,
                    )
                    result = await session.execute(stmt)
                    tag = result.scalar_one_or_none()

                    if not tag:
                        print_error(
                            f"Tag '{remove}' not found on snapshot {snapshot_id}")
                        return

                    await session.delete(tag)
                    await session.commit()
                    print_success(
                        f"Tag '{remove}' removed from snapshot {snapshot_id}")

                # List tags
                elif list_tags:
                    stmt = select(SnapshotTag).where(
                        SnapshotTag.snapshot_id == snapshot_id
                    ).order_by(SnapshotTag.created_at)
                    result = await session.execute(stmt)
                    tags = result.scalars().all()

                    if not tags:
                        console.print(
                            f"\n[yellow]No tags found for snapshot {snapshot_id}[/yellow]\n")
                        return

                    console.print(
                        f"\n[bold]Tags for Snapshot {snapshot_id}:[/bold]\n")
                    for tag in tags:
                        desc = f" - {tag.description}" if tag.description else ""
                        console.print(f"  • {tag.tag_name}{desc}")
                    console.print()

                else:
                    print_error("Please specify --add, --remove, or --list")

        except Exception as e:
            handle_cli_error(e, verbose=verbose)
        finally:
            await close_database()

    asyncio.run(_manage_tags())


@app.command("annotate")
def manage_annotations(
    snapshot_id: int = typer.Argument(..., help="Snapshot ID to annotate"),
    text: Optional[str] = typer.Option(
        None,
        "--add",
        "-a",
        help="Add an annotation to the snapshot",
    ),
    list_annotations: bool = typer.Option(
        False,
        "--list",
        "-l",
        help="List all annotations for the snapshot",
    ),
    annotation_type: Optional[str] = typer.Option(
        None,
        "--type",
        "-t",
        help="Type of annotation (note, warning, error, etc.)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed information",
    ),
) -> None:
    """Manage annotations for a snapshot."""
    validate_snapshot_id(snapshot_id)

    async def _manage_annotations() -> None:
        try:
            db = await get_initialized_database()

            async with db.get_session() as session:
                # Verify snapshot exists
                stmt = select(Snapshot).where(Snapshot.id == snapshot_id)
                result = await session.execute(stmt)
                snapshot = result.scalar_one_or_none()

                if not snapshot:
                    print_error(f"Snapshot {snapshot_id} not found")
                    return

                # Add annotation
                if text:
                    new_annotation = Annotation(
                        snapshot_id=snapshot_id,
                        annotation_text=text,
                        annotation_type=annotation_type or "note",
                        created_by="cli",
                    )
                    session.add(new_annotation)
                    await session.commit()
                    print_success(
                        f"Annotation added to snapshot {snapshot_id}")

                # List annotations
                elif list_annotations:
                    stmt = select(Annotation).where(
                        Annotation.snapshot_id == snapshot_id
                    ).order_by(Annotation.created_at)
                    result = await session.execute(stmt)
                    annotations = result.scalars().all()

                    if not annotations:
                        console.print(
                            f"\n[yellow]No annotations found for snapshot {snapshot_id}[/yellow]\n")
                        return

                    console.print(
                        f"\n[bold]Annotations for Snapshot {snapshot_id}:[/bold]\n")
                    for ann in annotations:
                        type_label = f"[{ann.annotation_type}]" if ann.annotation_type else ""
                        time_label = format_datetime(ann.created_at)
                        console.print(
                            f"  • {type_label} {ann.annotation_text}")
                        console.print(f"    [dim]{time_label}[/dim]")
                    console.print()

                else:
                    print_error("Please specify --add or --list")

        except Exception as e:
            handle_cli_error(e, verbose=verbose)
        finally:
            await close_database()

    asyncio.run(_manage_annotations())


if __name__ == "__main__":
    app()
