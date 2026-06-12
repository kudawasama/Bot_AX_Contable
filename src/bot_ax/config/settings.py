"""
Configuración del Bot AX Contable — constantes, rutas y validación.
"""

import os


def _find_project_root(marker: str = "pyproject.toml") -> str:
    """
    Busca la raíz del proyecto subiendo desde este archivo.
    Usa pyproject.toml como marcador de raíz.
    """
    current = os.path.dirname(os.path.abspath(__file__))
    for _ in range(10):  # límite de seguridad
        if os.path.isfile(os.path.join(current, marker)):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    # Fallback: subir 4 niveles (src/bot_ax/config/settings.py → raíz)
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)
    ))))


# Directorio base del proyecto (raíz, donde está pyproject.toml)
BASE_DIR = _find_project_root()

# Archivo de configuración de sectores
CONFIG_FILE = os.path.join(BASE_DIR, "config_sectores.json")

# Directorio de imágenes patrón
PATRONES_DIR = os.path.join(BASE_DIR, "patrones")

# Ruta de Tesseract: personalizable por variable de entorno, con fallback
TESSERACT_CMD = os.environ.get(
    "TESSERACT_CMD",
    r"C:\Users\jose.cespedes\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
)

# ── Nombres de archivos de patrones ──────────────────────────────
CHK_VACIO         = os.path.join(PATRONES_DIR, "checkbox_vacio.png")
BTN_MENU          = os.path.join(PATRONES_DIR, "btn_registrar_menu.png")
BTN_CONFIRM       = os.path.join(PATRONES_DIR, "btn_registrar_confirm.png")
CHK_MARCADO       = os.path.join(PATRONES_DIR, "check_usuario_marcado.png")
IMG_ERROR         = os.path.join(PATRONES_DIR, "Error_Registro.png")
BTN_ABAJO         = os.path.join(PATRONES_DIR, "Avanzar_Abajo.png")
IMG_FORMULARIOS   = os.path.join(PATRONES_DIR, "Formularios_Abiertos.png")
MSG_EXITO_ASIENTO = os.path.join(PATRONES_DIR, "msg_exito_asiento_1.png")


def validar_tesseract():
    """Verifica que Tesseract OCR esté instalado y accesible."""
    if not os.path.exists(TESSERACT_CMD):
        raise FileNotFoundError(
            f"Tesseract OCR no encontrado en: {TESSERACT_CMD}\n"
            f"Instálalo desde https://github.com/UB-Mannheim/tesseract/wiki "
            f"o configura la variable de entorno TESSERACT_CMD con la ruta correcta."
        )
    return True
