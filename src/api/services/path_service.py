"""
Path service layer.

Handles business logic for path operations including:
- Querying paths within snapshots
- Retrieving path details and content
- Path history tracking
- Path search
- Path annotations
"""

import logging
from typing import Optional

from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from src.core import models
from src.core.schemas import (
    PathSummary,
    PathDetailResponse,
    FileContentResponse,
    PathAnnotationResponse,
    ClaudeConfigResponse,
    McpServerResponse,
    PaginationParams,
)
from src.api.exceptions import NotFoundException

logger = logging.getLogger(__name__)


class PathService:
    """Service for path operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize path service.

        Args:
            db: Database session
        """
        self.db = db

    async def list_paths(
        self,
        snapshot_id: int,
        category: Optional[str] = None,
        exists: Optional[bool] = None,
        path_type: Optional[str] = None,
        search: Optional[str] = None,
        pagination: Optional[PaginationParams] = None,
    ) -> tuple[list[PathSummary], int]:
        """
        List paths in a snapshot with optional filtering and pagination.

        Args:
            snapshot_id: Snapshot ID to query
            category: Filter by category
            exists: Filter by existence
            path_type: Filter by type (file, directory, symlink)
            search: Search in resolved_path
            pagination: Pagination parameters

        Returns:
            Tuple of (list of path summaries, total count)

        Raises:
            NotFoundException: If snapshot not found
        """
        # Verify snapshot exists
        stmt = select(models.Snapshot).where(models.Snapshot.id == snapshot_id)
        result = await self.db.execute(stmt)
        snapshot = result.scalar_one_or_none()
        if not snapshot:
            raise NotFoundException(f"Snapshot {snapshot_id} not found")

        # Build base query
        stmt = select(models.SnapshotPath).where(
            models.SnapshotPath.snapshot_id == snapshot_id
        )

        # Apply filters
        if category:
            stmt = stmt.where(models.SnapshotPath.category == category)
        if exists is not None:
            stmt = stmt.where(models.SnapshotPath.exists == exists)
        if path_type:
            stmt = stmt.where(models.SnapshotPath.type == path_type)
        if search:
            stmt = stmt.where(
                or_(
                    models.SnapshotPath.resolved_path.ilike(f"%{search}%"),
                    models.SnapshotPath.name.ilike(f"%{search}%"),
                )
            )

        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one()

        # Apply sorting
        sort_by = pagination.sort_by if pagination else "id"
        sort_order = pagination.sort_order if pagination else "asc"

        if sort_by == "resolved_path":
            sort_col = models.SnapshotPath.resolved_path
        elif sort_by == "size_bytes":
            sort_col = models.SnapshotPath.size_bytes
        elif sort_by == "modified_time":
            sort_col = models.SnapshotPath.modified_time
        else:
            sort_col = models.SnapshotPath.id

        if sort_order == "desc":
            stmt = stmt.order_by(sort_col.desc())
        else:
            stmt = stmt.order_by(sort_col.asc())

        # Apply pagination
        if pagination:
            offset = (pagination.page - 1) * pagination.page_size
            stmt = stmt.offset(offset).limit(pagination.page_size)

        # Execute query
        result = await self.db.execute(stmt)
        paths = result.scalars().all()

        # Convert to summaries
        summaries = [PathSummary.model_validate(path) for path in paths]

        logger.info(
            f"Found {len(summaries)} paths (total: {total}) in snapshot {snapshot_id}"
        )
        return summaries, total

    async def get_path_detail(self, path_id: int) -> PathDetailResponse:
        """
        Get detailed information about a path including content and relationships.

        Args:
            path_id: Path ID

        Returns:
            Detailed path information

        Raises:
            NotFoundException: If path not found
        """
        # Query path with eager loading of relationships
        stmt = (
            select(models.SnapshotPath)
            .where(models.SnapshotPath.id == path_id)
            .options(
                joinedload(models.SnapshotPath.content),
                selectinload(models.SnapshotPath.annotations),
                selectinload(models.SnapshotPath.claude_config),
            )
        )

        result = await self.db.execute(stmt)
        path = result.scalar_one_or_none()

        if not path:
            raise NotFoundException(f"Path {path_id} not found")

        # Build detailed response
        detail = PathDetailResponse(
            id=path.id,
            snapshot_id=path.snapshot_id,
            category=path.category,
            name=path.name,
            path_template=path.path_template,
            resolved_path=path.resolved_path,
            exists=path.exists,
            type=path.type,
            size_bytes=path.size_bytes,
            modified_time=path.modified_time,
            created_time=path.created_time,
            accessed_time=path.accessed_time,
            permissions=path.permissions,
            item_count=path.item_count,
            error_message=path.error_message,
            content_hash=path.content_hash,
        )

        # Add content if exists
        if path.content:
            detail.content = FileContentResponse(
                id=path.content.id,
                content_hash=path.content.content_hash,
                content_type=path.content.content_type,
                size_bytes=path.content.size_bytes,
                compression=path.content.compression,
                reference_count=path.content.reference_count,
                created_at=path.content.created_at,
                content_text=None,  # Don't include content by default
                content_binary=None,
            )

        # Add Claude config if exists
        if path.claude_config:
            detail.claude_config = ClaudeConfigResponse.model_validate(
                path.claude_config
            )

        # Add annotations
        detail.annotations = [
            PathAnnotationResponse.model_validate(ann) for ann in path.annotations
        ]

        logger.info(f"Retrieved details for path {path_id}")
        return detail

    async def get_path_content(
        self, path_id: int, include_content: bool = True
    ) -> FileContentResponse:
        """
        Get file content for a path.

        Args:
            path_id: Path ID
            include_content: Whether to include actual content text/binary

        Returns:
            File content response

        Raises:
            NotFoundException: If path or content not found
        """
        # Query path with content
        stmt = (
            select(models.SnapshotPath)
            .where(models.SnapshotPath.id == path_id)
            .options(joinedload(models.SnapshotPath.content))
        )

        result = await self.db.execute(stmt)
        path = result.scalar_one_or_none()

        if not path:
            raise NotFoundException(f"Path {path_id} not found")

        if not path.content:
            raise NotFoundException(f"No content found for path {path_id}")

        # Build content response
        content_response = FileContentResponse(
            id=path.content.id,
            content_hash=path.content.content_hash,
            content_type=path.content.content_type,
            size_bytes=path.content.size_bytes,
            compression=path.content.compression,
            reference_count=path.content.reference_count,
            created_at=path.content.created_at,
            content_text=path.content.content_text if include_content else None,
            content_binary=path.content.content_binary if include_content else None,
        )

        logger.info(
            f"Retrieved content for path {path_id} (include_content={include_content})"
        )
        return content_response

    async def get_path_history(
        self, resolved_path: str, limit: Optional[int] = None
    ) -> list[PathSummary]:
        """
        Get history of a path across all snapshots.

        Args:
            resolved_path: Resolved path to track
            limit: Optional limit on number of history entries

        Returns:
            List of path summaries ordered by snapshot time (newest first)
        """
        # Query all snapshots where this path appears
        stmt = (
            select(models.SnapshotPath, models.Snapshot)
            .join(models.Snapshot)
            .where(models.SnapshotPath.resolved_path == resolved_path)
            .order_by(models.Snapshot.snapshot_time.desc())
        )

        if limit:
            stmt = stmt.limit(limit)

        result = await self.db.execute(stmt)
        rows = result.all()

        # Convert to summaries
        history = []
        for path, snapshot in rows:
            summary = PathSummary.model_validate(path)
            history.append(summary)

        logger.info(f"Found {len(history)} history entries for path: {resolved_path}")
        return history

    async def search_paths(
        self,
        snapshot_id: int,
        query: str,
        search_content: bool = False,
        pagination: Optional[PaginationParams] = None,
    ) -> tuple[list[PathSummary], int]:
        """
        Search paths in a snapshot.

        Args:
            snapshot_id: Snapshot ID to search in
            query: Search query string
            search_content: Whether to search file contents (slow)
            pagination: Pagination parameters

        Returns:
            Tuple of (matching paths, total count)

        Raises:
            NotFoundException: If snapshot not found
        """
        # Verify snapshot exists
        stmt = select(models.Snapshot).where(models.Snapshot.id == snapshot_id)
        result = await self.db.execute(stmt)
        snapshot = result.scalar_one_or_none()
        if not snapshot:
            raise NotFoundException(f"Snapshot {snapshot_id} not found")

        # Build search query
        stmt = select(models.SnapshotPath).where(
            models.SnapshotPath.snapshot_id == snapshot_id
        )

        # Search in path fields
        search_conditions = [
            models.SnapshotPath.resolved_path.ilike(f"%{query}%"),
            models.SnapshotPath.name.ilike(f"%{query}%"),
            models.SnapshotPath.category.ilike(f"%{query}%"),
        ]

        # Optionally search in content
        if search_content:
            stmt = stmt.outerjoin(models.FileContent)
            search_conditions.append(
                models.FileContent.content_text.ilike(f"%{query}%")
            )

        stmt = stmt.where(or_(*search_conditions))

        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one()

        # Apply pagination
        if pagination:
            offset = (pagination.page - 1) * pagination.page_size
            stmt = stmt.offset(offset).limit(pagination.page_size)
        else:
            stmt = stmt.limit(100)  # Default limit

        # Execute query
        result = await self.db.execute(stmt)
        paths = result.scalars().all()

        # Convert to summaries
        summaries = [PathSummary.model_validate(path) for path in paths]

        logger.info(f"Search found {len(summaries)} paths (total: {total})")
        return summaries, total

    async def add_path_annotation(
        self,
        path_id: int,
        annotation_text: str,
        annotation_type: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> PathAnnotationResponse:
        """
        Add annotation to a path.

        Args:
            path_id: Path ID
            annotation_text: Annotation text
            annotation_type: Optional annotation type
            created_by: Optional creator name

        Returns:
            Created annotation

        Raises:
            NotFoundException: If path not found
        """
        # Verify path exists
        stmt = select(models.SnapshotPath).where(models.SnapshotPath.id == path_id)
        result = await self.db.execute(stmt)
        path = result.scalar_one_or_none()

        if not path:
            raise NotFoundException(f"Path {path_id} not found")

        # Create annotation
        annotation = models.Annotation(
            snapshot_id=path.snapshot_id,
            snapshot_path_id=path_id,
            annotation_text=annotation_text,
            annotation_type=annotation_type,
            created_by=created_by,
        )

        self.db.add(annotation)
        await self.db.commit()
        await self.db.refresh(annotation)

        logger.info(f"Added annotation to path {path_id}")
        return PathAnnotationResponse.model_validate(annotation)
