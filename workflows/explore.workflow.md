## Workflow: Explore (subagente)

1. Recibir objetivo claro del Orquestador.
2. Escanear repo (priorizar archivos relevantes).
3. Extraer hasta 5 snippets con contexto.
4. Devolver JSON con `files`, `snippets`, `summary`.

Criterios de éxito: la lista `files` contiene al menos los principales módulos relacionados con la tarea.
