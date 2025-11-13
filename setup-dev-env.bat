@echo off
REM Setup Claude Config Editor Development Environment
REM This creates a containerized development environment that is identical
REM for both you and AI agents, eliminating environment friction

echo ========================================
echo Claude Config Editor - Dev Environment
echo ========================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Docker is not installed or not in PATH
    echo Please install Docker Desktop from: https://www.docker.com/products/docker-desktop
    echo.
    pause
    exit /b 1
)

echo [1/4] Checking Docker...
echo Docker found:
docker --version
echo.

REM Check if docker-compose is available
docker-compose --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: docker-compose is not available
    echo Please ensure Docker Desktop is installed and running
    echo.
    pause
    exit /b 1
)

echo [2/4] Building development container...
echo This may take a few minutes on first run...
echo.
docker-compose build dev-env
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to build container
    pause
    exit /b 1
)

echo.
echo [3/4] Creating data and logs directories...
if not exist "data" mkdir data
if not exist "logs" mkdir logs

echo.
echo [4/4] Starting development container...
docker-compose up -d dev-env
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to start container
    pause
    exit /b 1
)

echo.
echo ========================================
echo SUCCESS! Development environment is ready
echo ========================================
echo.
echo Container Name: claude-config-dev
echo API Port: http://localhost:8765
echo.
echo Quick Commands:
echo   runin "python -m src.cli.commands snapshot list"   - List snapshots
echo   runin "pytest"                                       - Run tests
echo   runin "python -m src.api.app"                        - Start API manually
echo.
echo Or start the API server:
echo   docker-compose --profile api up -d
echo.
echo To enter the container:
echo   docker exec -it claude-config-dev bash
echo.
echo To stop the environment:
echo   docker-compose down
echo.
pause
