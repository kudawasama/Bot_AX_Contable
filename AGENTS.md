# Instrucciones para Agentes de IA — Bot_AX_Contable

> ⚠️ **REGLA PRIORITARIA PARA AGENTES DE IA**:
> **LEE el contexto del proyecto ANTES de investigar o modificar cualquier cosa.**
> Este proyecto se gobierna por su contexto: si no lo lees, trabajas a ciegas.
> Última actualización: 2026-10-09

Este `AGENTS.md` define **QUÉ** hacer; el **CÓMO** (comandos exactos y metodología
para escribir las notas con alma) está en
[.context-map/contextmap-skill.md](.context-map/contextmap-skill.md).

> ⚠️ **El bot está en producción y en uso diario.** Asume que el proceso
> `pythonw -m src.ui.gui_classic` puede estar corriendo con Dynamics AX abierto:
> ninguna tarea debe interrumpirlo ni alterar su comportamiento.

---

## 1. Protocolo de Inicio (QUÉ hacer antes de trabajar)

Antes de responder preguntas sobre el proyecto o escribir código, el Agente DEBE:

1. **Leer el Brief Ejecutivo**: [.context-map/CONTEXT.md](.context-map/CONTEXT.md) —
   responde qué es el proyecto, por qué existe, qué cumple, sus riesgos y tareas
   pendientes.
2. **Explorar el Vault**: `.context-map/vault-Bot_AX_Contable/`:
   - `1.0-PROPOSITO/` (dominio y propósito)
   - `2.0-IDEAS/` (pendientes, futuras, completas)
   - `4.0-RIESGOS/` (deuda técnica y zonas de complejidad)
   - `5.0-BACKLOG/` (`5.1-Tareas.md`)
3. **Leer el plan vivo**: [docs/plans/plan-implementacion-mejoras.md](docs/plans/plan-implementacion-mejoras.md)
   (correcciones C-1…C-9, riesgos R-1…R-6, fases 0–7) y su insumo
   `docs/plans/plan-mejora-profesional.md`.
4. **Importar la historia del proyecto**: las conversaciones con el usuario también
   son contexto (comandos en la skill de ContextMap). Si el usuario comparte un
   chat, impórtalo ANTES de responder.
5. **No Suponer Lógica**: inspecciona el código fuente real antes de diagnosticar
   o cambiar. Antes de proponer cambios, responde las 3 preguntas del alma:
   *¿Por qué existe este proyecto? ¿Para qué sirve? ¿Qué cumple?*

---

## 2. Estándares de Desarrollo (QUÉ respetar)

* **Idioma**: explicaciones, comentarios y docstrings en **Español Técnico Profesional**.
* **Clean Architecture**: Principio de Responsabilidad Única (SRP) y convención modular `modulo/submodulo/archivo.py`.
* **Tipado Fuerte**: Type Hinting explícito en Python (`List`, `Dict`, `Tuple`, `Optional`).
* **Docstrings**: documentación formal en funciones, clases y módulos.
* **Raíz Limpia**: no crear archivos sueltos en la raíz (`PLAN.md`, `NOTES.txt`).
  Los planes van en `docs/plans/`, los scripts auxiliares en `scripts/`.
* **Reglas inmutables del bot**: ningún refactor puede alterar la lógica descrita en
  [docs/manual_proceso_bot.md](docs/manual_proceso_bot.md): foco dirigido no
  destructivo, barrera del último marcado, caché de posiciones, limpieza tras
  scroll, lista negra y confianza 0.85 en los checkboxes.

---

## 3. Protocolo de Verificación Obligatorio (antes de cada commit)

```bash
# 1. Suite de pruebas unitarias (debe pasar 100% → hoy 18/18)
python -m pytest

# 2. Contexto al día: scan + build (preservando manuales) + check de readiness
ctxmap refresh .
```

> ⚠️ **Intérprete**: usa el Python del bot (**3.12**). Si `python` no resuelve a
> 3.12 en tu shell, invócalo explícito:
> `"%LOCALAPPDATA%\Programs\Python\Python312\python.exe" -m pytest`

> ⚠️ **Con el bot corriendo**: los dobles inertes de `pyautogui` y `pytesseract`
> viven en `tests/conftest.py`, así que la suite nunca mueve el mouse ni captura la
> pantalla. No ejecutes `scripts/debug_*.py` ni `scripts/diagnose_vision.py`
> mientras el bot está en ejecución (sí toman control de la pantalla).

---

## 4. Protocolo de Cambio Seguro (proyecto en producción)

1. Trabajar en una rama (`feat/…`, `fix/…`, `docs/…`); no commitear directo en `main`.
2. Cambios en `src/core/engine.py`, `src/services/vision.py` o la calibración
   (`config_sectores.json`): verificar en el entorno real **antes** de desplegar y
   dejar constancia en el `CHANGELOG.md`.
3. Todo cambio se respalda con **commit + push** (Conventional Commits en español).
4. Al terminar, `ctxmap refresh .` para que el mapa refleje el trabajo
   (nodos CAMBIO / CORRECCION / IDEA).

---

<!-- CONTEXTMAP:BEGIN -->

## 🧰 Stack del proyecto (dato real)

- **Lenguaje(s)**: Python 3.12 (probado con 3.12.10; 3.11+ compatible)
- **Framework(s)**: Tkinter (GUI), PyAutoGUI (RPA / template matching), Tesseract vía `pytesseract` (OCR)
- **Package manager**: pip — `requirements.txt` (producción) y `requirements-dev.txt` (pytest, ruff, flake8)
- **Entrypoint(s)**: `python -m src.ui.gui_classic` (GUI principal), `python -m src.ui.gui_gemini` (GUI alternativa), `Lanzar_Bot.bat` / `Lanzar_Bot_Registro.bat`
- **Estructura**: `src/` (core, services, ui), `tests/`, `scripts/`, `docs/`, `patrones/`
- **Tests**: `python -m pytest` (18 pruebas: `tests/test_config.py`, `tests/test_vision.py`)
- **Build**: no aplica (aplicación de escritorio; sin empaquetado)

## ✅ Verificación obligatoria

```bash
python -m pytest          # 18/18 en verde
ctxmap refresh .          # scan + build (preservando manuales) + check
```

> Detalle de comandos y metodología de escritura: `.context-map/contextmap-skill.md`

> ℹ️ Nota de mantenimiento: este bloque lo genera `ctxmap adapt`, pero fue corregido
> a mano (antes decía "No detectado" y `echo 'No test runner detectado'`). Si
> `ctxmap adapt` lo regenera, **conservar estos comandos reales**.

<!-- CONTEXTMAP:END -->

---

## 5. Mantén Vivo el Contexto (QUÉ hacer al terminar)

El contexto es la **memoria viva del proyecto**:

1. Después de implementar, actualiza el mapa (`ctxmap refresh .`) para que refleje tu
   trabajo (nodos CAMBIO / CORRECCION / IDEA).
2. Al terminar una sesión de trabajo, importa la conversación (`import-sessions`,
   `import-antigravity`, `import-chat`) para que las decisiones y porqués queden
   registrados.
3. Un contexto que no se actualiza muere: el siguiente agente queda ciego y el
   proyecto pierde su historia.

> Comandos exactos: `.context-map/contextmap-skill.md`.

---

## 6. Convención de Commits

* Usar **Conventional Commits** en español (ej. `feat: ...`, `fix: ...`, `refactor: ...`, `docs: ...`).
* El hook `.githooks/pre-commit` incrementa la versión de `src/core/version.py`
  automáticamente (minor si el commit añade o elimina archivos, patch si solo
  modifica). Para un bump manual determinista: editar `version.py` y dejarlo staged.
