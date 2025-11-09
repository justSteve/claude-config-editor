"""
Pytest configuration and fixtures for database tests.

Provides fixtures for database setup, test sessions, and common test data.
"""

import pytest
import asyncio
from pathlib import Path
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from src.core.database import DatabaseManager
from src.core.models import Base


# Note: pytest-asyncio handles event loop creation automatically
# with asyncio_mode = "auto" in pytest.ini


@pytest.fixture(scope="function")
async def test_db_manager(tmp_path) -> AsyncGenerator[DatabaseManager, None]:
    """
    Create a test database manager with temporary file database.

    Uses a temporary file database for testing. Each test gets a fresh database.
    The file is automatically cleaned up after the test.
    """
    # Use temporary file database for testing (shared across connections)
    db_path = tmp_path / "test.db"
    database_url = f"sqlite+aiosqlite:///{db_path}"

    db_manager = DatabaseManager(database_url, echo=False)
    await db_manager.initialize()

    yield db_manager

    await db_manager.close()


# Note: Tables are already created by test_db_manager.initialize()
# Since we're using a temporary file database, each test gets a fresh database
# and it's automatically cleaned up when the test fixture completes


@pytest.fixture(scope="function")
async def test_session(test_db_manager: DatabaseManager) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a test database session.

    Provides a database session that is automatically rolled back after each test.
    """
    async with test_db_manager.get_session() as session:
        yield session
        await session.rollback()
