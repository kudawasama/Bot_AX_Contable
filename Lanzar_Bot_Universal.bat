@echo off
setlocal EnableDelayedExpansion
title Bot AX Contable - Lanzador Universal
color 0A

REM Un solo doble clic: PowerShell instala Python + Tesseract si faltan (winget o descarga),
REM luego pip instala Pillow, OpenCV, etc. Requiere conexion a Internet la primera vez.
REM Desactivar instalacion automatica del sistema: set BOT_AX_NO_AUTO=1
REM (o BOT_AX_NO_WINGET=1 por compatibilidad)

echo.
echo ===============================================
echo   Bot AX Contable - Iniciador Universal
echo ===============================================
echo.

cd /d "%~dp0"

echo Directorio: %cd%
echo.

if not defined BOT_AX_NO_AUTO if not defined BOT_AX_NO_WINGET (
  echo [1/3] Comprobando Python y Tesseract ^(puede tardar y pedir permisos^)...
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_prereqs.ps1"
  if errorlevel 1 (
    echo.
    echo ERROR: No se pudieron instalar o encontrar Python 3.10+ y/o Tesseract.
    echo Revisa logs\install_prereqs.log — o instala manualmente y vuelve a ejecutar.
    echo.
    pause
    exit /b 1
  )
  echo.
)

set "PY="
call :DetectPython
if errorlevel 1 (
  pause
  exit /b 1
)
if not defined PY (
  echo ERROR: No se encontro Python 3.10+ despues del instalador automatico.
  echo Revisa install_prereqs.ps1 y logs\install_prereqs.log
  pause
  exit /b 1
)

echo [2/3] Python: !PY!
!PY! --version

if not exist "app_gui.py" (
  echo ERROR: app_gui.py no encontrado en %cd%
  pause
  exit /b 1
)

if not exist "config_sectores.json" (
  echo ADVERTENCIA: config_sectores.json no encontrado — se creara al configurar areas
)

echo.
echo [3/3] Paquetes pip ^(Pillow, OpenCV, pyautogui...^)...
!PY! -m pip install --upgrade pip setuptools wheel
echo Limpiando Pillow y pyscreeze existentes...
!PY! -m pip uninstall -y Pillow pyscreeze pyautogui >nul 2>&1
echo Instalando Pillow>=10.2.0, pyscreeze y dependencias...
!PY! -m pip install --upgrade "Pillow>=10.2.0,<12" "pyscreeze>=0.1.30"
!PY! -m pip install -r requirements.txt
if !errorlevel! neq 0 (
  echo ERROR: pip install fallo. Ejecuta manualmente:
  echo   !PY! -m pip install -r requirements.txt
  pause
  exit /b 1
)
echo Verificando pyautogui y pyscreeze...
!PY! -c "import pyautogui; import pyscreeze; print('OK: pyautogui y pyscreeze funcionales')"
if !errorlevel! neq 0 (
  echo ERROR: pyautogui/pyscreeze no funcionan. Revisa Pillow.
  pause
  exit /b 1
)

echo Verificando Tesseract desde Python...
!PY! -c "from tesseract_util import find_tesseract_executable; import sys; sys.exit(0 if find_tesseract_executable() else 1)" >nul 2>&1
if !errorlevel! neq 0 (
  echo ERROR: tesseract.exe no localizable por el bot.
  echo Crea tesseract_path.local.txt con la ruta ^(ver .example^) o reinstala Tesseract.
  pause
  exit /b 1
)

for /f "delims=" %%i in ('!PY! -c "from tesseract_util import find_tesseract_executable; print(find_tesseract_executable() or '')"') do set TESSERACT_PATH=%%i
echo Tesseract: %TESSERACT_PATH%

!PY! -c "import cv2" >nul 2>&1
if !errorlevel! neq 0 (
  echo Instalando OpenCV...
  !PY! -m pip install -r requirements.txt
  if !errorlevel! neq 0 (
    pause
    exit /b 1
  )
)

echo.
echo ===============================================
echo   Iniciando Bot AX Contable...
echo ===============================================
echo.

!PY! app_gui.py

if !errorlevel! neq 0 (
  echo.
  echo ERROR AL EJECUTAR EL BOT. Revisa el mensaje arriba.
  echo   !PY! -m pip install -r requirements.txt
  pause
)

exit /b 0

REM ---------------------------------------------------------------------------
:DetectPython
if exist "python_cmd.local.txt" (
  for /f "usebackq delims=" %%P in ("python_cmd.local.txt") do set "PY=%%P"
  set "PY=!PY:"=!"
  if exist "!PY!" (
    "!PY!" -c "import sys; exit(0 if sys.version_info[:2]>=(3,10) else 1)" >nul 2>&1
    if !errorlevel! neq 0 (
      echo ERROR: python_cmd.local.txt no es un Python 3.10+ valido.
      exit /b 1
    )
    exit /b 0
  )
)
if defined PY (
  "!PY!" -c "import sys; exit(0 if sys.version_info[:2]>=(3,10) else 1)" >nul 2>&1
  if !errorlevel! equ 0 exit /b 0
  set "PY="
)
python -c "import sys; exit(0 if sys.version_info[:2]>=(3,10) else 1)" >nul 2>&1
if !errorlevel! equ 0 set "PY=python"
if defined PY exit /b 0
for %%V in (12 11 10) do (
  if not defined PY (
    py -3.%%V -c "import sys; exit(0 if sys.version_info[:2]>=(3,10) else 1)" >nul 2>&1
    if !errorlevel! equ 0 set "PY=py -3.%%V"
  )
)
if not defined PY (
  if exist "%LocalAppData%\Programs\Python\Python312\python.exe" (
    "%LocalAppData%\Programs\Python\Python312\python.exe" -c "import sys; exit(0 if sys.version_info[:2]>=(3,10) else 1)" >nul 2>&1
    if !errorlevel! equ 0 set "PY=%LocalAppData%\Programs\Python\Python312\python.exe"
  )
)
if not defined PY (
  if exist "%LocalAppData%\Programs\Python\Python311\python.exe" (
    "%LocalAppData%\Programs\Python\Python311\python.exe" -c "import sys; exit(0 if sys.version_info[:2]>=(3,10) else 1)" >nul 2>&1
    if !errorlevel! equ 0 set "PY=%LocalAppData%\Programs\Python\Python311\python.exe"
  )
)
exit /b 0
