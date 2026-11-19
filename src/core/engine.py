import json
import os
import threading
import time
from datetime import datetime
from typing import Callable, List, Optional, Set, Tuple

import pyautogui as gui

from src.core.config import (
    BASE_DIR,
    BTN_ABAJO,
    BTN_CONFIRM,
    BTN_MENU,
    CHK_MARCADO,
    CHK_VACIO,
    IMG_ERROR,
    IMG_FORMULARIOS,
    cargar_configuracion,
)
from src.core.event_log import event_log
from src.services.vision import (
    buscar_y_clickear,
    capturar_pantalla_error,
    esperar_resultado_registro,
    leer_id_diario,
    normalizar_id_diario,
)

try:
    import keyboard
    HAS_KEYBOARD: bool = True
except ImportError:
    HAS_KEYBOARD = False

# --- Parámetros de control del ciclo (ajustados con datos de producción) ---
# Scrolls SEGUIDOS sin que la lista se mueva antes de dar por terminada la lista de diarios.
MAX_INTENTOS_SIN_MOVIMIENTO: int = 3
# Tope total de scrolls por ciclo: red de seguridad si el OCR del ancla falla una y otra vez
# (sin este tope, un ancla mal leída podría hacer scroll indefinidamente).
MAX_SCROLLS_POR_CICLO: int = 25
# Tiempo máximo de espera del resultado de un registro. Medido sobre 2.051 registros reales:
# mediana 32 s, p90 202 s, p99 451 s y máximo 824 s; 20 minutos dejan margen amplio sin
# condenar al bot a esperar una hora cuando el registro no se llegó a disparar.
TIMEOUT_RESULTADO_SEGUNDOS: int = 1200


def _actualizar_intentos_scroll(
    ancla: Optional[str],
    ancla_anterior: Optional[str],
    intentos_actuales: int,
) -> int:
    """Cuenta scrolls seguidos SIN movimiento de la lista de diarios.

    Un scroll sólo debe contar como fallido si la pantalla no cambió. Si el ancla (ID del
    diario visible más arriba) es distinta, la lista se movió y hay más filas: se vuelve a
    cero. Una lectura dudosa (``None``) tampoco cuenta, para no terminar la ejecución por un
    OCR malo.

    Args:
        ancla (Optional[str]): Ancla de la pantalla actual; ``None`` si no es legible.
        ancla_anterior (Optional[str]): Ancla de la vuelta anterior de este ciclo.
        intentos_actuales (int): Contador acumulado antes de este scroll.

    Returns:
        int: Contador actualizado (0 si la lista se movió o no hay ancla fiable).
    """
    if ancla is None or ancla != ancla_anterior:
        return 0
    return intentos_actuales + 1


def _id_primera_casilla(casillas: List[object]) -> Optional[str]:
    """Devuelve el ID del diario visible más arriba (ancla de la pantalla).

    Se usa para saber si la lista se movió tras un scroll: si el ancla cambia, hay más
    filas abajo y el intento no debe contar como fallido. Devuelve ``None`` cuando no se
    puede leer con seguridad (lista vacía o lectura dudosa).

    Args:
        casillas (List[object]): Resultado de ``locateAllOnScreen`` ordenado por ``top``.

    Returns:
        Optional[str]: ID normalizado del primer diario, o ``None`` si no es legible.
    """
    if not casillas:
        return None
    try:
        centro = gui.center(casillas[0])
        identificador = leer_id_diario((int(centro.x), int(centro.y)))
    except Exception:
        return None
    if identificador == "ERROR_LECTURA":
        return None
    return normalizar_id_diario(identificador)


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


INTERVALO_HEARTBEAT_S: float = 60.0


def iniciar_heartbeat(
    stop_event: Optional[threading.Event],
    intervalo: float = INTERVALO_HEARTBEAT_S,
) -> threading.Thread:
    """Lanza un hilo daemon que emite un latido en la telemetría cada ``intervalo`` segundos.

    POR QUÉ (tarea B2 del plan): sin latido no hay forma de distinguir «el bot está
    esperando el resultado de AX» de «el bot se colgó» sin mirar la pantalla. El chequeo de
    salud (A3) puede apoyarse en estos eventos con un umbral corto y confiable. El latido
    cuesta una línea por minuto como máximo, así que no engorda ``logs/events.jsonl``.

    Args:
        stop_event (Optional[threading.Event]): Se activa al terminar la sesión (``bot_stop``).
        intervalo (float): Segundos entre latidos (60 por defecto).

    Returns:
        threading.Thread: Hilo daemon ya iniciado. El llamador debe activar ``stop_event``
        al terminar la sesión para que el latido no quede huérfano.
    """
    def _latir() -> None:
        while True:
            if stop_event is not None:
                if stop_event.wait(intervalo):
                    return  # la sesión terminó: el latido se corta sin dejar rastro
            else:
                time.sleep(intervalo)
            event_log("bot_heartbeat", intervalo_segundos=intervalo)

    hilo: threading.Thread = threading.Thread(target=_latir, name="bot-heartbeat", daemon=True)
    hilo.start()
    return hilo


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

    # B2: latido de la sesión en la telemetría estructurada (una línea por minuto).
    _heartbeat_stop: threading.Event = threading.Event()
    iniciar_heartbeat(_heartbeat_stop)

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
            # `intentos_scroll` cuenta sólo las vueltas en las que la lista NO se movió.
            # Antes contaba cualquier vuelta sin candidato, así que 3 pantallas seguidas de
            # diarios ya listados (lista negra) terminaban la ejecución aunque quedaran
            # diarios pendientes más abajo (incidente 2026-11-18 21:35: se cerró con
            # "No se encontraron más diarios" y a las 22:10 apareció 00342122).
            intentos_scroll: int = 0
            scrolls_ciclo: int = 0
            ancla_anterior: Optional[str] = None
            casilla_objetivo: Optional[Tuple[int, int]] = None
            id_actual: str = "DESCONOCIDO"

            while intentos_scroll < MAX_INTENTOS_SIN_MOVIMIENTO and scrolls_ciclo < MAX_SCROLLS_POR_CICLO:
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

                    # B1b: con una lectura dudosa NO se clickea la casilla. Procesar un
                    # identificador ilegible registraría —y listaría como error— un diario
                    # equivocado; se salta la casilla y queda constancia en la telemetría.
                    if identificador == "ERROR_LECTURA":
                        log(f"  -> ID ilegible en {coord}: se salta la casilla sin procesarla.")
                        _captura_id = capturar_pantalla_error("id_ilegible")
                        event_log(
                            "id_ilegible",
                            coords=[coord[0], coord[1]],
                            captura_path=_captura_id,
                        )
                        continue

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
                # El ancla es el ID del diario visible más arriba. Si cambia tras el scroll,
                # la lista se movió y hay más filas: el intento no cuenta como fallido.
                ancla = _id_primera_casilla(todas_vacias)
                intentos_scroll = _actualizar_intentos_scroll(ancla, ancla_anterior, intentos_scroll)
                ancla_anterior = ancla
                scrolls_ciclo += 1
                log(
                    f"No hay diarios nuevos en esta pantalla ({len(todas_vacias)} casillas, "
                    f"ancla={ancla or '?'}, sin movimiento {intentos_scroll}/{MAX_INTENTOS_SIN_MOVIMIENTO}, "
                    f"scrolls {scrolls_ciclo}/{MAX_SCROLLS_POR_CICLO}). Buscando botón de scroll..."
                )
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
                log(
                    f"No se encontraron más diarios: {MAX_INTENTOS_SIN_MOVIMIENTO} scrolls seguidos "
                    f"sin que la lista se moviese (scrolls totales: {scrolls_ciclo}). Fin."
                )
                event_log("bot_stop", reason="no_more_diarios", scrolls=scrolls_ciclo)
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
            # Pequeña espera activa: mueve el mouse 3px cada 1s para evitar suspensión
            for _ in range(2):
                try:
                    gui.moveRel(2, 0)
                    gui.moveRel(-2, 0)
                except Exception:
                    pass
                time.sleep(1)

            _ts_inicio_resultado = time.time()
            resultado = esperar_resultado_registro(
                ruta_obj_exito=CHK_MARCADO,
                ruta_obj_error=IMG_ERROR,
                sector_region=sector_a,
                timeout=TIMEOUT_RESULTADO_SEGUNDOS,
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
    finally:
        # B2: el latido nunca debe sobrevivir a la sesión (nada de hilos huérfanos).
        _heartbeat_stop.set()

    log("\nEjecución finalizada.")
    return True


if __name__ == "__main__":
    run_bot()
