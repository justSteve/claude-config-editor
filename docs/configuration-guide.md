# Configuration Guide

## Overview

The Claude Config Editor uses a multi-layered configuration system that supports:
- Environment-specific YAML configuration files
- Environment variable overrides
- Pydantic validation
- Configuration merging

## Configuration Files

### Environment-Specific Configurations

Located in `config/` directory:

| File | Purpose | When to Use |
|------|---------|-------------|
| `development.yaml` | Development settings | Local development, verbose logging, hot-reload |
| `production.yaml` | Production settings | Production deployment, optimized performance |
| `testing.yaml` | Testing settings | Automated tests, in-memory database |
| `logging.yaml` | Logging configuration | Detailed logging setup for all environments |
| `paths.yaml` | Path definitions | Claude config paths to scan |

### Configuration Loading Order

Settings are loaded with this priority (lowest to highest):

1. **YAML Configuration File** (`config/{environment}.yaml`)
2. **Environment Variables** (override YAML values)
3. **Explicit Overrides** (programmatic overrides)

## Usage

### Basic Usage

```python
from src.core.config import get_settings

# Load settings (automatically detects environment from ENV variable or defaults to development)
settings = get_settings()

print(f"Environment: {settings.environment}")
print(f"Database URL: {settings.database_url}")
print(f"Log Level: {settings.log_level}")
```

### Specify Environment

```python
from src.core.config import get_settings

# Load production settings
settings = get_settings(environment="production")

# Or set via environment variable
# export ENVIRONMENT=production
settings = get_settings()
```

### Custom Configuration File

```python
from pathlib import Path
from src.core.config import get_settings

# Load from custom file
settings = get_settings(config_file=Path("config/custom.yaml"))
```

### Environment Variables Only

```python
from src.core.config import get_settings

# Skip YAML loading, use only environment variables
settings = get_settings(use_yaml=False)
```

## Configuration Structure

### Development Configuration

```yaml
# config/development.yaml
environment: development

database:
  url: "sqlite+aiosqlite:///data/claude_config.db"
  echo: true  # Log SQL statements

api:
  host: "127.0.0.1"
  port: 8765
  reload: true
  debug: true

logging:
  level: "DEBUG"
  file: "logs/app.log"
  max_bytes: 10485760  # 10MB
  backup_count: 5

snapshot:
  retention_days: 90
  auto_compress: false
  compress_threshold_mb: 1

security:
  api_key: null
  cors_origins:
    - "http://localhost:8765"
    - "http://127.0.0.1:8765"
```

### Production Configuration

```yaml
# config/production.yaml
environment: production

database:
  url: "sqlite+aiosqlite:///data/claude_config.db"
  echo: false  # Don't log SQL in production

api:
  host: "127.0.0.1"
  port: 8765
  reload: false
  debug: false

logging:
  level: "INFO"
  file: "logs/app.log"
  max_bytes: 52428800  # 50MB
  backup_count: 10

snapshot:
  retention_days: 180
  auto_compress: true
  compress_threshold_mb: 1

security:
  api_key: null  # Set via environment variable
  cors_origins:
    - "http://localhost:8765"
```

## Environment Variables

Environment variables override YAML configuration. Use the following format:

### Top-Level Settings

| Environment Variable | YAML Path | Example |
|---------------------|-----------|---------|
| `ENVIRONMENT` | `environment` | `development` |

### Database Settings

| Environment Variable | YAML Path | Example |
|---------------------|-----------|---------|
| `DATABASE_URL` | `database.url` | `sqlite+aiosqlite:///data/db.db` |
| `DATABASE_ECHO` | `database.echo` | `true` |

### API Settings

| Environment Variable | YAML Path | Example |
|---------------------|-----------|---------|
| `API_HOST` | `api.host` | `0.0.0.0` |
| `API_PORT` | `api.port` | `8000` |
| `API_RELOAD` | `api.reload` | `false` |
| `API_DEBUG` | `api.debug` | `false` |

### Logging Settings

| Environment Variable | YAML Path | Example |
|---------------------|-----------|---------|
| `LOG_LEVEL` | `logging.level` | `INFO` |
| `LOG_FILE` | `logging.file` | `logs/app.log` |
| `LOG_MAX_BYTES` | `logging.max_bytes` | `10485760` |
| `LOG_BACKUP_COUNT` | `logging.backup_count` | `5` |

### Snapshot Settings

| Environment Variable | YAML Path | Example |
|---------------------|-----------|---------|
| `SNAPSHOT_RETENTION_DAYS` | `snapshot.retention_days` | `90` |
| `SNAPSHOT_AUTO_COMPRESS` | `snapshot.auto_compress` | `true` |
| `SNAPSHOT_COMPRESS_THRESHOLD_MB` | `snapshot.compress_threshold_mb` | `1` |

### Security Settings

| Environment Variable | YAML Path | Example |
|---------------------|-----------|---------|
| `API_KEY` | `security.api_key` | `your-secret-key` |
| `CORS_ORIGINS` | `security.cors_origins` | `http://localhost:8765,http://127.0.0.1:8765` |

## Examples

### Example 1: Development Setup

```bash
# Set environment
export ENVIRONMENT=development

# Optional: Override specific settings
export LOG_LEVEL=DEBUG
export API_PORT=9000

# Run application
python -m src.cli.commands snapshot create
```

### Example 2: Production Deployment

```bash
# Set environment
export ENVIRONMENT=production

# Set sensitive values via environment variables
export API_KEY=your-production-api-key
export DATABASE_URL=sqlite+aiosqlite:///var/data/claude_config.db

# Run application
python -m src.cli.commands snapshot create
```

### Example 3: Testing

```bash
# Tests automatically use testing configuration
pytest

# Or explicitly set environment
export ENVIRONMENT=testing
python -m pytest
```

### Example 4: Custom Configuration

Create a custom configuration file:

```yaml
# config/staging.yaml
environment: staging

database:
  url: "sqlite+aiosqlite:///data/staging.db"
  
api:
  host: "0.0.0.0"
  port: 8765

logging:
  level: "INFO"
  file: "logs/staging.log"
```

Load it programmatically:

```python
from pathlib import Path
from src.core.config import get_settings

settings = get_settings(config_file=Path("config/staging.yaml"))
```

## Configuration Validation

Settings are automatically validated using Pydantic:

```python
from src.core.config import get_settings
from pydantic import ValidationError

try:
    settings = get_settings()
    print("Configuration valid!")
except ValidationError as e:
    print(f"Configuration errors: {e}")
```

### Validation Rules

- **environment**: Must be one of: `development`, `production`, `testing`
- **log_level**: Must be one of: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- **api_port**: Must be integer between 0-65535
- **database_url**: Required field
- **api_host**: Required field

## Exporting Configuration

Export current settings to YAML:

```python
from pathlib import Path
from src.core.config import get_settings

settings = get_settings()
settings.to_yaml(Path("config/exported.yaml"))
```

## Configuration Loader API

For more advanced use cases, use the `ConfigLoader` directly:

```python
from src.core.config_loader import ConfigLoader
from pathlib import Path

# Create loader
loader = ConfigLoader(config_dir=Path("config"))

# Load configuration
config = loader.load(environment="production")

# Access nested values
db_url = loader.get("database.url")
log_level = loader.get("logging.level", default="INFO")

# Validate configuration
errors = loader.validate()
if errors:
    print(f"Validation errors: {errors}")

# Get full configuration dictionary
config_dict = loader.to_dict()
```

## Best Practices

1. **Use environment-specific files**: Maintain separate configs for dev/prod/test
2. **Keep secrets in environment variables**: Don't commit sensitive data to YAML files
3. **Version control YAML files**: Track configuration changes in git
4. **Use .env for local overrides**: Create `.env` file for local development settings
5. **Validate on startup**: Check configuration is valid before running application
6. **Document custom settings**: Add comments to YAML files explaining non-obvious settings

## Troubleshooting

### Configuration Not Loading

**Problem**: Settings not loading from YAML file

**Solution**:
- Check `ENVIRONMENT` variable is set correctly
- Verify config file exists: `config/{environment}.yaml`
- Check file permissions
- Look for error messages in logs

### Environment Variables Not Working

**Problem**: Environment variables not overriding YAML values

**Solution**:
- Ensure variable names match exactly (case-sensitive)
- Check variable is exported: `export VAR=value`
- Verify get_settings() is called with `use_yaml=True`
- Try reloading: `reload_settings()`

### Validation Errors

**Problem**: Pydantic validation fails

**Solution**:
- Check all required fields are present
- Verify values match expected types (int, bool, string)
- Check enum values (environment, log_level)
- Review error message for specific field causing issue

### Configuration Changes Not Applied

**Problem**: Changes to YAML not reflected in application

**Solution**:
- Restart application (settings are cached)
- Or call `reload_settings()` to force reload
- For tests, use `reload_settings()` in setup/teardown

## Related Documentation

- [Path Configuration Guide](./scanner-comparison-analysis.md) - For `paths.yaml` configuration
- [Logging Guide](./LOGGING.md) - For detailed logging configuration
- [Deployment Guide](./DEPLOYMENT.md) - For production deployment configuration

