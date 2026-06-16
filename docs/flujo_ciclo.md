# Flujo del Ciclo — Bot AX Contable

Este documento describe de manera gráfica y estructurada el flujo de control, la calibración de foco y las transiciones del bot. Estas especificaciones son de carácter permanente.

---

## Ciclo Principal de Registro

```
       ┌───────────────────────────────┐
       │     Inicio del Ciclo N        │
       └───────────────┬───────────────┘
                       │
                       ▼
         ¿Hay checkbox vacío visible?
         [ confidence=0.85 en Sector A ]
                       │
              ┌────────┴────────┐
              ▼ SI              ▼ NO
     ┌─────────────────┐ ┌─────────────────────────────┐
     │ ¿Está debajo de │ │   Realizar Scroll Abajo     │
     │ ultimo_marcado? │ │   [ 3 intentos máximo ]     │
     └────────┬────────┘ └──────────────┬──────────────┘
              │                         │
      ┌───────┴───────┐                 ▼
      ▼ SI            ▼ NO    Limpiar positions_cache  
  ¿Está en la   (Ignorar fila) [ posiciones_procesadas.clear() ]
  blacklist o   (Pasar a sig)           │
 positions_cache?                       ▼
      │                      ¿Se detectaron nuevos?
  ┌───┴───┐                   ┌─────────┴─────────┐
  ▼ NO    ▼ SI                ▼ SI                ▼ NO
Procesar (Ignorar fila)   Iniciar Ciclo     Detener Bot
  │                       desde Paso 1        (Fin)
  ▼
Foco Dirigido (Mover mouse y Click en la coordenada de la Casilla Objetivo)
  │
  ▼
Sector B (Click Registrar Menu → Esperar → Click Confirmar)
  │
  ▼
Esperar Resultado (Monitorear pop-ups de Éxito o Error en pantalla completa)
  │
  ├─► Éxito (Pop-up de asiento): Cerrar pop-up → Loguear Éxito → Ciclo N + 1
  │
  └─► Error (Cartel de error AX): Captura → Loguear Error → Lista Negra → Cerrar pop-up → Ciclo N + 1
```

---

## Consideraciones Inmutables del Proceso

> [!IMPORTANT]
> **1. Regla de Foco Dirigido (No destructiva):**
> Queda prohibido realizar clics ciegos de foco en la cabecera de la tabla de Dynamics AX al iniciar los ciclos. El foco de la aplicación se recupera exclusivamente mediante el clic dirigido sobre la coordenada del checkbox vacío a procesar. Esto evita alterar o desmarcar accidentalmente las filas completadas en iteraciones anteriores.

> [!IMPORTANT]
> **2. Limpieza de Caché tras Scroll:**
> Cada vez que el bot ejecute la acción física de scroll (sea a través de la flecha del Sector C o mediante el teclado), es mandatorio ejecutar `posiciones_procesadas.clear()`. Esto evita que las nuevas casillas que entran en la pantalla sean ignoradas por coincidir con coordenadas visuales previas.
