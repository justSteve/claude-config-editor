"""
Path definition loader for Claude Config scanner.

Loads path definitions from YAML configuration files and expands
environment variables based on the platform.
"""

import logging
import os
import platform
from pathlib import Path
from typing import Any, Optional

import yaml

logger = logging.getLogger(__name__)


class PathDefinition:
    """
    Represents a single path definition from configuration.

    Attributes:
        category: Logical grouping (e.g., "Settings Files")
        name: Human-readable identifier
        template: Path template with environment variables
        description: Description of this path
        enabled: Whether this path should be scanned
        options: Additional scanning options
        resolved_path: Template with environment variables expanded
    """

    def __init__(
        self,
        category: str,
        name: str,
        template: str,
        description: str = "",
        enabled: bool = True,
        options: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Initialize path definition.

        Args:
            category: Path category
            name: Path name
            template: Path template with env vars
            description: Optional description
            enabled: Whether to scan this path
            options: Additional options
        """
        self.category = category
        self.name = name
        self.template = template
        self.description = description
        self.enabled = enabled
        self.options = options or {}
        self.resolved_path: Optional[str] = None

    def resolve(self, platform_mappings: Optional[dict[str, str]] = None) -> str:
        """
        Resolve environment variables in path template.

        Args:
            platform_mappings: Platform-specific env var mappings

        Returns:
            Resolved path with environment variables expanded
        """
        if self.resolved_path is not None:
            return self.resolved_path

        # Start with template
        path = self.template

        # Apply platform-specific mappings first if provided
        if platform_mappings:
            for env_var, platform_path in platform_mappings.items():
                if env_var in path:
                    # Expand ~ in platform_path
                    expanded = os.path.expanduser(platform_path)
                    path = path.replace(env_var, expanded)

        # Expand remaining environment variables
        # Handle both Windows (%VAR%) and Unix ($VAR or ${VAR}) style
        path = os.path.expandvars(path)
        path = os.path.expanduser(path)

        # Normalize path separators for current platform
        path = str(Path(path))

        self.resolved_path = path
        return path

    def to_dict(self) -> dict[str, Any]:
        """
        Convert to dictionary format compatible with scanner.

        Returns:
            Dictionary with category, name, template, and path
        """
        return {
            "category": self.category,
            "name": self.name,
            "template": self.template,
            "path": self.resolved_path or self.resolve(),
            "description": self.description,
            "options": self.options,
        }

    def __repr__(self) -> str:
        return f"<PathDefinition(category={self.category}, name={self.name})>"


class PathLoader:
    """
    Loads and manages path definitions from YAML configuration.

    Features:
    - Load from YAML file
    - Platform-specific environment variable mapping
    - Path filtering by category or enabled status
    - Environment variable expansion
    """

    def __init__(self, config_path: Optional[Path] = None) -> None:
        """
        Initialize path loader.

        Args:
            config_path: Path to YAML config file (default: config/paths.yaml)
        """
        if config_path is None:
            # Default to config/paths.yaml in project root
            config_path = Path(__file__).parent.parent.parent / \
                "config" / "paths.yaml"

        self.config_path = config_path
        self.paths: list[PathDefinition] = []
        self.platform_mappings: dict[str, dict[str, str]] = {}
        self.options: dict[str, Any] = {}
        self._loaded = False

    def load(self) -> None:
        """
        Load path definitions from YAML configuration file.

        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If config file is invalid YAML
            ValueError: If config file has invalid structure
        """
        logger.debug(f"Attempting to load path configuration from {self.config_path}")
        
        if not self.config_path.exists():
            logger.error(f"Path configuration file not found: {self.config_path}")
            raise FileNotFoundError(
                f"Path configuration file not found: {self.config_path}")

        logger.info(f"Loading path definitions from {self.config_path}")

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in path configuration: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Failed to read path configuration file: {e}", exc_info=True)
            raise

        if not isinstance(config, dict):
            logger.error("Invalid path configuration: root must be a dictionary")
            raise ValueError(
                "Invalid path configuration: root must be a dictionary")

        # Load paths
        paths_data = config.get("paths", [])
        if not isinstance(paths_data, list):
            logger.error("Invalid path configuration: 'paths' must be a list")
            raise ValueError(
                "Invalid path configuration: 'paths' must be a list")

        logger.debug(f"Found {len(paths_data)} path definitions in configuration")

        for path_data in paths_data:
            if not isinstance(path_data, dict):
                logger.warning(
                    f"Skipping invalid path definition: {path_data}")
                continue

            try:
                path_def = PathDefinition(
                    category=path_data.get("category", ""),
                    name=path_data.get("name", ""),
                    template=path_data.get("template", ""),
                    description=path_data.get("description", ""),
                    enabled=path_data.get("enabled", True),
                    options=path_data.get("options", {}),
                )
                self.paths.append(path_def)
            except Exception as e:
                logger.error(
                    f"Error loading path definition {path_data.get('name')}: {e}")

        # Load platform mappings
        self.platform_mappings = config.get("platform_mappings", {})

        # Load options
        self.options = config.get("options", {})

        self._loaded = True
        
        # Log statistics
        enabled_count = len([p for p in self.paths if p.enabled])
        logger.info(
            f"Loaded {len(self.paths)} path definitions "
            f"({enabled_count} enabled, {len(self.paths) - enabled_count} disabled)"
        )
        logger.debug(f"Platform mappings configured for: {list(self.platform_mappings.keys())}")

    def get_paths(
        self,
        category: Optional[str] = None,
        enabled_only: bool = True,
    ) -> list[PathDefinition]:
        """
        Get path definitions, optionally filtered.

        Args:
            category: Filter by category (None for all)
            enabled_only: Only return enabled paths

        Returns:
            List of path definitions
        """
        if not self._loaded:
            self.load()

        paths = self.paths

        # Filter by enabled status
        if enabled_only:
            paths = [p for p in paths if p.enabled]

        # Filter by category
        if category:
            paths = [p for p in paths if p.category == category]

        return paths

    def get_resolved_paths(
        self,
        category: Optional[str] = None,
        enabled_only: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Get resolved path definitions as dictionaries.

        Args:
            category: Filter by category (None for all)
            enabled_only: Only return enabled paths

        Returns:
            List of resolved path dictionaries
        """
        paths = self.get_paths(category=category, enabled_only=enabled_only)

        # Get platform-specific mappings
        current_platform = platform.system()
        platform_mapping = self.platform_mappings.get(current_platform, {})

        # Resolve and convert to dictionaries
        resolved = []
        for path_def in paths:
            path_def.resolve(platform_mapping)
            resolved.append(path_def.to_dict())

        return resolved

    def get_categories(self) -> list[str]:
        """
        Get list of all categories.

        Returns:
            List of unique category names
        """
        if not self._loaded:
            self.load()

        categories = set(p.category for p in self.paths)
        return sorted(categories)

    def get_option(self, key: str, default: Any = None) -> Any:
        """
        Get scanner option from configuration.

        Args:
            key: Option key
            default: Default value if not found

        Returns:
            Option value or default
        """
        if not self._loaded:
            self.load()

        return self.options.get(key, default)

    def reload(self) -> None:
        """Reload configuration from file."""
        self.paths = []
        self.platform_mappings = {}
        self.options = {}
        self._loaded = False
        self.load()


# Global path loader instance
_path_loader: Optional[PathLoader] = None


def get_path_loader(config_path: Optional[Path] = None) -> PathLoader:
    """
    Get the global path loader instance.

    Args:
        config_path: Path to config file (only used on first call)

    Returns:
        PathLoader instance
    """
    global _path_loader

    if _path_loader is None:
        _path_loader = PathLoader(config_path)

    return _path_loader


def load_path_definitions(
    config_path: Optional[Path] = None,
    category: Optional[str] = None,
    enabled_only: bool = True,
) -> list[dict[str, Any]]:
    """
    Convenience function to load path definitions.

    Args:
        config_path: Path to config file
        category: Filter by category
        enabled_only: Only return enabled paths

    Returns:
        List of resolved path dictionaries
    """
    loader = get_path_loader(config_path)
    return loader.get_resolved_paths(category=category, enabled_only=enabled_only)
