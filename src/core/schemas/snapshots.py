"""
Snapshot-related Pydantic schemas.

Provides models for snapshots, tags, annotations, and environment variables.
"""

from datetime import datetime
from typing import Optional

from pydantic import Field

from src.core.schemas.base import BaseSchema, PaginatedResponse


class SnapshotBase(BaseSchema):
    """Base snapshot schema with common fields."""

    trigger_type: str = Field(...,
                              description="Trigger type (manual, scheduled, api, cli)")
    triggered_by: Optional[str] = Field(
        None, description="User or system that triggered snapshot")
    notes: Optional[str] = Field(
        None, description="Optional notes about the snapshot")


class SnapshotCreate(SnapshotBase):
    """Schema for creating a new snapshot."""

    tags: Optional[list[str]] = Field(
        None, description="Tags to apply to snapshot")


class SnapshotResponse(BaseSchema):
    """Basic snapshot response schema."""

    id: int = Field(..., description="Snapshot ID")
    snapshot_time: datetime = Field(...,
                                    description="When snapshot was created")
    snapshot_hash: str = Field(...,
                               description="SHA256 hash of snapshot content")
    trigger_type: str = Field(..., description="Trigger type")
    triggered_by: Optional[str] = Field(None, description="Triggered by")
    notes: Optional[str] = Field(None, description="Notes")

    # System context
    os_type: str = Field(..., description="Operating system type")
    os_version: Optional[str] = Field(None, description="OS version")
    hostname: Optional[str] = Field(None, description="System hostname")
    username: Optional[str] = Field(None, description="Username")


class SnapshotSummary(SnapshotResponse):
    """Summary snapshot schema with statistics."""

    total_locations: int = Field(..., description="Total locations scanned")
    files_found: int = Field(..., description="Number of files found")
    directories_found: int = Field(...,
                                   description="Number of directories found")
    total_size_bytes: int = Field(..., description="Total size in bytes")
    changed_from_previous: Optional[int] = Field(
        None, description="Number of changes from previous")
    is_baseline: bool = Field(...,
                              description="Whether this is a baseline snapshot")

    # Tags
    tags: list[str] = Field(default_factory=list,
                            description="Tags applied to snapshot")


class SnapshotEnvVarResponse(BaseSchema):
    """Environment variable response."""

    placeholder: str = Field(...,
                             description="Environment variable placeholder")
    resolved_path: str = Field(..., description="Resolved path value")


class SnapshotTagResponse(BaseSchema):
    """Snapshot tag response."""

    id: int = Field(..., description="Tag ID")
    tag_name: str = Field(..., description="Tag name")
    tag_type: Optional[str] = Field(None, description="Tag type")
    created_at: datetime = Field(..., description="When tag was created")
    created_by: Optional[str] = Field(None, description="Who created the tag")
    description: Optional[str] = Field(None, description="Tag description")


class SnapshotAnnotationResponse(BaseSchema):
    """Snapshot annotation response."""

    id: int = Field(..., description="Annotation ID")
    annotation_text: str = Field(..., description="Annotation text")
    annotation_type: Optional[str] = Field(None, description="Annotation type")
    created_at: datetime = Field(...,
                                 description="When annotation was created")
    created_by: Optional[str] = Field(
        None, description="Who created the annotation")


class SnapshotDetailResponse(SnapshotSummary):
    """Detailed snapshot response with relationships."""

    parent_snapshot_id: Optional[int] = Field(
        None, description="Parent snapshot ID")
    working_directory: Optional[str] = Field(
        None, description="Working directory at scan time")

    # Relationships
    env_vars: list[SnapshotEnvVarResponse] = Field(
        default_factory=list, description="Environment variables")
    annotations: list[SnapshotAnnotationResponse] = Field(
        default_factory=list, description="Annotations")
    tag_details: list[SnapshotTagResponse] = Field(
        default_factory=list, description="Tag details")


class SnapshotStatsResponse(BaseSchema):
    """Snapshot statistics response."""

    total_snapshots: int = Field(..., description="Total number of snapshots")
    total_size_bytes: int = Field(..., description="Total storage used")
    oldest_snapshot: Optional[datetime] = Field(
        None, description="Oldest snapshot time")
    newest_snapshot: Optional[datetime] = Field(
        None, description="Newest snapshot time")
    average_files_per_snapshot: float = Field(
        ..., description="Average files per snapshot")
    total_changes_tracked: int = Field(...,
                                       description="Total changes tracked")


class SnapshotListResponse(PaginatedResponse[SnapshotSummary]):
    """Paginated list of snapshots."""

    pass


class SnapshotTagCreate(BaseSchema):
    """Schema for creating a snapshot tag."""

    tag_name: str = Field(..., min_length=1,
                          max_length=255, description="Tag name")
    tag_type: Optional[str] = Field(
        None, max_length=20, description="Tag type")
    description: Optional[str] = Field(None, description="Tag description")
    created_by: Optional[str] = Field(
        None, max_length=100, description="Creator name")


class SnapshotAnnotationCreate(BaseSchema):
    """Schema for creating a snapshot annotation."""

    annotation_text: str = Field(..., min_length=1,
                                 description="Annotation text")
    annotation_type: Optional[str] = Field(
        None, max_length=20, description="Annotation type")
    created_by: Optional[str] = Field(
        None, max_length=100, description="Creator name")
