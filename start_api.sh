#!/bin/bash
# Start the Claude Config API server

echo "Starting Claude Config API server..."
echo "API will be available at: http://localhost:8765"
echo "API Docs will be available at: http://localhost:8765/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8765

