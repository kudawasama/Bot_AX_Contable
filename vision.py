"""
vision.py — Wrapper de compatibilidad.

Re-exporta todo desde el nuevo paquete src/bot_ax/vision/.
Los imports antiguos como:
    from vision import buscar_y_clickear, leer_id_diario, normalizar_id_diario
siguen funcionando sin cambios.
"""

import os
import sys

_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if _src not in sys.path:
    sys.path.insert(0, _src)

from bot_ax.vision.detector import (       # noqa: F401, E402
    buscar_y_clickear,
    buscar_estado_checkbox,
    esperar_resultado_registro,
)
from bot_ax.vision.ocr import leer_id_diario                      # noqa: F401, E402
from bot_ax.vision.captura import capturar_pantalla_error         # noqa: F401, E402
from bot_ax.vision.ids import (                                   # noqa: F401, E402
    normalizar_id_diario,
    nombre_corto,
    NOMBRES_IMAGENES,
)
