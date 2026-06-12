"""
Registro de resultados de procesamiento en archivo TXT por día.
"""

import os
from datetime import datetime
from bot_ax.config.settings import BASE_DIR


def registrar_log(id_diario, resultado):
    """Guarda el resultado del procesamiento en un archivo TXT por día."""
    ahora = datetime.now()
    fecha_hoy = ahora.strftime("%Y-%m-%d")
    nombre_archivo = os.path.join(BASE_DIR, f"registro_{fecha_hoy}.txt")
    timestamp = ahora.strftime("%H:%M:%S")
    linea = f"[{timestamp}] Diario: {id_diario} - Resultado: {resultado}\n"
    try:
        with open(nombre_archivo, "a", encoding="utf-8") as f:
            f.write(linea)
    except Exception as e:
        print(f"Error escribiendo registro: {e}")
