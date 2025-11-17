@echo off
REM Daily Development Session Starter
REM Automates project initialization and context gathering

echo ========================================
echo   Claude Config Editor - Session Start
echo ========================================
echo.

REM Check if Docker container is running
docker ps | findstr claude-config-dev >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [!] Development container not running. Starting...
    docker-compose up -d dev-env
    if %ERRORLEVEL% NEQ 0 (
        echo ERROR: Failed to start container. Run setup-dev-env.bat first.
        pause
        exit /b 1
    )
    echo [OK] Container started
    echo.
)

echo [1/5] LAST SESSION SUMMARY
echo ----------------------------------------
git log --oneline -5
echo.

echo [2/5] LAST COMMIT DETAILS
echo ----------------------------------------
for /f "delims=" %%i in ('git log -1 --format^="%%h"') do set LAST_HASH=%%i
echo Commit: %LAST_HASH%
git log -1 --format="Author: %%an"
git log -1 --format="Date: %%ad" --date=relative
echo.
echo Files changed:
git diff %LAST_HASH%~1 %LAST_HASH% --stat | head -20
echo.

echo [3/5] WORKING TREE STATUS
echo ----------------------------------------
git status --short
if %ERRORLEVEL% EQU 0 (
    git status --short | findstr /r "." >nul
    if %ERRORLEVEL% NEQ 0 (
        echo [Clean working tree - no uncommitted changes]
    )
)
echo.

echo [4/5] CREATING CLAUDE CONFIG SNAPSHOT
echo ----------------------------------------
echo Capturing current state of all 17 Claude configuration locations...
docker exec -it claude-config-dev bash -c "cd /workspace && python -m src.cli.commands snapshot create --notes 'Session start'" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [WARN] Could not create snapshot - database may need initialization
)
echo.

echo [5/5] TEST SUITE HEALTH CHECK
echo ----------------------------------------
docker exec -it claude-config-dev bash -c "cd /workspace && python -m pytest --tb=no -q 2>/dev/null | tail -5"
echo.

echo ========================================
echo   SESSION READY
echo ========================================
echo.
echo Quick Commands:
echo   runin "pytest"                              - Run full test suite
echo   runin "python -m src.api.app"              - Start API server
echo   runin "python -m src.cli.commands --help"  - CLI help
echo.
echo Session End:
echo   session-end.bat                            - Snapshot + commit workflow
echo.
