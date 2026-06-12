"""
Reconocimiento óptico de caracteres (OCR) para leer IDs de diario.
"""

import pyautogui
import pytesseract
from bot_ax.config.settings import TESSERACT_CMD
from bot_ax.core.logger import get_logger
from bot_ax.config.sectores import obtener_offset_ocr

logger = get_logger()

pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD


def leer_id_diario(coord_checkbox):
    """
    Toma una captura pequeña a la derecha del checkbox para leer el número de diario.
    """
    cx, cy = coord_checkbox
    ox, oy, ow, oh = obtener_offset_ocr()
    region_texto = (int(cx) + ox, int(cy) + oy, ow, oh)

    try:
        # Captura la zona en escala de grises para mejor lectura
        screenshot = pyautogui.screenshot(region=region_texto)
        screenshot = screenshot.convert('L')  # Escala de grises

        # Procesar con OCR (modo 7: una sola línea de texto)
        texto = pytesseract.image_to_string(screenshot, config='--psm 7').strip()
        # Limpieza básica de caracteres no deseados
        texto = "".join(c for c in texto if c.isalnum() or c == '-')

        return texto if texto else "DESCONOCIDO"
    except Exception as e:
        logger.error(f"Error en OCR: {e}")
        return "ERROR_LECTURA"
