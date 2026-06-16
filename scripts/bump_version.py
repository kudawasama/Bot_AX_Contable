#!/usr/bin/env python
"""bump_version.py — incrementa la versión en src/core/version.py.

Uso:
    python scripts/bump_version.py patch     # +0.00.01 (por defecto)
    python scripts/bump_version.py minor     # +0.01.00
    python scripts/bump_version.py major     # +01.00.00
"""

import re
import sys
from pathlib import Path
from typing import Tuple

# Ubicación del archivo de versión src/core/version.py a partir de scripts/
VERSION_FILE: Path = Path(__file__).parent.parent / "src" / "core" / "version.py"

# Expresión regular compatible con tipados explícitos de tipo: __version__: str = "XX.XX.XX"
_PATTERN: re.Pattern = re.compile(r'__version__(?:\s*:\s*str)?\s*=\s*"(\d+)\.(\d+)\.(\d+)"')


def read_version() -> Tuple[str, str, int, int, int]:
    """Lee el archivo de versión y extrae los campos correspondientes.

    Returns:
        Tuple[str, str, int, int, int]: Contenido completo, coincidencia exacta, major, minor, patch.
    """
    if not VERSION_FILE.exists():
        print(f"ERROR: No existe el archivo de versión en: {VERSION_FILE}", file=sys.stderr)
        sys.exit(1)
        
    content: str = VERSION_FILE.read_text(encoding="utf-8")
    m = _PATTERN.search(content)
    if not m:
        print("ERROR: no se encontró __version__ en version.py", file=sys.stderr)
        sys.exit(1)
        
    raw: str = m.group()
    major, minor, patch = int(m.group(1)), int(m.group(2)), int(m.group(3))
    return content, raw, major, minor, patch


def write_version(content: str, new_raw: str, new_ver: str) -> None:
    """Reemplaza la versión vieja por la nueva y escribe los cambios.

    Args:
        content (str): Contenido completo del archivo.
        new_raw (str): Coincidencia original de versión a reemplazar.
        new_ver (str): Nueva cadena de versión.
    """
    # Conservamos el tipado : str al guardar
    new_content: str = content.replace(new_raw, f'__version__: str = "{new_ver}"')
    VERSION_FILE.write_text(new_content, encoding="utf-8")
    print(f"v-{new_ver}")


def main() -> None:
    """Analiza argumentos de consola e incrementa el campo correspondiente de versión."""
    part: str = (sys.argv[1] if len(sys.argv) > 1 else "patch").lower()

    content, raw, major, minor, patch = read_version()

    if part == "major":
        major += 1
        minor = 0
        patch = 0
    elif part == "minor":
        minor += 1
        patch = 0
    else:  # patch
        patch += 1

    new_ver: str = f"{major:02d}.{minor:02d}.{patch:02d}"
    write_version(content, raw, new_ver)


if __name__ == "__main__":
    main()
