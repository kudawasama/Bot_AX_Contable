# Bot_AX_Contable — Brief para Agentes

> **LEE esto ANTES de trabajar.** Este brief y el vault son la memoria viva del
> proyecto: qué es, por qué existe, qué cumple, qué está pendiente y qué riesgos tiene.


## ¿Qué es y por qué existe?

**Bot_AX_Contable**: Bot de automatización para Microsoft Dynamics AX que registra diarios contables automáticamente mediante reconocimiento de imágenes (template matching) y OCR (Tesseract).

Antes de tocar código, pregúntate y responde con el contexto del vault
(`1.0-PROPOSITO/1.1-Mapa-Mental-Narrativo.md` y `1.3-Proposito.md`):

- **¿Por qué existe este proyecto?** — qué problema resuelve.
- **¿Para qué sirve?** — qué valor entrega a quien lo usa.
- **¿Qué cumple?** — qué promesas y objetivos debe respetar (no romper).
- **¿Para quién es?** — usuarios y stakeholders (completar con la historia).
- **¿Qué NO es?** — límites y fuera de alcance (lo que el proyecto NO hace).
- **¿Qué NO tocar?** — reglas inamovibles del proyecto.

> Si una casilla está "pendiente de contexto", complétala con la historia real
> (conversaciones, README, decisiones) en una nota protegida de
> `7.0-MANUAL/` (p. ej. `GOBIERNO.md`) — el build jamás la borra y el agente
> la lee en cada actualización.



## Cómo trabajar aquí — dale vida al contexto

Este proyecto se gobierna por su contexto. El agente DEBE:

1. **Leer este brief** y explorar el vault (`.context-map/vault-Bot_AX_Contable/`): propósito (1.0),
   ideas (2.0), riesgos (4.0) y backlog (5.0).
2. **Revisar los riesgos** antes de hacer cambios y **ejecutar los tests** antes de cada commit.
3. **Inspeccionar el código real** — no suponer rutas ni lógica.
4. **Importar la historia del proyecto** (chats y conversaciones con el usuario).
5. **Mantener vivo el contexto**: después de implementar, actualizar el mapa
   (`ctxmap refresh .`) y **verificar el resultado** — el script propone, el
   agente dispone: si quedaron títulos crudos, métricas en este brief, plantillas
   vacías o notas sin alma, corregirlas (notas con alma en `7.0-MANUAL/`).
   El contexto que no se actualiza muere y el siguiente agente queda ciego.

> Comandos exactos, criterios de verificación y metodología para escribir notas
> con alma: `.context-map/contextmap-skill.md`


## Comandos Útiles

```bash
# Actualizar el contexto en 1 paso (scan + build preservando manuales + check)
ctxmap refresh .
```

> Lista completa de comandos y metodología de escritura: `.context-map/contextmap-skill.md`


<!-- PROMPT_CACHE_BOUNDARY: INVARIANT_PREFIX -->

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


## Riesgos Críticos

- ⚠️ **Archivos de alta complejidad: scripts/observer_analyze.py, src/ui/gui_classic.py**
  Zona de alta complejidad: Archivos de alta complejidad (6 total): scripts/observer_analyze.py; src/ui/gui_classic.py; sc
- ⚠️ **Encontré un problema real y lo voy a arreglar con su prueba de regresión. Primer**
  Riesgo: Encontré un problema real y lo voy a arreglar con su prueba de regresión. Primero el diagnóstico exacto:

- logs
- ⚠️ **Entendido y aplicado: solo Bot_AX_Contable. Y me quedo con el hallazgo más impor**
  Riesgo: Entendido y aplicado: solo Bot_AX_Contable. Y me quedo con el hallazgo más importante de la sesión, que resultó 
- ⚠️ **Implemento T1 y T3. Leo el archivo actual para reescribirlo de una vez y sin rie**
  Riesgo: Implemento T1 y T3. Leo el archivo actual para reescribirlo de una vez y sin riesgo de parches parciales:.

## Tareas Pendientes

### 🔧 TODOs del código (deuda técnica)

- 📝 **TODO: L4: Centraliza todos los defaults numéricos para facilitar ajustes.**
  Pendiente: L4: Centraliza todos los defaults numéricos para facilitar ajustes..

Ubicación: `TODO`

## 🧠 Conocimiento Relevante (Second Brain)

> Mundo PKM independiente en `90-CONOCIMIENTO/` (notas `namespace: knowledge`).
> El código y el conocimiento son islas separadas: esto es lo capturado por el usuario.

_Sin páginas todavía. Captura con `ctxmap inbox add "<texto>"` o `ctxmap ingest --url <web>`._

> Consulta con citas: `ctxmap wiki query "<tema>"`.

## 🧮 Eficiencia de Contexto & Presupuesto de Tokens

- **Brief Principal (`CONTEXT.md`)**: `1270` tokens
- **Prefijo Invariante (Prompt Cache)**: `707` tokens deterministas (alta tasa de Cache Hit en Claude 3.7 / Gemini 2.5).
- **Optimización de Ventana**: **>99% de ahorro de tokens** (carga inmediata del mapa narrativo vs. inspección masiva de código).


---

> Este brief fue generado automáticamente por ContextMap IA.
> Última compilación: 2026-10-09 16:47
> Optimizado para Prompt Caching (Claude 3.7 Sonnet, Gemini 2.5 Pro/Flash, GPT-4o).
