"""
_version.py — fuente única de verdad para la versión de Bot AX Contable.

Formato: v-{major:02d}.{minor:02d}.{patch:02d}
Ejemplo: v-00.01.24

El versionado es MANUAL. Para incrementar la versión:
    python bump_version.py patch   # bug fixes
    python bump_version.py minor   # nuevas funcionalidades
    python bump_version.py major   # cambios grandes/rompientes

Sin auto-bump. Tú decides cuándo y qué bump aplicar.
"""

import subprocess
import os

__version__ = "00.01.39"
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
