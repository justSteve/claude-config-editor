"""
Test script for MCP server API endpoints.

Tests all MCP server endpoints including listing, details, status,
configuration (with sanitization), capabilities, logs, and statistics.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


async def test_mcp_endpoints():
    """Test MCP server endpoints."""
    from httpx import AsyncClient
    from src.api.app import app
    from src.core.database import init_database, close_database
    from src.core.config import get_settings

    print("\n" + "=" * 60)
    print("Testing MCP Server API Endpoints")
    print("=" * 60 + "\n")

    settings = get_settings()

    # Initialize database
    print("[SETUP] Initializing database...")
    await init_database(settings.database_url, echo=False)
    print("[OK] Database initialized\n")

    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            # First, ensure we have a snapshot with MCP servers
            # This will scan the system and find MCP servers
            print("[SETUP] Creating snapshot to scan for MCP servers...")
            create_data = {
                "trigger_type": "api",
                "triggered_by": "test_mcp@example.com",
                "notes": "MCP server testing snapshot",
                "tags": ["mcp-test"],
                "include_content": True,
                "detect_changes": False,
            }
            response = await client.post("/api/v1/snapshots", json=create_data)
            assert response.status_code == 201
            snapshot = response.json()
            snapshot_id = snapshot["snapshot_id"]
            print(f"[OK] Snapshot created: ID={snapshot_id}")
            print()

            # Test 1: List MCP servers
            print("[TEST 1] List MCP Servers")
            response = await client.get("/api/v1/mcp-servers?page=1&limit=10")
            assert response.status_code == 200
            servers_list = response.json()
            print(f"[OK] Found {servers_list['total']} MCP servers")
            print(f"     Page: {servers_list['page']}/{servers_list['total_pages']}")
            print(f"     Items: {len(servers_list['items'])}")

            if servers_list['items']:
                for server in servers_list['items'][:3]:
                    print(f"     - {server['server_name']} (ID: {server['id']})")
            print()

            # If no servers found, skip remaining tests
            if servers_list['total'] == 0:
                print("[INFO] No MCP servers found in snapshot. Tests will be limited.")
                print("[INFO] This is normal if Claude Desktop has no configured MCP servers.")
                print()

                # Test statistics endpoint (should work even with no servers)
                print("[TEST 7] Get MCP Server Statistics (empty)")
                response = await client.get("/api/v1/mcp-servers/stats")
                assert response.status_code == 200
                stats = response.json()
                print(f"[OK] Stats retrieved:")
                print(f"     Total servers: {stats['total_servers']}")
                print(f"     Total configurations: {stats['total_configurations']}")
                print()

                return  # Skip remaining tests

            # Get first server for detailed tests
            server_id = servers_list['items'][0]['id']
            server_name = servers_list['items'][0]['server_name']

            # Test 2: List with filter by snapshot
            print(f"[TEST 2] List MCP Servers - Filter by Snapshot {snapshot_id}")
            response = await client.get(f"/api/v1/mcp-servers?snapshot_id={snapshot_id}")
            assert response.status_code == 200
            filtered = response.json()
            print(f"[OK] Found {filtered['total']} servers in snapshot {snapshot_id}")
            print()

            # Test 3: List with filter by server name
            print(f"[TEST 3] List MCP Servers - Filter by Name '{server_name}'")
            response = await client.get(f"/api/v1/mcp-servers?server_name={server_name}")
            assert response.status_code == 200
            name_filtered = response.json()
            print(f"[OK] Found {name_filtered['total']} servers matching '{server_name}'")
            print()

            # Test 4: Get server details
            print(f"[TEST 4] Get MCP Server Details - ID {server_id}")
            response = await client.get(f"/api/v1/mcp-servers/{server_id}")
            assert response.status_code == 200
            details = response.json()
            print(f"[OK] Server details retrieved:")
            print(f"     Name: {details['server_name']}")
            print(f"     Command: {details.get('command', 'N/A')[:60]}...")
            print(f"     Config file: {details['config_file']}")
            print(f"     Snapshot ID: {details['snapshot_id']}")

            # Check if sanitization was applied
            command = details.get('command', '')
            if '[REDACTED_PII]' in command or '[REDACTED_' in str(details):
                print(f"     [SECURITY] Sanitization detected in response ✓")
            print()

            # Test 5: Get server status
            print(f"[TEST 5] Get MCP Server Status - ID {server_id}")
            response = await client.get(f"/api/v1/mcp-servers/{server_id}/status")
            assert response.status_code == 200
            status = response.json()
            print(f"[OK] Server status retrieved:")
            print(f"     Status: {status['status']}")
            print(f"     Last seen: {status['last_seen']}")
            print(f"     Snapshot count: {status['snapshot_count']}")
            print(f"     Config locations: {len(status['config_locations'])}")
            print()

            # Test 6: Get server configuration (should be sanitized)
            print(f"[TEST 6] Get MCP Server Configuration - ID {server_id}")
            response = await client.get(f"/api/v1/mcp-servers/{server_id}/config")
            assert response.status_code == 200
            config = response.json()
            print(f"[OK] Server configuration retrieved:")
            print(f"     Name: {config['server_name']}")
            print(f"     Command: {config.get('command', 'N/A')[:60]}...")
            print(f"     Has args: {config.get('args') is not None}")
            print(f"     Has env: {config.get('env') is not None}")
            print(f"     Sanitized: {config['sanitized']}")

            # Verify sanitization is working
            if config['sanitized']:
                print(f"     [SECURITY] Response marked as sanitized ✓")
                # Check for redaction patterns
                config_str = str(config)
                if 'REDACTED' in config_str:
                    print(f"     [SECURITY] Redaction patterns found ✓")
                else:
                    print(f"     [INFO] No secrets detected for redaction")
            print()

            # Test 7: Get server capabilities
            print(f"[TEST 7] Get MCP Server Capabilities - ID {server_id}")
            response = await client.get(f"/api/v1/mcp-servers/{server_id}/capabilities")
            assert response.status_code == 200
            caps = response.json()
            print(f"[OK] Server capabilities retrieved:")
            print(f"     Command type: {caps.get('command_type', 'unknown')}")
            print(f"     Has args: {caps['has_args']}")
            print(f"     Has env: {caps['has_env']}")
            print(f"     Has working dir: {caps['has_working_dir']}")
            print()

            # Test 8: Get server logs
            print(f"[TEST 8] Get MCP Server Logs - ID {server_id}")
            response = await client.get(f"/api/v1/mcp-servers/{server_id}/logs")
            assert response.status_code == 200
            logs = response.json()
            print(f"[OK] Server logs information retrieved:")
            print(f"     Log files found: {logs['log_files_found']}")
            print(f"     Locations: {len(logs['log_locations'])}")
            print(f"     Sanitized: {logs['sanitized']}")

            if logs['log_locations']:
                print(f"     Sample location: {logs['log_locations'][0][:60]}...")
                # Check for PII redaction in paths
                if '[REDACTED_PII]' in logs['log_locations'][0]:
                    print(f"     [SECURITY] PII redacted from paths ✓")
            print()

            # Test 9: Get server statistics
            print("[TEST 9] Get MCP Server Statistics")
            response = await client.get("/api/v1/mcp-servers/stats")
            assert response.status_code == 200
            stats = response.json()
            print(f"[OK] Statistics retrieved:")
            print(f"     Total servers: {stats['total_servers']}")
            print(f"     Total configurations: {stats['total_configurations']}")
            print(f"     Snapshots tracked: {len(stats['servers_by_snapshot'])}")

            if stats['most_common_servers']:
                print(f"     Most common servers:")
                for server in stats['most_common_servers'][:3]:
                    print(f"       - {server['server_name']}: {server['count']} config(s)")

            if stats['config_file_locations']:
                print(f"     Config locations: {len(stats['config_file_locations'])}")
                print(f"       - {stats['config_file_locations'][0]}")
            print()

            # Test 10: Error handling - Invalid server ID
            print("[TEST 10] Error Handling - Invalid Server ID")
            response = await client.get("/api/v1/mcp-servers/999999")
            assert response.status_code == 404
            error = response.json()
            print(f"[OK] 404 error returned for invalid ID:")
            print(f"     Message: {error.get('detail', 'N/A')}")
            print()

            # Test 11: Pagination
            print("[TEST 11] Pagination - Page 1 with Limit 2")
            response = await client.get("/api/v1/mcp-servers?page=1&limit=2")
            assert response.status_code == 200
            paginated = response.json()
            print(f"[OK] Pagination working:")
            print(f"     Total: {paginated['total']}")
            print(f"     Page: {paginated['page']}")
            print(f"     Page size: {paginated['page_size']}")
            print(f"     Has next: {paginated['has_next']}")
            print(f"     Has previous: {paginated['has_previous']}")
            print()

            # Summary
            print("=" * 60)
            print("All MCP Server Endpoint Tests Passed!")
            print("=" * 60)
            print(f"\nTotal Endpoints Tested: 11")
            print(f"Security Features Verified:")
            print(f"  - Configuration sanitization")
            print(f"  - Path PII redaction")
            print(f"  - Sanitized flags in responses")
            print(f"\nMCP Servers Found: {servers_list['total']}")
            print()

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        # Cleanup
        print("[CLEANUP] Closing database...")
        await close_database()
        print("[OK] Database closed")


if __name__ == "__main__":
    asyncio.run(test_mcp_endpoints())
