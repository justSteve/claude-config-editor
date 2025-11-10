"""
Snapshot API endpoints.

Provides CRUD operations for snapshots, tags, and annotations.
"""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.schemas import (
    SnapshotCreateRequest,
    SnapshotCreatedResponse,
    SnapshotQueryRequest,
    SnapshotsListResponse,
    SnapshotDetailResponse,
    SnapshotTagCreate,
    SnapshotTagResponse,
    SnapshotAnnotationCreate,
    SnapshotAnnotationResponse,
    MessageResponse,
    PaginationParams,
)
from src.core.schemas.converters import (
    snapshot_to_summary,
    snapshot_to_detail,
    tag_to_response,
    annotation_to_response,
)
from src.api.dependencies import get_db, get_pagination
from src.api.services import SnapshotService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/snapshots",
    response_model=SnapshotCreatedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new snapshot",
    description="Create a new configuration snapshot by scanning Claude configuration files.",
)
async def create_snapshot(
    request: SnapshotCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> SnapshotCreatedResponse:
    """
    Create a new snapshot.

    This endpoint triggers a scan of Claude configuration files and creates
    a new snapshot with the current state.

    Args:
        request: Snapshot creation parameters
        db: Database session

    Returns:
        Created snapshot details with statistics
    """
    service = SnapshotService(db)

    # Create snapshot
    snapshot = await service.create_snapshot(request)

    # Get statistics
    stats = await service.get_snapshot_stats(snapshot.id)

    return SnapshotCreatedResponse(
        snapshot_id=snapshot.id,
        snapshot_hash=snapshot.snapshot_hash,
        snapshot_time=snapshot.snapshot_time,
        files_found=snapshot.files_found,
        directories_found=snapshot.directories_found,
        total_size_bytes=snapshot.total_size_bytes,
        changes_detected=False,  # TODO: Implement change detection
        changed_from_previous=snapshot.changed_from_previous,
        scan_duration_seconds=0.0,  # TODO: Track scan duration
        content_captured=0,  # TODO: Track content capture
        errors_encountered=0,  # TODO: Track errors
        message=f"Snapshot {snapshot.id} created successfully",
    )


@router.get(
    "/snapshots",
    response_model=SnapshotsListResponse,
    summary="List snapshots",
    description="List all snapshots with optional filtering, sorting, and pagination.",
)
async def list_snapshots(
    trigger_type: str | None = None,
    triggered_by: str | None = None,
    os_type: str | None = None,
    is_baseline: bool | None = None,
    has_changes: bool | None = None,
    search: str | None = None,
    pagination: PaginationParams = Depends(get_pagination),
    db: AsyncSession = Depends(get_db),
) -> SnapshotsListResponse:
    """
    List snapshots with filtering and pagination.

    Args:
        trigger_type: Filter by trigger type
        triggered_by: Filter by who triggered it
        os_type: Filter by OS type
        is_baseline: Filter by baseline status
        has_changes: Filter by whether snapshot has changes
        search: Search in notes and triggered_by
        pagination: Pagination parameters
        db: Database session

    Returns:
        Paginated list of snapshot summaries
    """
    service = SnapshotService(db)

    # Build query params
    query_params = SnapshotQueryRequest(
        page=pagination.page,
        page_size=pagination.page_size,
        sort_by=pagination.sort_by or "snapshot_time",
        sort_order=pagination.sort_order,
        trigger_type=trigger_type,
        triggered_by=triggered_by,
        os_type=os_type,
        is_baseline=is_baseline,
        has_changes=has_changes,
        search=search,
    )

    # Get paginated results
    paginated = await service.list_snapshots(query_params)

    # Calculate additional stats
    total_size = sum(s.total_size_bytes for s in paginated.items)
    date_range_start = min(
        (s.snapshot_time for s in paginated.items), default=None)
    date_range_end = max(
        (s.snapshot_time for s in paginated.items), default=None)

    return SnapshotsListResponse(
        items=paginated.items,
        total=paginated.total,
        page=paginated.page,
        page_size=paginated.page_size,
        total_pages=paginated.total_pages,
        has_next=paginated.has_next,
        has_previous=paginated.has_previous,
        total_size_all_bytes=total_size,
        date_range_start=date_range_start,
        date_range_end=date_range_end,
    )


@router.get(
    "/snapshots/{snapshot_id}",
    response_model=SnapshotDetailResponse,
    summary="Get snapshot details",
    description="Get detailed information about a specific snapshot including all relationships.",
)
async def get_snapshot(
    snapshot_id: int,
    db: AsyncSession = Depends(get_db),
) -> SnapshotDetailResponse:
    """
    Get snapshot details.

    Args:
        snapshot_id: Snapshot ID
        db: Database session

    Returns:
        Detailed snapshot information
    """
    service = SnapshotService(db)
    snapshot = await service.get_snapshot(snapshot_id, load_relationships=True)

    return snapshot_to_detail(snapshot)


@router.delete(
    "/snapshots/{snapshot_id}",
    response_model=MessageResponse,
    summary="Delete snapshot",
    description="Delete a snapshot and all associated data.",
)
async def delete_snapshot(
    snapshot_id: int,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """
    Delete snapshot.

    Args:
        snapshot_id: Snapshot ID
        db: Database session

    Returns:
        Success message
    """
    service = SnapshotService(db)
    await service.delete_snapshot(snapshot_id)

    return MessageResponse(
        message=f"Snapshot {snapshot_id} deleted successfully",
        success=True,
    )


@router.post(
    "/snapshots/{snapshot_id}/tags",
    response_model=SnapshotTagResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add tag to snapshot",
    description="Add a new tag to a snapshot for organization and categorization.",
)
async def add_tag(
    snapshot_id: int,
    request: SnapshotTagCreate,
    db: AsyncSession = Depends(get_db),
) -> SnapshotTagResponse:
    """
    Add tag to snapshot.

    Args:
        snapshot_id: Snapshot ID
        request: Tag creation parameters
        db: Database session

    Returns:
        Created tag details
    """
    service = SnapshotService(db)

    tag = await service.add_tag(
        snapshot_id=snapshot_id,
        tag_name=request.tag_name,
        tag_type=request.tag_type,
        description=request.description,
        created_by=request.created_by,
    )

    return tag_to_response(tag)


@router.delete(
    "/snapshots/{snapshot_id}/tags/{tag_id}",
    response_model=MessageResponse,
    summary="Remove tag from snapshot",
    description="Remove a tag from a snapshot.",
)
async def remove_tag(
    snapshot_id: int,
    tag_id: int,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """
    Remove tag from snapshot.

    Args:
        snapshot_id: Snapshot ID
        tag_id: Tag ID to remove
        db: Database session

    Returns:
        Success message
    """
    service = SnapshotService(db)
    await service.remove_tag(snapshot_id, tag_id)

    return MessageResponse(
        message=f"Tag {tag_id} removed from snapshot {snapshot_id}",
        success=True,
    )


@router.post(
    "/snapshots/{snapshot_id}/annotations",
    response_model=SnapshotAnnotationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add annotation to snapshot",
    description="Add a text annotation to a snapshot for documentation.",
)
async def add_annotation(
    snapshot_id: int,
    request: SnapshotAnnotationCreate,
    db: AsyncSession = Depends(get_db),
) -> SnapshotAnnotationResponse:
    """
    Add annotation to snapshot.

    Args:
        snapshot_id: Snapshot ID
        request: Annotation creation parameters
        db: Database session

    Returns:
        Created annotation details
    """
    service = SnapshotService(db)

    annotation = await service.add_annotation(
        snapshot_id=snapshot_id,
        annotation_text=request.annotation_text,
        annotation_type=request.annotation_type,
        created_by=request.created_by,
    )

    return annotation_to_response(annotation)


@router.delete(
    "/snapshots/{snapshot_id}/annotations/{annotation_id}",
    response_model=MessageResponse,
    summary="Remove annotation from snapshot",
    description="Remove an annotation from a snapshot.",
)
async def remove_annotation(
    snapshot_id: int,
    annotation_id: int,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """
    Remove annotation from snapshot.

    Args:
        snapshot_id: Snapshot ID
        annotation_id: Annotation ID to remove
        db: Database session

    Returns:
        Success message
    """
    service = SnapshotService(db)
    await service.remove_annotation(snapshot_id, annotation_id)

    return MessageResponse(
        message=f"Annotation {annotation_id} removed from snapshot {snapshot_id}",
        success=True,
    )


@router.get(
    "/snapshots/{snapshot_id}/annotations",
    response_model=list[SnapshotAnnotationResponse],
    summary="List snapshot annotations",
    description="Get all annotations for a specific snapshot.",
)
async def list_annotations(
    snapshot_id: int,
    db: AsyncSession = Depends(get_db),
) -> list[SnapshotAnnotationResponse]:
    """
    List annotations for a snapshot.

    Args:
        snapshot_id: Snapshot ID
        db: Database session

    Returns:
        List of annotation responses
    """
    from sqlalchemy import select
    from src.core import models

    # Verify snapshot exists
    service = SnapshotService(db)
    await service.get_snapshot(snapshot_id, load_relationships=False)

    # Get annotations
    stmt = select(models.Annotation).where(
        models.Annotation.snapshot_id == snapshot_id
    ).order_by(models.Annotation.created_at.desc())

    result = await db.execute(stmt)
    annotations = result.scalars().all()

    return [annotation_to_response(ann) for ann in annotations]


@router.get(
    "/snapshots/{snapshot_id}/stats",
    response_model=dict[str, Any],
    summary="Get snapshot statistics",
    description="Get detailed statistics for a specific snapshot.",
)
async def get_snapshot_stats(
    snapshot_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Get snapshot statistics.

    Args:
        snapshot_id: Snapshot ID
        db: Database session

    Returns:
        Snapshot statistics
    """
    service = SnapshotService(db)
    return await service.get_snapshot_stats(snapshot_id)


@router.post(
    "/snapshots/{snapshot_id}/export",
    summary="Export snapshot",
    description="Export a snapshot to JSON or YAML format.",
)
async def export_snapshot(
    snapshot_id: int,
    format: str = "json",
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Export snapshot to JSON or YAML.

    Args:
        snapshot_id: Snapshot ID to export
        format: Export format (json or yaml)
        db: Database session

    Returns:
        Exported snapshot data
    """
    from sqlalchemy import select
    from src.core import models
    from src.core.schemas.converters import (
        snapshot_to_detail,
        path_to_response,
        tag_to_response,
        annotation_to_response,
    )

    # Validate format
    if format not in ["json", "yaml"]:
        from src.api.exceptions import ValidationException
        raise ValidationException(
            f"Invalid format: {format}. Must be 'json' or 'yaml'")

    # Get snapshot with relationships
    service = SnapshotService(db)
    snapshot = await service.get_snapshot(snapshot_id, load_relationships=True)

    # Get paths
    stmt = select(models.SnapshotPath).where(
        models.SnapshotPath.snapshot_id == snapshot_id
    )
    result = await db.execute(stmt)
    paths = result.scalars().all()

    # Build export data
    export_data = {
        "version": "1.0",
        "exported_at": datetime.utcnow().isoformat(),
        "snapshot": snapshot_to_detail(snapshot).model_dump(mode="python"),
        "paths": [path_to_response(p).model_dump(mode="python") for p in paths],
        "tags": [tag_to_response(t).model_dump(mode="python") for t in snapshot.tags] if snapshot.tags else [],
        "annotations": [
            annotation_to_response(a).model_dump(mode="python")
            for a in snapshot.annotations
        ] if snapshot.annotations else [],
    }

    return export_data
