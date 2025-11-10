"""
Tests for CLI formatters.

Tests formatting functions for tables, panels, and output.
"""

import pytest
from datetime import datetime, timezone
from rich.table import Table
from rich.panel import Panel

from src.cli.formatters import (
    format_datetime,
    format_size,
    format_hash,
    create_snapshot_list_table,
    create_snapshot_panel,
    create_stats_table,
    print_success,
    print_error,
    print_warning,
)
from src.core.models import Snapshot


class TestFormatFunctions:
    """Tests for basic formatting functions."""

    def test_format_datetime(self):
        """Test datetime formatting."""
        dt = datetime(2025, 11, 10, 12, 30, 45, tzinfo=timezone.utc)
        result = format_datetime(dt)

        assert isinstance(result, str)
        assert "2025" in result
        assert "11" in result or "Nov" in result.lower()

    def test_format_datetime_none(self):
        """Test datetime formatting with None."""
        result = format_datetime(None)

        assert isinstance(result, str)
        assert "n/a" in result.lower() or "none" in result.lower() or result == "-"

    def test_format_size_bytes(self):
        """Test size formatting for bytes."""
        result = format_size(512)

        assert isinstance(result, str)
        assert "512" in result or "B" in result

    def test_format_size_kb(self):
        """Test size formatting for kilobytes."""
        result = format_size(2048)  # 2 KB

        assert isinstance(result, str)
        assert "KB" in result or "K" in result

    def test_format_size_mb(self):
        """Test size formatting for megabytes."""
        result = format_size(2_097_152)  # 2 MB

        assert isinstance(result, str)
        assert "MB" in result or "M" in result

    def test_format_size_gb(self):
        """Test size formatting for gigabytes."""
        result = format_size(2_147_483_648)  # 2 GB

        assert isinstance(result, str)
        assert "GB" in result or "G" in result

    def test_format_size_zero(self):
        """Test size formatting for zero."""
        result = format_size(0)

        assert isinstance(result, str)
        assert "0" in result

    def test_format_size_negative(self):
        """Test size formatting for negative values."""
        result = format_size(-1024)

        assert isinstance(result, str)
        # Should handle negative gracefully

    def test_format_hash_short(self):
        """Test hash formatting with short hash (no truncation needed)."""
        hash_value = "abc123"
        result = format_hash(hash_value, length=16)

        assert result == hash_value

    def test_format_hash_long(self):
        """Test hash formatting with long hash (truncation applied)."""
        hash_value = "abc123def456789012345678"
        result = format_hash(hash_value, length=8)

        assert isinstance(result, str)
        assert len(result) == 11  # 8 + "..." = 11
        assert result.startswith("abc123")
        assert result.endswith("...")

    def test_format_hash_default_length(self):
        """Test hash formatting with default length."""
        hash_value = "a" * 30
        result = format_hash(hash_value)  # Default length=16

        assert isinstance(result, str)
        assert len(result) == 19  # 16 + "..." = 19
        assert result.endswith("...")


class TestTableCreation:
    """Tests for table creation functions."""

    def test_create_snapshot_list_table_empty(self):
        """Test creating table with empty snapshot list."""
        result = create_snapshot_list_table([])

        assert isinstance(result, Table)

    def test_create_snapshot_list_table_with_data(self):
        """Test creating table with snapshot data."""
        snapshots = [
            Snapshot(
                id=1,
                snapshot_hash="hash1",
                snapshot_time=datetime.now(timezone.utc),
                os_type="Windows",
                os_version="10.0",
                username="test",
                trigger_type="manual",
                triggered_by="test",
                total_scanned=10,
                files_found=5,
                directories_found=2,
                missing_paths=3,
                total_size_bytes=1024,
            )
        ]

        result = create_snapshot_list_table(snapshots)

        assert isinstance(result, Table)
        # Table should have the snapshot data

    def test_create_snapshot_panel(self):
        """Test creating snapshot panel."""
        result = create_snapshot_panel(
            snapshot_id=1,
            snapshot_hash="abc123",
            snapshot_time=datetime.now(timezone.utc),
            files_found=5,
            directories_found=2,
            total_size_bytes=1024000,
            changed_from_previous=0,
        )

        assert isinstance(result, Panel)

    def test_create_snapshot_panel_with_changes(self):
        """Test creating snapshot panel with changes."""
        result = create_snapshot_panel(
            snapshot_id=2,
            snapshot_hash="def456",
            snapshot_time=datetime.now(timezone.utc),
            files_found=6,
            directories_found=2,
            total_size_bytes=2048000,
            changed_from_previous=3,
        )

        assert isinstance(result, Panel)

    def test_create_stats_table(self):
        """Test creating stats table."""
        stats = {
            "database_size_bytes": 1024000,
            "total_snapshots": 5,
            "total_paths": 100,
            "total_files": 50,
        }

        result = create_stats_table(stats)

        assert isinstance(result, Table)

    def test_create_stats_table_empty(self):
        """Test creating stats table with empty dict."""
        result = create_stats_table({})

        assert isinstance(result, Table)


class TestPrintFunctions:
    """Tests for print functions."""

    def test_print_success(self, capsys):
        """Test printing success message."""
        print_success("Operation successful")

        captured = capsys.readouterr()
        assert "operation successful" in captured.out.lower() or "success" in captured.out.lower()

    def test_print_error(self, capsys):
        """Test printing error message."""
        print_error("An error occurred")

        captured = capsys.readouterr()
        assert "error" in captured.out.lower()

    def test_print_warning(self, capsys):
        """Test printing warning message."""
        print_warning("This is a warning")

        captured = capsys.readouterr()
        assert "warning" in captured.out.lower()


class TestEdgeCases:
    """Tests for edge cases in formatters."""

    def test_format_size_very_large(self):
        """Test formatting very large sizes."""
        result = format_size(10_000_000_000_000)  # 10 TB

        assert isinstance(result, str)
        # Should handle very large sizes

    def test_format_hash_empty_string(self):
        """Test formatting empty hash."""
        result = format_hash("")

        assert isinstance(result, str)

    def test_create_table_with_many_snapshots(self):
        """Test creating table with many snapshots."""
        snapshots = []
        for i in range(100):
            snapshots.append(
                Snapshot(
                    id=i,
                    snapshot_hash=f"hash{i}",
                    snapshot_time=datetime.now(timezone.utc),
                    os_type="Windows",
                    os_version="10.0",
                    username="test",
                    trigger_type="manual",
                    triggered_by="test",
                    total_scanned=10,
                    files_found=5,
                    directories_found=2,
                    missing_paths=3,
                    total_size_bytes=1024,
                )
            )

        result = create_snapshot_list_table(snapshots)

        assert isinstance(result, Table)
        # Should handle many rows
