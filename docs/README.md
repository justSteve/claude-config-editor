# Documentation Guide

**This project serves two masters:**

1. **Operators** - Users running the tool to snapshot their Claude configurations
2. **Developers** - Engineers building and maintaining the codebase

Both masters share a common environment: **Docker containers** ensure reproducible execution.

---

## For Operators

**Goal**: Track Claude configuration changes across 17 locations.

### Essential Reading

- **[../QUICKSTART.md](../QUICKSTART.md)** - Daily workflow with Docker
- **[CONTAINER-DEVELOPMENT.md](./CONTAINER-DEVELOPMENT.md)** - Container setup
- **[configuration-guide.md](./configuration-guide.md)** - Configuration options

### Quick Commands

```cmd
session-start.bat              # Start session, snapshot configs
runin "snapshot list"          # View snapshots
runin "snapshot show 5"        # View snapshot details
session-end.bat                # End session, document next steps
```

### What Gets Tracked

Your Claude config files:
- `.claude.json` - Conversation histories, MCP servers
- `settings.json` - User/project/enterprise settings
- `CLAUDE.md` - Memory and instructions
- Slash commands, subagents, logs

---

## For Developers

**Goal**: Maintain and extend the version control system.

### Essential Reading

- **[../QUICKSTART.md](../QUICKSTART.md)** - Development workflow
- **[../CLAUDE.md](../CLAUDE.md)** - Project conventions and architecture
- **[design-version-control-system.md](./design-version-control-system.md)** - System architecture
- **[PROJECT-HISTORY.md](./PROJECT-HISTORY.md)** - Compressed project evolution

### Quick Commands

```cmd
session-start.bat              # Review git history, run tests
runin "pytest"                 # Full test suite
runin "python -m src.api.app"  # Start API server
session-end.bat                # Commit workflow
```

### Architecture Overview

```
src/
├── core/           # Database models, scanner, config
├── cli/            # Typer CLI commands
├── api/            # FastAPI REST endpoints
└── utils/          # Logging, validation
```

### Key Components

- **PathScanner** (`src/core/scanner.py`) - Scans 17 config locations
- **Database** (`src/core/database.py`) - Async SQLite with deduplication
- **Models** (`src/core/models.py`) - SQLAlchemy ORM
- **API** (`src/api/app.py`) - FastAPI with OpenAPI docs

---

## Documentation Categories

### Active Guides (Current Use)

| Document | Audience | Purpose |
|----------|----------|---------|
| [../QUICKSTART.md](../QUICKSTART.md) | Both | Daily workflow |
| [CONTAINER-DEVELOPMENT.md](./CONTAINER-DEVELOPMENT.md) | Both | Docker setup |
| [configuration-guide.md](./configuration-guide.md) | Operators | Config options |
| [API-REFERENCE-MCP.md](./API-REFERENCE-MCP.md) | Developers | API documentation |
| [API-TESTING-GUIDE.md](./API-TESTING-GUIDE.md) | Developers | Testing procedures |

### Architecture & Design (Reference)

| Document | Purpose |
|----------|---------|
| [design-version-control-system.md](./design-version-control-system.md) | System architecture |
| [security-sanitization-design.md](./security-sanitization-design.md) | Security patterns |
| [planning-production-upgrade-architecture.md](./planning-production-upgrade-architecture.md) | Roadmap |

### Historical (Compressed)

| Document | Purpose |
|----------|---------|
| [PROJECT-HISTORY.md](./PROJECT-HISTORY.md) | Evolution summary |
| [archived/](./archived/) | Raw phase documents |

---

## Shared Environment Contract

**Both operators and developers execute in Docker:**

1. **Python 3.11.7** - Exact version locked
2. **All dependencies** - requirements.txt frozen
3. **SQLite database** - WAL mode, async access
4. **Consistent paths** - Container workspace `/workspace`

**This eliminates:**
- "Works on my machine" issues
- Version mismatches
- Path inconsistencies
- Environment drift

---

## File Naming Convention

```
design-*           # Architecture and design decisions
documentation-*    # Feature documentation
planning-*         # Future roadmaps
session-summary-*  # Historical work logs (→ archived)
phase-*           # Phase progress (→ archived)
task-*            # Task completions (→ archived)
```

**Most historical files now consolidated into PROJECT-HISTORY.md**

---

## Adding Documentation

### For Operators
Add to `../QUICKSTART.md` or create `operator-*.md` files.

### For Developers
Add to `../CLAUDE.md` or create `developer-*.md` files.

### For Both
Add to main guides or this README.

---

## Quick Links

### Operators Start Here
1. [../QUICKSTART.md](../QUICKSTART.md) - **START HERE**
2. [CONTAINER-DEVELOPMENT.md](./CONTAINER-DEVELOPMENT.md)
3. [configuration-guide.md](./configuration-guide.md)

### Developers Start Here
1. [../CLAUDE.md](../CLAUDE.md) - **PROJECT MEMORY**
2. [../QUICKSTART.md](../QUICKSTART.md) - **WORKFLOW**
3. [PROJECT-HISTORY.md](./PROJECT-HISTORY.md) - **CONTEXT**
4. [design-version-control-system.md](./design-version-control-system.md) - **ARCHITECTURE**

---

**Last Updated**: 2025-11-16
