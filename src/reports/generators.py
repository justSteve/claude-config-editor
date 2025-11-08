"""
Report generators for Claude Config version control system.

Generates structured reports from database queries.
"""

import logging
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models import (
    Snapshot,
    SnapshotPath,
    SnapshotChange,
    FileContent,
)
from src.reports.models import (
    ChangeDetectionReport,
    FileChange,
    SnapshotSummaryReport,
    PathInfo,
    CategoryStats,
    DeduplicationReport,
)

logger = logging.getLogger(__name__)


async def generate_change_report(
    session: AsyncSession,
    snapshot_id: int,
    previous_snapshot_id: Optional[int] = None,
) -> ChangeDetectionReport:
    """
    Generate a change detection report between two snapshots.

    Args:
        session: Database session
        snapshot_id: Current snapshot ID
        previous_snapshot_id: Previous snapshot ID (auto-detected if None)

    Returns:
        ChangeDetectionReport with all changes

    Raises:
        ValueError: If snapshot not found or no previous snapshot
    """
    # Get current snapshot
    stmt = select(Snapshot).where(Snapshot.id == snapshot_id)
    result = await session.execute(stmt)
    snapshot = result.scalar_one_or_none()

    if not snapshot:
        raise ValueError(f"Snapshot {snapshot_id} not found")

    # Determine previous snapshot
    if previous_snapshot_id is None:
        previous_snapshot_id = snapshot.parent_snapshot_id

    if previous_snapshot_id is None:
        raise ValueError(f"Snapshot {snapshot_id} has no previous snapshot (baseline)")

    # Get previous snapshot
    stmt = select(Snapshot).where(Snapshot.id == previous_snapshot_id)
    result = await session.execute(stmt)
    previous_snapshot = result.scalar_one_or_none()

    if not previous_snapshot:
        raise ValueError(f"Previous snapshot {previous_snapshot_id} not found")

    # Get all changes
    stmt = select(SnapshotChange).where(
        SnapshotChange.snapshot_id == snapshot_id,
        SnapshotChange.previous_snapshot_id == previous_snapshot_id,
    )
    result = await session.execute(stmt)
    changes = result.scalars().all()

    # Organize changes by type
    added = []
    modified = []
    deleted = []

    for change in changes:
        file_change = FileChange(
            path_template=change.path_template,
            change_type=change.change_type,
            old_size_bytes=change.old_size_bytes,
            new_size_bytes=change.new_size_bytes,
            old_modified_time=change.old_modified_time,
            new_modified_time=change.new_modified_time,
            old_content_hash=change.old_content_hash,
            new_content_hash=change.new_content_hash,
        )

        if change.change_type == "added":
            added.append(file_change)
        elif change.change_type == "modified":
            modified.append(file_change)
        elif change.change_type == "deleted":
            deleted.append(file_change)

    return ChangeDetectionReport(
        snapshot_id=snapshot.id,
        snapshot_time=snapshot.snapshot_time,
        previous_snapshot_id=previous_snapshot.id,
        previous_snapshot_time=previous_snapshot.snapshot_time,
        added_files=added,
        modified_files=modified,
        deleted_files=deleted,
    )


async def generate_snapshot_report(
    session: AsyncSession,
    snapshot_id: int,
) -> SnapshotSummaryReport:
    """
    Generate a comprehensive snapshot summary report.

    Args:
        session: Database session
        snapshot_id: Snapshot ID to report on

    Returns:
        SnapshotSummaryReport with full details

    Raises:
        ValueError: If snapshot not found
    """
    # Get snapshot
    stmt = select(Snapshot).where(Snapshot.id == snapshot_id)
    result = await session.execute(stmt)
    snapshot = result.scalar_one_or_none()

    if not snapshot:
        raise ValueError(f"Snapshot {snapshot_id} not found")

    # Get all paths
    stmt = select(SnapshotPath).where(SnapshotPath.snapshot_id == snapshot_id)
    result = await session.execute(stmt)
    paths = result.scalars().all()

    # Build path info list
    path_infos = []
    for path in paths:
        path_infos.append(
            PathInfo(
                category=path.category,
                name=path.name,
                path_template=path.path_template,
                exists=path.exists,
                type=path.type,
                size_bytes=path.size_bytes,
            )
        )

    # Calculate category statistics
    category_map: dict[str, CategoryStats] = {}
    for path in paths:
        if path.category not in category_map:
            category_map[path.category] = CategoryStats(
                category=path.category,
                total_locations=0,
                found=0,
                missing=0,
                total_size_bytes=0,
            )

        stats = category_map[path.category]
        stats.total_locations += 1

        if path.exists:
            stats.found += 1
            if path.size_bytes:
                stats.total_size_bytes += path.size_bytes
        else:
            stats.missing += 1

    category_stats = list(category_map.values())

    # Calculate deduplication statistics
    stmt = select(func.count(func.distinct(FileContent.content_hash))).select_from(
        FileContent
    ).join(
        SnapshotPath,
        SnapshotPath.content_id == FileContent.id
    ).where(
        SnapshotPath.snapshot_id == snapshot_id
    )
    result = await session.execute(stmt)
    unique_contents = result.scalar() or 0

    # Calculate deduplication savings
    total_size = snapshot.total_size_bytes
    stmt = select(func.sum(FileContent.size_bytes)).select_from(
        FileContent
    ).join(
        SnapshotPath,
        SnapshotPath.content_id == FileContent.id
    ).where(
        SnapshotPath.snapshot_id == snapshot_id
    )
    result = await session.execute(stmt)
    deduplicated_size = result.scalar() or 0

    savings = total_size - deduplicated_size if total_size > deduplicated_size else 0
    savings_percent = (savings / total_size * 100) if total_size > 0 else 0.0

    return SnapshotSummaryReport(
        snapshot_id=snapshot.id,
        snapshot_time=snapshot.snapshot_time,
        snapshot_hash=snapshot.snapshot_hash,
        trigger_type=snapshot.trigger_type,
        triggered_by=snapshot.triggered_by,
        notes=snapshot.notes,
        os_type=snapshot.os_type,
        hostname=snapshot.hostname,
        username=snapshot.username,
        total_locations=snapshot.total_locations,
        files_found=snapshot.files_found,
        directories_found=snapshot.directories_found,
        total_size_bytes=snapshot.total_size_bytes,
        paths=path_infos,
        category_stats=category_stats,
        unique_contents=unique_contents,
        deduplication_savings_bytes=savings,
        deduplication_percent=savings_percent,
    )


async def generate_deduplication_report(
    session: AsyncSession,
) -> DeduplicationReport:
    """
    Generate a report on content deduplication across all snapshots.

    Args:
        session: Database session

    Returns:
        DeduplicationReport with deduplication statistics
    """
    # Get total file contents
    stmt = select(func.count(FileContent.id))
    result = await session.execute(stmt)
    total_contents = result.scalar() or 0

    # Get unique hashes
    stmt = select(func.count(func.distinct(FileContent.content_hash)))
    result = await session.execute(stmt)
    unique_hashes = result.scalar() or 0

    # Get total references
    stmt = select(func.sum(FileContent.reference_count))
    result = await session.execute(stmt)
    total_references = result.scalar() or 0

    # Get size statistics
    stmt = select(func.sum(FileContent.size_bytes))
    result = await session.execute(stmt)
    total_size = result.scalar() or 0

    # Calculate deduplicated size (sum of size * reference_count)
    stmt = select(func.sum(FileContent.size_bytes * FileContent.reference_count))
    result = await session.execute(stmt)
    deduplicated_size = result.scalar() or 0

    savings = deduplicated_size - total_size
    savings_percent = (savings / deduplicated_size * 100) if deduplicated_size > 0 else 0.0

    # Get most referenced files
    stmt = (
        select(FileContent)
        .where(FileContent.reference_count > 1)
        .order_by(FileContent.reference_count.desc())
        .limit(10)
    )
    result = await session.execute(stmt)
    most_referenced_files = result.scalars().all()

    most_referenced = [
        {
            "content_hash": f.content_hash[:16] + "...",
            "content_type": f.content_type,
            "size_bytes": f.size_bytes,
            "reference_count": f.reference_count,
        }
        for f in most_referenced_files
    ]

    return DeduplicationReport(
        total_file_contents=total_contents,
        unique_hashes=unique_hashes,
        total_references=total_references,
        total_size_bytes=total_size,
        deduplicated_size_bytes=deduplicated_size,
        savings_bytes=savings,
        savings_percent=savings_percent,
        most_referenced=most_referenced,
    )
