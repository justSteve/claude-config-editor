"""
Reporting module for Claude Config version control system.

Provides comprehensive reporting capabilities including:
- Change detection between snapshots
- Snapshot summaries and statistics
- Multiple output formats (CLI, JSON, HTML)
"""

from src.reports.generators import (
    ChangeDetectionReport,
    SnapshotSummaryReport,
    generate_change_report,
    generate_snapshot_report,
)
from src.reports.formatters import (
    ReportFormatter,
    CLIFormatter,
    JSONFormatter,
    HTMLFormatter,
)

__all__ = [
    "ChangeDetectionReport",
    "SnapshotSummaryReport",
    "generate_change_report",
    "generate_snapshot_report",
    "ReportFormatter",
    "CLIFormatter",
    "JSONFormatter",
    "HTMLFormatter",
]
