@echo off
REM ============================================================
REM AI Workforce — 1-Click Setup for Windows
REM ============================================================
echo [AI Workforce] Setting up environment...
where antigravity-ide.cmd >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set IDE_CMD=antigravity-ide.cmd
    goto install
)
where cursor.cmd >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set IDE_CMD=cursor.cmd
    goto install
)
where code.cmd >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set IDE_CMD=code.cmd
    goto install
)

echo [WARNING] No IDE CLI found in PATH. Please install .vsix manually from extension/ folder.
goto end

:install
echo [OK] Using IDE: %IDE_CMD%
for /f "delims=" %%i in ('dir /b /o-d extension\ai-workforce-panel-*.vsix 2^>nul') do (
    echo [INFO] Installing extension\%%i...
    call %IDE_CMD% --install-extension "extension\%%i" --force
    goto installed
)

:installed
echo [INFO] Installing office viewer...
call %IDE_CMD% --install-extension cweijan.vscode-office --force 2>nul
echo [OK] Setup completed successfully!

:end
pause
