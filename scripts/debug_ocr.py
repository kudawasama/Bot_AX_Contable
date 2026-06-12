#!/usr/bin/env python
"""
debug_ocr.py — Debug de coordenadas OCR.

Toma capturas de la zona alrededor de un checkbox vacío para
ajustar el offset OCR. Útil durante la configuración inicial.

Uso: python scripts/debug_ocr.py
"""

import os
import sys

_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_script_dir)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import pyautogui
import time
from config import cargar_configuracion, CHK_VACIO

def debug_captura_ocr():
    sectores = cargar_configuracion()
    sector_a = sectores.get("sector_a")

    print("Buscando primera casilla vacía para test de OCR...")
    loc = pyautogui.locateOnScreen(CHK_VACIO, region=sector_a, confidence=0.8)

    if loc:
        centro = pyautogui.center(loc)
        cx, cy = int(centro.x), int(centro.y)
        from config import obtener_offset_ocr
        ox, oy, ow, oh = obtener_offset_ocr()
        r1 = (cx + ox, cy + oy, ow, oh)
        r2 = (cx - 150, cy - 12, 140, 30)
        r3 = (cx + 30, cy - 12, 200, 30)

        print(f"Casilla encontrada en {cx, cy}")
        print(f"Offset OCR aplicado: x={ox}, y={oy}, w={ow}, h={oh}")
        pyautogui.screenshot("debug_ocr_pos1.png", region=r1)
        pyautogui.screenshot("debug_ocr_pos2.png", region=r2)
        pyautogui.screenshot("debug_ocr_pos3.png", region=r3)
        print("Se han guardado 3 imágenes (debug_ocr_pos1, pos2, pos3).")
        print("Por favor, revísalas para ver en cuál se lee mejor el número de diario.")
    else:
        print("No se encontró la casilla vacía. ¿Está el programa AX al frente?")

if __name__ == "__main__":
    debug_captura_ocr()
