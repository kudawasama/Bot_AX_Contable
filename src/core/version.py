"""version.py — Fuente única de verdad para la versión del Bot AX Contable.

Formato: v-{major:02d}.{minor:02d}.{patch:02d}
Ejemplo: v-00.01.42
"""
import subprocess
import os

__version__: str = "00.08.00"
VERSION_TAG: str = f"v-{__version__}"


def get_git_short_sha() -> str:
    """Retorna el SHA corto del último commit Git, o '??????' si ocurre un error.

    Si el repositorio local tiene modificaciones no commiteadas,
    añade un sufijo indicador ' ◇'.

    Returns:
        str: El hash SHA corto de 7 caracteres o indicador de estado.
    """
    try:
        # Directorio de este archivo: src/core/
        core_dir: str = os.path.dirname(os.path.abspath(__file__))
        # Raíz del repositorio (dos niveles arriba: src/core/ -> src/ -> raíz)
        repo_root: str = os.path.dirname(os.path.dirname(core_dir))
        
        # Ejecutar comandos de Git
        sha_proc: subprocess.CompletedProcess = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, cwd=repo_root, timeout=2
        )
        sha: str = sha_proc.stdout.strip()

        dirty_proc: subprocess.CompletedProcess = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, cwd=repo_root, timeout=2
        )
        dirty: str = dirty_proc.stdout.strip()
        
        if dirty:
            sha += " ◇"
            
        return sha if sha else "??????"
    except Exception:
        return "??????"
