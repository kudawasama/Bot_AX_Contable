"""
_version.py — fuente única de verdad para la versión de Bot AX Contable.

Formato: v-{major:02d}.{minor:02d}.{patch:02d}
Ejemplo: v-00.01.42

Pre-alpha. El pre-commit hook auto-bumpea según los cambios:
  - Archivos NUEVOS añadidos → minor (+0.01.00)
  - Archivos ELIMINADOS → minor (+0.01.00)
  - Solo modificaciones en archivos existentes → patch (+0.00.01)
  - Si se tocó _version.py manualmente → NO auto-bump
"""

import subprocess
import os

__version__ = "00.01.44"
VERSION_TAG = f"v-{__version__}"


def get_git_short_sha() -> str:
    """Retorna el SHA corto del último commit, o '??????' si falla."""
    try:
        repo = os.path.dirname(os.path.abspath(__file__))
        sha = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, cwd=repo, timeout=2,
        ).stdout.strip()

        dirty = (
            subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True, text=True, cwd=repo, timeout=2,
            ).stdout.strip()
        )
        if dirty:
            sha += " ◇"
        return sha
    except Exception:
        return "??????"
