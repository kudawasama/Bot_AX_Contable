---
type: riesgo
status: activo
created: 2026-10-09T16:37:46
project: "Bot_AX_Contable"
tags: ["riesgo", "class:chore"]
source: "scanner"
---

# ⚠️ Archivos de alta complejidad: scripts/observer_analyze.py, src/ui/gui_classic.py, scripts/chequeo_salud.py

> #riesgo #activo #UI

Zona de alta complejidad: Archivos de alta complejidad (6 total): scripts/observer_analyze.py; src/ui/gui_classic.py; scripts/chequeo_salud.py.

## 🧠 Contexto Narrativo con Alma

### ⚠️ 1. ¿Qué RIESGO técnico es?
Riesgo técnico o zona de alta complejidad referente a 'Archivos de alta complejidad: scripts/observer_analyze.py, src/ui/gui_classic.py, scripts/chequeo_salud.py'.

### 📍 2. ¿Dónde se ubica el problema?
Detectado en el módulo/componente vía `scanner`.

### 💥 3. ¿Qué IMPACTO tiene si se ignora?
Incrementa la probabilidad de desacoplamientos o fallos al refactorizar. Zona de alta complejidad: Archivos de alta complejidad (6 total): scripts/observer_analyze.py; src/ui/gui_classic.py; scripts/chequeo_salud.py.

### 🛡️ 4. ¿Cómo MITIGAR este riesgo?
1. Modularizar el componente reduciendo el número de líneas/responsabilidades.
2. Incrementar la cobertura de pruebas unitarias antes de modificarlo.
3. Aislar las funciones públicas mediante interfaces bien definidas.

### 📊 5. MATRIZ DE GRAVEDAD Y MITIGACIÓN

| ⚠️ Nivel de Gravedad | 🛡️ Estrategia de Mitigación |
| :--- | :--- |
| **ALTO / CRÍTICO** | Aplicar Refactoring paso a paso y agregar tests unitarios preventivos. |
| **MEDIO** | Documentar docstrings y aislar la lógica compleja en submódulos. |

## 📋 Evidencia

- Archivo: scripts/observer_analyze.py
- Archivo: src/ui/gui_classic.py
- Archivo: scripts/chequeo_salud.py

## 🔗 Conexiones


---
[[4.0-RIESGOS/4.0-RIESGOS|⬅ Volver a 4.0 Riesgos]]
