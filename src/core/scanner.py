"""
Core snapshot system for Claude Config version control.

Handles:
- Scanning Claude configuration paths
- Content hashing and deduplication
- Snapshot creation with full metadata
- Change detection between snapshots
"""

import hashlib
import json
import logging
import os
import platform
import socket
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models import (
    FileContent,
    Snapshot,
    SnapshotEnvVar,
    SnapshotPath,
    SnapshotChange,
)
from src.core.path_loader import load_path_definitions

logger = logging.getLogger(__name__)


class PathScanner:
    """
    Scans Claude configuration paths and creates versioned snapshots.

    Features:
    - Complete path scanning (17 locations across 7 categories)
    - SHA256 content hashing for deduplication
    - Automatic change detection
    - Metadata capture (timestamps, sizes, permissions)
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize scanner with database session.

        Args:
            session: Active database session for storing results
        """
        self.session = session

    def get_path_definitions(self) -> list[dict[str, Any]]:
        """
        Get all Claude configuration path definitions from configuration.

        Returns:
            List of path definitions with category, name, template, and resolved path
        """
        try:
            # Load path definitions from config/paths.yaml
            path_defs = load_path_definitions()
            logger.debug(
                f"Loaded {len(path_defs)} path definitions from configuration")
            return path_defs
        except Exception as e:
            logger.error(
                f"Failed to load path definitions from configuration: {e}")
            logger.warning("Falling back to hardcoded path definitions")
            # Fallback to hardcoded paths if config loading fails
            return self._get_fallback_path_definitions()

    def _get_fallback_path_definitions(self) -> list[dict[str, str]]:
        """
        Fallback path definitions if configuration file cannot be loaded.

        This ensures the scanner can still function if the config file is missing
        or invalid, using the original hardcoded definitions.

        Returns:
            List of fallback path definitions
        """
        # Expand environment variables
        userprofile = Path(os.path.expandvars("%USERPROFILE%"))
        appdata = Path(os.path.expandvars("%APPDATA%"))
        programdata = Path(os.path.expandvars("%ProgramData%"))

        return [
            # 1. Settings Files (5 locations)
            {
                "category": "Settings Files",
                "name": "User Settings",
                "template": "%USERPROFILE%\\.claude\\settings.json",
                "path": str(userprofile / ".claude" / "settings.json"),
            },
            {
                "category": "Settings Files",
                "name": "Project Settings (Shared)",
                "template": ".claude\\settings.json",
                "path": ".claude\\settings.json",  # Relative to current directory
            },
            {
                "category": "Settings Files",
                "name": "Project Settings (Local)",
                "template": ".claude\\settings.local.json",
                "path": ".claude\\settings.local.json",
            },
            {
                "category": "Settings Files",
                "name": "Enterprise Managed Settings",
                "template": "%ProgramData%\\ClaudeCode\\managed-settings.json",
                "path": str(programdata / "ClaudeCode" / "managed-settings.json"),
            },
            {
                "category": "Settings Files",
                "name": "Original Claude Code Config",
                "template": "%USERPROFILE%\\.claude.json",
                "path": str(userprofile / ".claude.json"),
            },
            # 2. Memory Files (CLAUDE.md) (3 locations)
            {
                "category": "Memory Files (CLAUDE.md)",
                "name": "User Memory",
                "template": "%USERPROFILE%\\.claude\\CLAUDE.md",
                "path": str(userprofile / ".claude" / "CLAUDE.md"),
            },
            {
                "category": "Memory Files (CLAUDE.md)",
                "name": "Project Memory",
                "template": ".claude\\CLAUDE.md",
                "path": ".claude\\CLAUDE.md",
            },
            {
                "category": "Memory Files (CLAUDE.md)",
                "name": "Enterprise Memory",
                "template": "%ProgramData%\\ClaudeCode\\CLAUDE.md",
                "path": str(programdata / "ClaudeCode" / "CLAUDE.md"),
            },
            # 3. Subagents (2 locations)
            {
                "category": "Subagents",
                "name": "User Subagents",
                "template": "%USERPROFILE%\\.claude\\subagents",
                "path": str(userprofile / ".claude" / "subagents"),
            },
            {
                "category": "Subagents",
                "name": "Project Subagents",
                "template": ".claude\\subagents",
                "path": ".claude\\subagents",
            },
            # 4. Claude Desktop (1 location)
            {
                "category": "Claude Desktop",
                "name": "Claude Desktop Config",
                "template": "%APPDATA%\\Claude\\claude_desktop_config.json",
                "path": str(appdata / "Claude" / "claude_desktop_config.json"),
            },
            # 5. Slash Commands (2 locations)
            {
                "category": "Slash Commands",
                "name": "User Commands",
                "template": "%USERPROFILE%\\.claude\\commands",
                "path": str(userprofile / ".claude" / "commands"),
            },
            {
                "category": "Slash Commands",
                "name": "Project Commands",
                "template": ".claude\\commands",
                "path": ".claude\\commands",
            },
            # 6. MCP Servers (3 locations)
            {
                "category": "MCP Servers",
                "name": "Claude Desktop MCP Config",
                "template": "%APPDATA%\\Claude\\claude_desktop_config.json",
                "path": str(appdata / "Claude" / "claude_desktop_config.json"),
            },
            {
                "category": "MCP Servers",
                "name": "User MCP Config",
                "template": "%USERPROFILE%\\.claude\\mcp.json",
                "path": str(userprofile / ".claude" / "mcp.json"),
            },
            {
                "category": "MCP Servers",
                "name": "Project MCP Config",
                "template": ".claude\\mcp.json",
                "path": ".claude\\mcp.json",
            },
            # 7. Logs (1 location)
            {
                "category": "Logs",
                "name": "Claude Desktop Logs",
                "template": "%APPDATA%\\Claude\\logs",
                "path": str(appdata / "Claude" / "logs"),
            },
        ]

    async def create_snapshot(
        self,
        trigger_type: str = "manual",
        triggered_by: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Snapshot:
        """
        Create a new snapshot of all Claude configuration paths.

        Args:
            trigger_type: How snapshot was triggered ('manual', 'scheduled', 'api', 'cli')
            triggered_by: Username or system that triggered the scan
            notes: Optional notes about this snapshot

        Returns:
            Created Snapshot object
        """
        logger.info(
            f"Creating snapshot (trigger={trigger_type}, by={triggered_by})")

        # Collect system context
        os_type = platform.system()
        os_version = platform.version()
        hostname = socket.gethostname()
        username = os.getenv("USERNAME") or os.getenv("USER")
        working_dir = os.getcwd()

        # Get path definitions
        path_defs = self.get_path_definitions()

        # Scan all paths
        scanned_paths: list[SnapshotPath] = []
        files_found = 0
        directories_found = 0
        total_size = 0

        for path_def in path_defs:
            path_obj = await self._scan_path(path_def)
            scanned_paths.append(path_obj)

            if path_obj.exists:
                if path_obj.type == "file":
                    files_found += 1
                    if path_obj.size_bytes:
                        total_size += path_obj.size_bytes
                elif path_obj.type == "directory":
                    directories_found += 1

        # Compute snapshot hash (hash of all content hashes)
        content_hashes = [
            p.content_hash for p in scanned_paths if p.content_hash is not None
        ]
        snapshot_hash_input = "|".join(sorted(content_hashes))
        snapshot_hash = hashlib.sha256(
            snapshot_hash_input.encode()).hexdigest()

        # Create snapshot object
        snapshot = Snapshot(
            snapshot_hash=snapshot_hash,
            trigger_type=trigger_type,
            triggered_by=triggered_by,
            notes=notes,
            os_type=os_type,
            os_version=os_version,
            hostname=hostname,
            username=username,
            working_directory=working_dir,
            total_locations=len(path_defs),
            files_found=files_found,
            directories_found=directories_found,
            total_size_bytes=total_size,
            is_baseline=False,
        )

        # Add to session
        self.session.add(snapshot)
        await self.session.flush()  # Get snapshot ID

        # Store environment variables
        env_vars = [
            SnapshotEnvVar(
                snapshot_id=snapshot.id,
                placeholder="%USERPROFILE%",
                resolved_path=str(Path(os.path.expandvars("%USERPROFILE%"))),
            ),
            SnapshotEnvVar(
                snapshot_id=snapshot.id,
                placeholder="%APPDATA%",
                resolved_path=str(Path(os.path.expandvars("%APPDATA%"))),
            ),
            SnapshotEnvVar(
                snapshot_id=snapshot.id,
                placeholder="%ProgramData%",
                resolved_path=str(Path(os.path.expandvars("%ProgramData%"))),
            ),
        ]
        self.session.add_all(env_vars)

        # Update scanned paths with snapshot ID and add annotations
        for path_obj in scanned_paths:
            path_obj.snapshot_id = snapshot.id
            self.session.add(path_obj)

            # Add any annotations created during scanning (e.g., MCP logs)
            if hasattr(path_obj, "_annotations"):
                for annotation in path_obj._annotations:
                    annotation.snapshot_id = snapshot.id
                    # snapshot_path_id will be set after flush

        # Flush to get IDs for paths
        await self.session.flush()

        # Now update annotation snapshot_path_id references
        for path_obj in scanned_paths:
            if hasattr(path_obj, "_annotations"):
                for annotation in path_obj._annotations:
                    annotation.snapshot_path_id = path_obj.id
                    self.session.add(annotation)

        # Detect changes from previous snapshot
        await self._detect_changes(snapshot)

        # Commit transaction
        await self.session.commit()

        logger.info(
            f"Snapshot created: id={snapshot.id}, hash={snapshot_hash[:8]}..., "
            f"files={files_found}, dirs={directories_found}, size={total_size}"
        )

        return snapshot

    async def _scan_path(self, path_def: dict[str, str]) -> SnapshotPath:
        """
        Scan a single path and create SnapshotPath object.

        Args:
            path_def: Path definition with category, name, template, and path

        Returns:
            SnapshotPath object with metadata and content
        """
        path = Path(path_def["path"])
        snapshot_path = SnapshotPath(
            snapshot_id=0,  # Will be set later
            category=path_def["category"],
            name=path_def["name"],
            path_template=path_def["template"],
            resolved_path=str(path),
            exists=False,
        )

        try:
            if path.exists():
                snapshot_path.exists = True

                if path.is_file():
                    snapshot_path.type = "file"
                    stat = path.stat()
                    snapshot_path.size_bytes = stat.st_size
                    snapshot_path.modified_time = datetime.fromtimestamp(
                        stat.st_mtime)
                    snapshot_path.created_time = datetime.fromtimestamp(
                        stat.st_ctime)
                    snapshot_path.accessed_time = datetime.fromtimestamp(
                        stat.st_atime)

                    # Read and hash content
                    content = path.read_bytes()
                    content_hash = hashlib.sha256(content).hexdigest()
                    snapshot_path.content_hash = content_hash

                    # Get or create FileContent (deduplication)
                    file_content = await self._get_or_create_content(
                        content_hash, content, path
                    )
                    snapshot_path.content_id = file_content.id

                elif path.is_dir():
                    snapshot_path.type = "directory"
                    items = list(path.iterdir())
                    snapshot_path.item_count = len(items)

                    # Special handling for logs directory: enumerate MCP log files
                    if self._should_enumerate_logs(path_def):
                        await self._enumerate_mcp_logs(path, snapshot_path, path_def)

        except Exception as e:
            snapshot_path.error_message = str(e)
            logger.warning(f"Error scanning {path}: {e}")

        return snapshot_path

    async def _get_or_create_content(
        self, content_hash: str, content: bytes, path: Path
    ) -> FileContent:
        """
        Get existing FileContent or create new one (deduplication).

        Args:
            content_hash: SHA256 hash of content
            content: File content bytes
            path: Path to the file

        Returns:
            FileContent object
        """
        # Check if content already exists
        stmt = select(FileContent).where(
            FileContent.content_hash == content_hash)
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            # Increment reference count
            existing.reference_count += 1
            return existing

        # Create new content
        # Determine content type
        content_type = "binary"
        content_text = None
        content_binary = None

        try:
            text = content.decode("utf-8")
            content_text = text
            if path.suffix == ".json":
                content_type = "json"
            elif path.suffix == ".md":
                content_type = "markdown"
            else:
                content_type = "text"
        except UnicodeDecodeError:
            content_binary = content
            content_type = "binary"

        file_content = FileContent(
            content_hash=content_hash,
            content_text=content_text,
            content_binary=content_binary,
            content_type=content_type,
            size_bytes=len(content),
            compression="none",
            reference_count=1,
        )

        self.session.add(file_content)
        await self.session.flush()  # Get ID

        return file_content

    async def _detect_changes(self, snapshot: Snapshot) -> None:
        """
        Detect changes from previous snapshot.

        Args:
            snapshot: Current snapshot to compare
        """
        # Get previous snapshot
        stmt = (
            select(Snapshot)
            .where(Snapshot.id != snapshot.id)
            .order_by(Snapshot.snapshot_time.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        previous = result.scalar_one_or_none()

        if not previous:
            logger.info("No previous snapshot for comparison")
            snapshot.is_baseline = True
            return

        snapshot.parent_snapshot_id = previous.id

        # Load paths for both snapshots
        stmt = select(SnapshotPath).where(
            SnapshotPath.snapshot_id == snapshot.id)
        result = await self.session.execute(stmt)
        current_paths = {p.path_template: p for p in result.scalars()}

        stmt = select(SnapshotPath).where(
            SnapshotPath.snapshot_id == previous.id)
        result = await self.session.execute(stmt)
        previous_paths = {p.path_template: p for p in result.scalars()}

        # Detect changes
        changes: list[SnapshotChange] = []
        change_count = 0

        # Check for added, modified, unchanged
        for template, current_path in current_paths.items():
            if template not in previous_paths:
                # Added
                changes.append(
                    SnapshotChange(
                        snapshot_id=snapshot.id,
                        previous_snapshot_id=previous.id,
                        path_template=template,
                        change_type="added",
                        new_content_hash=current_path.content_hash,
                        new_size_bytes=current_path.size_bytes,
                        new_modified_time=current_path.modified_time,
                    )
                )
                change_count += 1
            else:
                prev_path = previous_paths[template]
                if current_path.content_hash != prev_path.content_hash:
                    # Modified
                    changes.append(
                        SnapshotChange(
                            snapshot_id=snapshot.id,
                            previous_snapshot_id=previous.id,
                            path_template=template,
                            change_type="modified",
                            old_content_hash=prev_path.content_hash,
                            new_content_hash=current_path.content_hash,
                            old_size_bytes=prev_path.size_bytes,
                            new_size_bytes=current_path.size_bytes,
                            old_modified_time=prev_path.modified_time,
                            new_modified_time=current_path.modified_time,
                        )
                    )
                    change_count += 1
                # else: unchanged

        # Check for deleted
        for template, prev_path in previous_paths.items():
            if template not in current_paths:
                changes.append(
                    SnapshotChange(
                        snapshot_id=snapshot.id,
                        previous_snapshot_id=previous.id,
                        path_template=template,
                        change_type="deleted",
                        old_content_hash=prev_path.content_hash,
                        old_size_bytes=prev_path.size_bytes,
                        old_modified_time=prev_path.modified_time,
                    )
                )
                change_count += 1

        snapshot.changed_from_previous = change_count
        self.session.add_all(changes)

        logger.info(
            f"Detected {change_count} changes from snapshot {previous.id}"
        )

    def _should_enumerate_logs(self, path_def: dict[str, Any]) -> bool:
        """
        Check if log enumeration should be performed for this path.

        Args:
            path_def: Path definition

        Returns:
            True if logs should be enumerated
        """
        # Check if path has enumerate_logs option
        options = path_def.get("options", {})
        if options.get("enumerate_logs"):
            return True

        # Also enumerate for paths named "Claude Desktop Logs" for backward compatibility
        if path_def.get("name") == "Claude Desktop Logs":
            return True

        return False

    async def _enumerate_mcp_logs(
        self,
        path: Path,
        snapshot_path: SnapshotPath,
        path_def: dict[str, Any],
    ) -> None:
        """
        Enumerate MCP log files in a logs directory.

        Finds all files matching the pattern (default: mcp*.log) and stores
        information about them in an annotation.

        Args:
            path: Path to logs directory
            snapshot_path: SnapshotPath object being created
            path_def: Path definition with options
        """
        try:
            # Get log pattern from options, default to "mcp*.log"
            options = path_def.get("options", {})
            log_pattern = options.get("log_pattern", "mcp*.log")

            # Find matching log files
            log_files = list(path.glob(log_pattern))

            if log_files:
                # Create annotation with log file list
                from src.core.models import Annotation

                # Format log file information
                log_info = {
                    "log_count": len(log_files),
                    "log_files": [
                        {
                            "name": log.name,
                            "size": log.stat().st_size,
                            "modified": datetime.fromtimestamp(log.stat().st_mtime).isoformat(),
                        }
                        for log in log_files[:50]  # Limit to first 50
                    ],
                }

                if len(log_files) > 50:
                    log_info["truncated"] = True
                    log_info["total_logs"] = len(log_files)

                # Store as JSON in annotation
                annotation = Annotation(
                    snapshot_id=snapshot_path.snapshot_id,
                    snapshot_path_id=snapshot_path.id,
                    annotation_text=json.dumps(log_info, indent=2),
                    annotation_type="mcp_logs",
                    created_by="scanner",
                )

                # Note: Annotation will be added to session when snapshot_path is added
                # Store reference in snapshot_path for now
                if not hasattr(snapshot_path, "_annotations"):
                    snapshot_path._annotations = []
                snapshot_path._annotations.append(annotation)

                logger.info(
                    f"Enumerated {len(log_files)} MCP log files in {path}"
                )
        except Exception as e:
            logger.warning(f"Failed to enumerate MCP logs in {path}: {e}")
