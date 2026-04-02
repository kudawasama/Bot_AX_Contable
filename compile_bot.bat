@echo off
setlocal EnableDelayedExpansion
title Bot AX Contable - Compilador Nuitka
color 0E

cd /d "%~dp0"

echo.
echo ===================================================
echo   COMPILANDO BOT AX CONTABLE (NUITKA)
echo ===================================================
echo.

set "VENV_PYTHON=.venv\Scripts\python.exe"

if not exist "!VENV_PYTHON!" (
    echo [!] No se encontro el entorno .venv. Ejecuta Lanzar_Bot_Universal.bat primero.
    pause
    exit /b 1
)

echo [1/3] Verificando Nuitka...
!VENV_PYTHON! -m pip install nuitka zstandard >nul

echo [2/3] Iniciando Compilacion (Esto puede tardar varios minutos)...
echo [i] Nuitka traducira el codigo a C y lo compilara para maxima seguridad.
echo.

REM COMANDO DE COMPILACIÓN
REM --standalone: incluye dependencias
REM --onefile: genera un unico .exe (mas lento de abrir, mas facil de distribuir)
REM --windows-disable-console: oculta la terminal negra
REM --plugin-enable=tk-inter: necesario para el GUI
REM --follow-imports: sigue las importaciones a los modulos locales
REM --include-module=license_manager,bot_main,setup_areas,tesseract_util: asegura inclusios de modulos clave

!VENV_PYTHON! -m nuitka ^
    --standalone ^
    --onefile ^
    --windows-disable-console ^
    --plugin-enable=tk-inter ^
    --follow-imports ^
    --output-dir=dist ^
    --output-filename=Bot_AX_Contable.exe ^
    app_gui.py

if %errorlevel% equ 0 (
    echo.
    echo [OK] Compilacion Exitosa.
    echo [i] El archivo generado esta en: dist\Bot_AX_Contable.exe
    echo.
) else (
    echo.
    echo [ERROR] La compilacion ha fallado. Revisa los mensajes arriba.
    echo.
)

pause
exit /b 0
