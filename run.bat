@echo off
REM ============================================================
REM  CleanTrack AI — Windows Setup & Run Script
REM  Run this from inside the CleanTrackAI/ folder
REM ============================================================
echo.
echo =====================================================
echo   CleanTrack AI - Setup and Launch
echo =====================================================
echo.
REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)
echo [1/3] Creating virtual environment...
if not exist "venv" (
    python -m venv venv
)
echo [2/3] Installing dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt
echo [3/3] Starting CleanTrack AI server...
echo.
echo  Open your browser and go to: http://127.0.0.1:5000
echo  Press CTRL+C to stop the server
echo.
python app.py
pause