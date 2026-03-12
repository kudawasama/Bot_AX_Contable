import sys
import time
import pyautogui
from config import cargar_configuracion, CHK_VACIO, BTN_MENU, BTN_CONFIRM, CHK_MARCADO, IMG_ERROR, BTN_ABAJO
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
    sector_scroll = sectores.get("sector_scroll")

    if not sector_scroll:
        print("ADVERTENCIA: No se encontró la configuración del Sector Scroll (Sector C).")
        print("Se recomienda volver a ejecutar 'python setup_areas.py' para seleccionarlo.")

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
            
            # Paso A: Buscar casillas vacías y elegir la mejor
            intentos_scroll = 0
            while intentos_scroll < 3:
                try:
                    todas_vacias = list(gui.locateAllOnScreen(CHK_VACIO, region=sector_a, confidence=0.9, grayscale=True))
                    todas_vacias.sort(key=lambda loc: loc.top)
                except:
                    todas_vacias = []

                casilla_objetivo = None
                id_actual = "DESCONOCIDO"

                for i, loc in enumerate(todas_vacias):
                    centro = gui.center(loc)
                    coord = (int(centro.x), int(centro.y))
                    identificador = leer_id_diario(coord)
                    
                    if identificador in diarios_con_error:
                        if intentos_scroll == 0: # Solo imprimir en el primer escaneo
                            print(f"  -> Ignorando {identificador} (lista negra).")
                        continue
                    
                    casilla_objetivo = coord
                    id_actual = identificador
                    break

                if casilla_objetivo:
                    break # Encontramos una!
                
                # Si no hay casillas o todas están en lista negra, intentamos bajar
                intentos_scroll += 1
                if intentos_scroll < 3:
                    print(f"No hay casillas nuevas en vista. Buscando botón de scroll ({intentos_scroll}/3)...")
                    
                    # Buscar el botón de avanzar abajo dentro del SECTOR SCROLL
                    pos_flecha = gui.locateCenterOnScreen(BTN_ABAJO, region=sector_scroll, confidence=0.8, grayscale=True)
                    
                    if pos_flecha:
                        print(f"Botón de scroll encontrado en {pos_flecha}. Presionando 5 veces...")
                        gui.moveTo(pos_flecha.x, pos_flecha.y, duration=0.2)
                        for _ in range(5):
                            gui.click()
                            time.sleep(0.1)
                        time.sleep(1.5) # Esperar a que AX cargue la siguiente página
                    else:
                        print("No se encontró el botón 'Avanzar_Abajo.png'. Intentando con PgDn como respaldo...")
                        gui.click(sector_a[0] + sector_a[2]//2, sector_a[1] + 50)
                        time.sleep(0.3)
                        gui.press('pgdn')
                        time.sleep(2)
                else:
                    print("Se alcanzó el límite de intentos de scroll sin éxito.")

            if not casilla_objetivo:
                print("Definitivamente no hay más casillas para procesar. Fin del trabajo.")
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
            time.sleep(0.5) 
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
