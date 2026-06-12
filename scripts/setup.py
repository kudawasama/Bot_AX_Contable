#!/usr/bin/env python
"""
setup.py — Configuración inicial del Bot AX Contable.

Verifica dependencias, crea directorios, guía al usuario
en la configuración de sectores y verifica patrones.

Uso:
    python scripts/setup.py
"""

import os
import sys
import shutil

_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_script_dir)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

OK = "  ✅"
WARN = "  ⚠️"
FAIL = "  ❌"


def heading(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")


def check_tesseract():
    """Verifica que Tesseract OCR esté instalado."""
    heading("Tesseract OCR")
    from config import TESSERACT_CMD, validar_tesseract
    try:
        validar_tesseract()
        print(f"{OK} Tesseract encontrado: {TESSERACT_CMD}")
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
        print(f"{OK} Versión: {pytesseract.get_tesseract_version()}")
        return True
    except FileNotFoundError as e:
        print(f"{FAIL} {e}")
        return False
    except Exception as e:
        print(f"{FAIL} Error: {e}")
        return False


def check_directories():
    """Crea los directorios necesarios si no existen."""
    heading("Directorios")
    dirs = [
        os.path.join(_project_root, "logs"),
        os.path.join(_project_root, "logs", "capturas"),
        os.path.join(_project_root, "patrones"),
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        print(f"{OK} {os.path.relpath(d, _project_root)}/")


def check_patterns():
    """Verifica que las imágenes patrón existan."""
    heading("Patrones de imagen")
    from config import (
        CHK_VACIO, BTN_MENU, BTN_CONFIRM, CHK_MARCADO,
        IMG_ERROR, BTN_ABAJO, IMG_FORMULARIOS, MSG_EXITO_ASIENTO,
    )
    patrones = [
        ("checkbox_vacio.png", CHK_VACIO),
        ("btn_registrar_menu.png", BTN_MENU),
        ("btn_registrar_confirm.png", BTN_CONFIRM),
        ("check_usuario_marcado.png", CHK_MARCADO),
        ("Error_Registro.png", IMG_ERROR),
        ("Avanzar_Abajo.png", BTN_ABAJO),
        ("Formularios_Abiertos.png", IMG_FORMULARIOS),
        ("msg_exito_asiento_1.png", MSG_EXITO_ASIENTO),
    ]
    todos_ok = True
    for name, path in patrones:
        if os.path.exists(path):
            size = os.path.getsize(path)
            print(f"{OK} {name} ({size} bytes)")
        else:
            print(f"{FAIL} {name} — NO ENCONTRADO")
            todos_ok = False
    return todos_ok


def check_config():
    """Verifica la configuración de sectores."""
    heading("Configuración de sectores")
    from config import CONFIG_FILE, cargar_configuracion

    if os.path.exists(CONFIG_FILE):
        config = cargar_configuracion()
        if config:
            for key in ["sector_a", "sector_b", "sector_scroll"]:
                val = config.get(key)
                if val:
                    print(f"{OK} {key}: {val}")
                else:
                    print(f"{WARN} {key}: no definido")
            offset = config.get("ocr_region_offset")
            if offset:
                print(f"{OK} ocr_region_offset: {offset}")
            print(f"\n{OK} Configuración cargada correctamente.")
        else:
            print(f"{FAIL} Archivo {CONFIG_FILE} tiene formato inválido.")
    else:
        print(f"{WARN} No hay configuración de sectores.")
        print(f"  Ejecuta: python setup_areas.py")


def check_dependencies():
    """Verifica dependencias Python."""
    heading("Dependencias Python")
    deps = [
        ("pyautogui", "pyautogui"),
        ("pytesseract", "pytesseract"),
        ("PIL", "pillow"),
        ("keyboard", "keyboard"),
    ]
    for name, pkg in deps:
        try:
            mod = __import__(name)
            ver = getattr(mod, "__version__", "ok")
            print(f"{OK} {pkg} ({ver})")
        except ImportError:
            print(f"{FAIL} {pkg} — No instalado. pip install {pkg}")


def check_git_hooks():
    """Verifica que los hooks de git estén configurados."""
    heading("Git Hooks")
    hooks_dir = os.path.join(_project_root, ".githooks")
    if os.path.exists(hooks_dir):
        try:
            import subprocess
            result = subprocess.run(
                ["git", "config", "core.hooksPath"],
                capture_output=True, text=True, cwd=_project_root, timeout=5,
            )
            current = result.stdout.strip()
            expected = ".githooks"
            if current == expected:
                print(f"{OK} Hooks configurados: {current}")
            else:
                print(f"{WARN} Hooks apuntan a '{current}' (debería ser '{expected}')")
                print(f"  Ejecuta: git config core.hooksPath .githooks")
        except Exception:
            print(f"{WARN} No se pudo verificar hooks de git.")
    else:
        print(f"{WARN} No hay directorio .githooks/.")


def main():
    print(f"\n{'#'*60}")
    print(f"#  Bot AX Contable — Setup")
    print(f"#  Proyecto: {_project_root}")
    print(f"{'#'*60}\n")

    checks = [
        ("Tesseract OCR", check_tesseract),
        ("Directorios", lambda: check_directories() or True),
        ("Patrones", check_patterns),
        ("Config. sectores", lambda: check_config() or True),
        ("Dependencias Python", lambda: check_dependencies() or True),
        ("Git Hooks", lambda: check_git_hooks() or True),
    ]

    results = []
    for name, fn in checks:
        try:
            result = fn()
            results.append((name, result))
        except Exception as e:
            print(f"{FAIL} {name}: Error inesperado — {e}")
            results.append((name, False))

    # Resumen final
    heading("Resumen")
    exit_code = 0
    for name, ok in results:
        icon = OK if ok else FAIL
        print(f"{icon} {name}")
        if not ok:
            exit_code = 1

    print()
    if exit_code == 0:
        print(f"{OK} Todo listo. Ejecuta: python app_gui.py")
    else:
        print(f"{WARN} Hay problemas que resolver antes de ejecutar el bot.")
        print(f"  Revisa las secciones marcadas con {FAIL} arriba.")
        print(f"  Para configurar sectores: python setup_areas.py")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
