# Bot_AX_Contable — Brief para Agentes

> **LEE esto ANTES de trabajar.** Este brief y el vault son la memoria viva del
> proyecto: qué es, por qué existe, qué cumple, qué está pendiente y qué riesgos tiene.


## ¿Qué es y por qué existe?

**Bot_AX_Contable**: Bot de automatización para Microsoft Dynamics AX que registra diarios contables automáticamente mediante reconocimiento de imágenes (template matching) y OCR (Tesseract).

Antes de tocar código, pregúntate y responde con el contexto del vault
(`1.0-PROPOSITO/1.1-Mapa-Mental-Narrativo.md` y `1.3-Proposito.md`):

- **¿Por qué existe este proyecto?** — qué problema resuelve. […]

## Resumen Ejecutivo

**Proyecto**: Bot_AX_Contable
**Nodos totales**: 77
**Distribución**: BASE: 11, FUTURO: 3, CORRECCION: 25, CAMBIO: 7, IDEA: 27, RIESGO: 4
**Readiness**: 75/100


## Estado del Proyecto

- **Ideas**: 27 (features, conceptos)
- **Bases**: 11 (fundamentos)
- **Riesgos**: 4 (problemas potenciales)
- **Cambios**: 7 (modificaciones)
- **Pendientes**: 3 (tareas por hacer)
- **Correcciones**: 25 (bugs/fixes)


## Estado del Contexto

✅ Contexto al día (último build).


## ⚠️ Riesgos

- Archivos de alta complejidad: scripts/observer_analyze.py, src/ui/gui_cl…
- Encontré un problema real y lo voy a arreglar con su prueba de regresión…
- Entendido y aplicado: solo Bot_AX_Contable. Y me quedo con el hallazgo m…
_(+1 más en `4.0-RIESGOS/`)_

## 📝 Pendientes

- TODO: L4: Centraliza todos los defaults numéricos para facilitar ajustes…
- TODO: L258: event_log("scroll_performed", intento=intentos_scroll, metod…
- TODO: L273: event_log("scroll_performed", intento=intentos_scroll, metod…

## 🔎 Ampliar contexto

- `ctxmap search "<tema>"` / tool MCP `context_search` → pasajes de nodos y
  notas con citas (sin cargar ficheros completos).
- Al volver a una sesión: `context_diff(since=<digest>)` → **solo lo que cambió**
  (evita releer el brief si nada cambió).
- Pendientes: `7.0-MANUAL/BACKLOG.md` · historia: `7.0-MANUAL/Diario/` · lecciones: `8.0-KNOWLEDGE/`.
- Salud: `ctxmap check .` · peso: `ctxmap doctor --sizes` · vault: `.context-map/vault-*/`.

---

> Este brief fue generado automáticamente por ContextMap IA.
> Última compilación: 2026-10-09 16:47
> Optimizado para Prompt Caching (Claude 3.7 Sonnet, Gemini 2.5 Pro/Flash, GPT-4o).
