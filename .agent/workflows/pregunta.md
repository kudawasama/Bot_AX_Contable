# /pregunta - Consultoría Técnica Especializada

Este flujo de trabajo se activa cuando el usuario tiene dudas conceptuales, arquitectónicas o de funcionamiento. El objetivo es proporcionar respuestas claras y fundamentadas sin modificar el código fuente del proyecto.

## Reglas de Comportamiento CRÍTICAS

1. **PROHIBIDO EDITAR CÓDIGO**: Bajo ninguna circunstancia este flujo de trabajo permite el uso de herramientas de edición de archivos (`write_to_file`, `replace_file_content`, etc.). Su única función es **leer y explicar**.
2. **PROHIBIDO EJECUTAR COMANDOS**: No se deben proponer ni ejecutar comandos de terminal (`run_command`).
3. **Enfoque Puramente Informativo**: La tarea termina una vez que el usuario recibe la respuesta textual.
4. **Contextualización**: Analiza siempre el historial de la conversación y el estado actual del código antes de responder.

## Pasos del Flujo de Trabajo

1. **Reconocimiento**: Responde confirmando que estás operando bajo el modo `/pregunta`.
2. **Análisis de Requerimientos**: Identifica los puntos específicos de la duda del usuario y los archivos del código involucrados.
3. **Investigación de Código**: Lee los fragmentos de código relevantes para asegurar que la explicación sea 100% precisa respecto a la implementación actual.
4. **Respuesta Estructurada**:
   - **Introducción**: Explica el caso de forma concisa (aprox. 4 líneas), usando ejemplos si es necesario.
   - **Solución Propuesta**: Presenta al menos una solución técnica detallando el "por qué" y el "cómo" funcionaría.
   - **Recomendación**: Brinda una sugerencia final que sea compatible con la arquitectura actual del proyecto.
5. **Formato**: Utiliza bloques de código, negritas y llamadas de atención (alerts) para facilitar la lectura.
