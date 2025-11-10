"""
Quick test script for the Claude Config API.

Tests the main endpoints to verify the API is working correctly.
"""

import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8765/api/v1"


def print_response(title: str, response: requests.Response) -> None:
    """Print a formatted API response."""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    try:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
    except:
        print(f"Response: {response.text}")


def test_health_check() -> bool:
    """Test the health check endpoint."""
    print("\n🔍 Testing Health Check...")
    try:
        response = requests.get("http://localhost:8765/health")
        print_response("Health Check", response)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_create_snapshot() -> Dict[str, Any] | None:
    """Test creating a snapshot."""
    print("\n🔍 Testing Create Snapshot...")
    try:
        response = requests.post(
            f"{BASE_URL}/snapshots",
            json={
                "trigger_type": "api",
                "triggered_by": "test-user",
                "notes": "API test snapshot",
                "tags": ["test", "api"]
            }
        )
        print_response("Create Snapshot", response)

        if response.status_code == 201:
            return response.json()
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def test_list_snapshots() -> bool:
    """Test listing snapshots."""
    print("\n🔍 Testing List Snapshots...")
    try:
        response = requests.get(
            f"{BASE_URL}/snapshots",
            params={"page": 1, "page_size": 10}
        )
        print_response("List Snapshots", response)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_get_snapshot(snapshot_id: int) -> bool:
    """Test getting a snapshot by ID."""
    print(f"\n🔍 Testing Get Snapshot {snapshot_id}...")
    try:
        response = requests.get(f"{BASE_URL}/snapshots/{snapshot_id}")
        print_response(f"Get Snapshot {snapshot_id}", response)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_get_snapshot_stats(snapshot_id: int) -> bool:
    """Test getting snapshot statistics."""
    print(f"\n🔍 Testing Get Snapshot Stats {snapshot_id}...")
    try:
        response = requests.get(f"{BASE_URL}/snapshots/{snapshot_id}/stats")
        print_response(f"Snapshot Stats {snapshot_id}", response)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_add_tag(snapshot_id: int) -> bool:
    """Test adding a tag to a snapshot."""
    print(f"\n🔍 Testing Add Tag to Snapshot {snapshot_id}...")
    try:
        response = requests.post(
            f"{BASE_URL}/snapshots/{snapshot_id}/tags",
            json={
                "tag_name": "test-tag",
                "tag_type": "test",
                "description": "Test tag from API",
                "created_by": "test-user"
            }
        )
        print_response(f"Add Tag to Snapshot {snapshot_id}", response)
        return response.status_code == 201
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_list_annotations(snapshot_id: int) -> bool:
    """Test listing annotations for a snapshot."""
    print(f"\n🔍 Testing List Annotations for Snapshot {snapshot_id}...")
    try:
        response = requests.get(
            f"{BASE_URL}/snapshots/{snapshot_id}/annotations")
        print_response(
            f"List Annotations for Snapshot {snapshot_id}", response)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_add_annotation(snapshot_id: int) -> bool:
    """Test adding an annotation to a snapshot."""
    print(f"\n🔍 Testing Add Annotation to Snapshot {snapshot_id}...")
    try:
        response = requests.post(
            f"{BASE_URL}/snapshots/{snapshot_id}/annotations",
            json={
                "annotation_text": "This is a test annotation from the API",
                "annotation_type": "note",
                "created_by": "test-user"
            }
        )
        print_response(f"Add Annotation to Snapshot {snapshot_id}", response)
        return response.status_code == 201
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_export_snapshot(snapshot_id: int) -> bool:
    """Test exporting a snapshot."""
    print(f"\n🔍 Testing Export Snapshot {snapshot_id}...")
    try:
        response = requests.post(
            f"{BASE_URL}/snapshots/{snapshot_id}/export",
            params={"format": "json"}
        )
        print_response(f"Export Snapshot {snapshot_id}", response)

        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Export successful!")
            print(f"   - Snapshot ID: {data.get('snapshot', {}).get('id')}")
            print(f"   - Paths: {len(data.get('paths', []))}")
            print(f"   - Tags: {len(data.get('tags', []))}")
            print(f"   - Annotations: {len(data.get('annotations', []))}")
            return True
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all API tests."""
    print("="*60)
    print("Claude Config API Test Suite")
    print("="*60)
    print("\n⚠️  Make sure the API server is running on http://localhost:8765")
    print("   Start it with: uvicorn src.api.app:app --reload")
    print("\nPress Enter to continue...")
    input()

    results = {}

    # Test health check
    results["health"] = test_health_check()

    # Test create snapshot
    snapshot = test_create_snapshot()
    if snapshot:
        snapshot_id = snapshot.get("snapshot_id")
        results["create_snapshot"] = True

        # Test other endpoints with the created snapshot
        results["list_snapshots"] = test_list_snapshots()
        results["get_snapshot"] = test_get_snapshot(snapshot_id)
        results["get_stats"] = test_get_snapshot_stats(snapshot_id)
        results["add_tag"] = test_add_tag(snapshot_id)
        results["add_annotation"] = test_add_annotation(snapshot_id)
        results["list_annotations"] = test_list_annotations(snapshot_id)
        results["export_snapshot"] = test_export_snapshot(snapshot_id)
    else:
        results["create_snapshot"] = False
        print("\n❌ Could not create snapshot. Skipping other tests.")

    # Print summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:30} {status}")

    total = len(results)
    passed = sum(1 for v in results.values() if v)
    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")


if __name__ == "__main__":
    main()
