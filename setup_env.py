#!/usr/bin/env python3
"""
Script de configuración del entorno para Bot AX Contable
Verifica e instala todas las dependencias necesarias
"""

import sys
import os
import subprocess
from pathlib import Path

from tesseract_util import find_tesseract_executable

def print_header(text):
    """Imprime un encabezado formateado"""
    print("\n" + "="*50)
    print(f"  {text}")
    print("="*50 + "\n")

def check_python_version():
    """Verifica la versión de Python (recomendado 3.10–3.12 en Windows)."""
    print_header("Verificando Python")
    version = sys.version_info
    print(f"Versión Python: {version.major}.{version.minor}.{version.micro}")
    print(f"Ejecutable: {sys.executable}")

    if version.major < 3 or version.minor < 10:
        print("❌ ERROR: Se requiere Python 3.10 o superior")
        print("   Descarga 3.11 o 3.12 x64: https://www.python.org/downloads/windows/")
        print('   Durante la instalación marca "Add python.exe to PATH".')
        print("   Si ya tienes varias versiones, usa el lanzador: py -3.11 setup_env.py")
        print("   O crea python_cmd.local.txt con una línea: ruta completa a python.exe")
        return False

    if version.minor >= 13:
        print("⚠️  Python 3.13+ puede dar problemas con algún paquete en Windows.")
        print("   Si algo falla, instala Python 3.11 o 3.12 y ejecuta de nuevo.")
        print("✅ Continuando comprobaciones…")
        return True

    print("✅ Python en rango recomendado (3.10 – 3.12)")
    return True

def check_tesseract():
    """Verifica si Tesseract-OCR está instalado"""
    print_header("Verificando Tesseract-OCR")

    path = find_tesseract_executable()
    if path:
        print(f"✅ Tesseract encontrado en: {path}")
        return True

    print("❌ Tesseract-OCR no encontrado")
    print("\nInstalación recomendada:")
    print("1. Descarga desde: https://github.com/UB-Mannheim/tesseract/wiki")
    print("2. Ejecuta: tesseract-ocr-w64-setup-v5.x.exe")
    print("3. Instala en la ruta por defecto o marca la opción de añadir al PATH del sistema")
    print("4. Crea tesseract_path.local.txt (copia tesseract_path.local.txt.example)")
    print("   con una línea: ruta completa a tesseract.exe")
    print("5. O define TESSERACT_CMD con esa ruta")
    print("6. Ejecuta este script nuevamente")

    return False

def install_requirements():
    """Instala los paquetes de Python desde requirements.txt"""
    print_header("Instalando dependencias de Python")
    
    req_file = "requirements.txt"
    if not os.path.exists(req_file):
        print(f"❌ ERROR: No se encuentra {req_file}")
        return False
    
    try:
        print("Actualizando pip, setuptools y wheel…")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"]
        )
        print("Instalando paquetes desde requirements.txt…")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", req_file])
        print("✅ Dependencias instaladas correctamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ ERROR al instalar dependencias: {e}")
        print("   Revisa el mensaje de pip arriba. En Windows suele ayudar:")
        print("   - Ejecutar desde la carpeta del proyecto")
        print("   - python -m pip install --upgrade pip")
        print("   - python -m pip install -r requirements.txt")
        return False

def check_folders():
    """Verifica que las carpetas necesarias existan"""
    print_header("Verificando estructura de carpetas")
    
    required_folders = [
        "patrones",
        "logs",
        "logs/capturas"
    ]
    
    all_ok = True
    for folder in required_folders:
        if os.path.isdir(folder):
            print(f"✅ Carpeta {folder}/ existe")
        else:
            print(f"⚠️  Carpeta {folder}/ no existe - se creará al ejecutar")
            Path(folder).mkdir(parents=True, exist_ok=True)
    
    return all_ok

def check_pattern_files():
    """Verifica que los archivos de patrones existan"""
    print_header("Verificando archivos de patrones")
    
    pattern_dir = "patrones"
    if not os.path.isdir(pattern_dir):
        print(f"⚠️  Carpeta {pattern_dir}/ no existe")
        print("Los patrones se cargarán cuando sea necesario")
        return True
    
    files = os.listdir(pattern_dir)
    if files:
        print(f"✅ Se encontraron {len(files)} archivo(s) de patrón")
        for file in files:
            print(f"   - {file}")
        return True
    else:
        print(f"⚠️  La carpeta {pattern_dir}/ está vacía")
        return False

def test_imports():
    """Prueba que los módulos principales se pueden importar"""
    print_header("Probando importaciones")
    
    modules = {
        "pyautogui": "Automatización",
        "keyboard": "Input del teclado",
        "PIL": "Procesamiento de imágenes",
        "pytesseract": "Reconocimiento OCR",
        "cv2": "OpenCV (búsqueda de imágenes con confidence)",
    }
    
    all_ok = True
    for module, description in modules.items():
        try:
            __import__(module)
            print(f"✅ {module:15} - {description}")
        except ImportError:
            print(f"❌ {module:15} - {description} (NO INSTALADO)")
            all_ok = False
    
    return all_ok

def main():
    """Función principal"""
    print("\n" + "█"*50)
    print("█" + " "*48 + "█")
    print("█  Bot AX Contable - Setup del Entorno         █")
    print("█" + " "*48 + "█")
    print("█"*50)
    
    checks = [
        ("Python", check_python_version),
        ("Carpetas", check_folders),
        ("Patrones", check_pattern_files),
        ("Importaciones", test_imports),
        ("Tesseract", check_tesseract),
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"❌ Error en verificación de {name}: {e}")
            results[name] = False
    
    # Resumen
    print_header("Resumen de Verificación")
    for name, result in results.items():
        status = "✅ OK" if result else "❌ FALTA"
        print(f"{status} - {name}")
    
    # Instalar si falta algo
    if not results.get("Importaciones", False):
        print("\n¿Deseas instalar las dependencias de Python? (s/n): ", end="")
        if input().lower() == 's':
            if install_requirements():
                print("\nReintentando importaciones...")
                test_imports()
    
    # Resumen final
    print_header("Siguiente paso")
    if all(results.values()):
        print("✅ El entorno está listo!")
        print("\nPuedes iniciar el bot con:")
        print("  - Doble clic en: Lanzar_Bot_Universal.bat")
        print("  - O ejecuta: python app_gui.py")
    else:
        print("⚠️  Hay problemas que resolver antes de ejecutar el bot")
        if not results.get("Tesseract", False):
            print("\n🔴 CRÍTICO: Instala Tesseract-OCR primero")
        if not results.get("Importaciones", False):
            print("\n🔴 CRÍTICO: Instala las dependencias de Python")

if __name__ == "__main__":
    main()
