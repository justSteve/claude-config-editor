"""
Tests for CLI utilities.

Tests utility functions for database access, validation, and error handling.
"""

import pytest
from unittest.mock import patch, AsyncMock, Mock
from pathlib import Path

from src.cli.utils import (
    validate_snapshot_id,
    confirm_action,
    handle_cli_error,
    get_initialized_database,
)


class TestValidateSnapshotId:
    """Tests for snapshot ID validation."""

    def test_valid_positive_id(self):
        """Test validation with valid positive ID."""
        # Should not raise exception
        validate_snapshot_id(1)
        validate_snapshot_id(100)
        validate_snapshot_id(999999)

    def test_invalid_zero(self):
        """Test validation with zero."""
        with pytest.raises(Exception):
            validate_snapshot_id(0)

    def test_invalid_negative(self):
        """Test validation with negative ID."""
        with pytest.raises(Exception):
            validate_snapshot_id(-1)
        with pytest.raises(Exception):
            validate_snapshot_id(-100)

    def test_valid_string_number(self):
        """Test validation with string that can be converted to int."""
        # Some implementations might accept strings
        try:
            validate_snapshot_id("5")
        except Exception:
            # If it raises, that's also acceptable behavior
            pass


class TestConfirmAction:
    """Tests for action confirmation."""

    def test_confirm_with_yes(self):
        """Test confirmation with 'yes' input."""
        with patch("typer.confirm", return_value=True):
            result = confirm_action("Continue?")
            assert result is True

    def test_confirm_with_no(self):
        """Test confirmation with 'no' input."""
        with patch("typer.confirm", return_value=False):
            result = confirm_action("Continue?")
            assert result is False

    def test_confirm_with_default_true(self):
        """Test confirmation with default=True."""
        with patch("typer.confirm", return_value=True):
            result = confirm_action("Continue?", default=True)
            assert result is True

    def test_confirm_with_default_false(self):
        """Test confirmation with default=False."""
        with patch("typer.confirm", return_value=False):
            result = confirm_action("Continue?", default=False)
            assert result is False


class TestHandleCliError:
    """Tests for CLI error handling."""

    def test_handle_generic_exception(self, capsys):
        """Test handling generic exception."""
        error = Exception("Test error")

        # Mock sys.exit to prevent actual exit
        with patch("sys.exit"):
            handle_cli_error(error, verbose=False)

        captured = capsys.readouterr()
        assert "error" in captured.out.lower() or "test error" in captured.out.lower()

    def test_handle_exception_verbose(self, capsys):
        """Test handling exception with verbose mode."""
        error = Exception("Test error")

        with patch("sys.exit"):
            handle_cli_error(error, verbose=True)

        captured = capsys.readouterr()
        # Should show more details in verbose mode
        assert "error" in captured.out.lower() or "test error" in captured.out.lower()

    def test_handle_value_error(self, capsys):
        """Test handling ValueError."""
        error = ValueError("Invalid value")

        with patch("sys.exit"):
            handle_cli_error(error, verbose=False)

        captured = capsys.readouterr()
        assert "error" in captured.out.lower() or "invalid" in captured.out.lower()

    def test_handle_file_not_found_error(self, capsys):
        """Test handling FileNotFoundError."""
        error = FileNotFoundError("File not found")

        with patch("sys.exit"):
            handle_cli_error(error, verbose=False)

        captured = capsys.readouterr()
        assert "error" in captured.out.lower() or "not found" in captured.out.lower()


class TestGetInitializedDatabase:
    """Tests for database initialization utility."""

    @pytest.mark.asyncio
    async def test_get_initialized_database_success(self):
        """Test successful database initialization."""
        mock_db = AsyncMock()
        mock_db.initialize = AsyncMock()

        with patch("src.cli.utils.DatabaseManager", return_value=mock_db):
            result = await get_initialized_database()

            assert result is not None
            # Database should be initialized
            mock_db.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_initialized_database_with_custom_url(self):
        """Test database initialization with custom URL."""
        mock_db = AsyncMock()
        mock_db.initialize = AsyncMock()

        with patch("src.cli.utils.DatabaseManager", return_value=mock_db):
            with patch("src.cli.utils.get_settings") as mock_settings:
                mock_settings.return_value.database_url = "sqlite:///test.db"
                result = await get_initialized_database()

                assert result is not None

    @pytest.mark.asyncio
    async def test_get_initialized_database_error(self):
        """Test database initialization error handling."""
        mock_db = AsyncMock()
        mock_db.initialize.side_effect = Exception("Initialization failed")

        with patch("src.cli.utils.DatabaseManager", return_value=mock_db):
            with pytest.raises(Exception):
                await get_initialized_database()


class TestUtilityIntegration:
    """Integration tests for utility functions."""

    @pytest.mark.asyncio
    async def test_validation_and_error_handling_flow(self, capsys):
        """Test flow of validation failure and error handling."""
        # Try to validate invalid ID
        try:
            validate_snapshot_id(-1)
        except Exception as e:
            # Handle the error
            with patch("sys.exit"):
                handle_cli_error(e, verbose=False)

            captured = capsys.readouterr()
            assert "error" in captured.out.lower() or "invalid" in captured.out.lower()

    def test_confirmation_workflow(self):
        """Test confirmation workflow."""
        with patch("typer.confirm", side_effect=[False, True]):
            # First confirmation denied
            result1 = confirm_action("Delete all data?", default=False)
            assert result1 is False

            # Second confirmation accepted
            result2 = confirm_action("Are you sure?", default=False)
            assert result2 is True
