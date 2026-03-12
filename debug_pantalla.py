import pyautogui
import os

def capturar_pantallas():
    print("Capturando vista completa del bot...")
    
    # Capturar la pantalla principal (por defecto)
    try:
        p1 = pyautogui.screenshot()
        p1.save("vista_principal.png")
        print(f"-> Pantalla Principal guardada: {os.path.abspath('vista_principal.png')}")
    except Exception as e:
        print(f"Error capturando principal: {e}")

    # Información de monitores
    # PyAutoGUI toma la pantalla principal por defecto, pero podemos ver el tamaño total
    size = pyautogui.size()
    print(f"-> Resolución detectada por PyAutoGUI (Tamaño de trabajo): {size}")
    
    print("\n[INFO] PyAutoGUI generalmente solo 've' el monitor principal a menos que se especifique lo contrario.")
    print("Si AX está en el monitor secundario, es posible que el bot no lo encuentre.")

if __name__ == "__main__":
    capturar_pantallas()
