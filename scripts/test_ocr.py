"""Verificación del motor Tesseract OCR usando la misma ruta que el bot.

Uso:
    python scripts/test_ocr.py
"""

import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytesseract

from src.core.config import TESSERACT_CMD


def resolver_tesseract() -> str | None:
    """Localiza el ejecutable de Tesseract: primero la ruta configurada, luego el PATH."""
    if os.path.exists(TESSERACT_CMD):
        return TESSERACT_CMD
    return shutil.which("tesseract")


def main() -> None:
    """Verifica si el motor Tesseract está accesible y muestra su versión instalada."""
    ruta = resolver_tesseract()
    if not ruta:
        print("FAILED: Tesseract no encontrado.")
        print(f"  Ruta configurada: {TESSERACT_CMD}")
        print("  Instálalo desde https://github.com/UB-Mannheim/tesseract/wiki")
        print("  o define la variable de entorno TESSERACT_CMD con la ruta correcta.")
        sys.exit(1)

    pytesseract.pytesseract.tesseract_cmd = ruta
    try:
        version = pytesseract.get_tesseract_version()
    except Exception as e:  # noqa: BLE001 - el diagnóstico debe reportar cualquier fallo
        print(f"FAILED: Tesseract no responde. Error: {e}")
        sys.exit(1)

    print(f"OK: Tesseract encontrado en {ruta}")
    print(f"SUCCESS: Version: {version}")


if __name__ == "__main__":
    main()
