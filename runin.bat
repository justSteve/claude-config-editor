@echo off
REM Execute a command inside the development container
REM Usage: runin "command to execute"
REM Example: runin "python -m src.cli.commands snapshot list"

if "%~1"=="" (
    echo Usage: runin "command"
    echo Example: runin "pytest"
    echo Example: runin "python -m src.cli.commands snapshot list"
    exit /b 1
)

REM Check if container is running
docker ps | findstr claude-config-dev >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Development container is not running
    echo Start it with: docker-compose up -d dev-env
    exit /b 1
)

REM Execute command in container
docker exec -it claude-config-dev bash -c "cd /workspace && %~1"
