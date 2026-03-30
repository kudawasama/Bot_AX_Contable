import os
import sys
import json
import argparse
from pathlib import Path
import subprocess

REPO_ROOT = Path(__file__).resolve().parents[1]


def discover_subagents():
    subagents = {}
    sa_dir = REPO_ROOT / 'agents' / 'subagents'
    if not sa_dir.exists():
        return subagents
    for p in sa_dir.iterdir():
        if p.suffix.lower() in ('.md', '.txt'):
            name = p.stem
            subagents[name.lower()] = p
    return subagents


def explore_repo(max_files=50):
    files = []
    for root, dirs, filenames in os.walk(REPO_ROOT):
        # skip __pycache__
        dirs[:] = [d for d in dirs if d != '__pycache__']
        for f in filenames:
            path = Path(root) / f
            files.append(str(path.relative_to(REPO_ROOT)))
            if len(files) >= max_files:
                return {'files': files, 'summary': f'Found {len(files)} files (truncated)'}
    return {'files': files, 'summary': f'Found {len(files)} files'}


def implement_change(instructions, dry_run=True):
    # Simple simulation: propose a patch that adds a file under agents/output/
    out_dir = REPO_ROOT / 'agents' / 'output'
    target = out_dir / 'propuesta.txt'
    content = f"Propuesta generada para: {instructions}\n\n(Esto es un dry-run: {'sí' if dry_run else 'no'})\n"
    patch = {'target': str(target.relative_to(REPO_ROOT)), 'content': content}
    if not dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding='utf-8')
    return patch


def verify_artifacts(files):
    results = []
    for f in files:
        if f.lower().endswith('.py'):
            path = REPO_ROOT / f
            try:
                src = path.read_text(encoding='utf-8')
                compile(src, str(path), 'exec')
                results.append({'file': f, 'status': 'pass'})
            except Exception as e:
                results.append({'file': f, 'status': 'fail', 'error': repr(e)})
        else:
            results.append({'file': f, 'status': 'skipped'})
    summary = {'pass': sum(1 for r in results if r['status']=='pass'), 'fail': sum(1 for r in results if r['status']=='fail')}
    return {'results': results, 'summary': summary}


def run_tests_and_lint():
    res = {'pytest': None, 'linter': None}
    # Run pytest if available
    try:
        p = subprocess.run([sys.executable, '-m', 'pytest', '-q', '--maxfail=1'], cwd=REPO_ROOT, capture_output=True, text=True, timeout=120)
        res['pytest'] = {'returncode': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}
    except FileNotFoundError:
        res['pytest'] = {'error': 'pytest not installed'}
    except subprocess.TimeoutExpired:
        res['pytest'] = {'error': 'pytest timeout'}

    # Run ruff (if available) as linter, else try flake8
    try:
        p = subprocess.run([sys.executable, '-m', 'ruff', 'check', '.'], cwd=REPO_ROOT, capture_output=True, text=True, timeout=60)
        res['linter'] = {'tool': 'ruff', 'returncode': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}
    except Exception:
        try:
            p = subprocess.run([sys.executable, '-m', 'flake8', '.'], cwd=REPO_ROOT, capture_output=True, text=True, timeout=60)
            res['linter'] = {'tool': 'flake8', 'returncode': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}
        except Exception:
            res['linter'] = {'error': 'no linter installed'}
    return res


def orchestrate(task, dry_run=True):
    discover_subagents()
    plan = []

    # Step 1: Explore
    ctx = explore_repo()
    plan.append({'id': 1, 'subagent': 'explore', 'result': ctx})

    # Step 2: Implement (simulation)
    impl = implement_change(task or 'Tarea genérica', dry_run=dry_run)
    plan.append({'id': 2, 'subagent': 'implement', 'result': impl})

    # Step 3: Verify (run basic checks on first N python files)
    files_to_check = ctx.get('files', [])[:20]
    ver = verify_artifacts(files_to_check)
    plan.append({'id': 3, 'subagent': 'verify', 'result': ver})

    # Step 4: Run tests and linter if available
    test_results = run_tests_and_lint()
    plan.append({'id': 4, 'subagent': 'test-runner', 'result': test_results})

    deliverable = {
        'summary': f'Orquestación completada para: {task}',
        'steps': plan,
        'deliverable': {'patch': impl if dry_run else {'applied': True, **impl}}
    }
    return deliverable


def main():
    parser = argparse.ArgumentParser(description='Runner para el Agente Orquestador (modo local, simulador)')
    parser.add_argument('--task', '-t', help='Descripción de la tarea a orquestar', default='Analizar repo y proponer cambio')
    parser.add_argument('--dry-run', action='store_true', help='No aplicar cambios (por defecto: dry-run)')
    parser.add_argument('--apply', action='store_true', help='Aplicar cambios (unsafe)')
    args = parser.parse_args()

    dry = True if args.dry_run and not args.apply else (not args.apply)
    if args.apply:
        confirm = input('Confirma aplicar cambios en el repo? (sí/no): ')
        if confirm.strip().lower() not in ('si','sí','s','y','yes'):
            print('Cancelado por el usuario.')
            sys.exit(1)
        dry = False

    out = orchestrate(args.task, dry_run=dry)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
