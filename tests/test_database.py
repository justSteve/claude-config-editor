"""
Tests for database operations and models.

Tests cover:
- Database initialization and connection
- Model creation and relationships
- File contents storage and retrieval
- Foreign key constraints
- Data integrity
"""

import pytest
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from src.core.database import DatabaseManager
from src.core.models import (
    Snapshot,
    SnapshotEnvVar,
    SnapshotPath,
    FileContent,
    JsonData,
    ClaudeConfig,
    McpServer,
    SnapshotChange,
    SnapshotTag,
    Annotation,
)


class TestDatabaseManager:
    """Tests for DatabaseManager."""

    async def test_database_initialization(self, test_db_manager: DatabaseManager):
        """Test database initialization creates tables."""
        # Database should be initialized
        assert test_db_manager.engine is not None
        assert test_db_manager.session_factory is not None

        # Health check should pass
        is_healthy = await test_db_manager.health_check()
        assert is_healthy is True

    async def test_database_stats(self, test_db_manager: DatabaseManager):
        """Test database statistics collection."""
        stats = await test_db_manager.get_database_stats()

        # Should have stats for all tables
        assert "snapshots_count" in stats
        assert "file_contents_count" in stats
        assert "snapshot_paths_count" in stats

        # All counts should be 0 for empty database
        assert stats["snapshots_count"] == 0
        assert stats["file_contents_count"] == 0

    async def test_session_management(self, test_db_manager: DatabaseManager):
        """Test database session creation and cleanup."""
        async with test_db_manager.get_session() as session:
            assert session is not None
            # Session should be usable
            result = await session.execute(select(1))
            assert result.scalar() == 1


class TestSnapshotModel:
    """Tests for Snapshot model."""

    async def test_create_snapshot(self, test_session):
        """Test creating a snapshot."""
        snapshot = Snapshot(
            snapshot_time=datetime.utcnow(),
            snapshot_hash="test_hash_123",
            trigger_type="manual",
            os_type="Windows",
            os_version="10.0",
            total_locations=10,
            files_found=5,
            directories_found=5,
            total_size_bytes=1000,
        )

        test_session.add(snapshot)
        await test_session.commit()
        await test_session.refresh(snapshot)

        assert snapshot.id is not None
        assert snapshot.snapshot_hash == "test_hash_123"
        assert snapshot.os_type == "Windows"

    async def test_snapshot_with_env_vars(self, test_session):
        """Test snapshot with environment variables."""
        snapshot = Snapshot(
            snapshot_time=datetime.utcnow(),
            snapshot_hash="test_hash_456",
            trigger_type="manual",
            os_type="Windows",
            total_locations=1,
            files_found=1,
            directories_found=0,
            total_size_bytes=100,
        )

        env_var = SnapshotEnvVar(
            snapshot=snapshot,
            placeholder="%APPDATA%",
            resolved_path="C:\\Users\\test\\AppData\\Roaming",
        )

        test_session.add(snapshot)
        test_session.add(env_var)
        await test_session.commit()

        # Verify relationship by querying with eager load

        result = await test_session.execute(
            select(Snapshot)
            .where(Snapshot.id == snapshot.id)
            .options(selectinload(Snapshot.env_vars))
        )
        loaded_snapshot = result.scalar_one()
        assert len(loaded_snapshot.env_vars) == 1
        assert loaded_snapshot.env_vars[0].placeholder == "%APPDATA%"

    async def test_snapshot_cascade_delete(self, test_session):
        """Test that deleting snapshot cascades to related records."""
        snapshot = Snapshot(
            snapshot_time=datetime.utcnow(),
            snapshot_hash="test_hash_789",
            trigger_type="manual",
            os_type="Windows",
            total_locations=1,
            files_found=1,
            directories_found=0,
            total_size_bytes=100,
        )

        env_var = SnapshotEnvVar(
            snapshot=snapshot,
            placeholder="%HOME%",
            resolved_path="C:\\Users\\test",
        )

        test_session.add(snapshot)
        test_session.add(env_var)
        await test_session.commit()

        snapshot_id = snapshot.id

        # Delete snapshot
        await test_session.delete(snapshot)
        await test_session.commit()

        # Verify env_var was deleted (cascade delete)
        result = await test_session.execute(
            select(SnapshotEnvVar).where(
                SnapshotEnvVar.snapshot_id == snapshot_id)
        )
        assert result.scalar_one_or_none() is None


class TestFileContentModel:
    """Tests for FileContent model."""

    async def test_create_file_content(self, test_session):
        """Test creating file content."""
        file_content = FileContent(
            content_hash="abc123def456",
            content_text='{"key": "value"}',
            content_type="json",
            size_bytes=20,
            compression="none",
            reference_count=1,
        )

        test_session.add(file_content)
        await test_session.commit()
        await test_session.refresh(file_content)

        assert file_content.id is not None
        assert file_content.content_hash == "abc123def456"
        assert file_content.content_text == '{"key": "value"}'
        assert file_content.reference_count == 1

    async def test_file_content_deduplication(self, test_session):
        """Test that file contents are deduplicated by hash."""
        # Create first file content
        file_content1 = FileContent(
            content_hash="same_hash_123",
            content_text="Same content",
            content_type="text",
            size_bytes=12,
            compression="none",
            reference_count=1,
        )

        test_session.add(file_content1)
        await test_session.commit()

        # Try to create duplicate (should fail due to unique constraint)
        file_content2 = FileContent(
            content_hash="same_hash_123",  # Same hash
            content_text="Different content",
            content_type="text",
            size_bytes=15,
            compression="none",
            reference_count=1,
        )

        test_session.add(file_content2)

        with pytest.raises(IntegrityError):
            await test_session.commit()

    async def test_file_content_with_snapshot_path(self, test_session):
        """Test file content linked to snapshot path."""
        # Create snapshot
        snapshot = Snapshot(
            snapshot_time=datetime.utcnow(),
            snapshot_hash="snapshot_hash_123",
            trigger_type="manual",
            os_type="Windows",
            total_locations=1,
            files_found=1,
            directories_found=0,
            total_size_bytes=100,
        )

        # Create file content
        file_content = FileContent(
            content_hash="file_hash_123",
            content_text="File content here",
            content_type="text",
            size_bytes=18,
            compression="none",
            reference_count=1,
        )

        # Create snapshot path linked to file content
        snapshot_path = SnapshotPath(
            snapshot=snapshot,
            category="config",
            name="test.json",
            path_template="%APPDATA%\\test.json",
            resolved_path="C:\\Users\\test\\AppData\\Roaming\\test.json",
            exists=True,
            type="file",
            size_bytes=18,
            content_hash="file_hash_123",
            content_id=None,  # Will be set after file_content is committed
        )

        test_session.add(snapshot)
        test_session.add(file_content)
        await test_session.flush()  # Flush to get file_content.id

        snapshot_path.content_id = file_content.id
        test_session.add(snapshot_path)
        await test_session.commit()

        # Verify relationships by querying with eager load

        # Verify snapshot_path -> content relationship
        result = await test_session.execute(
            select(SnapshotPath)
            .where(SnapshotPath.id == snapshot_path.id)
            .options(selectinload(SnapshotPath.content))
        )
        loaded_path = result.scalar_one()
        assert loaded_path.content is not None
        assert loaded_path.content.content_hash == "file_hash_123"

        # Verify file_content -> paths relationship
        result = await test_session.execute(
            select(FileContent)
            .where(FileContent.id == file_content.id)
            .options(selectinload(FileContent.paths))
        )
        loaded_content = result.scalar_one()
        assert len(loaded_content.paths) == 1
        assert loaded_content.paths[0].name == "test.json"


class TestSnapshotPathModel:
    """Tests for SnapshotPath model."""

    async def test_create_snapshot_path(self, test_session):
        """Test creating a snapshot path."""
        snapshot = Snapshot(
            snapshot_time=datetime.utcnow(),
            snapshot_hash="snapshot_hash_456",
            trigger_type="manual",
            os_type="Windows",
            total_locations=1,
            files_found=1,
            directories_found=0,
            total_size_bytes=100,
        )

        snapshot_path = SnapshotPath(
            snapshot=snapshot,
            category="config",
            name="config.json",
            path_template="%APPDATA%\\config.json",
            resolved_path="C:\\Users\\test\\AppData\\Roaming\\config.json",
            exists=True,
            type="file",
            size_bytes=500,
        )

        test_session.add(snapshot)
        test_session.add(snapshot_path)
        await test_session.commit()
        await test_session.refresh(snapshot_path)

        assert snapshot_path.id is not None
        assert snapshot_path.category == "config"
        assert snapshot_path.exists is True
        assert snapshot_path.type == "file"

    async def test_snapshot_path_with_json_data(self, test_session):
        """Test snapshot path with JSON data."""
        snapshot = Snapshot(
            snapshot_time=datetime.utcnow(),
            snapshot_hash="snapshot_hash_789",
            trigger_type="manual",
            os_type="Windows",
            total_locations=1,
            files_found=1,
            directories_found=0,
            total_size_bytes=100,
        )

        file_content = FileContent(
            content_hash="json_hash_123",
            content_text='{"projects": [{"name": "test"}]}',
            content_type="json",
            size_bytes=30,
            compression="none",
            reference_count=1,
        )

        snapshot_path = SnapshotPath(
            snapshot=snapshot,
            category="config",
            name="claude_desktop_config.json",
            path_template="%APPDATA%\\claude_desktop_config.json",
            resolved_path="C:\\Users\\test\\AppData\\Roaming\\claude_desktop_config.json",
            exists=True,
            type="file",
            size_bytes=30,
            content_hash="json_hash_123",
        )

        test_session.add(snapshot)
        test_session.add(file_content)
        await test_session.flush()

        snapshot_path.content_id = file_content.id
        test_session.add(snapshot_path)
        await test_session.flush()

        json_data = JsonData(
            content_id=file_content.id,
            snapshot_path_id=snapshot_path.id,
            json_path="projects[0].name",
            json_value="test",
            json_type="string",
        )

        test_session.add(json_data)
        await test_session.commit()

        # Verify relationship by querying with eager load
        from sqlalchemy.orm import selectinload

        result = await test_session.execute(
            select(SnapshotPath)
            .where(SnapshotPath.id == snapshot_path.id)
            .options(selectinload(SnapshotPath.json_data))
        )
        loaded_path = result.scalar_one()
        assert len(loaded_path.json_data) == 1
        assert loaded_path.json_data[0].json_path == "projects[0].name"


class TestClaudeConfigModel:
    """Tests for ClaudeConfig model."""

    async def test_create_claude_config(self, test_session):
        """Test creating a Claude config entry."""
        snapshot = Snapshot(
            snapshot_time=datetime.utcnow(),
            snapshot_hash="snapshot_hash_config",
            trigger_type="manual",
            os_type="Windows",
            total_locations=1,
            files_found=1,
            directories_found=0,
            total_size_bytes=100,
        )

        snapshot_path = SnapshotPath(
            snapshot=snapshot,
            category="config",
            name="claude_desktop_config.json",
            path_template="%APPDATA%\\claude_desktop_config.json",
            resolved_path="C:\\Users\\test\\AppData\\Roaming\\claude_desktop_config.json",
            exists=True,
            type="file",
            size_bytes=100,
        )

        claude_config = ClaudeConfig(
            snapshot_path=snapshot_path,
            config_type="desktop",
            num_projects=5,
            num_mcp_servers=3,
            total_size_bytes=100,
        )

        test_session.add(snapshot)
        test_session.add(snapshot_path)
        test_session.add(claude_config)
        await test_session.commit()
        await test_session.refresh(claude_config)

        assert claude_config.id is not None
        assert claude_config.config_type == "desktop"
        assert claude_config.num_projects == 5
        assert claude_config.num_mcp_servers == 3


class TestMcpServerModel:
    """Tests for McpServer model."""

    async def test_create_mcp_server(self, test_session):
        """Test creating an MCP server entry."""
        snapshot = Snapshot(
            snapshot_time=datetime.utcnow(),
            snapshot_hash="snapshot_hash_mcp",
            trigger_type="manual",
            os_type="Windows",
            total_locations=1,
            files_found=1,
            directories_found=0,
            total_size_bytes=100,
        )

        snapshot_path = SnapshotPath(
            snapshot=snapshot,
            category="config",
            name="claude_desktop_config.json",
            path_template="%APPDATA%\\claude_desktop_config.json",
            resolved_path="C:\\Users\\test\\AppData\\Roaming\\claude_desktop_config.json",
            exists=True,
            type="file",
            size_bytes=100,
        )

        mcp_server = McpServer(
            snapshot_path=snapshot_path,
            server_name="test_server",
            command="python",
            args='["-m", "server"]',
            env='{"KEY": "value"}',
            working_directory="C:\\path\\to\\server",
        )

        test_session.add(snapshot)
        test_session.add(snapshot_path)
        test_session.add(mcp_server)
        await test_session.commit()
        await test_session.refresh(mcp_server)

        assert mcp_server.id is not None
        assert mcp_server.server_name == "test_server"
        assert mcp_server.command == "python"


class TestSnapshotTagModel:
    """Tests for SnapshotTag model."""

    async def test_create_snapshot_tag(self, test_session):
        """Test creating a snapshot tag."""
        snapshot = Snapshot(
            snapshot_time=datetime.utcnow(),
            snapshot_hash="snapshot_hash_tag",
            trigger_type="manual",
            os_type="Windows",
            total_locations=1,
            files_found=1,
            directories_found=0,
            total_size_bytes=100,
        )

        tag = SnapshotTag(
            snapshot=snapshot,
            tag_name="v1.0.0",
            tag_type="version",
            description="Initial release",
        )

        test_session.add(snapshot)
        test_session.add(tag)
        await test_session.commit()

        assert tag.id is not None
        assert tag.tag_name == "v1.0.0"
        assert tag.tag_type == "version"

        # Verify relationship by querying with eager load
        from sqlalchemy.orm import selectinload

        result = await test_session.execute(
            select(Snapshot)
            .where(Snapshot.id == snapshot.id)
            .options(selectinload(Snapshot.tags))
        )
        loaded_snapshot = result.scalar_one()
        assert len(loaded_snapshot.tags) == 1
        assert loaded_snapshot.tags[0].tag_name == "v1.0.0"


class TestAnnotationModel:
    """Tests for Annotation model."""

    async def test_create_annotation(self, test_session):
        """Test creating an annotation."""
        snapshot = Snapshot(
            snapshot_time=datetime.utcnow(),
            snapshot_hash="snapshot_hash_annotation",
            trigger_type="manual",
            os_type="Windows",
            total_locations=1,
            files_found=1,
            directories_found=0,
            total_size_bytes=100,
        )

        annotation = Annotation(
            snapshot=snapshot,
            annotation_text="This is a test annotation",
            annotation_type="note",
            created_by="test_user",
        )

        test_session.add(snapshot)
        test_session.add(annotation)
        await test_session.commit()
        await test_session.refresh(annotation)

        assert annotation.id is not None
        assert annotation.annotation_text == "This is a test annotation"
        assert annotation.annotation_type == "note"


class TestDataIntegrity:
    """Tests for data integrity and constraints."""

    async def test_foreign_key_constraint(self, test_session):
        """Test that foreign key constraints are enforced."""
        # Try to create snapshot_path without valid snapshot
        snapshot_path = SnapshotPath(
            snapshot_id=99999,  # Non-existent snapshot ID
            category="config",
            name="test.json",
            path_template="%APPDATA%\\test.json",
            resolved_path="C:\\test.json",
            exists=True,
            type="file",
        )

        test_session.add(snapshot_path)

        with pytest.raises(IntegrityError):
            await test_session.commit()

    async def test_unique_constraints(self, test_session):
        """Test that unique constraints are enforced."""
        snapshot = Snapshot(
            snapshot_time=datetime.utcnow(),
            snapshot_hash="unique_hash_123",
            trigger_type="manual",
            os_type="Windows",
            total_locations=1,
            files_found=1,
            directories_found=0,
            total_size_bytes=100,
        )

        test_session.add(snapshot)
        await test_session.commit()

        # Try to create duplicate snapshot with same hash
        snapshot2 = Snapshot(
            snapshot_time=datetime.utcnow(),
            snapshot_hash="unique_hash_123",  # Same hash
            trigger_type="manual",
            os_type="Windows",
            total_locations=1,
            files_found=1,
            directories_found=0,
            total_size_bytes=100,
        )

        test_session.add(snapshot2)

        with pytest.raises(IntegrityError):
            await test_session.commit()
