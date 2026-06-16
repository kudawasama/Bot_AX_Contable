import pyautogui
import os

def capturar_pantallas() -> None:
    """Captura la pantalla completa principal y muestra información sobre la resolución y monitores."""
    print("Capturando vista completa de la pantalla...")
    
    script_dir: str = os.path.dirname(os.path.abspath(__file__))
    base_dir: str = os.path.dirname(script_dir)
    
    try:
        p1 = pyautogui.screenshot()
        ruta_guardado: str = os.path.join(base_dir, "vista_principal.png")
        p1.save(ruta_guardado)
        print(f"-> Pantalla Principal guardada en: {ruta_guardado}")
    except Exception as e:
        print(f"Error capturando principal: {e}")

    # Resolución detectada
    size = pyautogui.size()
    print(f"-> Resolución detectada por PyAutoGUI (Tamaño de trabajo): {size}")
    
    print("\n[INFO] PyAutoGUI generalmente solo 've' el monitor principal a menos que se especifique lo contrario.")
    print("Si AX está en un monitor secundario, es posible que el bot no lo detecte.")

if __name__ == "__main__":
    capturar_pantallas()
