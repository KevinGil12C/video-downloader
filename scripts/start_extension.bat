@echo off
setlocal EnableExtensions

cd /d "%~dp0.."
set "PROJECT_ROOT=%CD%"
set "EXTENSION_DIR=%PROJECT_ROOT%\extension"
set "PYTHON=%PROJECT_ROOT%\venv\Scripts\python.exe"

if not exist "%EXTENSION_DIR%\manifest.json" (
    echo ERROR: No se encontro la extension en:
    echo %EXTENSION_DIR%
    pause
    exit /b 1
)

if not exist "%PYTHON%" (
    set "PYTHON=py"
)

echo Iniciando Video Downloader en http://127.0.0.1:8000 ...
start "Video Downloader Backend" cmd /k ""%PYTHON%" -m uvicorn app.backend.server:app --host 127.0.0.1 --port 8000"

timeout /t 3 /nobreak >nul
start "" explorer.exe "%EXTENSION_DIR%"
start "" "chrome://extensions/"
start "" "edge://extensions/"

echo.
echo En el navegador:
echo 1. Activa Modo desarrollador.
echo 2. Pulsa Cargar extension sin comprimir.
echo 3. Selecciona:
echo    %EXTENSION_DIR%
echo.
pause
