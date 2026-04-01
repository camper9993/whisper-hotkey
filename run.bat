@echo off

if not exist "%~dp0.venv\Scripts\pythonw.exe" (
    echo [!] Run install.bat first
    pause
    exit /b 1
)

net session >nul 2>&1
if %errorlevel% neq 0 (
    powershell -Command "Start-Process -FilePath '%~f0' -Verb RunAs -WorkingDirectory '%~dp0'"
    exit /b
)

cd /d "%~dp0"
start "" .venv\Scripts\pythonw.exe main.py
