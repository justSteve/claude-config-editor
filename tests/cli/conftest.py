"""
Pytest configuration and fixtures for CLI tests.

Provides fixtures for CLI testing with Typer, including mock database,
test runners, and common test data.
"""

import pytest
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import Mock, AsyncMock, patch
from typer.testing import CliRunner

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from src.core.database import DatabaseManager
from src.core.models import Base, Snapshot
from src.cli.commands import app


@pytest.fixture(scope="function")
def cli_runner() -> Generator[CliRunner, None, None]:
    """
    Create a Typer CLI test runner.

    Provides a test runner for invoking CLI commands and capturing output.
    """
    yield CliRunner()


@pytest.fixture(scope="function")
async def cli_db_manager(tmp_path: Path) -> AsyncGenerator[DatabaseManager, None]:
    """
    Create a test database manager for CLI tests.

    Uses a temporary file database that persists across CLI command invocations
    but is cleaned up after the test.
    """
    # Use temporary file database
    db_path = tmp_path / "cli_test.db"
    database_url = f"sqlite+aiosqlite:///{db_path}"

    db_manager = DatabaseManager(database_url, echo=False)
    await db_manager.initialize()

    yield db_manager

    await db_manager.close()


@pytest.fixture(scope="function")
async def cli_session(cli_db_manager: DatabaseManager) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a test database session for CLI tests.

    Provides a database session for setting up test data.
    """
    async with cli_db_manager.get_session() as session:
        yield session


@pytest.fixture(scope="function")
async def sample_snapshot(cli_session: AsyncSession) -> Snapshot:
    """
    Create a sample snapshot for testing.

    Returns a snapshot with minimal data for testing snapshot-related commands.
    """
    from datetime import datetime, timezone

    snapshot = Snapshot(
        snapshot_hash="abc123def456",
        snapshot_time=datetime.now(timezone.utc),
        os_type="Windows",
        os_version="10.0.19045",
        username="test_user",
        trigger_type="manual",
        triggered_by="test",
        total_locations=10,
        files_found=5,
        directories_found=2,
        total_size_bytes=1024000,
        notes="Test snapshot",
    )

    cli_session.add(snapshot)
    await cli_session.commit()
    await cli_session.refresh(snapshot)

    return snapshot


@pytest.fixture(scope="function")
def mock_database_url(tmp_path: Path) -> str:
    """
    Provide a temporary database URL for CLI tests.

    Returns a database URL that can be used to mock the configuration.
    """
    db_path = tmp_path / "mock_cli.db"
    return f"sqlite+aiosqlite:///{db_path}"


@pytest.fixture(scope="function")
def mock_scanner():
    """
    Create a mock PathScanner for testing without actual file scanning.

    Provides a mock scanner that returns predefined results instead of
    scanning the filesystem.
    """
    scanner = AsyncMock()

    # Mock create_snapshot to return a snapshot object
    async def mock_create_snapshot(*args, **kwargs):
        from datetime import datetime, timezone
        return Snapshot(
            id=1,
            snapshot_hash="mock123",
            snapshot_time=datetime.now(timezone.utc),
            os_type="Windows",
            os_version="10.0.19045",
            username="mock_user",
            trigger_type=kwargs.get("trigger_type", "manual"),
            triggered_by=kwargs.get("triggered_by", "test"),
            total_locations=5,
            files_found=3,
            directories_found=1,
            total_size_bytes=5000,
            notes=kwargs.get("notes"),
        )

    scanner.create_snapshot = mock_create_snapshot
    scanner.get_path_definitions = Mock(return_value=[])

    return scanner


@pytest.fixture(scope="function")
def mock_settings(tmp_path: Path):
    """
    Create mock settings for CLI tests.

    Provides a settings object with test-appropriate values.
    """
    settings = Mock()
    settings.database_url = f"sqlite+aiosqlite:///{tmp_path}/test.db"
    settings.environment = "test"
    settings.log_level = "INFO"
    settings.log_file = str(tmp_path / "test.log")

    return settings


@pytest.fixture(scope="function")
def env_vars(tmp_path: Path, monkeypatch):
    """
    Set up environment variables for CLI tests.

    Configures environment variables to use test-specific paths and settings.
    """
    test_data_dir = tmp_path / "data"
    test_data_dir.mkdir()

    test_db = test_data_dir / "test.db"

    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{test_db}")
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("LOG_LEVEL", "ERROR")  # Reduce noise in tests

    return {
        "DATABASE_URL": f"sqlite+aiosqlite:///{test_db}",
        "ENVIRONMENT": "test",
        "LOG_LEVEL": "ERROR",
    }
