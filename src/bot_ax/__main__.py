"""
Entry point principal del Bot AX Contable.

Uso:
    python -m bot_ax             # Abre la GUI
    python -m bot_ax --cli       # Ejecuta en terminal (sin GUI)
"""

import sys
import os

# Asegurar que el proyecto está en el path (compatible con desarrollo local)
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_src_root = os.path.dirname(_project_root)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)
if _src_root not in sys.path:
    sys.path.insert(0, _src_root)


def main():
    """Entry point: decide entre GUI o CLI según argumentos."""
    if "--cli" in sys.argv:
        from bot_ax.core.engine import run_bot
        run_bot()
    else:
        from bot_ax.ui.app_gui import main as gui_main
        gui_main()


if __name__ == "__main__":
    main()
