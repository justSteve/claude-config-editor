# Documentation Index

**Last Updated**: 2025-11-16
**Purpose**: Central index serving both Operators and Developers

---

## Quick Start

| You Are... | Start Here |
|------------|------------|
| **Operator** (running the tool) | [QUICKSTART.md](../QUICKSTART.md) |
| **Developer** (building the code) | [CLAUDE.md](../CLAUDE.md) + [PROJECT-HISTORY.md](./PROJECT-HISTORY.md) |

---

## Active Documentation

### Essential Guides (Current Use)

| Document | Audience | Purpose |
|----------|----------|---------|
| [QUICKSTART.md](../QUICKSTART.md) | Both | Daily workflow with Docker |
| [README.md](./README.md) | Both | Documentation overview |
| [CONTAINER-DEVELOPMENT.md](./CONTAINER-DEVELOPMENT.md) | Both | Docker setup and usage |
| [configuration-guide.md](./configuration-guide.md) | Operators | Configuration options |
| [PROJECT-HISTORY.md](./PROJECT-HISTORY.md) | Developers | Compressed project evolution |

### API Documentation

| Document | Purpose |
|----------|---------|
| [API-REFERENCE-MCP.md](./API-REFERENCE-MCP.md) | Complete MCP endpoint reference |
| [API-TESTING-GUIDE.md](./API-TESTING-GUIDE.md) | Testing procedures and examples |
| [API-TEST-RESULTS.md](./API-TEST-RESULTS.md) | Test results and metrics |
| [security-sanitization-design.md](./security-sanitization-design.md) | Security patterns and sanitization |

### Architecture & Design

| Document | Purpose |
|----------|---------|
| [design-version-control-system.md](./design-version-control-system.md) | System architecture and database schema |
| [planning-production-upgrade-architecture.md](./planning-production-upgrade-architecture.md) | Roadmap and phase planning |

### Technical References

| Document | Purpose |
|----------|---------|
| [documentation-path-handling-concepts.md](./documentation-path-handling-concepts.md) | Path resolution strategies |
| [documentation-windows-path-scanner.md](./documentation-windows-path-scanner.md) | Windows scanner implementation |
| [scanner-comparison-analysis.md](./scanner-comparison-analysis.md) | Scanner architecture analysis |
| [scanner-migration-guide.md](./scanner-migration-guide.md) | Migration from v1 to v2 |

---

## Historical Documentation

### Consolidated History

**[PROJECT-HISTORY.md](./PROJECT-HISTORY.md)** - Contains compressed timeline of:
- All phase completions (Phase 1-5)
- 20+ task summaries
- Key architectural decisions
- Migration notes

### Archive

The [archived/](./archived/) folder contains raw historical documents:
- Phase completion summaries
- Task completion details
- Planning updates
- Session summaries

**Use PROJECT-HISTORY.md for context** - only dig into archived/ if you need specific implementation details.

---

## Documentation by Audience

### For Operators

**Goal**: Run the tool to snapshot Claude configurations

1. **[QUICKSTART.md](../QUICKSTART.md)** - Daily workflow
2. **[CONTAINER-DEVELOPMENT.md](./CONTAINER-DEVELOPMENT.md)** - Docker setup
3. **[configuration-guide.md](./configuration-guide.md)** - Config options

**Key Commands**:
```cmd
session-start.bat              # Start session
runin "snapshot list"          # View snapshots
session-end.bat                # End session
```

### For Developers

**Goal**: Maintain and extend the codebase

1. **[CLAUDE.md](../CLAUDE.md)** - Project memory and conventions
2. **[PROJECT-HISTORY.md](./PROJECT-HISTORY.md)** - Evolution context
3. **[design-version-control-system.md](./design-version-control-system.md)** - Architecture
4. **[planning-production-upgrade-architecture.md](./planning-production-upgrade-architecture.md)** - Roadmap

**Key Commands**:
```cmd
runin "pytest"                              # Full test suite
runin "python -m src.api.app"               # Start API
runin "python -m src.cli.commands --help"   # CLI help
```

---

## File Naming Convention

```
design-*           # Architecture and design decisions
documentation-*    # Feature documentation
planning-*         # Future roadmaps
API-*              # API-specific documentation
security-*         # Security patterns
scanner-*          # Scanner-related docs
```

**Historical files** (now in PROJECT-HISTORY.md or archived/):
```
phase-*            # Phase progress (consolidated)
task-*             # Task completions (archived)
session-summary-*  # Work logs (archived)
```

---

## Project Structure

```
claude-config-editor/
├── QUICKSTART.md              # START HERE (operators)
├── CLAUDE.md                  # PROJECT MEMORY (developers)
├── session-start.bat          # Daily session automation
├── session-end.bat            # Session wrap-up automation
├── setup-dev-env.bat          # One-time Docker setup
├── src/                       # Source code
│   ├── core/                  # Database, scanner, models
│   ├── cli/                   # Typer CLI commands
│   ├── api/                   # FastAPI REST endpoints
│   └── utils/                 # Logging, validation
├── docs/                      # This folder
│   ├── README.md              # Docs overview (two masters)
│   ├── PROJECT-HISTORY.md     # Compressed evolution
│   ├── archived/              # Historical raw docs
│   └── *.md                   # Active documentation
└── tests/                     # Test suite
```

---

## Quick Links

### Most Important (Operators)
- [QUICKSTART.md](../QUICKSTART.md)
- [CONTAINER-DEVELOPMENT.md](./CONTAINER-DEVELOPMENT.md)
- [configuration-guide.md](./configuration-guide.md)

### Most Important (Developers)
- [CLAUDE.md](../CLAUDE.md)
- [PROJECT-HISTORY.md](./PROJECT-HISTORY.md)
- [design-version-control-system.md](./design-version-control-system.md)
- [API-REFERENCE-MCP.md](./API-REFERENCE-MCP.md)

### Shared Baseline
- **Docker containers** - Reproducible environment
- **Python 3.11.7** - Exact version locked
- **SQLite + WAL mode** - Async database access

---

## Maintenance Notes

### Adding Documentation
1. Place in appropriate category
2. Update this index
3. Update [README.md](./README.md) if essential
4. Follow naming convention

### Archiving Documentation
1. Move to [archived/](./archived/) folder
2. Update PROJECT-HISTORY.md if significant
3. Remove from active sections above

---

**Last Updated**: 2025-11-16
