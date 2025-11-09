"""
Converter utilities for transforming database models to API schemas.

Provides functions to convert SQLAlchemy models to Pydantic schemas
with proper handling of relationships and computed fields.
"""

from typing import Optional

from src.core import models
from src.core.schemas import (
    snapshots as snapshot_schemas,
    paths as path_schemas,
    changes as change_schemas,
)


def snapshot_to_response(snapshot: models.Snapshot) -> snapshot_schemas.SnapshotResponse:
    """
    Convert Snapshot model to SnapshotResponse schema.

    Args:
        snapshot: Database Snapshot model

    Returns:
        SnapshotResponse schema
    """
    return snapshot_schemas.SnapshotResponse(
        id=snapshot.id,
        snapshot_time=snapshot.snapshot_time,
        snapshot_hash=snapshot.snapshot_hash,
        trigger_type=snapshot.trigger_type,
        triggered_by=snapshot.triggered_by,
        notes=snapshot.notes,
        os_type=snapshot.os_type,
        os_version=snapshot.os_version,
        hostname=snapshot.hostname,
        username=snapshot.username,
    )


def snapshot_to_summary(snapshot: models.Snapshot) -> snapshot_schemas.SnapshotSummary:
    """
    Convert Snapshot model to SnapshotSummary schema.

    Args:
        snapshot: Database Snapshot model

    Returns:
        SnapshotSummary schema
    """
    # Extract tag names from relationships
    tags = [tag.tag_name for tag in snapshot.tags] if snapshot.tags else []

    return snapshot_schemas.SnapshotSummary(
        id=snapshot.id,
        snapshot_time=snapshot.snapshot_time,
        snapshot_hash=snapshot.snapshot_hash,
        trigger_type=snapshot.trigger_type,
        triggered_by=snapshot.triggered_by,
        notes=snapshot.notes,
        os_type=snapshot.os_type,
        os_version=snapshot.os_version,
        hostname=snapshot.hostname,
        username=snapshot.username,
        total_locations=snapshot.total_locations,
        files_found=snapshot.files_found,
        directories_found=snapshot.directories_found,
        total_size_bytes=snapshot.total_size_bytes,
        changed_from_previous=snapshot.changed_from_previous,
        is_baseline=snapshot.is_baseline,
        tags=tags,
    )


def snapshot_to_detail(snapshot: models.Snapshot) -> snapshot_schemas.SnapshotDetailResponse:
    """
    Convert Snapshot model to SnapshotDetailResponse schema with all relationships.

    Args:
        snapshot: Database Snapshot model with loaded relationships

    Returns:
        SnapshotDetailResponse schema
    """
    # Convert relationships
    env_vars = [
        snapshot_schemas.SnapshotEnvVarResponse(
            placeholder=env_var.placeholder,
            resolved_path=env_var.resolved_path,
        )
        for env_var in snapshot.env_vars
    ] if snapshot.env_vars else []

    annotations = [
        snapshot_schemas.SnapshotAnnotationResponse(
            id=ann.id,
            annotation_text=ann.annotation_text,
            annotation_type=ann.annotation_type,
            created_at=ann.created_at,
            created_by=ann.created_by,
        )
        for ann in snapshot.annotations
    ] if snapshot.annotations else []

    tag_details = [
        snapshot_schemas.SnapshotTagResponse(
            id=tag.id,
            tag_name=tag.tag_name,
            tag_type=tag.tag_type,
            created_at=tag.created_at,
            created_by=tag.created_by,
            description=tag.description,
        )
        for tag in snapshot.tags
    ] if snapshot.tags else []

    # Extract tag names for summary
    tags = [tag.tag_name for tag in snapshot.tags] if snapshot.tags else []

    return snapshot_schemas.SnapshotDetailResponse(
        id=snapshot.id,
        snapshot_time=snapshot.snapshot_time,
        snapshot_hash=snapshot.snapshot_hash,
        trigger_type=snapshot.trigger_type,
        triggered_by=snapshot.triggered_by,
        notes=snapshot.notes,
        os_type=snapshot.os_type,
        os_version=snapshot.os_version,
        hostname=snapshot.hostname,
        username=snapshot.username,
        total_locations=snapshot.total_locations,
        files_found=snapshot.files_found,
        directories_found=snapshot.directories_found,
        total_size_bytes=snapshot.total_size_bytes,
        changed_from_previous=snapshot.changed_from_previous,
        is_baseline=snapshot.is_baseline,
        tags=tags,
        parent_snapshot_id=snapshot.parent_snapshot_id,
        working_directory=snapshot.working_directory,
        env_vars=env_vars,
        annotations=annotations,
        tag_details=tag_details,
    )


def path_to_response(path: models.SnapshotPath) -> path_schemas.PathResponse:
    """
    Convert SnapshotPath model to PathResponse schema.

    Args:
        path: Database SnapshotPath model

    Returns:
        PathResponse schema
    """
    return path_schemas.PathResponse(
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
        content_hash=path.content_hash,
    )


def path_to_summary(path: models.SnapshotPath) -> path_schemas.PathSummary:
    """
    Convert SnapshotPath model to PathSummary schema.

    Args:
        path: Database SnapshotPath model

    Returns:
        PathSummary schema
    """
    return path_schemas.PathSummary(
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
        content_hash=path.content_hash,
        created_time=path.created_time,
        accessed_time=path.accessed_time,
        permissions=path.permissions,
        item_count=path.item_count,
        error_message=path.error_message,
    )


def path_to_detail(path: models.SnapshotPath) -> path_schemas.PathDetailResponse:
    """
    Convert SnapshotPath model to PathDetailResponse schema with all relationships.

    Args:
        path: Database SnapshotPath model with loaded relationships

    Returns:
        PathDetailResponse schema
    """
    # Convert file content if available
    content = None
    if path.content:
        content = path_schemas.FileContentResponse(
            id=path.content.id,
            content_hash=path.content.content_hash,
            content_type=path.content.content_type,
            size_bytes=path.content.size_bytes,
            compression=path.content.compression,
            reference_count=path.content.reference_count,
            created_at=path.content.created_at,
            content_text=path.content.content_text,
            content_binary=path.content.content_binary,
        )

    # Convert JSON data
    json_data = [
        path_schemas.JsonDataResponse(
            id=jd.id,
            json_path=jd.json_path,
            json_value=jd.json_value,
            json_type=jd.json_type,
        )
        for jd in path.json_data
    ] if path.json_data else []

    # Convert Claude config
    claude_config = None
    if path.claude_config:
        claude_config = path_schemas.ClaudeConfigResponse(
            id=path.claude_config.id,
            config_type=path.claude_config.config_type,
            num_projects=path.claude_config.num_projects,
            num_mcp_servers=path.claude_config.num_mcp_servers,
            num_startups=path.claude_config.num_startups,
            total_size_bytes=path.claude_config.total_size_bytes,
            largest_project_path=path.claude_config.largest_project_path,
            largest_project_size=path.claude_config.largest_project_size,
        )

    # Convert MCP servers
    mcp_servers = [
        path_schemas.McpServerResponse(
            id=mcp.id,
            server_name=mcp.server_name,
            command=mcp.command,
            args=mcp.args,
            env=mcp.env,
            working_directory=mcp.working_directory,
        )
        for mcp in path.mcp_servers
    ] if path.mcp_servers else []

    # Convert annotations
    annotations = [
        path_schemas.PathAnnotationResponse(
            id=ann.id,
            annotation_text=ann.annotation_text,
            annotation_type=ann.annotation_type,
            created_at=ann.created_at,
            created_by=ann.created_by,
        )
        for ann in path.annotations
    ] if path.annotations else []

    return path_schemas.PathDetailResponse(
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
        content_hash=path.content_hash,
        created_time=path.created_time,
        accessed_time=path.accessed_time,
        permissions=path.permissions,
        item_count=path.item_count,
        error_message=path.error_message,
        content=content,
        json_data=json_data,
        claude_config=claude_config,
        mcp_servers=mcp_servers,
        annotations=annotations,
    )


def change_to_response(change: models.SnapshotChange) -> change_schemas.ChangeResponse:
    """
    Convert SnapshotChange model to ChangeResponse schema.

    Args:
        change: Database SnapshotChange model

    Returns:
        ChangeResponse schema
    """
    return change_schemas.ChangeResponse(
        id=change.id,
        snapshot_id=change.snapshot_id,
        previous_snapshot_id=change.previous_snapshot_id,
        path_template=change.path_template,
        change_type=change.change_type,
        old_content_hash=change.old_content_hash,
        new_content_hash=change.new_content_hash,
        old_size_bytes=change.old_size_bytes,
        new_size_bytes=change.new_size_bytes,
    )


def change_to_summary(change: models.SnapshotChange) -> change_schemas.ChangeSummary:
    """
    Convert SnapshotChange model to ChangeSummary schema with computed fields.

    Args:
        change: Database SnapshotChange model

    Returns:
        ChangeSummary schema
    """
    # Calculate size changes
    size_change_bytes = None
    size_change_percent = None

    if change.old_size_bytes is not None and change.new_size_bytes is not None:
        size_change_bytes = change.new_size_bytes - change.old_size_bytes
        if change.old_size_bytes > 0:
            size_change_percent = (size_change_bytes /
                                   change.old_size_bytes) * 100

    return change_schemas.ChangeSummary(
        id=change.id,
        snapshot_id=change.snapshot_id,
        previous_snapshot_id=change.previous_snapshot_id,
        path_template=change.path_template,
        change_type=change.change_type,
        old_content_hash=change.old_content_hash,
        new_content_hash=change.new_content_hash,
        old_size_bytes=change.old_size_bytes,
        new_size_bytes=change.new_size_bytes,
        old_modified_time=change.old_modified_time,
        new_modified_time=change.new_modified_time,
        diff_summary=change.diff_summary,
        size_change_bytes=size_change_bytes,
        size_change_percent=size_change_percent,
    )


def tag_to_response(tag: models.SnapshotTag) -> snapshot_schemas.SnapshotTagResponse:
    """
    Convert SnapshotTag model to SnapshotTagResponse schema.

    Args:
        tag: Database SnapshotTag model

    Returns:
        SnapshotTagResponse schema
    """
    return snapshot_schemas.SnapshotTagResponse(
        id=tag.id,
        tag_name=tag.tag_name,
        tag_type=tag.tag_type,
        created_at=tag.created_at,
        created_by=tag.created_by,
        description=tag.description,
    )


def annotation_to_response(
    annotation: models.Annotation,
) -> snapshot_schemas.SnapshotAnnotationResponse:
    """
    Convert Annotation model to SnapshotAnnotationResponse schema.

    Args:
        annotation: Database Annotation model

    Returns:
        SnapshotAnnotationResponse schema
    """
    return snapshot_schemas.SnapshotAnnotationResponse(
        id=annotation.id,
        annotation_text=annotation.annotation_text,
        annotation_type=annotation.annotation_type,
        created_at=annotation.created_at,
        created_by=annotation.created_by,
    )


def file_content_to_response(
    content: models.FileContent,
    include_content: bool = True,
) -> path_schemas.FileContentResponse:
    """
    Convert FileContent model to FileContentResponse schema.

    Args:
        content: Database FileContent model
        include_content: Whether to include actual content (can be large)

    Returns:
        FileContentResponse schema
    """
    return path_schemas.FileContentResponse(
        id=content.id,
        content_hash=content.content_hash,
        content_type=content.content_type,
        size_bytes=content.size_bytes,
        compression=content.compression,
        reference_count=content.reference_count,
        created_at=content.created_at,
        content_text=content.content_text if include_content else None,
        content_binary=content.content_binary if include_content else None,
    )


def mcp_server_to_response(mcp: models.McpServer) -> path_schemas.McpServerResponse:
    """
    Convert McpServer model to McpServerResponse schema.

    Args:
        mcp: Database McpServer model

    Returns:
        McpServerResponse schema
    """
    return path_schemas.McpServerResponse(
        id=mcp.id,
        server_name=mcp.server_name,
        command=mcp.command,
        args=mcp.args,
        env=mcp.env,
        working_directory=mcp.working_directory,
    )


def claude_config_to_response(
    config: models.ClaudeConfig,
) -> path_schemas.ClaudeConfigResponse:
    """
    Convert ClaudeConfig model to ClaudeConfigResponse schema.

    Args:
        config: Database ClaudeConfig model

    Returns:
        ClaudeConfigResponse schema
    """
    return path_schemas.ClaudeConfigResponse(
        id=config.id,
        config_type=config.config_type,
        num_projects=config.num_projects,
        num_mcp_servers=config.num_mcp_servers,
        num_startups=config.num_startups,
        total_size_bytes=config.total_size_bytes,
        largest_project_path=config.largest_project_path,
        largest_project_size=config.largest_project_size,
    )


# Batch converters for lists
def snapshots_to_summaries(
    snapshots: list[models.Snapshot],
) -> list[snapshot_schemas.SnapshotSummary]:
    """Convert list of Snapshot models to SnapshotSummary schemas."""
    return [snapshot_to_summary(snapshot) for snapshot in snapshots]


def paths_to_summaries(
    paths: list[models.SnapshotPath],
) -> list[path_schemas.PathSummary]:
    """Convert list of SnapshotPath models to PathSummary schemas."""
    return [path_to_summary(path) for path in paths]


def changes_to_summaries(
    changes: list[models.SnapshotChange],
) -> list[change_schemas.ChangeSummary]:
    """Convert list of SnapshotChange models to ChangeSummary schemas."""
    return [change_to_summary(change) for change in changes]
