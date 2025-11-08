"""
Data models for reporting system.

Defines structured report data that can be rendered in multiple formats.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class FileChange(BaseModel):
    """Represents a single file change between snapshots."""

    path_template: str
    change_type: str  # 'added', 'modified', 'deleted'
    old_size_bytes: Optional[int] = None
    new_size_bytes: Optional[int] = None
    old_modified_time: Optional[datetime] = None
    new_modified_time: Optional[datetime] = None
    old_content_hash: Optional[str] = None
    new_content_hash: Optional[str] = None
    size_delta: Optional[int] = None

    def __init__(self, **data):
        super().__init__(**data)
        # Calculate size delta
        if self.old_size_bytes is not None and self.new_size_bytes is not None:
            self.size_delta = self.new_size_bytes - self.old_size_bytes


class ChangeDetectionReport(BaseModel):
    """Report comparing two snapshots."""

    snapshot_id: int
    snapshot_time: datetime
    previous_snapshot_id: int
    previous_snapshot_time: datetime

    added_files: list[FileChange] = Field(default_factory=list)
    modified_files: list[FileChange] = Field(default_factory=list)
    deleted_files: list[FileChange] = Field(default_factory=list)

    total_changes: int = 0
    size_change_bytes: int = 0

    def __init__(self, **data):
        super().__init__(**data)
        self.total_changes = len(self.added_files) + len(self.modified_files) + len(self.deleted_files)
        self.size_change_bytes = sum(
            (c.size_delta or 0) for c in self.modified_files
        ) + sum(
            (c.new_size_bytes or 0) for c in self.added_files
        ) - sum(
            (c.old_size_bytes or 0) for c in self.deleted_files
        )


class PathInfo(BaseModel):
    """Information about a scanned path."""

    category: str
    name: str
    path_template: str
    exists: bool
    type: Optional[str] = None
    size_bytes: Optional[int] = None


class CategoryStats(BaseModel):
    """Statistics for a category of paths."""

    category: str
    total_locations: int
    found: int
    missing: int
    total_size_bytes: int


class SnapshotSummaryReport(BaseModel):
    """Comprehensive snapshot summary."""

    snapshot_id: int
    snapshot_time: datetime
    snapshot_hash: str
    trigger_type: str
    triggered_by: Optional[str] = None
    notes: Optional[str] = None

    # System context
    os_type: str
    hostname: Optional[str] = None
    username: Optional[str] = None

    # Statistics
    total_locations: int
    files_found: int
    directories_found: int
    total_size_bytes: int

    # Detailed path information
    paths: list[PathInfo] = Field(default_factory=list)

    # Category breakdown
    category_stats: list[CategoryStats] = Field(default_factory=list)

    # Deduplication info
    unique_contents: int = 0
    deduplication_savings_bytes: int = 0
    deduplication_percent: float = 0.0


class DeduplicationReport(BaseModel):
    """Report on content deduplication statistics."""

    total_file_contents: int
    unique_hashes: int
    total_references: int
    total_size_bytes: int
    deduplicated_size_bytes: int
    savings_bytes: int
    savings_percent: float

    # Top duplicated files
    most_referenced: list[dict] = Field(default_factory=list)
