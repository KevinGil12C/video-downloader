@echo off
setlocal EnableExtensions
title Video Downloader Local

set "ROOT_DIR=%~dp0"
for %%I in ("%ROOT_DIR%..") do set "ROOT_DIR=%%~fI\"
cd /d "%ROOT_DIR%"
set "VENV_DIR=%ROOT_DIR%venv"
set "PY=%VENV_DIR%\Scripts\python.exe"

set "MODE=desktop"
if /i "%~1"=="--api" set "MODE=api"
if /i "%~1"=="--desktop" set "MODE=desktop"

if not exist "%PY%" goto :noenv
if "%MODE%"=="api" goto :api
goto :desktop

REM --- Desktop mode (default) ---
:desktop
if not exist "%ROOT_DIR%app\desktop\main.py" (
    echo [INFO] Desktop entry point is not implemented yet.
    echo        Expected module: app.desktop.main
    echo        Start the API server instead: scripts\start.bat --api
    exit /b 1
)

echo Starting Video Downloader - Desktop mode.
echo.
"%PY%" -m app.desktop.main
exit /b %errorlevel%

REM --- API-only mode ---
:api
if not exist "%ROOT_DIR%app\backend\server.py" (
    echo [INFO] API server is not implemented yet.
    echo        Expected module: app.backend.server
    echo        Run scripts\install.bat --dev and implement the backend first.
    exit /b 1
)

echo Starting local API at http://127.0.0.1:8000
echo Press Ctrl+C to stop.
echo.
"%PY%" -m uvicorn app.backend.server:app --host 127.0.0.1 --port 8000
exit /b %errorlevel%

:noenv
echo [ERROR] Virtual environment not found.
echo         Run scripts\install.bat first.
echo.
exit /b 1