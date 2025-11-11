"""Test reporting functionality."""
import asyncio
from pathlib import Path

from src.core.config import get_settings
from src.core.database import close_database, init_database
from src.reports.formatters import JSONFormatter
from src.reports.generators import generate_change_report, generate_snapshot_report


async def test_change_report(tmp_path: Path):
    settings = get_settings()
    db = await init_database(settings.database_url, echo=False)

    try:
        async with db.get_session() as session:
            # Generate change report
            report = await generate_change_report(session, snapshot_id=2)

            # Save as JSON to temp directory
            formatter = JSONFormatter()
            json_output = formatter.format_change_report(report)
            output_file = tmp_path / "change_report.json"
            with open(output_file, "w") as f:
                f.write(json_output)
            print(f"SUCCESS: Change report saved to {output_file}")

            # Show summary
            print("\nChange Summary:")
            print(
                f"  Snapshot {report.snapshot_id} vs {report.previous_snapshot_id}")
            print(f"  Total changes: {report.total_changes}")
            print(f"  Added: {len(report.added_files)}")
            print(f"  Modified: {len(report.modified_files)}")
            print(f"  Deleted: {len(report.deleted_files)}")
            print(f"  Size change: {report.size_change_bytes:+,} bytes")

    finally:
        await close_database()


async def test_snapshot_report(tmp_path: Path):
    settings = get_settings()
    db = await init_database(settings.database_url, echo=False)

    try:
        async with db.get_session() as session:
            # Generate snapshot report
            report = await generate_snapshot_report(session, snapshot_id=2)

            # Save as JSON to temp directory
            formatter = JSONFormatter()
            json_output = formatter.format_snapshot_report(report)
            output_file = tmp_path / "snapshot_report.json"
            with open(output_file, "w") as f:
                f.write(json_output)
            print(f"\nSUCCESS: Snapshot report saved to {output_file}")

            # Show summary
            print("\nSnapshot Summary:")
            print(f"  ID: {report.snapshot_id}")
            print(f"  Time: {report.snapshot_time}")
            print(
                f"  Files: {report.files_found}, Dirs: {report.directories_found}")
            print(f"  Total size: {report.total_size_bytes:,} bytes")
            print(
                f"  Deduplication: {report.deduplication_percent:.1f}% savings")

    finally:
        await close_database()

if __name__ == "__main__":
    print("Testing Change Detection Report...")
    asyncio.run(test_change_report())

    print("\n" + "="*60)
    print("Testing Snapshot Summary Report...")
    asyncio.run(test_snapshot_report())
