import pyautogui
import os
from datetime import datetime

def diagnose() -> None:
    """Realiza un diagnóstico de la pantalla y la detección de patrones visuales de AX."""
    print(f"Primary screen size: {pyautogui.size()}")
    
    # Intento de captura de pantalla completa para depuración
    script_dir: str = os.path.dirname(os.path.abspath(__file__))
    base_dir: str = os.path.dirname(script_dir)
    
    try:
        ts: str = datetime.now().strftime("%H%M%S")
        screenshot_path: str = os.path.join(base_dir, f"diag_full_screen_{ts}.png")
        pyautogui.screenshot(screenshot_path)
        print(f"Full screen screenshot saved to {screenshot_path}")
    except Exception as e:
        print(f"Error capturing full screen: {e}")

    # Verificar existencia y detección de patrones clave
    patrones = [
        os.path.join(base_dir, "patrones", "checkbox_vacio.png"), 
        os.path.join(base_dir, "patrones", "btn_registrar_menu.png")
    ]
    
    for p in patrones:
        if os.path.exists(p):
            print(f"Checking pattern: {p}")
            try:
                # Buscar en toda la pantalla con la confianza ajustada del bot (0.85)
                pos = pyautogui.locateOnScreen(p, confidence=0.85, grayscale=True)
                if pos:
                    print(f"  -> FOUND at {pos}")
                else:
                    print("  -> NOT FOUND on screen (confidence 0.85)")
            except Exception as e:
                import traceback
                print(f"  -> Error searching: {e}")
                traceback.print_exc()
        else:
            print(f"Pattern file MISSING: {p}")

if __name__ == "__main__":
    diagnose()
