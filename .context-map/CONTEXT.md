# Bot_AX_Contable — Brief para Agentes

> **LEE esto ANTES de trabajar.** Este brief y el vault son la memoria viva del
> proyecto: qué es, por qué existe, qué cumple, qué está pendiente y qué riesgos tiene.
> Última actualización: 2026-08-12 08:45


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



## Resumen Ejecutivo

**Proyecto**: Bot_AX_Contable
**Nodos totales**: 61
**Distribución**: BASE: 4, FUTURO: 3, CORRECCION: 25, CAMBIO: 7, IDEA: 21, RIESGO: 1
**Readiness**: 50/100


## Estado del Proyecto

- **Ideas**: 21 (features, conceptos)
- **Bases**: 4 (fundamentos)
- **Riesgos**: 1 (problemas potenciales)
- **Cambios**: 7 (modificaciones)
- **Pendientes**: 3 (tareas por hacer)
- **Correcciones**: 25 (bugs/fixes)


## Estado del Contexto

✅ Contexto al día (último build).


## Riesgos Críticos

- ⚠️ **Archivos de alta complejidad: scripts/observer_analyze.py, src/ui/gui_classic.py**
  Zona de alta complejidad: Archivos de alta complejidad (5 total): scripts/observer_analyze.py; src/ui/gui_classic.py; sr

## Tareas Pendientes

### 🔧 TODOs del código (deuda técnica)

- 📝 **TODO: L4: Centraliza todos los defaults numéricos para facilitar ajustes.**
  Pendiente: L4: Centraliza todos los defaults numéricos para facilitar ajustes..

Ubicación: `TODO`
- 📝 **TODO: L258: event_log("scroll_performed", intento=intentos_scroll, metodo="boton**
  Pendiente: L258: event_log("scroll_performed", intento=intentos_scroll, metodo="boton").

Ubicación: `TODO`
- 📝 **TODO: L273: event_log("scroll_performed", intento=intentos_scroll, metodo="click**
  Pendiente: L273: event_log("scroll_performed", intento=intentos_scroll, metodo="click").

Ubicación: `TODO`

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


---

> Este brief fue generado automáticamente por Context Map.
> Actualízalo ejecutando `ctxmap build --brief`.
