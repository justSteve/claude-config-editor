"""Entry point for CLI when run as a module."""

import sys

from . import app

if __name__ == "__main__":
    try:
        app()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
