@echo off
title whisper-hotkey - Install

echo ============================================
echo   whisper-hotkey - Install
echo ============================================
echo.

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Python not found.
    echo     Download Python 3.10+ from https://python.org
    echo     IMPORTANT: check "Add Python to PATH" during install
    echo.
    pause
    exit /b 1
)

echo [+] Python found:
python --version
echo.

if not exist ".venv" (
    echo [*] Creating virtual environment...
    python -m venv .venv
    echo [+] Done
) else (
    echo [i] Virtual environment already exists
)
echo.

echo [*] Installing dependencies (this may take a few minutes)...
echo.
.venv\Scripts\pip.exe install --upgrade pip >nul 2>&1
.venv\Scripts\pip.exe install -r requirements.txt
echo.

if %errorlevel% neq 0 (
    echo [!] Error installing dependencies
    pause
    exit /b 1
)

echo ============================================
echo   Install complete!
echo   Run run.bat to start
echo ============================================
echo.
pause
