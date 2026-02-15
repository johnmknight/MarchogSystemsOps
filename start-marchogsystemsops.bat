@echo off
title MarchogSystemsOps Server
cd /d "%~dp0server"

:: Check for venv
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate
)

echo.
echo  =============================================
echo   MarchogSystemsOps - Multi-Screen Controller
echo  =============================================
echo.
echo  Starting server on http://localhost:8082
echo  Press Ctrl+C to stop
echo.

uvicorn main:app --host 0.0.0.0 --port 8082 --reload
