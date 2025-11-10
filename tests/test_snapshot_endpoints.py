"""
Test script for snapshot API endpoints.

Tests all snapshot CRUD operations, tag management, and annotations.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


async def test_snapshot_endpoints():
    """Test snapshot endpoints."""
    from httpx import AsyncClient
    from src.api.app import app
    from src.core.database import init_database, close_database
    from src.core.config import get_settings

    print("\n" + "=" * 60)
    print("Testing Snapshot API Endpoints")
    print("=" * 60 + "\n")

    settings = get_settings()

    # Initialize database
    print("[SETUP] Initializing database...")
    await init_database(settings.database_url, echo=False)
    print("[OK] Database initialized\n")

    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Test 1: Health check
            print("[TEST 1] Health Check")
            response = await client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            print(f"[OK] Health check passed: {data}")
            print()

            # Test 2: Create snapshot
            print("[TEST 2] Create Snapshot")
            create_data = {
                "trigger_type": "api",
                "triggered_by": "test_user@example.com",
                "notes": "Test snapshot for API testing",
                "tags": ["test", "api", "development"],
                "include_content": True,
                "detect_changes": True,
            }
            response = await client.post("/api/v1/snapshots", json=create_data)
            assert response.status_code == 201
            snapshot = response.json()
            snapshot_id = snapshot["snapshot_id"]
            print(f"[OK] Snapshot created: ID={snapshot_id}")
            print(f"     Hash: {snapshot['snapshot_hash'][:16]}...")
            print(f"     Time: {snapshot['snapshot_time']}")
            print()

            # Test 3: List snapshots
            print("[TEST 3] List Snapshots")
            response = await client.get("/api/v1/snapshots?page=1&page_size=10")
            assert response.status_code == 200
            snapshots = response.json()
            print(f"[OK] Found {snapshots['total']} snapshots")
            print(f"     Page: {snapshots['page']}/{snapshots['total_pages']}")
            print(f"     Items on page: {len(snapshots['items'])}")
            print()

            # Test 4: Get snapshot details
            print("[TEST 4] Get Snapshot Details")
            response = await client.get(f"/api/v1/snapshots/{snapshot_id}")
            assert response.status_code == 200
            details = response.json()
            print(f"[OK] Snapshot {snapshot_id} details retrieved")
            print(
                f"     Trigger: {details['trigger_type']} by {details['triggered_by']}")
            print(f"     Tags: {details['tags']}")
            print(f"     Notes: {details['notes']}")
            print()

            # Test 5: Get snapshot stats
            print("[TEST 5] Get Snapshot Statistics")
            response = await client.get(f"/api/v1/snapshots/{snapshot_id}/stats")
            assert response.status_code == 200
            stats = response.json()
            print(f"[OK] Snapshot {snapshot_id} statistics:")
            print(f"     Files: {stats['files_found']}")
            print(f"     Directories: {stats['directories_found']}")
            print(f"     Tags: {stats['tags_count']}")
            print(f"     Annotations: {stats['annotations_count']}")
            print()

            # Test 6: Add tag
            print("[TEST 6] Add Tag to Snapshot")
            tag_data = {
                "tag_name": "production",
                "tag_type": "environment",
                "description": "Production deployment snapshot",
                "created_by": "test_user",
            }
            response = await client.post(
                f"/api/v1/snapshots/{snapshot_id}/tags",
                json=tag_data
            )
            assert response.status_code == 201
            tag = response.json()
            tag_id = tag["id"]
            print(f"[OK] Tag added: '{tag['tag_name']}' (ID={tag_id})")
            print(f"     Type: {tag['tag_type']}")
            print(f"     Description: {tag['description']}")
            print()

            # Test 7: Add annotation
            print("[TEST 7] Add Annotation to Snapshot")
            annotation_data = {
                "annotation_text": "This is a test annotation for documentation purposes.",
                "annotation_type": "note",
                "created_by": "test_user",
            }
            response = await client.post(
                f"/api/v1/snapshots/{snapshot_id}/annotations",
                json=annotation_data
            )
            assert response.status_code == 201
            annotation = response.json()
            annotation_id = annotation["id"]
            print(f"[OK] Annotation added (ID={annotation_id})")
            print(f"     Type: {annotation['annotation_type']}")
            print(f"     Text: {annotation['annotation_text'][:50]}...")
            print()

            # Test 8: List snapshots with filters
            print("[TEST 8] List Snapshots with Filters")
            response = await client.get(
                "/api/v1/snapshots?trigger_type=api&search=test"
            )
            assert response.status_code == 200
            filtered = response.json()
            print(f"[OK] Found {filtered['total']} snapshots matching filters")
            print(f"     Filter: trigger_type=api, search=test")
            print()

            # Test 9: Remove annotation
            print("[TEST 9] Remove Annotation")
            response = await client.delete(
                f"/api/v1/snapshots/{snapshot_id}/annotations/{annotation_id}"
            )
            assert response.status_code == 200
            result = response.json()
            print(f"[OK] {result['message']}")
            print()

            # Test 10: Remove tag
            print("[TEST 10] Remove Tag")
            response = await client.delete(
                f"/api/v1/snapshots/{snapshot_id}/tags/{tag_id}"
            )
            assert response.status_code == 200
            result = response.json()
            print(f"[OK] {result['message']}")
            print()

            # Test 11: Delete snapshot
            print("[TEST 11] Delete Snapshot")
            response = await client.delete(f"/api/v1/snapshots/{snapshot_id}")
            assert response.status_code == 200
            result = response.json()
            print(f"[OK] {result['message']}")
            print()

            # Test 12: Verify deletion
            print("[TEST 12] Verify Snapshot Deletion")
            response = await client.get(f"/api/v1/snapshots/{snapshot_id}")
            assert response.status_code == 404
            error = response.json()
            print(f"[OK] Snapshot not found (as expected)")
            print(f"     Error: {error['error']}")
            print()

            print("=" * 60)
            print("[SUCCESS] All 12 tests passed!")
            print("=" * 60 + "\n")

    finally:
        # Cleanup
        print("[CLEANUP] Closing database...")
        await close_database()
        print("[OK] Database closed\n")


def main():
    """Run tests."""
    try:
        asyncio.run(test_snapshot_endpoints())
    except Exception as e:
        print(f"\n[FAIL] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
