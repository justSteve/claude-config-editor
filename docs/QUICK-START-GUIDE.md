# Quick Start Guide

**Last Updated**: 2025-11-09  
**Purpose**: Get started quickly with Claude Config Editor

---

## 🚀 Quick Start

### 1. Installation

```bash
# Clone repository (if applicable)
# cd to project directory

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Run configuration wizard
claude-config config init

# Or manually edit config/development.yaml
```

### 3. Start API Server

```bash
# Windows
start_api.bat

# Linux/Mac
./start_api.sh

# Or manually
uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8765
```

### 4. Verify API is Running

```bash
# Check health endpoint
curl http://localhost:8765/health

# Or open Swagger UI
# Open: http://localhost:8765/docs
```

---

## 🎯 Live Usage

### CLI Commands (Recommended)

#### Create Your First Snapshot

```bash
# Create a snapshot of all Claude configurations
python -m src.cli.commands snapshot create

# With notes
python -m src.cli.commands snapshot create --notes "Before cleanup"
```

**Output**: Shows snapshot ID, hash, files found, directories, and scan results.

#### List Snapshots

```bash
# List all snapshots
python -m src.cli.commands snapshot list

# Limit results
python -m src.cli.commands snapshot list --limit 5
```

#### View Snapshot Details

```bash
# Show full details
python -m src.cli.commands snapshot show 1

# Show all scanned paths
python -m src.cli.commands snapshot show 1 --paths

# Show changes from previous snapshot
python -m src.cli.commands snapshot show 1 --changes
```

#### Compare Snapshots

```bash
# Compare snapshot with previous
python -m src.cli.commands snapshot compare 2

# Compare specific snapshots
python -m src.cli.commands snapshot compare 2 --previous 1
```

#### Generate Reports

```bash
# Generate comprehensive snapshot report
python -m src.cli.commands snapshot report 2
```

#### Database Statistics

```bash
# View database statistics
python -m src.cli.commands stats

# View deduplication statistics
python -m src.cli.commands dedup
```

---

### REST API Usage (Advanced)

For programmatic access or integration with other tools, use the REST API directly:

#### Create Snapshot via API

```bash
curl -X POST "http://localhost:8765/api/v1/snapshots" \
  -H "Content-Type: application/json" \
  -d '{
    "trigger_type": "manual",
    "triggered_by": "your-username",
    "notes": "My first snapshot"
  }'
```

#### List Snapshots with Filtering

```bash
# Get all snapshots (paginated)
curl "http://localhost:8765/api/v1/snapshots?page=1&page_size=10"

# Filter by trigger type
curl "http://localhost:8765/api/v1/snapshots?trigger_type=manual"

# Sort by size
curl "http://localhost:8765/api/v1/snapshots?sort_by=total_size_bytes&sort_order=desc"
```

#### Get Snapshot Information

```bash
# Full snapshot details
curl "http://localhost:8765/api/v1/snapshots/1"

# Statistics only
curl "http://localhost:8765/api/v1/snapshots/1/stats"

# All paths in snapshot
curl "http://localhost:8765/api/v1/snapshots/1/paths"
```

#### Tag Management via API

```bash
# Add a tag
curl -X POST "http://localhost:8765/api/v1/snapshots/1/tags" \
  -H "Content-Type: application/json" \
  -d '{
    "tag_name": "production",
    "tag_type": "environment",
    "description": "Production configuration"
  }'

# List tags
curl "http://localhost:8765/api/v1/snapshots/1/tags"

# Remove a tag
curl -X DELETE "http://localhost:8765/api/v1/snapshots/1/tags/1"
```

#### Export Data

```bash
# Export as JSON
curl "http://localhost:8765/api/v1/snapshots/1/export?format=json" > snapshot-1.json
```

---

### Common Workflows

**Daily Backup** (CLI):
```bash
python -m src.cli.commands snapshot create --notes "Start of day"
```

**Before Major Changes** (CLI):
```bash
python -m src.cli.commands snapshot create --notes "Before cleanup"
# Make your changes...
python -m src.cli.commands snapshot create --notes "After cleanup"
python -m src.cli.commands snapshot compare 2
```

**Automated Monitoring** (API):
```bash
# Can be called from scripts, cron jobs, or CI/CD pipelines
curl -X POST "http://localhost:8765/api/v1/snapshots" \
  -H "Content-Type: application/json" \
  -d '{"trigger_type": "automated", "triggered_by": "monitoring-script", "notes": "Hourly backup"}'
```

---

## 📚 Documentation Quick Links

### Essential Documents
- **[Main Planning](./planning-production-upgrade-architecture.md)** - Overall project plan
- **[Review & Test Process](./REVIEW-AND-TEST-PROCESS.md)** - Review and testing procedures
- **[API Testing Guide](./API-TESTING-GUIDE.md)** - How to test the API
- **[Documentation Index](./DOCUMENTATION-INDEX.md)** - All documentation

### By Role
- **Developers**: [Design Document](./design-version-control-system.md), [Phase Plans](./phase-*-plan.md)
- **Testers**: [Review & Test Process](./REVIEW-AND-TEST-PROCESS.md), [API Testing Guide](./API-TESTING-GUIDE.md)
- **Users**: [README.md](./README.md), [API Quick Reference](./phase-5-quick-reference.md)

---

## 🧪 Quick Test

### Test API

```bash
# Start server
uvicorn src.api.app:app --reload

# Run quick test
python quick_test.py
```

### Test CLI

```bash
# Create snapshot
claude-config snapshot create --notes "Test"

# List snapshots
claude-config snapshot list

# Export snapshot
claude-config export snapshot 1 --format json
```

---

## 📖 Next Steps

1. **Read**: [Main Planning Document](./planning-production-upgrade-architecture.md)
2. **Test**: [API Testing Guide](./API-TESTING-GUIDE.md)
3. **Review**: [Review & Test Process](./REVIEW-AND-TEST-PROCESS.md)
4. **Explore**: [Documentation Index](./DOCUMENTATION-INDEX.md)

---

**Last Updated**: 2025-11-09

