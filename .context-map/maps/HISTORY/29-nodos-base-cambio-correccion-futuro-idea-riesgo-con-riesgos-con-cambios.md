# Bot_AX_Contable — Context Map

## Identidad del proyecto

Bot_AX_Contable

## Historia causal

- BASE.002: Proyecto 'Bot_AX_Contable' — 308 archivos, 288542 líneas, sin entrypoints
- BASE.001: Documentación principal: README.md
- RIESGO.001: Archivos de alta complejidad: observer_analyze.py, gui_classic.py, engine.py
- FUTURO.004: TODO: L4: Centraliza todos los defaults numéricos para facilitar ajustes.
- FUTURO.003: TODO: L47: _logger.setLevel(logging.DEBUG)

## Mapa mental de contexto

- **BASE**

  - **ID**, título/tags, estado, source, versión

    - **BASE.002** Proyecto 'Bot_AX_Contable' — 308 archivos, 288542 líneas, sin entrypoints `[arquitectura, class:other, proyecto]` completado | v1 | src: scanner | ev: Cantidad: 308; Líneas de código: 288542
      - Proyecto 'Bot_AX_Contable' — 308 archivos, 288542 líneas, sin entrypoints.
    - **BASE.001** Documentación principal: README.md `[class:chore, documentacion, proyecto]` completado | v1 | src: scanner | ev: Archivo: README.md
      - Documentación: Documentación principal: README.md.

- **IDEA**

  - **ID**, título/tags, estado, source, versión

    - **IDEA.002** [898600f] feat: observer watchdog — vigilancia en vivo del bot via cron `[class:feature, git, idea]` completado | v1 | src: git | ev: Cantidad: 898600
      - Feature implementada: feat: observer watchdog — vigilancia en vivo del bot via cron
    - **IDEA.001** [64e2d1c] feat: observer analyzer + event logging estructurado (JSONL) `[class:feature, git, idea]` completado | v1 | src: git | ev: Cantidad: 64
      - Feature implementada: feat: observer analyzer + event logging estructurado (JSONL)

- **FUTURO**

  - **ID**, título/tags, estado, source, versión

    - **FUTURO.004** TODO: L4: Centraliza todos los defaults numéricos para facilitar ajustes. `[class:chore]` pendiente | v1 | src: scanner | ev: Cantidad: 4
      - Pendiente: TODO: L4: Centraliza todos los defaults numéricos para facilitar ajustes..

Ubicación: `TODO`
    - **FUTURO.001** TODO: L258: event_log("scroll_performed", intento=intentos_scroll, metodo="boton") `[class:chore]` pendiente | v1 | src: scanner | ev: Cantidad: 258
      - Pendiente: TODO: L258: event_log("scroll_performed", intento=intentos_scroll, metodo="boton").

Ubicación: `TODO`
    - **FUTURO.002** TODO: L273: event_log("scroll_performed", intento=intentos_scroll, metodo="click") `[class:chore]` pendiente | v1 | src: scanner | ev: Cantidad: 273
      - Pendiente: TODO: L273: event_log("scroll_performed", intento=intentos_scroll, metodo="click").

Ubicación: `TODO`

- **CORRECCION**

  - **ID**, título/tags, estado, source, versión

    - **FUTURO.003** TODO: L47: _logger.setLevel(logging.DEBUG) `[class:fix]` pendiente | v1 | src: scanner | ev: Archivo: _logger.setLevel; Archivo: logging.DEBUG; Cantidad: 47
      - Pendiente: TODO: L47: _logger.setLevel(logging.DEBUG).

Ubicación: `TODO`
    - **FUTURO.005** TODO: L59: file_handler.setLevel(logging.DEBUG) `[class:fix]` pendiente | v1 | src: scanner | ev: Archivo: file_handler.setLevel; Archivo: logging.DEBUG; Cantidad: 59
      - Pendiente: TODO: L59: file_handler.setLevel(logging.DEBUG).

Ubicación: `TODO`
    - **CORRECCION.014** [3ef8880] fix: jiggle de mouse cada 12s / 1s para evitar suspension del notebook durante espera de registro `[class:fix, correccion, git]` completado | v1 | src: git | ev: Cantidad: 3
      - Corrección: fix: jiggle de mouse cada 12s / 1s para evitar suspension del notebook durante espera de registro
    - **CORRECCION.010** [3e5617d] fix: restaurar CHK_VACIO a 0.9 (unico cambio entre commit que funciona y ahora) `[class:fix, correccion, git]` completado | v1 | src: git | ev: Archivo: 0.9; Cantidad: 3
      - Corrección: fix: restaurar CHK_VACIO a 0.9 (unico cambio entre commit que funciona y ahora)
    - **CORRECCION.011** [6612fac] Revert "fix: restaurar deteccion check vacio - confianza 0.9 + filtro posicional + sector A 55px" `[class:fix, correccion, git]` completado | v1 | src: git | ev: Archivo: 0.9; Cantidad: 6612
      - Corrección: Revert "fix: restaurar deteccion check vacio - confianza 0.9 + filtro posicional + sector A 55px"
    - **CORRECCION.012** [738559f] fix: restaurar deteccion check vacio - confianza 0.9 + filtro posicional + sector A 55px `[class:fix, correccion, git]` completado | v1 | src: git | ev: Archivo: 0.9; Cantidad: 738559
      - Corrección: fix: restaurar deteccion check vacio - confianza 0.9 + filtro posicional + sector A 55px
    - **CORRECCION.013** [8596fb1] fix: bajar confianza CHK_VACIO de 0.9 a 0.8 por anti-aliasing `[class:fix, correccion, git]` completado | v1 | src: git | ev: Archivo: 0.9; Archivo: 0.8; Cantidad: 8596
      - Corrección: fix: bajar confianza CHK_VACIO de 0.9 a 0.8 por anti-aliasing
    - **CORRECCION.006** [ab65367] fix: bajar a 0.7 deteccion check marcado para encontrar el ultimo `[class:fix, correccion, git]` completado | v1 | src: git | ev: Archivo: 0.7; Cantidad: 65367
      - Corrección: fix: bajar a 0.7 deteccion check marcado para encontrar el ultimo
    - **CORRECCION.007** [b074875] fix: continuar desde el ultimo checkbox marcado hacia abajo `[class:fix, correccion, git]` completado | v1 | src: git | ev: Cantidad: 074875
      - Corrección: fix: continuar desde el ultimo checkbox marcado hacia abajo
    - **CORRECCION.004** [8b077e4] fix: ajustar sector A solo a columna checkboxes (x=300, w=55) `[class:fix, correccion, git]` completado | v1 | src: git | ev: Cantidad: 8
      - Corrección: fix: ajustar sector A solo a columna checkboxes (x=300, w=55)
    - **CORRECCION.003** [672e913] fix: auto-bump categoriza cambios (add/delete=minor, modify=patch) `[class:fix, correccion, git]` completado | v1 | src: git | ev: Cantidad: 672
      - Corrección: fix: auto-bump categoriza cambios (add/delete=minor, modify=patch)
    - **CORRECCION.005** [8ebabbe] fix: restaurar auto-bump patch simple `[class:fix, correccion, git]` completado | v1 | src: git | ev: Cantidad: 8
      - Corrección: fix: restaurar auto-bump patch simple
    - **CORRECCION.001** [43353fe] fix: desactivar auto-bump, version manual `[class:fix, correccion, git]` completado | v1 | src: git | ev: Cantidad: 43353
      - Corrección: fix: desactivar auto-bump, version manual
    - **CORRECCION.002** [4e89205] fix: bajar confianza scroll sector de 0.7 a 0.6 `[class:fix, correccion, git]` completado | v1 | src: git | ev: Archivo: 0.7; Archivo: 0.6; Cantidad: 4
      - Corrección: fix: bajar confianza scroll sector de 0.7 a 0.6

- **CAMBIO**

  - **ID**, título/tags, estado, source, versión

    - **BASE.003** Repositorio git con 100 commits totales, branch: main `[class:other, git]` completado | v1 | src: git | ev: Cantidad: 100
      - Repositorio: Repositorio git con 100 commits totales, branch: main.
    - **CAMBIO.004** [c91f5d7] docs: documentar especificacion del proceso del bot contable y agregar manual operativo inmutable `[cambio, class:feature, git]` completado | v1 | src: git | ev: Cantidad: 91
      - Cambio: docs: documentar especificacion del proceso del bot contable y agregar manual operativo inmutable
    - **CORRECCION.009** [2aad23d] refactor: Reestructuracion modular del proyecto bajo src/, ordenamiento de scripts auxiliares y correccion de foco no destructivo en Dynamics AX `[class:update, correccion, git]` completado | v1 | src: git | ev: Cantidad: 2
      - Corrección: refactor: Reestructuracion modular del proyecto bajo src/, ordenamiento de scripts auxiliares y correccion de foco no destructivo en Dynamics AX
    - **CAMBIO.003** [5cd53f0] docs: crear flujo del ciclo exacto del bot (según descripción) `[cambio, class:feature, git]` completado | v1 | src: git | ev: Cantidad: 5
      - Cambio: docs: crear flujo del ciclo exacto del bot (según descripción)
    - **CORRECCION.008** [a835dfa] merge: unificar fix/lint (GUI moderna + app_gui_qt + launchers) con main (estructura profesional) `[class:fix, correccion, git]` completado | v1 | src: git | ev: Cantidad: 835
      - Corrección: merge: unificar fix/lint (GUI moderna + app_gui_qt + launchers) con main (estructura profesional)
    - **CAMBIO.001** [2b6460d] chore: limpiar __pycache__ del tracking de git `[cambio, class:update, git]` completado | v1 | src: git | ev: Cantidad: 2
      - Cambio: chore: limpiar __pycache__ del tracking de git
    - **CAMBIO.002** [deaafb6] refactor: modernización GUI + launchers portable `[cambio, class:update, git]` completado | v1 | src: git | ev: Cantidad: 6
      - Cambio: refactor: modernización GUI + launchers portable

- **RIESGO**

  - **ID**, título/tags, estado, source, versión

    - **RIESGO.001** Archivos de alta complejidad: observer_analyze.py, gui_classic.py, engine.py `[class:other, riesgo]` activo | v1 | src: scanner | ev: Archivo: observer_analyze.py; Archivo: gui_classic.py; Archivo: engine.py; Líneas de código: 749
      - Zona de alta complejidad: Archivos de alta complejidad (5 total): observer_analyze.py (749 líneas); gui_classic.py (708 líneas); engine.py (456 líneas).

## Conexiones

_(sin conexiones)_

## Cambios esperados / vivos

- BASE.003: Repositorio git con 100 commits totales, branch: main
- CAMBIO.004: [c91f5d7] docs: documentar especificacion del proceso del bot contable y agregar manual operativo inmutable
- CORRECCION.009: [2aad23d] refactor: Reestructuracion modular del proyecto bajo src/, ordenamiento de scripts auxiliares y correccion de foco no destructivo en Dynamics AX
- CAMBIO.003: [5cd53f0] docs: crear flujo del ciclo exacto del bot (según descripción)
- CORRECCION.008: [a835dfa] merge: unificar fix/lint (GUI moderna + app_gui_qt + launchers) con main (estructura profesional)
- CAMBIO.001: [2b6460d] chore: limpiar __pycache__ del tracking de git
- CAMBIO.002: [deaafb6] refactor: modernización GUI + launchers portable

## Riesgos activos

- RIESGO.001: Archivos de alta complejidad: observer_analyze.py, gui_classic.py, engine.py

## Instrucciones para agentes

1) Usar solo este archivo como memoria oficial del proyecto.
2) No reeditar el mapa: usar CLI para agregar nodos/eventos.
3) Toda modificación genera snapshot en `.context-map/maps/HISTORY/`.

