import pyautogui
import os
import sys
import pyautogui as gui

# Asegurar que la raíz del proyecto esté en el path de Python
script_dir: str = os.path.dirname(os.path.abspath(__file__))
base_dir: str = os.path.dirname(script_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from src.core.config import cargar_configuracion, CHK_VACIO, obtener_offset_ocr

def debug_captura_ocr() -> None:
    """Busca el primer checkbox vacío en Sector A y guarda 3 capturas del área derecha para calibrar OCR."""
    sectores = cargar_configuracion()
    if not sectores:
        print("ERROR: Sectores no definidos en config_sectores.json.")
        return
        
    sector_a = sectores.get("sector_a")
    if not sector_a:
        print("ERROR: Sector A no definido en configuración.")
        return
    
    print("Buscando primera casilla vacía para test de OCR...")
    # Usar el umbral óptimo del bot (0.85)
    loc = gui.locateOnScreen(CHK_VACIO, region=sector_a, confidence=0.85)
    
    if loc:
        centro = gui.center(loc)
        cx, cy = int(centro.x), int(centro.y)
        print(f"Casilla encontrada en {cx, cy}")
        
        ox, oy, ow, oh = obtener_offset_ocr(sectores)
        r1 = (cx + ox, cy + oy, ow, oh)
        r2 = (cx - 150, cy - 12, 140, 30)
        r3 = (cx + 30, cy - 12, 200, 30)
        
        print(f"Offset OCR aplicado: x={ox}, y={oy}, w={ow}, h={oh}")
        
        # Guardar capturas de prueba en la raíz del proyecto
        gui.screenshot(os.path.join(base_dir, "debug_ocr_pos1.png"), region=r1)
        gui.screenshot(os.path.join(base_dir, "debug_ocr_pos2.png"), region=r2)
        gui.screenshot(os.path.join(base_dir, "debug_ocr_pos3.png"), region=r3)
        
        print("Se han guardado 3 imágenes en la raíz del proyecto:")
        print("  - debug_ocr_pos1.png (Región offset actual)")
        print("  - debug_ocr_pos2.png (Franja izquierda de respaldo)")
        print("  - debug_ocr_pos3.png (Franja derecha de respaldo)")
        print("Por favor, revísalas para verificar en cuál se lee mejor el número de diario.")
    else:
        print("No se encontró la casilla vacía. ¿Está el programa AX al frente?")

if __name__ == "__main__":
    debug_captura_ocr()
