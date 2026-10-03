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

echo [INFO] Checking Pandoc...
where pandoc >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Pandoc not found. Please install manually from https://pandoc.org/
) else (
    echo [OK] Pandoc found.
)

echo [INFO] Checking Python environment...
if not exist ".venv" (
    echo [INFO] Creating .venv...
    where uv >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        call uv venv .venv
    ) else (
        where python >nul 2>nul
        if %ERRORLEVEL% EQU 0 (
            call python -m venv .venv
        ) else (
            echo [ERROR] Python not found. Please install Python.
            goto end
        )
    )
)

if exist ".venv\Scripts\activate.bat" (
    echo [INFO] Installing Python dependencies...
    call .venv\Scripts\activate.bat
    where uv >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        call uv pip install -r requirements.txt
    ) else (
        call pip install -r requirements.txt
    )
    call deactivate
)

echo [INFO] Checking document converter (scripts\doc_ingest.py)...
if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe -c "import markitdown, mammoth, pdfplumber, openpyxl, pptx, pymupdf" >nul 2>nul
    if errorlevel 1 (
        echo [WARNING] .venv is missing markitdown/document readers. Run: .venv\Scripts\pip install -r requirements.txt
    ) else (
        echo [OK] markitdown + DOCX/PDF/XLSX/PPTX readers ready in .venv
    )
)

REM LibreOffice (optional, not auto-installed): needed by doc_ingest for DOC/XLS/PPT, ODT/ODS/ODP, RTF
set "SOFFICE_FOUND="
where soffice >nul 2>nul
if not errorlevel 1 set "SOFFICE_FOUND=1"
if exist "%ProgramFiles%\LibreOffice\program\soffice.exe" set "SOFFICE_FOUND=1"
if exist "%ProgramFiles(x86)%\LibreOffice\program\soffice.exe" set "SOFFICE_FOUND=1"
if defined SOFFICE_FOUND (
    echo [OK] LibreOffice found.
) else (
    echo [OPTIONAL] LibreOffice not found - DOC/XLS/PPT/ODT/RTF cannot be read. Install: winget install -e --id TheDocumentFoundation.LibreOffice
)

REM tesseract (optional): OCR draft for scanned pages (Apple Vision is macOS-only)
where tesseract >nul 2>nul
if errorlevel 1 (
    echo [OPTIONAL] tesseract not found - no OCR draft for scans. Install: winget install -e --id UB-Mannheim.TesseractOCR ^(choose Vietnamese + Japanese language data^)
) else (
    echo [OK] tesseract found. Make sure language data vie + jpn is installed.
)

echo [OK] Setup completed successfully!

:end
pause
