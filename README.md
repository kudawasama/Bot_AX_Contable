# Bot AX Contable

Bot de automatización para **Microsoft Dynamics AX** que registra diarios contables automáticamente mediante reconocimiento de imágenes (template matching) y OCR (Tesseract).

---

## 🚀 Requisitos

- **Python 3.12** (o 3.11+)
- **Tesseract OCR** — [Descargar desde UB-Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)
- Dependencias Python: `pip install -r requirements.txt`

## 📦 Instalación

```bash
# 1. Clonar o copiar el proyecto
cd ruta/al/proyecto

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Verificar Tesseract OCR
python test_ocr.py

# 4. Verificar que los patrones de imagen se detectan en pantalla
python diagnose_vision.py
```

Si Tesseract no está en la ruta por defecto, configurar la variable de entorno:

```bash
set TESSERACT_CMD=C:\Ruta\a\tesseract.exe
```

## 🎯 Configuración inicial

Antes del primer uso, definir las áreas de la pantalla donde el bot buscará:

```bash
python setup_areas.py
```

Esto abre un selector visual. Define en orden:

1. **Sector A** — Área donde están los checkboxes de los diarios
2. **Sector B** — Área donde está el botón "Registrar"
3. **Sector C (Scroll)** — Área donde está la flecha de scroll

Las coordenadas se guardan en `config_sectores.json`.

Ajustar `ocr_region_offset` si los IDs de diario no se leen correctamente (offset desde el centro del checkbox hacia el texto).

> 💡 Copia `config_sectores.json.default` como plantilla si empiezas desde cero.

## ▶️ Uso

### Interfaz gráfica (recomendado)

```bash
python app_gui.py
```

O doble clic en `Lanzar_Bot.bat`

### Panel ACTIONS

| Botón | Función |
|-------|---------|
| Adjust Regions | Abre selector de áreas |
| View Snapshots | Abre carpeta de capturas de error |
| Export Logs | Abre registro del día (`registro_YYYY-MM-DD.txt`) |
| Clear Errors | Resetea contadores y borra `blacklist.json` |
| **Reiniciar** 🆕 | Resetea contadores + borra blacklist + envía **Home** a AX |

### Controles

| Control | Función |
|---------|---------|
| **Start Engine** | Inicia el ciclo de registro |
| **Stop Engine** | Detiene el proceso (vía `stop_event`) |
| **Pause** | Pausa/reanuda el ciclo |

## 📋 Formato de logs

```
[14:55:21] . No hay casillas nuevas. Buscando botón de scroll (1/2)...
[14:55:21] . Botón de scroll encontrado. Presionando 5 veces...
[15:07:55] . [2026-06-12] [INFO] Click: Menu @ (1284,104)
[15:07:55] . [2026-06-12] [INFO] Click: Confirmar @ (1154,108)
[15:07:58] . [2026-06-12] [INFO] Esperando resultado (timeout: 60min)...
[15:08:11] . [2026-06-12] [INFO] -> EXITO! (pop-up confirmado)
[15:08:12] + [RESULT:OK] -> Registro de 00328313 completado.
```

- Nombres cortos: `Menu`, `Confirmar`, `Scroll`, `Exito-Ventana`
- IDs normalizados: solo números (`00328313` en vez de `IS00328313Diat`)
- Fecha sin hora duplicada (la hora la pone la GUI)

## ⚙️ Cómo funciona

1. **Busca checkboxes vacíos** en Sector A (`checkbox_vacio.png`, confianza 0.9)
2. **Lee el ID del diario** con OCR (Tesseract) con offset configurable
3. **Filtra**: saltar posiciones ya procesadas y diarios en lista negra (IDs normalizados)
4. **Registra** en AX: clic en checkbox → botón "Registrar" → confirmación
5. **Espera resultado** hasta 60 min (detecta pop-up `msg_exito_asiento_1.png` o `Error_Registro.png`)
6. Al detectar el pop-up de éxito: **1 ESC** para cerrarlo
7. Al detectar error: clic + ESC para cerrar pop-up de error
8. **Persiste** resultado en `registro_YYYY-MM-DD.txt` y errores en `blacklist.json`
9. **Repite** hasta no encontrar más diarios

### Scroll

- Busca `Avanzar_Abajo.png` (16×15 px) en Sector Scroll (confianza 0.7)
- Si no lo encuentra: busca en pantalla completa (confianza 0.65)
- Si lo encuentra: **5 clics**, máximo **2 intentos**
- Fallback: clic + rueda del mouse si no se encuentra el botón

## 🔧 Solución de problemas

| Problema | Causa probable | Solución |
|----------|---------------|----------|
| "Tesseract no encontrado" | Ruta incorrecta | Verificar `TESSERACT_CMD` o variable de entorno |
| "Sectores no definidos" | `config_sectores.json` ausente | Ejecutar `python setup_areas.py` |
| No encuentra checkboxes | Confianza muy alta o sector mal definido | Redefinir Sector A con `setup_areas.py` |
| Mismos diarios reintentados | OCR variante (`IS` vs `iS` vs `1S`) | El bot normaliza IDs por núcleo numérico |
| Timeout excesivo (1h) | Pop-up no detectado | Verificar `msg_exito_asiento_1.png` en `patrones/` |
| Bot no arranca | `.bat` no encuentra unidad H: | Verificar conexión Google Drive |
| Error `Errno 22` en registro | Ruta relativa o archivo bloqueado | El bot ya usa ruta absoluta + try/except |

## 📁 Estructura del proyecto

```
Bot_AX_Contable/
├── app_gui.py                  # Interfaz gráfica principal (Tkinter)
├── bot_ax_registro.py          # Interfaz alternativa
├── bot_main.py                 # Núcleo del bot (ciclo principal)
├── vision.py                   # OCR + reconocimiento de imágenes
├── config.py                   # Configuración y validación
├── logger.py                   # Logging estructurado con rotación
├── _version.py                 # Versión del proyecto (auto-bump)
├── bump_version.py             # Script para incrementar versión
├── setup_areas.py              # Herramienta para definir sectores
├── test_ocr.py                 # Verificación de Tesseract
├── debug_ocr.py                # Debug de coordenadas OCR
├── debug_pantalla.py           # Debug de captura de pantalla
├── diagnose_vision.py          # Verificación de patrones
├── patrones/                   # Imágenes patrón (14 archivos)
│   ├── checkbox_vacio.png      # Checkbox sin marcar (21×17)
│   ├── check_usuario_marcado.png
│   ├── check_usuario_desmarcado.png  # Fila usuario sin marcar (211×19)
│   ├── btn_registrar_menu.png  # Botón "Registrar" en menú
│   ├── btn_registrar_confirm.png     # Botón confirmación
│   ├── Error_Registro.png      # Pop-up de error
│   ├── msg_exito_asiento_1.png # Pop-up de éxito
│   ├── btn_cerrar_info.png     # Botón cerrar info
│   ├── Avanzar_Abajo.png       # Flecha scroll abajo (16×15)
│   └── ...
├── config_sectores.json        # Coordenadas de sectores
├── config_sectores.json.default
├── blacklist.json              # Diarios con error (auto-generado)
├── .githooks/pre-commit        # Auto-bump version
├── tests/                      # Tests unitarios
├── logs/                       # Logs y capturas de error
│   └── capturas/               # Capturas de pantalla en errores
├── docs/plans/
├── requirements.txt
└── README.md
```

## 🔢 Versionado

El pre-commit hook (`bump_version.py`) auto-incrementa la versión según el tipo de commit:

| Commit comienza con | Bump | Ejemplo |
|--------------------|------|---------|
| `fix:` | patch | `v-00.01.39 → v-00.01.40` |
| `feat:` | minor | `v-00.01.39 → v-00.02.00` |
| `refactor:` | minor | `v-00.01.39 → v-00.02.00` |
| `BREAKING:` | major | `v-00.01.39 → v-01.00.00` |
| default | patch | `v-00.01.39 → v-00.01.40` |

Para bumpear manualmente: `python bump_version.py [patch|minor|major]`

## 🧪 Tests

```bash
# Tests de configuración
python -m pytest tests/test_config.py -v

# Tests de normalización de IDs (inline)
python -c "
from vision import normalizar_id_diario
tests = [('IS00327946iat','00327946'),('iS00327946Diai','00327946')]
for inp, exp in tests:
    assert normalizar_id_diario(inp) == exp, f'{inp} -> {exp}'
print('✅ Todos los tests pasaron')
"
```

## 📊 Logs

- **`logs/bot_ax.log`** — Log estructurado con rotación (máx 5MB, 3 backups)
- **`registro_YYYY-MM-DD.txt`** — Resumen diario de resultados
- **`blacklist.json`** — IDs normalizados de diarios con error (persistente)
- **`logs/capturas/error_*.png`** — Capturas de pantalla en cada error (solo 1 por tipo)

## 📜 Historial de cambios

| Fecha | Versión | Cambios |
|-------|---------|---------|
| 2026-06-12 | v-00.01.40+ | Auto-bump por commit type, log comprimido, botón Reiniciar, scroll 5×2, pop-up éxito/error con ESC, error popup clic, versionado corregido |
| 2026-06-05 | v-00.01.39 | Rutas absolutas, blacklist normalizada, región éxito ampliada, validación Tesseract, cache posiciones, blacklist persistente, OCR externalizado, logging estructurado, tests unitarios, README |
| Anterior | v2.0 | Versión original con dos interfaces gráficas |

## 👤 Autor

José Céspedes — Casino Express / Casino Lo Águila
