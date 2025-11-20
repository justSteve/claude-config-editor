"""
Tests for entity dataclasses.

Validates entity creation, serialization, and snapshot summaries.
"""

import pytest
from datetime import datetime, timezone

from src.core.entities import (
    McpServerEntity,
    SubagentEntity,
    SlashCommandEntity,
    ClaudeMemoryEntity,
    EntitySnapshot,
)


class TestMcpServerEntity:
    """Test MCP server entity functionality."""

    def test_mcp_server_entity_creation(self):
        """Test creating an MCP server entity with all fields."""
        server = McpServerEntity(
            name="filesystem",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
            env={"NODE_ENV": "production"},
            enabled=True,
            config_file="/home/user/.config/claude/mcp.json",
        )

        assert server.name == "filesystem"
        assert server.command == "npx"
        assert server.args == ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
        assert server.env == {"NODE_ENV": "production"}
        assert server.enabled is True
        assert server.config_file == "/home/user/.config/claude/mcp.json"

    def test_mcp_server_entity_defaults(self):
        """Test MCP server entity with default values."""
        server = McpServerEntity(
            name="simple-server",
            command="/usr/bin/server",
        )

        assert server.name == "simple-server"
        assert server.command == "/usr/bin/server"
        assert server.args == []
        assert server.env == {}
        assert server.enabled is True
        assert server.config_file is None

    def test_mcp_server_entity_to_dict(self):
        """Test serializing MCP server entity to dictionary."""
        server = McpServerEntity(
            name="brave-search",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-brave-search"],
            env={"BRAVE_API_KEY": "test_key"},
            enabled=False,
            config_file="/etc/claude/mcp.json",
        )

        result = server.to_dict()

        assert isinstance(result, dict)
        assert result["name"] == "brave-search"
        assert result["command"] == "npx"
        assert result["args"] == ["-y", "@modelcontextprotocol/server-brave-search"]
        assert result["env"] == {"BRAVE_API_KEY": "test_key"}
        assert result["enabled"] is False
        assert result["config_file"] == "/etc/claude/mcp.json"

    def test_mcp_server_entity_mutable_defaults(self):
        """Test that mutable defaults (lists/dicts) don't share references."""
        server1 = McpServerEntity(name="server1", command="cmd1")
        server2 = McpServerEntity(name="server2", command="cmd2")

        server1.args.append("arg1")
        server1.env["KEY"] = "value1"

        # Verify server2's defaults are not affected
        assert server2.args == []
        assert server2.env == {}


class TestSubagentEntity:
    """Test subagent entity functionality."""

    def test_subagent_entity_creation(self):
        """Test creating a subagent entity."""
        created = datetime(2025, 1, 15, 10, 30, 0)
        subagent = SubagentEntity(
            name="code-reviewer",
            content="You are a code reviewer...",
            created_at=created,
            config_file="/home/user/.config/claude/subagents/code-reviewer.md",
        )

        assert subagent.name == "code-reviewer"
        assert subagent.content == "You are a code reviewer..."
        assert subagent.created_at == created
        assert subagent.config_file == "/home/user/.config/claude/subagents/code-reviewer.md"

    def test_subagent_entity_to_dict(self):
        """Test serializing subagent entity to dictionary."""
        created = datetime(2025, 1, 15, 10, 30, 0)
        subagent = SubagentEntity(
            name="debugger",
            content="You are a debugging assistant...",
            created_at=created,
            config_file="/home/user/subagents/debugger.md",
        )

        result = subagent.to_dict()

        assert isinstance(result, dict)
        assert result["name"] == "debugger"
        assert result["content"] == "You are a debugging assistant..."
        assert result["created_at"] == "2025-01-15T10:30:00"
        assert result["config_file"] == "/home/user/subagents/debugger.md"

    def test_subagent_entity_none_created_at(self):
        """Test subagent entity with None created_at."""
        subagent = SubagentEntity(
            name="test",
            content="content",
            created_at=None,
            config_file=None,
        )

        result = subagent.to_dict()
        assert result["created_at"] is None
        assert result["config_file"] is None


class TestSlashCommandEntity:
    """Test slash command entity functionality."""

    def test_slash_command_entity_creation(self):
        """Test creating a slash command entity."""
        created = datetime(2025, 2, 1, 14, 0, 0)
        command = SlashCommandEntity(
            name="/review-pr",
            content="Review the pull request and provide feedback...",
            created_at=created,
            config_file="/home/user/.config/claude/commands/review-pr.md",
        )

        assert command.name == "/review-pr"
        assert command.content == "Review the pull request and provide feedback..."
        assert command.created_at == created
        assert command.config_file == "/home/user/.config/claude/commands/review-pr.md"

    def test_slash_command_entity_to_dict(self):
        """Test serializing slash command entity to dictionary."""
        created = datetime(2025, 2, 1, 14, 0, 0)
        command = SlashCommandEntity(
            name="/debug",
            content="Help debug the issue...",
            created_at=created,
            config_file="/commands/debug.md",
        )

        result = command.to_dict()

        assert isinstance(result, dict)
        assert result["name"] == "/debug"
        assert result["content"] == "Help debug the issue..."
        assert result["created_at"] == "2025-02-01T14:00:00"
        assert result["config_file"] == "/commands/debug.md"


class TestClaudeMemoryEntity:
    """Test Claude memory entity functionality."""

    def test_claude_memory_entity_creation(self):
        """Test creating a Claude memory entity."""
        memory = ClaudeMemoryEntity(
            scope="user",
            content="# CLAUDE.md\n\nUser preferences and context...",
            path="/home/user/.config/claude/CLAUDE.md",
        )

        assert memory.scope == "user"
        assert memory.content == "# CLAUDE.md\n\nUser preferences and context..."
        assert memory.path == "/home/user/.config/claude/CLAUDE.md"

    def test_claude_memory_entity_to_dict(self):
        """Test serializing Claude memory entity to dictionary."""
        memory = ClaudeMemoryEntity(
            scope="project",
            content="# Project Memory\n\nProject-specific context...",
            path="/project/.claude/CLAUDE.md",
        )

        result = memory.to_dict()

        assert isinstance(result, dict)
        assert result["scope"] == "project"
        assert result["content"] == "# Project Memory\n\nProject-specific context..."
        assert result["path"] == "/project/.claude/CLAUDE.md"

    def test_claude_memory_entity_scopes(self):
        """Test different memory scopes."""
        user_memory = ClaudeMemoryEntity(
            scope="user",
            content="user content",
            path="/user/CLAUDE.md",
        )
        project_memory = ClaudeMemoryEntity(
            scope="project",
            content="project content",
            path="/project/CLAUDE.md",
        )
        enterprise_memory = ClaudeMemoryEntity(
            scope="enterprise",
            content="enterprise content",
            path="/enterprise/CLAUDE.md",
        )

        assert user_memory.scope == "user"
        assert project_memory.scope == "project"
        assert enterprise_memory.scope == "enterprise"


class TestEntitySnapshot:
    """Test entity snapshot functionality."""

    def test_entity_snapshot_creation(self):
        """Test creating an entity snapshot with all entities."""
        snapshot_time = datetime(2025, 3, 1, 12, 0, 0)

        mcp_server = McpServerEntity(
            name="filesystem",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem"],
        )

        subagent = SubagentEntity(
            name="code-reviewer",
            content="You are a reviewer...",
            created_at=datetime.now(timezone.utc),
        )

        command = SlashCommandEntity(
            name="/review",
            content="Review code...",
            created_at=datetime.now(timezone.utc),
        )

        memory = ClaudeMemoryEntity(
            scope="user",
            content="# CLAUDE.md",
            path="/user/CLAUDE.md",
        )

        snapshot = EntitySnapshot(
            snapshot_id=42,
            snapshot_time=snapshot_time,
            mcp_servers=[mcp_server],
            subagents=[subagent],
            slash_commands=[command],
            memory=memory,
        )

        assert snapshot.snapshot_id == 42
        assert snapshot.snapshot_time == snapshot_time
        assert len(snapshot.mcp_servers) == 1
        assert len(snapshot.subagents) == 1
        assert len(snapshot.slash_commands) == 1
        assert snapshot.memory is not None

    def test_entity_snapshot_defaults(self):
        """Test entity snapshot with default empty lists."""
        snapshot_time = datetime(2025, 3, 1, 12, 0, 0)

        snapshot = EntitySnapshot(
            snapshot_id=1,
            snapshot_time=snapshot_time,
        )

        assert snapshot.snapshot_id == 1
        assert snapshot.snapshot_time == snapshot_time
        assert snapshot.mcp_servers == []
        assert snapshot.subagents == []
        assert snapshot.slash_commands == []
        assert snapshot.memory is None

    def test_entity_snapshot_summary(self):
        """Test entity snapshot summary generation."""
        snapshot_time = datetime(2025, 3, 1, 12, 0, 0)

        # Create entities
        mcp1 = McpServerEntity(name="server1", command="cmd1")
        mcp2 = McpServerEntity(name="server2", command="cmd2")
        mcp3 = McpServerEntity(name="server3", command="cmd3")

        subagent1 = SubagentEntity(name="sub1", content="c1", created_at=datetime.now(timezone.utc))
        subagent2 = SubagentEntity(name="sub2", content="c2", created_at=datetime.now(timezone.utc))

        command1 = SlashCommandEntity(name="/cmd1", content="c1", created_at=datetime.now(timezone.utc))

        memory = ClaudeMemoryEntity(scope="user", content="memory", path="/path")

        snapshot = EntitySnapshot(
            snapshot_id=123,
            snapshot_time=snapshot_time,
            mcp_servers=[mcp1, mcp2, mcp3],
            subagents=[subagent1, subagent2],
            slash_commands=[command1],
            memory=memory,
        )

        summary = snapshot.summary()

        assert isinstance(summary, dict)
        assert summary["snapshot_id"] == 123
        assert summary["snapshot_time"] == "2025-03-01T12:00:00"
        assert summary["mcp_server_count"] == 3
        assert summary["subagent_count"] == 2
        assert summary["command_count"] == 1
        assert summary["has_memory"] is True

    def test_entity_snapshot_summary_empty(self):
        """Test entity snapshot summary with no entities."""
        snapshot_time = datetime(2025, 3, 1, 12, 0, 0)

        snapshot = EntitySnapshot(
            snapshot_id=456,
            snapshot_time=snapshot_time,
        )

        summary = snapshot.summary()

        assert summary["snapshot_id"] == 456
        assert summary["snapshot_time"] == "2025-03-01T12:00:00"
        assert summary["mcp_server_count"] == 0
        assert summary["subagent_count"] == 0
        assert summary["command_count"] == 0
        assert summary["has_memory"] is False

    def test_entity_snapshot_to_dict(self):
        """Test serializing entity snapshot to dictionary."""
        snapshot_time = datetime(2025, 3, 1, 12, 0, 0)

        mcp_server = McpServerEntity(name="fs", command="npx")
        subagent = SubagentEntity(
            name="reviewer",
            content="content",
            created_at=datetime(2025, 1, 1, 10, 0, 0)
        )
        command = SlashCommandEntity(
            name="/test",
            content="test",
            created_at=datetime(2025, 1, 1, 11, 0, 0)
        )
        memory = ClaudeMemoryEntity(scope="user", content="mem", path="/mem")

        snapshot = EntitySnapshot(
            snapshot_id=789,
            snapshot_time=snapshot_time,
            mcp_servers=[mcp_server],
            subagents=[subagent],
            slash_commands=[command],
            memory=memory,
        )

        result = snapshot.to_dict()

        assert isinstance(result, dict)
        assert result["snapshot_id"] == 789
        assert result["snapshot_time"] == "2025-03-01T12:00:00"
        assert len(result["mcp_servers"]) == 1
        assert result["mcp_servers"][0]["name"] == "fs"
        assert len(result["subagents"]) == 1
        assert result["subagents"][0]["name"] == "reviewer"
        assert len(result["slash_commands"]) == 1
        assert result["slash_commands"][0]["name"] == "/test"
        assert result["memory"]["scope"] == "user"

    def test_entity_snapshot_to_dict_empty(self):
        """Test serializing empty entity snapshot."""
        snapshot_time = datetime(2025, 3, 1, 12, 0, 0)

        snapshot = EntitySnapshot(
            snapshot_id=999,
            snapshot_time=snapshot_time,
        )

        result = snapshot.to_dict()

        assert result["snapshot_id"] == 999
        assert result["snapshot_time"] == "2025-03-01T12:00:00"
        assert result["mcp_servers"] == []
        assert result["subagents"] == []
        assert result["slash_commands"] == []
        assert result["memory"] is None

    def test_entity_snapshot_mutable_defaults(self):
        """Test that entity lists don't share references."""
        snapshot1 = EntitySnapshot(snapshot_id=1, snapshot_time=datetime.now(timezone.utc))
        snapshot2 = EntitySnapshot(snapshot_id=2, snapshot_time=datetime.now(timezone.utc))

        mcp = McpServerEntity(name="test", command="cmd")
        snapshot1.mcp_servers.append(mcp)

        # Verify snapshot2's lists are not affected
        assert len(snapshot1.mcp_servers) == 1
        assert len(snapshot2.mcp_servers) == 0
