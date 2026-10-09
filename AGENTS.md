# Instrucciones para Agentes de IA — Bot_AX_Contable

> ⚠️ **REGLA PRIORITARIA PARA AGENTES DE IA**:
> Lee este documento antes de realizar cualquier investigación o modificación en el repositorio.
> Última actualización: 2026-07-31 15:42

Este proyecto utiliza **ContextMap** para gobernanza de contexto, mapas conceptuales y trazabilidad técnica. Cualquier agente de Inteligencia Artificial (Antigravity, Cursor, Claude, Hermes, Copilot, Windsurf, etc.) debe seguir estas instrucciones obligatoriamente.

---

## 1. Protocolo de Inicio (Ponerse en Contexto)

Antes de responder preguntas sobre el proyecto o escribir código, el Agente DEBE:

1. **Leer el Brief Ejecutivo**:
   Consultar [.context-map/CONTEXT.md](file:///.context-map/CONTEXT.md) para entender el resumen ejecutivo, métricas, riesgos críticos y tareas pendientes.
2. **Explorar el Vault Jerárquico**:
   Inspeccionar `.context-map/vault/` o `.context-map/vault-Bot_AX_Contable/`:
   - `1.0-PROPOSITO/` (Dominio del proyecto y README)
   - `2.0-IDEAS/` (`2.1-Ideas-Pendientes`, `2.2-Ideas-Futuras`, `2.3-Ideas-Completas`)
   - `4.0-RIESGOS/` (Deuda técnica y zonas de complejidad)
   - `5.0-BACKLOG/` (`5.1-Tareas.md`)
3. **No Suponer Lógica**:
   Inspeccionar los archivos de código fuente antes de formular diagnósticos o proponer cambios.

---

## 2. Estándares de Desarrollo y Arquitectura

* **Idioma**: Todas las explicaciones, comentarios y docstrings deben estar en **Español Técnico Profesional**.
* **Clean Architecture**: Adherirse al Principio de Responsabilidad Única (SRP) y a la convención modular `modulo/submodulo/archivo.py`.
* **Tipado Fuerte**: Uso explícito de Type Hinting en Python (`List`, `Dict`, `Tuple`, `Optional`).
* **Docstrings**: Documentación formal en funciones, clases y módulos.
* **Raíz Limpia**: No crear archivos estáticos de notas en la raíz (`PLAN.md`, `NOTES.txt`). Mantener únicamente los archivos estándar del repositorio.

---

## 3. Protocolo de Verificación Obligatorio

Después de realizar modificaciones o implementar nuevas funciones, el Agente DEBE ejecutar los siguientes comandos de verificación:

```bash
# 1. Ejecutar suite de pruebas unitarias (debe pasar 100%)
python -m pytest

# 2. Escanear cambios en el mapa de contexto
python -m context_map.cli scan .

# 3. Reconstruir el Vault de Obsidian y el Brief ejecutivo
python -m context_map.cli build --clean --brief

# 4. Auditar el score de readiness
python -m context_map.cli check .
```

---

## 4. Convención de Commits

* Usar **Conventional Commits** en español (ej. `feat: ...`, `fix: ...`, `refactor: ...`, `docs: ...`).


<!-- CONTEXTMAP:BEGIN -->

# Instrucciones para Agentes de IA — Bot_AX_Contable

> ⚠️ **REGLA PRIORITARIA PARA AGENTES DE IA**:
> **LEE el contexto del proyecto ANTES de investigar o modificar cualquier cosa.**
> Este proyecto se gobierna por su contexto: si no lo lees, trabajas a ciegas.
> Última actualización: 2026-08-11 17:27
> ⚡ Generado automáticamente por **ContextMap** — adaptado al stack real del proyecto.

Este `AGENTS.md` define **QUÉ** hacer; el **CÓMO** (comandos exactos y metodología
para escribir las notas con alma) está en
**[.context-map/contextmap-skill.md](file:///.context-map/contextmap-skill.md)**.

---

## 1. Protocolo de Inicio (QUÉ hacer antes de trabajar)

1. **Leer el Brief Ejecutivo**: `.context-map/CONTEXT.md` — responde qué es el
   proyecto, por qué existe, qué cumple, sus riesgos y tareas pendientes.
2. **Explorar el Vault**: `.context-map/vault/` o `.context-map/vault-{project_name}/`:
   propósito (1.0), ideas (2.0), riesgos (4.0) y backlog (5.0).
3. **Importar la historia del proyecto**: las conversaciones con el usuario también
   son contexto (comandos en la skill). Si el usuario comparte un chat, impórtalo
   ANTES de responder.
4. **Responder las 3 preguntas del alma** antes de proponer cambios:
   ¿Por qué existe este proyecto? ¿Para qué sirve? ¿Qué cumple?
5. **No Suponer Lógica**: inspecciona el código fuente antes de diagnosticar o cambiar.

---

## 2. Estándares de Desarrollo (QUÉ respetar)

* **Idioma**: explicaciones, comentarios y docstrings en **Español Técnico Profesional**.
* **Clean Architecture**: Principio de Responsabilidad Única (SRP) y convención modular `modulo/submodulo/archivo.py`.
* **Tipado Fuerte**: Type Hinting explícito en Python (`List`, `Dict`, `Tuple`, `Optional`).
* **Docstrings**: documentación formal en funciones, clases y módulos.
* **Raíz Limpia**: no crear archivos sueltos en la raíz (`PLAN.md`, `NOTES.txt`).

---

## 🧰 Stack detectado por ContextMap (dato del proyecto)

- **Lenguaje(s)**: No detectado
- **Framework(s)**: No detectado
- **Package manager**: No detectado
- **Entrypoint(s)**: `No detectado`
- **Estructura**: src, tests, docs, scripts
- **Tests**: `echo 'No test runner detectado'`
- **Build**: `echo 'No build command detectado'`

## ✅ Verificación obligatoria (antes de cada commit)

```bash
echo 'No test runner detectado'
ctxmap refresh .          # contexto al día: scan + build (preservando manuales) + check
```

> Detalle de comandos y metodología de escritura: `.context-map/contextmap-skill.md`

---

## 3. Mantén Vivo el Contexto (QUÉ hacer al terminar)

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

## 4. Convención de Commits

* Usar **Conventional Commits** en español (ej. `feat: ...`, `fix: ...`, `refactor: ...`, `docs: ...`).

<!-- CONTEXTMAP:END -->
