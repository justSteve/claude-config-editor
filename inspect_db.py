#!/usr/bin/env python3
"""
Quick database inspector - shows what's in the database.
"""

import asyncio
import sqlite3
from pathlib import Path


def inspect_database():
    """Inspect the database and print contents."""
    db_path = Path("data/claude_config.db")

    if not db_path.exists():
        print(f"ERROR: Database not found at: {db_path}")
        return

    print(f"Database: {db_path}\n")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = cursor.fetchall()

    print(f"Tables ({len(tables)}):")
    print("-" * 80)

    for (table_name,) in tables:
        # Count rows
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]

        print(f"\n[{table_name}] - {count} rows")

        if count > 0:
            # Show sample data
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]

            # Get first few rows
            limit = min(3, count)
            cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
            rows = cursor.fetchall()

            print(f"  Columns: {', '.join(columns)}")
            print(f"  Sample data:")
            for i, row in enumerate(rows, 1):
                print(f"    Row {i}:")
                for col, val in zip(columns, row):
                    # Truncate long values
                    if isinstance(val, str) and len(val) > 60:
                        val = val[:60] + "..."
                    print(f"      {col}: {val}")

    print("\n" + "=" * 80)
    print("\nDetailed Snapshot Info:\n")

    # Show snapshot details
    cursor.execute("""
        SELECT
            id,
            snapshot_time,
            trigger_type,
            files_found,
            directories_found,
            total_size_bytes,
            changed_from_previous
        FROM snapshots
        ORDER BY snapshot_time DESC
    """)

    snapshots = cursor.fetchall()
    for snap in snapshots:
        snap_id, time, trigger, files, dirs, size, changes = snap
        print(f"Snapshot #{snap_id}")
        print(f"  Time: {time}")
        print(f"  Trigger: {trigger}")
        print(f"  Files: {files}, Dirs: {dirs}")
        print(f"  Size: {size:,} bytes ({size/1024:.1f} KB)")
        print(f"  Changes: {changes if changes else 'N/A (baseline)'}")
        print()

    # Show file contents info
    cursor.execute("""
        SELECT
            content_hash,
            content_type,
            size_bytes,
            reference_count
        FROM file_contents
        ORDER BY size_bytes DESC
    """)

    print("File Contents (deduplicated):\n")
    contents = cursor.fetchall()
    for hash_val, ctype, size, refs in contents:
        print(f"  {hash_val[:16]}... ({ctype})")
        print(f"    Size: {size:,} bytes")
        print(f"    Referenced by: {refs} snapshot path(s)")
        print()

    # Show path scan results
    cursor.execute("""
        SELECT
            category,
            COUNT(*) as count,
            SUM(CASE WHEN "exists" = 1 THEN 1 ELSE 0 END) as found
        FROM snapshot_paths
        WHERE snapshot_id = (SELECT MAX(id) FROM snapshots)
        GROUP BY category
        ORDER BY category
    """)

    print("Paths Scanned (latest snapshot):\n")
    categories = cursor.fetchall()
    for cat, total, found in categories:
        print(f"  {cat}: {found}/{total} found")

    conn.close()

    print("\n" + "=" * 80)
    print("SUCCESS: Inspection complete!")


if __name__ == "__main__":
    inspect_database()
