@echo off
title Bot AX Contable - Lanzador Universal
color 0A

REM Este script no depende de rutas específicas
REM Se ejecutará desde donde esté el archivo .bat

echo.
echo ===============================================
echo   Bot AX Contable - Iniciador Universal
echo ===============================================
echo.

REM Obtener la ruta actual del script
cd /d "%~dp0"

echo Directorio: %cd%
echo.

REM Verificar si Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python no está instalado o no está en PATH
    echo Descarga Python desde: https://www.python.org/downloads/
    echo IMPORTANTE: Marca la opción "Add Python to PATH" durante la instalación
    pause
    exit /b 1
)

REM Verificar si existen los archivos necesarios
if not exist "app_gui.py" (
    echo ERROR: app_gui.py no encontrado en %cd%
    pause
    exit /b 1
)

if not exist "config_sectores.json" (
    echo ADVERTENCIA: config_sectores.json no encontrado
    echo Se creará al configurar las áreas
)

echo Verificando dependencias de Python...
pip show pyautogui >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo Instalando dependencias necesarias...
    echo Esto puede tardar algunos minutos...
    echo.
    pip install -r requirements.txt --verbose
    if %errorlevel% neq 0 (
        echo.
        echo ===============================================
        echo ERROR: No se pudieron instalar las dependencias
        echo ===============================================
        echo.
        echo Por favor, intenta ejecutar manualmente:
        echo   python -m pip install --upgrade pip
        echo   python -m pip install -r requirements.txt
        echo.
        echo Si el error persiste, copia el mensaje de error arriba
        echo y comparte con soporte.
        echo.
        pause
        exit /b 1
    )
)

REM Verificar Tesseract-OCR
python -c "import pytesseract; pytesseract.pytesseract.pytesseract_cmd" >nul 2>&1
echo.
echo Verificando Tesseract-OCR...

REM Intentar encontrar Tesseract en rutas comunes
set TESSERACT_FOUND=0

REM Buscar en Program Files
if exist "C:\Program Files\Tesseract-OCR\tesseract.exe" (
    set TESSERACT_FOUND=1
    set TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
)

REM Buscar en Program Files (x86) para sistemas 32-bit
if exist "C:\Program Files (x86)\Tesseract-OCR\tesseract.exe" (
    set TESSERACT_FOUND=1
    set TESSERACT_PATH=C:\Program Files (x86)\Tesseract-OCR\tesseract.exe
)

if %TESSERACT_FOUND% equ 0 (
    echo.
    echo ADVERTENCIA: Tesseract-OCR no está instalado o no se encontró
    echo.
    echo Necesitas descargar e instalar Tesseract-OCR:
    echo 1. Descargar desde: https://github.com/UB-Mannheim/tesseract/wiki
    echo 2. Ejecutar el instalador (tesseract-ocr-w64-setup-v5.x.exe)
    echo 3. Aceptar la ruta de instalación por defecto
    echo 4. Ejecutar este script nuevamente
    echo.
    pause
    exit /b 1
) else (
    echo Tesseract encontrado en: %TESSERACT_PATH%
)

echo.
echo ===============================================
echo   Iniciando Bot AX Contable...
echo ===============================================
echo.

REM Ejecutar el bot y mostrar cualquier error
python app_gui.py

REM Si hay error, mostrar y no cerrar
if %errorlevel% neq 0 (
    echo.
    echo ===============================================
    echo ERROR AL EJECUTAR EL BOT
    echo ===============================================
    echo.
    echo Si ves errores de importación arriba, intenta:
    echo   python -m pip install --upgrade pip
    echo   python -m pip install -r requirements.txt
    echo.
    pause
)

exit /b 0
