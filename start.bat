@echo off
:: Contract Obligation Tracker — One-command launch script (Windows)
:: Usage: start.bat

cd /d "%~dp0"

echo Contract Obligation Tracker
echo ==================================

:: Create virtual environment if needed
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

:: Activate venv
call .venv\Scripts\activate.bat

:: Install dependencies if needed
python -c "import fastapi" 2>nul
if errorlevel 1 (
    echo Installing dependencies (first run only^)...
    pip install -e . --quiet
)

:: Create data directories
if not exist "data\uploads" mkdir data\uploads

:: Start API server in background
echo Starting API server on port 8000...
start "OT-API" /b uvicorn ot_app.main:app --host 0.0.0.0 --port 8000

:: Wait for API
echo Waiting for API...
timeout /t 5 /nobreak >nul

:: Open browser
start http://localhost:8501

:: Start Streamlit in background
echo Starting dashboard on port 8501...
echo.
echo   Dashboard: http://localhost:8501
echo   API docs:  http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop, or use the Shut Down button in the app.
echo.

start "OT-Frontend" /b streamlit run ot_frontend/app.py --server.port 8501 --server.headless true

:: Wait for API process to exit (shutdown endpoint kills it)
:wait_loop
timeout /t 2 /nobreak >nul
curl -s http://localhost:8000/api/v1/health >nul 2>&1
if not errorlevel 1 goto wait_loop

:: API is gone — clean up any remaining processes
echo Shutting down...
taskkill /fi "WINDOWTITLE eq OT-API" /f >nul 2>&1
taskkill /fi "WINDOWTITLE eq OT-Frontend" /f >nul 2>&1
echo Stopped.
