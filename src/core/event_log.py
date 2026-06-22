"""Sistema de logging de eventos estructurado (JSONL) para Bot AX Contable.

Cada evento importante del bot se registra como una linea JSON en
``logs/events.jsonl``, permitiendo que un observador externo analice el
comportamiento del bot con precision.

El modulo es a prueba de fallos: si no puede escribir, el bot sigue
funcionando normalmente.  No introduce dependencias nuevas ni altera la
logica existente del bot.

Uso::

    from src.core.event_log import event_log

    event_log("checkbox_found", id_bruto="IS00330201", id_normalizado="00330201",
              coords=[1284, 104])

Produce una linea::

    {"ts": "2026-06-22T10:30:45.123456", "event": "checkbox_found",
     "id_bruto": "IS00330201", "id_normalizado": "00330201", "coords": [1284, 104]}
"""

import json
import os
from datetime import datetime
from typing import Any

# ──────────────────────────────────────────────────────────────
# Resolucion de rutas (identica a logger.py / config.py)
# ──────────────────────────────────────────────────────────────

# Directorio de este archivo: src/core/
_CORE_DIR: str = os.path.dirname(os.path.abspath(__file__))

# Directorio raiz del proyecto (dos niveles arriba: src/core/ -> src/ -> raiz)
_BASE_DIR: str = os.path.dirname(os.path.dirname(_CORE_DIR))

# Ruta del archivo de eventos JSONL junto a bot_ax.log
_EVENTS_FILE: str = os.path.join(_BASE_DIR, "logs", "events.jsonl")


def event_log(event_type: str, **fields: Any) -> None:
    """Registra un evento estructurado como una linea JSON en ``events.jsonl``.

    La funcion **nunca** lanza excepciones: si ocurre cualquier error de
    escritura (disco lleno, permisos, ruta invalida, etc.) se ignora
    silenciosamente para no afectar la ejecucion del bot.

    Args:
        event_type: Tipo de evento (ej: ``"bot_start"``,
            ``"checkbox_found"``, ``"result_exito"``).
        **fields: Campos adicionales del evento (cualquier tipo
            serializable por ``json.dumps``).
    """
    try:
        # Asegurar que el directorio de logs exista
        _log_dir: str = os.path.dirname(_EVENTS_FILE)
        os.makedirs(_log_dir, exist_ok=True)

        # Construir el registro con timestamp ISO-8601 y tipo de evento
        registro: dict = {
            "ts": datetime.now().isoformat(),
            "event": event_type,
        }
        registro.update(fields)

        # Escribir una linea JSON compacta con soporte UTF-8
        with open(_EVENTS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(registro, ensure_ascii=False) + "\n")
    except Exception:
        # Silencioso: nunca romper el bot
        pass
