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

O editar la línea 12-13 de `config.py`.

## 🎯 Configuración

Antes del primer uso, definir las áreas de la pantalla donde el bot buscará:

```bash
python setup_areas.py
```

Esto abre un selector visual. Define en orden:

1. **Sector A** — Área donde están los checkboxes de los diarios
2. **Sector B** — Área donde está el botón "Registrar"
3. **Sector C (Scroll)** — Área donde está la flecha de scroll

Las coordenadas se guardan en `config_sectores.json`.

También puedes ajustar `ocr_region_offset` en `config_sectores.json` si los IDs de diario no se leen correctamente (offset desde el centro del checkbox hacia la izquierda donde está el texto).

> 💡 Copia `config_sectores.json.default` como plantilla si empiezas desde cero.

## ▶️ Uso

### Interfaz gráfica (recomendado)

```bash
python app_gui.py
```

O directamente desde Windows: doble clic en `Lanzar_Bot.bat`

### Interfaz alternativa (Gemini Engine)

```bash
python bot_ax_registro.py
```

### Sin interfaz gráfica

```bash
python -c "from bot_main import run_bot; run_bot()"
```

### Herramientas de diagnóstico

```bash
python debug_ocr.py      # Captura imágenes para ajustar el OCR
python debug_pantalla.py  # Captura la pantalla completa
python diagnose_vision.py # Verifica patrones de imagen
```

## 🧪 Tests

```bash
# Tests de configuración
python -m pytest tests/test_config.py -v

# Tests de visión (función de normalización de IDs)
python -c "
import re
source = open('vision.py').read()
idx = source.find('import re')
end = source.find('def capturar', idx)
exec(source[idx:end])
# (ejecuta las pruebas inline)
"
```

## 📁 Estructura del proyecto

```
Bot_AX_Contable/
├── app_gui.py                  # Interfaz gráfica principal (Tkinter)
├── bot_ax_registro.py          # Interfaz alternativa (Gemini Engine)
├── bot_main.py                 # Núcleo del bot (ciclo principal)
├── vision.py                   # OCR + reconocimiento de imágenes
├── config.py                   # Configuración y validación
├── logger.py                   # Logging estructurado con rotación
├── setup_areas.py              # Herramienta para definir sectores
├── test_ocr.py                 # Verificación de Tesseract
├── debug_ocr.py                # Debug de coordenadas OCR
├── debug_pantalla.py           # Debug de captura de pantalla
├── diagnose_vision.py          # Verificación de patrones
├── patrones/                   # Imágenes patrón (template matching)
│   ├── checkbox_vacio.png
│   ├── check_usuario_marcado.png
│   ├── btn_registrar_menu.png
│   ├── btn_registrar_confirm.png
│   ├── Error_Registro.png
│   ├── Avanzar_Abajo.png
│   ├── Formularios_Abiertos.png
│   └── ... (otros patrones)
├── config_sectores.json        # Coordenadas de sectores (por máquina)
├── config_sectores.json.default # Plantilla de configuración
├── blacklist.json              # Diarios con error (auto-generado)
├── tests/                      # Tests unitarios
├── logs/                       # Logs y capturas de error
│   └── capturas/               # Capturas de pantalla en errores
├── docs/plans/                 # Planes de implementación
├── requirements.txt
└── README.md
```

## ⚙️ Cómo funciona

1. **Busca checkboxes vacíos** en Sector A mediante template matching
2. **Lee el ID del diario** con OCR (Tesseract) en la posición configurada
3. **Filtra** diarios ya procesados (cache de posición) y en lista negra (errores previos)
4. **Registra** en AX: clic en checkbox → botón "Registrar" → confirmación
5. **Espera resultado** — detecta check marcado (éxito) o cartel de error
6. **Persiste** el resultado en `registro_YYYY-MM-DD.txt` y diarios con error en `blacklist.json`
7. **Repite** hasta no encontrar más diarios

## 🔧 Solución de problemas

| Problema | Causa probable | Solución |
|----------|---------------|----------|
| "Tesseract no encontrado" | Ruta incorrecta | Verificar `TESSERACT_CMD` o variable de entorno |
| "Sectores no definidos" | `config_sectores.json` ausente | Ejecutar `python setup_areas.py` |
| No encuentra checkboxes | Patrones no coinciden o sector mal definido | Verificar `patrones/checkbox_vacio.png` y redefinir Sector A |
| Mismos diarios reintentados | OCR variante (`IS` vs `iS` vs `1S`) | El fix B1 normaliza IDs por núcleo numérico |
| Timeout excesivo (1h) | Región de éxito muy pequeña | El fix B2 usa Sector A completo |
| Bot no arranca | `.bat` no encuentra unidad H: | Verificar conexión Google Drive |

## 📊 Logs

- **`logs/bot_ax.log`** — Log estructurado con rotación (máx 5MB, 3 backups)
- **`registro_YYYY-MM-DD.txt`** — Resumen diario de resultados
- **`blacklist.json`** — IDs normalizados de diarios con error (persistente)
- **`logs/capturas/error_*.png`** — Capturas de pantalla en cada error

## 📜 Historial de cambios

| Fecha | Versión | Cambios |
|-------|---------|---------|
| 2026-06-05 | v2.1 | Rutas absolutas, lista negra normalizada, región éxito ampliada, validación Tesseract, cache de posiciones, blacklist persistente, OCR externalizado, logging estructurado, tests unitarios |
| Anterior | v2.0 | Dos interfaces gráficas, ciclo principal estable |

## 👤 Autor

José Céspedes — Casino Express / Casino Lo Águila
