@echo off
title Bot AX Contable - Lanzador
:: Verificar que la unidad H: existe
if not exist "H:\" (
    echo ERROR: La unidad H: no esta disponible. Conecta Google Drive.
    pause
    exit /b 1
)
:: Entrar a la carpeta del proyecto
cd /d "H:\Mi unidad\Desarrollo y Proyectos\GitHub\Bot_AX_Contable"
if errorlevel 1 (
    echo ERROR: No se pudo acceder a la carpeta del proyecto.
    echo Ruta: H:\Mi unidad\Desarrollo y Proyectos\GitHub\Bot_AX_Contable
    pause
    exit /b 1
)
:: Verificar que el script existe
if not exist "src\ui\gui_classic.py" (
    echo ERROR: No se encontro src\ui\gui_classic.py en la carpeta actual.
    pause
    exit /b 1
)
:: Ejecutar la interfaz grafica
set PYTHONPATH=.
start "" "%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe" -m src.ui.gui_classic
exit
