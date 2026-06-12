"""
Captura de pantalla para diagnóstico de errores.
"""

import os
import pyautogui
from datetime import datetime
from bot_ax.core.logger import get_logger

logger = get_logger()

# Directorio de capturas (relativo al proyecto)
CAPTURAS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "logs", "capturas"
)


def capturar_pantalla_error(id_diario="global"):
    """
    Captura una imagen de la pantalla completa y la guarda en la carpeta de capturas.
    """
    try:
        if not os.path.exists(CAPTURAS_DIR):
            os.makedirs(CAPTURAS_DIR)

        ahora = datetime.now()
        timestamp = ahora.strftime("%Y-%m-%d_%H%M%S")
        nombre_archivo = f"error_{id_diario}_{timestamp}.png"
        ruta_completa = os.path.join(CAPTURAS_DIR, nombre_archivo)

        screenshot = pyautogui.screenshot()
        screenshot.save(ruta_completa)
        logger.info(f"Captura de pantalla guardada en: {ruta_completa}")
        return ruta_completa
    except Exception as e:
        logger.error(f"No se pudo realizar la captura de pantalla: {e}")
        return None
