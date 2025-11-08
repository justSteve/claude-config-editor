"""
Report formatters for different output formats.

Supports CLI (Rich), JSON, and HTML output.
"""

import json
from abc import ABC, abstractmethod
from typing import Union
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from src.reports.models import (
    ChangeDetectionReport,
    SnapshotSummaryReport,
    DeduplicationReport,
)


class ReportFormatter(ABC):
    """Base class for report formatters."""

    @abstractmethod
    def format_change_report(self, report: ChangeDetectionReport) -> str:
        """Format a change detection report."""
        pass

    @abstractmethod
    def format_snapshot_report(self, report: SnapshotSummaryReport) -> str:
        """Format a snapshot summary report."""
        pass

    @abstractmethod
    def format_deduplication_report(self, report: DeduplicationReport) -> str:
        """Format a deduplication report."""
        pass


class CLIFormatter(ReportFormatter):
    """Format reports for CLI output using Rich."""

    def __init__(self):
        self.console = Console()

    def format_change_report(self, report: ChangeDetectionReport) -> str:
        """Format change report as Rich tables."""
        output = []

        # Header panel
        header = (
            f"[bold]Snapshot {report.snapshot_id}[/bold] vs [bold]Snapshot {report.previous_snapshot_id}[/bold]\n"
            f"Current: {report.snapshot_time}\n"
            f"Previous: {report.previous_snapshot_time}\n\n"
            f"[cyan]Total Changes:[/cyan] {report.total_changes}\n"
            f"[cyan]Size Change:[/cyan] {self._format_size_delta(report.size_change_bytes)}"
        )

        panel = Panel(header, title="Change Detection Report", border_style="cyan")

        # Capture Rich output to string
        from io import StringIO
        string_io = StringIO()
        temp_console = Console(file=string_io, force_terminal=True, width=120, legacy_windows=False)
        temp_console.print(panel)

        # Added files
        if report.added_files:
            temp_console.print("\n[bold green]Added Files[/bold green]\n")
            table = Table(show_header=True, header_style="bold green", box=box.ROUNDED)
            table.add_column("Path", style="white")
            table.add_column("Size", justify="right", style="green")
            table.add_column("Modified", style="dim")

            for file in report.added_files:
                table.add_row(
                    file.path_template,
                    self._format_size(file.new_size_bytes),
                    self._format_time(file.new_modified_time),
                )
            temp_console.print(table)

        # Modified files
        if report.modified_files:
            temp_console.print("\n[bold yellow]Modified Files[/bold yellow]\n")
            table = Table(show_header=True, header_style="bold yellow", box=box.ROUNDED)
            table.add_column("Path", style="white")
            table.add_column("Old Size", justify="right", style="dim")
            table.add_column("New Size", justify="right", style="yellow")
            table.add_column("Delta", justify="right", style="cyan")

            for file in report.modified_files:
                table.add_row(
                    file.path_template,
                    self._format_size(file.old_size_bytes),
                    self._format_size(file.new_size_bytes),
                    self._format_size_delta(file.size_delta),
                )
            temp_console.print(table)

        # Deleted files
        if report.deleted_files:
            temp_console.print("\n[bold red]Deleted Files[/bold red]\n")
            table = Table(show_header=True, header_style="bold red", box=box.ROUNDED)
            table.add_column("Path", style="white")
            table.add_column("Size", justify="right", style="red")
            table.add_column("Last Modified", style="dim")

            for file in report.deleted_files:
                table.add_row(
                    file.path_template,
                    self._format_size(file.old_size_bytes),
                    self._format_time(file.old_modified_time),
                )
            temp_console.print(table)

        return string_io.getvalue()

    def format_snapshot_report(self, report: SnapshotSummaryReport) -> str:
        """Format snapshot summary as Rich tables."""
        from io import StringIO
        string_io = StringIO()
        temp_console = Console(file=string_io, force_terminal=True, width=120, legacy_windows=False)

        # Header
        header = (
            f"[bold]Snapshot ID:[/bold] {report.snapshot_id}\n"
            f"[bold]Time:[/bold] {report.snapshot_time}\n"
            f"[bold]Hash:[/bold] {report.snapshot_hash[:16]}...\n"
            f"[bold]Trigger:[/bold] {report.trigger_type} by {report.triggered_by or 'N/A'}\n"
            f"[bold]OS:[/bold] {report.os_type}\n"
        )

        if report.notes:
            header += f"\n[bold]Notes:[/bold] {report.notes}\n"

        header += (
            f"\n[cyan]Locations:[/cyan] {report.total_locations} ({report.files_found} files, {report.directories_found} dirs)\n"
            f"[cyan]Total Size:[/cyan] {self._format_size(report.total_size_bytes)}\n"
            f"[cyan]Deduplication:[/cyan] {report.unique_contents} unique contents, "
            f"{report.deduplication_percent:.1f}% savings ({self._format_size(report.deduplication_savings_bytes)})"
        )

        panel = Panel(header, title="Snapshot Summary", border_style="cyan")
        temp_console.print(panel)

        # Category breakdown
        if report.category_stats:
            temp_console.print("\n[bold cyan]Category Breakdown[/bold cyan]\n")
            table = Table(show_header=True, header_style="bold cyan", box=box.ROUNDED)
            table.add_column("Category", style="white")
            table.add_column("Found", justify="center", style="green")
            table.add_column("Missing", justify="center", style="dim")
            table.add_column("Total", justify="center")
            table.add_column("Size", justify="right", style="cyan")

            for cat in report.category_stats:
                table.add_row(
                    cat.category,
                    str(cat.found),
                    str(cat.missing),
                    str(cat.total_locations),
                    self._format_size(cat.total_size_bytes),
                )
            temp_console.print(table)

        # Path details
        if report.paths:
            temp_console.print("\n[bold cyan]All Paths[/bold cyan]\n")
            table = Table(show_header=True, header_style="bold cyan", box=box.ROUNDED)
            table.add_column("Category", style="cyan")
            table.add_column("Name", style="white")
            table.add_column("Exists", justify="center")
            table.add_column("Type", justify="center")
            table.add_column("Size", justify="right")

            for path in report.paths:
                exists_str = "[green]YES[/green]" if path.exists else "[dim]NO[/dim]"
                type_str = path.type or "-"
                size_str = self._format_size(path.size_bytes) if path.size_bytes else "-"

                table.add_row(
                    path.category,
                    path.name,
                    exists_str,
                    type_str,
                    size_str,
                )
            temp_console.print(table)

        return string_io.getvalue()

    def format_deduplication_report(self, report: DeduplicationReport) -> str:
        """Format deduplication report as Rich tables."""
        from io import StringIO
        string_io = StringIO()
        temp_console = Console(file=string_io, force_terminal=True, width=120, legacy_windows=False)

        # Header
        header = (
            f"[cyan]Total File Contents:[/cyan] {report.total_file_contents}\n"
            f"[cyan]Unique Hashes:[/cyan] {report.unique_hashes}\n"
            f"[cyan]Total References:[/cyan] {report.total_references}\n\n"
            f"[cyan]Storage Used:[/cyan] {self._format_size(report.total_size_bytes)}\n"
            f"[cyan]Without Dedup:[/cyan] {self._format_size(report.deduplicated_size_bytes)}\n"
            f"[green]Savings:[/green] {self._format_size(report.savings_bytes)} ({report.savings_percent:.1f}%)"
        )

        panel = Panel(header, title="Deduplication Report", border_style="green")
        temp_console.print(panel)

        # Most referenced files
        if report.most_referenced:
            temp_console.print("\n[bold green]Most Referenced Files[/bold green]\n")
            table = Table(show_header=True, header_style="bold green", box=box.ROUNDED)
            table.add_column("Content Hash", style="dim")
            table.add_column("Type", style="white")
            table.add_column("Size", justify="right")
            table.add_column("References", justify="right", style="green")

            for item in report.most_referenced:
                table.add_row(
                    item["content_hash"],
                    item["content_type"],
                    self._format_size(item["size_bytes"]),
                    str(item["reference_count"]),
                )
            temp_console.print(table)

        return string_io.getvalue()

    @staticmethod
    def _format_size(size_bytes: int | None) -> str:
        """Format bytes as human-readable size."""
        if size_bytes is None:
            return "-"
        if size_bytes < 1024:
            return f"{size_bytes}B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f}KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f}MB"

    @staticmethod
    def _format_size_delta(delta: int | None) -> str:
        """Format size delta with +/- sign."""
        if delta is None or delta == 0:
            return "0"
        sign = "+" if delta > 0 else ""
        if abs(delta) < 1024:
            return f"{sign}{delta}B"
        elif abs(delta) < 1024 * 1024:
            return f"{sign}{delta / 1024:.1f}KB"
        else:
            return f"{sign}{delta / (1024 * 1024):.1f}MB"

    @staticmethod
    def _format_time(dt) -> str:
        """Format datetime."""
        if dt is None:
            return "-"
        return dt.strftime("%Y-%m-%d %H:%M:%S")


class JSONFormatter(ReportFormatter):
    """Format reports as JSON."""

    def format_change_report(self, report: ChangeDetectionReport) -> str:
        """Format change report as JSON."""
        return json.dumps(report.model_dump(), indent=2, default=str)

    def format_snapshot_report(self, report: SnapshotSummaryReport) -> str:
        """Format snapshot summary as JSON."""
        return json.dumps(report.model_dump(), indent=2, default=str)

    def format_deduplication_report(self, report: DeduplicationReport) -> str:
        """Format deduplication report as JSON."""
        return json.dumps(report.model_dump(), indent=2, default=str)


class HTMLFormatter(ReportFormatter):
    """Format reports as HTML."""

    def format_change_report(self, report: ChangeDetectionReport) -> str:
        """Format change report as HTML."""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Change Detection Report - Snapshot {report.snapshot_id}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }}
        h1 {{ color: #333; }}
        .meta {{ background: #e3f2fd; padding: 15px; border-radius: 4px; margin-bottom: 20px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th {{ background: #1976d2; color: white; padding: 10px; text-align: left; }}
        td {{ padding: 8px; border-bottom: 1px solid #ddd; }}
        tr:hover {{ background: #f5f5f5; }}
        .added {{ color: #2e7d32; }}
        .modified {{ color: #f57c00; }}
        .deleted {{ color: #c62828; }}
        .section {{ margin: 30px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Change Detection Report</h1>
        <div class="meta">
            <p><strong>Current Snapshot:</strong> {report.snapshot_id} ({report.snapshot_time})</p>
            <p><strong>Previous Snapshot:</strong> {report.previous_snapshot_id} ({report.previous_snapshot_time})</p>
            <p><strong>Total Changes:</strong> {report.total_changes}</p>
            <p><strong>Size Change:</strong> {self._format_size_delta_html(report.size_change_bytes)}</p>
        </div>
"""

        if report.added_files:
            html += '<div class="section"><h2 class="added">Added Files</h2><table><tr><th>Path</th><th>Size</th></tr>'
            for file in report.added_files:
                html += f'<tr><td>{file.path_template}</td><td>{self._format_size_html(file.new_size_bytes)}</td></tr>'
            html += '</table></div>'

        if report.modified_files:
            html += '<div class="section"><h2 class="modified">Modified Files</h2><table><tr><th>Path</th><th>Old Size</th><th>New Size</th><th>Delta</th></tr>'
            for file in report.modified_files:
                html += f'<tr><td>{file.path_template}</td><td>{self._format_size_html(file.old_size_bytes)}</td><td>{self._format_size_html(file.new_size_bytes)}</td><td>{self._format_size_delta_html(file.size_delta)}</td></tr>'
            html += '</table></div>'

        if report.deleted_files:
            html += '<div class="section"><h2 class="deleted">Deleted Files</h2><table><tr><th>Path</th><th>Size</th></tr>'
            for file in report.deleted_files:
                html += f'<tr><td>{file.path_template}</td><td>{self._format_size_html(file.old_size_bytes)}</td></tr>'
            html += '</table></div>'

        html += '</div></body></html>'
        return html

    def format_snapshot_report(self, report: SnapshotSummaryReport) -> str:
        """Format snapshot summary as HTML."""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Snapshot Summary - {report.snapshot_id}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }}
        h1 {{ color: #333; }}
        .meta {{ background: #e3f2fd; padding: 15px; border-radius: 4px; margin-bottom: 20px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th {{ background: #1976d2; color: white; padding: 10px; text-align: left; }}
        td {{ padding: 8px; border-bottom: 1px solid #ddd; }}
        tr:hover {{ background: #f5f5f5; }}
        .section {{ margin: 30px 0; }}
        .exists {{ color: #2e7d32; }}
        .missing {{ color: #999; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Snapshot Summary</h1>
        <div class="meta">
            <p><strong>Snapshot ID:</strong> {report.snapshot_id}</p>
            <p><strong>Time:</strong> {report.snapshot_time}</p>
            <p><strong>Hash:</strong> {report.snapshot_hash[:16]}...</p>
            <p><strong>Trigger:</strong> {report.trigger_type} by {report.triggered_by or 'N/A'}</p>
            <p><strong>Total Size:</strong> {self._format_size_html(report.total_size_bytes)}</p>
            <p><strong>Files Found:</strong> {report.files_found} files, {report.directories_found} directories</p>
            <p><strong>Deduplication:</strong> {report.deduplication_percent:.1f}% savings</p>
        </div>

        <div class="section">
            <h2>Category Breakdown</h2>
            <table>
                <tr><th>Category</th><th>Found</th><th>Missing</th><th>Total</th><th>Size</th></tr>
"""
        for cat in report.category_stats:
            html += f'<tr><td>{cat.category}</td><td class="exists">{cat.found}</td><td class="missing">{cat.missing}</td><td>{cat.total_locations}</td><td>{self._format_size_html(cat.total_size_bytes)}</td></tr>'

        html += '</table></div></div></body></html>'
        return html

    def format_deduplication_report(self, report: DeduplicationReport) -> str:
        """Format deduplication report as HTML."""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Deduplication Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }}
        h1 {{ color: #333; }}
        .meta {{ background: #e8f5e9; padding: 15px; border-radius: 4px; margin-bottom: 20px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th {{ background: #2e7d32; color: white; padding: 10px; text-align: left; }}
        td {{ padding: 8px; border-bottom: 1px solid #ddd; }}
        tr:hover {{ background: #f5f5f5; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Deduplication Report</h1>
        <div class="meta">
            <p><strong>Total File Contents:</strong> {report.total_file_contents}</p>
            <p><strong>Unique Hashes:</strong> {report.unique_hashes}</p>
            <p><strong>Total References:</strong> {report.total_references}</p>
            <p><strong>Storage Used:</strong> {self._format_size_html(report.total_size_bytes)}</p>
            <p><strong>Without Deduplication:</strong> {self._format_size_html(report.deduplicated_size_bytes)}</p>
            <p><strong>Savings:</strong> {self._format_size_html(report.savings_bytes)} ({report.savings_percent:.1f}%)</p>
        </div>
    </div>
</body>
</html>
"""
        return html

    @staticmethod
    def _format_size_html(size_bytes: int | None) -> str:
        """Format bytes as human-readable size for HTML."""
        if size_bytes is None:
            return "-"
        if size_bytes < 1024:
            return f"{size_bytes}B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f}KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f}MB"

    @staticmethod
    def _format_size_delta_html(delta: int | None) -> str:
        """Format size delta with +/- sign for HTML."""
        if delta is None or delta == 0:
            return "0"
        sign = "+" if delta > 0 else ""
        if abs(delta) < 1024:
            return f"{sign}{delta}B"
        elif abs(delta) < 1024 * 1024:
            return f"{sign}{delta / 1024:.1f}KB"
        else:
            return f"{sign}{delta / (1024 * 1024):.1f}MB"
