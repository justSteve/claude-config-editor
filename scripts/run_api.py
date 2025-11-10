#!/usr/bin/env python3
"""
Start the Claude Config API server.

Usage:
    python run_api.py                    # Development mode
    python run_api.py --prod             # Production mode
    python run_api.py --port 8000        # Custom port
"""

import argparse
import sys
import uvicorn
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))


def main():
    parser = argparse.ArgumentParser(description="Run Claude Config API")
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Port to bind to (default: 8765)",
    )
    parser.add_argument(
        "--prod",
        action="store_true",
        help="Run in production mode (no reload, no debug)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker processes (production only, default: 1)",
    )

    args = parser.parse_args()

    if args.prod:
        # Production mode
        print(f"🚀 Starting API in PRODUCTION mode")
        print(f"📍 Server: http://{args.host}:{args.port}")
        print(f"👷 Workers: {args.workers}")
        print(f"📚 Docs: http://{args.host}:{args.port}/docs")
        print(f"\n⚡ Press CTRL+C to quit\n")

        uvicorn.run(
            "src.api.app:app",
            host=args.host,
            port=args.port,
            workers=args.workers,
            log_level="info",
            access_log=True,
        )
    else:
        # Development mode
        print(f"🔧 Starting API in DEVELOPMENT mode")
        print(f"📍 Server: http://{args.host}:{args.port}")
        print(f"🔄 Auto-reload: enabled")
        print(f"📚 Docs: http://{args.host}:{args.port}/docs")
        print(f"\n⚡ Press CTRL+C to quit\n")

        uvicorn.run(
            "src.api.app:app",
            host=args.host,
            port=args.port,
            reload=True,
            log_level="debug",
            access_log=True,
        )


if __name__ == "__main__":
    main()

