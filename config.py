import os
import json

CONFIG_FILE = "config_sectores.json"

PATRONES_DIR = "patrones"

# Nombres de archivos de patrones según la documentación.
CHK_VACIO = os.path.join(PATRONES_DIR, "checkbox_vacio.png")
BTN_MENU = os.path.join(PATRONES_DIR, "btn_registrar_menu.png")
BTN_CONFIRM = os.path.join(PATRONES_DIR, "btn_registrar_confirm.png")
CHK_MARCADO = os.path.join(PATRONES_DIR, "check_usuario_marcado.png")
IMG_ERROR = os.path.join(PATRONES_DIR, "Error_Registro.png")
BTN_ABAJO = os.path.join(PATRONES_DIR, "Avanzar_Abajo.png")
IMG_FORMULARIOS = os.path.join(PATRONES_DIR, "Formularios_Abiertos.png")


def cargar_configuracion():
    """Carga la configuración de los sectores desde un archivo JSON."""
    if not os.path.exists(CONFIG_FILE):
        return None
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


def guardar_configuracion(sector_a, sector_b, sector_scroll):
    """Guarda la configuración de los sectores en un archivo JSON."""
    config = {
        "sector_a": sector_a,
        "sector_b": sector_b,
        "sector_scroll": sector_scroll
    }
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)
        
    print(f"Configuración guardada en {CONFIG_FILE}:")
    print(f"Sector A: {sector_a}")
    print(f"Sector B: {sector_b}")
    print(f"Sector Scroll: {sector_scroll}")
