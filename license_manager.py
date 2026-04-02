import hashlib
import subprocess
import os
import sys
from path_utils import get_external_path

# Clave secreta para la firma digital - ¡Mantener esto en privado!
# Si se cambia esta sal, todas las llaves generadas anteriormente dejarán de ser válidas.
SECRET_SALT = "COTANO_SECRET_2024_PRO_AX"

def get_hwid():
    """Genera un ID de hardware único para la máquina actual usando PowerShell."""
    try:
        # Alternativa moderna a WMIC usando Get-CimInstance
        # Obtiene el número de serie de la placa base y el UUID del sistema
        cmd = 'powershell -NoProfile -Command "(Get-CimInstance Win32_BaseBoard).SerialNumber; (Get-CimInstance Win32_ComputerSystemProduct).UUID"'
        salida = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode().strip().split('\r\n')
        
        serial = salida[0].strip() if len(salida) > 0 else "NOSERIAL"
        uuid = salida[1].strip() if len(salida) > 1 else "NOUUID"
        
        id_crudo = f"{serial}-{uuid}"
        return hashlib.sha256(id_crudo.encode()).hexdigest()[:16].upper()
    except Exception:
        # Respaldo en caso de que PowerShell falle (poco probable en Windows moderno)
        import socket
        import uuid as _uuid
        fallback = f"{socket.gethostname()}-{_uuid.getnode()}"
        return hashlib.sha256(fallback.encode()).hexdigest()[:16].upper()

def generate_key(hwid):
    """Genera una llave de licencia para un HWID específico."""
    crudo = f"{hwid}{SECRET_SALT}"
    return hashlib.sha256(crudo.encode()).hexdigest()[:24].upper()

def check_license():
    """Verifica si existe una licencia válida en este equipo."""
    # Usamos la utilidad de rutas para asegurar que busque al lado del .exe
    ruta_licencia = get_external_path("license.key")
    
    if not os.path.exists(ruta_licencia):
        return False, get_hwid()
    
    try:
        with open(ruta_licencia, "r") as f:
            llave_guardada = f.read().strip()
        
        hwid = get_hwid()
        llave_esperada = generate_key(hwid)
        
        return (llave_guardada == llave_esperada), hwid
    except Exception:
        return False, get_hwid()

if __name__ == "__main__":
    # Si se ejecuta directamente, muestra el HWID y la llave sugerida
    hwid_pc = get_hwid()
    print(f"ID de Hardware (HWID): {hwid_pc}")
    print(f"Llave sugerida: {generate_key(hwid_pc)}")
