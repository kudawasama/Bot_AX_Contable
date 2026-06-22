import sys
import time
import json
import os
from datetime import datetime
from typing import Callable, Optional, Set, List, Tuple
import threading
import pyautogui as gui

from src.core.config import (
    cargar_configuracion, CHK_VACIO, BTN_MENU, BTN_CONFIRM, CHK_MARCADO, 
    IMG_ERROR, BTN_ABAJO, IMG_FORMULARIOS, BASE_DIR
)
from src.services.vision import (
    buscar_y_clickear, buscar_estado_checkbox, esperar_resultado_registro,
    leer_id_diario, capturar_pantalla_error, normalizar_id_diario
)
from src.core.event_log import event_log

try:
    import keyboard
    HAS_KEYBOARD: bool = True
except ImportError:
    HAS_KEYBOARD = False


def registrar_log(id_diario: str, resultado: str) -> None:
    """Guarda el resultado del procesamiento diario en un archivo de texto en la raíz.

    Genera un archivo de log diario con el formato 'registro_YYYY-MM-DD.txt'.

    Args:
        id_diario (str): Identificador del diario procesado.
        resultado (str): Resultado final (EXITOSO / ERROR / etc.).
    """
    ahora: datetime = datetime.now()
    fecha_hoy: str = ahora.strftime("%Y-%m-%d")
    nombre_archivo: str = os.path.join(BASE_DIR, f"registro_{fecha_hoy}.txt")
    timestamp: str = ahora.strftime("%H:%M:%S")
    linea: str = f"[{timestamp}] Diario: {id_diario} - Resultado: {resultado}\n"
    try:
        with open(nombre_archivo, "a", encoding="utf-8") as f:
            f.write(linea)
    except Exception as e:
        print(f"Error escribiendo registro: {e}")


def run_bot(
    log_callback: Callable[[str], None] = print, 
    stop_event: Optional[threading.Event] = None, 
    pause_event: Optional[threading.Event] = None
) -> bool:
    """Ejecuta el ciclo principal del Bot AX Contable de manera síncrona.

    Busca checkboxes vacíos en el Sector A, gestiona la automatización del menú en
    el Sector B y la confirmación, espera el resultado del registro AX en pantalla
    completa y hace scroll en el Sector C si es necesario.

    Args:
        log_callback (Callable[[str], None]): Función receptora de mensajes en consola / interfaz.
        stop_event (Optional[threading.Event]): Evento para detener el bot.
        pause_event (Optional[threading.Event]): Evento para pausar la ejecución del bot.

    Returns:
        bool: True si el bot finalizó su flujo normalmente, False si ocurrió un error crítico de inicio.
    """
    def log(msg: str) -> None:
        log_callback(msg)
        
    log("Iniciando Bot AX Contable...")
    
    # 0. Validar disponibilidad de Tesseract OCR antes de proceder
    from src.core.config import validar_tesseract
    try:
        validar_tesseract()
        log("Tesseract OCR verificado.")
    except FileNotFoundError as e:
        log(f"ERROR CRÍTICO: {e}")
        return False
    
    # 0.5. Cargar lista negra persistente de diarios con error de la raíz
    blacklist_file: str = os.path.join(BASE_DIR, "blacklist.json")
    diarios_con_error: List[str] = []
    if os.path.exists(blacklist_file):
        try:
            with open(blacklist_file, "r", encoding="utf-8") as f:
                diarios_con_error = json.load(f)
                if not isinstance(diarios_con_error, list):
                    diarios_con_error = []
            if diarios_con_error:
                log(f"Lista negra cargada: {len(diarios_con_error)} diario(s) con error previo.")
        except Exception:
            diarios_con_error = []
    
    # 1. Cargar la configuración de los sectores
    sectores = cargar_configuracion()
    if not sectores:
        log("ERROR: Sectores no definidos. Ejecuta el calibrador de áreas.")
        return False
        
    sector_a_raw = sectores.get("sector_a")
    if sector_a_raw:
        # Aplicar margen de seguridad (padding) dinámico para evitar recortes de checkboxes en el borde
        x_a, y_a, w_a, h_a = sector_a_raw
        pad_x = 25
        pad_y = 15
        sector_a = [max(0, x_a - pad_x), max(0, y_a - pad_y), w_a + (pad_x * 2), h_a + (pad_y * 2)]
        log(f"Sector A original: {sector_a_raw} -> Ajustado con padding a: {sector_a}")
    else:
        log("ERROR: Sector A no definido en la configuración.")
        return False
        
    sector_b = sectores.get("sector_b")
    sector_scroll = sectores.get("sector_scroll")

    if not sector_scroll:
        log("ADVERTENCIA: Sector Scroll (Sector C) no definido.")
 
    # Evento estructurado: inicio del bot con parametros de configuracion
    event_log(
        "bot_start",
        sector_a=sector_a,
        sector_b=sector_b,
        blacklist_count=len(diarios_con_error),
    )

    log("\n[Instrucción] El bot se está ejecutando.")
    if stop_event is None:
        log("[Instrucción] MANTÉN PRESIONADA LA TECLA 'ESC' PARA DETENER.\n")
    
    time.sleep(1) 

    ciclo: int = 1
    log("\n--- CONFIGURACIÓN OCR ACTIVA ---")
    
    try:
        posiciones_procesadas: Set[Tuple[int, int]] = set()  # Cache de coordenadas ya procesadas
        while True:
            # Requisito de seguridad: Cancelar si hay formularios abiertos en medio
            try:
                if gui.locateOnScreen(IMG_FORMULARIOS, confidence=0.8, grayscale=True):
                    log("!!! SEGURIDAD: Se detectó 'Formularios Abiertos'. Deteniendo bot.")
                    _captura_form = capturar_pantalla_error("formularios_abiertos_stop")
                    event_log("formulario_abierto_detectado", captura_path=_captura_form)
                    event_log("bot_stop", reason="formularios_abiertos")
                    break
            except Exception:
                pass

            # Verificación de parada externa
            if stop_event and stop_event.is_set():
                log("Bot detenido por la interfaz.")
                event_log("bot_stop", reason="user_esc")
                break
            if not stop_event and HAS_KEYBOARD and keyboard.is_pressed('esc'):
                log("Bot detenido por el usuario (ESC).")
                event_log("bot_stop", reason="user_esc")
                break

            # Bucle de pausa
            while pause_event and pause_event.is_set():
                if stop_event and stop_event.is_set():
                    break
                time.sleep(0.3)

            if stop_event and stop_event.is_set():
                break

            log(f"\n--- Iniciando Ciclo {ciclo} ---")
            event_log("ciclo_start", ciclo_num=ciclo)
            
            # Paso A: Buscar casillas vacías y elegir la mejor
            intentos_scroll: int = 0
            casilla_objetivo: Optional[Tuple[int, int]] = None
            id_actual: str = "DESCONOCIDO"

            while intentos_scroll < 3:
                # Verificar parada intermedia
                if (stop_event and stop_event.is_set()) or (not stop_event and HAS_KEYBOARD and keyboard.is_pressed('esc')):
                    break
                # Verificar pausa
                while pause_event and pause_event.is_set():
                    if stop_event and stop_event.is_set():
                        break
                    time.sleep(0.3)
                if stop_event and stop_event.is_set():
                    break

                # El foco se asegura de forma natural al clickear la casilla vacía objetivo.
                # Se remueve el clic ciego en la primera fila para evitar alterar los checks ya procesados.
                time.sleep(0.3)

                try:
                    # Confianza en 0.85 para balance óptimo de detección
                    todas_vacias = list(gui.locateAllOnScreen(CHK_VACIO,
                        region=sector_a, confidence=0.85, grayscale=True))
                    todas_vacias.sort(key=lambda loc: loc.top)
                except Exception:
                    todas_vacias = []

                # Encontrar el checkbox marcado más abajo (último procesado)
                ultimo_marcado_y: int = 0
                try:
                    # Confianza en 0.85 para evitar marcas fantasmas que bloqueen el avance
                    marcados = list(gui.locateAllOnScreen(CHK_MARCADO, region=sector_a, confidence=0.85, grayscale=True))
                    if marcados:
                        ultimo_marcado_y = max(gui.center(m).y for m in marcados)
                except Exception:
                    pass

                for loc in todas_vacias:
                    centro = gui.center(loc)
                    coord = (int(centro.x), int(centro.y))
                    # Solo procesar checkboxes vacíos que estén debajo del último marcado
                    if coord[1] <= ultimo_marcado_y:
                        continue
                    # Redondear coordenadas para absorber pequeñas fluctuaciones
                    coord_redondeada = (coord[0] // 5 * 5, coord[1] // 5 * 5)
                    
                    # Saltar si ya procesamos esta posición
                    if coord_redondeada in posiciones_procesadas:
                        continue
                    
                    posiciones_procesadas.add(coord_redondeada)
                    
                    identificador = leer_id_diario(coord)
                    id_normalizado = normalizar_id_diario(identificador)
                    
                    if id_normalizado in diarios_con_error:
                        if intentos_scroll == 0:
                            log(f"  -> Ignorando {identificador} (lista negra, normalizado: {id_normalizado}).")
                        event_log("checkbox_skip_blacklist", id_normalizado=id_normalizado)
                        continue
                    
                    event_log(
                        "checkbox_found",
                        id_bruto=identificador,
                        id_normalizado=id_normalizado,
                        coords=[coord[0], coord[1]],
                    )
                    casilla_objetivo = coord
                    id_actual = identificador
                    break

                if casilla_objetivo:
                    break
                
                # Realizar scroll si no se encontraron casillas
                intentos_scroll += 1
                log(f"No hay casillas nuevas. Buscando botón de scroll ({intentos_scroll}/3)...")
                try:
                    pos_flecha = gui.locateCenterOnScreen(BTN_ABAJO, region=sector_scroll, confidence=0.7, grayscale=True)
                except Exception:
                    pos_flecha = None

                if pos_flecha:
                    log("Botón de scroll encontrado. Presionando 1 vez...")
                    event_log("scroll_performed", intento=intentos_scroll, metodo="boton")
                    gui.moveTo(pos_flecha.x, pos_flecha.y, duration=0.2)
                    for _ in range(1):
                        gui.click()
                        time.sleep(0.1)
                    time.sleep(1.5)
                else:
                    log("Botón no encontrado. Scroll por clic...")
                    if intentos_scroll == 2:
                        capturar_pantalla_error("scroll_button_not_found")
                    try:
                        gui.moveTo(sector_a[0] + sector_a[2]//2, sector_a[1] + sector_a[3] - 10)
                        gui.click()
                        time.sleep(0.2)
                        gui.scroll(-10)
                        event_log("scroll_performed", intento=intentos_scroll, metodo="click")
                    except Exception:
                        gui.press('pgdn')
                        event_log("scroll_performed", intento=intentos_scroll, metodo="pgdn")
                    time.sleep(1.5)

                # Limpiar la caché de posiciones procesadas tras desplazar la pantalla,
                # ya que las coordenadas físicas de las filas cambian.
                posiciones_procesadas.clear()
                log("Caché de posiciones del Sector A restablecida tras scroll.")

            if not casilla_objetivo:
                log("No se encontraron más diarios tras 3 intentos de scroll. Fin.")
                event_log("bot_stop", reason="no_more_diarios")
                break

            log(f"==> PROCESANDO DIARIO: {normalizar_id_diario(id_actual)}")
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
                if stop_event and stop_event.is_set(): 
                    break
                log(f"Error: No se encontró el botón de registrar para {id_actual}.")
                _captura_menu = capturar_pantalla_error(id_actual)
                event_log("timeout_menu", segundos=30, captura_path=_captura_menu)
                diarios_con_error.append(normalizar_id_diario(id_actual))
                ciclo += 1
                time.sleep(0.5)
                continue
            else:
                # encontrado_menu es (x, y) o True; registrar el clic del menú
                _menu_coords = encontrado_menu if isinstance(encontrado_menu, tuple) else None
                _in_sector_b = False
                if _menu_coords and sector_b:
                    _in_sector_b = (sector_b[0] <= _menu_coords[0] <= sector_b[0] + sector_b[2] and
                                    sector_b[1] <= _menu_coords[1] <= sector_b[1] + sector_b[3])
                event_log(
                    "menu_click",
                    coords=list(_menu_coords) if _menu_coords else [],
                    in_sector=_in_sector_b,
                )
            
            # Paso C: Confirmación
            time.sleep(0.5) 
            encontrado_confirm = buscar_y_clickear(
                ruta_imagen=BTN_CONFIRM, 
                timeout=20,
                confidencialidad=0.8,
                stop_event=stop_event
            )
            
            if not encontrado_confirm:
                 if stop_event and stop_event.is_set(): 
                     break
                 log(f"Error: No se encontró la confirmación para {id_actual}.")
                 _captura_confirm = capturar_pantalla_error(id_actual)
                 event_log("timeout_confirm", segundos=20)
                 diarios_con_error.append(normalizar_id_diario(id_actual))
                 ciclo += 1
                 time.sleep(0.5)
                 continue
            else:
                # encontrado_confirm es (x, y) o True; registrar el clic de confirmar
                _confirm_coords = encontrado_confirm if isinstance(encontrado_confirm, tuple) else None
                _in_sector_b = False
                if _confirm_coords and sector_b:
                    _in_sector_b = (sector_b[0] <= _confirm_coords[0] <= sector_b[0] + sector_b[2] and
                                    sector_b[1] <= _confirm_coords[1] <= sector_b[1] + sector_b[3])
                event_log(
                    "confirm_click",
                    coords=list(_confirm_coords) if _confirm_coords else [],
                    in_sector=_in_sector_b,
                )
            
            # Paso D: Esperar resultado
            px, py = punto_click_a
            time.sleep(2)
            
            _ts_inicio_resultado = time.time()
            resultado = esperar_resultado_registro(
                ruta_obj_exito=CHK_MARCADO,
                ruta_obj_error=IMG_ERROR,
                sector_region=sector_a,
                timeout=3600,
                stop_event=stop_event
            )
            _tiempo_total = round(time.time() - _ts_inicio_resultado, 2)
            
            if resultado == 'exito':
                log(f"[RESULT:OK] -> Registro de {normalizar_id_diario(id_actual)} completado.")
                event_log(
                    "result_exito",
                    id_normalizado=normalizar_id_diario(id_actual),
                    tiempo_total_segundos=_tiempo_total,
                )
                registrar_log(id_actual, "EXITOSO")
                time.sleep(2)
            elif resultado == 'cancelado':
                log("Registro cancelado por el usuario.")
                event_log("bot_stop", reason="user_esc")
                break
            elif resultado == 'error':
                 log(f"[RESULT:ERROR] Se detectó un Error en {id_actual}. A la lista negra.")
                 _captura_err = capturar_pantalla_error(id_actual)
                 event_log(
                     "result_error",
                     id_normalizado=normalizar_id_diario(id_actual),
                     captura_path=_captura_err,
                 )
                 registrar_log(id_actual, "ERROR")
                 diarios_con_error.append(normalizar_id_diario(id_actual))
                 event_log(
                     "blacklist_updated",
                     id_added=normalizar_id_diario(id_actual),
                     total=len(diarios_con_error),
                 )
                 # Guardar blacklist actualizada en la raíz
                 try:
                     with open(blacklist_file, "w", encoding="utf-8") as f:
                         json.dump(diarios_con_error, f)
                 except Exception:
                     pass
                 gui.press('esc')
                 time.sleep(1)
                 # Cerrar pop-up de error si sigue en pantalla
                 try:
                     ubi_err = gui.locateCenterOnScreen(IMG_ERROR, confidence=0.8, grayscale=True)
                     if ubi_err:
                         gui.moveTo(int(ubi_err[0]), int(ubi_err[1]))
                         gui.click()
                         time.sleep(0.5)
                         gui.press('esc')
                 except Exception:
                     pass
                 time.sleep(1)
            else:
                 log(f"[RESULT:ERROR] Timeout extremo para {id_actual}.")
                 _captura_to = capturar_pantalla_error(id_actual)
                 event_log(
                     "result_timeout",
                     id_normalizado=normalizar_id_diario(id_actual),
                     segundos_esperados=3600,
                 )
                 event_log("bot_stop", reason="timeout_extremo")
                 break
                 
            ciclo += 1
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        log("\nBot detenido manualmente.")
        event_log("bot_stop", reason="user_esc")
    except gui.FailSafeException as e:
        log(f"\nFAIL-SAFE de PyAutoGUI activado: {e}")
        event_log("failsafe_triggered", detalle_error=str(e))
        event_log("bot_stop", reason="error")
    except Exception as e:
        log(f"\nError inesperado: {e}")
        event_log("bot_stop", reason="error")
        
    log("\nEjecución finalizada.")
    return True


if __name__ == "__main__":
    run_bot()
