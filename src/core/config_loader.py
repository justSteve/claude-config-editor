"""
Configuration loader for Claude Config version control system.

Handles loading and merging configuration from multiple sources:
1. Base configuration (config/base.yaml or environment-specific)
2. Environment-specific configuration (config/{environment}.yaml)
3. Environment variables
4. Command-line overrides (if applicable)
"""

import logging
import os
from pathlib import Path
from typing import Any, Optional

import yaml

logger = logging.getLogger(__name__)


class ConfigLoader:
    """
    Loads and merges configuration from multiple sources.
    
    Configuration precedence (lowest to highest):
    1. Base/environment-specific YAML file
    2. Environment variables
    3. Explicit overrides
    """
    
    def __init__(self, config_dir: Optional[Path] = None) -> None:
        """
        Initialize configuration loader.
        
        Args:
            config_dir: Path to config directory (default: config/)
        """
        if config_dir is None:
            config_dir = Path(__file__).parent.parent.parent / "config"
        
        self.config_dir = config_dir
        self.config: dict[str, Any] = {}
    
    def load(
        self,
        environment: Optional[str] = None,
        config_file: Optional[Path] = None,
    ) -> dict[str, Any]:
        """
        Load configuration from file and environment.
        
        Args:
            environment: Environment name (development, production, testing)
            config_file: Explicit config file path (overrides environment)
            
        Returns:
            Merged configuration dictionary
        """
        # Determine environment
        if environment is None:
            environment = os.getenv("ENVIRONMENT", "development")
        
        # Load from YAML file
        if config_file:
            self.config = self._load_yaml(config_file)
        else:
            # Load environment-specific config
            env_config_path = self.config_dir / f"{environment}.yaml"
            if env_config_path.exists():
                self.config = self._load_yaml(env_config_path)
                logger.info(f"Loaded configuration from {env_config_path}")
            else:
                logger.warning(
                    f"Configuration file not found: {env_config_path}, "
                    f"using defaults"
                )
                self.config = {}
        
        # Merge with environment variables
        self._merge_env_vars()
        
        return self.config
    
    def _load_yaml(self, file_path: Path) -> dict[str, Any]:
        """
        Load configuration from YAML file.
        
        Args:
            file_path: Path to YAML file
            
        Returns:
            Configuration dictionary
            
        Raises:
            FileNotFoundError: If file doesn't exist
            yaml.YAMLError: If file is invalid YAML
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        with open(file_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        
        if not isinstance(config, dict):
            raise ValueError(f"Invalid configuration file: {file_path}")
        
        return config
    
    def _merge_env_vars(self) -> None:
        """
        Merge environment variables into configuration.
        
        Supports nested keys using __ separator:
        DATABASE__URL -> database.url
        API__HOST -> api.host
        """
        # Environment variable mappings
        env_mappings = {
            # Top-level
            "ENVIRONMENT": "environment",
            
            # Database
            "DATABASE_URL": "database.url",
            "DATABASE_ECHO": "database.echo",
            
            # API
            "API_HOST": "api.host",
            "API_PORT": "api.port",
            "API_RELOAD": "api.reload",
            "API_DEBUG": "api.debug",
            
            # Logging
            "LOG_LEVEL": "logging.level",
            "LOG_FILE": "logging.file",
            "LOG_MAX_BYTES": "logging.max_bytes",
            "LOG_BACKUP_COUNT": "logging.backup_count",
            "LOG_CONSOLE_OUTPUT": "logging.console_output",
            
            # Snapshot
            "SNAPSHOT_RETENTION_DAYS": "snapshot.retention_days",
            "SNAPSHOT_AUTO_COMPRESS": "snapshot.auto_compress",
            "SNAPSHOT_COMPRESS_THRESHOLD_MB": "snapshot.compress_threshold_mb",
            
            # Security
            "API_KEY": "security.api_key",
            "CORS_ORIGINS": "security.cors_origins",
        }
        
        for env_var, config_key in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                self._set_nested_key(config_key, self._convert_value(value))
    
    def _set_nested_key(self, key: str, value: Any) -> None:
        """
        Set a nested key in configuration.
        
        Args:
            key: Dot-separated key (e.g., "database.url")
            value: Value to set
        """
        parts = key.split(".")
        current = self.config
        
        # Navigate to parent
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        # Set value
        current[parts[-1]] = value
    
    def _convert_value(self, value: str) -> Any:
        """
        Convert string value to appropriate type.
        
        Args:
            value: String value from environment variable
            
        Returns:
            Converted value
        """
        # Boolean conversion
        if value.lower() in ("true", "yes", "1", "on"):
            return True
        if value.lower() in ("false", "no", "0", "off"):
            return False
        
        # Integer conversion
        try:
            return int(value)
        except ValueError:
            pass
        
        # Float conversion
        try:
            return float(value)
        except ValueError:
            pass
        
        # List conversion (comma-separated)
        if "," in value:
            return [item.strip() for item in value.split(",")]
        
        # String
        return value
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.
        
        Supports nested keys using dot notation.
        
        Args:
            key: Configuration key (e.g., "database.url")
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        parts = key.split(".")
        current = self.config
        
        for part in parts:
            if not isinstance(current, dict) or part not in current:
                return default
            current = current[part]
        
        return current
    
    def validate(self) -> list[str]:
        """
        Validate configuration for required fields and valid values.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check required fields
        required_fields = [
            "environment",
            "database.url",
            "api.host",
            "api.port",
            "logging.level",
        ]
        
        for field in required_fields:
            if self.get(field) is None:
                errors.append(f"Required configuration missing: {field}")
        
        # Validate environment
        valid_environments = ["development", "production", "testing"]
        env = self.get("environment")
        if env not in valid_environments:
            errors.append(
                f"Invalid environment: {env}. "
                f"Must be one of {valid_environments}"
            )
        
        # Validate log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        log_level = self.get("logging.level")
        if log_level and log_level.upper() not in valid_log_levels:
            errors.append(
                f"Invalid log level: {log_level}. "
                f"Must be one of {valid_log_levels}"
            )
        
        # Validate API port
        api_port = self.get("api.port")
        if api_port is not None:
            try:
                port = int(api_port)
                if port < 0 or port > 65535:
                    errors.append(f"Invalid API port: {port}. Must be 0-65535")
            except (ValueError, TypeError):
                errors.append(f"Invalid API port: {api_port}. Must be an integer")
        
        return errors
    
    def to_dict(self) -> dict[str, Any]:
        """
        Get configuration as dictionary.
        
        Returns:
            Configuration dictionary
        """
        return self.config.copy()


# Global configuration loader instance
_config_loader: Optional[ConfigLoader] = None


def get_config_loader(config_dir: Optional[Path] = None) -> ConfigLoader:
    """
    Get the global configuration loader instance.
    
    Args:
        config_dir: Path to config directory (only used on first call)
        
    Returns:
        ConfigLoader instance
    """
    global _config_loader
    
    if _config_loader is None:
        _config_loader = ConfigLoader(config_dir)
    
    return _config_loader


def load_config(
    environment: Optional[str] = None,
    config_file: Optional[Path] = None,
    config_dir: Optional[Path] = None,
) -> dict[str, Any]:
    """
    Convenience function to load configuration.
    
    Args:
        environment: Environment name
        config_file: Explicit config file path
        config_dir: Config directory path
        
    Returns:
        Configuration dictionary
    """
    loader = get_config_loader(config_dir)
    return loader.load(environment=environment, config_file=config_file)

