# Flujo del Ciclo — Bot AX Contable

Este documento describe de manera gráfica y estructurada el flujo de control, la calibración de foco, el filtrado dinámico y las transiciones de estado del bot contable. Estas especificaciones son de carácter permanente.

---

## Ciclo Principal de Registro

```
                 ┌─────────────────────────────────┐
                 │    Inicio de Ejecución Bot      │
                 └────────────────┬────────────────┘
                                  │
                                  ▼
                 ┌─────────────────────────────────┐
                 │     Verificar Tesseract OCR     │
                 └────────────────┬────────────────┘
                                  │
                                  ▼
                 ┌─────────────────────────────────┐
                 │ Cargar Sectores e Config / Blacklist│
                 │   [ Sector A con Padding Activo ]   │
                 └────────────────┬────────────────┘
                                  │
                                  ▼
                 ┌─────────────────────────────────┐
                 │       Inicio de Ciclo N         │
                 └────────────────┬────────────────┘
                                  │
                                  ▼
                 ¿Se detecta pop-up Formularios? ────────► SI ──► Detener Bot
                                  │ NO                             (Parada Emergencia)
                                  ▼
                       ¿Hay checkboxes vacíos?
                     [ confianza=0.85 en Sector A ]
                                  │
                         ┌────────┴────────┐
                         ▼ SI              ▼ NO
               ┌───────────────────┐ ┌───────────────────────────┐
               │  Buscar último    │ │ Realizar Scroll Abajo     │
               │  check marcado    │ │ [ 3 intentos máximo ]    │
               └─────────┬─────────┘ └─────────────┬─────────────┘
                         │                         │
                         ▼                         ▼
               ┌───────────────────┐     ¿Scroll exitoso?
               │  Calcular barrera │     ┌─────────┴─────────┐
               │  ultimo_marcado_y │     ▼ SI                ▼ NO
               └─────────┬─────────┘   Limpiar caché de    Detener Bot
                         │             posiciones          (Fin de registros)
                         ▼             [posiciones_procesadas.clear()]
              ¿Está la casilla vacía               │
             debajo de ultimo_marcado_y?           ▼
                         │               Reiniciar ciclo
                 ┌───────┴───────┐       desde Paso 1
                 ▼ SI            ▼ NO
            ¿Está en la    ──► (Ignorar casilla)
          blacklist/caché?
                 │
         ┌───────┴───────┐
         ▼ NO            ▼ SI
     Elegir como   ──► (Ignorar casilla)
  casilla_objetivo
         │
         ▼
 ┌────────────────────────────────────────────────────────┐
 │ 1. Foco Dirigido: Mover mouse y click en coord de       │
 │    casilla_objetivo (No destructivo)                  │
 └───────────────────────┬────────────────────────────────┘
                         │
                         ▼
 ┌────────────────────────────────────────────────────────┐
 │ 2. Sector B: Click en Registrar Menú (Timeout 30s)     │
 └───────────────────────┬────────────────────────────────┘
                         │
                         ▼
 ┌────────────────────────────────────────────────────────┐
 │ 3. Confirmación: Click en Confirmar (Timeout 20s)      │
 └───────────────────────┬────────────────────────────────┘
                         │
                         ▼
 ┌────────────────────────────────────────────────────────┐
 │ 4. Esperar Resultado (Timeout 1 hora)                 │
 └───────────────────────┬────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         ▼                               ▼
      [EXITO]                         [ERROR]
(Detecta check_marcado)       (Detecta error_registro)
         │                               │
         ▼                               ▼
· Registrar en Log OK          · Capturar pantalla fallo
· Avanzar a Ciclo N + 1        · Registrar en Log ERROR
                               · Agregar ID a blacklist.json
                               · Cerrar pop-up con ESC
                               · Avanzar a Ciclo N + 1
```

---

## Consideraciones Inmutables del Proceso

> [!IMPORTANT]
> **1. Regla de Foco Dirigido (No destructiva):**
> Queda estrictamente prohibido realizar clics ciegos de foco en la cabecera de la tabla de Dynamics AX al iniciar los ciclos. El foco de la aplicación se recupera exclusivamente mediante el clic dirigido sobre la coordenada del checkbox vacío a procesar. Esto evita alterar o desmarcar accidentalmente las filas completadas en iteraciones anteriores.

> [!IMPORTANT]
> **2. Limpieza de Caché tras Scroll:**
> Cada vez que el bot ejecute la acción física de scroll (sea a través de la flecha del Sector C o mediante el teclado), es mandatorio ejecutar `posiciones_procesadas.clear()`. Esto evita que las nuevas casillas que entran en la pantalla sean ignoradas por coincidir con coordenadas visuales previas.

> [!IMPORTANT]
> **3. Blacklist de Errores Persistente:**
> La lista negra de diarios con error (`blacklist.json`) reside en la raíz y persiste entre ejecuciones. Cualquier diario que lance un error permanente debe ser omitido en el escaneo inicial de casillas para que el flujo contable nunca se detenga en registros inválidos.
