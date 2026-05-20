@echo off
setlocal EnableExtensions

cd /d "%~dp0"

echo.
echo ============================================
echo  E-Learning Portal - Installer
echo ============================================
echo.

set "PYTHON_CMD="
py -3 --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=py -3"
) else (
    python --version >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_CMD=python"
    )
)

if "%PYTHON_CMD%"=="" (
    echo ERROR: Python is not installed or not in PATH.
    echo Install Python 3.8+ from https://www.python.org/
    echo During installation, enable "Add Python to PATH".
    pause
    exit /b 1
)

echo [1/6] Python detected:
%PYTHON_CMD% --version

if not exist ".venv\Scripts\python.exe" (
    echo.
    echo [2/6] Creating virtual environment .venv...
    %PYTHON_CMD% -m venv .venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
) else (
    echo.
    echo [2/6] Virtual environment already exists .venv
)

set "VENV_PY=.venv\Scripts\python.exe"
if not exist "%VENV_PY%" (
    echo ERROR: Virtual environment python executable not found.
    pause
    exit /b 1
)

echo.
echo [3/6] Using virtual environment python...
"%VENV_PY%" --version

echo.
echo [4/6] Checking pip...
"%VENV_PY%" -m pip --version

echo.
echo [5/6] Installing dependencies from requirements.txt...
set "MAX_RETRIES=3"
set "ATTEMPT=1"

:install_requirements
echo Attempt %ATTEMPT% of %MAX_RETRIES%...
"%VENV_PY%" -m pip install -r requirements.txt
if errorlevel 1 (
    if %ATTEMPT% GEQ %MAX_RETRIES% (
        echo ERROR: Dependency installation failed after %MAX_RETRIES% attempts.
        echo Check internet connection, then run install.bat again.
        pause
        exit /b 1
    )
    set /a ATTEMPT+=1
    echo Retrying dependency installation...
    goto :install_requirements
)

if not exist "instance" mkdir "instance"

echo.
if not exist "instance\elearning.db" (
    echo [6/6] Initializing database with sample data...
    "%VENV_PY%" init_db.py
    if errorlevel 1 (
        echo ERROR: Failed to initialize database.
        pause
        exit /b 1
    )
) else (
    echo [6/6] Database already exists, skipping initialization.
)

echo.
echo ============================================
echo  Setup complete
echo ============================================
echo Run start.bat to launch the app.
echo URL: http://localhost:5000
echo.
pause

endlocal
