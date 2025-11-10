"""
API route handlers.

Organized by resource type (snapshots, paths, changes, etc.)
"""

from src.api.routes import snapshots, claude_config, paths

__all__ = [
    "snapshots",
    "claude_config",
    "paths",
]
