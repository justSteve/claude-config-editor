# Quick Reference: Files to Remove/Archive

## 🗑️ DELETE THESE FILES IMMEDIATELY (13 files)

**Deprecated Scripts (replaced by CLI):**
- `windows_scan.py`
- `create_snapshot.py`
- `inspect_db.py`
- `generate_html_report.py`

**Generated Output Files:**
- `change_report.json`
- `snapshot_report.json`
- `scan_results.json`
- `windowsPaths.txt`
- `index.html`
- `comprehensive_report.html`

**Test Files (move or delete):**
- `test_api_startup.py`

---

## 📦 CONSOLIDATE/MOVE (5 files)

Consider moving to `tests/` directory or deleting if pytest suite covers them:
- `quick_test.py`
- `test_api.py`
- `test_reports.py`
- `test_snapshot_endpoints.py`

---

## 📚 ARCHIVE OLD DOCS (25+ files)

Move to `archived-docs/` or delete if not needed for historical reference:

**Phase 3 Documentation (9 files):**
- `PHASE-3-COMPLETE.md`
- `phase-3-core-refactoring-plan.md`
- `phase-3-progress-summary.md`
- `phase-3-task-1-summary.md`
- `phase-3-task-3-summary.md`
- `phase-3-task-4-summary.md`
- `phase-3-task-5-summary.md`

**Phase 4 Documentation (4 files):**
- `phase-4-cli-enhancement-plan.md`
- `phase-4-progress-summary.md`
- `PHASE-4-PROGRESS-UPDATE.md`
- `phase-4-task-1-2-summary.md`

**Consolidation/Documentation Markers (4 files):**
- `CONSOLIDATION-COMPLETE.md`
- `DOCUMENTATION-COMPLETE.md`
- `DOCUMENTATION-CONSOLIDATION-SUMMARY.md`
- `TASK_3.4_COMPLETE.md`
- `PHASE_5_TASK_2_COMPLETE.md`

**Planning/Summary Files (4 files):**
- `PLANNING-DOCUMENT-UPDATE.md`
- `PLANNING-UPDATE-SUMMARY.md`
- `session-summary-path-clarity-improvements.md`
- `session-summary-system-paths-gui.md`
- `session-summary-windows-path-implementation.md`

---

## ⚠️ REVIEW BEFORE DELETING

These may still be useful - check before deleting:
- `QUICKSTART.md` - Compare with README.md
- `CLAUDE.md` - Check purpose
- `API-TEST-RESULTS.md` - May be useful reference
- `API-TESTING-GUIDE.md` - May be current guide
- `QUICK-START-GUIDE.md` - Duplicate of QUICKSTART.md?
- `README-DOCS.md` - Duplicate of doc/README.md?
- `DOCUMENTATION-INDEX.md` - Check if current
- Marketing and analysis docs (if you want to keep them)

---

## ✅ USE THESE COMMANDS

### Quick verification (check for references before deleting):
```bash
# Example - check if windows_scan.py is referenced anywhere
grep -r "windows_scan" src/ --include="*.py"
grep -r "create_snapshot.py" src/ --include="*.py"
```

### Safe to delete:
```bash
rm -f windows_scan.py create_snapshot.py inspect_db.py generate_html_report.py
rm -f change_report.json snapshot_report.json scan_results.json windowsPaths.txt
rm -f index.html comprehensive_report.html test_api_startup.py
```

### Archive old documentation:
```bash
mkdir -p archived-docs
mv doc/PHASE-3-*.md archived-docs/
mv doc/PHASE-4-*.md archived-docs/
mv doc/phase-3-*.md archived-docs/
mv doc/phase-4-*.md archived-docs/
mv doc/session-summary-*.md archived-docs/
mv PHASE_5_TASK_2_COMPLETE.md archived-docs/
mv TASK_3.4_COMPLETE.md archived-docs/
```

---

**See `UNUSED_FILES_ANALYSIS.md` for detailed analysis with reasons and recommendations.**
