"""
Database management commands.

Commands for database statistics, maintenance, and management.
"""

import asyncio
from typing import Optional

import typer
from rich.console import Console
from sqlalchemy import func, select

from src.cli.formatters import create_stats_table, format_size, print_error, print_success
from src.cli.progress import show_status
from src.cli.utils import confirm_action, get_initialized_database, handle_cli_error
from src.core.database import close_database
from src.core.models import FileContent
from src.utils.logger import get_logger

app = typer.Typer(help="Database management commands")
console = Console()
logger = get_logger(__name__)


@app.command("stats")
def show_stats(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show additional statistics",
    ),
) -> None:
    """Show database statistics and storage information."""

    async def _stats() -> None:
        try:
            with show_status("Gathering database statistics..."):
                db = await get_initialized_database()
                stats = await db.get_database_stats()

            console.print("\n[bold cyan]Database Statistics[/bold cyan]\n")

            # Create and display table
            table = create_stats_table(stats)
            console.print(table)

            if verbose:
                console.print("\n[bold]Additional Information:[/bold]")
                console.print(f"  Database URL: {db.database_url}")
                console.print(f"  Engine: SQLite")
                console.print()

        except Exception as e:
            handle_cli_error(e, verbose=verbose)
        finally:
            await close_database()

    asyncio.run(_stats())


@app.command("dedup")
def show_deduplication(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed deduplication information",
    ),
) -> None:
    """Show file content deduplication statistics."""

    async def _dedup() -> None:
        try:
            db = await get_initialized_database()

            async with db.get_session() as session:
                # Get deduplication stats
                stmt = select(
                    func.count(FileContent.id).label("unique_files"),
                    func.sum(FileContent.size_bytes).label("total_size"),
                    func.sum(FileContent.reference_count).label(
                        "total_references"),
                )
                result = await session.execute(stmt)
                row = result.one()

                unique_files = row.unique_files or 0
                total_size = row.total_size or 0
                total_references = row.total_references or 0

                # Calculate savings
                if total_references > 0:
                    duplicate_refs = total_references - unique_files
                    savings_bytes = (duplicate_refs / total_references) * \
                        total_size if total_references > 0 else 0
                    dedup_ratio = (unique_files / total_references *
                                   100) if total_references > 0 else 0
                else:
                    duplicate_refs = 0
                    savings_bytes = 0
                    dedup_ratio = 0

                console.print(
                    "\n[bold cyan]Deduplication Statistics[/bold cyan]\n")
                console.print(f"[bold]Unique files:[/bold] {unique_files:,}")
                console.print(
                    f"[bold]Total references:[/bold] {total_references:,}")
                console.print(
                    f"[bold]Duplicate references:[/bold] {duplicate_refs:,}")
                console.print(
                    f"[bold]Storage used:[/bold] {format_size(total_size)}")
                console.print(
                    f"[bold]Storage saved:[/bold] {format_size(int(savings_bytes))}")
                console.print(
                    f"[bold]Deduplication ratio:[/bold] {dedup_ratio:.1f}%")
                console.print()

                if verbose and unique_files > 0:
                    # Show most referenced files
                    stmt = (
                        select(FileContent)
                        .where(FileContent.reference_count > 1)
                        .order_by(FileContent.reference_count.desc())
                        .limit(10)
                    )
                    result = await session.execute(stmt)
                    files = result.scalars().all()

                    if files:
                        console.print("[bold]Most Referenced Files:[/bold]")
                        for file in files:
                            console.print(
                                f"  {file.reference_count:3}x - {format_size(file.size_bytes):>10} - {file.content_hash[:16]}..."
                            )
                        console.print()

        except Exception as e:
            handle_cli_error(e, verbose=verbose)
        finally:
            await close_database()

    asyncio.run(_dedup())


@app.command("vacuum")
def vacuum_database(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed vacuum information",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Skip confirmation prompt",
    ),
) -> None:
    """Vacuum the database to reclaim space and optimize performance."""

    async def _vacuum() -> None:
        try:
            if not force:
                if not confirm_action(
                    "This will vacuum the database. Continue?", default=True
                ):
                    console.print("\n[yellow]Vacuum cancelled[/yellow]\n")
                    return

            db = await get_initialized_database()

            with show_status("Vacuuming database...", "Database vacuumed successfully!"):
                async with db.get_session() as session:
                    await session.execute("VACUUM")
                    await session.commit()

                # Get new size
                stats = await db.get_database_stats()
                new_size = stats.get("database_size_bytes", 0)

                console.print()
                console.print(
                    f"[bold]Database size:[/bold] {format_size(new_size)}")
                console.print()

        except Exception as e:
            handle_cli_error(e, verbose=verbose)
        finally:
            await close_database()

    asyncio.run(_vacuum())


@app.command("health")
def health_check(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed health information",
    ),
) -> None:
    """Check database health and connectivity."""

    async def _health() -> None:
        try:
            db = await get_initialized_database()

            with show_status("Checking database health..."):
                is_healthy = await db.health_check()

            if is_healthy:
                print_success("Database is healthy and accessible")

                if verbose:
                    stats = await db.get_database_stats()
                    console.print("\n[bold]Health Details:[/bold]")
                    console.print(f"  Connected: Yes")
                    console.print(f"  Tables: {len(stats)} metrics available")
                    console.print(
                        f"  Size: {format_size(stats.get('database_size_bytes', 0))}")
                    console.print()
            else:
                print_error("Database health check failed")

        except Exception as e:
            handle_cli_error(e, verbose=verbose)
        finally:
            await close_database()

    asyncio.run(_health())


if __name__ == "__main__":
    app()
