@echo off
REM Start the Claude Config Editor API Server
REM Automatically kills any existing instances on port 8765

echo Checking for existing API server instances...

REM Kill any processes on port 8765
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8765 ^| findstr LISTENING') do taskkill /F /PID %%a /T 2>nul

REM Wait for port to be free
timeout /t 2 /nobreak >nul

echo.
echo Starting Claude Config Editor API Server...
echo.
echo - Config Editor UI: http://localhost:8765/ui
echo - Snapshot Viewer:  http://localhost:8765/snapshots
echo - API Docs:         http://localhost:8765/docs
echo.

REM Activate virtual environment and run
call .venv\Scripts\activate.bat
uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8765
