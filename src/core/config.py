import os
import json
from typing import Optional, Dict, Any, List, Tuple

# Directorio de este archivo: src/core/
CORE_DIR: str = os.path.dirname(os.path.abspath(__file__))

# Directorio raíz del proyecto (dos niveles arriba: src/core/ -> src/ -> raíz)
BASE_DIR: str = os.path.dirname(os.path.dirname(CORE_DIR))

# Ruta del archivo de configuración de sectores en la raíz
CONFIG_FILE: str = os.path.join(BASE_DIR, "config_sectores.json")

# Ruta del directorio de patrones visuales en la raíz
PATRONES_DIR: str = os.path.join(BASE_DIR, "patrones")

# Ruta de Tesseract OCR con fallback por defecto en el sistema
TESSERACT_CMD: str = os.environ.get(
    "TESSERACT_CMD",
    r"C:\Users\jose.cespedes\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
)

# Nombres de archivos de patrones visuales
CHK_VACIO: str = os.path.join(PATRONES_DIR, "checkbox_vacio.png")
BTN_MENU: str = os.path.join(PATRONES_DIR, "btn_registrar_menu.png")
BTN_CONFIRM: str = os.path.join(PATRONES_DIR, "btn_registrar_confirm.png")
CHK_MARCADO: str = os.path.join(PATRONES_DIR, "check_usuario_marcado.png")
IMG_ERROR: str = os.path.join(PATRONES_DIR, "Error_Registro.png")
BTN_ABAJO: str = os.path.join(PATRONES_DIR, "Avanzar_Abajo.png")
IMG_FORMULARIOS: str = os.path.join(PATRONES_DIR, "Formularios_Abiertos.png")
MSG_EXITO_ASIENTO: str = os.path.join(PATRONES_DIR, "msg_exito_asiento_1.png")


def cargar_configuracion() -> Optional[Dict[str, Any]]:
    """Carga y valida la configuración de sectores desde el archivo JSON de la raíz.

    Returns:
        Optional[Dict[str, Any]]: Diccionario de configuración con los sectores si es válido,
                                  o None si ocurre algún error.
    """
    if not os.path.exists(CONFIG_FILE):
        return None
    
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config: Dict[str, Any] = json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: {CONFIG_FILE} no es un JSON válido: {e}")
        return None
    
    # Validar que existen los sectores requeridos
    for key in ["sector_a", "sector_b"]:
        if key not in config:
            print(f"ERROR: Falta '{key}' en {CONFIG_FILE}")
            return None
        val: Any = config[key]
        if not isinstance(val, (list, tuple)) or len(val) != 4:
            print(f"ERROR: '{key}' debe ser una lista de 4 números [x, y, w, h]")
            return None
        if not all(isinstance(n, (int, float)) for n in val):
            print(f"ERROR: '{key}' contiene valores no numéricos")
            return None
    
    return config


def guardar_configuracion(sector_a: List[int], sector_b: List[int], sector_scroll: List[int]) -> None:
    """Guarda la configuración de los sectores en el archivo JSON de la raíz.

    Args:
        sector_a (List[int]): Coordenadas y tamaño del Sector A [x, y, w, h].
        sector_b (List[int]): Coordenadas y tamaño del Sector B [x, y, w, h].
        sector_scroll (List[int]): Coordenadas y tamaño del Sector C [x, y, w, h].
    """
    # Preservar ocr_region_offset si ya existe
    config_actual: Optional[Dict[str, Any]] = cargar_configuracion()
    ocr_offset: Optional[List[int]] = None
    if config_actual and "ocr_region_offset" in config_actual:
        ocr_offset = config_actual["ocr_region_offset"]
    
    config: Dict[str, Any] = {
        "sector_a": sector_a,
        "sector_b": sector_b,
        "sector_scroll": sector_scroll
    }
    if ocr_offset:
        config["ocr_region_offset"] = ocr_offset
    
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
        print(f"Configuración guardada en {CONFIG_FILE}:")
        print(f"Sector A: {sector_a}")
        print(f"Sector B: {sector_b}")
        print(f"Sector Scroll: {sector_scroll}")
    except Exception as e:
        print(f"ERROR al guardar la configuración: {e}")


def validar_tesseract() -> bool:
    """Verifica que el ejecutable de Tesseract OCR esté instalado y accesible.

    Returns:
        bool: True si el ejecutable existe.

    Raises:
        FileNotFoundError: Si Tesseract no se localiza en la ruta especificada.
    """
    if not os.path.exists(TESSERACT_CMD):
        raise FileNotFoundError(
            f"Tesseract OCR no encontrado en: {TESSERACT_CMD}\n"
            f"Instálalo desde https://github.com/UB-Mannheim/tesseract/wiki "
            f"o configura la variable de entorno TESSERACT_CMD con la ruta correcta."
        )
    return True


def obtener_offset_ocr(config: Optional[Dict[str, Any]] = None) -> Tuple[int, int, int, int]:
    """Obtiene el offset de la región OCR desde la configuración con fallback por defecto.

    Args:
        config (Optional[Dict[str, Any]]): Configuración cargada previamente, o None para recargar.

    Returns:
        Tuple[int, int, int, int]: Offset de la región OCR (x, y, w, h).
    """
    if config is None:
        config = cargar_configuracion()
    if config and "ocr_region_offset" in config:
        offset: Any = config["ocr_region_offset"]
        if isinstance(offset, (list, tuple)) and len(offset) == 4:
            return tuple(offset)
    # Fallback a valores por defecto en el sistema
    return (-275, -13, 110, 28)
