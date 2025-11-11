"""
MCP Server API endpoints.

Provides operations for querying and analyzing MCP server configurations
across snapshots.

All responses are automatically sanitized to prevent sensitive data leakage.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.schemas import (
    McpServerSummary,
    McpServerDetail,
    McpServerStatusResponse,
    McpServerConfigResponse,
    McpServerCapabilitiesResponse,
    McpServerLogsResponse,
    McpServerListResponse,
    McpServerStatsResponse,
    PaginationParams,
)
from src.api.dependencies import get_db, get_pagination
from src.api.services import McpService
from src.utils import sanitize_response

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/mcp-servers",
    response_model=McpServerListResponse,
    summary="List MCP servers",
    description="""
    Get all MCP servers found across snapshots with optional filtering.

    MCP servers are extracted from Claude configuration files during snapshot
    creation. Use filters to narrow down results by snapshot or server name.

    **Pagination**: Use `page` and `limit` parameters for pagination.
    **Filtering**: Use `snapshot_id` to see servers from a specific snapshot.
    """,
)
async def list_mcp_servers(
    snapshot_id: Optional[int] = Query(
        None,
        description="Filter by snapshot ID"
    ),
    server_name: Optional[str] = Query(
        None,
        description="Filter by server name (partial match, case-insensitive)"
    ),
    pagination: PaginationParams = Depends(get_pagination),
    db: AsyncSession = Depends(get_db),
) -> McpServerListResponse:
    """
    List MCP servers with optional filtering.

    Returns all MCP server configurations found during snapshot scans,
    with optional filters for snapshot and server name.

    Args:
        snapshot_id: Filter by snapshot ID
        server_name: Filter by server name (partial match)
        pagination: Pagination parameters (page, limit)
        db: Database session

    Returns:
        Paginated list of MCP server summaries
    """
    service = McpService(db)
    servers, total = await service.list_mcp_servers(
        snapshot_id=snapshot_id,
        server_name=server_name,
        pagination=pagination,
    )

    # Build paginated response
    response = McpServerListResponse(
        items=servers,
        total=total,
        page=pagination.page,
        page_size=pagination.limit,
        total_pages=(total + pagination.limit - 1) // pagination.limit if total > 0 else 0,
        has_next=pagination.offset + len(servers) < total,
        has_previous=pagination.page > 1,
    )

    logger.info(
        f"Listed {len(servers)} MCP servers (page {pagination.page}, total: {total})"
    )
    return response


@router.get(
    "/mcp-servers/{server_id}",
    response_model=McpServerDetail,
    summary="Get MCP server details",
    description="""
    Get detailed information about a specific MCP server.

    Returns complete configuration including command, arguments, environment
    variables, and the snapshot where it was found.

    **Note**: Sensitive data in this response will be sanitized for security.
    """,
)
async def get_mcp_server(
    server_id: int,
    db: AsyncSession = Depends(get_db),
) -> McpServerDetail:
    """
    Get detailed information about an MCP server.

    Args:
        server_id: MCP server ID
        db: Database session

    Returns:
        Detailed server information

    Raises:
        NotFoundException: If server not found (404)
    """
    service = McpService(db)
    detail = await service.get_mcp_server(server_id)

    # Sanitize sensitive data in the response
    detail = sanitize_response(detail)

    logger.info(f"Retrieved MCP server {server_id}: {detail.server_name}")
    return detail


@router.get(
    "/mcp-servers/{server_id}/status",
    response_model=McpServerStatusResponse,
    summary="Get MCP server status",
    description="""
    Get operational status for an MCP server.

    Returns information about when the server was last seen, in how many
    snapshots it appears, and where it's configured.

    **Status values**:
    - `detected`: Server found in recent snapshot
    - `configured`: Server exists but not recently seen
    - `unknown`: Status cannot be determined
    """,
)
async def get_mcp_server_status(
    server_id: int,
    db: AsyncSession = Depends(get_db),
) -> McpServerStatusResponse:
    """
    Get operational status for an MCP server.

    Returns status information including last seen time, number of snapshots
    containing this server, and configuration locations.

    Args:
        server_id: MCP server ID
        db: Database session

    Returns:
        Server status information

    Raises:
        NotFoundException: If server not found (404)
    """
    service = McpService(db)
    status_response = await service.get_mcp_server_status(server_id)

    logger.info(
        f"Retrieved status for MCP server {server_id}: {status_response.status}"
    )
    return status_response


@router.get(
    "/mcp-servers/{server_id}/config",
    response_model=McpServerConfigResponse,
    summary="Get MCP server configuration",
    description="""
    Get the full configuration for an MCP server.

    **IMPORTANT**: This response is automatically sanitized to remove:
    - API keys and tokens
    - Passwords and credentials
    - Connection strings with credentials
    - Personal identifiable information (PII) in paths
    - Environment variables containing secrets

    Sensitive values are replaced with placeholders like `[REDACTED_API_KEY]`.

    The `sanitized` field will be `true` when sanitization has been applied.
    """,
)
async def get_mcp_server_config(
    server_id: int,
    db: AsyncSession = Depends(get_db),
) -> McpServerConfigResponse:
    """
    Get configuration for an MCP server (sanitized).

    Returns the server's configuration including command, arguments, and
    environment variables. All sensitive data is automatically redacted.

    Args:
        server_id: MCP server ID
        db: Database session

    Returns:
        Server configuration (sanitized)

    Raises:
        NotFoundException: If server not found (404)
    """
    service = McpService(db)
    config = await service.get_mcp_server_config(server_id)

    # Apply sanitization to protect sensitive data
    config = sanitize_response(config)
    config.sanitized = True

    logger.info(f"Retrieved config for MCP server {server_id} (sanitized)")
    return config


@router.get(
    "/mcp-servers/{server_id}/capabilities",
    response_model=McpServerCapabilitiesResponse,
    summary="Get MCP server capabilities",
    description="""
    Get detected capabilities for an MCP server.

    Analyzes the server configuration to determine:
    - Command type (node, python, binary, etc.)
    - Whether arguments are configured
    - Whether environment variables are set
    - Whether a working directory is specified

    **Note**: This is based on static configuration analysis, not runtime capabilities.
    """,
)
async def get_mcp_server_capabilities(
    server_id: int,
    db: AsyncSession = Depends(get_db),
) -> McpServerCapabilitiesResponse:
    """
    Get capabilities for an MCP server.

    Analyzes the server configuration to detect capabilities based on
    command type and configuration settings.

    Args:
        server_id: MCP server ID
        db: Database session

    Returns:
        Server capabilities information

    Raises:
        NotFoundException: If server not found (404)
    """
    service = McpService(db)
    capabilities = await service.get_mcp_server_capabilities(server_id)

    logger.info(
        f"Retrieved capabilities for MCP server {server_id}: "
        f"type={capabilities.command_type}"
    )
    return capabilities


@router.get(
    "/mcp-servers/{server_id}/logs",
    response_model=McpServerLogsResponse,
    summary="Get MCP server logs information",
    description="""
    Get information about log files associated with an MCP server.

    During snapshot creation, the scanner may enumerate MCP log files in the
    Claude Desktop logs directory. This endpoint returns information about
    log files found for this server.

    **Note**: This returns log file locations, not log contents. Log file
    paths are sanitized to remove personal information.
    """,
)
async def get_mcp_server_logs(
    server_id: int,
    db: AsyncSession = Depends(get_db),
) -> McpServerLogsResponse:
    """
    Get log information for an MCP server.

    Returns information about log files found during snapshot scans,
    including file locations (sanitized) and file counts.

    Args:
        server_id: MCP server ID
        db: Database session

    Returns:
        Server logs information (sanitized)

    Raises:
        NotFoundException: If server not found (404)
    """
    service = McpService(db)
    logs = await service.get_mcp_server_logs(server_id)

    # Apply sanitization to log paths to remove PII
    logs = sanitize_response(logs)
    logs.sanitized = True

    logger.info(
        f"Retrieved log info for MCP server {server_id}: "
        f"{logs.log_files_found} files (sanitized)"
    )
    return logs


@router.get(
    "/mcp-servers/stats",
    response_model=McpServerStatsResponse,
    summary="Get MCP server statistics",
    description="""
    Get statistics about MCP servers across all snapshots.

    Returns aggregated information including:
    - Total number of unique servers
    - Total configurations across all snapshots
    - Server counts by snapshot
    - Most commonly configured servers
    - Configuration file locations

    **Use case**: Get an overview of MCP server usage across your Claude
    configuration history.
    """,
)
async def get_mcp_server_stats(
    db: AsyncSession = Depends(get_db),
) -> McpServerStatsResponse:
    """
    Get statistics about MCP servers.

    Returns aggregated statistics about MCP servers across all snapshots,
    including counts, most common servers, and configuration locations.

    Args:
        db: Database session

    Returns:
        MCP server statistics
    """
    service = McpService(db)
    stats = await service.get_mcp_server_stats()

    logger.info(
        f"Retrieved MCP stats: {stats.total_servers} unique servers, "
        f"{stats.total_configurations} total configurations"
    )
    return stats
