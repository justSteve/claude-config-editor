"""
Path API endpoints.

Provides operations for querying paths, retrieving content, and managing annotations.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.schemas import (
    PathSummary,
    PathDetailResponse,
    FileContentResponse,
    PathAnnotationResponse,
    PathListResponse,
    PaginationParams,
)
from src.api.dependencies import get_db, get_pagination
from src.api.services import PathService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/snapshots/{snapshot_id}/paths",
    response_model=PathListResponse,
    summary="List paths in snapshot",
    description="Get all paths found in a snapshot with optional filtering and pagination.",
)
async def list_paths(
    snapshot_id: int,
    category: Optional[str] = Query(
        None, description="Filter by category (e.g., settings, memory, mcp)"
    ),
    exists: Optional[bool] = Query(None, description="Filter by existence"),
    path_type: Optional[str] = Query(
        None, description="Filter by type (file/directory/symlink)"
    ),
    search: Optional[str] = Query(
        None, description="Search in path names and resolved paths"
    ),
    pagination: PaginationParams = Depends(get_pagination),
    db: AsyncSession = Depends(get_db),
) -> PathListResponse:
    """
    List paths in a snapshot.

    Returns all paths discovered during the snapshot scan,
    with optional filters for category, existence, type, and search.

    Args:
        snapshot_id: Snapshot ID to query
        category: Optional category filter
        exists: Optional existence filter
        path_type: Optional type filter
        search: Optional search query
        pagination: Pagination parameters
        db: Database session

    Returns:
        Paginated list of path summaries
    """
    service = PathService(db)

    paths, total = await service.list_paths(
        snapshot_id=snapshot_id,
        category=category,
        exists=exists,
        path_type=path_type,
        search=search,
        pagination=pagination,
    )

    return PathListResponse(
        items=paths,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=(total + pagination.page_size - 1) // pagination.page_size,
    )


@router.get(
    "/paths/{path_id}",
    response_model=PathDetailResponse,
    summary="Get path details",
    description="Get detailed information about a specific path including content metadata and relationships.",
)
async def get_path(
    path_id: int,
    db: AsyncSession = Depends(get_db),
) -> PathDetailResponse:
    """
    Get detailed path information.

    Returns complete metadata including file info, content metadata,
    Claude config (if applicable), and annotations.

    Args:
        path_id: Path ID
        db: Database session

    Returns:
        Detailed path information
    """
    service = PathService(db)

    detail = await service.get_path_detail(path_id)

    return detail


@router.get(
    "/paths/{path_id}/content",
    response_model=FileContentResponse,
    summary="Get file content",
    description="Retrieve the actual file content for a path.",
)
async def get_path_content(
    path_id: int,
    include_content: bool = Query(
        True, description="Whether to include actual content text/binary"
    ),
    db: AsyncSession = Depends(get_db),
) -> FileContentResponse:
    """
    Get file content.

    Returns the deduplicated file content with optional
    inclusion of the actual content text/binary data.

    Args:
        path_id: Path ID
        include_content: Whether to include content data
        db: Database session

    Returns:
        File content response
    """
    service = PathService(db)

    content = await service.get_path_content(path_id, include_content=include_content)

    return content


@router.get(
    "/paths/{path_id}/history",
    response_model=list[PathSummary],
    summary="Get path history",
    description="Get the history of a path across all snapshots.",
)
async def get_path_history(
    path_id: int,
    limit: Optional[int] = Query(None, description="Limit number of history entries", ge=1),
    db: AsyncSession = Depends(get_db),
) -> list[PathSummary]:
    """
    Get path history.

    Returns all snapshots where this path appears,
    showing how the path has changed over time.

    Args:
        path_id: Path ID
        limit: Optional limit on results
        db: Database session

    Returns:
        List of path summaries (newest first)
    """
    service = PathService(db)

    # First get the path to find its resolved_path
    path = await service.get_path_detail(path_id)

    # Then get history using the resolved path
    history = await service.get_path_history(
        resolved_path=path.resolved_path, limit=limit
    )

    return history


@router.get(
    "/snapshots/{snapshot_id}/search",
    response_model=PathListResponse,
    summary="Search paths",
    description="Search for paths in a snapshot by name, path, or optionally content.",
)
async def search_paths(
    snapshot_id: int,
    q: str = Query(..., description="Search query", min_length=1),
    search_content: bool = Query(
        False, description="Search in file contents (slower)"
    ),
    pagination: PaginationParams = Depends(get_pagination),
    db: AsyncSession = Depends(get_db),
) -> PathListResponse:
    """
    Search paths in a snapshot.

    Searches path names, resolved paths, and categories.
    Optionally searches file content text (slower).

    Args:
        snapshot_id: Snapshot ID to search in
        q: Search query string
        search_content: Whether to search content
        pagination: Pagination parameters
        db: Database session

    Returns:
        Paginated list of matching paths
    """
    service = PathService(db)

    paths, total = await service.search_paths(
        snapshot_id=snapshot_id,
        query=q,
        search_content=search_content,
        pagination=pagination,
    )

    return PathListResponse(
        items=paths,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=(total + pagination.page_size - 1) // pagination.page_size,
    )


@router.post(
    "/paths/{path_id}/annotations",
    response_model=PathAnnotationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add path annotation",
    description="Add a note or annotation to a specific path.",
)
async def add_path_annotation(
    path_id: int,
    annotation_text: str = Query(..., description="Annotation text", min_length=1),
    annotation_type: Optional[str] = Query(
        None, description="Annotation type (e.g., note, warning, todo)"
    ),
    created_by: Optional[str] = Query(None, description="Creator name"),
    db: AsyncSession = Depends(get_db),
) -> PathAnnotationResponse:
    """
    Add annotation to a path.

    Creates a note or annotation attached to a specific path
    for documentation, warnings, or TODO tracking.

    Args:
        path_id: Path ID
        annotation_text: Annotation text
        annotation_type: Optional type
        created_by: Optional creator
        db: Database session

    Returns:
        Created annotation
    """
    service = PathService(db)

    annotation = await service.add_path_annotation(
        path_id=path_id,
        annotation_text=annotation_text,
        annotation_type=annotation_type,
        created_by=created_by,
    )

    return annotation
