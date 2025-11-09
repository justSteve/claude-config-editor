"""
API request Pydantic schemas.

Provides request models for all API operations.
"""

from typing import Optional

from pydantic import Field

from src.core.schemas.base import BaseSchema, PaginationParams, TimeRangeFilter


class SnapshotCreateRequest(BaseSchema):
    """Request to create a new snapshot."""

    trigger_type: str = Field(
        default="api",
        description="Trigger type (manual, scheduled, api, cli)",
        pattern="^(manual|scheduled|api|cli)$",
    )
    triggered_by: Optional[str] = Field(None, max_length=100, description="User or system triggering scan")
    notes: Optional[str] = Field(None, description="Optional notes about the snapshot")
    tags: Optional[list[str]] = Field(None, description="Tags to apply to snapshot")
    
    # Scan options
    include_content: bool = Field(default=True, description="Whether to capture file contents")
    compress_large_files: bool = Field(default=True, description="Whether to compress large files")
    detect_changes: bool = Field(default=True, description="Whether to detect changes from previous")


class SnapshotQueryRequest(PaginationParams):
    """Request to query snapshots."""

    # Filters
    trigger_type: Optional[str] = Field(None, description="Filter by trigger type")
    triggered_by: Optional[str] = Field(None, description="Filter by triggered by")
    os_type: Optional[str] = Field(None, description="Filter by OS type")
    is_baseline: Optional[bool] = Field(None, description="Filter by baseline status")
    has_changes: Optional[bool] = Field(None, description="Filter by whether snapshot has changes")
    
    # Time range
    time_range: Optional[TimeRangeFilter] = Field(None, description="Time range filter")
    
    # Tags
    tags: Optional[list[str]] = Field(None, description="Filter by tags (any match)")
    tags_all: Optional[list[str]] = Field(None, description="Filter by tags (all must match)")
    
    # Search
    search: Optional[str] = Field(None, description="Search in notes and triggered_by")
    
    # Sorting
    sort_by: str = Field(
        default="snapshot_time",
        description="Field to sort by",
        pattern="^(snapshot_time|id|files_found|total_size_bytes|changed_from_previous)$",
    )


class PathQueryRequest(PaginationParams):
    """Request to query paths."""

    # Required
    snapshot_id: int = Field(..., ge=1, description="Snapshot ID to query paths from")
    
    # Filters
    category: Optional[str] = Field(None, description="Filter by category")
    exists: Optional[bool] = Field(None, description="Filter by existence")
    type: Optional[str] = Field(None, description="Filter by type (file, directory, symlink)")
    has_content: Optional[bool] = Field(None, description="Filter by whether content is captured")
    has_errors: Optional[bool] = Field(None, description="Filter by whether errors occurred")
    
    # Size filters
    min_size_bytes: Optional[int] = Field(None, ge=0, description="Minimum file size")
    max_size_bytes: Optional[int] = Field(None, ge=0, description="Maximum file size")
    
    # Time filters
    modified_after: Optional[str] = Field(None, description="Modified after timestamp")
    modified_before: Optional[str] = Field(None, description="Modified before timestamp")
    
    # Search
    search: Optional[str] = Field(None, description="Search in path names and templates")
    
    # Sorting
    sort_by: str = Field(
        default="name",
        description="Field to sort by",
        pattern="^(name|category|size_bytes|modified_time)$",
    )


class CompareSnapshotsRequest(BaseSchema):
    """Request to compare two snapshots."""

    snapshot_id_1: int = Field(..., ge=1, description="First snapshot ID")
    snapshot_id_2: int = Field(..., ge=1, description="Second snapshot ID")
    
    # Options
    include_unchanged: bool = Field(default=False, description="Include unchanged paths")
    include_content_diff: bool = Field(default=False, description="Include content diffs for text files")
    max_diff_size: int = Field(default=1024 * 1024, description="Max file size for content diff (bytes)")
    
    # Filters
    categories: Optional[list[str]] = Field(None, description="Limit to specific categories")
    change_types: Optional[list[str]] = Field(None, description="Filter by change types")


class TagSnapshotRequest(BaseSchema):
    """Request to tag a snapshot."""

    tag_name: str = Field(..., min_length=1, max_length=255, description="Tag name")
    tag_type: Optional[str] = Field(None, max_length=20, description="Tag type")
    description: Optional[str] = Field(None, description="Tag description")
    created_by: Optional[str] = Field(None, max_length=100, description="Creator name")


class AnnotateSnapshotRequest(BaseSchema):
    """Request to annotate a snapshot."""

    annotation_text: str = Field(..., min_length=1, description="Annotation text")
    annotation_type: Optional[str] = Field(None, max_length=20, description="Annotation type (note, warning, error)")
    created_by: Optional[str] = Field(None, max_length=100, description="Creator name")


class AnnotatePathRequest(BaseSchema):
    """Request to annotate a path."""

    annotation_text: str = Field(..., min_length=1, description="Annotation text")
    annotation_type: Optional[str] = Field(None, max_length=20, description="Annotation type")
    created_by: Optional[str] = Field(None, max_length=100, description="Creator name")


class DeleteSnapshotRequest(BaseSchema):
    """Request to delete snapshot(s)."""

    snapshot_ids: list[int] = Field(..., min_length=1, description="Snapshot IDs to delete")
    delete_orphaned_content: bool = Field(default=True, description="Delete orphaned file contents")
    vacuum_after: bool = Field(default=True, description="Vacuum database after deletion")


class ExportSnapshotRequest(BaseSchema):
    """Request to export snapshot."""

    format: str = Field(
        default="json",
        description="Export format",
        pattern="^(json|yaml|html|csv)$",
    )
    include_content: bool = Field(default=True, description="Include file contents")
    compress: bool = Field(default=False, description="Compress export file")
    
    # Filters
    categories: Optional[list[str]] = Field(None, description="Limit to specific categories")
    include_metadata: bool = Field(default=True, description="Include snapshot metadata")

