"""
Pydantic schemas for Claude Config API.

This module provides request and response models for the API,
including model converters to transform database models to API schemas.
"""

# Base models
from src.core.schemas.base import (
    BaseSchema,
    ErrorResponse,
    MessageResponse,
    PaginationParams,
    PaginatedResponse,
)

# Snapshot schemas
from src.core.schemas.snapshots import (
    SnapshotBase,
    SnapshotCreate,
    SnapshotResponse,
    SnapshotSummary,
    SnapshotListResponse,
    SnapshotDetailResponse,
    SnapshotStatsResponse,
    SnapshotTagCreate,
    SnapshotTagResponse,
    SnapshotAnnotationCreate,
    SnapshotAnnotationResponse,
)

# Path schemas
from src.core.schemas.paths import (
    PathBase,
    PathResponse,
    PathSummary,
    PathDetailResponse,
    FileContentResponse,
    McpServerResponse,
    ClaudeConfigResponse,
)

# Change schemas
from src.core.schemas.changes import (
    ChangeBase,
    ChangeResponse,
    ChangeSummary,
    ChangeListResponse,
)

# Request schemas
from src.core.schemas.requests import (
    SnapshotCreateRequest,
    SnapshotQueryRequest,
    PathQueryRequest,
    CompareSnapshotsRequest,
    TagSnapshotRequest,
    AnnotateSnapshotRequest,
    AnnotatePathRequest,
)

# Response schemas
from src.core.schemas.responses import (
    SnapshotCreatedResponse,
    SnapshotsListResponse,
    SnapshotDetailedResponse,
    PathsListResponse,
    PathDetailedResponse,
    ChangesComparisonResponse,
    DatabaseStatsResponse,
    HealthCheckResponse,
)

# Converters
from src.core.schemas.converters import (
    snapshot_to_response,
    snapshot_to_summary,
    snapshot_to_detail,
    path_to_response,
    path_to_summary,
    path_to_detail,
    change_to_response,
    tag_to_response,
    annotation_to_response,
)

__all__ = [
    # Base
    "BaseSchema",
    "ErrorResponse",
    "MessageResponse",
    "PaginationParams",
    "PaginatedResponse",
    # Snapshots
    "SnapshotBase",
    "SnapshotCreate",
    "SnapshotResponse",
    "SnapshotSummary",
    "SnapshotListResponse",
    "SnapshotDetailResponse",
    "SnapshotStatsResponse",
    "SnapshotTagCreate",
    "SnapshotTagResponse",
    "SnapshotAnnotationCreate",
    "SnapshotAnnotationResponse",
    # Paths
    "PathBase",
    "PathResponse",
    "PathSummary",
    "PathDetailResponse",
    "FileContentResponse",
    "McpServerResponse",
    "ClaudeConfigResponse",
    # Changes
    "ChangeBase",
    "ChangeResponse",
    "ChangeSummary",
    "ChangeListResponse",
    # Requests
    "SnapshotCreateRequest",
    "SnapshotQueryRequest",
    "PathQueryRequest",
    "CompareSnapshotsRequest",
    "TagSnapshotRequest",
    "AnnotateSnapshotRequest",
    "AnnotatePathRequest",
    # Responses
    "SnapshotCreatedResponse",
    "SnapshotsListResponse",
    "SnapshotDetailedResponse",
    "PathsListResponse",
    "PathDetailedResponse",
    "ChangesComparisonResponse",
    "DatabaseStatsResponse",
    "HealthCheckResponse",
    # Converters
    "snapshot_to_response",
    "snapshot_to_summary",
    "snapshot_to_detail",
    "path_to_response",
    "path_to_summary",
    "path_to_detail",
    "change_to_response",
    "tag_to_response",
    "annotation_to_response",
]

