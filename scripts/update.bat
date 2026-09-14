@echo off
setlocal EnableExtensions
title Video Downloader Local - Update

set "ROOT_DIR=%~dp0"
for %%I in ("%ROOT_DIR%..") do set "ROOT_DIR=%%~fI\"
set "VENV_DIR=%ROOT_DIR%venv"
set "PY=%VENV_DIR%\Scripts\python.exe"
set "DEV_DEPS=0"

if /i "%~1"=="--dev" set "DEV_DEPS=1"

if not exist "%PY%" (
    echo [ERROR] Virtual environment not found.
    echo         Run scripts\install.bat first.
    echo.
    exit /b 1
)

REM ---------- Git pull ----------
where git >nul 2>nul
if not errorlevel 1 (
    echo Pulling latest changes...
    git -C "%ROOT_DIR%" pull
    if errorlevel 1 (
        echo [WARN] git pull finished with warnings. Continuing...
    )
    echo.
) else (
    echo [WARN] Git is not installed. Skipping source update.
    echo.
)

REM ---------- Upgrade dependencies ----------
echo Upgrading runtime dependencies...
"%PY%" -m pip install --upgrade -r "%ROOT_DIR%requirements.txt"
if errorlevel 1 (
    echo [ERROR] Failed to upgrade runtime dependencies.
    exit /b 1
)

if "%DEV_DEPS%"=="1" (
    echo Upgrading development dependencies...
    "%PY%" -m pip install --upgrade -r "%ROOT_DIR%requirements-dev.txt"
    if errorlevel 1 (
        echo [ERROR] Failed to upgrade development dependencies.
        exit /b 1
    )
)

echo.
echo Update complete.
echo.
exit /b 0
