"""
MCP server related Pydantic schemas.

Provides models for MCP server queries, responses, and related data.
"""

from datetime import datetime
from typing import Optional, Any

from pydantic import Field

from src.core.schemas.base import BaseSchema, PaginatedResponse
from src.core.schemas.paths import McpServerResponse


class McpServerSummary(BaseSchema):
    """MCP server summary for list views."""

    id: int = Field(..., description="MCP server ID")
    server_name: str = Field(..., description="Server name")
    command: Optional[str] = Field(None, description="Command to run")
    snapshot_id: int = Field(..., description="Snapshot ID where found")
    snapshot_path_id: int = Field(..., description="Path ID where found")
    config_file: str = Field(..., description="Configuration file path")


class McpServerDetail(McpServerResponse):
    """Detailed MCP server information."""

    snapshot_path_id: int = Field(..., description="Path ID where found")

    # Related info
    snapshot_id: int = Field(..., description="Snapshot ID where found")
    config_file: str = Field(..., description="Configuration file path")
    snapshot_time: datetime = Field(..., description="When snapshot was created")


class McpServerStatusResponse(BaseSchema):
    """MCP server operational status."""

    server_id: int = Field(..., description="MCP server ID")
    server_name: str = Field(..., description="Server name")
    status: str = Field(..., description="Status (detected/configured/unknown)")
    last_seen: datetime = Field(..., description="Last time server was seen in a snapshot")
    snapshot_count: int = Field(..., description="Number of snapshots containing this server")
    config_locations: list[str] = Field(
        default_factory=list,
        description="Configuration file locations"
    )


class McpServerConfigResponse(BaseSchema):
    """MCP server configuration (with sanitization)."""

    server_id: int = Field(..., description="MCP server ID")
    server_name: str = Field(..., description="Server name")
    command: Optional[str] = Field(None, description="Command (may be redacted)")
    args: Optional[dict[str, Any]] = Field(
        None,
        description="Arguments (sanitized)"
    )
    env: Optional[dict[str, str]] = Field(
        None,
        description="Environment variables (sanitized)"
    )
    working_directory: Optional[str] = Field(
        None,
        description="Working directory (may be redacted)"
    )
    sanitized: bool = Field(
        ...,
        description="Whether response has been sanitized for security"
    )


class McpServerCapabilitiesResponse(BaseSchema):
    """MCP server capabilities (if detectable)."""

    server_id: int = Field(..., description="MCP server ID")
    server_name: str = Field(..., description="Server name")
    command_type: Optional[str] = Field(
        None,
        description="Type of command (node, python, binary, etc.)"
    )
    has_args: bool = Field(..., description="Whether server has arguments configured")
    has_env: bool = Field(..., description="Whether server has environment variables")
    has_working_dir: bool = Field(..., description="Whether server has working directory set")


class McpServerLogsResponse(BaseSchema):
    """MCP server logs information."""

    server_id: int = Field(..., description="MCP server ID")
    server_name: str = Field(..., description="Server name")
    log_files_found: int = Field(..., description="Number of log files found")
    log_locations: list[str] = Field(
        default_factory=list,
        description="Log file paths (may be redacted)"
    )
    sanitized: bool = Field(
        ...,
        description="Whether response has been sanitized for security"
    )


class McpServerListResponse(PaginatedResponse[McpServerSummary]):
    """Paginated list of MCP servers."""

    pass


class McpServerStatsResponse(BaseSchema):
    """Statistics about MCP servers across snapshots."""

    total_servers: int = Field(..., description="Total unique servers found")
    total_configurations: int = Field(..., description="Total server configurations across all snapshots")
    servers_by_snapshot: dict[str, int] = Field(
        default_factory=dict,
        description="Server count by snapshot ID"
    )
    most_common_servers: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Most commonly configured servers"
    )
    config_file_locations: list[str] = Field(
        default_factory=list,
        description="Configuration file locations"
    )
