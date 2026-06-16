## Workflow: Verify (subagente)

1. Recibir artefactos a verificar (patch o lista de archivos).
2. Ejecutar checks: lint, compilación de `.py`, y tests si están disponibles.
3. Devolver `results`, `summary` y `blocking`.

Criterios de éxito: no existan `blocking: true` y failures críticos.
