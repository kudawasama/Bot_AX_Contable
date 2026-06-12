#!/usr/bin/env python
"""
check_ocr.py — Verifica que Tesseract OCR esté instalado y accesible.

Uso: python scripts/check_ocr.py
"""

import os
import sys

# Agregar raíz del proyecto al path
_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_script_dir)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from config import TESSERACT_CMD

try:
    import pytesseract
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
    print(pytesseract.get_tesseract_version())
    print("SUCCESS: Tesseract engine found!")
except Exception as e:
    print(f"FAILED: Tesseract engine not found. Error: {e}")
