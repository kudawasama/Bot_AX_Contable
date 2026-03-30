# Agents helper

Uso rápido:

- Ejecutar en modo dry-run (simulación):

```bash
python agents/run_orquestador.py --task "Implementar X" --dry-run
```

- Para aplicar cambios (pide confirmación):

```bash
python agents/run_orquestador.py --task "Implementar X" --apply
```

Notas:

- El script es un simulador que usa los archivos en `agents/subagents` para identificar subagentes disponibles.
- `Implement` solo genera una propuesta en `agents/output/propuesta.txt` si se usa `--apply`.
