@echo off
title Bot AX Contable - Lanzador
:: Lanza la GUI clasica del bot (registro de diarios en Microsoft Dynamics AX).
:: La raiz del proyecto es la carpeta de este .bat, asi que funciona en cualquier
:: unidad (H:, C:, ...) sin depender de que Google Drive este montado.
cd /d "%~dp0"
if not exist "src\ui\gui_classic.py" (
    echo ERROR: no se encontro src\ui\gui_classic.py en %~dp0
    pause
    exit /b 1
)
:: Resolver pythonw.exe (sin consola visible): instalacion local primero, luego PATH
:: descartando el stub de WindowsApps, que abre la Microsoft Store en vez de Python.
set "PYW="
for %%v in (313 312 311) do (
    if not defined PYW if exist "%LOCALAPPDATA%\Programs\Python\Python%%v\pythonw.exe" set "PYW=%LOCALAPPDATA%\Programs\Python\Python%%v\pythonw.exe"
)
if not defined PYW for /f "delims=" %%i in ('where pythonw 2^>nul') do (
    if not defined PYW (
        echo %%i | findstr /i /c:"WindowsApps" >nul || set "PYW=%%i"
    )
)
if not defined PYW (
    echo ERROR: no se encontro pythonw.exe. Instala Python 3.11+ o agregalo al PATH.
    pause
    exit /b 1
)
set PYTHONPATH=%cd%
start "" "%PYW%" -m src.ui.gui_classic
exit
