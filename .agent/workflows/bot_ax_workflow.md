---
description: Flujo de trabajo principal del Bot AX Contable
---

# Flujo de Trabajo del Bot AX Contable

Este documento contiene las INSTRUCCIONES ESTRICTAS Y PERMANENTES sobre cómo debe operar el bot en el escritorio remoto.
Estas instrucciones no deben ser olvidadas ni alteradas por procesos anteriores.

## Contexto

El bot opera en un escritorio remoto. El área de trabajo está definida en la imagen `areas de trabajo.png`. Existen dos sectores principales: Sector A y Sector B.

## Paso a Paso del Bot

1. **Definir Áreas de Trabajo:**
   Cargar y establecer las coordenadas de las áreas basadas en `areas de trabajo.png` (Sector A y Sector B).

2. **Acción en el Sector A (Selección inicial):**
   - Buscar el primer patrón `patrones/checkbox_vacio.png` DENTRO del Sector A.
   - Hacer CLICK en esa casilla vacía encontrada.

3. **Acción en el Sector B (Registro):**
   - Ir al Sector B.
   - Buscar el patrón `patrones/btn_registrar_menu.png`.
   - Posicionar el puntero del mouse sobre el botón y hacer CLICK.
   - Se abrirá un sub-menú/botón secundario llamado `patrones/btn_registrar_confirm.png`.
   - Hacer CLICK en `btn_registrar_confirm.png`.

4. **Bucle de Espera y Verificación:**
   - Mantenerse en espera (hasta 1 hora si es necesario).
   - Existen dos resultados posibles:
     - **Éxito**: Aparece el patrón `patrones/check_usuario_marcado.png` en el Sector A.
     - **Error**: Aparece el mensaje de error `patrones/Error_Registro.png`.

5. **Acciones según el Resultado:**
   - **En caso de Éxito:**
     - Hacer CLICK sobre el `check_usuario_marcado.png`.
     - Presionar la tecla `FLECHA HACIA ABAJO` para pasar a la siguiente iteración.
     - Volver a iniciar el proceso desde el paso 2 (Acción Sector A). *Nota: dado que bajamos una fila, la fila exitosa ya no es vacía y el código automáticamente procesará la próxima casilla.*
   - **Manejo de Avance (Éxito o Error):**
     - El bot siempre incrementa un contador de `saltos_acumulados` después de intentar un registro.
     - En el siguiente ciclo, calcula la posición de la próxima fila sumando N * 21 píxeles a la coordenada visual del primer `checkbox_vacio.png`.
     - Esto garantiza que el bot nunca se quede "pegado" en una fila ya procesada.
