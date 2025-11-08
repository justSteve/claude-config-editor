"""Test reporting functionality."""
import asyncio
import json
from src.core.config import get_settings
from src.core.database import init_database, close_database
from src.reports.generators import generate_change_report, generate_snapshot_report
from src.reports.formatters import JSONFormatter, CLIFormatter

async def test_change_report():
    settings = get_settings()
    db = await init_database(settings.database_url, echo=False)

    try:
        async with db.get_session() as session:
            # Generate change report
            report = await generate_change_report(session, snapshot_id=2)

            # Save as JSON
            formatter = JSONFormatter()
            json_output = formatter.format_change_report(report)
            with open("change_report.json", "w") as f:
                f.write(json_output)
            print("SUCCESS: Change report saved to change_report.json")

            # Show summary
            print(f"\nChange Summary:")
            print(f"  Snapshot {report.snapshot_id} vs {report.previous_snapshot_id}")
            print(f"  Total changes: {report.total_changes}")
            print(f"  Added: {len(report.added_files)}")
            print(f"  Modified: {len(report.modified_files)}")
            print(f"  Deleted: {len(report.deleted_files)}")
            print(f"  Size change: {report.size_change_bytes:+,} bytes")

    finally:
        await close_database()

async def test_snapshot_report():
    settings = get_settings()
    db = await init_database(settings.database_url, echo=False)

    try:
        async with db.get_session() as session:
            # Generate snapshot report
            report = await generate_snapshot_report(session, snapshot_id=2)

            # Save as JSON
            formatter = JSONFormatter()
            json_output = formatter.format_snapshot_report(report)
            with open("snapshot_report.json", "w") as f:
                f.write(json_output)
            print("\nSUCCESS: Snapshot report saved to snapshot_report.json")

            # Show summary
            print(f"\nSnapshot Summary:")
            print(f"  ID: {report.snapshot_id}")
            print(f"  Time: {report.snapshot_time}")
            print(f"  Files: {report.files_found}, Dirs: {report.directories_found}")
            print(f"  Total size: {report.total_size_bytes:,} bytes")
            print(f"  Deduplication: {report.deduplication_percent:.1f}% savings")

    finally:
        await close_database()

if __name__ == "__main__":
    print("Testing Change Detection Report...")
    asyncio.run(test_change_report())

    print("\n" + "="*60)
    print("Testing Snapshot Summary Report...")
    asyncio.run(test_snapshot_report())
