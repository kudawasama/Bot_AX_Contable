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
        # La GUI aún está en app_gui.py en la raíz del proyecto
        import importlib.util
        gui_path = os.path.join(_project_root, "app_gui.py")
        if os.path.exists(gui_path):
            import app_gui
            root = app_gui.tk.Tk()
            app = app_gui.BotAXGui(root)
            root.mainloop()
        else:
            print("ERROR: app_gui.py no encontrado en la raíz del proyecto.")
            sys.exit(1)


if __name__ == "__main__":
    main()
