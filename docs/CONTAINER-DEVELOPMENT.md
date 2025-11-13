# Container-Based Development Guide

## 🎯 Purpose

This containerized development environment **eliminates friction** between your local environment and AI agent execution environments. When an agent tests code, it runs in the **exact same environment** you'll use, ensuring:

- ✅ No "works on my machine" issues
- ✅ Identical Python versions and dependencies
- ✅ Consistent behavior across all development scenarios
- ✅ Easy rollback if something breaks

## 🚀 Quick Start

### Prerequisites

- **Docker Desktop** installed and running
  - Download from: https://www.docker.com/products/docker-desktop
  - Windows 10/11 with WSL2 enabled
  - Minimum 4GB RAM allocated to Docker

### One-Time Setup

```cmd
# Run the setup script (first time only)
setup-dev-env.bat
```

This will:
1. Check Docker installation
2. Build the development container
3. Create data and logs directories
4. Start the container

**Time:** ~5 minutes on first run (downloads base images and installs dependencies)

## 📋 Daily Workflow

### Starting the Environment

```cmd
# Start the container
docker-compose up -d dev-env

# Verify it's running
docker ps
```

### Running Commands

Use the `runin` wrapper to execute commands in the container:

```cmd
# Run CLI commands
runin "python -m src.cli.commands snapshot list"
runin "python -m src.cli.commands snapshot create --notes 'Test snapshot'"

# Run tests
runin "pytest"
runin "pytest tests/test_scanner.py -v"

# Run code quality checks
runin "black src/ tests/"
runin "ruff check src/"
runin "mypy src/"

# Start the API server
runin "uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8765"
```

### Alternative: Start API as Service

```cmd
# Start API server as a separate container
docker-compose --profile api up -d

# View logs
docker-compose logs -f api

# Stop API server
docker-compose --profile api down
```

### Accessing the Container Shell

```cmd
# Enter the container for interactive work
docker exec -it claude-config-dev bash

# Once inside, you can run any command:
python -m src.cli.commands snapshot list
pytest -v
exit  # to leave the container
```

## 🔧 Container Architecture

### Directory Structure

```
claude-config-editor/
├── Dockerfile              # Container definition
├── docker-compose.yml      # Container orchestration
├── setup-dev-env.bat       # One-time setup script
├── runin.bat              # Command wrapper
├── src/                   # Mounted read-write (live editing)
├── tests/                 # Mounted read-write
├── data/                  # Persistent database
└── logs/                  # Persistent logs
```

### Volume Mounts

| Local Path | Container Path | Purpose |
|------------|----------------|---------|
| `./src` | `/workspace/src` | Live code editing |
| `./tests` | `/workspace/tests` | Test files |
| `./data` | `/workspace/data` | SQLite database |
| `./logs` | `/workspace/logs` | Application logs |

**Changes to files in these directories are immediately reflected in the container.**

### Port Mappings

| Port | Service | URL |
|------|---------|-----|
| 8765 | API Server | http://localhost:8765 |

### Environment Variables

Set in `docker-compose.yml`:
- `DATABASE_URL` - SQLite connection string
- `LOG_LEVEL` - Logging verbosity (INFO, DEBUG, etc.)
- `LOG_FILE` - Log file location
- `PYTHONPATH` - Python module search path

## 🛠️ Common Tasks

### Running the Full Test Suite

```cmd
runin "pytest -v --cov=src --cov-report=html"

# View coverage report
start htmlcov\index.html
```

### Code Formatting

```cmd
# Format all Python code
runin "black src/ tests/"

# Check formatting without changes
runin "black --check src/ tests/"
```

### Linting

```cmd
# Lint with ruff
runin "ruff check src/ tests/"

# Auto-fix issues
runin "ruff check --fix src/ tests/"
```

### Type Checking

```cmd
runin "mypy src/"
```

### Database Operations

```cmd
# Run migrations
runin "alembic upgrade head"

# Create a snapshot
runin "python -m src.cli.commands snapshot create"

# View database
runin "sqlite3 data/claude_config.db 'SELECT * FROM snapshots LIMIT 5;'"
```

### Viewing Logs

```cmd
# Container logs
docker-compose logs -f dev-env

# Application logs
runin "tail -f logs/app.log"
```

## 🔄 Updating Dependencies

### Adding a New Python Package

1. Add package to `requirements.txt` (production) or `requirements-dev.txt` (development)
2. Rebuild the container:

```cmd
docker-compose build dev-env
docker-compose up -d dev-env
```

### Updating Existing Packages

```cmd
# Update requirements files with new versions
# Then rebuild:
docker-compose build --no-cache dev-env
docker-compose up -d dev-env
```

## 🧹 Cleanup

### Stop the Environment

```cmd
# Stop but keep data
docker-compose down

# Stop and remove volumes (deletes data!)
docker-compose down -v
```

### Remove Containers

```cmd
# Remove stopped containers
docker container prune

# Remove all project containers
docker-compose down --rmi all
```

### Full Cleanup

```cmd
# WARNING: Deletes all data, logs, and containers
docker-compose down -v --rmi all
rmdir /s /q data logs
```

## 🐛 Troubleshooting

### Container Won't Start

```cmd
# Check Docker is running
docker ps

# Check logs for errors
docker-compose logs dev-env

# Rebuild from scratch
docker-compose down
docker-compose build --no-cache dev-env
docker-compose up -d dev-env
```

### "Cannot connect to Docker daemon"

- Ensure Docker Desktop is running
- On Windows, ensure WSL2 is enabled

### Port 8765 Already in Use

```cmd
# Find process using port
netstat -ano | findstr :8765

# Kill the process (replace PID)
taskkill /F /PID <PID>

# Or use a different port in docker-compose.yml
```

### Container Runs Out of Space

```cmd
# Clean up Docker
docker system prune -a

# Remove unused volumes
docker volume prune
```

### File Changes Not Reflected

- Ensure you're editing files in the mounted directories (`src/`, `tests/`)
- Restart the container: `docker-compose restart dev-env`

## 🔐 Security Notes

- The container runs as a non-root user (`developer`)
- Read-only mounts for configuration files
- No sensitive credentials in the container
- Git config is read-only
- Database and logs persist outside the container

## 📊 Performance

**First Build:** ~5 minutes (downloads images, installs dependencies)
**Subsequent Builds:** ~30 seconds (uses cached layers)
**Startup Time:** <5 seconds
**Command Execution:** Identical to native Python

## 🆚 Container vs Native Development

| Aspect | Container | Native |
|--------|-----------|--------|
| Setup Time | 5 min (one-time) | Variable |
| Consistency | ✅ Perfect | ⚠️ Environment drift |
| Isolation | ✅ Complete | ❌ Shared system |
| Agent Parity | ✅ Identical | ❌ Different |
| Performance | ~Native | Native |
| Disk Space | ~2GB | ~500MB |

## 💡 Pro Tips

1. **Keep container running** - Start it once, use `runin` for all commands
2. **Use VS Code Remote Containers** - Full IDE inside container
3. **Alias `runin`** - Create shortcuts for common commands
4. **Monitor logs** - Run `docker-compose logs -f` in separate terminal
5. **Snapshot before updates** - Create backup before dependency changes

## 🎓 Learning Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [VS Code Remote Containers](https://code.visualstudio.com/docs/remote/containers)

---

## 🤝 Agent Collaboration

When working with AI agents:

1. **Agent generates code** → Immediately testable with `runin "pytest"`
2. **Agent suggests commands** → Copy-paste with `runin "..."`
3. **Agent debugs issues** → Same environment, no "works for me" problems
4. **Agent creates features** → Test in container before local install

**This is a black box solution - you don't need to understand Docker internals to benefit from consistent, friction-free development.**
