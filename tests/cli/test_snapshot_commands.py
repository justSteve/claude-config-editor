"""
Tests for snapshot CLI commands.

Tests create, list, show, and compare snapshot commands.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import patch, AsyncMock, Mock
from typer.testing import CliRunner

from src.cli.commands import app
from src.core.models import Snapshot, SnapshotChange, SnapshotPath
from sqlalchemy import select


class TestSnapshotCreate:
    """Tests for 'snapshot create' command."""

    @pytest.mark.asyncio
    async def test_create_snapshot_success(self, cli_runner: CliRunner, cli_db_manager, mock_scanner):
        """Test successful snapshot creation."""
        with patch("src.cli.commands.snapshot.get_initialized_database", return_value=cli_db_manager):
            with patch("src.cli.commands.snapshot.PathScanner", return_value=mock_scanner):
                result = cli_runner.invoke(app, ["snapshot", "create"])

                assert result.exit_code == 0
                assert "Snapshot created successfully" in result.output or "snapshot" in result.output.lower()

    @pytest.mark.asyncio
    async def test_create_snapshot_with_notes(self, cli_runner: CliRunner, cli_db_manager, mock_scanner):
        """Test snapshot creation with notes."""
        with patch("src.cli.commands.snapshot.get_initialized_database", return_value=cli_db_manager):
            with patch("src.cli.commands.snapshot.PathScanner", return_value=mock_scanner):
                result = cli_runner.invoke(
                    app, ["snapshot", "create", "--notes", "Test notes"]
                )

                assert result.exit_code == 0

    @pytest.mark.asyncio
    async def test_create_snapshot_with_tag(self, cli_runner: CliRunner, cli_db_manager, mock_scanner):
        """Test snapshot creation with tag."""
        with patch("src.cli.commands.snapshot.get_initialized_database", return_value=cli_db_manager):
            with patch("src.cli.commands.snapshot.PathScanner", return_value=mock_scanner):
                result = cli_runner.invoke(
                    app, ["snapshot", "create", "--tag", "v1.0.0"]
                )

                assert result.exit_code == 0
                assert "v1.0.0" in result.output or "tag" in result.output.lower()

    @pytest.mark.asyncio
    async def test_create_snapshot_verbose(self, cli_runner: CliRunner, cli_db_manager, mock_scanner):
        """Test snapshot creation with verbose output."""
        with patch("src.cli.commands.snapshot.get_initialized_database", return_value=cli_db_manager):
            with patch("src.cli.commands.snapshot.PathScanner", return_value=mock_scanner):
                result = cli_runner.invoke(
                    app, ["snapshot", "create", "--verbose"]
                )

                assert result.exit_code == 0

    @pytest.mark.asyncio
    async def test_create_snapshot_error_handling(self, cli_runner: CliRunner):
        """Test error handling during snapshot creation."""
        mock_db = AsyncMock()
        mock_db.get_session.side_effect = Exception("Database error")

        with patch("src.cli.commands.snapshot.get_initialized_database", return_value=mock_db):
            result = cli_runner.invoke(app, ["snapshot", "create"])

            # Command should handle error gracefully
            assert result.exit_code != 0 or "error" in result.output.lower()


class TestSnapshotList:
    """Tests for 'snapshot list' command."""

    @pytest.mark.asyncio
    async def test_list_snapshots_empty(self, cli_runner: CliRunner, cli_db_manager):
        """Test listing snapshots when database is empty."""
        with patch("src.cli.commands.snapshot.get_initialized_database", return_value=cli_db_manager):
            result = cli_runner.invoke(app, ["snapshot", "list"])

            assert result.exit_code == 0
            assert "no snapshots" in result.output.lower()

    @pytest.mark.asyncio
    async def test_list_snapshots_with_data(self, cli_runner: CliRunner, cli_db_manager, sample_snapshot):
        """Test listing snapshots with data."""
        with patch("src.cli.commands.snapshot.get_initialized_database", return_value=cli_db_manager):
            result = cli_runner.invoke(app, ["snapshot", "list"])

            assert result.exit_code == 0
            assert "snapshot" in result.output.lower()

    @pytest.mark.asyncio
    async def test_list_snapshots_with_limit(self, cli_runner: CliRunner, cli_db_manager, cli_session):
        """Test listing snapshots with custom limit."""
        # Create multiple snapshots
        for i in range(5):
            snapshot = Snapshot(
                snapshot_hash=f"hash{i}",
                snapshot_time=datetime.now(timezone.utc),
                os_type="Windows",
                os_version="10.0",
                username="test",
                trigger_type="manual",
                triggered_by="test",
                total_locations=1,
                files_found=1,
                directories_found=0,

                total_size_bytes=1000,
            )
            cli_session.add(snapshot)

        await cli_session.commit()

        with patch("src.cli.commands.snapshot.get_initialized_database", return_value=cli_db_manager):
            result = cli_runner.invoke(app, ["snapshot", "list", "--limit", "3"])

            assert result.exit_code == 0

    @pytest.mark.asyncio
    async def test_list_snapshots_verbose(self, cli_runner: CliRunner, cli_db_manager, sample_snapshot):
        """Test listing snapshots with verbose output."""
        with patch("src.cli.commands.snapshot.get_initialized_database", return_value=cli_db_manager):
            result = cli_runner.invoke(app, ["snapshot", "list", "--verbose"])

            assert result.exit_code == 0


class TestSnapshotShow:
    """Tests for 'snapshot show' command."""

    @pytest.mark.asyncio
    async def test_show_snapshot_success(self, cli_runner: CliRunner, cli_db_manager, sample_snapshot):
        """Test showing snapshot details."""
        with patch("src.cli.commands.snapshot.get_initialized_database", return_value=cli_db_manager):
            result = cli_runner.invoke(
                app, ["snapshot", "show", str(sample_snapshot.id)]
            )

            assert result.exit_code == 0
            assert str(sample_snapshot.id) in result.output or "snapshot" in result.output.lower()

    @pytest.mark.asyncio
    async def test_show_snapshot_not_found(self, cli_runner: CliRunner, cli_db_manager):
        """Test showing non-existent snapshot."""
        with patch("src.cli.commands.snapshot.get_initialized_database", return_value=cli_db_manager):
            result = cli_runner.invoke(app, ["snapshot", "show", "999"])

            assert result.exit_code == 0  # Command succeeds but shows error message
            assert "not found" in result.output.lower()

    @pytest.mark.asyncio
    async def test_show_snapshot_with_paths(self, cli_runner: CliRunner, cli_db_manager, sample_snapshot, cli_session):
        """Test showing snapshot with paths."""
        # Add some paths
        path = SnapshotPath(
            snapshot_id=sample_snapshot.id,
            category="settings",
            name="test_file",
            path_template="%APPDATA%/test",
            resolved_path="C:/Users/test/AppData/Roaming/test",
            exists=True,
            type="file",
            size_bytes=1024,
        )
        cli_session.add(path)
        await cli_session.commit()

        with patch("src.cli.commands.snapshot.get_initialized_database", return_value=cli_db_manager):
            result = cli_runner.invoke(
                app, ["snapshot", "show", str(sample_snapshot.id), "--paths"]
            )

            assert result.exit_code == 0
            assert "paths" in result.output.lower() or "test_file" in result.output

    @pytest.mark.asyncio
    async def test_show_snapshot_with_changes(self, cli_runner: CliRunner, cli_db_manager, cli_session):
        """Test showing snapshot with changes."""
        # Create two snapshots
        snapshot1 = Snapshot(
            snapshot_hash="hash1",
            snapshot_time=datetime.now(timezone.utc),
            os_type="Windows",
            os_version="10.0",
            username="test",
            trigger_type="manual",
            triggered_by="test",
            total_locations=1,
            files_found=1,
            directories_found=0,

            total_size_bytes=1000,
        )
        cli_session.add(snapshot1)
        await cli_session.commit()
        await cli_session.refresh(snapshot1)

        snapshot2 = Snapshot(
            snapshot_hash="hash2",
            snapshot_time=datetime.now(timezone.utc),
            os_type="Windows",
            os_version="10.0",
            username="test",
            trigger_type="manual",
            triggered_by="test",
            total_locations=1,
            files_found=1,
            directories_found=0,

            total_size_bytes=1000,
            changed_from_previous=1,
        )
        cli_session.add(snapshot2)
        await cli_session.commit()
        await cli_session.refresh(snapshot2)

        # Add a change
        change = SnapshotChange(
            snapshot_id=snapshot2.id,
            previous_snapshot_id=snapshot1.id,
            change_type="modified",
            path_template="%APPDATA%/test",
            old_content_hash="oldhash",
            new_content_hash="newhash",
            old_size_bytes=1000,
            new_size_bytes=1500,
        )
        cli_session.add(change)
        await cli_session.commit()

        with patch("src.cli.commands.snapshot.get_initialized_database", return_value=cli_db_manager):
            result = cli_runner.invoke(
                app, ["snapshot", "show", str(snapshot2.id), "--changes"]
            )

            assert result.exit_code == 0

    @pytest.mark.asyncio
    async def test_show_snapshot_invalid_id(self, cli_runner: CliRunner):
        """Test showing snapshot with invalid ID."""
        result = cli_runner.invoke(app, ["snapshot", "show", "-1"])

        # Should fail validation or show error
        assert result.exit_code != 0 or "invalid" in result.output.lower() or "error" in result.output.lower()

    @pytest.mark.asyncio
    async def test_show_snapshot_verbose(self, cli_runner: CliRunner, cli_db_manager, sample_snapshot):
        """Test showing snapshot with verbose output."""
        with patch("src.cli.commands.snapshot.get_initialized_database", return_value=cli_db_manager):
            result = cli_runner.invoke(
                app, ["snapshot", "show", str(sample_snapshot.id), "--verbose"]
            )

            assert result.exit_code == 0


class TestSnapshotCompare:
    """Tests for 'snapshot compare' command."""

    @pytest.mark.asyncio
    async def test_compare_snapshots_success(self, cli_runner: CliRunner, cli_db_manager, cli_session):
        """Test comparing two snapshots."""
        # Create two snapshots
        snapshot1 = Snapshot(
            snapshot_hash="hash1",
            snapshot_time=datetime.now(timezone.utc),
            os_type="Windows",
            os_version="10.0",
            username="test",
            trigger_type="manual",
            triggered_by="test",
            total_locations=1,
            files_found=1,
            directories_found=0,

            total_size_bytes=1000,
        )
        cli_session.add(snapshot1)
        await cli_session.commit()
        await cli_session.refresh(snapshot1)

        snapshot2 = Snapshot(
            snapshot_hash="hash2",
            snapshot_time=datetime.now(timezone.utc),
            os_type="Windows",
            os_version="10.0",
            username="test",
            trigger_type="manual",
            triggered_by="test",
            total_locations=1,
            files_found=1,
            directories_found=0,

            total_size_bytes=1000,
            changed_from_previous=1,
        )
        cli_session.add(snapshot2)
        await cli_session.commit()
        await cli_session.refresh(snapshot2)

        # Add a change
        change = SnapshotChange(
            snapshot_id=snapshot2.id,
            previous_snapshot_id=snapshot1.id,
            change_type="modified",
            path_template="%APPDATA%/test",
            old_content_hash="oldhash",
            new_content_hash="newhash",
        )
        cli_session.add(change)
        await cli_session.commit()

        with patch("src.cli.commands.snapshot.get_initialized_database", return_value=cli_db_manager):
            result = cli_runner.invoke(
                app, ["snapshot", "compare", str(snapshot2.id)]
            )

            assert result.exit_code == 0
            assert "comparing" in result.output.lower() or "changes" in result.output.lower()

    @pytest.mark.asyncio
    async def test_compare_snapshots_explicit_previous(self, cli_runner: CliRunner, cli_db_manager, cli_session):
        """Test comparing snapshots with explicit previous ID."""
        # Create two snapshots
        snapshot1 = Snapshot(
            snapshot_hash="hash1",
            snapshot_time=datetime.now(timezone.utc),
            os_type="Windows",
            os_version="10.0",
            username="test",
            trigger_type="manual",
            triggered_by="test",
            total_locations=1,
            files_found=1,
            directories_found=0,

            total_size_bytes=1000,
        )
        cli_session.add(snapshot1)
        await cli_session.commit()
        await cli_session.refresh(snapshot1)

        snapshot2 = Snapshot(
            snapshot_hash="hash2",
            snapshot_time=datetime.now(timezone.utc),
            os_type="Windows",
            os_version="10.0",
            username="test",
            trigger_type="manual",
            triggered_by="test",
            total_locations=1,
            files_found=1,
            directories_found=0,

            total_size_bytes=1000,
        )
        cli_session.add(snapshot2)
        await cli_session.commit()
        await cli_session.refresh(snapshot2)

        with patch("src.cli.commands.snapshot.get_initialized_database", return_value=cli_db_manager):
            result = cli_runner.invoke(
                app,
                ["snapshot", "compare", str(snapshot2.id), "--previous", str(snapshot1.id)],
            )

            assert result.exit_code == 0

    @pytest.mark.asyncio
    async def test_compare_snapshots_no_changes(self, cli_runner: CliRunner, cli_db_manager, cli_session):
        """Test comparing snapshots with no changes."""
        # Create two snapshots
        snapshot1 = Snapshot(
            snapshot_hash="hash1",
            snapshot_time=datetime.now(timezone.utc),
            os_type="Windows",
            os_version="10.0",
            username="test",
            trigger_type="manual",
            triggered_by="test",
            total_locations=1,
            files_found=1,
            directories_found=0,

            total_size_bytes=1000,
        )
        cli_session.add(snapshot1)
        await cli_session.commit()
        await cli_session.refresh(snapshot1)

        snapshot2 = Snapshot(
            snapshot_hash="hash1_no_change",  # Different hash but represents same state
            snapshot_time=datetime.now(timezone.utc),
            os_type="Windows",
            os_version="10.0",
            username="test",
            trigger_type="manual",
            triggered_by="test",
            total_locations=1,
            files_found=1,
            directories_found=0,

            total_size_bytes=1000,
            changed_from_previous=0,
        )
        cli_session.add(snapshot2)
        await cli_session.commit()
        await cli_session.refresh(snapshot2)

        with patch("src.cli.commands.snapshot.get_initialized_database", return_value=cli_db_manager):
            result = cli_runner.invoke(
                app, ["snapshot", "compare", str(snapshot2.id)]
            )

            assert result.exit_code == 0
            assert "no changes" in result.output.lower()

    @pytest.mark.asyncio
    async def test_compare_snapshots_not_found(self, cli_runner: CliRunner, cli_db_manager):
        """Test comparing non-existent snapshots."""
        with patch("src.cli.commands.snapshot.get_initialized_database", return_value=cli_db_manager):
            result = cli_runner.invoke(app, ["snapshot", "compare", "999"])

            assert result.exit_code == 0
            assert "not found" in result.output.lower()

    @pytest.mark.asyncio
    async def test_compare_snapshots_no_previous(self, cli_runner: CliRunner, cli_db_manager, cli_session):
        """Test comparing when no previous snapshot exists."""
        snapshot = Snapshot(
            snapshot_hash="hash1",
            snapshot_time=datetime.now(timezone.utc),
            os_type="Windows",
            os_version="10.0",
            username="test",
            trigger_type="manual",
            triggered_by="test",
            total_locations=1,
            files_found=1,
            directories_found=0,

            total_size_bytes=1000,
        )
        cli_session.add(snapshot)
        await cli_session.commit()
        await cli_session.refresh(snapshot)

        with patch("src.cli.commands.snapshot.get_initialized_database", return_value=cli_db_manager):
            result = cli_runner.invoke(
                app, ["snapshot", "compare", str(snapshot.id)]
            )

            assert result.exit_code == 0
            assert "no previous" in result.output.lower() or "not found" in result.output.lower()

    @pytest.mark.asyncio
    async def test_compare_snapshots_verbose(self, cli_runner: CliRunner, cli_db_manager, cli_session):
        """Test comparing snapshots with verbose output."""
        # Create two snapshots
        snapshot1 = Snapshot(
            snapshot_hash="hash1",
            snapshot_time=datetime.now(timezone.utc),
            os_type="Windows",
            os_version="10.0",
            username="test",
            trigger_type="manual",
            triggered_by="test",
            total_locations=1,
            files_found=1,
            directories_found=0,

            total_size_bytes=1000,
        )
        cli_session.add(snapshot1)
        await cli_session.commit()
        await cli_session.refresh(snapshot1)

        snapshot2 = Snapshot(
            snapshot_hash="hash2",
            snapshot_time=datetime.now(timezone.utc),
            os_type="Windows",
            os_version="10.0",
            username="test",
            trigger_type="manual",
            triggered_by="test",
            total_locations=1,
            files_found=1,
            directories_found=0,

            total_size_bytes=1000,
        )
        cli_session.add(snapshot2)
        await cli_session.commit()
        await cli_session.refresh(snapshot2)

        with patch("src.cli.commands.snapshot.get_initialized_database", return_value=cli_db_manager):
            result = cli_runner.invoke(
                app,
                ["snapshot", "compare", str(snapshot2.id), "--verbose"],
            )

            assert result.exit_code == 0
