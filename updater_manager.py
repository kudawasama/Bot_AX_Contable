import os
import sys
import subprocess
import time
import requests
from path_utils import get_root_dir, get_external_path

# Versión actual de la aplicación
CURRENT_VERSION = "1.00"
# URL de ejemplo para verificación de versión (deberá configurarse por el usuario)
UPDATE_URL = "https://raw.githubusercontent.com/usuario/bot_ax/main/version.json"

def check_for_updates():
    """Busca si hay una nueva versión disponible en línea."""
    try:
        # Si no estamos en modo compilado (.exe), no buscamos actualizaciones (entorno desarrollo)
        if not (getattr(sys, 'frozen', False) or '__compiled__' in globals()):
            return False, CURRENT_VERSION

        respuesta = requests.get(UPDATE_URL, timeout=5)
        if respuesta.status_code == 200:
            datos = respuesta.json()
            version_remota = datos.get("version", CURRENT_VERSION)
            download_url = datos.get("url", "")
            
            # Comparación numérica simple
            if float(version_remota) > float(CURRENT_VERSION):
                return True, version_remota, download_url
                
    except Exception as e:
        print(f"Error al buscar actualizaciones: {e}")
        
    return False, CURRENT_VERSION, ""

def apply_update(download_url):
    """
    Descarga el nuevo .exe y lo reemplaza usando un script .bat atómico.
    """
    try:
        exe_path = sys.executable
        new_exe_path = exe_path + ".new"
        
        # Descarga de la nueva versión
        print(f"Descargando actualización desde {download_url}...")
        respuesta = requests.get(download_url, stream=True)
        with open(new_exe_path, "wb") as f:
            for bloque in respuesta.iter_content(chunk_size=8192):
                f.write(bloque)
        
        # Creamos un script .bat para reemplazo atómico
        # 1. Espera que el proceso original termine.
        # 2. Borra el .exe anterior.
        # 3. Renombra el nuevo al original.
        # 4. Inicia el nuevo proceso.
        # 5. Se borra a sí mismo.
        bat_content = f'''
@echo off
timeout /t 2 /nobreak > nul
del "{exe_path}"
ren "{new_exe_path}" "{os.path.basename(exe_path)}"
start "" "{exe_path}"
del "%~f0"
'''
        bat_path = os.path.join(os.environ["TEMP"], "update_bot.bat")
        with open(bat_path, "w") as f:
            f.write(bat_content)
            
        # Lanzamos el script .bat de forma independiente (no bloqueante)
        subprocess.Popen(["cmd.exe", "/c", bat_path], 
                         creationflags=subprocess.CREATE_NO_WINDOW)
        
        # Terminamos el proceso actual
        sys.exit(0)
        
    except Exception as e:
        print(f"Error al aplicar la actualización: {e}")
        return False
