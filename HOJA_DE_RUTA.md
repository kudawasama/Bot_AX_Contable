# Hoja de Ruta: Bot AX Contable (Resumen de Profesionalización)

Este documento resume el trabajo realizado para transformar el script de desarrollo en un **producto comercial blindado y portable**. Debido a restricciones de antivirus (ESET) en el entorno laboral, la compilación final debe realizarse en un equipo personal (notebook).

## 1. Estado Actual del Proyecto
El código ha sido auditado y está listo para ser distribuido como un único archivo `.exe`.

*   **Rutas Inteligentes (`path_utils.py`)**: El Bot ahora distingue entre recursos internos (empaquetados en el `.exe`) y externos (licencia, logs).
*   **Seguridad HWID (`license_manager.py`)**: El sistema de licencias está vinculado al hardware y busca el archivo `license.key` fuera del `.exe`.
*   **Auto-Actualizador (`updater_manager.py`)**: Capacidad de buscar versiones en GitHub y auto-reemplazar el ejecutable.
*   **Acceso Directo (`shortcut_manager.py`)**: Crea automáticamente un icono en el escritorio al primer inicio.
*   **Comentarios**: 100% en español según lo solicitado.

## 2. Archivos Críticos a Revisar
- **`app_gui.py`**: Interfaz principal con integración de tareas de fondo.
- **`compile_local.ps1`**: Script de PowerShell diseñado para compilar en local (más rápido y seguro que Drive).
- **`requirements.txt`**: Incluye `requests` y `zstandard` para Nuitka.

## 3. Instrucciones para la Notebook (Casa)
Cuando abras el proyecto en tu equipo personal, sigue estos pasos:

1.  **Sincronizar**: Haz un `git pull` para recibir todos los cambios que acabo de subir.
2.  **Preparar Entorno**:
    - Asegúrate de tener Python instalado (preferiblemente 3.10 o superior).
    - Recomiendo desactivar temporalmente el antivirus local antes de compilar para evitar el error de "Failed to add resources".
3.  **Compilar**: 
    - Abre una terminal de PowerShell en la carpeta del proyecto.
    - Ejecuta: `powershell -ExecutionPolicy Bypass -File "compile_local.ps1"`
4.  **Resultado**: 
    - El archivo final aparecerá en la carpeta `dist/Bot_AX_Contable.exe`.
    - **¡Ese es el único archivo que necesitas entregar a tus clientes!**

## 4. Pendientes Finales
- Configurar la URL real de `version.json` en `updater_manager.py` (Línea 11) si deseas activar las actualizaciones automáticas ahora mismo.

---
**El proyecto ha sido Commiteado y Pusheado con éxito.** ¡Suerte con la compilación en casa!
