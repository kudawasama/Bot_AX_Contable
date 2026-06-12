"""
Carga y guardado de la configuración de sectores (config_sectores.json).
"""

import json
from bot_ax.config.settings import CONFIG_FILE, TESSERACT_CMD


def cargar_configuracion():
    """Carga y valida la configuración de sectores desde JSON."""
    import os
    if not os.path.exists(CONFIG_FILE):
        return None

    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: {CONFIG_FILE} no es un JSON válido: {e}")
        return None

    # Validar que existen los sectores requeridos
    for key in ["sector_a", "sector_b"]:
        if key not in config:
            print(f"ERROR: Falta '{key}' en {CONFIG_FILE}")
            return None
        val = config[key]
        if not isinstance(val, (list, tuple)) or len(val) != 4:
            print(f"ERROR: '{key}' debe ser una lista de 4 números [x, y, w, h]")
            return None
        if not all(isinstance(n, (int, float)) for n in val):
            print(f"ERROR: '{key}' contiene valores no numéricos")
            return None

    return config


def guardar_configuracion(sector_a, sector_b, sector_scroll):
    """Guarda la configuración de los sectores en un archivo JSON."""
    # Preservar ocr_region_offset si ya existe
    config_actual = cargar_configuracion()
    ocr_offset = None
    if config_actual and "ocr_region_offset" in config_actual:
        ocr_offset = config_actual["ocr_region_offset"]

    config = {
        "sector_a": sector_a,
        "sector_b": sector_b,
        "sector_scroll": sector_scroll
    }
    if ocr_offset:
        config["ocr_region_offset"] = ocr_offset

    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

    print(f"Configuración guardada en {CONFIG_FILE}:")
    print(f"Sector A: {sector_a}")
    print(f"Sector B: {sector_b}")
    print(f"Sector Scroll: {sector_scroll}")


def obtener_offset_ocr(config=None):
    """Obtiene el offset de la región OCR desde la configuración, con fallback a valores por defecto."""
    if config is None:
        config = cargar_configuracion()
    if config and "ocr_region_offset" in config:
        offset = config["ocr_region_offset"]
        if isinstance(offset, (list, tuple)) and len(offset) == 4:
            return tuple(offset)
    # Fallback a valores por defecto
    return (-275, -13, 110, 28)
