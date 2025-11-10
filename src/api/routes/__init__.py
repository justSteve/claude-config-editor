"""
API route handlers.

Organized by resource type (snapshots, paths, changes, etc.)
"""

from src.api.routes import snapshots

__all__ = [
    "snapshots",
]
