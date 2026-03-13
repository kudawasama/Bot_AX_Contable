import sys
import time
import pyautogui
from config import cargar_configuracion, CHK_VACIO, BTN_MENU, BTN_CONFIRM, CHK_MARCADO, IMG_ERROR, BTN_ABAJO, IMG_FORMULARIOS
from vision import buscar_y_clickear, buscar_estado_checkbox, esperar_resultado_registro, leer_id_diario, capturar_pantalla_error
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
def run_bot(log_callback=print, stop_event=None):
    """
    Ejecuta el bot. 
    log_callback: Función para enviar mensajes (por defecto print).
    stop_event: threading.Event para detener el bot desde la UI.
    """
    def log(msg):
        log_callback(msg)
        
    log("Iniciando Bot AX Contable...")
    
    # 1. Cargar la configuración de los sectores
    sectores = cargar_configuracion()
    if not sectores:
        log("ERROR: Sectores no definidos. Ejecuta setup_areas.py")
        return False
        
    sector_a = sectores.get("sector_a")
    sector_b = sectores.get("sector_b")
    sector_scroll = sectores.get("sector_scroll")

    if not sector_scroll:
        log("ADVERTENCIA: Sector Scroll (Sector C) no definido.")

    log("\n[Instrucción] El bot se está ejecutando.")
    if stop_event is None:
        log("[Instrucción] MANTÉN PRESIONADA LA TECLA 'ESC' PARA DETENER.\n")
    
    time.sleep(1) 

    ciclo = 1
    diarios_con_error = [] # Lista negra de IDs que fallaron
    
    log("\n--- CONFIGURACIÓN OCR ACTIVA ---")
    
    try:
        while True:
            # Requisito de seguridad: Cancelar si hay formularios abiertos en medio
            try:
                if gui.locateOnScreen(IMG_FORMULARIOS, confidence=0.8, grayscale=True):
                    log("!!! SEGURIDAD: Se detectó 'Formularios Abiertos'. Deteniendo bot.")
                    capturar_pantalla_error("formularios_abiertos_stop")
                    break
            except:
                pass

            # Verificación de parada
            if stop_event and stop_event.is_set():
                log("Bot detenido por la interfaz.")
                break
            if not stop_event and keyboard.is_pressed('esc'):
                log("Bot detenido por el usuario (ESC).")
                break
                
            log(f"\n--- Iniciando Ciclo {ciclo} ---")
            
            # Paso A: Buscar casillas vacías y elegir la mejor
            intentos_scroll = 0
            while intentos_scroll < 10:
                # Verificar parada dentro de bucles internos
                if (stop_event and stop_event.is_set()) or (not stop_event and keyboard.is_pressed('esc')):
                    break

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
                        if intentos_scroll == 0:
                            log(f"  -> Ignorando {identificador} (lista negra).")
                        continue
                    
                    casilla_objetivo = coord
                    id_actual = identificador
                    break

                if casilla_objetivo:
                    break
                
                # Scroll si no hay casillas
                intentos_scroll += 1
                if intentos_scroll < 10:
                    log(f"No hay casillas nuevas. Buscando botón de scroll ({intentos_scroll}/10)...")
                    pos_flecha = gui.locateCenterOnScreen(BTN_ABAJO, region=sector_scroll, confidence=0.8, grayscale=True)
                    
                    if pos_flecha:
                        log(f"Botón de scroll encontrado. Presionando 5 veces...")
                        gui.moveTo(pos_flecha.x, pos_flecha.y, duration=0.2)
                        for _ in range(5):
                            gui.click()
                            time.sleep(0.1)
                        time.sleep(1.5)
                    else:
                        log("Botón no encontrado. Intentando con PgDn...")
                        capturar_pantalla_error("scroll_button_not_found")
                        gui.click(sector_a[0] + sector_a[2]//2, sector_a[1] + 50)
                        time.sleep(0.3)
                        gui.press('pgdn')
                        time.sleep(2)
                else:
                    log("Límite de intentos de scroll (10) alcanzado.")

            if not casilla_objetivo:
                log("No se encontraron más diarios tras 10 intentos de scroll. Fin.")
                break

            log(f"==> PROCESANDO DIARIO: {id_actual}")
            gui.moveTo(casilla_objetivo[0], casilla_objetivo[1], duration=0.5)
            gui.click()
            punto_click_a = casilla_objetivo
            time.sleep(1)

             # Paso B: Menú Registrar
            encontrado_menu = buscar_y_clickear(
                ruta_imagen=BTN_MENU, 
                sector_region=sector_b,
                timeout=30,
                stop_event=stop_event
            )

            if not encontrado_menu:
                if stop_event and stop_event.is_set(): break
                log(f"Error: No se encontró el botón de registrar para {id_actual}.")
                capturar_pantalla_error(id_actual)
                break
            
            # Paso C: Confirmación
            time.sleep(0.5) 
            encontrado_confirm = buscar_y_clickear(
                ruta_imagen=BTN_CONFIRM, 
                timeout=20,
                confidencialidad=0.8,
                stop_event=stop_event
            )
            
            if not encontrado_confirm:
                 if stop_event and stop_event.is_set(): break
                 log(f"Error: No se encontró la confirmación para {id_actual}.")
                 capturar_pantalla_error(id_actual)
                 break
            
            # Paso D: Esperar resultado
            px, py = punto_click_a
            region_especifica_checkbox = (int(px)-20, int(py)-20, 40, 40)
            time.sleep(2)
            
            resultado = esperar_resultado_registro(
                ruta_obj_exito=CHK_MARCADO,
                ruta_obj_error=IMG_ERROR,
                sector_region=region_especifica_checkbox,
                timeout=3600,
                stop_event=stop_event
            )
            
            if resultado == 'exito':
                log(f"-> Registro de {id_actual} completado.")
                registrar_log(id_actual, "EXITOSO")
                time.sleep(0.1)
            elif resultado == 'cancelado':
                log("Registro cancelado por el usuario.")
                break
            elif resultado == 'error':
                 log(f"Se detectó un Error en {id_actual}. A la lista negra.")
                 capturar_pantalla_error(id_actual)
                 registrar_log(id_actual, "ERROR")
                 diarios_con_error.append(id_actual)
                 gui.press('esc')
                 time.sleep(2) 
            else:
                 log(f"Timeout extremo para {id_actual}.")
                 capturar_pantalla_error(id_actual)
                 break
                 
            ciclo += 1
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        log("\nBot detenido manualmente.")
    except Exception as e:
        log(f"\nError inesperado: {e}")
        
    log("\nEjecución finalizada.")
    return True

if __name__ == "__main__":
    run_bot()
