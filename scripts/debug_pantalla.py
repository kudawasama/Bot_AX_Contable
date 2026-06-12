#!/usr/bin/env python
"""
debug_pantalla.py — Diagnóstico de captura de pantalla y monitores.

Verifica qué resolución ve PyAutoGUI y captura la pantalla principal.
Útil si el bot no encuentra elementos porque AX está en otro monitor.

Uso: python scripts/debug_pantalla.py
"""

import os
import sys

_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_script_dir)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import pyautogui

def capturar_pantallas():
    print("Capturando vista completa del bot...")

    try:
        p1 = pyautogui.screenshot()
        p1.save("vista_principal.png")
        print(f"-> Pantalla Principal guardada: {os.path.abspath('vista_principal.png')}")
    except Exception as e:
        print(f"Error capturando principal: {e}")

    size = pyautogui.size()
    print(f"-> Resolución detectada por PyAutoGUI: {size}")
    print("\n[INFO] PyAutoGUI solo 've' el monitor principal a menos que se especifique.")
    print("Si AX está en el monitor secundario, el bot puede no encontrarlo.")

if __name__ == "__main__":
    capturar_pantallas()
