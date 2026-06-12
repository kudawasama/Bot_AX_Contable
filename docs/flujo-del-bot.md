# Bot AX Contable — Documentación de Flujo

## Visión General

Bot de automatización para **Microsoft Dynamics AX** que registra diarios contables mediante reconocimiento de imágenes (template matching con PyAutoGUI) y OCR (Tesseract).

---

## Arquitectura (src/bot_ax/)

```
src/bot_ax/
├── __init__.py
├── __main__.py                  # Entry point: python -m bot_ax
├── _version.py                  # Versión (auto-bump patch por commit)
├── config/
│   ├── __init__.py
│   ├── settings.py              # Constantes: rutas de imágenes patrón
│   ├── sectores.py              # Carga/valida/guarda config_sectores.json
│   └── defaults.py              # Valores por defecto (confianzas, timeouts)
├── core/
│   ├── __init__.py
│   ├── engine.py                # Ciclo principal run_bot() (~320 líneas)
│   ├── blacklist.py             # Carga/guarda lista negra persistente
│   ├── registrador.py           # Escribe registro_YYYY-MM-DD.txt
│   └── logger.py                # Logging estructurado con rotación
└── vision/
    ├── __init__.py
    ├── detector.py              # buscar_y_clickear, esperar_resultado_registro
    ├── captura.py               # capturar_pantalla_error
    ├── ids.py                   # normalizar_id_diario
    └── ocr.py                   # leer_id_diario (Tesseract OCR)
```

---

## Flujo Completo del Bot

### 1. INICIO

```
[Usuario] → Click "Start Engine" en GUI
           → run_bot(stop_event, pause_event) se ejecuta en thread
```

**Validaciones iniciales:**
1. Verificar que Tesseract OCR existe en `TESSERACT_CMD`
2. Cargar `config_sectores.json` (Sector A, B, C)
3. Cargar `blacklist.json` (diarios con error previo)

Si alguna validación falla → el bot se detiene con mensaje claro.

---

### 2. CICLO PRINCIPAL (while True)

```
Cada iteración procesa UN diario.
```

```
┌─────────────────────────────────────────────────┐
│ 2.1 BUSCAR CHECKBOX VACÍO EN SECTOR A           │
│                                                  │
│   Imagen: checkbox_vacio.png (21×17 píxeles)    │
│   Confianza: 0.9                                 │
│   Lugar: Sector A únicamente                     │
│                                                  │
│   ¿Encuentra?                                    │
│   ├─ No → 2.2 (SCROLL)                          │
│   └─ Sí → 2.3 (LEER ID)                         │
└─────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│ 2.2 SCROLL (si no hay checkboxes en Sector A)   │
│                                                  │
│   Busca Avanzar_Abajo.png (16×15 píxeles)        │
│   Solo en Sector C (confianza 0.7)               │
│   Sin búsqueda en pantalla completa              │
│                                                  │
│   ¿Encuentra botón scroll?                       │
│   ├─ No → scroll por clic + rueda               │
│   └─ Sí → 3 clics en el botón                   │
│                                                  │
│   ↓ Una vez terminado el scroll:                 │
│   → VOLVER a 2.1 (buscar en Sector A)           │
│                                                  │
│   Si tras 3 intentos no hay checkboxes → FIN     │
└─────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│ 2.3 LEER ID (OCR)                                │
│                                                  │
│   Captura región a la izquierda del checkbox     │
│   usando ocr_region_offset de config             │
│   Aplica Tesseract OCR (PSM 7, línea única)      │
│   Normaliza: extrae solo dígitos                 │
│   (IS00327946iat → 00327946)                     │
│                                                  │
│   ¿Está en lista negra?                          │
│   ├─ Sí → salta, busca otro checkbox             │
│   └─ No → continúa                               │
└─────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│ 2.4 REGISTRAR CLICKS                             │
│                                                  │
│   a) Click en checkbox (selecciona diario)       │
│   b) Busca btn_registrar_menu.png → click        │
│      - En Sector B (confianza 0.8)               │
│      - Fallback: pantalla completa                │
│   c) Busca btn_registrar_confirm.png → click     │
│      - Pantalla completa (confianza 0.8)         │
│                                                  │
│   ¿Menú o confirmar no encontrado?               │
│   ├─ Sí → agrega a blacklist → continúa          │
│   └─ No → espera resultado                       │
└─────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│ 2.5 ESPERAR RESULTADO (hasta 60 min)             │
│                                                  │
│   Cada 1 segundo verifica:                       │
│                                                  │
│   1° ¿Pop-up de ÉXITO?                          │
│      Imagen: msg_exito_asiento_1.png             │
│      Lugar: pantalla completa                    │
│      Confianza: 0.8                              │
│      → Presiona ESC + Enter (cierra diálogo)    │
│      → RESULT:OK                                 │
│                                                  │
│   2° ¿Pop-up de ERROR?                          │
│      Imagen: Error_Registro.png                  │
│      Lugar: pantalla completa                    │
│      Confianza: 0.9                              │
│      → RESULT:ERROR                              │
│                                                  │
│   ¿Presionó ESC usuario?                         │
│   → CANCELADO (stop_event)                       │
└─────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│ 2.6 POST-PROCESO                                 │
│                                                  │
│   ÉXITO:                                         │
│   ├─ Registra en registro_YYYY-MM-DD.txt         │
│   └─ Siguiente ciclo                             │
│                                                  │
│   ERROR:                                         │
│   ├─ Captura pantalla (logs/capturas/)           │
│   ├─ Agrega a blacklist.json (persistente)       │
│   ├─ Cierra pop-up (ESC + clic)                  │
│   └─ Siguiente ciclo                             │
│                                                  │
│   CANCELADO:                                     │
│   └→ Sale del ciclo → Ejecución finalizada       │
└─────────────────────────────────────────────────┘
         │
         ▼
                  ┌─────────────────────┐
                  │ SIGUIENTE CICLO     │
                  │ (vuelve a 2.1)      │
                  └─────────────────────┘
```

---

## Tres Sectores de Pantalla

| Sector | Nombre | Propósito | Tamaño típico |
|--------|--------|-----------|---------------|
| A | Checkboxes | Buscar `checkbox_vacio.png` (21×17 px) | ~300×470 px |
| B | Botones menú | Buscar `btn_registrar_menu.png` (148×32 px) | ~200×30 px |
| C | Scroll | Buscar `Avanzar_Abajo.png` (16×15 px) | ~32×24 px |

Cada sector se define con `setup_areas.py` (selector visual de rectángulos).
Las coordenadas se guardan en `config_sectores.json`.

**Regla fundamental:** cada sector se usa SOLO para su propósito. No hay búsquedas fuera del sector. Si no se encuentra en el sector → se usa el mecanismo de scroll (Sector C) o fallback a pantalla completa solo para botones y pop-ups.

---

## Imágenes Patrón (patrones/)

| Archivo | Tamaño | Uso |
|---------|--------|-----|
| `checkbox_vacio.png` | 21×17 | Detectar diarios sin procesar en Sector A |
| `btn_registrar_menu.png` | 148×32 | Botón "Registrar" en menú de AX |
| `btn_registrar_confirm.png` | ~? | Botón de confirmación de registro |
| `Error_Registro.png` | ~? | Pop-up de error de AX |
| `msg_exito_asiento_1.png` | ~? | Pop-up de éxito (cierra con ESC+Enter) |
| `Avanzar_Abajo.png` | 16×15 | Flecha de scroll hacia abajo |
| `Formularios_Abiertos.png` | ~? | Detección de formularios abiertos (seguridad) |
| `btn_cerrar_info.png` | ~? | Botón cerrar (fallback) |
| `check_usuario_marcado.png` | 12×12 | Checkbox marcado (NO usado en filtros) |
| `check_usuario_desmarcado.png` | 211×19 | Fila usuario sin marcar (NO usado) |

---

## Flujo de Scroll

```
Sector A → ¿checkbox_vacio.png?
  ├─ Sí → procesa
  └─ No → intento 1/3:
           → Busca Avanzar_Abajo.png en Sector C (0.7)
           → ¿No? Clic + rueda mouse (-10)
           → ¿Sí? 3 clics en el botón
           → Vuelve a Sector A → ¿checkbox_vacio.png?
           → ¿No? intento 2/3... hasta 3/3
           → ¿Tras 3 intentos sin checkboxes? → FIN
```

---

## Versionado

```
Pre-alpha (v-00.xx.xx)
  Auto-bump: patch (+0.00.01) en cada commit vía pre-commit hook
  Minor/Major: manual (python bump_version.py minor|major)
  Si se modifica _version.py manualmente → no auto-bump
```

---

## Historial de la Conversación (cambios realizados)

1. Rutas absolutas con `__file__` en lugar de relativas
2. Región de éxito ampliada a Sector A completo (no 40×40 px)
3. Normalización de IDs OCR (IS00327946iat → 00327946)
4. Validación de Tesseract al inicio
5. Blacklist persistente en `blacklist.json`
6. Cache de posiciones procesadas (evita OCR redundante)
7. Coordenadas OCR externalizadas a `config_sectores.json`
8. Scroll: 5 clics, 4 intentos, fallback a clic+rueda
9. Pop-up éxito: ESC+Enter para cerrar
10. Pop-up error: clic+ESC para cerrar
11. Log estructurado con rotación (5MB, 3 backups)
12. Logs comprimidos (nombres cortos, fecha sin hora duplicada, IDs normalizados)
13. Botón Reiniciar en GUI (resetea contadores, borra blacklist, va al inicio)
14. Auto-bump version por tipo de commit
15. Arquitectura reestructurada a `src/bot_ax/` (modular)
