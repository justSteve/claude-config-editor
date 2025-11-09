"""
API response Pydantic schemas.

Provides unified response models for all API operations.
"""

from datetime import datetime
from typing import Optional

from pydantic import Field

from src.core.schemas.base import BaseSchema, PaginatedResponse
from src.core.schemas.snapshots import SnapshotDetailResponse, SnapshotSummary
from src.core.schemas.paths import PathDetailResponse, PathSummary
from src.core.schemas.changes import ChangeSummary, ChangeStatsResponse


class SnapshotCreatedResponse(BaseSchema):
    """Response after creating a snapshot."""

    snapshot_id: int = Field(..., description="Created snapshot ID")
    snapshot_hash: str = Field(..., description="Snapshot hash")
    snapshot_time: datetime = Field(..., description="Snapshot creation time")

    # Statistics
    files_found: int = Field(..., description="Number of files found")
    directories_found: int = Field(...,
                                   description="Number of directories found")
    total_size_bytes: int = Field(..., description="Total size in bytes")

    # Change detection
    changes_detected: bool = Field(...,
                                   description="Whether changes were detected")
    changed_from_previous: Optional[int] = Field(
        None, description="Number of changes")

    # Processing info
    scan_duration_seconds: float = Field(...,
                                         description="Scan duration in seconds")
    content_captured: int = Field(...,
                                  description="Number of files with content captured")
    errors_encountered: int = Field(...,
                                    description="Number of errors encountered")

    # Message
    message: str = Field(..., description="Success message")


class SnapshotsListResponse(PaginatedResponse[SnapshotSummary]):
    """Paginated list of snapshots."""

    # Additional stats
    total_size_all_bytes: int = Field(
        default=0, description="Total size of all snapshots")
    date_range_start: Optional[datetime] = Field(
        None, description="Earliest snapshot time")
    date_range_end: Optional[datetime] = Field(
        None, description="Latest snapshot time")


class SnapshotDetailedResponse(BaseSchema):
    """Detailed snapshot response."""

    snapshot: SnapshotDetailResponse = Field(...,
                                             description="Snapshot details")

    # Related paths summary
    paths_summary: dict[str,
                        int] = Field(..., description="Paths grouped by category")

    # Related changes summary
    changes_summary: Optional[ChangeStatsResponse] = Field(
        None, description="Changes summary")


class PathsListResponse(PaginatedResponse[PathSummary]):
    """Paginated list of paths."""

    # Additional stats
    snapshot_id: int = Field(...,
                             description="Snapshot ID these paths belong to")
    total_size_bytes: int = Field(
        default=0, description="Total size of all paths")
    files_count: int = Field(default=0, description="Number of files")
    directories_count: int = Field(
        default=0, description="Number of directories")


class PathDetailedResponse(BaseSchema):
    """Detailed path response."""

    path: PathDetailResponse = Field(..., description="Path details")

    # Historical info
    changes_history: list[ChangeSummary] = Field(
        default_factory=list,
        description="History of changes to this path"
    )

    # Related info
    previous_versions: list[PathSummary] = Field(
        default_factory=list,
        description="Previous versions in other snapshots"
    )


class ChangesComparisonResponse(BaseSchema):
    """Response for snapshot comparison."""

    snapshot_1: SnapshotSummary = Field(..., description="First snapshot")
    snapshot_2: SnapshotSummary = Field(..., description="Second snapshot")

    # Statistics
    stats: ChangeStatsResponse = Field(..., description="Change statistics")

    # Changes
    changes: list[ChangeSummary] = Field(..., description="List of changes")

    # Summary
    summary: str = Field(..., description="Human-readable summary")
    is_identical: bool = Field(...,
                               description="Whether snapshots are identical")


class DatabaseStatsResponse(BaseSchema):
    """Database statistics response."""

    # Table counts
    snapshots_count: int = Field(..., description="Number of snapshots")
    paths_count: int = Field(..., description="Number of paths")
    file_contents_count: int = Field(...,
                                     description="Number of file contents")
    changes_count: int = Field(..., description="Number of changes")
    tags_count: int = Field(..., description="Number of tags")
    annotations_count: int = Field(..., description="Number of annotations")

    # Size info
    database_size_bytes: int = Field(..., description="Database size in bytes")
    total_content_size_bytes: int = Field(...,
                                          description="Total content size in bytes")

    # Additional stats
    mcp_servers_count: int = Field(
        default=0, description="Number of MCP servers tracked")
    claude_configs_count: int = Field(
        default=0, description="Number of Claude configs tracked")
    json_data_count: int = Field(
        default=0, description="Number of JSON data entries")

    # Date range
    oldest_snapshot: Optional[datetime] = Field(
        None, description="Oldest snapshot time")
    newest_snapshot: Optional[datetime] = Field(
        None, description="Newest snapshot time")


class HealthCheckResponse(BaseSchema):
    """Health check response."""

    status: str = Field(...,
                        description="Health status (healthy, degraded, unhealthy)")
    database_connected: bool = Field(...,
                                     description="Database connection status")
    database_size_mb: float = Field(..., description="Database size in MB")

    # Statistics
    total_snapshots: int = Field(..., description="Total snapshots")
    total_paths: int = Field(..., description="Total paths")

    # System info
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Check timestamp")
    uptime_seconds: Optional[float] = Field(
        None, description="Application uptime in seconds")


class ExportResponse(BaseSchema):
    """Export operation response."""

    export_path: str = Field(..., description="Path to exported file")
    export_format: str = Field(..., description="Export format")
    file_size_bytes: int = Field(..., description="Export file size")
    compressed: bool = Field(..., description="Whether export is compressed")

    # Export stats
    snapshots_exported: int = Field(...,
                                    description="Number of snapshots exported")
    paths_exported: int = Field(..., description="Number of paths exported")
    export_duration_seconds: float = Field(..., description="Export duration")

    message: str = Field(..., description="Success message")


class DeleteResponse(BaseSchema):
    """Delete operation response."""

    deleted_count: int = Field(..., description="Number of items deleted")
    snapshot_ids: list[int] = Field(..., description="Deleted snapshot IDs")
    orphaned_content_deleted: int = Field(
        default=0, description="Orphaned content items deleted")
    space_freed_bytes: int = Field(..., description="Space freed in bytes")
    vacuum_performed: bool = Field(...,
                                   description="Whether vacuum was performed")

    message: str = Field(..., description="Success message")
