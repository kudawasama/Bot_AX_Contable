# Skill: Orquestador

Propósito:
Esta skill define comportamientos y buenas prácticas para el Orquestador: descomposición, delegación, consolidación y entrega.

Capacidades:
- Planificación de alto nivel y descomposición de tareas.
- Orquestación de subagentes mediante `runSubagent`.
- Validación y ensamblado de resultados.

Limitaciones y seguridad:
- No ejecutar comandos peligrosos sin confirmación del usuario.
- Siempre preservar backups antes de aplicar cambios a archivos del repositorio (si procede).

Cuándo invocar:
- Tareas multi-paso que requieren lectura del repositorio, cambios de código y verificación.

Ejemplo de flujo (alto nivel):
1. Clarificar requerimientos con el usuario.
2. Invocar `Explore` para recolectar contexto.
3. Invocar `Implement` para generar parches o archivos.
4. Invocar `Verify` para revisar la calidad.
5. Consolidar y devolver entregable.
