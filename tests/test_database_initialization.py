"""
Tests for database initialization with entity models.

Tests verify that:
- DatabaseManager creates all required tables on startup
- Entity model tables (mcp_server_snapshots, subagent_snapshots,
  slash_command_snapshots, claude_memory_snapshots) are created
- Table schemas match model definitions
- Foreign key relationships work correctly
- init_db() is idempotent (can be called multiple times safely)
"""

import pytest
from sqlalchemy import inspect, text, select
from sqlalchemy.exc import IntegrityError

from src.core.database import DatabaseManager
from src.core.models import (
    Base,
    Snapshot,
    FileContent,
    McpServerSnapshot,
    SubagentSnapshot,
    SlashCommandSnapshot,
    ClaudeMemorySnapshot,
)


class TestDatabaseInitialization:
    """Tests for database table creation on initialization."""

    async def test_entity_tables_created(self, test_db_manager: DatabaseManager):
        """Test that all 4 new entity tables are created on initialization."""
        # Get database inspector and table names in one run_sync call
        async with test_db_manager.engine.begin() as conn:
            def get_tables(sync_conn):
                inspector = inspect(sync_conn)
                return inspector.get_table_names()

            tables = await conn.run_sync(get_tables)

            # Verify all 4 entity tables exist
            assert "mcp_server_snapshots" in tables, "mcp_server_snapshots table not created"
            assert "subagent_snapshots" in tables, "subagent_snapshots table not created"
            assert "slash_command_snapshots" in tables, "slash_command_snapshots table not created"
            assert "claude_memory_snapshots" in tables, "claude_memory_snapshots table not created"

            # Verify base tables also exist
            assert "snapshots" in tables
            assert "file_contents" in tables

    async def test_all_expected_tables_created(self, test_db_manager: DatabaseManager):
        """Test that all expected tables are created."""
        expected_tables = {
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
            "mcp_server_snapshots",
            "subagent_snapshots",
            "slash_command_snapshots",
            "claude_memory_snapshots",
        }

        async with test_db_manager.engine.begin() as conn:
            def get_tables(sync_conn):
                inspector = inspect(sync_conn)
                return set(inspector.get_table_names())

            tables = await conn.run_sync(get_tables)

            # Verify all expected tables exist
            missing_tables = expected_tables - tables
            assert not missing_tables, f"Missing tables: {missing_tables}"

            # Should have exactly these tables (no extras)
            assert tables == expected_tables

    async def test_init_db_idempotent(self, test_db_manager: DatabaseManager):
        """Test that calling create_tables multiple times is safe."""
        # Create tables a second time (already created in fixture)
        await test_db_manager.create_tables()

        # Create tables a third time
        await test_db_manager.create_tables()

        # Verify tables still exist and are usable
        async with test_db_manager.engine.begin() as conn:
            def get_tables(sync_conn):
                inspector = inspect(sync_conn)
                return inspector.get_table_names()

            tables = await conn.run_sync(get_tables)

            assert "mcp_server_snapshots" in tables
            assert "subagent_snapshots" in tables
            assert "slash_command_snapshots" in tables
            assert "claude_memory_snapshots" in tables


class TestMcpServerSnapshotSchema:
    """Tests for mcp_server_snapshots table schema."""

    async def test_mcp_server_snapshot_table_schema(self, test_db_manager: DatabaseManager):
        """Test that mcp_server_snapshots table has correct columns."""
        async with test_db_manager.engine.begin() as conn:
            def get_schema_info(sync_conn):
                inspector = inspect(sync_conn)
                columns = {col["name"]: col for col in inspector.get_columns("mcp_server_snapshots")}
                pk_columns = inspector.get_pk_constraint("mcp_server_snapshots")
                fks = inspector.get_foreign_keys("mcp_server_snapshots")
                return columns, pk_columns, fks

            columns, pk_columns, fks = await conn.run_sync(get_schema_info)

            # Verify all required columns exist
            required_columns = {
                "id",
                "snapshot_id",
                "server_name",
                "command",
                "args_json",
                "env_json",
                "enabled",
                "config_file_path",
            }

            actual_columns = set(columns.keys())
            assert required_columns == actual_columns, f"Column mismatch. Expected: {required_columns}, Got: {actual_columns}"

            # Verify primary key
            assert pk_columns["constrained_columns"] == ["id"]

            # Verify foreign keys
            assert len(fks) == 1, "Should have 1 foreign key to snapshots table"
            assert fks[0]["referred_table"] == "snapshots"
            assert fks[0]["constrained_columns"] == ["snapshot_id"]

    async def test_mcp_server_snapshot_indexes(self, test_db_manager: DatabaseManager):
        """Test that mcp_server_snapshots table has correct indexes."""
        async with test_db_manager.engine.begin() as conn:
            def get_indexes_info(sync_conn):
                inspector = inspect(sync_conn)
                indexes = inspector.get_indexes("mcp_server_snapshots")
                return {idx["name"] for idx in indexes}

            index_names = await conn.run_sync(get_indexes_info)

            # Should have indexes defined in model
            assert "idx_snapshot_server" in index_names
            assert "idx_server_name" in index_names


class TestSubagentSnapshotSchema:
    """Tests for subagent_snapshots table schema."""

    async def test_subagent_snapshot_table_schema(self, test_db_manager: DatabaseManager):
        """Test that subagent_snapshots table has correct columns."""
        async with test_db_manager.engine.begin() as conn:
            def get_schema_info(sync_conn):
                inspector = inspect(sync_conn)
                columns = {col["name"]: col for col in inspector.get_columns("subagent_snapshots")}
                pk_columns = inspector.get_pk_constraint("subagent_snapshots")
                fks = inspector.get_foreign_keys("subagent_snapshots")
                return columns, pk_columns, fks

            columns, pk_columns, fks = await conn.run_sync(get_schema_info)

            # Verify all required columns exist
            required_columns = {
                "id",
                "snapshot_id",
                "agent_name",
                "content_hash",
                "content_id",
                "config_file_path",
            }

            actual_columns = set(columns.keys())
            assert required_columns == actual_columns, f"Column mismatch. Expected: {required_columns}, Got: {actual_columns}"

            # Verify primary key
            assert pk_columns["constrained_columns"] == ["id"]

            # Verify foreign keys (2: to snapshots and file_contents)
            assert len(fks) == 2, "Should have 2 foreign keys (snapshots and file_contents)"

            fk_tables = {fk["referred_table"] for fk in fks}
            assert "snapshots" in fk_tables
            assert "file_contents" in fk_tables

    async def test_subagent_snapshot_indexes(self, test_db_manager: DatabaseManager):
        """Test that subagent_snapshots table has correct indexes."""
        async with test_db_manager.engine.begin() as conn:
            def get_indexes_info(sync_conn):
                inspector = inspect(sync_conn)
                indexes = inspector.get_indexes("subagent_snapshots")
                return {idx["name"] for idx in indexes}

            index_names = await conn.run_sync(get_indexes_info)

            # Should have indexes defined in model
            assert "idx_snapshot_agent" in index_names
            assert "idx_agent_name" in index_names


class TestSlashCommandSnapshotSchema:
    """Tests for slash_command_snapshots table schema."""

    async def test_slash_command_snapshot_table_schema(self, test_db_manager: DatabaseManager):
        """Test that slash_command_snapshots table has correct columns."""
        async with test_db_manager.engine.begin() as conn:
            def get_schema_info(sync_conn):
                inspector = inspect(sync_conn)
                columns = {col["name"]: col for col in inspector.get_columns("slash_command_snapshots")}
                pk_columns = inspector.get_pk_constraint("slash_command_snapshots")
                fks = inspector.get_foreign_keys("slash_command_snapshots")
                return columns, pk_columns, fks

            columns, pk_columns, fks = await conn.run_sync(get_schema_info)

            # Verify all required columns exist
            required_columns = {
                "id",
                "snapshot_id",
                "command_name",
                "content_hash",
                "content_id",
                "config_file_path",
            }

            actual_columns = set(columns.keys())
            assert required_columns == actual_columns, f"Column mismatch. Expected: {required_columns}, Got: {actual_columns}"

            # Verify primary key
            assert pk_columns["constrained_columns"] == ["id"]

            # Verify foreign keys (2: to snapshots and file_contents)
            assert len(fks) == 2, "Should have 2 foreign keys (snapshots and file_contents)"

            fk_tables = {fk["referred_table"] for fk in fks}
            assert "snapshots" in fk_tables
            assert "file_contents" in fk_tables

    async def test_slash_command_snapshot_indexes(self, test_db_manager: DatabaseManager):
        """Test that slash_command_snapshots table has correct indexes."""
        async with test_db_manager.engine.begin() as conn:
            def get_indexes_info(sync_conn):
                inspector = inspect(sync_conn)
                indexes = inspector.get_indexes("slash_command_snapshots")
                return {idx["name"] for idx in indexes}

            index_names = await conn.run_sync(get_indexes_info)

            # Should have indexes defined in model
            assert "idx_snapshot_command" in index_names
            assert "idx_command_name" in index_names


class TestClaudeMemorySnapshotSchema:
    """Tests for claude_memory_snapshots table schema."""

    async def test_claude_memory_snapshot_table_schema(self, test_db_manager: DatabaseManager):
        """Test that claude_memory_snapshots table has correct columns."""
        async with test_db_manager.engine.begin() as conn:
            def get_schema_info(sync_conn):
                inspector = inspect(sync_conn)
                columns = {col["name"]: col for col in inspector.get_columns("claude_memory_snapshots")}
                pk_columns = inspector.get_pk_constraint("claude_memory_snapshots")
                fks = inspector.get_foreign_keys("claude_memory_snapshots")
                return columns, pk_columns, fks

            columns, pk_columns, fks = await conn.run_sync(get_schema_info)

            # Verify all required columns exist
            required_columns = {
                "id",
                "snapshot_id",
                "scope",
                "content_hash",
                "content_id",
                "config_file_path",
            }

            actual_columns = set(columns.keys())
            assert required_columns == actual_columns, f"Column mismatch. Expected: {required_columns}, Got: {actual_columns}"

            # Verify primary key
            assert pk_columns["constrained_columns"] == ["id"]

            # Verify foreign keys (2: to snapshots and file_contents)
            assert len(fks) == 2, "Should have 2 foreign keys (snapshots and file_contents)"

            fk_tables = {fk["referred_table"] for fk in fks}
            assert "snapshots" in fk_tables
            assert "file_contents" in fk_tables

    async def test_claude_memory_snapshot_indexes(self, test_db_manager: DatabaseManager):
        """Test that claude_memory_snapshots table has correct indexes."""
        async with test_db_manager.engine.begin() as conn:
            def get_indexes_info(sync_conn):
                inspector = inspect(sync_conn)
                indexes = inspector.get_indexes("claude_memory_snapshots")
                return {idx["name"] for idx in indexes}

            index_names = await conn.run_sync(get_indexes_info)

            # Should have index defined in model
            assert "idx_snapshot_memory" in index_names


class TestEntityRelationships:
    """Tests for entity model foreign key relationships."""

    async def test_mcp_server_snapshot_relationship_works(self, test_session):
        """Test that MCP server snapshot can be created with FK to snapshot."""
        from datetime import datetime

        # Create snapshot
        snapshot = Snapshot(
            snapshot_time=datetime.utcnow(),
            snapshot_hash="test_hash_mcp_rel",
            trigger_type="manual",
            os_type="Windows",
            total_locations=1,
            files_found=1,
            directories_found=0,
            total_size_bytes=100,
        )

        test_session.add(snapshot)
        await test_session.commit()
        await test_session.refresh(snapshot)

        # Create MCP server snapshot with FK
        mcp_snapshot = McpServerSnapshot(
            snapshot_id=snapshot.id,
            server_name="test-server",
            command="node",
            args_json='["index.js"]',
            env_json='{"NODE_ENV": "production"}',
            enabled=True,
            config_file_path="/path/to/config.json",
        )

        test_session.add(mcp_snapshot)
        await test_session.commit()
        await test_session.refresh(mcp_snapshot)

        # Verify relationship
        assert mcp_snapshot.id is not None
        assert mcp_snapshot.snapshot_id == snapshot.id
        assert mcp_snapshot.server_name == "test-server"

    async def test_subagent_snapshot_relationship_works(self, test_session):
        """Test that subagent snapshot can be created with FKs."""
        from datetime import datetime

        # Create snapshot
        snapshot = Snapshot(
            snapshot_time=datetime.utcnow(),
            snapshot_hash="test_hash_subagent_rel",
            trigger_type="manual",
            os_type="Windows",
            total_locations=1,
            files_found=1,
            directories_found=0,
            total_size_bytes=100,
        )

        # Create file content
        file_content = FileContent(
            content_hash="subagent_content_hash",
            content_text="Subagent content here",
            content_type="text",
            size_bytes=20,
            compression="none",
            reference_count=1,
        )

        test_session.add(snapshot)
        test_session.add(file_content)
        await test_session.commit()
        await test_session.refresh(snapshot)
        await test_session.refresh(file_content)

        # Create subagent snapshot with FKs
        subagent_snapshot = SubagentSnapshot(
            snapshot_id=snapshot.id,
            agent_name="test-agent",
            content_hash="subagent_content_hash",
            content_id=file_content.id,
            config_file_path="/path/to/agent.md",
        )

        test_session.add(subagent_snapshot)
        await test_session.commit()
        await test_session.refresh(subagent_snapshot)

        # Verify relationships
        assert subagent_snapshot.id is not None
        assert subagent_snapshot.snapshot_id == snapshot.id
        assert subagent_snapshot.content_id == file_content.id
        assert subagent_snapshot.agent_name == "test-agent"

    async def test_slash_command_snapshot_relationship_works(self, test_session):
        """Test that slash command snapshot can be created with FKs."""
        from datetime import datetime

        # Create snapshot
        snapshot = Snapshot(
            snapshot_time=datetime.utcnow(),
            snapshot_hash="test_hash_command_rel",
            trigger_type="manual",
            os_type="Windows",
            total_locations=1,
            files_found=1,
            directories_found=0,
            total_size_bytes=100,
        )

        # Create file content
        file_content = FileContent(
            content_hash="command_content_hash",
            content_text="Command content here",
            content_type="text",
            size_bytes=20,
            compression="none",
            reference_count=1,
        )

        test_session.add(snapshot)
        test_session.add(file_content)
        await test_session.commit()
        await test_session.refresh(snapshot)
        await test_session.refresh(file_content)

        # Create slash command snapshot with FKs
        command_snapshot = SlashCommandSnapshot(
            snapshot_id=snapshot.id,
            command_name="test-command",
            content_hash="command_content_hash",
            content_id=file_content.id,
            config_file_path="/path/to/command.md",
        )

        test_session.add(command_snapshot)
        await test_session.commit()
        await test_session.refresh(command_snapshot)

        # Verify relationships
        assert command_snapshot.id is not None
        assert command_snapshot.snapshot_id == snapshot.id
        assert command_snapshot.content_id == file_content.id
        assert command_snapshot.command_name == "test-command"

    async def test_claude_memory_snapshot_relationship_works(self, test_session):
        """Test that Claude memory snapshot can be created with FKs."""
        from datetime import datetime

        # Create snapshot
        snapshot = Snapshot(
            snapshot_time=datetime.utcnow(),
            snapshot_hash="test_hash_memory_rel",
            trigger_type="manual",
            os_type="Windows",
            total_locations=1,
            files_found=1,
            directories_found=0,
            total_size_bytes=100,
        )

        # Create file content
        file_content = FileContent(
            content_hash="memory_content_hash",
            content_text="# CLAUDE.md\n\nMemory content here",
            content_type="markdown",
            size_bytes=35,
            compression="none",
            reference_count=1,
        )

        test_session.add(snapshot)
        test_session.add(file_content)
        await test_session.commit()
        await test_session.refresh(snapshot)
        await test_session.refresh(file_content)

        # Create memory snapshot with FKs
        memory_snapshot = ClaudeMemorySnapshot(
            snapshot_id=snapshot.id,
            scope="project",
            content_hash="memory_content_hash",
            content_id=file_content.id,
            config_file_path="/path/to/CLAUDE.md",
        )

        test_session.add(memory_snapshot)
        await test_session.commit()
        await test_session.refresh(memory_snapshot)

        # Verify relationships
        assert memory_snapshot.id is not None
        assert memory_snapshot.snapshot_id == snapshot.id
        assert memory_snapshot.content_id == file_content.id
        assert memory_snapshot.scope == "project"

    async def test_entity_cascade_delete(self, test_session):
        """Test that deleting snapshot cascades to entity snapshots."""
        from datetime import datetime

        # Create snapshot
        snapshot = Snapshot(
            snapshot_time=datetime.utcnow(),
            snapshot_hash="test_hash_cascade",
            trigger_type="manual",
            os_type="Windows",
            total_locations=1,
            files_found=1,
            directories_found=0,
            total_size_bytes=100,
        )

        test_session.add(snapshot)
        await test_session.commit()
        await test_session.refresh(snapshot)

        # Create entity snapshots
        mcp_snapshot = McpServerSnapshot(
            snapshot_id=snapshot.id,
            server_name="test-server",
            command="node",
            args_json='[]',
            env_json='{}',
            enabled=True,
        )

        test_session.add(mcp_snapshot)
        await test_session.commit()

        snapshot_id = snapshot.id

        # Delete snapshot
        await test_session.delete(snapshot)
        await test_session.commit()

        # Verify entity snapshot was deleted (cascade delete)
        result = await test_session.execute(
            select(McpServerSnapshot).where(
                McpServerSnapshot.snapshot_id == snapshot_id
            )
        )
        assert result.scalar_one_or_none() is None

    async def test_entity_foreign_key_constraint(self, test_session):
        """Test that foreign key constraints are enforced for entity tables."""
        # Try to create entity snapshot without valid snapshot
        mcp_snapshot = McpServerSnapshot(
            snapshot_id=99999,  # Non-existent snapshot ID
            server_name="invalid-server",
            command="node",
            args_json='[]',
            env_json='{}',
            enabled=True,
        )

        test_session.add(mcp_snapshot)

        with pytest.raises(IntegrityError):
            await test_session.commit()
