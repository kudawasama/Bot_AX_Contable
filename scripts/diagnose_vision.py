#!/usr/bin/env python
"""
diagnose_vision.py — Diagnóstico de detección de patrones visuales.

Verifica la resolución de pantalla y busca los patrones de imagen
en la pantalla actual. Útil para debug de template matching.

Uso: python scripts/diagnose_vision.py
"""

import os
import sys
from datetime import datetime

_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_script_dir)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import pyautogui
from PIL import Image

def diagnose():
    print(f"Primary screen size: {pyautogui.size()}")

    try:
        ts = datetime.now().strftime("%H%M%S")
        screenshot_path = f"diag_full_screen_{ts}.png"
        pyautogui.screenshot(screenshot_path)
        print(f"Full screen screenshot saved to {screenshot_path}")
    except Exception as e:
        print(f"Error capturing full screen: {e}")

    patrones = ["patrones/checkbox_vacio.png", "patrones/btn_registrar_menu.png"]
    for p in patrones:
        full_path = os.path.join(_project_root, p)
        if os.path.exists(full_path):
            print(f"Checking pattern: {full_path}")
            try:
                pos = pyautogui.locateOnScreen(full_path, confidence=0.9, grayscale=True)
                if pos:
                    print(f"  -> FOUND at {pos}")
                else:
                    print(f"  -> NOT FOUND on screen (confidence 0.9)")
            except Exception as e:
                import traceback
                print(f"  -> Error searching: {e}")
                traceback.print_exc()
        else:
            print(f"Pattern file MISSING: {full_path}")

if __name__ == "__main__":
    diagnose()
