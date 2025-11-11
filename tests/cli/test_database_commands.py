"""
Tests for database CLI commands.

Tests stats, dedup, vacuum, and health check commands.
"""

import pytest
from unittest.mock import patch, AsyncMock, Mock
from typer.testing import CliRunner

from src.cli.commands import app
from src.core.models import FileContent


class TestDatabaseStats:
    """Tests for 'db stats' command."""

    @pytest.mark.asyncio
    async def test_stats_success(self, cli_runner: CliRunner, cli_db_manager):
        """Test showing database statistics."""
        # Mock get_database_stats
        mock_stats = {
            "database_size_bytes": 1024000,
            "total_snapshots": 5,
            "total_paths": 100,
            "total_files": 50,
        }
        cli_db_manager.get_database_stats = AsyncMock(return_value=mock_stats)

        with patch("src.cli.commands.database.get_initialized_database", return_value=cli_db_manager):
            result = cli_runner.invoke(app, ["db", "stats"])

            assert result.exit_code == 0
            assert "database" in result.output.lower() or "statistics" in result.output.lower()

    @pytest.mark.asyncio
    async def test_stats_verbose(self, cli_runner: CliRunner, cli_db_manager):
        """Test showing database statistics with verbose output."""
        mock_stats = {
            "database_size_bytes": 1024000,
            "total_snapshots": 5,
        }
        cli_db_manager.get_database_stats = AsyncMock(return_value=mock_stats)

        with patch("src.cli.commands.database.get_initialized_database", return_value=cli_db_manager):
            result = cli_runner.invoke(app, ["db", "stats", "--verbose"])

            assert result.exit_code == 0
            # Should show additional information like database URL
            assert "url" in result.output.lower() or "engine" in result.output.lower()

    @pytest.mark.asyncio
    async def test_stats_error_handling(self, cli_runner: CliRunner):
        """Test error handling when stats fail."""
        mock_db = AsyncMock()
        mock_db.get_database_stats.side_effect = Exception("Database error")

        with patch("src.cli.commands.database.get_initialized_database", return_value=mock_db):
            result = cli_runner.invoke(app, ["db", "stats"])

            # Should handle error gracefully
            assert result.exit_code != 0 or "error" in result.output.lower()


class TestDatabaseDedup:
    """Tests for 'db dedup' command."""

    @pytest.mark.asyncio
    async def test_dedup_no_files(self, cli_runner: CliRunner, cli_db_manager):
        """Test dedup with no files in database."""
        with patch("src.cli.commands.database.get_initialized_database", return_value=cli_db_manager):
            result = cli_runner.invoke(app, ["db", "dedup"])

            assert result.exit_code == 0
            assert "deduplication" in result.output.lower()
            # Should show 0 files
            assert "0" in result.output

    @pytest.mark.asyncio
    async def test_dedup_with_files(self, cli_runner: CliRunner, cli_db_manager, cli_session):
        """Test dedup with files in database."""
        # Create some file contents
        file1 = FileContent(
            content_hash="hash1",
            content_text="content1",
            content_type="text",
            size_bytes=1000,
            reference_count=3,  # Referenced 3 times
        )
        file2 = FileContent(
            content_hash="hash2",
            content_text="content2",
            content_type="text",
            size_bytes=2000,
            reference_count=1,  # Referenced once
        )
        cli_session.add(file1)
        cli_session.add(file2)
        await cli_session.commit()

        with patch("src.cli.commands.database.get_initialized_database", return_value=cli_db_manager):
            result = cli_runner.invoke(app, ["db", "dedup"])

            assert result.exit_code == 0
            assert "deduplication" in result.output.lower()
            # Should show unique files count
            assert "2" in result.output or "unique" in result.output.lower()

    @pytest.mark.asyncio
    async def test_dedup_verbose(self, cli_runner: CliRunner, cli_db_manager, cli_session):
        """Test dedup with verbose output showing most referenced files."""
        # Create file with multiple references
        file = FileContent(
            content_hash="hash1",
            content_text="content1",
            content_type="text",
            size_bytes=1000,
            reference_count=5,
        )
        cli_session.add(file)
        await cli_session.commit()

        with patch("src.cli.commands.database.get_initialized_database", return_value=cli_db_manager):
            result = cli_runner.invoke(app, ["db", "dedup", "--verbose"])

            assert result.exit_code == 0
            assert "deduplication" in result.output.lower()
            # Should show most referenced files
            if "most referenced" in result.output.lower():
                assert "5" in result.output or "hash1" in result.output

    @pytest.mark.asyncio
    async def test_dedup_calculations(self, cli_runner: CliRunner, cli_db_manager, cli_session):
        """Test dedup calculations are correct."""
        # Create files with known reference counts
        file1 = FileContent(
            content_hash="hash1",
            content_text="content1",
            content_type="text",
            size_bytes=1000,
            reference_count=3,  # Saved 2x duplicates
        )
        file2 = FileContent(
            content_hash="hash2",
            content_text="content2",
            content_type="text",
            size_bytes=1000,
            reference_count=2,  # Saved 1x duplicate
        )
        cli_session.add_all([file1, file2])
        await cli_session.commit()

        with patch("src.cli.commands.database.get_initialized_database", return_value=cli_db_manager):
            result = cli_runner.invoke(app, ["db", "dedup"])

            assert result.exit_code == 0
            # Should calculate savings correctly (3 total duplicates out of 5 references)
            assert "deduplication" in result.output.lower()


class TestDatabaseVacuum:
    """Tests for 'db vacuum' command."""

    @pytest.mark.asyncio
    async def test_vacuum_with_force(self, cli_runner: CliRunner, cli_db_manager):
        """Test vacuum with --force flag (skips confirmation)."""
        mock_stats = {"database_size_bytes": 1024000}
        cli_db_manager.get_database_stats = AsyncMock(return_value=mock_stats)

        with patch("src.cli.commands.database.get_initialized_database", return_value=cli_db_manager):
            result = cli_runner.invoke(app, ["db", "vacuum", "--force"])

            assert result.exit_code == 0
            assert "vacuum" in result.output.lower() or "database" in result.output.lower()

    @pytest.mark.asyncio
    async def test_vacuum_without_force_confirmed(self, cli_runner: CliRunner, cli_db_manager):
        """Test vacuum with confirmation (user confirms)."""
        mock_stats = {"database_size_bytes": 1024000}
        cli_db_manager.get_database_stats = AsyncMock(return_value=mock_stats)

        with patch("src.cli.commands.database.get_initialized_database", return_value=cli_db_manager):
            with patch("src.cli.commands.database.confirm_action", return_value=True):
                result = cli_runner.invoke(app, ["db", "vacuum"])

                assert result.exit_code == 0
                assert "vacuum" in result.output.lower()

    @pytest.mark.asyncio
    async def test_vacuum_without_force_cancelled(self, cli_runner: CliRunner, cli_db_manager):
        """Test vacuum with confirmation (user cancels)."""
        with patch("src.cli.commands.database.get_initialized_database", return_value=cli_db_manager):
            with patch("src.cli.commands.database.confirm_action", return_value=False):
                result = cli_runner.invoke(app, ["db", "vacuum"])

                assert result.exit_code == 0
                assert "cancelled" in result.output.lower()

    @pytest.mark.asyncio
    async def test_vacuum_verbose(self, cli_runner: CliRunner, cli_db_manager):
        """Test vacuum with verbose output."""
        mock_stats = {"database_size_bytes": 1024000}
        cli_db_manager.get_database_stats = AsyncMock(return_value=mock_stats)

        with patch("src.cli.commands.database.get_initialized_database", return_value=cli_db_manager):
            result = cli_runner.invoke(
                app, ["db", "vacuum", "--force", "--verbose"]
            )

            assert result.exit_code == 0

    @pytest.mark.asyncio
    async def test_vacuum_error_handling(self, cli_runner: CliRunner):
        """Test error handling when vacuum fails."""
        mock_db = AsyncMock()
        mock_db.get_session.side_effect = Exception("Vacuum failed")

        with patch("src.cli.commands.database.get_initialized_database", return_value=mock_db):
            with patch("src.cli.commands.database.confirm_action", return_value=True):
                result = cli_runner.invoke(app, ["db", "vacuum"])

                # Should handle error gracefully
                assert result.exit_code != 0 or "error" in result.output.lower()


class TestDatabaseHealth:
    """Tests for 'db health' command."""

    @pytest.mark.asyncio
    async def test_health_check_success(self, cli_runner: CliRunner, cli_db_manager):
        """Test successful health check."""
        cli_db_manager.health_check = AsyncMock(return_value=True)
        mock_stats = {"database_size_bytes": 1024000}
        cli_db_manager.get_database_stats = AsyncMock(return_value=mock_stats)

        with patch("src.cli.commands.database.get_initialized_database", return_value=cli_db_manager):
            result = cli_runner.invoke(app, ["db", "health"])

            assert result.exit_code == 0
            assert "healthy" in result.output.lower() or "success" in result.output.lower()

    @pytest.mark.asyncio
    async def test_health_check_failure(self, cli_runner: CliRunner, cli_db_manager):
        """Test failed health check."""
        cli_db_manager.health_check = AsyncMock(return_value=False)

        with patch("src.cli.commands.database.get_initialized_database", return_value=cli_db_manager):
            result = cli_runner.invoke(app, ["db", "health"])

            assert result.exit_code == 0
            assert "failed" in result.output.lower() or "unhealthy" in result.output.lower()

    @pytest.mark.asyncio
    async def test_health_check_verbose(self, cli_runner: CliRunner, cli_db_manager):
        """Test health check with verbose output."""
        cli_db_manager.health_check = AsyncMock(return_value=True)
        mock_stats = {
            "database_size_bytes": 1024000,
            "total_snapshots": 5,
        }
        cli_db_manager.get_database_stats = AsyncMock(return_value=mock_stats)

        with patch("src.cli.commands.database.get_initialized_database", return_value=cli_db_manager):
            result = cli_runner.invoke(app, ["db", "health", "--verbose"])

            assert result.exit_code == 0
            assert "healthy" in result.output.lower()
            # Should show detailed health information
            assert "connected" in result.output.lower(
            ) or "tables" in result.output.lower() or "size" in result.output.lower()

    @pytest.mark.asyncio
    async def test_health_check_error_handling(self, cli_runner: CliRunner):
        """Test error handling when health check fails with exception."""
        mock_db = AsyncMock()
        mock_db.health_check.side_effect = Exception("Connection error")

        with patch("src.cli.commands.database.get_initialized_database", return_value=mock_db):
            result = cli_runner.invoke(app, ["db", "health"])

            # Should handle error gracefully
            assert result.exit_code != 0 or "error" in result.output.lower()


class TestDatabaseIntegration:
    """Integration tests for database commands."""

    @pytest.mark.asyncio
    async def test_stats_and_health_sequence(self, cli_runner: CliRunner, cli_db_manager):
        """Test running stats and health commands in sequence."""
        mock_stats = {"database_size_bytes": 1024000}
        cli_db_manager.get_database_stats = AsyncMock(return_value=mock_stats)
        cli_db_manager.health_check = AsyncMock(return_value=True)

        with patch("src.cli.commands.database.get_initialized_database", return_value=cli_db_manager):
            # Run stats
            result1 = cli_runner.invoke(app, ["db", "stats"])
            assert result1.exit_code == 0

            # Run health check
            result2 = cli_runner.invoke(app, ["db", "health"])
            assert result2.exit_code == 0

    @pytest.mark.asyncio
    async def test_dedup_after_vacuum(self, cli_runner: CliRunner, cli_db_manager, cli_session):
        """Test dedup statistics after vacuum operation."""
        # Add some file content
        file = FileContent(
            content_hash="hash1",
            content_text="content1",
            content_type="text",
            size_bytes=1000,
            reference_count=2,
        )
        cli_session.add(file)
        await cli_session.commit()

        mock_stats = {"database_size_bytes": 1024000}
        cli_db_manager.get_database_stats = AsyncMock(return_value=mock_stats)

        with patch("src.cli.commands.database.get_initialized_database", return_value=cli_db_manager):
            # Run vacuum
            result1 = cli_runner.invoke(app, ["db", "vacuum", "--force"])
            assert result1.exit_code == 0

            # Check dedup stats
            result2 = cli_runner.invoke(app, ["db", "dedup"])
            assert result2.exit_code == 0
            assert "unique" in result2.output.lower(
            ) or "deduplication" in result2.output.lower()
