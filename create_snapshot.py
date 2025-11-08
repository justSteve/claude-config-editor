"""Quick script to create a snapshot."""
import asyncio
from src.core.config import get_settings
from src.core.database import init_database, close_database
from src.core.scanner import PathScanner

async def main():
    settings = get_settings()
    db = await init_database(settings.database_url, echo=False)

    try:
        async with db.get_session() as session:
            scanner = PathScanner(session)
            snapshot = await scanner.create_snapshot(
                trigger_type="cli",
                triggered_by="manual",
                notes="Second snapshot for change detection"
            )
            print(f"SUCCESS: Snapshot {snapshot.id} created successfully!")
            print(f"  Files: {snapshot.files_found}, Dirs: {snapshot.directories_found}")
            print(f"  Size: {snapshot.total_size_bytes:,} bytes")
            if snapshot.changed_from_previous:
                print(f"  Changes: {snapshot.changed_from_previous}")
    finally:
        await close_database()

if __name__ == "__main__":
    asyncio.run(main())
