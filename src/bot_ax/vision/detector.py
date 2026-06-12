"""
Detección de patrones visuales y automatización de clics.
"""

import os
import time
from PIL import Image
import pyautogui
from bot_ax.core.logger import get_logger
from bot_ax.vision.ids import nombre_corto
from bot_ax.config.defaults import VISION

logger = get_logger()

# PAUSE: Tiempo de espera mínimo después de comandos de pyautogui
pyautogui.PAUSE = 0.1


def buscar_y_clickear(ruta_imagen, sector_region=None, confidencialidad=0.8,
                       timeout=10, mover_hacia_abajo=False, wait_only=False,
                       stop_event=None):
    """
    Busca una imagen y clickea. Retorna True si la encontró.
    stop_event: Si se activa, termina la búsqueda inmediatamente.
    """
    if not os.path.exists(ruta_imagen):
        logger.error(f"No se encuentra la imagen: {ruta_imagen}")
        return False

    inicio = time.time()

    while time.time() - inicio < timeout:
        if stop_event and stop_event.is_set():
            return False

        try:
            ubicacion = None
            if sector_region:
                try:
                    img = Image.open(ruta_imagen)
                    iw, ih = img.size
                    if iw > sector_region[2] or ih > sector_region[3]:
                        logger.warning(
                            f"Region {sector_region} muy pequeña para "
                            f"{nombre_corto(ruta_imagen)} ({iw}x{ih}). "
                            "Buscando en pantalla completa."
                        )
                    else:
                        try:
                            ubicacion = pyautogui.locateCenterOnScreen(
                                ruta_imagen,
                                region=sector_region,
                                confidence=confidencialidad,
                                grayscale=True
                            )
                        except pyautogui.ImageNotFoundException:
                            pass
                except Exception:
                    try:
                        ubicacion = pyautogui.locateCenterOnScreen(
                            ruta_imagen,
                            region=sector_region,
                            confidence=confidencialidad,
                            grayscale=True
                        )
                    except pyautogui.ImageNotFoundException:
                        pass

            if not ubicacion:
                try:
                    ubicacion = pyautogui.locateCenterOnScreen(
                        ruta_imagen,
                        confidence=max(0.7, confidencialidad - 0.1),
                        grayscale=True
                    )
                    if ubicacion and sector_region:
                        logger.warning(f"{nombre_corto(ruta_imagen)} fuera de sector B")
                except pyautogui.ImageNotFoundException:
                    pass

            if ubicacion:
                ubicacion = (int(ubicacion[0]), int(ubicacion[1]))
                if wait_only:
                    logger.info(f"Detectado: {nombre_corto(ruta_imagen)}")
                    return ubicacion

                logger.info(f"Click: {nombre_corto(ruta_imagen)} @ ({ubicacion[0]},{ubicacion[1]})")
                pyautogui.moveTo(ubicacion[0], ubicacion[1])
                pyautogui.click()

                if mover_hacia_abajo:
                    logger.info("Presionando FLECHA ABAJO para pasar al siguiente registro.")
                    time.sleep(0.3)
                    pyautogui.press('down')

                return ubicacion

        except pyautogui.ImageNotFoundException:
            pass
        except Exception as e:
            logger.error(f"Error durante la búsqueda de imagen: {e}")

        time.sleep(0.5)

    logger.warning(f"Timeout: {nombre_corto(ruta_imagen)} no encontrado ({timeout}s).")
    return False


def buscar_estado_checkbox(ruta_obj_inicial, ruta_obj_final, sector_region,
                            timeout=30, stop_event=None):
    """
    Espera hasta que el objeto en el Sector A cambie al estado final.
    """
    inicio = time.time()
    logger.info(f"Esperando a que aparezca {ruta_obj_final}...")

    while time.time() - inicio < timeout:
        if stop_event and stop_event.is_set():
            return False

        try:
            ubicacion = pyautogui.locateCenterOnScreen(
                ruta_obj_final,
                region=sector_region,
                confidence=VISION.confianza_media,
                grayscale=True
            )
            if ubicacion:
                logger.info("Cambio de estado detectado correctamente.")
                return True
        except pyautogui.ImageNotFoundException:
            pass

        time.sleep(0.5)

    logger.warning("Timeout esperando cambio de estado en el checkbox.")
    return False


def esperar_resultado_registro(ruta_obj_exito, ruta_obj_error, sector_region,
                                timeout=300, stop_event=None):
    """
    Espera hasta que aparezca el check de éxito o el cartel de error.
    stop_event: Atiende la parada inmediata de la UI.
    """
    inicio = time.time()
    logger.info(f"Esperando resultado (timeout: {timeout/60:.0f}min)...")

    ultimo_mensaje = inicio
    while time.time() - inicio < timeout:
        if stop_event and stop_event.is_set():
            return 'cancelado'

        if time.time() - ultimo_mensaje > 30:
            logger.info(f"...esperando ({int(time.time() - inicio)}s)")
            ultimo_mensaje = time.time()
            try:
                pyautogui.moveRel(1, 0)
                pyautogui.moveRel(-1, 0)
            except Exception:
                pass

        # 1. Buscar pop-up de ÉXITO en pantalla completa
        try:
            from bot_ax.config.settings import MSG_EXITO_ASIENTO
            ubi_popup = pyautogui.locateCenterOnScreen(
                MSG_EXITO_ASIENTO,
                confidence=VISION.confianza_media,
                grayscale=True
            )
            if ubi_popup:
                logger.info("-> EXITO! (pop-up confirmado)")
                pyautogui.press('esc')
                time.sleep(0.5)
                return 'exito'
        except pyautogui.ImageNotFoundException:
            pass

        # 2. Buscar Error de registro en pantalla completa
        try:
            ubi_error = pyautogui.locateCenterOnScreen(
                ruta_obj_error,
                confidence=0.9,
                grayscale=True
            )
            if ubi_error:
                logger.warning("-> ERROR de Registro AX!")
                return 'error'
        except pyautogui.ImageNotFoundException:
            pass

        time.sleep(1)

    return None
