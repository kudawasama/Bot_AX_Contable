"""
Resolución portable de la ruta del ejecutable Tesseract (PATH, env, rutas típicas Windows).
"""

from __future__ import annotations
import os
import sys
import shutil
from pathlib import Path
from path_utils import get_resource_path, get_external_path

# Archivo opcional para forzar una ruta de Tesseract localmente
_LOCAL_FILE = "tesseract_path.local.txt"

def _path_from_local_file():
    """Busca la primera ruta válida en tesseract_path.local.txt."""
    # Buscamos el archivo de configuración al lado del ejecutable
    p = Path(get_external_path(_LOCAL_FILE))
    if not p.is_file():
        return None
    try:
        texto = p.read_text(encoding="utf-8-sig", errors="ignore")
    except OSError:
        return None
    for linea_cruda in texto.splitlines():
        linea = linea_cruda.strip().strip('"').strip()
        if not linea or linea.startswith("#"):
            continue
        if os.path.isfile(linea):
            return linea
    return None

def find_tesseract_executable():
    """
    Devuelve la ruta al ejecutable tesseract.exe si se encuentra.
    Prioridad:
      1. Archivo tesseract_path.local.txt
      2. Carpeta local bin/tesseract (al lado del ejecutable)
      3. Variable de entorno TESSERACT_CMD
      4. Comando tesseract en el PATH de Windows
      5. Rutas típicas en Program Files
    """
    local = _path_from_local_file()
    if local:
        return local

    # Nueva prioridad: Carpeta local bin/tesseract (empaquetada o al lado del exe)
    ruta_bin_proyecto = Path(get_resource_path("bin/tesseract/tesseract.exe"))
    if ruta_bin_proyecto.is_file():
        return str(ruta_bin_proyecto)

    # Buscar en variables de entorno del sistema
    env = (os.environ.get("TESSERACT_CMD") or "").strip().strip('"')
    if env and os.path.isfile(env):
        return env

    # Buscar en el PATH de Windows
    en_path = shutil.which("tesseract")
    if en_path and os.path.isfile(en_path):
        return en_path

    # Buscar en rutas estándar de instalación de Windows
    for ruta in (
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ):
        if os.path.isfile(ruta):
            return ruta

    return None
