@echo off
REM Backward-compatible one-click setup and launch script

cd /d "%~dp0"

call install.bat
if errorlevel 1 (
    exit /b 1
)

call start.bat
