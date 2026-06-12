"""
Gestión de la lista negra de diarios con error.
Persiste en blacklist.json para que sobreviva a reinicios del bot.
"""

import json
import os
from bot_ax.config.settings import BASE_DIR

BLACKLIST_FILE = os.path.join(BASE_DIR, "blacklist.json")


def cargar_blacklist():
    """Carga la lista negra de diarios con error desde el archivo JSON."""
    if not os.path.exists(BLACKLIST_FILE):
        return []

    try:
        with open(BLACKLIST_FILE, "r") as f:
            diarios = json.load(f)
        if not isinstance(diarios, list):
            return []
        return diarios
    except Exception:
        return []


def guardar_blacklist(diarios_con_error):
    """Guarda la lista negra en el archivo JSON."""
    try:
        with open(BLACKLIST_FILE, "w") as f:
            json.dump(diarios_con_error, f)
        return True
    except Exception:
        return False
