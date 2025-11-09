"""
Change tracking related Pydantic schemas.

Provides models for tracking changes between snapshots.
"""

from datetime import datetime
from typing import Optional

from pydantic import Field

from src.core.schemas.base import BaseSchema, PaginatedResponse


class ChangeBase(BaseSchema):
    """Base change schema."""

    path_template: str = Field(..., description="Path template")
    change_type: str = Field(..., description="Change type (added, modified, deleted)")


class ChangeResponse(ChangeBase):
    """Basic change response."""

    id: int = Field(..., description="Change ID")
    snapshot_id: int = Field(..., description="Current snapshot ID")
    previous_snapshot_id: int = Field(..., description="Previous snapshot ID")
    
    # For modified files
    old_content_hash: Optional[str] = Field(None, description="Old content hash")
    new_content_hash: Optional[str] = Field(None, description="New content hash")
    old_size_bytes: Optional[int] = Field(None, description="Old size in bytes")
    new_size_bytes: Optional[int] = Field(None, description="New size in bytes")


class ChangeSummary(ChangeResponse):
    """Change summary with additional details."""

    old_modified_time: Optional[datetime] = Field(None, description="Old modification time")
    new_modified_time: Optional[datetime] = Field(None, description="New modification time")
    diff_summary: Optional[str] = Field(None, description="Diff summary")
    
    # Computed fields
    size_change_bytes: Optional[int] = Field(None, description="Size change in bytes")
    size_change_percent: Optional[float] = Field(None, description="Size change percentage")


class ChangeListResponse(PaginatedResponse[ChangeSummary]):
    """Paginated list of changes."""

    pass


class ChangeStatsResponse(BaseSchema):
    """Change statistics response."""

    total_changes: int = Field(..., description="Total number of changes")
    added: int = Field(..., description="Number of added paths")
    modified: int = Field(..., description="Number of modified paths")
    deleted: int = Field(..., description="Number of deleted paths")
    total_size_added: int = Field(..., description="Total size added in bytes")
    total_size_removed: int = Field(..., description="Total size removed in bytes")

