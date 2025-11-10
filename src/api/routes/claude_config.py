"""
Claude Config API endpoints.

Provides operations for querying and analyzing Claude configuration files.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.schemas import (
    ClaudeConfigSummary,
    ClaudeConfigDetail,
    ClaudeConfigComparison,
    ConfigSummaryStats,
    ClaudeConfigListResponse,
    ClaudeConfigDetailResponse,
)
from src.api.dependencies import get_db
from src.api.services import ClaudeConfigService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/snapshots/{snapshot_id}/claude-configs",
    response_model=ClaudeConfigListResponse,
    summary="List Claude configs in snapshot",
    description="Get all Claude configuration files found in a snapshot with optional filtering.",
)
async def list_claude_configs(
    snapshot_id: int,
    config_type: Optional[str] = Query(
        None,
        description="Filter by config type (desktop/project/enterprise)"
    ),
    min_projects: Optional[int] = Query(
        None,
        description="Minimum number of projects",
        ge=0
    ),
    min_size: Optional[int] = Query(
        None,
        description="Minimum file size in bytes",
        ge=0
    ),
    db: AsyncSession = Depends(get_db),
) -> ClaudeConfigListResponse:
    """
    List Claude configurations in a snapshot.

    Returns all .claude.json files found during the snapshot scan,
    with optional filters for config type, project count, and file size.

    Args:
        snapshot_id: Snapshot ID to query
        config_type: Optional filter by type
        min_projects: Optional minimum project count
        min_size: Optional minimum file size
        db: Database session

    Returns:
        List of configuration summaries
    """
    service = ClaudeConfigService(db)

    configs = await service.list_configs(
        snapshot_id=snapshot_id,
        config_type=config_type,
        min_projects=min_projects,
        min_size=min_size,
    )

    return ClaudeConfigListResponse(
        items=configs,
        total=len(configs),
        page=1,
        page_size=len(configs),
        total_pages=1,
    )


@router.get(
    "/claude-configs/{config_id}",
    response_model=ClaudeConfigDetailResponse,
    summary="Get Claude config details",
    description="Get detailed information about a specific Claude configuration.",
)
async def get_claude_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
) -> ClaudeConfigDetailResponse:
    """
    Get detailed Claude configuration information.

    Returns complete metadata including largest project,
    file path, content hash, and modification times.

    Args:
        config_id: Configuration ID
        db: Database session

    Returns:
        Detailed configuration information
    """
    service = ClaudeConfigService(db)

    config = await service.get_config_detail(config_id)

    return ClaudeConfigDetailResponse(config=config)


@router.get(
    "/claude-configs/{config_id}/compare/{other_id}",
    response_model=ClaudeConfigComparison,
    summary="Compare two Claude configs",
    description="Compare two Claude configurations and show what changed between them.",
)
async def compare_claude_configs(
    config_id: int,
    other_id: int,
    db: AsyncSession = Depends(get_db),
) -> ClaudeConfigComparison:
    """
    Compare two Claude configurations.

    Detects differences in project counts, MCP server counts,
    and file sizes between two configuration snapshots.

    Args:
        config_id: First configuration ID
        other_id: Second configuration ID
        db: Database session

    Returns:
        Comparison with detected differences
    """
    service = ClaudeConfigService(db)

    comparison = await service.compare_configs(config_id, other_id)

    return comparison


@router.get(
    "/snapshots/{snapshot_id}/claude-configs/summary",
    response_model=ConfigSummaryStats,
    summary="Get config summary statistics",
    description="Get aggregate statistics for all Claude configs in a snapshot.",
)
async def get_config_summary(
    snapshot_id: int,
    db: AsyncSession = Depends(get_db),
) -> ConfigSummaryStats:
    """
    Get summary statistics for Claude configurations.

    Returns aggregate counts, sizes, and identifies
    bloated configurations (> 1MB).

    Args:
        snapshot_id: Snapshot ID
        db: Database session

    Returns:
        Summary statistics
    """
    service = ClaudeConfigService(db)

    stats = await service.get_config_summary(snapshot_id)

    return stats
