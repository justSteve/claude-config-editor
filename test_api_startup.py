"""
Test script to verify FastAPI application setup.

Tests:
- App can be imported
- App has correct metadata
- Basic endpoints are registered
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def test_app_import():
    """Test that app can be imported."""
    try:
        from src.api.app import app
        print("[OK] App imported successfully")
        return app
    except Exception as e:
        print(f"[FAIL] Failed to import app: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def test_app_metadata(app):
    """Test app metadata."""
    try:
        assert app.title == "Claude Config Version Control API"
        assert app.version == "1.0.0"
        assert app.docs_url == "/docs"
        print("[OK] App metadata correct")
    except AssertionError as e:
        print(f"[FAIL] App metadata incorrect: {e}")
        sys.exit(1)


def test_routes(app):
    """Test that basic routes are registered."""
    try:
        routes = [route.path for route in app.routes]
        assert "/" in routes
        assert "/health" in routes
        assert "/openapi.json" in routes
        print("[OK] Basic routes registered")
        print(f"     Routes: {', '.join(routes)}")
    except AssertionError as e:
        print(f"[FAIL] Routes not registered: {e}")
        sys.exit(1)


def main():
    print("\nTesting FastAPI Application Setup\n")
    print("=" * 50)

    # Test 1: Import app
    app = test_app_import()

    # Test 2: Check metadata
    test_app_metadata(app)

    # Test 3: Check routes
    test_routes(app)

    print("=" * 50)
    print("\n[SUCCESS] All tests passed!\n")
    print("Next steps:")
    print("  1. Run: python run_api.py")
    print("  2. Open: http://127.0.0.1:8765/docs")
    print("  3. Test: curl http://127.0.0.1:8765/health\n")


if __name__ == "__main__":
    main()
