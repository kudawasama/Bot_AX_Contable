#!/usr/bin/env python3
"""
Script de diagnóstico para Bot AX Contable
Identifica qué módulos faltan o tienen problemas
"""

import sys
import subprocess

print("=" * 60)
print("  DIAGNÓSTICO BOT AX CONTABLE")
print("=" * 60)
print()

# Versión de Python
print(f"Python: {sys.version}")
print(f"Ejecutable: {sys.executable}")
print()

# Módulos requeridos
modulos = {
    "pyautogui": "Automatización de pantalla",
    "pyscreeze": "Búsqueda de imágenes",
    "PIL": "Procesamiento de imágenes (Pillow)",
    "pytesseract": "Reconocimiento OCR",
    "keyboard": "Input de teclado",
    "tkinter": "Interfaz gráfica",
}

print("-" * 60)
print("VERIFICANDO MÓDULOS")
print("-" * 60)
print()

errores = []

for modulo, descripcion in modulos.items():
    try:
        __import__(modulo)
        print(f"✅ {modulo:15} - {descripcion}")
    except ImportError as e:
        print(f"❌ {modulo:15} - {descripcion}")
        print(f"   Error: {e}")
        errores.append(modulo)
    except Exception as e:
        print(f"⚠️  {modulo:15} - {descripcion}")
        print(f"   Advertencia: {e}")

print()

if errores:
    print("-" * 60)
    print("MÓDULOS FALTANTES")
    print("-" * 60)
    print()
    print(f"Falta instalar: {', '.join(errores)}")
    print()
    print("Ejecuta esto para instalar:")
    print("  python -m pip install --upgrade pip")
    print("  python -m pip install -r requirements.txt")
    print()
else:
    print("-" * 60)
    print("✅ TODOS LOS MÓDULOS ESTÁN INSTALADOS")
    print("-" * 60)
    print()
    print("Puedes ejecutar el bot:")
    print("  python app_gui.py")
    print()

# Intento final de importar app_gui
print("-" * 60)
print("PRUEBA DE IMPORTACIÓN")
print("-" * 60)
print()

try:
    import app_gui
    print("✅ app_gui.py se puede importar correctamente")
except Exception as e:
    print(f"❌ Error al importar app_gui.py:")
    print(f"   {type(e).__name__}: {e}")

print()
print("=" * 60)
