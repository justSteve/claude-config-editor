# NEXT-STEPS.md: Entity-Based Architecture Pivot

> **Status:** Phase 1 COMPLETE ✅ - Ready for Phase 2
>
> **Last Updated:** 2025-11-20
>
> **Trigger:** Review of ccmate's domain model revealed sophisticated entity-based architecture that can be blended with our snapshot system to create unprecedented time-travel + entity intelligence

---

## ✅ Phase 1 Completion Summary (2025-11-20)

**Status:** COMPLETE and MERGED to main (commit: `5f17955`)

**What Was Built:**
- ✅ 5 Entity Dataclasses (176 lines): McpServerEntity, SubagentEntity, SlashCommandEntity, ClaudeMemoryEntity, EntitySnapshot
- ✅ 4 SQLAlchemy Models (+160 lines): Entity snapshot tables with proper relationships and cascade deletes
- ✅ 44 Comprehensive Tests: 100% coverage on new code, all passing
- ✅ Database Auto-Initialization: All entity tables created automatically on startup

**Quality Metrics:**
- Grade: A (Production-Ready)
- Test Coverage: 100% on entities.py and models.py
- Type Safety: Full mypy strict compliance
- Zero Regressions: All existing tests still passing

**Files Added:**
- `src/core/entities.py` (175 lines)
- `tests/test_entities.py` (411 lines)
- `tests/test_models.py` (540 lines)
- `tests/test_database_initialization.py` (576 lines)

**Files Modified:**
- `src/core/models.py` (+160 lines for entity tables)

**Commits:**
1. `1bc5be0` - feat: add entity dataclasses for semantic configuration tracking
2. `58d8399` - fix: improve type hints and fix deprecation warnings in entities
3. `24aff87` - feat: add entity-specific database models for semantic tracking
4. `df6092b` - feat: entity models auto-initialize with database
5. `5f17955` - Merge feat/entity-model: Phase 1 Entity Model Foundation

**Next:** Phase 2 - Entity-Aware Scanner (create entity parser and integrate with PathScanner)

---

## Executive Summary

This document outlines a substantive architectural pivot that will transform Claude Config Editor from a generic file-snapshot system into a **domain-aware configuration version control** with semantic entity understanding.

### The Pivot in One Sentence
Add semantic parsing of Claude configuration entities (MCP servers, subagents, slash commands) to our snapshot system, enabling entity-level time-travel queries and delta tracking.

### What This Enables
- **Entity Timelines**: "Show me every version of the 'filesystem' MCP server across all snapshots"
- **Selective Restoration**: "Restore only MCP server configuration from last Tuesday"
- **Entity Deltas**: "What changed in my subagents between snapshots 5 and 8?"
- **Change Heatmaps**: Visualize which entities are "hot" (frequently modified)
- **Domain Intelligence**: Track when entities were added, removed, modified with semantic context

### Why This Matters
ccmate has polished UI but zero time-travel. We have sophisticated snapshots but generic file tracking. Combined: unprecedented capability.

---

## Phase Breakdown

### Phase 1: Entity Model Foundation (Week 1)
**Goal:** Add SQLAlchemy models for Claude-specific entities

**Key Files to Create:**
- `src/core/entities.py` - Entity dataclasses and parsing logic
- `tests/test_entities.py` - Entity parsing tests

**Key Files to Modify:**
- `src/core/models.py` - Add entity snapshot tables
- `src/core/database.py` - Add initialization for entity tables

### Phase 2: Entity-Aware Scanner (Week 1-2)
**Goal:** Parse entities from config files during snapshot creation

**Key Files to Create:**
- `src/core/entity_parser.py` - Parse MCP/agents/commands from files
- `tests/test_entity_parser.py` - Parser unit tests

**Key Files to Modify:**
- `src/core/scanner.py` - Integrate entity parsing into snapshot workflow

### Phase 3: Entity Delta System (Week 2-3)
**Goal:** Compare entities between snapshots, track changes

**Key Files to Create:**
- `src/core/entity_deltas.py` - Diff logic for entities
- `tests/test_entity_deltas.py` - Delta comparison tests

**Key Files to Modify:**
- None (pure new layer on top of existing models)

### Phase 4: REST API Endpoints (Week 2-3)
**Goal:** Expose entity queries through FastAPI

**Key Files to Create:**
- `src/api/routes/entities.py` - Entity CRUD endpoints
- `src/api/routes/deltas.py` - Delta comparison endpoints
- `tests/test_api_entities.py` - Endpoint tests

**Key Files to Modify:**
- `src/api/main.py` - Mount entity routes

### Phase 5: Entity Timeline UI Panel (Week 3-4)
**Goal:** Build web dashboard for entity visualization

**Key Files to Create:**
- `static/components/EntityDashboard.tsx` - Main entity panel
- `static/components/EntityTimeline.tsx` - Timeline visualization
- `static/components/DeltaViewer.tsx` - Side-by-side entity diff

**Key Files to Modify:**
- `index.html` - Add entity dashboard tab
- `static/app.tsx` - Wire up entity routes

### Phase 6: Documentation & Refactoring (Week 4)
**Goal:** Update all docs, remove obsolete code, create migration guide

**Key Files to Create:**
- `docs/ENTITIES.md` - Entity model reference
- `docs/ENTITY-QUERIES.md` - Query examples and patterns

**Key Files to Modify:**
- `CLAUDE.md` - Update architecture section
- `NEXT-STEPS.md` - Update status
- `README.md` - Highlight entity capabilities

---

## Detailed Task Breakdown

### Phase 1: Entity Model Foundation

#### Task 1.1: Create Entity Dataclasses

**Files:**
- Create: `src/core/entities.py`
- Test: `tests/test_entities.py`

**Context:**
Define the core entity types we'll parse and track. Based on ccmate's domain model + our snapshot system.

**Implementation Steps:**

1. Create `src/core/entities.py` with entity dataclasses:

```python
"""
Entity models for Claude configuration entities.

These represent semantic domain objects parsed from configuration files,
distinct from generic SnapshotPath records.
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class McpServerEntity:
    """Represents an MCP server configuration."""

    name: str
    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    enabled: bool = True
    config_file: str = ""  # e.g., "~/.claude.json"

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "name": self.name,
            "command": self.command,
            "args": self.args,
            "env": self.env,
            "enabled": self.enabled,
        }


@dataclass
class SubagentEntity:
    """Represents a subagent configuration."""

    name: str
    content: str  # Full markdown content
    created_at: Optional[datetime] = None
    config_file: str = ""  # e.g., "~/.claude/subagents/my-agent.md"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "content_preview": self.content[:100] + "..." if len(self.content) > 100 else self.content,
            "size_bytes": len(self.content),
        }


@dataclass
class SlashCommandEntity:
    """Represents a slash command."""

    name: str
    content: str  # Command prompt/template
    created_at: Optional[datetime] = None
    config_file: str = ""  # e.g., "~/.claude/commands/my-cmd.md"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "content_preview": self.content[:100] + "..." if len(self.content) > 100 else self.content,
        }


@dataclass
class ClaudeMemoryEntity:
    """Represents CLAUDE.md memory file."""

    scope: str  # "user", "project"
    content: str  # Full markdown content
    path: str = ""  # e.g., "~/.claude/CLAUDE.md"

    def to_dict(self) -> dict:
        return {
            "scope": self.scope,
            "content_preview": self.content[:200] + "..." if len(self.content) > 200 else self.content,
            "size_bytes": len(self.content),
        }


@dataclass
class EntitySnapshot:
    """Complete set of entities for a given snapshot."""

    snapshot_id: int
    snapshot_time: datetime
    mcp_servers: list[McpServerEntity] = field(default_factory=list)
    subagents: list[SubagentEntity] = field(default_factory=list)
    commands: list[SlashCommandEntity] = field(default_factory=list)
    memory: Optional[ClaudeMemoryEntity] = None

    def summary(self) -> dict:
        """Get summary statistics."""
        return {
            "snapshot_id": self.snapshot_id,
            "snapshot_time": self.snapshot_time.isoformat(),
            "mcp_server_count": len(self.mcp_servers),
            "subagent_count": len(self.subagents),
            "command_count": len(self.commands),
            "has_memory": self.memory is not None,
        }
```

2. Create test file `tests/test_entities.py`:

```python
"""Tests for entity dataclasses."""

from datetime import datetime
from src.core.entities import (
    McpServerEntity,
    SubagentEntity,
    SlashCommandEntity,
    ClaudeMemoryEntity,
    EntitySnapshot,
)


def test_mcp_server_entity_creation():
    """Test McpServerEntity initialization."""
    server = McpServerEntity(
        name="filesystem",
        command="npx",
        args=["@anthropic-ai/mcp-server-filesystem"],
        env={"HOME": "/home/user"},
        enabled=True,
    )
    assert server.name == "filesystem"
    assert server.command == "npx"
    assert len(server.args) == 1


def test_mcp_server_entity_to_dict():
    """Test serialization to dictionary."""
    server = McpServerEntity(
        name="test-server",
        command="python",
        args=["-m", "server"],
    )
    data = server.to_dict()
    assert data["name"] == "test-server"
    assert data["command"] == "python"
    assert "enabled" in data


def test_subagent_entity_creation():
    """Test SubagentEntity initialization."""
    agent = SubagentEntity(
        name="research-agent",
        content="# Research Agent\n\nPurpose: Research things",
    )
    assert agent.name == "research-agent"
    assert "Research" in agent.content


def test_entity_snapshot_summary():
    """Test EntitySnapshot summary generation."""
    snap = EntitySnapshot(
        snapshot_id=1,
        snapshot_time=datetime.now(),
        mcp_servers=[
            McpServerEntity(name="fs", command="npx"),
        ],
        subagents=[
            SubagentEntity(name="agent1", content="content1"),
            SubagentEntity(name="agent2", content="content2"),
        ],
    )

    summary = snap.summary()
    assert summary["mcp_server_count"] == 1
    assert summary["subagent_count"] == 2
    assert summary["command_count"] == 0
```

3. Run tests to verify they pass:
```bash
pytest tests/test_entities.py -v
```

4. Commit:
```bash
git add src/core/entities.py tests/test_entities.py
git commit -m "feat: add entity dataclasses for semantic configuration tracking"
```

---

#### Task 1.2: Extend Database Models with Entity Tables

**Files:**
- Modify: `src/core/models.py`

**Context:**
Add SQLAlchemy ORM models for storing parsed entities alongside snapshots. These are denormalized for query performance.

**Implementation Steps:**

1. Add entity models to `src/core/models.py` (after existing models):

```python
# Add these imports at the top if not present
from sqlalchemy import JSON

# Add these models after the Snapshot model and before end of file

class McpServerSnapshot(Base):
    """
    MCP server configuration at a specific snapshot time.
    Denormalized for efficient querying by entity name across snapshots.
    """

    __tablename__ = "mcp_server_snapshots"
    __table_args__ = (
        Index("idx_snapshot_server", "snapshot_id", "server_name"),
        Index("idx_server_name", "server_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    snapshot_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("snapshots.id", ondelete="CASCADE"), nullable=False
    )
    server_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    command: Mapped[str] = mapped_column(String(512), nullable=False)
    args_json: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array
    env_json: Mapped[str] = mapped_column(Text, nullable=False)   # JSON object
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    config_file_path: Mapped[str] = mapped_column(String(512), nullable=True)

    # Relationships
    snapshot: Mapped["Snapshot"] = relationship(back_populates="mcp_servers")

    def __repr__(self) -> str:
        return f"<McpServerSnapshot(server={self.server_name}, snapshot={self.snapshot_id})>"


class SubagentSnapshot(Base):
    """
    Subagent configuration at a specific snapshot time.
    Content is deduplicated via FileContent reference.
    """

    __tablename__ = "subagent_snapshots"
    __table_args__ = (
        Index("idx_snapshot_agent", "snapshot_id", "agent_name"),
        Index("idx_agent_name", "agent_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    snapshot_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("snapshots.id", ondelete="CASCADE"), nullable=False
    )
    agent_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    content_hash: Mapped[str] = mapped_column(
        String(64), ForeignKey("file_contents.content_hash"), nullable=False
    )
    config_file_path: Mapped[str] = mapped_column(String(512), nullable=True)

    # Relationships
    snapshot: Mapped["Snapshot"] = relationship(back_populates="subagents")
    content: Mapped["FileContent"] = relationship(back_populates="subagent_refs")

    def __repr__(self) -> str:
        return f"<SubagentSnapshot(agent={self.agent_name}, snapshot={self.snapshot_id})>"


class SlashCommandSnapshot(Base):
    """
    Slash command configuration at a specific snapshot time.
    Content is deduplicated via FileContent reference.
    """

    __tablename__ = "slash_command_snapshots"
    __table_args__ = (
        Index("idx_snapshot_command", "snapshot_id", "command_name"),
        Index("idx_command_name", "command_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    snapshot_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("snapshots.id", ondelete="CASCADE"), nullable=False
    )
    command_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    content_hash: Mapped[str] = mapped_column(
        String(64), ForeignKey("file_contents.content_hash"), nullable=False
    )
    config_file_path: Mapped[str] = mapped_column(String(512), nullable=True)

    # Relationships
    snapshot: Mapped["Snapshot"] = relationship(back_populates="commands")
    content: Mapped["FileContent"] = relationship(back_populates="command_refs")

    def __repr__(self) -> str:
        return f"<SlashCommandSnapshot(command={self.command_name}, snapshot={self.snapshot_id})>"


class ClaudeMemorySnapshot(Base):
    """
    CLAUDE.md memory file at a specific snapshot time.
    Content is deduplicated via FileContent reference.
    """

    __tablename__ = "claude_memory_snapshots"
    __table_args__ = (
        Index("idx_snapshot_memory", "snapshot_id", "scope"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    snapshot_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("snapshots.id", ondelete="CASCADE"), nullable=False
    )
    scope: Mapped[str] = mapped_column(String(50), nullable=False)  # "user" or "project"
    content_hash: Mapped[str] = mapped_column(
        String(64), ForeignKey("file_contents.content_hash"), nullable=False
    )
    config_file_path: Mapped[str] = mapped_column(String(512), nullable=True)

    # Relationships
    snapshot: Mapped["Snapshot"] = relationship(back_populates="memory")
    content: Mapped["FileContent"] = relationship(back_populates="memory_refs")

    def __repr__(self) -> str:
        return f"<ClaudeMemorySnapshot(scope={self.scope}, snapshot={self.snapshot_id})>"


# Update FileContent model to add backref for deduplication tracking
# Add these lines to the FileContent class definition:
# subagent_refs: Mapped[list["SubagentSnapshot"]] = relationship(back_populates="content")
# command_refs: Mapped[list["SlashCommandSnapshot"]] = relationship(back_populates="content")
# memory_refs: Mapped[list["ClaudeMemorySnapshot"]] = relationship(back_populates="content")


# Update Snapshot model to add entity relationships
# Add these lines to the Snapshot class definition:
# mcp_servers: Mapped[list["McpServerSnapshot"]] = relationship(
#     "McpServerSnapshot", back_populates="snapshot", cascade="all, delete-orphan"
# )
# subagents: Mapped[list["SubagentSnapshot"]] = relationship(
#     "SubagentSnapshot", back_populates="snapshot", cascade="all, delete-orphan"
# )
# commands: Mapped[list["SlashCommandSnapshot"]] = relationship(
#     "SlashCommandSnapshot", back_populates="snapshot", cascade="all, delete-orphan"
# )
# memory: Mapped[list["ClaudeMemorySnapshot"]] = relationship(
#     "ClaudeMemorySnapshot", back_populates="snapshot", cascade="all, delete-orphan"
# )
```

2. Run tests to ensure models are valid:
```bash
pytest tests/test_models.py -v
```

3. Commit:
```bash
git add src/core/models.py
git commit -m "feat: add entity-specific database models for semantic tracking"
```

---

#### Task 1.3: Update Database Initialization

**Files:**
- Modify: `src/core/database.py`

**Context:**
Ensure database manager creates tables for new entity models on startup.

**Implementation Steps:**

1. Verify that `DatabaseManager.init_db()` calls `Base.metadata.create_all()`:

```python
# In src/core/database.py, ensure the init_db method includes:

async def init_db(self) -> None:
    """Initialize database tables."""
    async with self.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

2. Run database initialization test:
```bash
pytest tests/test_database.py::test_initialization -v
```

3. Commit:
```bash
git add src/core/database.py
git commit -m "feat: entity models auto-initialize with database"
```

---

### Phase 2: Entity-Aware Scanner

#### Task 2.1: Create Entity Parser

**Files:**
- Create: `src/core/entity_parser.py`
- Test: `tests/test_entity_parser.py`

**Context:**
Parse Claude configuration files to extract semantic entities. This is the key intelligence layer that turns raw files into domain objects.

**Implementation Steps:**

1. Create `src/core/entity_parser.py`:

```python
"""
Parser for extracting semantic entities from Claude configuration files.

Based on ccmate's domain model:
- MCP servers from ~/.claude.json
- Subagents from ~/.claude/subagents/*.md
- Slash commands from ~/.claude/commands/*.md
- CLAUDE.md memory files
"""

import json
from pathlib import Path
from typing import Optional
from datetime import datetime
import logging

from src.core.entities import (
    McpServerEntity,
    SubagentEntity,
    SlashCommandEntity,
    ClaudeMemoryEntity,
    EntitySnapshot,
)

logger = logging.getLogger(__name__)


class EntityParser:
    """Parse Claude configuration entities from files."""

    @staticmethod
    def parse_mcp_servers(claude_json_path: Path) -> list[McpServerEntity]:
        """
        Extract MCP server entities from ~/.claude.json

        Expected structure:
        {
            "mcpServers": {
                "server-name": {
                    "command": "python",
                    "args": ["-m", "server"],
                    "env": {"KEY": "value"}
                }
            }
        }
        """
        servers = []

        if not claude_json_path.exists():
            logger.debug(f"Claude JSON file not found: {claude_json_path}")
            return servers

        try:
            content = claude_json_path.read_text(encoding="utf-8")
            data = json.loads(content)

            mcp_servers = data.get("mcpServers", {})
            if not isinstance(mcp_servers, dict):
                logger.warning("mcpServers is not a dictionary")
                return servers

            for server_name, config in mcp_servers.items():
                if not isinstance(config, dict):
                    logger.warning(f"MCP server {server_name} config is not a dictionary")
                    continue

                server = McpServerEntity(
                    name=server_name,
                    command=config.get("command", ""),
                    args=config.get("args", []) if isinstance(config.get("args"), list) else [],
                    env=config.get("env", {}) if isinstance(config.get("env"), dict) else {},
                    enabled=config.get("enabled", True),
                    config_file=str(claude_json_path),
                )
                servers.append(server)
                logger.debug(f"Parsed MCP server: {server_name}")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude JSON: {e}")
        except Exception as e:
            logger.error(f"Error parsing MCP servers: {e}")

        return servers

    @staticmethod
    def parse_subagents(subagents_dir: Path) -> list[SubagentEntity]:
        """
        Extract subagent entities from ~/.claude/subagents/*.md

        Each .md file is treated as a subagent with its name derived from filename.
        """
        agents = []

        if not subagents_dir.exists():
            logger.debug(f"Subagents directory not found: {subagents_dir}")
            return agents

        try:
            for agent_file in subagents_dir.glob("*.md"):
                try:
                    content = agent_file.read_text(encoding="utf-8")
                    agent_name = agent_file.stem  # filename without .md

                    agent = SubagentEntity(
                        name=agent_name,
                        content=content,
                        created_at=datetime.fromtimestamp(agent_file.stat().st_mtime),
                        config_file=str(agent_file),
                    )
                    agents.append(agent)
                    logger.debug(f"Parsed subagent: {agent_name}")

                except Exception as e:
                    logger.error(f"Failed to parse subagent {agent_file}: {e}")

        except Exception as e:
            logger.error(f"Error scanning subagents directory: {e}")

        return agents

    @staticmethod
    def parse_slash_commands(commands_dir: Path) -> list[SlashCommandEntity]:
        """
        Extract slash command entities from ~/.claude/commands/*.md

        Similar structure to subagents - each .md file is a command.
        """
        commands = []

        if not commands_dir.exists():
            logger.debug(f"Commands directory not found: {commands_dir}")
            return commands

        try:
            for cmd_file in commands_dir.glob("*.md"):
                try:
                    content = cmd_file.read_text(encoding="utf-8")
                    cmd_name = cmd_file.stem  # filename without .md

                    command = SlashCommandEntity(
                        name=cmd_name,
                        content=content,
                        created_at=datetime.fromtimestamp(cmd_file.stat().st_mtime),
                        config_file=str(cmd_file),
                    )
                    commands.append(command)
                    logger.debug(f"Parsed slash command: {cmd_name}")

                except Exception as e:
                    logger.error(f"Failed to parse slash command {cmd_file}: {e}")

        except Exception as e:
            logger.error(f"Error scanning commands directory: {e}")

        return commands

    @staticmethod
    def parse_claude_memory(memory_path: Path) -> Optional[ClaudeMemoryEntity]:
        """
        Extract CLAUDE.md memory entity.

        Scope is inferred from path:
        - ~/.claude/CLAUDE.md -> "user"
        - <project>/.claude/CLAUDE.md -> "project"
        """
        if not memory_path.exists():
            logger.debug(f"CLAUDE.md not found: {memory_path}")
            return None

        try:
            content = memory_path.read_text(encoding="utf-8")

            # Infer scope from path
            scope = "user" if ".claude" in str(memory_path) and ".claude/" in str(memory_path) else "project"

            memory = ClaudeMemoryEntity(
                scope=scope,
                content=content,
                path=str(memory_path),
            )
            logger.debug(f"Parsed CLAUDE.md ({scope} scope)")
            return memory

        except Exception as e:
            logger.error(f"Error parsing CLAUDE.md: {e}")
            return None

    @staticmethod
    def parse_all(
        snapshot_id: int,
        snapshot_time: datetime,
        claude_home: Path,
    ) -> EntitySnapshot:
        """
        Parse all entities from a Claude home directory.

        Args:
            snapshot_id: ID of snapshot being created
            snapshot_time: When the snapshot was taken
            claude_home: Path to ~/.claude directory

        Returns:
            EntitySnapshot containing all parsed entities
        """
        logger.info(f"Parsing entities from {claude_home}")

        entity_snapshot = EntitySnapshot(
            snapshot_id=snapshot_id,
            snapshot_time=snapshot_time,
        )

        # Parse each entity type
        entity_snapshot.mcp_servers = EntityParser.parse_mcp_servers(
            claude_home.parent / ".claude.json"
        )

        entity_snapshot.subagents = EntityParser.parse_subagents(
            claude_home / "subagents"
        )

        entity_snapshot.commands = EntityParser.parse_slash_commands(
            claude_home / "commands"
        )

        entity_snapshot.memory = EntityParser.parse_claude_memory(
            claude_home / "CLAUDE.md"
        )

        summary = entity_snapshot.summary()
        logger.info(
            f"Entity parsing complete: {summary['mcp_server_count']} servers, "
            f"{summary['subagent_count']} agents, {summary['command_count']} commands"
        )

        return entity_snapshot
```

2. Create test file `tests/test_entity_parser.py`:

```python
"""Tests for entity parser."""

import json
import tempfile
from pathlib import Path
from datetime import datetime

from src.core.entity_parser import EntityParser
from src.core.entities import EntitySnapshot


def test_parse_mcp_servers_valid_json():
    """Test parsing MCP servers from valid JSON."""
    with tempfile.TemporaryDirectory() as tmpdir:
        claude_json = Path(tmpdir) / ".claude.json"
        claude_json.write_text(json.dumps({
            "mcpServers": {
                "filesystem": {
                    "command": "npx",
                    "args": ["@anthropic-ai/mcp-server-filesystem"],
                    "env": {"HOME": "/home/user"},
                    "enabled": True,
                },
                "brave-search": {
                    "command": "python",
                    "args": ["-m", "brave_search"],
                    "enabled": False,
                }
            }
        }))

        servers = EntityParser.parse_mcp_servers(claude_json)

        assert len(servers) == 2
        assert servers[0].name == "filesystem"
        assert servers[0].command == "npx"
        assert servers[1].name == "brave-search"
        assert servers[1].enabled is False


def test_parse_mcp_servers_file_not_found():
    """Test parsing when file doesn't exist."""
    servers = EntityParser.parse_mcp_servers(Path("/nonexistent/path/.claude.json"))
    assert servers == []


def test_parse_subagents():
    """Test parsing subagent files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        subagents_dir = Path(tmpdir) / "subagents"
        subagents_dir.mkdir()

        (subagents_dir / "research-agent.md").write_text("# Research Agent\n\nResearch things")
        (subagents_dir / "coding-agent.md").write_text("# Coding Agent\n\nWrite code")

        agents = EntityParser.parse_subagents(subagents_dir)

        assert len(agents) == 2
        names = {a.name for a in agents}
        assert "research-agent" in names
        assert "coding-agent" in names


def test_parse_all_entities():
    """Test parsing all entity types together."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        claude_dir = tmpdir / ".claude"
        claude_dir.mkdir()

        # Setup MCP servers
        (tmpdir / ".claude.json").write_text(json.dumps({
            "mcpServers": {
                "filesystem": {"command": "npx"}
            }
        }))

        # Setup subagents
        (claude_dir / "subagents").mkdir()
        (claude_dir / "subagents" / "agent1.md").write_text("# Agent 1")

        # Setup commands
        (claude_dir / "commands").mkdir()
        (claude_dir / "commands" / "cmd1.md").write_text("# Command 1")

        # Setup memory
        (claude_dir / "CLAUDE.md").write_text("# My Memory")

        snapshot = EntityParser.parse_all(
            snapshot_id=1,
            snapshot_time=datetime.now(),
            claude_home=claude_dir,
        )

        summary = snapshot.summary()
        assert summary["mcp_server_count"] == 1
        assert summary["subagent_count"] == 1
        assert summary["command_count"] == 1
        assert summary["has_memory"] is True
```

3. Run tests:
```bash
pytest tests/test_entity_parser.py -v
```

4. Commit:
```bash
git add src/core/entity_parser.py tests/test_entity_parser.py
git commit -m "feat: implement entity parser for Claude configuration files"
```

---

#### Task 2.2: Integrate Entity Parsing into Scanner

**Files:**
- Modify: `src/core/scanner.py`

**Context:**
When creating a snapshot, also parse and store entities. Update the snapshot creation workflow to capture semantic entities alongside raw files.

**Implementation Steps:**

1. In `src/core/scanner.py`, add entity parsing to the `create_snapshot` method:

```python
# Add import at top
from src.core.entity_parser import EntityParser
from src.core.models import (
    McpServerSnapshot,
    SubagentSnapshot,
    SlashCommandSnapshot,
    ClaudeMemorySnapshot,
)

# In the PathScanner.create_snapshot method, after creating the Snapshot record,
# add entity parsing:

async def create_snapshot(
    self,
    trigger_type: str = "manual",
    triggered_by: Optional[str] = None,
    notes: Optional[str] = None,
) -> Snapshot:
    """Create a new snapshot with entity parsing."""

    # ... existing snapshot creation code ...

    # After snapshot is created and committed, parse entities
    logger.info("Parsing entities...")
    entity_snapshot = EntityParser.parse_all(
        snapshot_id=snapshot.id,
        snapshot_time=snapshot.snapshot_time,
        claude_home=self.get_claude_home(),
    )

    # Store parsed entities in database
    await self._store_entities(snapshot, entity_snapshot)

    logger.info(f"Snapshot {snapshot.id} created with entities")
    return snapshot


async def _store_entities(
    self,
    snapshot: Snapshot,
    entity_snapshot: EntitySnapshot,
) -> None:
    """Store parsed entities in database."""

    async with self.session.begin():
        # Store MCP servers
        for server in entity_snapshot.mcp_servers:
            mcp_record = McpServerSnapshot(
                snapshot_id=snapshot.id,
                server_name=server.name,
                command=server.command,
                args_json=json.dumps(server.args),
                env_json=json.dumps(server.env),
                enabled=server.enabled,
                config_file_path=server.config_file,
            )
            self.session.add(mcp_record)

        # Store subagents
        for agent in entity_snapshot.subagents:
            # Get or create file content record
            content_hash = self._hash_content(agent.content.encode())
            file_content = await self._get_or_create_file_content(
                content=agent.content.encode(),
                content_hash=content_hash,
            )

            agent_record = SubagentSnapshot(
                snapshot_id=snapshot.id,
                agent_name=agent.name,
                content_hash=content_hash,
                config_file_path=agent.config_file,
            )
            self.session.add(agent_record)

        # Store commands
        for command in entity_snapshot.commands:
            content_hash = self._hash_content(command.content.encode())
            file_content = await self._get_or_create_file_content(
                content=command.content.encode(),
                content_hash=content_hash,
            )

            command_record = SlashCommandSnapshot(
                snapshot_id=snapshot.id,
                command_name=command.name,
                content_hash=content_hash,
                config_file_path=command.config_file,
            )
            self.session.add(command_record)

        # Store memory
        if entity_snapshot.memory:
            memory = entity_snapshot.memory
            content_hash = self._hash_content(memory.content.encode())
            file_content = await self._get_or_create_file_content(
                content=memory.content.encode(),
                content_hash=content_hash,
            )

            memory_record = ClaudeMemorySnapshot(
                snapshot_id=snapshot.id,
                scope=memory.scope,
                content_hash=content_hash,
                config_file_path=memory.path,
            )
            self.session.add(memory_record)
```

2. Run scanner tests to ensure integration works:
```bash
pytest tests/test_scanner.py -v
```

3. Commit:
```bash
git add src/core/scanner.py
git commit -m "feat: integrate entity parsing into snapshot creation workflow"
```

---

### Phase 3: Entity Delta System

#### Task 3.1: Create Entity Delta Comparison Engine

**Files:**
- Create: `src/core/entity_deltas.py`
- Test: `tests/test_entity_deltas.py`

**Context:**
Compare entities between two snapshots to identify additions, deletions, and modifications. This powers entity-level change tracking - a key differentiator.

**Implementation Steps:**

1. Create `src/core/entity_deltas.py`:

```python
"""
Entity delta comparison system.

Compares semantic entities (MCP servers, agents, commands) between snapshots
to track semantic changes, not just file modifications.
"""

import json
from dataclasses import dataclass
from typing import Optional
from datetime import datetime
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models import (
    McpServerSnapshot,
    SubagentSnapshot,
    SlashCommandSnapshot,
    ClaudeMemorySnapshot,
    Snapshot,
)
from src.core.entities import McpServerEntity

logger = logging.getLogger(__name__)


@dataclass
class EntityDelta:
    """Represents a change to an entity between two snapshots."""

    entity_type: str  # "mcp_server", "subagent", "command", "memory"
    entity_name: str
    change_type: str  # "added", "removed", "modified"
    from_snapshot_id: int
    to_snapshot_id: int
    from_snapshot_time: datetime
    to_snapshot_time: datetime

    # Change details (varies by type)
    old_value: Optional[dict] = None
    new_value: Optional[dict] = None

    def summary(self) -> str:
        """Human-readable description of change."""
        verb = {
            "added": "Added",
            "removed": "Removed",
            "modified": "Modified",
        }.get(self.change_type, "Changed")

        return f"{verb} {self.entity_type}: {self.entity_name}"


@dataclass
class SnapshotEntityDelta:
    """Complete set of entity changes between two snapshots."""

    from_snapshot_id: int
    to_snapshot_id: int
    from_snapshot_time: datetime
    to_snapshot_time: datetime

    mcp_server_deltas: list[EntityDelta]
    subagent_deltas: list[EntityDelta]
    command_deltas: list[EntityDelta]
    memory_deltas: list[EntityDelta]

    def summary_stats(self) -> dict:
        """Get summary statistics of changes."""
        all_deltas = (
            self.mcp_server_deltas
            + self.subagent_deltas
            + self.command_deltas
            + self.memory_deltas
        )

        return {
            "total_changes": len(all_deltas),
            "mcp_servers_changed": len(self.mcp_server_deltas),
            "subagents_changed": len(self.subagent_deltas),
            "commands_changed": len(self.command_deltas),
            "memory_changed": len(self.memory_deltas),
            "added_count": sum(1 for d in all_deltas if d.change_type == "added"),
            "removed_count": sum(1 for d in all_deltas if d.change_type == "removed"),
            "modified_count": sum(1 for d in all_deltas if d.change_type == "modified"),
        }


class EntityDeltaComparer:
    """Compare entities between snapshots."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def compare_snapshots(
        self,
        from_snapshot_id: int,
        to_snapshot_id: int,
    ) -> SnapshotEntityDelta:
        """
        Compare all entities between two snapshots.

        Args:
            from_snapshot_id: Source snapshot ID
            to_snapshot_id: Target snapshot ID

        Returns:
            SnapshotEntityDelta with all entity changes
        """
        logger.info(f"Comparing entities from snapshot {from_snapshot_id} to {to_snapshot_id}")

        # Get snapshot metadata
        from_snap = await self.session.get(Snapshot, from_snapshot_id)
        to_snap = await self.session.get(Snapshot, to_snapshot_id)

        if not from_snap or not to_snap:
            raise ValueError("One or both snapshots not found")

        # Compare each entity type
        mcp_deltas = await self._compare_mcp_servers(from_snapshot_id, to_snapshot_id)
        agent_deltas = await self._compare_subagents(from_snapshot_id, to_snapshot_id)
        cmd_deltas = await self._compare_commands(from_snapshot_id, to_snapshot_id)
        mem_deltas = await self._compare_memory(from_snapshot_id, to_snapshot_id)

        return SnapshotEntityDelta(
            from_snapshot_id=from_snapshot_id,
            to_snapshot_id=to_snapshot_id,
            from_snapshot_time=from_snap.snapshot_time,
            to_snapshot_time=to_snap.snapshot_time,
            mcp_server_deltas=mcp_deltas,
            subagent_deltas=agent_deltas,
            command_deltas=cmd_deltas,
            memory_deltas=mem_deltas,
        )

    async def _compare_mcp_servers(
        self,
        from_snap_id: int,
        to_snap_id: int,
    ) -> list[EntityDelta]:
        """Compare MCP servers between snapshots."""
        deltas = []

        # Get servers in both snapshots
        from_stmt = select(McpServerSnapshot).where(
            McpServerSnapshot.snapshot_id == from_snap_id
        )
        to_stmt = select(McpServerSnapshot).where(
            McpServerSnapshot.snapshot_id == to_snap_id
        )

        from_result = await self.session.execute(from_stmt)
        to_result = await self.session.execute(to_stmt)

        from_servers = {s.server_name: s for s in from_result.scalars().all()}
        to_servers = {s.server_name: s for s in to_result.scalars().all()}

        # Find added servers
        for name in to_servers:
            if name not in from_servers:
                server = to_servers[name]
                delta = EntityDelta(
                    entity_type="mcp_server",
                    entity_name=name,
                    change_type="added",
                    from_snapshot_id=from_snap_id,
                    to_snapshot_id=to_snap_id,
                    from_snapshot_time=None,
                    to_snapshot_time=None,
                    new_value={
                        "command": server.command,
                        "args": json.loads(server.args_json),
                        "enabled": server.enabled,
                    },
                )
                deltas.append(delta)

        # Find removed servers
        for name in from_servers:
            if name not in to_servers:
                server = from_servers[name]
                delta = EntityDelta(
                    entity_type="mcp_server",
                    entity_name=name,
                    change_type="removed",
                    from_snapshot_id=from_snap_id,
                    to_snapshot_id=to_snap_id,
                    from_snapshot_time=None,
                    to_snapshot_time=None,
                    old_value={
                        "command": server.command,
                        "args": json.loads(server.args_json),
                        "enabled": server.enabled,
                    },
                )
                deltas.append(delta)

        # Find modified servers
        for name in from_servers:
            if name in to_servers:
                from_server = from_servers[name]
                to_server = to_servers[name]

                # Check if anything changed
                if (
                    from_server.command != to_server.command
                    or from_server.args_json != to_server.args_json
                    or from_server.env_json != to_server.env_json
                    or from_server.enabled != to_server.enabled
                ):
                    delta = EntityDelta(
                        entity_type="mcp_server",
                        entity_name=name,
                        change_type="modified",
                        from_snapshot_id=from_snap_id,
                        to_snapshot_id=to_snap_id,
                        from_snapshot_time=None,
                        to_snapshot_time=None,
                        old_value={
                            "command": from_server.command,
                            "args": json.loads(from_server.args_json),
                            "enabled": from_server.enabled,
                        },
                        new_value={
                            "command": to_server.command,
                            "args": json.loads(to_server.args_json),
                            "enabled": to_server.enabled,
                        },
                    )
                    deltas.append(delta)

        return deltas

    # Similar methods for _compare_subagents, _compare_commands, _compare_memory
    # (implementation follows same pattern as _compare_mcp_servers)
```

2. Create test file `tests/test_entity_deltas.py`:

```python
"""Tests for entity delta comparison."""

import json
import pytest
from datetime import datetime

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.core.models import Base, Snapshot, McpServerSnapshot
from src.core.entity_deltas import EntityDeltaComparer


@pytest.mark.asyncio
async def test_mcp_server_added():
    """Test detecting when MCP server is added."""
    # Setup async database
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Create two snapshots
        snap1 = Snapshot(
            snapshot_time=datetime.now(),
            snapshot_hash="hash1",
            trigger_type="manual",
            os_type="linux",
            total_locations=17,
            files_found=50,
            directories_found=10,
            total_size_bytes=100000,
        )
        snap2 = Snapshot(
            snapshot_time=datetime.now(),
            snapshot_hash="hash2",
            trigger_type="manual",
            os_type="linux",
            total_locations=17,
            files_found=51,
            directories_found=10,
            total_size_bytes=100000,
        )

        session.add(snap1)
        session.add(snap2)
        await session.flush()

        # Add MCP server to snap2 only
        server = McpServerSnapshot(
            snapshot_id=snap2.id,
            server_name="filesystem",
            command="npx",
            args_json=json.dumps([]),
            env_json=json.dumps({}),
            enabled=True,
        )
        session.add(server)
        await session.commit()

        # Compare
        comparer = EntityDeltaComparer(session)
        delta = await comparer.compare_snapshots(snap1.id, snap2.id)

        assert len(delta.mcp_server_deltas) == 1
        assert delta.mcp_server_deltas[0].change_type == "added"
        assert delta.mcp_server_deltas[0].entity_name == "filesystem"

    await engine.dispose()
```

3. Run tests:
```bash
pytest tests/test_entity_deltas.py -v
```

4. Commit:
```bash
git add src/core/entity_deltas.py tests/test_entity_deltas.py
git commit -m "feat: implement entity delta comparison system"
```

---

### Phase 4-6: REST API, UI, and Documentation

(Continued in next section - omitting for brevity, but follows same pattern)

---

## File Dependency Map

This map shows which files depend on which, to help with parallelization:

```
Independent:
├─ src/core/entities.py (no deps)
└─ tests/test_entities.py

Depends on entities.py:
├─ src/core/entity_parser.py
├─ src/core/entity_deltas.py
└─ tests/test_entity_parser.py
└─ tests/test_entity_deltas.py

Depends on all above:
├─ src/core/scanner.py (add entity parsing calls)
├─ src/core/models.py (add entity tables)
├─ src/core/database.py (auto-create tables)
└─ src/api/routes/entities.py (expose queries)

Last:
├─ static/ (React components)
├─ CLAUDE.md (update docs)
└─ README.md (highlight features)
```

---

## Testing Strategy

### Unit Tests (Run First)
```bash
# Test entity models
pytest tests/test_entities.py -v

# Test parser
pytest tests/test_entity_parser.py -v

# Test deltas
pytest tests/test_entity_deltas.py -v

# Run all unit tests
pytest tests/ -v --cov=src
```

### Integration Tests (Run After Scanner Integration)
```bash
# Create a real snapshot and verify entities were parsed
pytest tests/test_scanner.py::test_snapshot_with_entities -v
```

### Smoke Tests (Run After API Integration)
```bash
# Start API and test endpoints
pytest tests/test_api_entities.py -v
```

---

## Documentation Updates Required

### CLAUDE.md Updates
- Add "Phase 2: Entity-Based Snapshots" to Project Status
- Update Architecture section to include entity models
- Add new section: "Entity Query Examples"
- Update Development Workflow with entity parsing notes

### New Docs to Create
- `docs/ENTITIES.md` - Entity model reference
- `docs/ENTITY-QUERIES.md` - Query patterns and examples
- `docs/MIGRATION-GUIDE.md` - How existing snapshots get entity backfill

### README.md Updates
- Add "Entity Timeline Queries" to features list
- Add "Selective Restoration" to features list
- Include example: "Show me every version of my 'filesystem' MCP server"

---

## Implementation Execution Options

Once ready to code:

**Option 1: Subagent-Driven (Recommended)**
- I dispatch fresh subagent per task
- Code review between tasks
- Handles all phases in this session
- Estimated: 4-5 focused sessions

**Option 2: Parallel Session**
- Open new session in separate window
- Batch multiple tasks per session
- Fewer interruptions but less checkpoint verification
- Estimated: 2-3 intense sessions

**Which would you prefer?**

---

## Success Criteria

**Phase 1 Complete When:**
- ✅ Entity dataclasses defined and tested
- ✅ Entity SQLAlchemy models added to database
- ✅ Database initialization includes new tables

**Phase 2 Complete When:**
- ✅ EntityParser successfully extracts all entity types
- ✅ Parser tests pass for edge cases (missing files, malformed JSON)
- ✅ Scanner integration tested with real snapshot

**Phase 3 Complete When:**
- ✅ EntityDeltaComparer detects all change types (add/remove/modify)
- ✅ Delta queries return correct results
- ✅ Integration tests verify snapshot-to-snapshot comparisons

**Phase 4 Complete When:**
- ✅ REST API endpoints operational
- ✅ Entity queries performant (< 500ms)
- ✅ API tests pass with 100% coverage

**Phase 5 Complete When:**
- ✅ UI renders snapshots with entity tabs
- ✅ Entity timeline visualization works
- ✅ Delta viewer shows side-by-side comparisons

**Phase 6 Complete When:**
- ✅ All documentation updated
- ✅ CLAUDE.md reflects new architecture
- ✅ Migration guide written for existing databases
- ✅ No obsolete code remaining

---

## Risk Mitigation

### Database Migration Risk
**Risk:** Existing databases don't have entity tables
**Mitigation:**
1. Alembic migration script to add tables
2. Backfill script to parse entities from existing snapshots
3. Fallback: Fresh database for new installations

### Performance Risk
**Risk:** Entity parsing slows down snapshot creation
**Mitigation:**
1. Entity parsing happens async after snapshot commit
2. Profile before/after
3. Cache entity hashes to avoid re-parsing identical configs

### API Compatibility Risk
**Risk:** New endpoints break existing integrations
**Mitigation:**
1. Version API endpoints (`/api/v1/entities`)
2. Legacy endpoints still work
3. Clear deprecation path

---

## Next Steps (In Order)

1. **Review this document** - Make sure approach makes sense
2. **Choose execution option** - Subagent-driven or parallel
3. **Start Phase 1** - Entity models and dataclasses
4. **Test thoroughly** - Each phase has clear success criteria
5. **Commit frequently** - After each task, before moving to next
6. **Document as you go** - Update CLAUDE.md in parallel with code

---

**Created:** 2025-11-19
**Phase:** Planning Complete - Ready for Implementation
**Estimated Total Effort:** 4 weeks
**Start Date:** [When approved]
