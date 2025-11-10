"""
Pydantic schemas for Claude Config API endpoints.

Provides request and response models for querying and analyzing
Claude configuration files across snapshots.
"""

from datetime import datetime
from typing import Optional

from pydantic import Field

from src.core.schemas.base import BaseSchema, PaginatedResponse


class ClaudeConfigSummary(BaseSchema):
    """Summary view of Claude configuration for list endpoints."""

    id: int = Field(..., description="Config ID")
    config_type: str = Field(..., description="Configuration type (desktop/project/enterprise)")
    num_projects: Optional[int] = Field(None, description="Number of projects")
    num_mcp_servers: Optional[int] = Field(None, description="Number of MCP servers")
    num_startups: Optional[int] = Field(None, description="Number of startups")
    total_size_bytes: Optional[int] = Field(None, description="Total file size in bytes")
    snapshot_id: int = Field(..., description="Snapshot ID")
    snapshot_time: datetime = Field(..., description="Snapshot timestamp")


class ClaudeConfigDetail(ClaudeConfigSummary):
    """Detailed view of Claude configuration with additional metadata."""

    largest_project_path: Optional[str] = Field(None, description="Path to largest project")
    largest_project_size: Optional[int] = Field(None, description="Largest project size in bytes")
    resolved_path: str = Field(..., description="Full resolved file path")
    content_hash: Optional[str] = Field(None, description="SHA256 content hash")
    modified_time: Optional[datetime] = Field(None, description="File last modified time")


class ConfigDifferences(BaseSchema):
    """Differences between two Claude configurations."""

    projects_added: int = Field(0, description="Number of projects added")
    projects_removed: int = Field(0, description="Number of projects removed")
    projects_modified: list[str] = Field(default_factory=list, description="Paths of modified projects")
    mcp_servers_added: int = Field(0, description="Number of MCP servers added")
    mcp_servers_removed: int = Field(0, description="Number of MCP servers removed")
    mcp_servers_modified: list[str] = Field(default_factory=list, description="Names of modified MCP servers")
    size_change_bytes: int = Field(0, description="Change in total size (bytes)")
    size_change_percent: float = Field(0.0, description="Percentage change in size")


class ClaudeConfigComparison(BaseSchema):
    """Comparison of two Claude configurations."""

    config_1: ClaudeConfigSummary = Field(..., description="First configuration")
    config_2: ClaudeConfigSummary = Field(..., description="Second configuration")
    differences: ConfigDifferences = Field(..., description="Detected differences")


class ConfigSummaryStats(BaseSchema):
    """Aggregate statistics for Claude configurations in a snapshot."""

    total_configs: int = Field(..., description="Total number of configs found")
    config_types: dict[str, int] = Field(..., description="Count by config type")
    total_projects: int = Field(..., description="Total projects across all configs")
    total_mcp_servers: int = Field(..., description="Total MCP servers across all configs")
    total_size_bytes: int = Field(..., description="Combined size of all configs")
    largest_config_type: Optional[str] = Field(None, description="Config type with most projects")
    bloat_candidates: list[ClaudeConfigSummary] = Field(
        default_factory=list,
        description="Configs larger than 1MB (potential bloat)"
    )


class ClaudeConfigListResponse(PaginatedResponse):
    """Response for list of Claude configurations."""

    items: list[ClaudeConfigSummary] = Field(default_factory=list, description="Configuration summaries")


class ClaudeConfigDetailResponse(BaseSchema):
    """Response for detailed Claude configuration view."""

    config: ClaudeConfigDetail = Field(..., description="Configuration details")
