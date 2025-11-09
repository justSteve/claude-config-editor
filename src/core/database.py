"""
Database manager for Claude Config version control system.

Handles database initialization, connections, and session management using
SQLAlchemy 2.0 async support with SQLite backend.
"""

import logging
from pathlib import Path
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from src.core.models import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages database connections and operations for the version control system.

    Handles:
    - Database initialization and schema creation
    - Connection pooling
    - Session management
    - SQLite-specific optimizations (WAL mode, foreign keys)
    """

    def __init__(self, database_url: str, echo: bool = False) -> None:
        """
        Initialize database manager.

        Args:
            database_url: SQLAlchemy database URL (e.g., 'sqlite+aiosqlite:///data/claude_config.db')
            echo: Whether to log SQL statements (useful for debugging)
        """
        self.database_url = database_url
        self.echo = echo
        self.engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[async_sessionmaker[AsyncSession]] = None

    async def initialize(self) -> None:
        """
        Initialize database engine and create tables if needed.

        This should be called once at application startup.
        """
        logger.info(f"Initializing database: {self.database_url}")
        logger.debug(f"Database configuration: echo={self.echo}")

        # Create engine with optimized settings for SQLite
        self.engine = create_async_engine(
            self.database_url,
            echo=self.echo,
            poolclass=NullPool,  # Use NullPool for SQLite to avoid connection issues
            connect_args={
                "check_same_thread": False,  # Allow multi-threaded access (safe with SQLite in WAL mode)
            },
        )

        # Configure SQLite-specific settings
        @event.listens_for(self.engine.sync_engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):  # type: ignore
            """Enable SQLite optimizations on each connection."""
            cursor = dbapi_conn.cursor()

            # Enable WAL mode for better concurrency
            cursor.execute("PRAGMA journal_mode=WAL")

            # Enable foreign key constraints
            cursor.execute("PRAGMA foreign_keys=ON")

            # Optimize for speed (safe for our use case)
            cursor.execute("PRAGMA synchronous=NORMAL")

            # Increase cache size to 10MB
            cursor.execute("PRAGMA cache_size=-10000")

            cursor.close()

        # Create session factory
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Ensure database directory exists
        if "sqlite" in self.database_url:
            db_path = self.database_url.split("///")[-1]
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Create all tables
        try:
            await self.create_tables()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}", exc_info=True)
            raise

    async def create_tables(self) -> None:
        """Create all database tables from models."""
        logger.info("Creating database tables...")

        if self.engine is None:
            logger.error("Database engine not initialized")
            raise RuntimeError("Database engine not initialized. Call initialize() first.")

        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}", exc_info=True)
            raise

    async def drop_tables(self) -> None:
        """
        Drop all database tables.

        WARNING: This will delete all data! Use with caution.
        """
        logger.warning("Dropping all database tables...")

        if self.engine is None:
            raise RuntimeError("Database engine not initialized. Call initialize() first.")

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

        logger.warning("All database tables dropped")

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get a database session.

        Use as an async context manager:

        ```python
        async with db.get_session() as session:
            # Use session here
            pass
        ```

        Or with dependency injection (FastAPI):

        ```python
        async def get_db() -> AsyncGenerator[AsyncSession, None]:
            async with db_manager.get_session() as session:
                yield session
        ```
        """
        if self.session_factory is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        async with self.session_factory() as session:
            try:
                yield session
            finally:
                await session.close()

    async def close(self) -> None:
        """
        Close database connections and clean up resources.

        Should be called at application shutdown.
        """
        if self.engine:
            logger.info("Closing database connections...")
            await self.engine.dispose()
            logger.info("Database connections closed")

    async def get_database_stats(self) -> dict[str, int]:
        """
        Get database statistics.

        Returns:
            Dictionary with table row counts and database size
        """
        if self.engine is None:
            logger.error("Database not initialized when getting stats")
            raise RuntimeError("Database not initialized. Call initialize() first.")

        logger.debug("Collecting database statistics")
        stats: dict[str, int] = {}

        async with self.engine.begin() as conn:
            # Get row counts for each table
            tables = [
                "snapshots",
                "snapshot_env_vars",
                "snapshot_paths",
                "file_contents",
                "json_data",
                "claude_configs",
                "mcp_servers",
                "snapshot_changes",
                "snapshot_tags",
                "annotations",
            ]

            for table in tables:
                result = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                stats[f"{table}_count"] = count or 0

            # Get database size (SQLite specific)
            if "sqlite" in self.database_url:
                result = await conn.execute(text("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()"))
                size = result.scalar()
                stats["database_size_bytes"] = size or 0

        logger.debug(f"Database statistics collected: {stats}")
        return stats

    async def vacuum(self) -> None:
        """
        Vacuum the database to reclaim space and optimize performance.

        Should be run periodically, especially after deleting snapshots.
        """
        if self.engine is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        logger.info("Vacuuming database...")

        async with self.engine.begin() as conn:
            await conn.execute(text("VACUUM"))

        logger.info("Database vacuumed successfully")

    async def health_check(self) -> bool:
        """
        Check if database is accessible and healthy.

        Returns:
            True if database is healthy, False otherwise
        """
        logger.debug("Performing database health check")
        try:
            if self.engine is None:
                logger.warning("Database health check failed: engine not initialized")
                return False

            async with self.engine.begin() as conn:
                await conn.execute(text("SELECT 1"))

            logger.debug("Database health check passed")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}", exc_info=True)
            return False


# Global database manager instance
db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """
    Get the global database manager instance.

    Raises:
        RuntimeError: If database manager not initialized
    """
    if db_manager is None:
        raise RuntimeError(
            "Database manager not initialized. "
            "Call init_database() at application startup."
        )
    return db_manager


async def init_database(database_url: str, echo: bool = False) -> DatabaseManager:
    """
    Initialize the global database manager.

    Args:
        database_url: SQLAlchemy database URL
        echo: Whether to log SQL statements

    Returns:
        Initialized DatabaseManager instance
    """
    global db_manager

    db_manager = DatabaseManager(database_url, echo=echo)
    await db_manager.initialize()

    return db_manager


async def close_database() -> None:
    """Close the global database manager."""
    global db_manager

    if db_manager:
        await db_manager.close()
        db_manager = None
