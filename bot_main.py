import sys
import time
import pyautogui
from config import cargar_configuracion, CHK_VACIO, BTN_MENU, BTN_CONFIRM, CHK_MARCADO, IMG_ERROR
from vision import buscar_y_clickear, buscar_estado_checkbox, esperar_resultado_registro, leer_id_diario
import keyboard
import pyautogui as gui
from datetime import datetime

def registrar_log(id_diario, resultado):
    """Guarda el resultado del procesamiento en un archivo TXT por día."""
    ahora = datetime.now()
    fecha_hoy = ahora.strftime("%Y-%m-%d")
    nombre_archivo = f"registro_{fecha_hoy}.txt"
    timestamp = ahora.strftime("%H:%M:%S")
    linea = f"[{timestamp}] Diario: {id_diario} - Resultado: {resultado}\n"
    with open(nombre_archivo, "a", encoding="utf-8") as f:
        f.write(linea)

# Ciclo principal de ejecución
def run_bot():
    print("Iniciando Bot AX Contable...")
    
    # 1. Cargar la configuración de los sectores
    sectores = cargar_configuracion()
    if not sectores:
        print("ERROR: Sectores A y B no están definidos.")
        print("Por favor ejecuta primero 'python setup_areas.py' para seleccionar las áreas.")
        sys.exit(1)
        
    sector_a = sectores.get("sector_a")
    sector_b = sectores.get("sector_b")

    print("\n[Instrucción] El bot se ejecutará en bucle.")
    print("[Instrucción] MANTÉN PRESIONADA LA TECLA 'ESC' PARA DETENER EL BOT EN CUALQUIER MOMENTO.\n")
    time.sleep(2) 

    ciclo = 1
    diarios_con_error = [] # Lista negra de IDs que fallaron
    
    print("\n--- CONFIGURACIÓN OCR ACTIVA ---")
    print(f"Buscando casillas en Sector A...")
    
    try:
        while True:
            if keyboard.is_pressed('esc'):
                print("Bot detenido por el usuario (ESC).")
                break
                
            print(f"\n--- Iniciando Ciclo {ciclo} ---")
            
            # Paso A: Buscar casillas vacías
            # Usamos locateAllOnScreen para ver todas las que hay en el sector
            try:
                todas_vacias = list(gui.locateAllOnScreen(CHK_VACIO, region=sector_a, confidence=0.9, grayscale=True))
                # Ordenar de arriba hacia abajo
                todas_vacias.sort(key=lambda loc: loc.top)
            except Exception as e:
                print(f"Error buscando casillas: {e}")
                todas_vacias = []

            if not todas_vacias:
                print("No se encontró ningún checkbox vacío. Fin de la lista.")
                break 

            # Intentar procesar la primera casilla que no esté en la lista negra
            casilla_objetivo = None
            id_actual = "DESCONOCIDO"

            for i, loc in enumerate(todas_vacias):
                centro = gui.center(loc)
                coord = (int(centro.x), int(centro.y))
                
                # Leer el ID de esta casilla
                identificador = leer_id_diario(coord)
                print(f"Analizando Fila Visual {i+1}: ID '{identificador}'")

                if identificador in diarios_con_error:
                    print(f"  -> Ignorando {identificador} (está en lista negra por error previo).")
                    continue
                
                # Si llegamos aquí, es una fila válida
                casilla_objetivo = coord
                id_actual = identificador
                break

            if not casilla_objetivo:
                print("Todas las casillas visibles están en la lista negra o no hay más para procesar.")
                break

            print(f"==> PROCESANDO DIARIO: {id_actual}")
            # duration: Velocidad del mouse al ir a la casilla (0.5 segundos)
            gui.moveTo(casilla_objetivo[0], casilla_objetivo[1], duration=0.5)
            gui.click()
            punto_click_a = casilla_objetivo
            time.sleep(1)
             # Paso B: Menú Registrar
            encontrado_menu = buscar_y_clickear(
                ruta_imagen=BTN_MENU, 
                sector_region=sector_b,
                timeout=12
            )

            if not encontrado_menu:
                print("Error: No se encontró el botón de registrar.")
                break
            
            # Paso C: Confirmación
            time.sleep(0.8) 
            encontrado_confirm = buscar_y_clickear(
                ruta_imagen=BTN_CONFIRM, 
                timeout=20,
                confidencialidad=0.8
            )
            
            if not encontrado_confirm:
                 print("Error: No se encontró la confirmación.")
                 break
            
            # Paso D: Esperar resultado
            px, py = punto_click_a
            region_especifica_checkbox = (int(px)-20, int(py)-20, 40, 40)
            time.sleep(2)
            
            resultado = esperar_resultado_registro(
                ruta_obj_exito=CHK_MARCADO,
                ruta_obj_error=IMG_ERROR,
                sector_region=region_especifica_checkbox,
                timeout=3600
            )
            
            if resultado == 'exito':
                print(f"-> Registro de {id_actual} completado exitosamente.")
                registrar_log(id_actual, "EXITOSO")
                time.sleep(1)
                
            elif resultado == 'error':
                 print(f"Se detectó un Error en {id_actual}. Agregando a lista negra.")
                 registrar_log(id_actual, "ERROR")
                 diarios_con_error.append(id_actual)
                 gui.press('esc')
                 # Pausa para que AX cierre el cartel de error antes de seguir
                 time.sleep(2) 
            else:
                 print("Timeout extremo alcanzado.")
                 break
                 
            ciclo += 1
            # Pausa de seguridad entre ciclos
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nBot detenido manualmente.")
        
    print("\nEjecución finalizada.")

if __name__ == "__main__":
    run_bot()
