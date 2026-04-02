@echo off
cd /d "%~dp0"
echo [1/2] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 goto :INSTALL_PY

:START_BOT
echo [2/2] Iniciando aplicacion...
if not exist ".venv" (
    echo [i] Creando entorno virtual local (.venv)...
    python -m venv .venv
)

echo [i] Verificando librerias necesarias...
".venv\Scripts\python.exe" -m pip install -r requirements.txt

echo.
echo [OK] Todo listo. Iniciando Bot...
".venv\Scripts\python.exe" app_gui.py
if errorlevel 1 (
    echo.
    echo [ERROR] Hubo un problema al ejecutar el Bot.
    pause
)
exit /b 0

:INSTALL_PY
echo [!] Python no detectado. Intentando instalacion automatica...
powershell -NoProfile -ExecutionPolicy Bypass -File "install_prereqs.ps1"
if errorlevel 1 (
    echo [ERROR] No se pudo instalar Python. Por favor instalalo desde python.org
    pause
    exit /b 1
)
goto :START_BOT
