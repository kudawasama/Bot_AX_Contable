"""
logger.py — Wrapper de compatibilidad.
Re-exporta desde el nuevo paquete src/bot_ax/core/logger.py.
"""

import os
import sys

_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if _src not in sys.path:
    sys.path.insert(0, _src)

from bot_ax.core.logger import get_logger, QueueLogHandler, LOG_DIR, LOG_FILE  # noqa: F401, E402
