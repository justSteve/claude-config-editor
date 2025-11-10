# Task #10: Claude Config Endpoints - Detailed Scope

**Date**: 2025-11-10
**Status**: Not Started
**Priority**: Medium
**Estimated Duration**: 1.5 days
**Phase**: 5 (API Enhancement)

---

## 📋 Overview

Implement REST API endpoints to query and analyze Claude configuration files across snapshots, with focus on tracking configuration changes over time for content (not metadata).

---

## 🎯 Objectives

1. **Query Claude configs** - List and retrieve Claude configuration metadata from snapshots
2. **Track changes** - Compare configurations across snapshots to show what changed
3. **Content focus** - Track actual project/MCP content bodies, not just metadata
4. **Enable analysis** - Provide data for identifying bloat and cleanup candidates

---

## 📊 Current State Analysis

### ✅ What Exists

**Database Models** (`src/core/models.py`):
- `ClaudeConfig` - Stores config metadata (num_projects, num_mcp_servers, sizes)
- `McpServer` - Stores MCP server configurations
- `JsonData` - Stores parsed JSON structures from configs

**Schemas** (`src/core/schemas/paths.py`):
- `ClaudeConfigResponse` - Response schema for config data
- `McpServerResponse` - Response schema for MCP servers

**Related Files**:
- `src/api/routes/snapshots.py` - Existing snapshot endpoints (reference pattern)
- `src/api/services/snapshot_service.py` - Existing service layer (reference pattern)

### ❌ What's Missing

**API Routes**:
- No `claude_config.py` routes file
- No endpoints implemented

**Services**:
- No `ClaudeConfigService` class
- No business logic for config queries
- No change detection logic

**Schemas** (likely missing):
- No `ClaudeConfigListResponse` for listing configs
- No `ClaudeConfigDetailResponse` for detailed view
- No `ClaudeConfigChangeResponse` for comparing configs
- No comparison/diff schemas

**Scanner Integration**:
- Unknown if scanner populates `ClaudeConfig` table
- Unknown if scanner extracts project/MCP bodies into `JsonData`
- May need scanner enhancements to parse `.claude.json` structure

---

## 🔨 Implementation Scope

### Part 1: API Endpoints (Required)

**File**: `src/api/routes/claude_config.py`

```python
# Endpoints to implement:
GET  /api/v1/snapshots/{snapshot_id}/claude-configs        # List configs in snapshot
GET  /api/v1/claude-configs/{config_id}                    # Get config details
GET  /api/v1/claude-configs/{config_id}/compare/{other_id} # Compare two configs
GET  /api/v1/snapshots/{snapshot_id}/claude-configs/summary # Config summary stats
```

**Key Features**:
- List all Claude configs found in a snapshot
- Get detailed config info (metadata + content preview)
- Compare two configs showing body changes (not metadata)
- Summary statistics across all configs in snapshot

### Part 2: Service Layer (Required)

**File**: `src/api/services/claude_config_service.py`

```python
class ClaudeConfigService:
    async def list_configs(snapshot_id, filters) -> list[ClaudeConfigSummary]
    async def get_config_detail(config_id) -> ClaudeConfigDetail
    async def compare_configs(config_id_1, config_id_2) -> ConfigComparison
    async def get_config_summary(snapshot_id) -> ConfigSummaryStats
```

**Business Logic**:
- Query configs by snapshot
- Filter by config type (desktop, project, enterprise)
- Load related data (projects, MCP servers, sizes)
- Compute differences between configs
- Generate summary statistics

### Part 3: Enhanced Schemas (Required)

**File**: `src/core/schemas/claude_config.py` (new)

```python
# Summary for lists
class ClaudeConfigSummary(BaseSchema):
    id: int
    config_type: str
    num_projects: int
    num_mcp_servers: int
    total_size_bytes: int
    snapshot_id: int
    snapshot_time: datetime

# Detailed view
class ClaudeConfigDetail(ClaudeConfigSummary):
    largest_project_path: str
    largest_project_size: int
    projects_preview: list[str]  # First 10 project names
    mcp_servers_preview: list[str]  # MCP server names
    content_sample: str  # First 500 chars of content

# Comparison view
class ClaudeConfigComparison(BaseSchema):
    config_1: ClaudeConfigSummary
    config_2: ClaudeConfigSummary
    differences: ConfigDifferences

class ConfigDifferences(BaseSchema):
    projects_added: int
    projects_removed: int
    projects_modified: list[str]  # Project paths that changed
    mcp_servers_added: int
    mcp_servers_removed: int
    mcp_servers_modified: list[str]
    size_change_bytes: int
    size_change_percent: float

# Summary stats
class ConfigSummaryStats(BaseSchema):
    total_configs: int
    config_types: dict[str, int]  # {desktop: 1, project: 3}
    total_projects: int
    total_mcp_servers: int
    total_size_bytes: int
    largest_config_type: str
    bloat_candidates: list[ClaudeConfigSummary]  # Configs > 1MB
```

### Part 4: Scanner Integration (If Needed)

**Unknown Status**: Need to verify if scanner already:
1. Populates `ClaudeConfig` table with metadata
2. Extracts project/MCP content into `JsonData` table
3. Links configs to snapshot_paths

**If scanner doesn't do this**, need to add:
- Parse `.claude.json` files when scanning
- Extract project list and sizes
- Extract MCP server list
- Store in `ClaudeConfig` and `JsonData` tables

**File to Modify**: `src/core/scanner.py`
- Add `.claude.json` detection logic
- Add JSON parsing and extraction
- Add database insertion for `ClaudeConfig`

---

## 📋 Detailed Task Breakdown

### Task 10.1: Investigate Scanner Status (0.25 days)

**Objective**: Determine if scanner already populates Claude config data

**Steps**:
1. Search scanner.py for "ClaudeConfig" or ".claude.json"
2. Check if `ClaudeConfig` table has data in test database
3. Review `JsonData` table structure and usage
4. Document findings

**Decision Point**:
- ✅ If scanner works → Skip to Task 10.3
- ❌ If scanner incomplete → Do Task 10.2 first

### Task 10.2: Enhance Scanner (If Needed) (0.5 days)

**Objective**: Make scanner extract Claude config metadata

**Files**:
- `src/core/scanner.py` - Add config extraction

**Implementation**:
- Detect `.claude.json` files during scan
- Parse JSON to count projects, MCP servers
- Calculate sizes and identify largest project
- Insert into `ClaudeConfig` table
- Link to `SnapshotPath`

**Validation**:
- Run scanner on test config
- Verify `ClaudeConfig` table populated
- Verify counts match actual JSON structure

### Task 10.3: Create Schemas (0.25 days)

**Objective**: Define response schemas for API

**Files**:
- `src/core/schemas/claude_config.py` (new)
- `src/core/schemas/__init__.py` (update exports)

**Schemas to Create**:
- `ClaudeConfigSummary` - List view
- `ClaudeConfigDetail` - Detail view
- `ClaudeConfigComparison` - Comparison view
- `ConfigDifferences` - Change details
- `ConfigSummaryStats` - Aggregate stats

**Validation**:
- Import schemas without errors
- Pydantic validation works on sample data

### Task 10.4: Create Service Layer (0.25 days)

**Objective**: Implement business logic

**Files**:
- `src/api/services/claude_config_service.py` (new)
- `src/api/services/__init__.py` (update exports)

**Methods to Implement**:
- `list_configs()` - Query with filters
- `get_config_detail()` - Load full details
- `compare_configs()` - Compute differences
- `get_config_summary()` - Aggregate stats

**Validation**:
- Unit tests for each method
- Test with real database data
- Verify query performance

### Task 10.5: Create API Endpoints (0.25 days)

**Objective**: Expose REST API

**Files**:
- `src/api/routes/claude_config.py` (new)
- `src/api/routes/__init__.py` (update router registration)
- `src/api/app.py` (register routes)

**Endpoints**:
- `GET /snapshots/{id}/claude-configs` - List
- `GET /claude-configs/{id}` - Details
- `GET /claude-configs/{id}/compare/{other}` - Compare
- `GET /snapshots/{id}/claude-configs/summary` - Stats

**Validation**:
- Test each endpoint with Postman/httpx
- Verify response schemas
- Check error handling (404, 400)

---

## 🧪 Testing Strategy

### Unit Tests
- Schema validation tests
- Service method tests with mock data
- Change detection algorithm tests

### Integration Tests
- API endpoint tests with test database
- Scanner integration tests (if modified)
- End-to-end config retrieval tests

### Manual Testing
- Create test snapshots with various configs
- Test filtering and sorting
- Test comparison with actual config changes
- Verify performance with large configs

---

## ✅ Success Criteria

1. **API Functional**
   - All 4 endpoints working
   - Proper error handling (404, 400, 500)
   - Response times < 500ms

2. **Data Accuracy**
   - Config metadata matches actual files
   - Change detection finds all differences
   - Size calculations accurate

3. **Code Quality**
   - Type hints throughout
   - Docstrings on all public methods
   - Follows existing patterns (snapshots routes/service)

4. **Documentation**
   - OpenAPI docs auto-generated
   - Examples in docstrings
   - This scope doc updated with completion status

---

## 📦 Deliverables

### Code Files (4-5 files)
1. `src/api/routes/claude_config.py` (~200-300 lines)
2. `src/api/services/claude_config_service.py` (~250-350 lines)
3. `src/core/schemas/claude_config.py` (~150-200 lines)
4. `src/core/scanner.py` (modifications if needed, ~50-100 lines)
5. Tests (if time permits)

### Documentation
1. This scope document (updated with completion notes)
2. OpenAPI documentation (auto-generated)
3. Testing notes

### Total Estimate
- **Investigation**: 0.25 days
- **Scanner (conditional)**: 0-0.5 days
- **Schemas**: 0.25 days
- **Service**: 0.25 days
- **Routes**: 0.25 days
- **Testing**: included in each
- **TOTAL**: 1.0-1.5 days

---

## 🔗 Dependencies

### Required Before Starting
- ✅ Phase 5 Task 1 complete (FastAPI setup)
- ✅ Phase 5 Task 2 complete (Snapshot endpoints as reference)
- ✅ Database models exist (`ClaudeConfig`, `JsonData`)

### Blocks
- None (standalone task)

### Unblocks
- Task 9 (MCP endpoints) - can share service patterns
- Task 8 (Change tracking) - can reuse comparison logic

---

## 📝 Open Questions

1. **Scanner Status**: Does it already populate `ClaudeConfig`? → **NEEDS INVESTIGATION**

2. **JsonData Usage**: Is this table being used for project/MCP content? → **NEEDS INVESTIGATION**

3. **Change Detection**: Should we store comparison results or compute on-demand? → **Recommend compute on-demand for MVP**

4. **Content Preview**: How much content to show in detail view? → **Recommend 500 chars max + "..." with full content available separately**

5. **Filtering**: What filters do we need on list endpoint? → **Recommend: config_type, min_projects, min_size**

---

## 🚀 Next Steps

1. **Immediate**: Investigate scanner status (Task 10.1)
2. **Then**: Either enhance scanner or proceed to schemas
3. **Finally**: Implement service → routes → test

---

**Document Created**: 2025-11-10
**Author**: Claude (AI Assistant)
**Related Tasks**: Phase 5, Task 10
**Status**: Ready for implementation after investigation
