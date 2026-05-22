@echo off
title E-Learning Portal - Setup & Launch
color 0A
cls

echo ============================================================
echo   E-Learning Portal - Installer and Launcher
echo ============================================================
echo.

:: --- Step 1: Check Python ---
echo [1/5] Checking for Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    color 0C
    echo.
    echo  ERROR: Python is not installed or not in PATH.
    echo.
    echo  Please install Python 3.10 or newer from:
    echo    https://www.python.org/downloads/
    echo.
    echo  IMPORTANT: During installation, check the box that says
    echo  "Add Python to PATH" before clicking Install.
    echo.
    pause
    exit /b 1
)
python --version
echo  Python found.
echo.

:: --- Step 2: Create virtual environment ---
echo [2/5] Setting up virtual environment...
if not exist ".venv\Scripts\activate.bat" (
    echo  Creating .venv ...
    python -m venv .venv
    if errorlevel 1 (
        color 0C
        echo  ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo  Virtual environment created.
) else (
    echo  Virtual environment already exists. Skipping.
)
echo.

:: --- Step 3: Install dependencies ---
echo [3/5] Installing required packages (this may take a minute)...
call .venv\Scripts\activate.bat
pip install -r requirements.txt --quiet
if errorlevel 1 (
    color 0C
    echo  ERROR: Failed to install packages. Check your internet connection.
    pause
    exit /b 1
)
echo  All packages installed successfully.
echo.

:: --- Step 4: Initialize database ---
echo [4/5] Setting up database...
if not exist "instance\elearning.db" (
    echo  Creating database and loading sample data...
    if not exist "instance" mkdir instance
    python init_db.py
    if errorlevel 1 (
        color 0C
        echo  ERROR: Database initialization failed.
        pause
        exit /b 1
    )
    echo  Database ready with sample data.
) else (
    echo  Database already exists. Skipping initialization.
)
if not exist "uploads" mkdir uploads
echo.

:: --- Step 5: Launch the app ---
echo [5/5] Starting the E-Learning Portal...
echo.
echo ============================================================
echo   App is starting at: http://localhost:5000
echo ============================================================
echo.
echo  Demo Login Credentials:
echo  ------------------------------------------------
echo  ADMIN    : admin@elearning.local   / admin123
echo  TEACHER  : john.smith@faculty.local / teacher123
echo  STUDENT  : student1@faculty.local  / student123
echo  ------------------------------------------------
echo.
echo  The browser will open automatically in a few seconds.
echo  To stop the server, close this window or press Ctrl+C.
echo.

:: Open browser after a short delay
start "" /B cmd /C "timeout /T 3 /NOBREAK >nul && start http://localhost:5000"

:: Start Flask app
python main_enhanced.py

echo.
echo  Server stopped. Press any key to exit.
pause >nul
