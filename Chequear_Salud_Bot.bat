@echo off
title Bot AX Contable - Chequeo de salud
:: Utilidad de SOLO LECTURA: revisa la salud del bot y muestra el informe.
:: No toca el bot en ejecucion ni la pantalla, asi que se puede usar en cualquier momento.
:: La raiz del proyecto es la carpeta de este .bat (funciona en cualquier unidad).
cd /d "%~dp0"
if not exist "scripts\chequeo_salud.py" (
    echo ERROR: no se encontro scripts\chequeo_salud.py en %~dp0
    pause
    exit /b 1
)
:: Resolver interprete (primera coincidencia disponible)
set "PY="
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PY=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if not defined PY for /f "delims=" %%i in ('where python 2^>nul') do if not defined PY set "PY=%%i"
if not defined PY (
    echo ERROR: No se encontro Python. Instala Python 3.11+ o agregalo al PATH.
    pause
    exit /b 1
)
set PYTHONPATH=%cd%
"%PY%" scripts\chequeo_salud.py
echo.
pause
