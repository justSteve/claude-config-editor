"""
Claude Config service layer.

Handles business logic for Claude configuration operations including:
- Querying configs by snapshot
- Retrieving detailed config information
- Comparing configs across snapshots
- Generating summary statistics
"""

import logging
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.core import models
from src.core.schemas import (
    ClaudeConfigSummary,
    ClaudeConfigDetail,
    ConfigDifferences,
    ClaudeConfigComparison,
    ConfigSummaryStats,
)
from src.api.exceptions import NotFoundException

logger = logging.getLogger(__name__)


class ClaudeConfigService:
    """Service for Claude configuration operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize Claude config service.

        Args:
            db: Database session
        """
        self.db = db

    async def list_configs(
        self,
        snapshot_id: int,
        config_type: Optional[str] = None,
        min_projects: Optional[int] = None,
        min_size: Optional[int] = None,
    ) -> list[ClaudeConfigSummary]:
        """
        List Claude configurations in a snapshot with optional filters.

        Args:
            snapshot_id: Snapshot ID to query
            config_type: Filter by config type (desktop/project/enterprise)
            min_projects: Minimum number of projects
            min_size: Minimum file size in bytes

        Returns:
            List of configuration summaries

        Raises:
            NotFoundException: If snapshot not found
        """
        # Verify snapshot exists
        stmt = select(models.Snapshot).where(models.Snapshot.id == snapshot_id)
        result = await self.db.execute(stmt)
        snapshot = result.scalar_one_or_none()
        if not snapshot:
            raise NotFoundException(f"Snapshot {snapshot_id} not found")

        # Query configs with filters
        stmt = (
            select(models.ClaudeConfig, models.SnapshotPath)
            .join(models.SnapshotPath)
            .where(models.SnapshotPath.snapshot_id == snapshot_id)
        )

        if config_type:
            stmt = stmt.where(models.ClaudeConfig.config_type == config_type)
        if min_projects is not None:
            stmt = stmt.where(models.ClaudeConfig.num_projects >= min_projects)
        if min_size is not None:
            stmt = stmt.where(models.ClaudeConfig.total_size_bytes >= min_size)

        result = await self.db.execute(stmt)
        rows = result.all()

        # Convert to summaries
        summaries = []
        for config, path in rows:
            summaries.append(
                ClaudeConfigSummary(
                    id=config.id,
                    config_type=config.config_type,
                    num_projects=config.num_projects,
                    num_mcp_servers=config.num_mcp_servers,
                    num_startups=config.num_startups,
                    total_size_bytes=config.total_size_bytes,
                    snapshot_id=snapshot_id,
                    snapshot_time=snapshot.snapshot_time,
                )
            )

        logger.info(f"Found {len(summaries)} configs in snapshot {snapshot_id}")
        return summaries

    async def get_config_detail(self, config_id: int) -> ClaudeConfigDetail:
        """
        Get detailed information about a Claude configuration.

        Args:
            config_id: Configuration ID

        Returns:
            Detailed configuration information

        Raises:
            NotFoundException: If config not found
        """
        # Query config with relationships
        stmt = (
            select(models.ClaudeConfig, models.SnapshotPath, models.Snapshot)
            .join(models.SnapshotPath)
            .join(models.Snapshot)
            .where(models.ClaudeConfig.id == config_id)
        )

        result = await self.db.execute(stmt)
        row = result.first()
        if not row:
            raise NotFoundException(f"Claude config {config_id} not found")

        config, path, snapshot = row

        return ClaudeConfigDetail(
            id=config.id,
            config_type=config.config_type,
            num_projects=config.num_projects,
            num_mcp_servers=config.num_mcp_servers,
            num_startups=config.num_startups,
            total_size_bytes=config.total_size_bytes,
            snapshot_id=snapshot.id,
            snapshot_time=snapshot.snapshot_time,
            largest_project_path=config.largest_project_path,
            largest_project_size=config.largest_project_size,
            resolved_path=path.resolved_path,
            content_hash=path.content_hash,
            modified_time=path.modified_time,
        )

    async def compare_configs(
        self, config_id_1: int, config_id_2: int
    ) -> ClaudeConfigComparison:
        """
        Compare two Claude configurations and detect differences.

        Args:
            config_id_1: First config ID
            config_id_2: Second config ID

        Returns:
            Comparison with detected differences

        Raises:
            NotFoundException: If either config not found
        """
        # Get both configs
        config_1 = await self._get_config_summary(config_id_1)
        config_2 = await self._get_config_summary(config_id_2)

        # Calculate differences
        projects_diff = (config_2.num_projects or 0) - (config_1.num_projects or 0)
        mcp_diff = (config_2.num_mcp_servers or 0) - (config_1.num_mcp_servers or 0)
        size_diff = (config_2.total_size_bytes or 0) - (config_1.total_size_bytes or 0)

        # Calculate percentage change
        size_change_percent = 0.0
        if config_1.total_size_bytes and config_1.total_size_bytes > 0:
            size_change_percent = (size_diff / config_1.total_size_bytes) * 100

        differences = ConfigDifferences(
            projects_added=max(0, projects_diff),
            projects_removed=max(0, -projects_diff),
            projects_modified=[],  # TODO: Detailed project tracking in future
            mcp_servers_added=max(0, mcp_diff),
            mcp_servers_removed=max(0, -mcp_diff),
            mcp_servers_modified=[],  # TODO: Detailed MCP tracking in future
            size_change_bytes=size_diff,
            size_change_percent=round(size_change_percent, 2),
        )

        return ClaudeConfigComparison(
            config_1=config_1,
            config_2=config_2,
            differences=differences,
        )

    async def get_config_summary(self, snapshot_id: int) -> ConfigSummaryStats:
        """
        Get aggregate statistics for all configs in a snapshot.

        Args:
            snapshot_id: Snapshot ID

        Returns:
            Summary statistics

        Raises:
            NotFoundException: If snapshot not found
        """
        # Get all configs for snapshot
        configs = await self.list_configs(snapshot_id)

        if not configs:
            return ConfigSummaryStats(
                total_configs=0,
                config_types={},
                total_projects=0,
                total_mcp_servers=0,
                total_size_bytes=0,
                largest_config_type=None,
                bloat_candidates=[],
            )

        # Calculate statistics
        config_types: dict[str, int] = {}
        total_projects = 0
        total_mcp_servers = 0
        total_size = 0
        bloat_threshold = 1024 * 1024  # 1MB
        bloat_candidates = []

        for config in configs:
            # Count by type
            config_types[config.config_type] = config_types.get(config.config_type, 0) + 1

            # Sum totals
            total_projects += config.num_projects or 0
            total_mcp_servers += config.num_mcp_servers or 0
            total_size += config.total_size_bytes or 0

            # Identify bloat candidates
            if config.total_size_bytes and config.total_size_bytes > bloat_threshold:
                bloat_candidates.append(config)

        # Find config type with most presence
        largest_config_type = max(config_types, key=config_types.get) if config_types else None

        return ConfigSummaryStats(
            total_configs=len(configs),
            config_types=config_types,
            total_projects=total_projects,
            total_mcp_servers=total_mcp_servers,
            total_size_bytes=total_size,
            largest_config_type=largest_config_type,
            bloat_candidates=bloat_candidates,
        )

    async def _get_config_summary(self, config_id: int) -> ClaudeConfigSummary:
        """
        Internal helper to get config summary.

        Args:
            config_id: Configuration ID

        Returns:
            Configuration summary

        Raises:
            NotFoundException: If config not found
        """
        stmt = (
            select(models.ClaudeConfig, models.SnapshotPath, models.Snapshot)
            .join(models.SnapshotPath)
            .join(models.Snapshot)
            .where(models.ClaudeConfig.id == config_id)
        )

        result = await self.db.execute(stmt)
        row = result.first()
        if not row:
            raise NotFoundException(f"Claude config {config_id} not found")

        config, path, snapshot = row

        return ClaudeConfigSummary(
            id=config.id,
            config_type=config.config_type,
            num_projects=config.num_projects,
            num_mcp_servers=config.num_mcp_servers,
            num_startups=config.num_startups,
            total_size_bytes=config.total_size_bytes,
            snapshot_id=snapshot.id,
            snapshot_time=snapshot.snapshot_time,
        )
