"""
Snapshot service layer.

Handles business logic for snapshot operations including:
- Creating new snapshots
- Querying and filtering snapshots
- Managing tags and annotations
- Deleting snapshots
"""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import select, func, desc, asc, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.core import models
from src.core.schemas import (
    SnapshotCreateRequest,
    SnapshotQueryRequest,
    SnapshotSummary,
    SnapshotDetailResponse,
    PaginatedResponse,
)
from src.core.schemas.converters import (
    snapshot_to_summary,
    snapshot_to_detail,
)
from src.api.exceptions import NotFoundException, ValidationException

logger = logging.getLogger(__name__)


class SnapshotService:
    """Service for snapshot operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize snapshot service.

        Args:
            db: Database session
        """
        self.db = db

    async def create_snapshot(
        self,
        request: SnapshotCreateRequest,
    ) -> models.Snapshot:
        """
        Create a new snapshot by scanning Claude configuration files.

        Args:
            request: Snapshot creation request

        Returns:
            Created snapshot model

        Raises:
            ValidationException: If validation fails
        """
        logger.info(
            f"Creating snapshot: {request.trigger_type} by {request.triggered_by}")

        # Import scanner here to avoid circular imports
        from src.core.scanner import PathScanner

        # Create scanner instance with database session
        scanner = PathScanner(self.db)

        # Create snapshot using scanner (this will actually scan files)
        snapshot = await scanner.create_snapshot(
            trigger_type=request.trigger_type,
            triggered_by=request.triggered_by,
            notes=request.notes,
        )

        # Add tags if provided
        if request.tags:
            for tag_name in request.tags:
                try:
                    # Check if tag already exists for this snapshot
                    existing = await self.db.execute(
                        select(models.SnapshotTag).where(
                            and_(
                                models.SnapshotTag.snapshot_id == snapshot.id,
                                models.SnapshotTag.tag_name == tag_name,
                            )
                        )
                    )
                    if existing.scalar_one_or_none():
                        logger.debug(
                            f"Tag '{tag_name}' already exists on snapshot {snapshot.id}, skipping")
                        continue

                    tag = models.SnapshotTag(
                        snapshot_id=snapshot.id,
                        tag_name=tag_name,
                        created_at=datetime.utcnow(),
                    )
                    self.db.add(tag)
                except Exception as e:
                    logger.warning(f"Could not add tag '{tag_name}': {e}")
                    # Continue with other tags
                    continue

            await self.db.commit()
            await self.db.refresh(snapshot)

        logger.info(
            f"Snapshot created: {snapshot.id} ({snapshot.snapshot_hash[:8]}...), "
            f"files={snapshot.files_found}, dirs={snapshot.directories_found}"
        )

        return snapshot

    async def get_snapshot(
        self,
        snapshot_id: int,
        load_relationships: bool = True,
    ) -> models.Snapshot:
        """
        Get snapshot by ID.

        Args:
            snapshot_id: Snapshot ID
            load_relationships: Whether to load relationships

        Returns:
            Snapshot model

        Raises:
            NotFoundException: If snapshot not found
        """
        query = select(models.Snapshot).where(
            models.Snapshot.id == snapshot_id)

        if load_relationships:
            query = query.options(
                joinedload(models.Snapshot.tags),
                joinedload(models.Snapshot.annotations),
                joinedload(models.Snapshot.env_vars),
            )

        result = await self.db.execute(query)

        # Use unique() for queries with joinedload on collections
        if load_relationships:
            snapshot = result.unique().scalar_one_or_none()
        else:
            snapshot = result.scalar_one_or_none()

        if not snapshot:
            raise NotFoundException(f"Snapshot {snapshot_id} not found")

        return snapshot

    async def list_snapshots(
        self,
        query_params: SnapshotQueryRequest,
    ) -> PaginatedResponse[SnapshotSummary]:
        """
        List snapshots with filtering and pagination.

        Args:
            query_params: Query parameters

        Returns:
            Paginated snapshot summaries
        """
        # Build base query
        stmt = select(models.Snapshot).options(
            joinedload(models.Snapshot.tags))

        # Apply filters
        filters = []

        if query_params.trigger_type:
            filters.append(models.Snapshot.trigger_type ==
                           query_params.trigger_type)

        if query_params.triggered_by:
            filters.append(models.Snapshot.triggered_by ==
                           query_params.triggered_by)

        if query_params.os_type:
            filters.append(models.Snapshot.os_type == query_params.os_type)

        if query_params.is_baseline is not None:
            filters.append(models.Snapshot.is_baseline ==
                           query_params.is_baseline)

        if query_params.has_changes is not None:
            if query_params.has_changes:
                filters.append(models.Snapshot.changed_from_previous > 0)
            else:
                filters.append(
                    or_(
                        models.Snapshot.changed_from_previous == 0,
                        models.Snapshot.changed_from_previous.is_(None),
                    )
                )

        # Time range filter
        if query_params.time_range:
            if query_params.time_range.start_time:
                filters.append(
                    models.Snapshot.snapshot_time >= query_params.time_range.start_time
                )
            if query_params.time_range.end_time:
                filters.append(
                    models.Snapshot.snapshot_time <= query_params.time_range.end_time
                )

        # Search filter
        if query_params.search:
            search_pattern = f"%{query_params.search}%"
            filters.append(
                or_(
                    models.Snapshot.notes.ilike(search_pattern),
                    models.Snapshot.triggered_by.ilike(search_pattern),
                )
            )

        if filters:
            stmt = stmt.where(and_(*filters))

        # Tag filtering
        if query_params.tags or query_params.tags_all:
            tag_filters = query_params.tags_all or query_params.tags
            if tag_filters:
                # Join with tags
                stmt = stmt.join(models.Snapshot.tags)
                stmt = stmt.where(models.SnapshotTag.tag_name.in_(tag_filters))

                if query_params.tags_all:
                    # Must have ALL tags
                    stmt = stmt.group_by(models.Snapshot.id)
                    stmt = stmt.having(
                        func.count(models.SnapshotTag.id) == len(tag_filters)
                    )

        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Apply sorting
        sort_field = getattr(models.Snapshot, query_params.sort_by)
        if query_params.sort_order == "desc":
            stmt = stmt.order_by(desc(sort_field))
        else:
            stmt = stmt.order_by(asc(sort_field))

        # Apply pagination
        stmt = stmt.offset(query_params.offset).limit(query_params.limit)

        # Execute query
        result = await self.db.execute(stmt)
        snapshots = result.unique().scalars().all()

        # Convert to summaries
        summaries = [snapshot_to_summary(s) for s in snapshots]

        return PaginatedResponse.create(
            items=summaries,
            total=total,
            page=query_params.page,
            page_size=query_params.page_size,
        )

    async def delete_snapshot(
        self,
        snapshot_id: int,
    ) -> None:
        """
        Delete snapshot.

        Args:
            snapshot_id: Snapshot ID to delete

        Raises:
            NotFoundException: If snapshot not found
        """
        snapshot = await self.get_snapshot(snapshot_id, load_relationships=False)

        await self.db.delete(snapshot)
        await self.db.commit()

        logger.info(f"Snapshot deleted: {snapshot_id}")

    async def add_tag(
        self,
        snapshot_id: int,
        tag_name: str,
        tag_type: Optional[str] = None,
        description: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> models.SnapshotTag:
        """
        Add tag to snapshot.

        Args:
            snapshot_id: Snapshot ID
            tag_name: Tag name
            tag_type: Tag type (optional)
            description: Tag description (optional)
            created_by: Creator name (optional)

        Returns:
            Created tag

        Raises:
            NotFoundException: If snapshot not found
            ValidationException: If tag already exists
        """
        # Verify snapshot exists
        await self.get_snapshot(snapshot_id, load_relationships=False)

        # Check if tag already exists
        existing_tag = await self.db.execute(
            select(models.SnapshotTag).where(
                and_(
                    models.SnapshotTag.snapshot_id == snapshot_id,
                    models.SnapshotTag.tag_name == tag_name,
                )
            )
        )
        if existing_tag.scalar_one_or_none():
            raise ValidationException(
                f"Tag '{tag_name}' already exists on snapshot {snapshot_id}")

        # Create tag
        tag = models.SnapshotTag(
            snapshot_id=snapshot_id,
            tag_name=tag_name,
            tag_type=tag_type,
            description=description,
            created_at=datetime.utcnow(),
            created_by=created_by,
        )

        self.db.add(tag)
        await self.db.commit()
        await self.db.refresh(tag)

        logger.info(f"Tag added to snapshot {snapshot_id}: {tag_name}")

        return tag

    async def remove_tag(
        self,
        snapshot_id: int,
        tag_id: int,
    ) -> None:
        """
        Remove tag from snapshot.

        Args:
            snapshot_id: Snapshot ID
            tag_id: Tag ID to remove

        Raises:
            NotFoundException: If tag not found
        """
        result = await self.db.execute(
            select(models.SnapshotTag).where(
                and_(
                    models.SnapshotTag.id == tag_id,
                    models.SnapshotTag.snapshot_id == snapshot_id,
                )
            )
        )
        tag = result.scalar_one_or_none()

        if not tag:
            raise NotFoundException(
                f"Tag {tag_id} not found on snapshot {snapshot_id}")

        await self.db.delete(tag)
        await self.db.commit()

        logger.info(f"Tag removed from snapshot {snapshot_id}: {tag_id}")

    async def add_annotation(
        self,
        snapshot_id: int,
        annotation_text: str,
        annotation_type: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> models.Annotation:
        """
        Add annotation to snapshot.

        Args:
            snapshot_id: Snapshot ID
            annotation_text: Annotation text
            annotation_type: Annotation type (optional)
            created_by: Creator name (optional)

        Returns:
            Created annotation

        Raises:
            NotFoundException: If snapshot not found
        """
        # Verify snapshot exists
        await self.get_snapshot(snapshot_id, load_relationships=False)

        # Create annotation
        annotation = models.Annotation(
            snapshot_id=snapshot_id,
            annotation_text=annotation_text,
            annotation_type=annotation_type,
            created_at=datetime.utcnow(),
            created_by=created_by,
        )

        self.db.add(annotation)
        await self.db.commit()
        await self.db.refresh(annotation)

        logger.info(f"Annotation added to snapshot {snapshot_id}")

        return annotation

    async def remove_annotation(
        self,
        snapshot_id: int,
        annotation_id: int,
    ) -> None:
        """
        Remove annotation from snapshot.

        Args:
            snapshot_id: Snapshot ID
            annotation_id: Annotation ID to remove

        Raises:
            NotFoundException: If annotation not found
        """
        result = await self.db.execute(
            select(models.Annotation).where(
                and_(
                    models.Annotation.id == annotation_id,
                    models.Annotation.snapshot_id == snapshot_id,
                )
            )
        )
        annotation = result.scalar_one_or_none()

        if not annotation:
            raise NotFoundException(
                f"Annotation {annotation_id} not found on snapshot {snapshot_id}"
            )

        await self.db.delete(annotation)
        await self.db.commit()

        logger.info(
            f"Annotation removed from snapshot {snapshot_id}: {annotation_id}")

    async def get_snapshot_stats(self, snapshot_id: int) -> dict:
        """
        Get statistics for a snapshot.

        Args:
            snapshot_id: Snapshot ID

        Returns:
            Dictionary with statistics

        Raises:
            NotFoundException: If snapshot not found
        """
        snapshot = await self.get_snapshot(snapshot_id, load_relationships=True)

        # Count related entities
        paths_count = await self.db.execute(
            select(func.count(models.SnapshotPath.id)).where(
                models.SnapshotPath.snapshot_id == snapshot_id
            )
        )

        changes_count = await self.db.execute(
            select(func.count(models.SnapshotChange.id)).where(
                models.SnapshotChange.snapshot_id == snapshot_id
            )
        )

        return {
            "snapshot_id": snapshot.id,
            "snapshot_hash": snapshot.snapshot_hash,
            "snapshot_time": snapshot.snapshot_time,
            "total_locations": snapshot.total_locations,
            "files_found": snapshot.files_found,
            "directories_found": snapshot.directories_found,
            "total_size_bytes": snapshot.total_size_bytes,
            "paths_count": paths_count.scalar() or 0,
            "changes_count": changes_count.scalar() or 0,
            "tags_count": len(snapshot.tags) if snapshot.tags else 0,
            "annotations_count": len(snapshot.annotations) if snapshot.annotations else 0,
        }
