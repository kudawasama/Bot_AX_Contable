import os
import sys
import subprocess
from path_utils import get_root_dir, get_external_path

def create_desktop_shortcut():
    """
    Crea un acceso directo en el escritorio para el ejecutable actual.
    Usa un pequeño script VBS temporal para invocar el Shell de Windows.
    """
    try:
        # Solo para sistemas operativos Windows
        if sys.platform != "win32":
            return
            
        # Si no estamos en modo "frozen" (.exe), no se crea (entorno de desarrollo)
        if not (getattr(sys, 'frozen', False) or '__compiled__' in globals()):
            return

        exe_path = sys.executable
        exe_name = os.path.basename(exe_path).replace(".exe", "")
        desktop = os.path.join(os.environ["USERPROFILE"], "Desktop")
        shortcut_path = os.path.join(desktop, f"{exe_name}.lnk")
        
        # Si el acceso directo ya existe, no lo sobreescribe
        if os.path.exists(shortcut_path):
            return

        # Preparamos el contenido del script VBS
        vbs_content = f'''
Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = "{shortcut_path}"
Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = "{exe_path}"
oLink.WorkingDirectory = "{os.path.dirname(exe_path)}"
oLink.Description = "Bot AX Contable - Automatización"
oLink.Save
'''
        vbs_path = os.path.join(os.environ["TEMP"], "create_shortcut.vbs")
        # Escritura manual para asegurar codificación nativa Windows
        with open(vbs_path, "w", encoding="latin-1") as f:
            f.write(vbs_content)
            
        # Ejecutamos el script VBS usando el motor nativo de Windows (cscript)
        subprocess.call(["cscript.exe", "/nologo", vbs_path])
        # Limpieza del script temporal
        os.remove(vbs_path)
        print("Acceso directo creado en el escritorio.")
        
    except Exception as e:
        print(f"No se pudo crear el acceso directo: {e}")

if __name__ == "__main__":
    # Prueba manual del creador de accesos directos
    create_desktop_shortcut()
