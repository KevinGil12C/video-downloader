@echo off
setlocal EnableExtensions
title Video Downloader Local - Uninstall

set "ROOT_DIR=%~dp0"
for %%I in ("%ROOT_DIR%..") do set "ROOT_DIR=%%~fI\"
set "VENV_DIR=%ROOT_DIR%venv"
set "REMOVE_DATA=0"

if /i "%~1"=="--all" set "REMOVE_DATA=1"

echo.
echo ===================================================
echo   Video Downloader Local - Uninstall
echo ===================================================
echo.
echo This will remove the virtual environment and installed packages.
if "%REMOVE_DATA%"=="1" (
    echo It will also delete the "downloads" and "logs" folders.
)
echo.

choice /c YN /m "Continue"
if errorlevel 2 (
    echo.
    echo Aborted.
    exit /b 0
)
echo.

REM ---------- Remove virtual environment ----------
if exist "%VENV_DIR%" (
    echo Removing virtual environment...
    rmdir /s /q "%VENV_DIR%"
    echo        Done.
) else (
    echo No virtual environment found.
)

REM ---------- Optional: remove downloaded files ----------
if "%REMOVE_DATA%"=="1" (
    echo.
    if exist "%ROOT_DIR%downloads" (
        echo Removing downloads folder...
        rmdir /s /q "%ROOT_DIR%downloads"
    )
    if exist "%ROOT_DIR%logs" (
        echo Removing logs folder...
        rmdir /s /q "%ROOT_DIR%logs"
    )
    echo User data removed.
) else (
    echo.
    echo Your downloaded files in downloads/ and logs/ were preserved.
    echo Use --all to remove them as well.
)

echo.
echo Uninstall complete.
echo.
endlocal
exit /b 0
