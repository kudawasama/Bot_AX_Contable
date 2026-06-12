#!/usr/bin/env python
"""
bump_version.py — Incrementa la versión en _version.py.

Uso:
    python scripts/bump_version.py patch     # +0.00.01 (por defecto)
    python scripts/bump_version.py minor     # +0.01.00
    python scripts/bump_version.py major     # +01.00.00

Sin argumentos: patch.
"""

import re
import sys
from pathlib import Path

# _version.py está en la raíz del proyecto
VERSION_FILE = Path(__file__).resolve().parent.parent / "_version.py"

_PATTERN = re.compile(r'__version__\s*=\s*"(\d+)\.(\d+)\.(\d+)"')


def read_version() -> tuple:
    content = VERSION_FILE.read_text(encoding="utf-8")
    m = _PATTERN.search(content)
    if not m:
        print("ERROR: no se encontró __version__ en _version.py", file=sys.stderr)
        sys.exit(1)
    raw = m.group()
    major, minor, patch = int(m.group(1)), int(m.group(2)), int(m.group(3))
    return content, raw, major, minor, patch


def write_version(content, new_raw, new_ver):
    new_content = content.replace(new_raw, f'__version__ = "{new_ver}"')
    VERSION_FILE.write_text(new_content, encoding="utf-8")
    print(f"v-{new_ver}")


def main():
    part = (sys.argv[1] if len(sys.argv) > 1 else "patch").lower()
    content, raw, major, minor, patch = read_version()

    if part == "major":
        major += 1
        minor = 0
        patch = 0
    elif part == "minor":
        minor += 1
        patch = 0
    else:
        patch += 1

    new_ver = f"{major:02d}.{minor:02d}.{patch:02d}"
    write_version(content, raw, new_ver)


if __name__ == "__main__":
    main()
