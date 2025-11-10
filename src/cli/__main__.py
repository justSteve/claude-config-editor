#!/usr/bin/env python
"""CLI wrapper script."""

import sys

from src.cli.commands import app

if __name__ == "__main__":
    sys.exit(app())
