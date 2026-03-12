import pyautogui
import time
import os
from config import cargar_configuracion, CHK_VACIO
import pyautogui as gui

# Este script buscará la primera casilla y guardará lo que ve a su derecha para ajustar el OCR
def debug_captura_ocr():
    sectores = cargar_configuracion()
    sector_a = sectores.get("sector_a")
    
    print("Buscando primera casilla vácía para test de OCR...")
    loc = gui.locateOnScreen(CHK_VACIO, region=sector_a, confidence=0.8)
    
    if loc:
        centro = gui.center(loc)
        cx, cy = int(centro.x), int(centro.y)
        
        # Intentamos capturar hacia la IZQUIERDA (donde suele estar el ID)
        # Una franja larga a la izquierda
        r1 = (cx - 320, cy - 12, 300, 30)
        # Una franja central
        r2 = (cx - 150, cy - 12, 140, 30)
        # Una franja a la derecha (por si acaso)
        r3 = (cx + 30, cy - 12, 200, 30)
        
        print(f"Casilla encontrada en {cx, cy}")
        pyautogui.screenshot("debug_ocr_pos1.png", region=r1)
        pyautogui.screenshot("debug_ocr_pos2.png", region=r2)
        pyautogui.screenshot("debug_ocr_pos3.png", region=r3)
        
        print("Se han guardado 3 imágenes (debug_ocr_pos1, pos2, pos3).")
        print("Por favor, revísalas para ver en cuál se lee mejor el número de diario.")
    else:
        print("No se encontró la casilla vacía. ¿Está el programa AX al frente?")

if __name__ == "__main__":
    debug_captura_ocr()
