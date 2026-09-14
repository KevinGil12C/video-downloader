@echo off
setlocal EnableExtensions
title Video Downloader Local - Tests

set "ROOT_DIR=%~dp0"
for %%I in ("%ROOT_DIR%..") do set "ROOT_DIR=%%~fI\"
set "VENV_DIR=%ROOT_DIR%venv"
set "PY=%VENV_DIR%\Scripts\python.exe"

if not exist "%PY%" (
    echo [ERROR] Virtual environment not found.
    echo         Run scripts\install.bat --dev first.
    echo.
    exit /b 1
)

REM --- Ensure pytest is installed (auto-install dev deps if missing) ---
"%PY%" -m pytest --version >nul 2>nul
if errorlevel 1 (
    echo Installing development dependencies...
    "%PY%" -m pip install -r "%ROOT_DIR%requirements-dev.txt"
    if errorlevel 1 (
        echo [ERROR] Failed to install development dependencies.
        echo         Run scripts\install.bat --dev manually.
        exit /b 1
    )
)

REM --- Check whether any test files exist ---
if not exist "%ROOT_DIR%tests\test_*.py" (
    echo [INFO] No test files found under tests/.
    echo        Tests will appear in the testing phase.
    exit /b 0
)

REM --- Run pytest ---
echo.
echo ---------------------------------------------------
echo   Running pytest
echo ---------------------------------------------------
"%PY%" -m pytest -v --tb=short
set "PYTEST_EXIT=%errorlevel%"

REM --- Lint (non-blocking) ---
echo.
echo ---------------------------------------------------
echo   Linting with ruff
echo ---------------------------------------------------
"%PY%" -m ruff check .
set "RUFF_EXIT=%errorlevel%"

REM --- Summary ---
echo.
if not "%PYTEST_EXIT%"=="0" (
    echo [FAIL] pytest exited with code %PYTEST_EXIT%.
    exit /b %PYTEST_EXIT%
)
if not "%RUFF_EXIT%"=="0" (
    echo [WARN] ruff reported issues - exit code %RUFF_EXIT%.
)

echo All checks passed.
exit /b 0
