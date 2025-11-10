"""
Quick API test - creates a snapshot and tests basic functionality.
"""

import requests
import json
import time

BASE_URL = "http://localhost:8765/api/v1"

print("="*60)
print("Claude Config API - Quick Test")
print("="*60)

# Test 1: Health Check
print("\n1. Testing Health Check...")
try:
    response = requests.get("http://localhost:8765/health", timeout=5)
    if response.status_code == 200:
        print(f"   [OK] Health check passed: {response.json()}")
    else:
        print(f"   [FAIL] Health check failed: {response.status_code}")
        exit(1)
except Exception as e:
    print(f"   [ERROR] Error: {e}")
    print("   [WARNING] Make sure the server is running!")
    print("   Start it with: uvicorn src.api.app:app --reload")
    exit(1)

# Test 2: Create Snapshot
print("\n2. Creating Snapshot...")
try:
    response = requests.post(
        f"{BASE_URL}/snapshots",
        json={
            "trigger_type": "api",
            "triggered_by": "test-user",
            "notes": "Quick API test snapshot",
            "tags": ["test", "quick-test"]
        },
        timeout=30  # Snapshot creation can take a while
    )
    
    if response.status_code == 201:
        snapshot = response.json()
        snapshot_id = snapshot.get("snapshot_id")
        print(f"   [OK] Snapshot created: ID={snapshot_id}")
        print(f"   [INFO] Files: {snapshot.get('files_found')}, Dirs: {snapshot.get('directories_found')}")
        print(f"   [INFO] Size: {snapshot.get('total_size_bytes')} bytes")
        print(f"   [INFO] Hash: {snapshot.get('snapshot_hash')[:16]}...")
    else:
        print(f"   [FAIL] Failed to create snapshot: {response.status_code}")
        print(f"   Response: {response.text}")
        exit(1)
except Exception as e:
    print(f"   [ERROR] Error: {e}")
    exit(1)

# Test 3: List Snapshots
print("\n3. Listing Snapshots...")
try:
    response = requests.get(f"{BASE_URL}/snapshots", params={"page": 1, "page_size": 5}, timeout=5)
    if response.status_code == 200:
        data = response.json()
        print(f"   [OK] Found {data.get('total')} snapshot(s)")
        print(f"   [INFO] Showing {len(data.get('items', []))} on page {data.get('page')}")
    else:
        print(f"   [FAIL] Failed to list snapshots: {response.status_code}")
except Exception as e:
    print(f"   [ERROR] Error: {e}")

# Test 4: Get Snapshot Details
print(f"\n4. Getting Snapshot {snapshot_id} Details...")
try:
    response = requests.get(f"{BASE_URL}/snapshots/{snapshot_id}", timeout=5)
    if response.status_code == 200:
        details = response.json()
        print(f"   [OK] Snapshot details retrieved")
        print(f"   [INFO] Notes: {details.get('notes')}")
        print(f"   [INFO] Tags: {len(details.get('tags', []))} tag(s)")
        print(f"   [INFO] Annotations: {len(details.get('annotations', []))} annotation(s)")
        print(f"   [INFO] Environment: {details.get('os_type')} {details.get('os_version')}")
    else:
        print(f"   [FAIL] Failed to get snapshot details: {response.status_code}")
except Exception as e:
    print(f"   [ERROR] Error: {e}")

# Test 5: Get Statistics
print(f"\n5. Getting Snapshot {snapshot_id} Statistics...")
try:
    response = requests.get(f"{BASE_URL}/snapshots/{snapshot_id}/stats", timeout=5)
    if response.status_code == 200:
        stats = response.json()
        print(f"   [OK] Statistics retrieved")
        print(f"   [INFO] Paths: {stats.get('paths_count')}")
        print(f"   [INFO] Files: {stats.get('files_found')}")
        print(f"   [INFO] Directories: {stats.get('directories_found')}")
        print(f"   [INFO] Tags: {stats.get('tags_count')}")
        print(f"   [INFO] Annotations: {stats.get('annotations_count')}")
    else:
        print(f"   [FAIL] Failed to get statistics: {response.status_code}")
except Exception as e:
    print(f"   [ERROR] Error: {e}")

# Test 6: Add Tag
print(f"\n6. Adding Tag to Snapshot {snapshot_id}...")
try:
    response = requests.post(
        f"{BASE_URL}/snapshots/{snapshot_id}/tags",
        json={
            "tag_name": "quick-test-tag",
            "tag_type": "test",
            "description": "Tag added during quick test",
            "created_by": "test-user"
        },
        timeout=5
    )
    if response.status_code == 201:
        tag = response.json()
        print(f"   [OK] Tag added: {tag.get('tag_name')}")
        tag_id = tag.get('id')
    else:
        print(f"   [FAIL] Failed to add tag: {response.status_code}")
        print(f"   Response: {response.text}")
except Exception as e:
    print(f"   [ERROR] Error: {e}")

# Test 7: Add Annotation
print(f"\n7. Adding Annotation to Snapshot {snapshot_id}...")
try:
    response = requests.post(
        f"{BASE_URL}/snapshots/{snapshot_id}/annotations",
        json={
            "annotation_text": "This is a test annotation from the quick test script",
            "annotation_type": "note",
            "created_by": "test-user"
        },
        timeout=5
    )
    if response.status_code == 201:
        annotation = response.json()
        print(f"   [OK] Annotation added: {annotation.get('annotation_text')[:50]}...")
        annotation_id = annotation.get('id')
    else:
        print(f"   [FAIL] Failed to add annotation: {response.status_code}")
except Exception as e:
    print(f"   [ERROR] Error: {e}")

# Test 8: List Annotations
print(f"\n8. Listing Annotations for Snapshot {snapshot_id}...")
try:
    response = requests.get(f"{BASE_URL}/snapshots/{snapshot_id}/annotations", timeout=5)
    if response.status_code == 200:
        annotations = response.json()
        print(f"   [OK] Found {len(annotations)} annotation(s)")
        for ann in annotations:
            print(f"      - {ann.get('annotation_text')[:50]}...")
    else:
        print(f"   [FAIL] Failed to list annotations: {response.status_code}")
except Exception as e:
    print(f"   [ERROR] Error: {e}")

# Test 9: Export Snapshot
print(f"\n9. Exporting Snapshot {snapshot_id}...")
try:
    response = requests.post(
        f"{BASE_URL}/snapshots/{snapshot_id}/export",
        params={"format": "json"},
        timeout=10
    )
    if response.status_code == 200:
        export_data = response.json()
        print(f"   [OK] Export successful")
        print(f"   [INFO] Version: {export_data.get('version')}")
        print(f"   [INFO] Paths: {len(export_data.get('paths', []))}")
        print(f"   [INFO] Tags: {len(export_data.get('tags', []))}")
        print(f"   [INFO] Annotations: {len(export_data.get('annotations', []))}")
    else:
        print(f"   [FAIL] Failed to export snapshot: {response.status_code}")
except Exception as e:
    print(f"   [ERROR] Error: {e}")

print("\n" + "="*60)
print("[SUCCESS] Quick Test Complete!")
print("="*60)
print(f"\n[INFO] Snapshot ID: {snapshot_id}")
print(f"[INFO] API Docs: http://localhost:8765/docs")
print(f"[INFO] Health: http://localhost:8765/health")
print(f"\n[TIP] You can view the snapshot details at:")
print(f"   http://localhost:8765/api/v1/snapshots/{snapshot_id}")

