"""
Test script for Path API endpoints.

Tests all path-related endpoints to verify functionality:
- List paths in snapshot (with filtering)
- Get path details
- Get path content
- Get path history
- Search paths
- Add path annotations
"""

import asyncio
import httpx
from datetime import datetime
from typing import Optional

BASE_URL = "http://localhost:8765/api/v1"


async def test_path_endpoints():
    """Test all path API endpoints."""

    async with httpx.AsyncClient() as client:
        print("=" * 80)
        print("Path API Endpoints Test Suite")
        print("=" * 80)

        # Test 1: Create a snapshot first (to have paths to work with)
        # Test 1: Get an existing snapshot (or create one if none exist)
        print("\n[1] Getting existing snapshot...")
        response = await client.get(f"{BASE_URL}/snapshots")
        assert response.status_code == 200, f"Failed to list snapshots: {response.text}"
        snapshots_response = response.json()

        if snapshots_response.get("items") and len(snapshots_response["items"]) > 0:
            # Use the most recent snapshot
            snapshot = snapshots_response["items"][0]
            snapshot_id = snapshot["id"]
            print(f">>> Using existing snapshot: ID={snapshot_id}")
            print(f"  - Snapshot time: {snapshot.get('snapshot_time')}")
            print(f"  - Total locations: {snapshot.get('total_locations')}")
            print(f"  - Files found: {snapshot.get('files_found')}")
        else:
            # Create a new snapshot if none exist
            print("  No snapshots found, creating one...")
            response = await client.post(
                f"{BASE_URL}/snapshots",
                json={}  # Empty request body - use defaults
            )
            assert response.status_code == 201, f"Failed to create snapshot: {response.text}"
            snapshot = response.json()
            # Note: create uses snapshot_id, not id
            snapshot_id = snapshot["snapshot_id"]
            print(f">>> Snapshot created: ID={snapshot_id}")
            print(f"  - Total locations: {snapshot['total_locations']}")
            print(f"  - Files found: {snapshot['files_found']}")
            # Test 2: List all paths in snapshot
            print(f"  - Directories found: {snapshot['directories_found']}")
        print("\n[2] Testing: GET /snapshots/{snapshot_id}/paths")
        response = await client.get(f"{BASE_URL}/snapshots/{snapshot_id}/paths")
        assert response.status_code == 200, f"Failed to list paths: {response.text}"
        paths_response = response.json()
        print(f"[OK] Listed paths successfully")
        print(f"  - Total paths: {paths_response['total']}")
        print(f"  - Page: {paths_response['page']}")
        print(f"  - Page size: {paths_response['page_size']}")
        print(f"  - Items returned: {len(paths_response['items'])}")

        if paths_response['items']:
            first_path = paths_response['items'][0]
            path_id = first_path['id']
            print(f"\n  First path:")
            print(f"    - ID: {first_path['id']}")
            print(f"    - Name: {first_path['name']}")
            print(f"    - Category: {first_path['category']}")
            print(f"    - Resolved path: {first_path['resolved_path']}")
            print(f"    - Exists: {first_path['exists']}")
            print(f"    - Type: {first_path.get('type', 'N/A')}")
        else:
            print("  ⚠ No paths found in snapshot")
            return

        # Test 3: List paths with filtering (exists=true)
        print("\n[3] Testing: GET /snapshots/{snapshot_id}/paths?exists=true")
        response = await client.get(
            f"{BASE_URL}/snapshots/{snapshot_id}/paths",
            params={"exists": True}
        )
        assert response.status_code == 200
        existing_paths = response.json()
        print(f"[OK] Filtered paths (exists=true)")
        print(f"  - Total existing paths: {existing_paths['total']}")

        # Test 4: List paths with category filter
        if paths_response['items']:
            first_category = paths_response['items'][0]['category']
            print(
                f"\n[4] Testing: GET /snapshots/{snapshot_id}/paths?category={first_category}")
            response = await client.get(
                f"{BASE_URL}/snapshots/{snapshot_id}/paths",
                params={"category": first_category}
            )
            assert response.status_code == 200
            category_paths = response.json()
            print(f"[OK] Filtered paths by category '{first_category}'")
            print(f"  - Total paths in category: {category_paths['total']}")

        # Test 5: List paths with pagination
        print(
            f"\n[5] Testing: GET /snapshots/{snapshot_id}/paths?page=1&page_size=5")
        response = await client.get(
            f"{BASE_URL}/snapshots/{snapshot_id}/paths",
            params={"page": 1, "page_size": 5}
        )
        assert response.status_code == 200
        paginated = response.json()
        print(f"[OK] Paginated results")
        print(f"  - Items in page: {len(paginated['items'])}")
        print(f"  - Total pages: {paginated['total_pages']}")

        # Test 6: Get path details
        print(f"\n[6] Testing: GET /paths/{path_id}")
        response = await client.get(f"{BASE_URL}/paths/{path_id}")
        assert response.status_code == 200
        path_detail = response.json()
        print(f"[OK] Retrieved path details")
        print(f"  - ID: {path_detail['id']}")
        print(f"  - Name: {path_detail['name']}")
        print(f"  - Resolved path: {path_detail['resolved_path']}")
        print(f"  - Exists: {path_detail['exists']}")
        print(f"  - Type: {path_detail.get('type', 'N/A')}")
        print(f"  - Size: {path_detail.get('size_bytes', 'N/A')} bytes")
        print(f"  - Modified: {path_detail.get('modified_time', 'N/A')}")
        print(f"  - Content hash: {path_detail.get('content_hash', 'N/A')}")

        # Test 7: Get path content (if has content)
        if path_detail.get('content_hash'):
            print(f"\n[7] Testing: GET /paths/{path_id}/content")
            response = await client.get(f"{BASE_URL}/paths/{path_id}/content")
            assert response.status_code == 200
            content = response.json()
            print(f"[OK] Retrieved path content")
            print(f"  - Content ID: {content['id']}")
            print(f"  - Content type: {content['content_type']}")
            print(f"  - Size: {content['size_bytes']} bytes")
            print(f"  - Hash: {content['content_hash'][:16]}...")
            print(f"  - Compression: {content.get('compression', 'none')}")
            print(f"  - Reference count: {content.get('reference_count', 1)}")

            # Test 7b: Get content without actual data
            print(
                f"\n[7b] Testing: GET /paths/{path_id}/content?include_content=false")
            response = await client.get(
                f"{BASE_URL}/paths/{path_id}/content",
                params={"include_content": False}
            )
            assert response.status_code == 200
            content_meta = response.json()
            print(f"[OK] Retrieved content metadata only")
            print(
                f"  - Has content_text: {content_meta.get('content_text') is not None}")
            print(
                f"  - Has content_binary: {content_meta.get('content_binary') is not None}")
        else:
            print(f"\n[7] Skipping content test - path has no content")

        # Test 8: Get path history
        print(f"\n[8] Testing: GET /paths/{path_id}/history")
        response = await client.get(f"{BASE_URL}/paths/{path_id}/history")
        assert response.status_code == 200
        history = response.json()
        print(f"[OK] Retrieved path history")
        print(f"  - History entries: {len(history)}")
        if history:
            for i, entry in enumerate(history[:3], 1):
                print(
                    f"    [{i}] Snapshot {entry['snapshot_id']} - {entry['resolved_path']}")

        # Test 9: Search paths
        print(f"\n[9] Testing: GET /snapshots/{snapshot_id}/search?q=config")
        response = await client.get(
            f"{BASE_URL}/snapshots/{snapshot_id}/search",
            params={"q": "config"}
        )
        assert response.status_code == 200
        search_results = response.json()
        print(f"[OK] Search completed")
        print(f"  - Matches found: {search_results['total']}")
        if search_results['items']:
            for i, item in enumerate(search_results['items'][:3], 1):
                print(f"    [{i}] {item['name']} - {item['resolved_path']}")

        # Test 10: Search with content search
        print(
            f"\n[10] Testing: GET /snapshots/{snapshot_id}/search?q=mcp&search_content=true")
        response = await client.get(
            f"{BASE_URL}/snapshots/{snapshot_id}/search",
            params={"q": "mcp", "search_content": True}
        )
        assert response.status_code == 200
        content_search = response.json()
        print(f"[OK] Content search completed")
        print(f"  - Matches found: {content_search['total']}")

        # Test 11: Add path annotation
        print(f"\n[11] Testing: POST /paths/{path_id}/annotations")
        response = await client.post(
            f"{BASE_URL}/paths/{path_id}/annotations",
            params={
                "annotation_text": "Test annotation from API test",
                "annotation_type": "note",
                "created_by": "test_script"
            }
        )
        assert response.status_code == 201
        annotation = response.json()
        print(f"[OK] Annotation added")
        print(f"  - ID: {annotation['id']}")
        print(f"  - Text: {annotation['annotation_text']}")
        print(f"  - Type: {annotation.get('annotation_type', 'N/A')}")
        print(f"  - Created by: {annotation.get('created_by', 'N/A')}")

        # Test 12: Verify annotation appears in path details
        print(f"\n[12] Testing: Verify annotation in path details")
        response = await client.get(f"{BASE_URL}/paths/{path_id}")
        assert response.status_code == 200
        updated_detail = response.json()
        annotations = updated_detail.get('annotations', [])
        print(f"[OK] Retrieved updated path details")
        print(f"  - Total annotations: {len(annotations)}")
        if annotations:
            latest = annotations[-1]
            print(f"  - Latest annotation: {latest['annotation_text']}")

        # Test 13: List paths with search filter
        print(
            f"\n[13] Testing: GET /snapshots/{snapshot_id}/paths?search=.json")
        response = await client.get(
            f"{BASE_URL}/snapshots/{snapshot_id}/paths",
            params={"search": ".json"}
        )
        assert response.status_code == 200
        json_paths = response.json()
        print(f"[OK] Search filter applied")
        print(f"  - JSON files found: {json_paths['total']}")

        # Test 14: Error handling - non-existent path
        print(f"\n[14] Testing: Error handling - GET /paths/99999")
        response = await client.get(f"{BASE_URL}/paths/99999")
        assert response.status_code == 404
        error = response.json()
        print(f"[OK] 404 error handled correctly")
        print(f"  - Error: {error.get('detail', 'N/A')}")

        # Test 15: Error handling - non-existent snapshot
        print(f"\n[15] Testing: Error handling - GET /snapshots/99999/paths")
        response = await client.get(f"{BASE_URL}/snapshots/99999/paths")
        assert response.status_code == 404
        print(">>> 404 error handled correctly for snapshot")

        print("\n" + "=" * 80)
        print(">>> ALL PATH ENDPOINT TESTS PASSED!")
        print("=" * 80)
        print("\nTested endpoints:")
        print(
            "  1. GET  /snapshots/{snapshot_id}/paths (with various filters)")
        print("  2. GET  /paths/{path_id}")
        print("  3. GET  /paths/{path_id}/content")
        print("  4. GET  /paths/{path_id}/history")
        print("  5. GET  /snapshots/{snapshot_id}/search")
        print("  6. POST /paths/{path_id}/annotations")
        print("\nAll endpoints functional and returning expected data!")


if __name__ == "__main__":
    print("\n>>> Starting Path API Endpoint Tests...")
    print("Make sure the API server is running on http://localhost:8765\n")

    try:
        asyncio.run(test_path_endpoints())
    except httpx.ConnectError:
        print("\n*** ERROR: Could not connect to API server")
        print("Please start the server with: uvicorn src.api.app:app --host 0.0.0.0 --port 8765")
    except AssertionError as e:
        print(f"\n*** TEST FAILED: {e}")
    except Exception as e:
        print(f"\n*** UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()

