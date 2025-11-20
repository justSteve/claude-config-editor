"""
Tests for entity database models.

Verifies that entity snapshot models can be instantiated correctly,
foreign key relationships work, cascade deletes work properly,
and indexes are created.
"""

import json
import pytest
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from src.core.models import (
    Base,
    Snapshot,
    FileContent,
    McpServerSnapshot,
    SubagentSnapshot,
    SlashCommandSnapshot,
    ClaudeMemorySnapshot,
)


@pytest.fixture
async def async_session():
    """Create an in-memory async SQLite database for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session factory
    async_session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    # Provide session
    async with async_session_maker() as session:
        yield session

    # Cleanup
    await engine.dispose()


@pytest.mark.asyncio
async def test_mcp_server_snapshot_creation(async_session):
    """Test that McpServerSnapshot can be instantiated correctly."""
    # Create a snapshot first
    snapshot = Snapshot(
        snapshot_time=datetime.now(),
        snapshot_hash="test_hash_1",
        trigger_type="manual",
        os_type="linux",
        total_locations=17,
        files_found=50,
        directories_found=10,
        total_size_bytes=100000,
    )
    async_session.add(snapshot)
    await async_session.flush()

    # Create MCP server snapshot
    mcp_server = McpServerSnapshot(
        snapshot_id=snapshot.id,
        server_name="filesystem",
        command="npx",
        args_json=json.dumps(["@anthropic-ai/mcp-server-filesystem"]),
        env_json=json.dumps({"HOME": "/home/user"}),
        enabled=True,
        config_file_path="/home/user/.claude.json",
    )
    async_session.add(mcp_server)
    await async_session.commit()

    # Verify it was created
    stmt = select(McpServerSnapshot).where(
        McpServerSnapshot.server_name == "filesystem"
    )
    result = await async_session.execute(stmt)
    retrieved = result.scalar_one()

    assert retrieved.server_name == "filesystem"
    assert retrieved.command == "npx"
    assert retrieved.enabled is True
    assert json.loads(retrieved.args_json) == ["@anthropic-ai/mcp-server-filesystem"]
    assert json.loads(retrieved.env_json) == {"HOME": "/home/user"}


@pytest.mark.asyncio
async def test_subagent_snapshot_with_file_content(async_session):
    """Test SubagentSnapshot with FileContent deduplication."""
    # Create snapshot
    snapshot = Snapshot(
        snapshot_time=datetime.now(),
        snapshot_hash="test_hash_2",
        trigger_type="manual",
        os_type="linux",
        total_locations=17,
        files_found=50,
        directories_found=10,
        total_size_bytes=100000,
    )
    async_session.add(snapshot)
    await async_session.flush()

    # Create file content
    content = FileContent(
        content_hash="abc123def456",
        content_text="# Research Agent\n\nThis is a research agent.",
        content_type="markdown",
        size_bytes=50,
        compression="none",
    )
    async_session.add(content)
    await async_session.flush()

    # Create subagent snapshot
    subagent = SubagentSnapshot(
        snapshot_id=snapshot.id,
        agent_name="research-agent",
        content_hash=content.content_hash,
        content_id=content.id,
        config_file_path="/home/user/.claude/subagents/research-agent.md",
    )
    async_session.add(subagent)
    await async_session.commit()

    # Verify relationship works
    stmt = select(SubagentSnapshot).where(
        SubagentSnapshot.agent_name == "research-agent"
    )
    result = await async_session.execute(stmt)
    retrieved = result.scalar_one()

    assert retrieved.agent_name == "research-agent"
    assert retrieved.content_hash == "abc123def456"
    assert retrieved.content.content_type == "markdown"


@pytest.mark.asyncio
async def test_slash_command_snapshot_creation(async_session):
    """Test SlashCommandSnapshot can be instantiated correctly."""
    # Create snapshot
    snapshot = Snapshot(
        snapshot_time=datetime.now(),
        snapshot_hash="test_hash_3",
        trigger_type="manual",
        os_type="linux",
        total_locations=17,
        files_found=50,
        directories_found=10,
        total_size_bytes=100000,
    )
    async_session.add(snapshot)
    await async_session.flush()

    # Create file content
    content = FileContent(
        content_hash="cmd123hash",
        content_text="Review this pull request",
        content_type="text",
        size_bytes=25,
        compression="none",
    )
    async_session.add(content)
    await async_session.flush()

    # Create slash command snapshot
    command = SlashCommandSnapshot(
        snapshot_id=snapshot.id,
        command_name="review-pr",
        content_hash=content.content_hash,
        content_id=content.id,
        config_file_path="/home/user/.claude/commands/review-pr.md",
    )
    async_session.add(command)
    await async_session.commit()

    # Verify
    stmt = select(SlashCommandSnapshot).where(
        SlashCommandSnapshot.command_name == "review-pr"
    )
    result = await async_session.execute(stmt)
    retrieved = result.scalar_one()

    assert retrieved.command_name == "review-pr"
    assert retrieved.content.content_text == "Review this pull request"


@pytest.mark.asyncio
async def test_claude_memory_snapshot_creation(async_session):
    """Test ClaudeMemorySnapshot can be instantiated correctly."""
    # Create snapshot
    snapshot = Snapshot(
        snapshot_time=datetime.now(),
        snapshot_hash="test_hash_4",
        trigger_type="manual",
        os_type="linux",
        total_locations=17,
        files_found=50,
        directories_found=10,
        total_size_bytes=100000,
    )
    async_session.add(snapshot)
    await async_session.flush()

    # Create file content
    content = FileContent(
        content_hash="memory123hash",
        content_text="# CLAUDE.md\n\nProject memory content here.",
        content_type="markdown",
        size_bytes=45,
        compression="none",
    )
    async_session.add(content)
    await async_session.flush()

    # Create memory snapshot
    memory = ClaudeMemorySnapshot(
        snapshot_id=snapshot.id,
        scope="project",
        content_hash=content.content_hash,
        content_id=content.id,
        config_file_path="/home/user/project/.claude/CLAUDE.md",
    )
    async_session.add(memory)
    await async_session.commit()

    # Verify
    stmt = select(ClaudeMemorySnapshot).where(ClaudeMemorySnapshot.scope == "project")
    result = await async_session.execute(stmt)
    retrieved = result.scalar_one()

    assert retrieved.scope == "project"
    assert retrieved.content.content_text == "# CLAUDE.md\n\nProject memory content here."


@pytest.mark.asyncio
async def test_cascade_delete_on_snapshot(async_session):
    """Test that deleting a snapshot cascades to entity snapshots."""
    # Create snapshot
    snapshot = Snapshot(
        snapshot_time=datetime.now(),
        snapshot_hash="test_hash_5",
        trigger_type="manual",
        os_type="linux",
        total_locations=17,
        files_found=50,
        directories_found=10,
        total_size_bytes=100000,
    )
    async_session.add(snapshot)
    await async_session.flush()

    # Create file content
    content = FileContent(
        content_hash="cascade_test_hash",
        content_text="Test content",
        content_type="text",
        size_bytes=12,
        compression="none",
    )
    async_session.add(content)
    await async_session.flush()

    # Create entity snapshots
    mcp_server = McpServerSnapshot(
        snapshot_id=snapshot.id,
        server_name="test-server",
        command="test",
        args_json=json.dumps([]),
        env_json=json.dumps({}),
    )
    subagent = SubagentSnapshot(
        snapshot_id=snapshot.id,
        agent_name="test-agent",
        content_hash=content.content_hash,
        content_id=content.id,
    )
    command = SlashCommandSnapshot(
        snapshot_id=snapshot.id,
        command_name="test-cmd",
        content_hash=content.content_hash,
        content_id=content.id,
    )
    memory = ClaudeMemorySnapshot(
        snapshot_id=snapshot.id,
        scope="user",
        content_hash=content.content_hash,
        content_id=content.id,
    )

    async_session.add_all([mcp_server, subagent, command, memory])
    await async_session.commit()

    snapshot_id = snapshot.id

    # Verify all entities exist
    mcp_count = await async_session.scalar(
        select(McpServerSnapshot).where(McpServerSnapshot.snapshot_id == snapshot_id)
    )
    assert mcp_count is not None

    # Delete the snapshot
    await async_session.delete(snapshot)
    await async_session.commit()

    # Verify cascade delete worked
    mcp_result = await async_session.execute(
        select(McpServerSnapshot).where(McpServerSnapshot.snapshot_id == snapshot_id)
    )
    assert mcp_result.scalar_one_or_none() is None

    subagent_result = await async_session.execute(
        select(SubagentSnapshot).where(SubagentSnapshot.snapshot_id == snapshot_id)
    )
    assert subagent_result.scalar_one_or_none() is None

    command_result = await async_session.execute(
        select(SlashCommandSnapshot).where(
            SlashCommandSnapshot.snapshot_id == snapshot_id
        )
    )
    assert command_result.scalar_one_or_none() is None

    memory_result = await async_session.execute(
        select(ClaudeMemorySnapshot).where(
            ClaudeMemorySnapshot.snapshot_id == snapshot_id
        )
    )
    assert memory_result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_snapshot_relationships(async_session):
    """Test that Snapshot model has correct relationships to entity snapshots."""
    # Create snapshot
    snapshot = Snapshot(
        snapshot_time=datetime.now(),
        snapshot_hash="test_hash_6",
        trigger_type="manual",
        os_type="linux",
        total_locations=17,
        files_found=50,
        directories_found=10,
        total_size_bytes=100000,
    )
    async_session.add(snapshot)
    await async_session.flush()

    # Create file content
    content = FileContent(
        content_hash="rel_test_hash",
        content_text="Test",
        content_type="text",
        size_bytes=4,
        compression="none",
    )
    async_session.add(content)
    await async_session.flush()

    # Add entities to snapshot
    mcp_server = McpServerSnapshot(
        snapshot_id=snapshot.id,
        server_name="server1",
        command="cmd1",
        args_json="[]",
        env_json="{}",
    )
    subagent = SubagentSnapshot(
        snapshot_id=snapshot.id,
        agent_name="agent1",
        content_hash=content.content_hash,
        content_id=content.id,
    )

    async_session.add_all([mcp_server, subagent])
    await async_session.commit()

    # Query with eager loading of relationships
    stmt = (
        select(Snapshot)
        .where(Snapshot.id == snapshot.id)
        .options(
            selectinload(Snapshot.mcp_server_snapshots),
            selectinload(Snapshot.subagent_snapshots),
        )
    )
    result = await async_session.execute(stmt)
    loaded_snapshot = result.scalar_one()

    # Verify relationships
    assert len(loaded_snapshot.mcp_server_snapshots) == 1
    assert loaded_snapshot.mcp_server_snapshots[0].server_name == "server1"
    assert len(loaded_snapshot.subagent_snapshots) == 1
    assert loaded_snapshot.subagent_snapshots[0].agent_name == "agent1"


@pytest.mark.asyncio
async def test_file_content_backref_relationships(async_session):
    """Test that FileContent has correct backref relationships to entity snapshots."""
    # Create snapshot
    snapshot = Snapshot(
        snapshot_time=datetime.now(),
        snapshot_hash="test_hash_7",
        trigger_type="manual",
        os_type="linux",
        total_locations=17,
        files_found=50,
        directories_found=10,
        total_size_bytes=100000,
    )
    async_session.add(snapshot)
    await async_session.flush()

    # Create shared file content
    content = FileContent(
        content_hash="shared_hash",
        content_text="Shared content",
        content_type="text",
        size_bytes=14,
        compression="none",
    )
    async_session.add(content)
    await async_session.flush()

    # Create multiple entities sharing the same content
    subagent = SubagentSnapshot(
        snapshot_id=snapshot.id,
        agent_name="agent2",
        content_hash=content.content_hash,
        content_id=content.id,
    )
    command = SlashCommandSnapshot(
        snapshot_id=snapshot.id,
        command_name="cmd2",
        content_hash=content.content_hash,
        content_id=content.id,
    )
    memory = ClaudeMemorySnapshot(
        snapshot_id=snapshot.id,
        scope="user",
        content_hash=content.content_hash,
        content_id=content.id,
    )

    async_session.add_all([subagent, command, memory])
    await async_session.commit()

    # Query with eager loading of backref relationships
    stmt = (
        select(FileContent)
        .where(FileContent.id == content.id)
        .options(
            selectinload(FileContent.subagent_refs),
            selectinload(FileContent.command_refs),
            selectinload(FileContent.memory_refs),
        )
    )
    result = await async_session.execute(stmt)
    loaded_content = result.scalar_one()

    # Verify backref relationships
    assert len(loaded_content.subagent_refs) == 1
    assert loaded_content.subagent_refs[0].agent_name == "agent2"
    assert len(loaded_content.command_refs) == 1
    assert loaded_content.command_refs[0].command_name == "cmd2"
    assert len(loaded_content.memory_refs) == 1
    assert loaded_content.memory_refs[0].scope == "user"


@pytest.mark.asyncio
async def test_model_repr_methods(async_session):
    """Test that all entity models have proper __repr__ methods."""
    # Create snapshot
    snapshot = Snapshot(
        snapshot_time=datetime.now(),
        snapshot_hash="test_hash_8",
        trigger_type="manual",
        os_type="linux",
        total_locations=17,
        files_found=50,
        directories_found=10,
        total_size_bytes=100000,
    )
    async_session.add(snapshot)
    await async_session.flush()

    # Create file content
    content = FileContent(
        content_hash="repr_test_hash",
        content_text="Test",
        content_type="text",
        size_bytes=4,
        compression="none",
    )
    async_session.add(content)
    await async_session.flush()

    # Create entities
    mcp_server = McpServerSnapshot(
        snapshot_id=snapshot.id,
        server_name="test",
        command="cmd",
        args_json="[]",
        env_json="{}",
    )
    subagent = SubagentSnapshot(
        snapshot_id=snapshot.id,
        agent_name="test",
        content_hash=content.content_hash,
        content_id=content.id,
    )
    command = SlashCommandSnapshot(
        snapshot_id=snapshot.id,
        command_name="test",
        content_hash=content.content_hash,
        content_id=content.id,
    )
    memory = ClaudeMemorySnapshot(
        snapshot_id=snapshot.id,
        scope="user",
        content_hash=content.content_hash,
        content_id=content.id,
    )

    # Test repr methods don't raise exceptions
    assert "McpServerSnapshot" in repr(mcp_server)
    assert "test" in repr(mcp_server)
    assert "SubagentSnapshot" in repr(subagent)
    assert "test" in repr(subagent)
    assert "SlashCommandSnapshot" in repr(command)
    assert "test" in repr(command)
    assert "ClaudeMemorySnapshot" in repr(memory)
    assert "user" in repr(memory)
