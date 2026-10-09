@echo off
title Bot AX Registro - Lanzador Gemini Engine
:: Portabilidad (hallazgo C-6): la raiz del proyecto es la carpeta que contiene
:: este .bat, no una ruta fija. Funciona montado en H:, C:, G:, etc.
cd /d "%~dp0"
if errorlevel 1 (
    echo ERROR: No se pudo acceder a la carpeta del proyecto: %~dp0
    pause
    exit /b 1
)
:: Verificar que el script existe
if not exist "src\ui\gui_gemini.py" (
    echo ERROR: No se encontro src\ui\gui_gemini.py en la carpeta actual.
    pause
    exit /b 1
)
:: Resolver interprete (primera coincidencia disponible):
::   1) Instalacion oficial de Python 3.12 del usuario (la que usa el bot)
::   2) pythonw.exe del PATH del sistema
set "PYW="
if exist "%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe" set "PYW=%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe"
if not defined PYW for /f "delims=" %%i in ('where pythonw 2^>nul') do if not defined PYW set "PYW=%%i"
if not defined PYW (
    echo ERROR: No se encontro pythonw.exe. Instala Python 3.11+ o agregalo al PATH.
    pause
    exit /b 1
)
:: Ejecutar la interfaz grafica
set PYTHONPATH=%cd%
start "" "%PYW%" -m src.ui.gui_gemini
exit
