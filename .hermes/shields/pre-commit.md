# Escudo Pre-Commit — Bot_AX_Contable

## Verificaciones obligatorias

- [ ] Tests pasan: `python -m pytest` (18/18; usar el Python 3.12 del bot)
- [ ] Sin secretos en el diff (api_key, password, .env)
- [ ] Sin archivos huérfanos en la raíz (PLAN.md, NOTAS.txt)
- [ ] ContextMap actualizado: `ctxmap refresh .`
- [ ] Conventional Commits en español
- [ ] Si se tocó `config_sectores.json` o `src/core/engine.py`, se verificó en el
      entorno real antes de commitear (proyecto en producción)
