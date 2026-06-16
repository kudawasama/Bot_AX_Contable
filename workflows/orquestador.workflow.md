## Workflow: Orquestación de tareas complejas

Pasos:
1. Recepción: Recibe tarea del usuario y confirma ambigüedades.
2. Descomposición: Divide en pasos numerados y asigna subagentes.
3. Contexto: Ejecuta `Explore` para obtener archivos y dependencias.
4. Implementación: Ejecuta `Implement` para generar cambios (parches o archivos).
5. Verificación: Ejecuta `Verify` para validación estática y pruebas básicas.
6. Consolidación: Recolecta outputs y prepara el `deliverable`.
7. Entrega: Devuelve resumen, steps y artefactos listos.

Criterios de éxito:
- Cada paso debe devolver el `expected_output` definido.
- El `Verify` debe pasar checks mínimos (lint, tests unitarios si aplica).

Notas:
- Mantener cada subagent invocation pequeña y con objetivos testables.
