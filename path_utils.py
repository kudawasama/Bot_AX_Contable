import os
import sys

def get_root_dir():
    """Devuelve el directorio donde reside el .exe o el script .py."""
    if getattr(sys, 'frozen', False) or '__compiled__' in globals():
        # Ejecutándose desde un archivo compilado (.exe)
        return os.path.dirname(sys.executable)
    # Ejecutándose desde el código fuente de Python
    return os.path.dirname(os.path.abspath(__file__))

def get_resource_path(relative_path):
    """
    Devuelve la ruta a un recurso (imágenes, iconos).
    En modo Onefile de Nuitka, los archivos se extraen en una carpeta temporal.
    Primero busca en la carpeta raíz externa (permite sobrescribir)
    y luego en la carpeta interna empaquetada.
    """
    # Intentar buscar fuera del .exe primero (permite personalización externa)
    external_path = os.path.join(get_root_dir(), relative_path)
    if os.path.exists(external_path):
        return external_path
    
    # En Nuitka, los recursos empaquetados están relativos a __file__ en la carpeta temporal
    internal_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)
    return internal_path

def get_external_path(relative_path):
    """
    Devuelve la ruta a un archivo que DEBE estar fuera del .exe (ej: licencia, logs).
    Siempre relativo al directorio del ejecutable.
    """
    return os.path.join(get_root_dir(), relative_path)
