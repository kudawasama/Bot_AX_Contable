"""
bot_main.py — Wrapper de compatibilidad.

Re-exporta todo desde src/bot_ax/core/engine.py.
El import antiguo `from bot_main import run_bot` sigue funcionando.
"""

import os
import sys

_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if _src not in sys.path:
    sys.path.insert(0, _src)

from bot_ax.core.engine import run_bot  # noqa: F401, E402
