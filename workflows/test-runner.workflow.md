## Workflow: Test-Runner

1. Recibir solicitud de ejecución de tests/linters.
2. Ejecutar `pytest` (si disponible) con `-q --maxfail=1`.
3. Ejecutar `ruff check .` o `flake8 .`.
4. Normalizar resultados y devolver JSON.

Criterios de éxito: `pytest` returncode == 0 y linter returncode == 0.
