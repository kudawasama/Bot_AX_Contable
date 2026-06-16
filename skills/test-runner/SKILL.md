# Skill: Test-Runner

Propósito:
Definir cómo ejecutar pruebas y linters automáticamente y cómo reportar resultados.

Comportamiento:
- Ejecutar `pytest` y `ruff`/`flake8` si están disponibles.
- Normalizar salida en JSON para que el Orquestador la incluya en `steps`.

Salida:
- `pytest`, `linter` con `returncode`, `stdout`, `stderr`.
