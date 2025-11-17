@echo off
REM Daily Development Session End
REM Creates final snapshot and guides commit workflow

echo ========================================
echo   Claude Config Editor - Session End
echo ========================================
echo.

REM Check if Docker container is running
docker ps | findstr claude-config-dev >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [WARN] Development container not running. Skipping snapshot.
    echo.
    goto :git_workflow
)

echo [1/4] CREATING END-OF-SESSION CONFIG SNAPSHOT
echo ----------------------------------------
echo Capturing final state of Claude configuration files...
set /p SUMMARY="Session summary (brief): "
docker exec -it claude-config-dev bash -c "cd /workspace && python -m src.cli.commands snapshot create --notes 'End of session: %SUMMARY%'" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [WARN] Could not create snapshot
)
echo.

:git_workflow
echo [2/4] WORKING TREE STATUS
echo ----------------------------------------
git status --short
echo.
git status --short | findstr /r "." >nul
if %ERRORLEVEL% NEQ 0 (
    echo [No changes to commit]
    goto :next_steps
)

echo [3/4] CHANGES TO COMMIT
echo ----------------------------------------
git diff --stat
echo.

set /p DO_COMMIT="Commit these changes? (y/n): "
if /i not "%DO_COMMIT%"=="y" goto :next_steps

echo.
git add -A
echo Staged all changes.
echo.

set /p COMMIT_MSG="Commit message: "
git commit -m "%COMMIT_MSG%"
echo.

:next_steps
echo [4/4] DOCUMENT NEXT STEPS
echo ----------------------------------------
echo What should be done next session?
echo (This will be saved to SESSION_NOTES.md)
echo Type your notes, then press Ctrl+Z and Enter when done:
echo.
copy con SESSION_NOTES_TEMP.md >nul
echo.

REM Prepend timestamp to notes
echo ## Session End: %DATE% %TIME% > SESSION_NOTES.md
echo. >> SESSION_NOTES.md
type SESSION_NOTES_TEMP.md >> SESSION_NOTES.md
del SESSION_NOTES_TEMP.md >nul 2>&1

echo.
echo ========================================
echo   SESSION COMPLETE
echo ========================================
echo.
echo Next steps saved to SESSION_NOTES.md
echo.
echo To stop container: docker-compose down
echo.
