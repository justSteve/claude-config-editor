"""
Data models for Claude Config version control system.

Uses SQLAlchemy 2.0 ORM with async support for database operations.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    LargeBinary,
    Float,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class Snapshot(Base):
    """
    Represents a complete snapshot of Claude configurations at a point in time.
    Each scan creates a new snapshot (similar to a git commit).
    """

    __tablename__ = "snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    snapshot_time: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, index=True
    )
    snapshot_hash: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )  # SHA256

    # Trigger metadata
    trigger_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # 'manual', 'scheduled', 'api', 'cli'
    triggered_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # System context
    os_type: Mapped[str] = mapped_column(String(20), nullable=False)
    os_version: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    hostname: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    username: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    working_directory: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Scan statistics
    total_locations: Mapped[int] = mapped_column(Integer, nullable=False)
    files_found: Mapped[int] = mapped_column(Integer, nullable=False)
    directories_found: Mapped[int] = mapped_column(Integer, nullable=False)
    total_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)

    # Change detection
    changed_from_previous: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    is_baseline: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    parent_snapshot_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("snapshots.id"), nullable=True
    )

    # Relations to other tables
    env_vars: Mapped[list["SnapshotEnvVar"]] = relationship(
        "SnapshotEnvVar", back_populates="snapshot", cascade="all, delete-orphan"
    )
    paths: Mapped[list["SnapshotPath"]] = relationship(
        "SnapshotPath", back_populates="snapshot", cascade="all, delete-orphan"
    )
    changes: Mapped[list["SnapshotChange"]] = relationship(
        "SnapshotChange",
        foreign_keys="SnapshotChange.snapshot_id",
        back_populates="snapshot",
        cascade="all, delete-orphan",
    )
    tags: Mapped[list["SnapshotTag"]] = relationship(
        "SnapshotTag", back_populates="snapshot", cascade="all, delete-orphan"
    )
    annotations: Mapped[list["Annotation"]] = relationship(
        "Annotation", back_populates="snapshot", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Snapshot(id={self.id}, time={self.snapshot_time}, hash={self.snapshot_hash[:8]}...)>"


class SnapshotEnvVar(Base):
    """Environment variables captured during snapshot."""

    __tablename__ = "snapshot_env_vars"
    __table_args__ = (
        UniqueConstraint("snapshot_id", "placeholder", name="uq_snapshot_env_var"),
    )

    snapshot_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("snapshots.id", ondelete="CASCADE"), primary_key=True
    )
    placeholder: Mapped[str] = mapped_column(String(100), primary_key=True)
    resolved_path: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    snapshot: Mapped["Snapshot"] = relationship("Snapshot", back_populates="env_vars")

    def __repr__(self) -> str:
        return f"<SnapshotEnvVar({self.placeholder}={self.resolved_path})>"


class FileContent(Base):
    """
    Actual file contents (deduplicated by hash).
    Multiple snapshots can reference the same content.
    """

    __tablename__ = "file_contents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    content_hash: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )  # SHA256
    content_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_binary: Mapped[Optional[bytes]] = mapped_column(
        LargeBinary, nullable=True
    )
    content_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # 'json', 'text', 'binary', 'markdown'
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    compression: Mapped[str] = mapped_column(
        String(10), nullable=False, default="none"
    )  # 'none', 'gzip', 'zlib'
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    reference_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, index=True
    )

    # Relationships
    paths: Mapped[list["SnapshotPath"]] = relationship(
        "SnapshotPath", back_populates="content"
    )

    def __repr__(self) -> str:
        return f"<FileContent(hash={self.content_hash[:8]}..., type={self.content_type}, size={self.size_bytes}, refs={self.reference_count})>"


class SnapshotPath(Base):
    """Discovered paths and their state at snapshot time."""

    __tablename__ = "snapshot_paths"
    __table_args__ = (
        Index("idx_snapshot_paths_snapshot", "snapshot_id"),
        Index("idx_snapshot_paths_template", "path_template"),
        Index("idx_snapshot_paths_exists", "exists"),
        Index("idx_snapshot_paths_hash", "content_hash"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    snapshot_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("snapshots.id", ondelete="CASCADE"), nullable=False
    )

    # Path identification
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    path_template: Mapped[str] = mapped_column(Text, nullable=False)
    resolved_path: Mapped[str] = mapped_column(Text, nullable=False)

    # File/directory state
    exists: Mapped[bool] = mapped_column(Boolean, nullable=False)
    type: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )  # 'file', 'directory', 'symlink'

    # File metadata
    size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    modified_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    accessed_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    permissions: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Directory metadata
    item_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Content tracking
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    content_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("file_contents.id"), nullable=True
    )

    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    snapshot: Mapped["Snapshot"] = relationship("Snapshot", back_populates="paths")
    content: Mapped[Optional["FileContent"]] = relationship(
        "FileContent", back_populates="paths"
    )
    json_data: Mapped[list["JsonData"]] = relationship(
        "JsonData", back_populates="snapshot_path", cascade="all, delete-orphan"
    )
    claude_config: Mapped[Optional["ClaudeConfig"]] = relationship(
        "ClaudeConfig", back_populates="snapshot_path", uselist=False
    )
    mcp_servers: Mapped[list["McpServer"]] = relationship(
        "McpServer", back_populates="snapshot_path", cascade="all, delete-orphan"
    )
    annotations: Mapped[list["Annotation"]] = relationship(
        "Annotation", back_populates="snapshot_path", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<SnapshotPath(id={self.id}, name={self.name}, exists={self.exists})>"


class JsonData(Base):
    """Parsed JSON content for queryability."""

    __tablename__ = "json_data"
    __table_args__ = (Index("idx_json_path", "json_path"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    content_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("file_contents.id", ondelete="CASCADE"), nullable=False
    )
    snapshot_path_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("snapshot_paths.id", ondelete="CASCADE"), nullable=False
    )

    # JSON structure flattened
    json_path: Mapped[str] = mapped_column(Text, nullable=False)
    json_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    json_type: Mapped[str] = mapped_column(String(20), nullable=False)

    # Relationships
    snapshot_path: Mapped["SnapshotPath"] = relationship(
        "SnapshotPath", back_populates="json_data"
    )

    def __repr__(self) -> str:
        return f"<JsonData(path={self.json_path}, type={self.json_type})>"


class ClaudeConfig(Base):
    """Track specific Claude config structures."""

    __tablename__ = "claude_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    snapshot_path_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("snapshot_paths.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    config_type: Mapped[str] = mapped_column(String(20), nullable=False)

    # Extracted metadata
    num_projects: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    num_mcp_servers: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    num_startups: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Size analysis
    total_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    largest_project_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    largest_project_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Relationships
    snapshot_path: Mapped["SnapshotPath"] = relationship(
        "SnapshotPath", back_populates="claude_config"
    )

    def __repr__(self) -> str:
        return f"<ClaudeConfig(type={self.config_type}, projects={self.num_projects}, mcp={self.num_mcp_servers})>"


class McpServer(Base):
    """MCP server configurations extracted."""

    __tablename__ = "mcp_servers"
    __table_args__ = (Index("idx_mcp_snapshot", "snapshot_path_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    snapshot_path_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("snapshot_paths.id", ondelete="CASCADE"), nullable=False
    )

    server_name: Mapped[str] = mapped_column(String(255), nullable=False)
    command: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    args: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    env: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON object
    working_directory: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    snapshot_path: Mapped["SnapshotPath"] = relationship(
        "SnapshotPath", back_populates="mcp_servers"
    )

    def __repr__(self) -> str:
        return f"<McpServer(name={self.server_name}, command={self.command})>"


class SnapshotChange(Base):
    """Change tracking between snapshots."""

    __tablename__ = "snapshot_changes"
    __table_args__ = (
        Index("idx_changes_snapshot", "snapshot_id"),
        Index("idx_changes_type", "change_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    snapshot_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("snapshots.id", ondelete="CASCADE"), nullable=False
    )
    previous_snapshot_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("snapshots.id"), nullable=False
    )

    path_template: Mapped[str] = mapped_column(Text, nullable=False)
    change_type: Mapped[str] = mapped_column(String(20), nullable=False)

    # For modified files
    old_content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    new_content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    old_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    new_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    old_modified_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    new_modified_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )

    # Change details
    diff_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    snapshot: Mapped["Snapshot"] = relationship(
        "Snapshot",
        foreign_keys=[snapshot_id],
        back_populates="changes",
    )

    def __repr__(self) -> str:
        return f"<SnapshotChange(type={self.change_type}, path={self.path_template})>"


class SnapshotTag(Base):
    """Tags/labels for snapshots (like git tags)."""

    __tablename__ = "snapshot_tags"
    __table_args__ = (
        UniqueConstraint("tag_name", name="uq_tag_name"),
        Index("idx_tags_snapshot", "snapshot_id"),
        Index("idx_tags_name", "tag_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    snapshot_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("snapshots.id", ondelete="CASCADE"), nullable=False
    )
    tag_name: Mapped[str] = mapped_column(String(255), nullable=False)
    tag_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    snapshot: Mapped["Snapshot"] = relationship("Snapshot", back_populates="tags")

    def __repr__(self) -> str:
        return f"<SnapshotTag(name={self.tag_name}, snapshot_id={self.snapshot_id})>"


class Annotation(Base):
    """Annotations/notes on specific files or snapshots."""

    __tablename__ = "annotations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    snapshot_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("snapshots.id", ondelete="CASCADE"), nullable=False
    )
    snapshot_path_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("snapshot_paths.id", ondelete="CASCADE"), nullable=True
    )

    annotation_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    annotation_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Relationships
    snapshot: Mapped["Snapshot"] = relationship("Snapshot", back_populates="annotations")
    snapshot_path: Mapped[Optional["SnapshotPath"]] = relationship(
        "SnapshotPath", back_populates="annotations"
    )

    def __repr__(self) -> str:
        return f"<Annotation(type={self.annotation_type}, snapshot_id={self.snapshot_id})>"
