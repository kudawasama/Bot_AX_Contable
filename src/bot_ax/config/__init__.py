"""
Config — re-exporta todo para importación conveniente.

Uso:
    from bot_ax.config import settings, sectores, defaults
    # o directamente:
    from bot_ax.config.settings import TESSERACT_CMD, validar_tesseract
    from bot_ax.config.sectores import cargar_configuracion
"""

from bot_ax.config.settings import (
    BASE_DIR, CONFIG_FILE, PATRONES_DIR, TESSERACT_CMD,
    CHK_VACIO, BTN_MENU, BTN_CONFIRM, CHK_MARCADO,
    IMG_ERROR, BTN_ABAJO, IMG_FORMULARIOS, MSG_EXITO_ASIENTO,
    validar_tesseract,
)
from bot_ax.config.sectores import (
    cargar_configuracion, guardar_configuracion, obtener_offset_ocr,
)
from bot_ax.config.defaults import (
    OCR, VISION, LOG,
    OCRDefaults, VisionDefaults, LogDefaults,
)

__all__ = [
    "BASE_DIR", "CONFIG_FILE", "PATRONES_DIR", "TESSERACT_CMD",
    "CHK_VACIO", "BTN_MENU", "BTN_CONFIRM", "CHK_MARCADO",
    "IMG_ERROR", "BTN_ABAJO", "IMG_FORMULARIOS", "MSG_EXITO_ASIENTO",
    "validar_tesseract",
    "cargar_configuracion", "guardar_configuracion", "obtener_offset_ocr",
    "OCR", "VISION", "LOG",
    "OCRDefaults", "VisionDefaults", "LogDefaults",
]
