"""
Configuration management for Claude Config version control system.

Uses Pydantic for validation, YAML for configuration files,
and python-dotenv for environment variables.

Configuration loading order (lowest to highest priority):
1. YAML configuration file (config/{environment}.yaml)
2. Environment variables  
3. Explicit overrides

For YAML-based configuration, see config_loader.py
"""

import logging
import os
from pathlib import Path
from typing import Any, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.core.config_loader import load_config

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Values can be set via:
    1. Environment variables
    2. .env file
    3. Default values
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application Environment
    environment: str = Field(
        default="development",
        description="Application environment (development, production, testing)",
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode (enables verbose logging and development features)",
    )

    # Database Configuration
    database_url: str = Field(
        default="sqlite+aiosqlite:///data/claude_config.db",
        description="SQLAlchemy database URL",
    )

    # API Server Configuration
    api_host: str = Field(
        default="127.0.0.1",
        description="API server host",
    )
    api_port: int = Field(
        default=8765,
        description="API server port",
    )
    api_reload: bool = Field(
        default=True,
        description="Auto-reload on code changes (dev only)",
    )

    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    log_file: Optional[str] = Field(
        default="logs/app.log",
        description="Path to log file",
    )
    log_max_bytes: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        description="Maximum size of each log file before rotation",
    )
    log_backup_count: int = Field(
        default=5,
        description="Number of backup log files to keep",
    )

    # Snapshot Configuration
    snapshot_retention_days: int = Field(
        default=90,
        description="How long to keep snapshots (0 = forever)",
    )
    snapshot_auto_compress: bool = Field(
        default=True,
        description="Auto-compress large files",
    )
    snapshot_compress_threshold_mb: int = Field(
        default=1,
        description="Compress files larger than this (MB)",
    )

    # Security (optional)
    api_key: Optional[str] = Field(
        default=None,
        description="Optional API key for authentication",
    )
    cors_origins: str = Field(
        default="http://localhost:8765,http://127.0.0.1:8765",
        description="Allowed CORS origins (comma-separated)",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """Get CORS origins as a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment.lower() == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment.lower() == "production"

    @property
    def database_path(self) -> Optional[Path]:
        """Get database file path (if using SQLite)."""
        if "sqlite" in self.database_url:
            db_path = self.database_url.split("///")[-1]
            return Path(db_path)
        return None

    @classmethod
    def from_yaml(
        cls,
        environment: Optional[str] = None,
        config_file: Optional[Path] = None,
    ) -> "Settings":
        """
        Create Settings from YAML configuration file.

        Args:
            environment: Environment name (development, production, testing)
            config_file: Explicit config file path

        Returns:
            Settings instance with values from YAML and environment
        """
        # Load YAML configuration
        yaml_config = load_config(
            environment=environment, config_file=config_file)

        # Flatten nested config for Pydantic
        flat_config = cls._flatten_config(yaml_config)

        # Create Settings instance
        # Environment variables will override YAML values due to Pydantic's behavior
        return cls(**flat_config)

    @staticmethod
    def _flatten_config(config: dict[str, Any], prefix: str = "") -> dict[str, Any]:
        """
        Flatten nested configuration dictionary for Pydantic.

        Args:
            config: Nested configuration dictionary
            prefix: Key prefix for recursion

        Returns:
            Flattened dictionary
        """
        flat = {}

        for key, value in config.items():
            full_key = f"{prefix}{key}" if prefix else key

            if isinstance(value, dict) and key not in ["options", "dev_options", "prod_options", "test_options"]:
                # Recursively flatten nested dicts (except option dicts)
                flat.update(Settings._flatten_config(value, f"{full_key}_"))
            else:
                flat[full_key] = value

        return flat

    def to_yaml(self, file_path: Path) -> None:
        """
        Export settings to YAML file.

        Args:
            file_path: Path to write YAML file
        """
        import yaml

        # Convert settings to dictionary
        config_dict = {
            "environment": self.environment,
            "database": {
                "url": self.database_url,
            },
            "api": {
                "host": self.api_host,
                "port": self.api_port,
                "reload": self.api_reload,
            },
            "logging": {
                "level": self.log_level,
                "file": self.log_file,
                "max_bytes": self.log_max_bytes,
                "backup_count": self.log_backup_count,
            },
            "snapshot": {
                "retention_days": self.snapshot_retention_days,
                "auto_compress": self.snapshot_auto_compress,
                "compress_threshold_mb": self.snapshot_compress_threshold_mb,
            },
            "security": {
                "api_key": self.api_key,
                "cors_origins": self.cors_origins_list,
            },
        }

        # Write to file
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Settings exported to {file_path}")

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(
                f"Invalid log level: {v}. Must be one of {valid_levels}"
            )
        return v.upper()

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment."""
        valid_envs = ["development", "production", "testing"]
        if v.lower() not in valid_envs:
            raise ValueError(
                f"Invalid environment: {v}. Must be one of {valid_envs}"
            )
        return v.lower()


# Global settings instance
_settings: Optional[Settings] = None


def get_settings(
    use_yaml: bool = True,
    environment: Optional[str] = None,
    config_file: Optional[Path] = None,
) -> Settings:
    """
    Get application settings singleton.

    Args:
        use_yaml: Whether to load from YAML config files
        environment: Environment name (only used if use_yaml=True)
        config_file: Explicit config file path (only used if use_yaml=True)

    Returns:
        Settings instance
    """
    global _settings

    if _settings is None:
        if use_yaml:
            try:
                _settings = Settings.from_yaml(
                    environment=environment,
                    config_file=config_file,
                )
                logger.info(
                    f"Settings loaded from YAML for environment: {_settings.environment}")
            except Exception as e:
                logger.warning(f"Failed to load YAML configuration: {e}")
                logger.info("Falling back to environment variables only")
                _settings = Settings()
        else:
            _settings = Settings()

    return _settings


def reload_settings(
    use_yaml: bool = True,
    environment: Optional[str] = None,
    config_file: Optional[Path] = None,
) -> Settings:
    """
    Reload settings from environment.

    Useful for testing or when environment changes.

    Args:
        use_yaml: Whether to load from YAML config files
        environment: Environment name (only used if use_yaml=True)
        config_file: Explicit config file path (only used if use_yaml=True)

    Returns:
        New Settings instance
    """
    global _settings

    if use_yaml:
        try:
            _settings = Settings.from_yaml(
                environment=environment,
                config_file=config_file,
            )
        except Exception as e:
            logger.error(f"Failed to reload YAML configuration: {e}")
            _settings = Settings()
    else:
        _settings = Settings()

    return _settings
