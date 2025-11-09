"""
Path and file content related Pydantic schemas.

Provides models for paths, file contents, MCP servers, and Claude configs.
"""

from datetime import datetime
from typing import Optional

from pydantic import Field

from src.core.schemas.base import BaseSchema, PaginatedResponse


class PathBase(BaseSchema):
    """Base path schema with common fields."""

    category: str = Field(..., description="Path category")
    name: str = Field(..., description="Path name")
    path_template: str = Field(...,
                               description="Path template with placeholders")
    resolved_path: str = Field(..., description="Resolved actual path")


class PathResponse(PathBase):
    """Basic path response."""

    id: int = Field(..., description="Path ID")
    snapshot_id: int = Field(...,
                             description="Snapshot ID this path belongs to")
    exists: bool = Field(..., description="Whether path exists")
    type: Optional[str] = Field(
        None, description="Path type (file, directory, symlink)")

    # File metadata
    size_bytes: Optional[int] = Field(None, description="File size in bytes")
    modified_time: Optional[datetime] = Field(
        None, description="Last modified time")
    content_hash: Optional[str] = Field(
        None, description="Content hash (SHA256)")


class PathSummary(PathResponse):
    """Path summary with additional metadata."""

    created_time: Optional[datetime] = Field(None, description="Creation time")
    accessed_time: Optional[datetime] = Field(
        None, description="Last access time")
    permissions: Optional[str] = Field(None, description="File permissions")

    # Directory metadata
    item_count: Optional[int] = Field(
        None, description="Number of items in directory")

    # Error handling
    error_message: Optional[str] = Field(
        None, description="Error message if scan failed")


class FileContentResponse(BaseSchema):
    """File content response."""

    id: int = Field(..., description="Content ID")
    content_hash: str = Field(..., description="Content hash (SHA256)")
    content_type: str = Field(...,
                              description="Content type (json, text, binary, markdown)")
    size_bytes: int = Field(..., description="Content size in bytes")
    compression: str = Field(...,
                             description="Compression type (none, gzip, zlib)")
    reference_count: int = Field(...,
                                 description="Number of paths referencing this content")
    created_at: datetime = Field(..., description="When content was stored")

    # Actual content (optional, may be large)
    content_text: Optional[str] = Field(None, description="Text content")
    content_binary: Optional[bytes] = Field(None, description="Binary content")


class JsonDataResponse(BaseSchema):
    """Parsed JSON data response."""

    id: int = Field(..., description="JSON data ID")
    json_path: str = Field(...,
                           description="JSON path (e.g., 'mcpServers.server1.command')")
    json_value: Optional[str] = Field(None, description="JSON value as string")
    json_type: str = Field(..., description="JSON value type")


class McpServerResponse(BaseSchema):
    """MCP server configuration response."""

    id: int = Field(..., description="MCP server ID")
    server_name: str = Field(..., description="Server name")
    command: Optional[str] = Field(None, description="Command to run")
    args: Optional[str] = Field(None, description="Arguments (JSON array)")
    env: Optional[str] = Field(
        None, description="Environment variables (JSON object)")
    working_directory: Optional[str] = Field(
        None, description="Working directory")


class ClaudeConfigResponse(BaseSchema):
    """Claude configuration response."""

    id: int = Field(..., description="Config ID")
    config_type: str = Field(..., description="Configuration type")
    num_projects: Optional[int] = Field(None, description="Number of projects")
    num_mcp_servers: Optional[int] = Field(
        None, description="Number of MCP servers")
    num_startups: Optional[int] = Field(
        None, description="Number of startup configurations")
    total_size_bytes: Optional[int] = Field(
        None, description="Total size in bytes")
    largest_project_path: Optional[str] = Field(
        None, description="Path to largest project")
    largest_project_size: Optional[int] = Field(
        None, description="Largest project size")


class PathDetailResponse(PathSummary):
    """Detailed path response with all relationships."""

    # Related data
    content: Optional[FileContentResponse] = Field(
        None, description="File content")
    json_data: list[JsonDataResponse] = Field(
        default_factory=list, description="Parsed JSON data")
    claude_config: Optional[ClaudeConfigResponse] = Field(
        None, description="Claude config details")
    mcp_servers: list[McpServerResponse] = Field(
        default_factory=list, description="MCP servers")
    annotations: list["PathAnnotationResponse"] = Field(
        default_factory=list, description="Annotations")


class PathAnnotationResponse(BaseSchema):
    """Path annotation response."""

    id: int = Field(..., description="Annotation ID")
    annotation_text: str = Field(..., description="Annotation text")
    annotation_type: Optional[str] = Field(None, description="Annotation type")
    created_at: datetime = Field(...,
                                 description="When annotation was created")
    created_by: Optional[str] = Field(
        None, description="Who created the annotation")


class PathListResponse(PaginatedResponse[PathSummary]):
    """Paginated list of paths."""

    pass


# Update forward references
PathDetailResponse.model_rebuild()
