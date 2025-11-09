"""
Alembic environment configuration for async SQLAlchemy.

Note: Alembic migrations run in synchronous mode, but we convert the async
database URL to a sync one for migration purposes.
"""

from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import pool
from sqlalchemy.engine import Connection

from alembic import context

# Import models to ensure Base.metadata is populated
from src.core.models import Base  # noqa: F401

# Import settings to get database URL
from src.core.config import get_settings

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Get database URL from settings
settings = get_settings()
database_url = settings.database_url

# Convert async SQLite URL to sync for migrations
# sqlite+aiosqlite:/// becomes sqlite:///
if database_url.startswith("sqlite+aiosqlite:///"):
    database_url = database_url.replace("sqlite+aiosqlite:///", "sqlite:///")
elif database_url.startswith("sqlite+aiosqlite://"):
    database_url = database_url.replace("sqlite+aiosqlite://", "sqlite://")

# Set the database URL in the config
config.set_main_option("sqlalchemy.url", database_url)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with the given connection."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    # For SQLite, we can use sync mode which is simpler
    # Alembic doesn't fully support async migrations yet
    from sqlalchemy import create_engine

    # Ensure database directory exists
    if "sqlite" in database_url:
        db_path = database_url.replace("sqlite:///", "")
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    # Create sync engine for migrations (Alembic works better with sync)
    connectable = create_engine(
        database_url,
        poolclass=pool.NullPool,
        connect_args={"check_same_thread": False},
    )

    with connectable.connect() as connection:
        # Enable SQLite optimizations
        if "sqlite" in database_url:
            from sqlalchemy import text

            connection.execute(text("PRAGMA foreign_keys=ON"))  # type: ignore
            connection.execute(text("PRAGMA journal_mode=WAL"))  # type: ignore

        do_run_migrations(connection)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
