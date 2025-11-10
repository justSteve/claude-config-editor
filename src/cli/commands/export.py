"""
Export commands for snapshots and data.

Commands for exporting snapshots, configurations, and database backups
in various formats (JSON, YAML, HTML, CSV).
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.cli.formatters import format_datetime, format_size, print_error, print_success
from src.cli.progress import show_status
from src.cli.utils import get_initialized_database, handle_cli_error, validate_snapshot_id
from src.core.config import get_settings
from src.core.database import close_database
from src.core.models import Snapshot, SnapshotPath
from src.core.schemas.converters import snapshot_to_detail
from src.utils.logger import get_logger

app = typer.Typer(help="Export commands for data portability")
console = Console()
logger = get_logger(__name__)


@app.command("snapshot")
def export_snapshot(
    snapshot_id: int = typer.Argument(..., help="Snapshot ID to export"),
    output: Path = typer.Option(
        None,
        "--output",
        help="Output file path (defaults to snapshot_<id>.<format>)",
    ),
    format: str = typer.Option(
        "json",
        "--format",
        help="Export format: json, yaml, html, csv",
    ),
    include_content: bool = typer.Option(
        True,
        "--content/--no-content",
        help="Include file contents in export",
    ),
    compress: bool = typer.Option(
        False,
        "--compress",
        help="Compress export file (gzip)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed export information",
    ),
) -> None:
    """Export a snapshot to JSON, YAML, HTML, or CSV format."""
    validate_snapshot_id(snapshot_id)

    # Validate format
    valid_formats = ["json", "yaml", "html", "csv"]
    if format not in valid_formats:
        print_error(
            f"Invalid format: {format}. Must be one of: {', '.join(valid_formats)}")
        return

    # Determine output file
    if output is None:
        extension = format
        if compress:
            extension += ".gz"
        output = Path(f"snapshot_{snapshot_id}.{extension}")

    async def _export() -> None:
        try:
            db = await get_initialized_database()

            async with db.get_session() as session:
                # Get snapshot with eagerly loaded relationships
                stmt = (
                    select(Snapshot)
                    .where(Snapshot.id == snapshot_id)
                    .options(
                        selectinload(Snapshot.env_vars),
                        selectinload(Snapshot.paths),
                        selectinload(Snapshot.changes),
                        selectinload(Snapshot.tags),
                        selectinload(Snapshot.annotations),
                    )
                )
                result = await session.execute(stmt)
                snapshot = result.scalar_one_or_none()

                if not snapshot:
                    print_error(f"Snapshot {snapshot_id} not found")
                    return

                # Get paths
                stmt = select(SnapshotPath).where(
                    SnapshotPath.snapshot_id == snapshot_id
                )
                result = await session.execute(stmt)
                paths = result.scalars().all()

                if verbose:
                    console.print(
                        f"\n[cyan]Exporting snapshot {snapshot_id}...[/cyan]")
                    console.print(f"  Paths to export: {len(paths)}")
                    console.print(f"  Format: {format}")
                    console.print(f"  Output: {output}")
                    console.print()

                # Export based on format (inside session context to keep objects attached)
                console.print("[bold cyan]Exporting...[/bold cyan]")
                if format == "json":
                    await _export_json(snapshot, paths, output, include_content, compress)
                elif format == "yaml":
                    await _export_yaml(snapshot, paths, output, include_content, compress)
                elif format == "html":
                    await _export_html(snapshot, paths, output)
                elif format == "csv":
                    await _export_csv(snapshot, paths, output)

                # Get file size
                file_size = output.stat().st_size if output.exists() else 0

                print_success(
                    "Snapshot exported successfully",
                    f"File: {output}\nSize: {format_size(file_size)}\nFormat: {format.upper()}",
                )

        except Exception as e:
            handle_cli_error(e, verbose=verbose)
        finally:
            await close_database()

    asyncio.run(_export())


async def _export_json(
    snapshot: Snapshot,
    paths: list[SnapshotPath],
    output: Path,
    include_content: bool,
    compress: bool,
) -> None:
    """Export snapshot to JSON format."""
    # Convert to Pydantic schema
    snapshot_data = snapshot_to_detail(snapshot)

    # Build export data
    export_data = {
        "version": "1.0",
        "exported_at": datetime.utcnow().isoformat(),
        "snapshot": snapshot_data.model_dump(mode="json"),
        "paths": [
            {
                "id": p.id,
                "category": p.category,
                "name": p.name,
                "path_template": p.path_template,
                "resolved_path": p.resolved_path,
                "exists": p.exists,
                "type": p.type,
                "size_bytes": p.size_bytes,
                "modified_time": p.modified_time.isoformat() if p.modified_time else None,
                "content_hash": p.content_hash,
            }
            for p in paths
        ],
    }

    # Write to file
    if compress:
        import gzip
        with gzip.open(output, "wt", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, default=str)
    else:
        with open(output, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, default=str)


async def _export_yaml(
    snapshot: Snapshot,
    paths: list[SnapshotPath],
    output: Path,
    include_content: bool,
    compress: bool,
) -> None:
    """Export snapshot to YAML format."""
    import yaml

    # Convert to Pydantic schema
    snapshot_data = snapshot_to_detail(snapshot)

    # Build export data
    export_data = {
        "version": "1.0",
        "exported_at": datetime.utcnow().isoformat(),
        "snapshot": snapshot_data.model_dump(mode="python"),
        "paths": [
            {
                "id": p.id,
                "category": p.category,
                "name": p.name,
                "path_template": p.path_template,
                "resolved_path": p.resolved_path,
                "exists": p.exists,
                "type": p.type,
                "size_bytes": p.size_bytes,
                "modified_time": p.modified_time.isoformat() if p.modified_time else None,
                "content_hash": p.content_hash,
            }
            for p in paths
        ],
    }

    # Write to file
    if compress:
        import gzip
        with gzip.open(output, "wt", encoding="utf-8") as f:
            yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)
    else:
        with open(output, "w", encoding="utf-8") as f:
            yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)


async def _export_html(
    snapshot: Snapshot,
    paths: list[SnapshotPath],
    output: Path,
) -> None:
    """Export snapshot to HTML format."""
    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Snapshot {snapshot.id} - Claude Config Export</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background-color: #2c3e50;
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        .stat-card {{
            background-color: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .stat-label {{
            color: #7f8c8d;
            font-size: 0.9em;
            margin-bottom: 5px;
        }}
        .stat-value {{
            font-size: 1.5em;
            font-weight: bold;
            color: #2c3e50;
        }}
        table {{
            width: 100%;
            background-color: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ecf0f1;
        }}
        th {{
            background-color: #34495e;
            color: white;
            font-weight: 600;
        }}
        tr:hover {{
            background-color: #f8f9fa;
        }}
        .exists {{
            color: #27ae60;
        }}
        .missing {{
            color: #e74c3c;
        }}
        .footer {{
            margin-top: 20px;
            text-align: center;
            color: #7f8c8d;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Snapshot {snapshot.id}</h1>
        <p>Created: {format_datetime(snapshot.snapshot_time)}</p>
        <p>Hash: {snapshot.snapshot_hash[:16]}...</p>
    </div>

    <div class="stats">
        <div class="stat-card">
            <div class="stat-label">Files Found</div>
            <div class="stat-value">{snapshot.files_found:,}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Directories</div>
            <div class="stat-value">{snapshot.directories_found:,}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Total Size</div>
            <div class="stat-value">{format_size(snapshot.total_size_bytes)}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Changes</div>
            <div class="stat-value">{snapshot.changed_from_previous or 0:,}</div>
        </div>
    </div>

    <table>
        <thead>
            <tr>
                <th>Name</th>
                <th>Category</th>
                <th>Path</th>
                <th>Status</th>
                <th>Type</th>
                <th>Size</th>
            </tr>
        </thead>
        <tbody>
"""

    # Add path rows
    for path in paths:
        status_class = "exists" if path.exists else "missing"
        status_text = "✓ Exists" if path.exists else "✗ Missing"
        size_text = format_size(path.size_bytes) if path.size_bytes else "-"

        html_template += f"""
            <tr>
                <td>{path.name}</td>
                <td>{path.category}</td>
                <td><code>{path.resolved_path}</code></td>
                <td class="{status_class}">{status_text}</td>
                <td>{path.type or "-"}</td>
                <td>{size_text}</td>
            </tr>
"""

    html_template += """
        </tbody>
    </table>

    <div class="footer">
        <p>Exported from Claude Config Editor</p>
        <p>Generated: """ + format_datetime(datetime.utcnow()) + """</p>
    </div>
</body>
</html>
"""

    # Write to file
    with open(output, "w", encoding="utf-8") as f:
        f.write(html_template)


async def _export_csv(
    snapshot: Snapshot,
    paths: list[SnapshotPath],
    output: Path,
) -> None:
    """Export snapshot paths to CSV format."""
    import csv

    with open(output, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # Write header
        writer.writerow([
            "ID",
            "Category",
            "Name",
            "Path Template",
            "Resolved Path",
            "Exists",
            "Type",
            "Size (bytes)",
            "Modified Time",
            "Content Hash",
        ])

        # Write rows
        for path in paths:
            writer.writerow([
                path.id,
                path.category,
                path.name,
                path.path_template,
                path.resolved_path,
                "Yes" if path.exists else "No",
                path.type or "",
                path.size_bytes or "",
                format_datetime(
                    path.modified_time) if path.modified_time else "",
                path.content_hash or "",
            ])


@app.command("config")
def export_config(
    output: Path = typer.Option(
        Path("claude-config-export.yaml"),
        "--output",
        "-o",
        help="Output file path",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed information",
    ),
) -> None:
    """Export current configuration to YAML file."""

    try:
        with show_status("Exporting configuration...", "Configuration exported successfully!"):
            settings = get_settings()
            settings.to_yaml(output)

        file_size = output.stat().st_size if output.exists() else 0

        print_success(
            "Configuration exported",
            f"File: {output}\nSize: {format_size(file_size)}",
        )

    except Exception as e:
        handle_cli_error(e, verbose=verbose)


if __name__ == "__main__":
    app()
