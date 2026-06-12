"""
Motor principal del Bot AX Contable.

Contiene el ciclo principal run_bot() que automatiza
el registro de diarios contables en Microsoft Dynamics AX.
"""

import sys
import time
import os
import pyautogui as gui
from datetime import datetime
from bot_ax.config.settings import (
    CHK_VACIO, BTN_MENU, BTN_CONFIRM, CHK_MARCADO,
    IMG_ERROR, BTN_ABAJO, IMG_FORMULARIOS,
)
from bot_ax.config.sectores import cargar_configuracion
from bot_ax.config.defaults import VISION
from bot_ax.vision.detector import buscar_y_clickear, esperar_resultado_registro
from bot_ax.vision.ids import normalizar_id_diario
from bot_ax.vision.captura import capturar_pantalla_error
from bot_ax.core.registrador import registrar_log
from bot_ax.core.blacklist import cargar_blacklist, guardar_blacklist, BLACKLIST_FILE

try:
    import keyboard
    HAS_KEYBOARD = True
except ImportError:
    HAS_KEYBOARD = False


def run_bot(log_callback=print, stop_event=None, pause_event=None):
    """
    Ejecuta el bot.

    log_callback: Función para enviar mensajes (por defecto print).
    stop_event: threading.Event para detener el bot desde la UI.
    pause_event: threading.Event — cuando está set, el bot espera.
    """
    def log(msg):
        log_callback(msg)

    log("Iniciando Bot AX Contable...")

    # 0. Validar que Tesseract esté disponible antes de empezar
    from bot_ax.config.settings import validar_tesseract
    try:
        validar_tesseract()
        log("Tesseract OCR verificado.")
    except FileNotFoundError as e:
        log(f"ERROR CRÍTICO: {e}")
        return False

    # 0.5. Cargar lista negra persistente de diarios con error
    diarios_con_error = cargar_blacklist()
    if diarios_con_error:
        log(f"Lista negra cargada: {len(diarios_con_error)} diario(s) con error previo.")

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

    log("\n--- CONFIGURACIÓN OCR ACTIVA ---")

    try:
        posiciones_procesadas = set()
        while True:
            # Requisito de seguridad: Cancelar si hay formularios abiertos en medio
            try:
                if gui.locateOnScreen(IMG_FORMULARIOS, confidence=0.8, grayscale=True):
                    log("!!! SEGURIDAD: Se detectó 'Formularios Abiertos'. Deteniendo bot.")
                    capturar_pantalla_error("formularios_abiertos_stop")
                    break
            except Exception:
                pass

            # Verificación de parada
            if stop_event and stop_event.is_set():
                log("Bot detenido por la interfaz.")
                break
            if not stop_event and HAS_KEYBOARD and keyboard.is_pressed('esc'):
                log("Bot detenido por el usuario (ESC).")
                break

            # Pausa: esperar hasta que se reanude
            while pause_event and pause_event.is_set():
                if stop_event and stop_event.is_set():
                    break
                time.sleep(0.3)

            if stop_event and stop_event.is_set():
                break

            log(f"\n--- Iniciando Ciclo {ciclo} ---")

            # Paso A: Buscar casillas vacías y elegir la mejor
            intentos_scroll = 0
            while intentos_scroll < VISION.scroll_intentos:
                if (stop_event and stop_event.is_set()) or \
                   (not stop_event and HAS_KEYBOARD and keyboard.is_pressed('esc')):
                    break
                while pause_event and pause_event.is_set():
                    if stop_event and stop_event.is_set():
                        break
                    time.sleep(0.3)
                if stop_event and stop_event.is_set():
                    break

                # Asegurar foco en la ventana de AX antes de buscar
                try:
                    gui.moveTo(sector_a[0] + sector_a[2]//2, sector_a[1] + 10)
                    gui.click()
                    time.sleep(0.3)
                except Exception:
                    pass

                try:
                    todas_vacias = list(gui.locateAllOnScreen(
                        CHK_VACIO, region=sector_a,
                        confidence=VISION.confianza_alta, grayscale=True
                    ))
                    todas_vacias.sort(key=lambda loc: loc.top)
                except Exception:
                    todas_vacias = []

                casilla_objetivo = None
                id_actual = "DESCONOCIDO"

                for loc in todas_vacias:
                    centro = gui.center(loc)
                    coord = (int(centro.x), int(centro.y))
                    coord_redondeada = (coord[0] // 5 * 5, coord[1] // 5 * 5)

                    if coord_redondeada in posiciones_procesadas:
                        continue

                    posiciones_procesadas.add(coord_redondeada)

                    from bot_ax.vision.ocr import leer_id_diario
                    identificador = leer_id_diario(coord)
                    id_normalizado = normalizar_id_diario(identificador)

                    if id_normalizado in diarios_con_error:
                        if intentos_scroll == 0:
                            log(f"  -> Ignorando {identificador} (lista negra, normalizado: {id_normalizado}).")
                        continue

                    casilla_objetivo = coord
                    id_actual = identificador
                    break

                if casilla_objetivo:
                    break

                # Scroll si no hay casillas
                intentos_scroll += 1
                log(f"No hay casillas nuevas. Buscando botón de scroll ({intentos_scroll}/{VISION.scroll_intentos})...")
                try:
                    pos_flecha = gui.locateCenterOnScreen(
                        BTN_ABAJO, region=sector_scroll,
                        confidence=VISION.confianza_scroll_sector, grayscale=True
                    )
                except Exception:
                    pos_flecha = None

                if pos_flecha:
                    log("Botón de scroll encontrado. Presionando 1 vez...")
                    gui.moveTo(pos_flecha.x, pos_flecha.y, duration=0.2)
                    for _ in range(VISION.scroll_clicks):
                        gui.click()
                        time.sleep(0.1)
                    time.sleep(1.5)
                else:
                    log("Botón no encontrado. Scroll por clic...")
                    if intentos_scroll == VISION.scroll_intentos:
                        capturar_pantalla_error("scroll_button_not_found")
                    try:
                        gui.moveTo(sector_a[0] + sector_a[2]//2, sector_a[1] + sector_a[3] - 10)
                        gui.click()
                        time.sleep(0.2)
                        gui.scroll(-10)
                    except Exception:
                        gui.press('pgdn')
                    time.sleep(1.5)

            if not casilla_objetivo:
                log(f"No se encontraron más diarios tras {VISION.scroll_intentos} intentos de scroll. Fin.")
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
                timeout=VISION.timeout_normal,
                stop_event=stop_event
            )

            if not encontrado_menu:
                if stop_event and stop_event.is_set():
                    break
                log(f"Error: No se encontró el botón de registrar para {id_actual}.")
                capturar_pantalla_error(id_actual)
                diarios_con_error.append(normalizar_id_diario(id_actual))
                ciclo += 1
                time.sleep(0.5)
                continue

            # Paso C: Confirmación
            time.sleep(0.5)
            encontrado_confirm = buscar_y_clickear(
                ruta_imagen=BTN_CONFIRM,
                timeout=VISION.timeout_normal,
                confidencialidad=VISION.confianza_media,
                stop_event=stop_event
            )

            if not encontrado_confirm:
                if stop_event and stop_event.is_set():
                    break
                log(f"Error: No se encontró la confirmación para {id_actual}.")
                capturar_pantalla_error(id_actual)
                diarios_con_error.append(normalizar_id_diario(id_actual))
                ciclo += 1
                time.sleep(0.5)
                continue

            # Paso D: Esperar resultado
            time.sleep(2)

            resultado = esperar_resultado_registro(
                ruta_obj_exito=CHK_MARCADO,
                ruta_obj_error=IMG_ERROR,
                sector_region=sector_a,
                timeout=VISION.timeout_resultado,
                stop_event=stop_event
            )

            if resultado == 'exito':
                log(f"[RESULT:OK] -> Registro de {normalizar_id_diario(id_actual)} completado.")
                registrar_log(id_actual, "EXITOSO")
                time.sleep(2)
            elif resultado == 'cancelado':
                log("Registro cancelado por el usuario.")
                break
            elif resultado == 'error':
                log(f"[RESULT:ERROR] Se detectó un Error en {id_actual}. A la lista negra.")
                capturar_pantalla_error(id_actual)
                registrar_log(id_actual, "ERROR")
                diarios_con_error.append(normalizar_id_diario(id_actual))
                guardar_blacklist(diarios_con_error)
                gui.press('esc')
                time.sleep(1)
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
