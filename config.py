import os
import json
import sys

# Directorio base: donde está este archivo (config.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(BASE_DIR, "config_sectores.json")

PATRONES_DIR = os.path.join(BASE_DIR, "patrones")

# Ruta de Tesseract: personalizable por variable de entorno, con fallback
TESSERACT_CMD = os.environ.get(
    "TESSERACT_CMD",
    r"C:\Users\jose.cespedes\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
)

# Nombres de archivos de patrones según la documentación.
CHK_VACIO = os.path.join(PATRONES_DIR, "checkbox_vacio.png")
BTN_MENU = os.path.join(PATRONES_DIR, "btn_registrar_menu.png")
BTN_CONFIRM = os.path.join(PATRONES_DIR, "btn_registrar_confirm.png")
CHK_MARCADO = os.path.join(PATRONES_DIR, "check_usuario_marcado.png")
IMG_ERROR = os.path.join(PATRONES_DIR, "Error_Registro.png")
BTN_ABAJO = os.path.join(PATRONES_DIR, "Avanzar_Abajo.png")
IMG_FORMULARIOS = os.path.join(PATRONES_DIR, "Formularios_Abiertos.png")
MSG_EXITO_ASIENTO = os.path.join(PATRONES_DIR, "msg_exito_asiento_1.png")
BTN_CERRAR_INFO = os.path.join(PATRONES_DIR, "btn_cerrar_info.png")


def cargar_configuracion():
    """Carga y valida la configuración de sectores desde JSON."""
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


def validar_tesseract():
    """Verifica que Tesseract OCR esté instalado y accesible."""
    if not os.path.exists(TESSERACT_CMD):
        raise FileNotFoundError(
            f"Tesseract OCR no encontrado en: {TESSERACT_CMD}\n"
            f"Instálalo desde https://github.com/UB-Mannheim/tesseract/wiki "
            f"o configura la variable de entorno TESSERACT_CMD con la ruta correcta."
        )
    return True


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
