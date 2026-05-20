@echo off
setlocal EnableExtensions

cd /d "%~dp0"

echo.
echo ============================================
echo  E-Learning Portal - Starting
echo ============================================
echo.

set "APP_PYTHON="
if exist ".venv\Scripts\python.exe" (
    set "APP_PYTHON=.venv\Scripts\python.exe"
) else if exist "venv\Scripts\python.exe" (
    set "APP_PYTHON=venv\Scripts\python.exe"
)

if "%APP_PYTHON%"=="" (
    echo ERROR: Virtual environment not found.
    echo Run install.bat first.
    pause
    exit /b 1
)

if not exist "instance" mkdir "instance"

if not exist "instance\elearning.db" (
    echo Database not found. Initializing...
    "%APP_PYTHON%" init_db.py
    if errorlevel 1 (
        echo ERROR: Database initialization failed.
        pause
        exit /b 1
    )
)

echo Starting Flask application on http://127.0.0.1:5000
echo Press CTRL+C to stop the server.
echo.
"%APP_PYTHON%" main_enhanced.py

pause
endlocal
