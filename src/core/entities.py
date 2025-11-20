"""
Entity dataclasses for semantic configuration tracking.

These dataclasses represent high-level semantic entities extracted from
Claude configurations, providing a business-logic layer above the raw
database models.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class McpServerEntity:
    """
    Represents an MCP (Model Context Protocol) server configuration.

    Attributes:
        name: Server identifier (e.g., "filesystem", "brave-search")
        command: Executable command to start the server
        args: Command-line arguments for the server
        env: Environment variables for the server process
        enabled: Whether the server is currently enabled
        config_file: Source configuration file path
    """
    name: str
    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    enabled: bool = True
    config_file: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert entity to dictionary for serialization."""
        return {
            "name": self.name,
            "command": self.command,
            "args": self.args,
            "env": self.env,
            "enabled": self.enabled,
            "config_file": self.config_file,
        }


@dataclass
class SubagentEntity:
    """
    Represents a Claude subagent configuration.

    Attributes:
        name: Subagent identifier (e.g., "code-reviewer", "debugger")
        content: Full content/definition of the subagent
        created_at: When the subagent was created
        config_file: Source configuration file path
    """
    name: str
    content: str
    created_at: datetime
    config_file: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert entity to dictionary for serialization."""
        return {
            "name": self.name,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "config_file": self.config_file,
        }


@dataclass
class SlashCommandEntity:
    """
    Represents a Claude slash command configuration.

    Attributes:
        name: Command identifier (e.g., "/review-pr", "/debug")
        content: Command definition/prompt
        created_at: When the command was created
        config_file: Source configuration file path
    """
    name: str
    content: str
    created_at: datetime
    config_file: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert entity to dictionary for serialization."""
        return {
            "name": self.name,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "config_file": self.config_file,
        }


@dataclass
class ClaudeMemoryEntity:
    """
    Represents Claude memory/CLAUDE.md content.

    Attributes:
        scope: Memory scope ("user", "project", "enterprise")
        content: Full memory content
        path: File path to the CLAUDE.md file
    """
    scope: str
    content: str
    path: str

    def to_dict(self) -> dict:
        """Convert entity to dictionary for serialization."""
        return {
            "scope": self.scope,
            "content": self.content,
            "path": self.path,
        }


@dataclass
class EntitySnapshot:
    """
    Complete snapshot of all semantic entities at a point in time.

    This provides a high-level view of Claude's configuration state,
    aggregating all entity types into a single cohesive snapshot.

    Attributes:
        snapshot_id: Database snapshot ID
        snapshot_time: When the snapshot was taken
        mcp_servers: List of MCP server configurations
        subagents: List of subagent configurations
        slash_commands: List of slash command configurations
        memory: Claude memory entity (optional)
    """
    snapshot_id: int
    snapshot_time: datetime
    mcp_servers: list[McpServerEntity] = field(default_factory=list)
    subagents: list[SubagentEntity] = field(default_factory=list)
    slash_commands: list[SlashCommandEntity] = field(default_factory=list)
    memory: Optional[ClaudeMemoryEntity] = None

    def to_dict(self) -> dict:
        """Convert entity snapshot to dictionary for serialization."""
        return {
            "snapshot_id": self.snapshot_id,
            "snapshot_time": self.snapshot_time.isoformat(),
            "mcp_servers": [s.to_dict() for s in self.mcp_servers],
            "subagents": [s.to_dict() for s in self.subagents],
            "slash_commands": [c.to_dict() for c in self.slash_commands],
            "memory": self.memory.to_dict() if self.memory else None,
        }

    def summary(self) -> dict:
        """
        Generate a summary of the entity snapshot.

        Returns:
            Dictionary with snapshot metadata and entity counts:
            - snapshot_id: Database snapshot ID
            - snapshot_time: ISO format timestamp
            - mcp_server_count: Number of MCP servers
            - subagent_count: Number of subagents
            - command_count: Number of slash commands
            - has_memory: Whether memory content exists
        """
        return {
            "snapshot_id": self.snapshot_id,
            "snapshot_time": self.snapshot_time.isoformat(),
            "mcp_server_count": len(self.mcp_servers),
            "subagent_count": len(self.subagents),
            "command_count": len(self.slash_commands),
            "has_memory": self.memory is not None,
        }
