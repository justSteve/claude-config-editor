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

### 4. Test API

```bash
# Quick test
python quick_test.py

# Or use Swagger UI
# Open: http://localhost:8765/docs
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

