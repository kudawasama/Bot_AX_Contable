"""
Resolución portable de la ruta del ejecutable Tesseract (PATH, env, rutas típicas Windows).
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

_LOCAL_FILE = "tesseract_path.local.txt"


def _path_from_local_file():
    """Primera ruta válida en tesseract_path.local.txt (misma carpeta que este módulo)."""
    p = Path(__file__).resolve().parent / _LOCAL_FILE
    if not p.is_file():
        return None
    try:
        text = p.read_text(encoding="utf-8-sig", errors="ignore")
    except OSError:
        return None
    for raw in text.splitlines():
        line = raw.strip().strip('"').strip()
        if not line or line.startswith("#"):
            continue
        if os.path.isfile(line):
            return line
    return None


def find_tesseract_executable():
    """
    Devuelve la ruta a tesseract.exe si se encuentra, o None.
    Orden:
      1. Archivo tesseract_path.local.txt (una ruta por línea; ignora # comentarios)
      2. Variable de entorno TESSERACT_CMD
      3. Comando tesseract en el PATH
      4. Rutas típicas en Program Files (Windows)
    """
    local = _path_from_local_file()
    if local:
        return local

    env = (os.environ.get("TESSERACT_CMD") or "").strip().strip('"')
    if env and os.path.isfile(env):
        return env

    which = shutil.which("tesseract")
    if which and os.path.isfile(which):
        return which

    for ruta in (
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ):
        if os.path.isfile(ruta):
            return ruta

    return None
