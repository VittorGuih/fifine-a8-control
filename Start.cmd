@echo off
setlocal
if not exist "%~dp0.venv\Scripts\pythonw.exe" (
    echo Install the app first using the README instructions.
    pause
    exit /b 1
)
start "" "%~dp0.venv\Scripts\pythonw.exe" -m fifine_a8_control
