import pyautogui
import os
from datetime import datetime

def diagnose():
    print(f"Primary screen size: {pyautogui.size()}")
    
    # Intento de captura de pantalla completa
    try:
        ts = datetime.now().strftime("%H%M%S")
        screenshot_path = f"diag_full_screen_{ts}.png"
        pyautogui.screenshot(screenshot_path)
        print(f"Full screen screenshot saved to {screenshot_path}")
    except Exception as e:
        print(f"Error capturing full screen: {e}")

    # Verificar existencia de patrones
    patrones = ["patrones/checkbox_vacio.png", "patrones/btn_registrar_menu.png"]
    for p in patrones:
        if os.path.exists(p):
            print(f"Checking pattern: {p}")
            try:
                # Buscar en toda la pantalla con confianza 0.9 (como el bot)
                pos = pyautogui.locateOnScreen(p, confidence=0.9, grayscale=True)
                if pos:
                    print(f"  -> FOUND at {pos}")
                else:
                    print("  -> NOT FOUND on screen (confidence 0.7)")
            except Exception as e:
                import traceback
                print(f"  -> Error searching: {e}")
                traceback.print_exc()
        else:
            print(f"Pattern file MISSING: {p}")

if __name__ == "__main__":
    diagnose()
