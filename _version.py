"""
_version.py — Wrapper de compatibilidad.
Re-exporta desde el nuevo paquete estructurado en src/bot_ax/_version.py.
"""

import os
import sys

_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if _src not in sys.path:
    sys.path.insert(0, _src)

# Import explícito (__version__ empieza con _, no lo trae import *)
from bot_ax._version import __version__, VERSION_TAG, get_git_short_sha  # noqa: F401, E402
