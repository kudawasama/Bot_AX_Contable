# Flujo del Ciclo — Bot AX Contable

## Ciclo principal

```
1. SECTOR A
   └── Buscar checkbox vacío → click

2. SECTOR B
   └── Click "Registrar"

3. VENTANA REGISTRAR
   └── Click confirmación

4. ESPERAR
   └── Esperar a que termine el registro en AX
   └── Esperar a que salgan los pop-ups
   └── Cerrar pop-ups

5. VOLVER AL PASO 1
   └── Siguiente checkbox vacío
```

## Si no hay checkboxes vacíos en Sector A

Cuando el Sector A está lleno de checkboxes marcados:

```
1. SECTOR C (Avanzar)
   └── Buscar botón "Avanzar"
   └── Click (3 veces × 2)

2. VOLVER A SECTOR A
   └── Verificar si hay checkbox vacío
   └── Si hay → comenzar ciclo 1 desde el paso 1
   └── Si no hay → repetir scroll (hasta 3 intentos)
```

## Vista general

```
   ┌─────────────────────────────────────────┐
   │   SECTOR A                              │
   │   [ ] checkbox vacío → click            │
   │                                         │
   │   SECTOR B                              │
   │   [Registrar] → click                   │
   │                                         │
   │   VENTANA REGISTRAR                     │
   │   [Confirmar] → click                   │
   │                                         │
   │   ESPERAR POP-UPS                       │
   │   → cierre automático                   │
   │                                         │
   │   ── Siguiente ciclo ──▶                │
   │                                         │
   │   Si no hay vacíos en A:                │
   │   SECTOR C [▼] → Avanzar               │
   │   → Volver a revisar A                  │
   └─────────────────────────────────────────┘
```
