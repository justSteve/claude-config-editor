"""
MCP server service layer.

Handles business logic for MCP server operations including:
- Querying MCP servers across snapshots
- Retrieving server details and configuration
- Server status and capabilities
- Server logs information
"""

import json
import logging
from typing import Optional, Any
from datetime import datetime

from sqlalchemy import select, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.core import models
from src.core.schemas import (
    McpServerSummary,
    McpServerDetail,
    McpServerStatusResponse,
    McpServerConfigResponse,
    McpServerCapabilitiesResponse,
    McpServerLogsResponse,
    McpServerStatsResponse,
    PaginationParams,
)
from src.api.exceptions import NotFoundException

logger = logging.getLogger(__name__)


class McpService:
    """Service for MCP server operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize MCP service.

        Args:
            db: Database session
        """
        self.db = db

    async def list_mcp_servers(
        self,
        snapshot_id: Optional[int] = None,
        server_name: Optional[str] = None,
        pagination: Optional[PaginationParams] = None,
    ) -> tuple[list[McpServerSummary], int]:
        """
        List MCP servers with optional filtering and pagination.

        Args:
            snapshot_id: Filter by snapshot ID
            server_name: Filter by server name (partial match)
            pagination: Pagination parameters

        Returns:
            Tuple of (list of server summaries, total count)
        """
        # Build base query with joins to get snapshot and path info
        stmt = (
            select(models.McpServer)
            .join(models.SnapshotPath)
            .join(models.Snapshot)
        )

        # Apply filters
        if snapshot_id:
            stmt = stmt.where(models.Snapshot.id == snapshot_id)
        if server_name:
            stmt = stmt.where(models.McpServer.server_name.ilike(f"%{server_name}%"))

        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await self.db.scalar(count_stmt) or 0

        # Apply pagination
        if pagination:
            stmt = stmt.offset(pagination.offset).limit(pagination.limit)

        # Order by server name
        stmt = stmt.order_by(models.McpServer.server_name)

        # Execute query with eager loading
        result = await self.db.execute(
            stmt.options(
                joinedload(models.McpServer.snapshot_path).joinedload(
                    models.SnapshotPath.snapshot
                )
            )
        )
        servers = result.unique().scalars().all()

        # Convert to summaries
        summaries = []
        for server in servers:
            summaries.append(
                McpServerSummary(
                    id=server.id,
                    server_name=server.server_name,
                    command=server.command,
                    snapshot_id=server.snapshot_path.snapshot_id,
                    snapshot_path_id=server.snapshot_path_id,
                    config_file=server.snapshot_path.resolved_path,
                )
            )

        logger.info(f"Listed {len(summaries)} MCP servers (total: {total})")
        return summaries, total

    async def get_mcp_server(self, server_id: int) -> McpServerDetail:
        """
        Get detailed information about a specific MCP server.

        Args:
            server_id: MCP server ID

        Returns:
            Detailed server information

        Raises:
            NotFoundException: If server not found
        """
        stmt = (
            select(models.McpServer)
            .where(models.McpServer.id == server_id)
            .options(
                joinedload(models.McpServer.snapshot_path).joinedload(
                    models.SnapshotPath.snapshot
                )
            )
        )

        result = await self.db.execute(stmt)
        server = result.unique().scalar_one_or_none()

        if not server:
            raise NotFoundException(f"MCP server {server_id} not found")

        # Build detail response
        detail = McpServerDetail(
            id=server.id,
            server_name=server.server_name,
            command=server.command,
            args=server.args,
            env=server.env,
            working_directory=server.working_directory,
            snapshot_path_id=server.snapshot_path_id,
            snapshot_id=server.snapshot_path.snapshot_id,
            config_file=server.snapshot_path.resolved_path,
            snapshot_time=server.snapshot_path.snapshot.snapshot_time,
        )

        logger.info(f"Retrieved MCP server {server_id}: {server.server_name}")
        return detail

    async def get_mcp_server_status(
        self, server_id: int
    ) -> McpServerStatusResponse:
        """
        Get operational status for an MCP server.

        Args:
            server_id: MCP server ID

        Returns:
            Server status information

        Raises:
            NotFoundException: If server not found
        """
        # Get the server
        stmt = (
            select(models.McpServer)
            .where(models.McpServer.id == server_id)
            .options(
                joinedload(models.McpServer.snapshot_path).joinedload(
                    models.SnapshotPath.snapshot
                )
            )
        )

        result = await self.db.execute(stmt)
        server = result.unique().scalar_one_or_none()

        if not server:
            raise NotFoundException(f"MCP server {server_id} not found")

        # Find all occurrences of this server across snapshots
        # (servers with same name)
        stmt = (
            select(models.McpServer, models.Snapshot, models.SnapshotPath)
            .join(models.SnapshotPath)
            .join(models.Snapshot)
            .where(models.McpServer.server_name == server.server_name)
            .order_by(models.Snapshot.snapshot_time.desc())
        )

        result = await self.db.execute(stmt)
        occurrences = result.all()

        # Build status response
        snapshot_count = len(occurrences)
        config_locations = list(
            set(occ.SnapshotPath.resolved_path for occ in occurrences)
        )
        last_seen = max(occ.Snapshot.snapshot_time for occ in occurrences)

        # Determine status
        # "detected" if found in recent snapshot, "configured" otherwise
        status = "detected" if occurrences else "unknown"

        status_response = McpServerStatusResponse(
            server_id=server.id,
            server_name=server.server_name,
            status=status,
            last_seen=last_seen,
            snapshot_count=snapshot_count,
            config_locations=config_locations,
        )

        logger.info(
            f"Retrieved status for MCP server {server_id}: "
            f"{status}, seen in {snapshot_count} snapshots"
        )
        return status_response

    async def get_mcp_server_config(
        self, server_id: int
    ) -> McpServerConfigResponse:
        """
        Get configuration for an MCP server (will be sanitized).

        Args:
            server_id: MCP server ID

        Returns:
            Server configuration (sanitized for security)

        Raises:
            NotFoundException: If server not found
        """
        stmt = select(models.McpServer).where(models.McpServer.id == server_id)
        result = await self.db.execute(stmt)
        server = result.scalar_one_or_none()

        if not server:
            raise NotFoundException(f"MCP server {server_id} not found")

        # Parse args and env if present
        args_dict = None
        if server.args:
            try:
                args_dict = json.loads(server.args)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse args for server {server_id}")
                args_dict = {"_raw": server.args}

        env_dict = None
        if server.env:
            try:
                env_dict = json.loads(server.env)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse env for server {server_id}")
                env_dict = {"_raw": server.env}

        # TODO: Apply sanitization (will be implemented in next step)
        # For now, mark as not sanitized
        config_response = McpServerConfigResponse(
            server_id=server.id,
            server_name=server.server_name,
            command=server.command,
            args=args_dict,
            env=env_dict,
            working_directory=server.working_directory,
            sanitized=False,  # TODO: Set to True after sanitization
        )

        logger.info(f"Retrieved config for MCP server {server_id}")
        return config_response

    async def get_mcp_server_capabilities(
        self, server_id: int
    ) -> McpServerCapabilitiesResponse:
        """
        Get capabilities for an MCP server (based on configuration).

        Args:
            server_id: MCP server ID

        Returns:
            Server capabilities information

        Raises:
            NotFoundException: If server not found
        """
        stmt = select(models.McpServer).where(models.McpServer.id == server_id)
        result = await self.db.execute(stmt)
        server = result.scalar_one_or_none()

        if not server:
            raise NotFoundException(f"MCP server {server_id} not found")

        # Detect command type from command string
        command_type = None
        if server.command:
            cmd_lower = server.command.lower()
            if "node" in cmd_lower or ".js" in cmd_lower:
                command_type = "node"
            elif "python" in cmd_lower or ".py" in cmd_lower:
                command_type = "python"
            elif "npx" in cmd_lower:
                command_type = "npx"
            else:
                command_type = "binary"

        capabilities = McpServerCapabilitiesResponse(
            server_id=server.id,
            server_name=server.server_name,
            command_type=command_type,
            has_args=server.args is not None and len(server.args) > 0,
            has_env=server.env is not None and len(server.env) > 0,
            has_working_dir=(
                server.working_directory is not None
                and len(server.working_directory) > 0
            ),
        )

        logger.info(f"Retrieved capabilities for MCP server {server_id}")
        return capabilities

    async def get_mcp_server_logs(
        self, server_id: int
    ) -> McpServerLogsResponse:
        """
        Get log information for an MCP server.

        Args:
            server_id: MCP server ID

        Returns:
            Server logs information (sanitized)

        Raises:
            NotFoundException: If server not found
        """
        stmt = (
            select(models.McpServer)
            .where(models.McpServer.id == server_id)
            .options(joinedload(models.McpServer.snapshot_path))
        )
        result = await self.db.execute(stmt)
        server = result.unique().scalar_one_or_none()

        if not server:
            raise NotFoundException(f"MCP server {server_id} not found")

        # Look for annotations on the snapshot path that might contain log info
        # MCP logs are typically enumerated during scanning
        stmt = (
            select(models.Annotation)
            .where(models.Annotation.snapshot_path_id == server.snapshot_path_id)
            .where(models.Annotation.annotation_type == "mcp_logs")
        )
        result = await self.db.execute(stmt)
        log_annotations = result.scalars().all()

        log_files_found = 0
        log_locations = []

        # Parse log information from annotations
        for annotation in log_annotations:
            try:
                # Annotations may contain JSON with log file info
                if annotation.annotation_text.startswith("{"):
                    log_data = json.loads(annotation.annotation_text)
                    if "log_files" in log_data:
                        log_files = log_data["log_files"]
                        log_files_found += len(log_files)
                        log_locations.extend(log_files)
            except json.JSONDecodeError:
                logger.warning(
                    f"Failed to parse log annotation for server {server_id}"
                )

        # TODO: Apply sanitization to log_locations
        logs_response = McpServerLogsResponse(
            server_id=server.id,
            server_name=server.server_name,
            log_files_found=log_files_found,
            log_locations=log_locations,
            sanitized=False,  # TODO: Set to True after sanitization
        )

        logger.info(
            f"Retrieved log info for MCP server {server_id}: "
            f"{log_files_found} files found"
        )
        return logs_response

    async def get_mcp_server_stats(self) -> McpServerStatsResponse:
        """
        Get statistics about MCP servers across all snapshots.

        Returns:
            Statistics about MCP servers
        """
        # Count total unique servers (by name)
        stmt = select(func.count(distinct(models.McpServer.server_name)))
        total_servers = await self.db.scalar(stmt) or 0

        # Count total configurations
        stmt = select(func.count(models.McpServer.id))
        total_configurations = await self.db.scalar(stmt) or 0

        # Servers by snapshot
        stmt = (
            select(
                models.Snapshot.id,
                models.Snapshot.snapshot_time,
                func.count(models.McpServer.id),
            )
            .join(models.SnapshotPath)
            .join(models.McpServer)
            .group_by(models.Snapshot.id, models.Snapshot.snapshot_time)
            .order_by(models.Snapshot.snapshot_time.desc())
        )
        result = await self.db.execute(stmt)
        servers_by_snapshot = {
            f"Snapshot {row[0]} ({row[1].strftime('%Y-%m-%d %H:%M')})": row[2]
            for row in result.all()
        }

        # Most common servers
        stmt = (
            select(models.McpServer.server_name, func.count(models.McpServer.id))
            .group_by(models.McpServer.server_name)
            .order_by(func.count(models.McpServer.id).desc())
            .limit(10)
        )
        result = await self.db.execute(stmt)
        most_common_servers = [
            {"server_name": row[0], "count": row[1]} for row in result.all()
        ]

        # Config file locations
        stmt = (
            select(distinct(models.SnapshotPath.resolved_path))
            .join(models.McpServer)
        )
        result = await self.db.execute(stmt)
        config_file_locations = [row[0] for row in result.all()]

        stats = McpServerStatsResponse(
            total_servers=total_servers,
            total_configurations=total_configurations,
            servers_by_snapshot=servers_by_snapshot,
            most_common_servers=most_common_servers,
            config_file_locations=config_file_locations,
        )

        logger.info(
            f"Retrieved MCP server stats: {total_servers} unique servers, "
            f"{total_configurations} total configurations"
        )
        return stats
