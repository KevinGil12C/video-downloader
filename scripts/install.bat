@echo off
setlocal EnableExtensions
title Video Downloader Local - Install

set "ROOT_DIR=%~dp0"
for %%I in ("%ROOT_DIR%..") do set "ROOT_DIR=%%~fI\"
set "VENV_DIR=%ROOT_DIR%venv"
set "PYTHON="
set "DEV_DEPS=0"

if /i "%~1"=="--dev" set "DEV_DEPS=1"

echo.
echo ===================================================
echo   Video Downloader Local - Installation
echo ===================================================
echo.

REM ---------- Locate Python 3.10+ ----------
REM Try the Windows Python Launcher (py) first to avoid the
REM Microsoft Store alias that may exist at C:\WindowsApps\python.exe.

where py >nul 2>nul
if not errorlevel 1 (
    py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
    if not errorlevel 1 set "PYTHON=py -3"
)

if not defined PYTHON (
    where python >nul 2>nul
    if not errorlevel 1 (
        python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
        if not errorlevel 1 set "PYTHON=python"
    )
)

if not defined PYTHON (
    echo [ERROR] Python 3.10 or newer was not found.
    echo         Install it from https://www.python.org/downloads/ and
    echo         enable "Add python.exe to PATH" during installation.
    echo.
    exit /b 1
)

%PYTHON% --version
echo.

REM ---------- 1/4  Virtual environment ----------
echo [1/4] Virtual environment...
if not exist "%VENV_DIR%\Scripts\python.exe" (
    %PYTHON% -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo [ERROR] Failed to create the virtual environment.
        exit /b 1
    )
    echo        Created at "%VENV_DIR%".
) else (
    echo        Virtual environment already exists at "%VENV_DIR%".
)

set "PY=%VENV_DIR%\Scripts\python.exe"
set "PIP=%VENV_DIR%\Scripts\pip.exe"

REM ---------- 2/4  Upgrade pip ----------
echo.
echo [2/4] Upgrading pip...
"%PY%" -m pip install --upgrade pip >nul
if errorlevel 1 (
    echo [ERROR] Failed to upgrade pip.
    exit /b 1
)
echo        pip upgraded.

REM ---------- 3/4  Install dependencies ----------
echo.
echo [3/4] Installing dependencies...
"%PY%" -m pip install -r "%ROOT_DIR%requirements.txt"
if errorlevel 1 (
    echo [ERROR] Failed to install runtime dependencies.
    exit /b 1
)
echo        Runtime dependencies installed.

if "%DEV_DEPS%"=="1" (
    echo        Installing development dependencies...
    "%PY%" -m pip install -r "%ROOT_DIR%requirements-dev.txt"
    if errorlevel 1 (
        echo [ERROR] Failed to install development dependencies.
        exit /b 1
    )
    echo        Development dependencies installed.
)

REM ---------- 4/4  Check FFmpeg ----------
echo.
echo [4/4] Checking FFmpeg...
set "FFMPEG_OK=0"
where ffmpeg >nul 2>nul
if not errorlevel 1 set "FFMPEG_OK=1"
if exist "%ROOT_DIR%bin\ffmpeg\ffmpeg.exe" set "FFMPEG_OK=1"

if "%FFMPEG_OK%"=="1" (
    echo        FFmpeg found.
) else (
    echo [WARN] FFmpeg was not found.
    echo        Put ffmpeg.exe in "%ROOT_DIR%bin\ffmpeg\" or add it to your PATH.
    echo        FFmpeg is required to merge and convert media.
)

echo.
echo ===================================================
echo   Installation complete.
echo.
if "%DEV_DEPS%"=="1" (
    echo   Next: scripts\start.bat          run the application
    echo         scripts\test.bat           run tests and lint
) else (
    echo   Next: scripts\start.bat          run the application
    echo.
    echo   Dev:  scripts\install.bat --dev  install dev dependencies
)
echo ===================================================
echo.
endlocal
exit /b 0
