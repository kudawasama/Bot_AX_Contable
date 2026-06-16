---
description: Flujo de trabajo principal del Bot AX Contable
---

# Flujo de Trabajo del Bot AX Contable — Reglas de Diseño Inmutables

Este documento describe con carácter **estricto y permanente** el flujo de procesamiento del bot contable sobre la interfaz de Dynamics AX. Estas directrices no deben ser modificadas ni revertidas bajo ninguna circunstancia.

---

## 1. Reglas Críticas de Interacción y Foco

* **Regla del Foco No Destructivo (PROHIBIDO realizar clics ciegos de foco):**
  El bot tiene estrictamente prohibido mover el mouse y realizar clics ciegos sobre coordenadas fijas de la tabla (como la parte superior del Sector A) para "asegurar foco". Dynamics AX interpreta los clics en registros ya marcados como órdenes para alternar el checkbox o limpiar la selección multiregistro, rompiendo el avance del ciclo.
  
* **Solución de Foco Dirigido:**
  El foco de la ventana de Dynamics AX debe recuperarse de manera natural y segura mediante el clic directo sobre el checkbox vacío de la `casilla_objetivo` a procesar en el ciclo actual. Si no hay casillas visibles, el foco se asegura al hacer clic sobre el botón o área de scroll.

---

## 2. Paso a Paso del Ciclo de Ejecución

El bot opera dividiendo la pantalla en tres sectores principales calibrados por el usuario:
* **Sector A**: Columna de checkboxes e IDs de diario.
* **Sector B**: Botones superiores de registro.
* **Sector Scroll (Sector C)**: Flecha/página de desplazamiento hacia abajo.

### Paso 1: Escaneo y Detección de Casillas (Sector A)
1. **Buscar checkboxes vacíos:** Localizar todas las coordenadas de casillas desmarcadas (`patrones/checkbox_vacio.png`) en el Sector A utilizando un umbral de confianza óptimo de **`0.85`** y ordenar la lista de arriba a abajo por su coordenada vertical Y.
2. **Buscar último marcado:** Localizar todas las coordenadas de casillas ya confirmadas (`patrones/check_usuario_marcado.png`) en el Sector A utilizando una confianza de **`0.85`** (para evitar falsos positivos). La coordenada Y del marcado más bajo define la barrera `ultimo_marcado_y`.
3. **Filtrar casillas vacías a procesar:**
   * Omitir cualquier checkbox vacío cuya coordenada Y sea menor o igual a `ultimo_marcado_y` (para no reprocesar registros superiores).
   * Omitir cualquier coordenada de pantalla redondeada que ya se encuentre registrada en el set de caché `posiciones_procesadas`.
4. **Leer Identificador (OCR):** Para el primer checkbox vacío que supere los filtros:
   * Capturar la franja derecha de texto a partir del offset configurado.
   * Procesar mediante Tesseract OCR en modo monolínea.
   * Normalizar el identificador de diario (dígitos numéricos).
   * Si el ID está en la lista negra (`blacklist.json`), ignorar la casilla y pasar a la siguiente vacía de la lista.
5. **Establecer Objetivo:** La primera casilla válida que supere las verificaciones se guarda como `casilla_objetivo`.

### Paso 2: Ejecución de Registro (Sector B)
1. Si se define la `casilla_objetivo`, el cursor se desplaza a sus coordenadas y realiza un único clic. Esto da foco a Dynamics AX y selecciona la fila.
2. Ir al Sector B y hacer clic en Registrar (`patrones/btn_registrar_menu.png`).
3. Esperar a que se despliegue la confirmación y hacer clic en Confirmar (`patrones/btn_registrar_confirm.png`).

### Paso 3: Espera de Registro y Pop-Ups
1. Monitorear la pantalla en espera de uno de los siguientes resultados:
   * **Éxito:** Aparece el pop-up de éxito de asiento (`patrones/msg_exito_asiento_1.png`). El bot lo cierra automáticamente presionando `ESC` y `ENTER`, guarda el diario en el registro diario e inicia el siguiente ciclo.
   * **Error:** Aparece el cartel de error (`patrones/Error_Registro.png`). El bot captura la pantalla del error, registra el fallo, añade el ID del diario a la lista negra (`blacklist.json`) para omitirlo en futuros inicios, cierra el pop-up de error y pasa al siguiente ciclo.

---

## 3. Regla Obligatoria de Desplazamiento (Scroll)

* Si tras analizar todos los checkboxes vacíos visibles en pantalla no se encuentra ninguno apto para procesar, el bot incrementa el contador de `intentos_scroll` y procede a presionar el botón de scroll de la interfaz (`patrones/Avanzar_Abajo.png`) o a realizar un scroll de teclado en el Sector A.
* **Limpieza de la Caché de Pantalla (OBLIGATORIO):**
  Inmediatamente después de completarse la interacción física de scroll, **se debe limpiar por completo el conjunto `posiciones_procesadas`** (`posiciones_procesadas.clear()`). Al desplazarse la pantalla, los nuevos registros suben y toman las coordenadas físicas que antes tenían otras filas. Limpiar la caché garantiza que el bot no los ignore en la siguiente iteración de escaneo.
