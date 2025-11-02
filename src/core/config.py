"""
Configuration management for Claude Config version control system.

Uses Pydantic for validation and python-dotenv for environment variables.
"""

import os
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


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


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get application settings singleton.

    Returns:
        Settings instance
    """
    global _settings

    if _settings is None:
        _settings = Settings()

    return _settings


def reload_settings() -> Settings:
    """
    Reload settings from environment.

    Useful for testing or when environment changes.

    Returns:
        New Settings instance
    """
    global _settings
    _settings = Settings()
    return _settings
