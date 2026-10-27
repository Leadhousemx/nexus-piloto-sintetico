"""Control de políticas del piloto. Sólo examina metadatos de GitHub.

Ejecución autorizada: desde workflow_run usando código confiable de main.
No descarga, importa ni ejecuta archivos procedentes del PR.
No revisa semántica ni autoriza merge, despliegue o DONE.
"""
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE = 'https://api.github.com'
CI_WORKFLOW_FILE = 'piloto-ci.yml'
GATE_NAME = 'Piloto / Politicas'
ALLOWED = {'calculadora.py', 'PILOTO.md'}


def path_allowed(name):
    return name in ALLOWED or (name.startswith('tests/') and name.endswith('.py')
                               and name.count('/') == 1)


def evaluate(run, pr, files, expected_workflow_id):
    """Decisión pura. Cualquier dato incoherente es un fallo de política."""
    errors = []
    sha = run.get('head_sha', '')
    if run.get('event') != 'pull_request' or run.get('name') != 'Piloto CI':
        errors.append('ORIGEN_CI_INVALIDO')
    if run.get('workflow_id') != expected_workflow_id:
        errors.append('WORKFLOW_ID_INVALIDO')
    if run.get('conclusion') != 'success' or run.get('status') != 'completed':
        errors.append('CI_NO_APROBADA')
    if pr.get('state') != 'open' or pr.get('draft', True):
        errors.append('PR_NO_LISTO')
    if pr.get('base', {}).get('ref') != 'main':
        errors.append('BASE_INCORRECTA')
    if pr.get('head', {}).get('sha') != sha or len(sha) != 40:
        errors.append('SHA_DESACTUALIZADO')
    if pr.get('head', {}).get('repo', {}).get('full_name') != pr.get('base', {}).get('repo', {}).get('full_name'):
        errors.append('FORK_NO_ADMITIDO')
    declared = pr.get('changed_files')
    if not isinstance(declared, int) or declared < 1 or declared > 20 or len(files) != declared:
        errors.append('LISTADO_ARCHIVOS_INCOMPLETO')
    if any(not path_allowed(f.get('filename', '')) for f in files):
        errors.append('RUTA_NO_AUTORIZADA')
    if any(f.get('status') not in ('added', 'modified') for f in files):
        errors.append('OPERACION_ARCHIVO_NO_AUTORIZADA')
    return errors


def api(method, path, data=None):
    token = os.environ['GITHUB_TOKEN']
    headers = {'Authorization': 'Bearer ' + token,
               'Accept': 'application/vnd.github+json',
               'X-GitHub-Api-Version': '2022-11-28',
               'User-Agent': 'nexus-piloto-policy-gate'}
    body = None if data is None else json.dumps(data).encode('utf-8')
    if body is not None:
        headers['Content-Type'] = 'application/json'
    request = Request(BASE + path, method=method, data=body, headers=headers)
    with urlopen(request, timeout=20) as resp:
        return json.load(resp)


def resolve_pr(repo, run):
    """Sólo PR del mismo repo asociados al commit; ambiguos -> fallo cerrado."""
    candidates = run.get('pull_requests') or []
    if not candidates:
        candidates = api('GET', f'/repos/{repo}/commits/{run["head_sha"]}/pulls?per_page=100')
    nums = {p['number'] for p in candidates if isinstance(p.get('number'), int)}
    if len(nums) != 1:
        raise ValueError('PR_NO_UNICO')
    return api('GET', f'/repos/{repo}/pulls/{nums.pop()}')


def main():
    with open(os.environ['GITHUB_EVENT_PATH'], encoding='utf-8') as f:
        event = json.load(f)
    run = event['workflow_run']
    if run.get('event') != 'pull_request':
        print('SKIP: ejecución que no procede de un PR')
        return 0
    repo = os.environ['GITHUB_REPOSITORY']
    if run.get('head_repository', {}).get('full_name') != repo:
        print('SKIP: repositorio de origen diferente')
        return 0
    pr = resolve_pr(repo, run)
    sha = pr.get('head', {}).get('sha')
    if not sha or len(sha) != 40:
        raise ValueError('HEAD_INVALIDO')
    files = api('GET', f'/repos/{repo}/pulls/{pr["number"]}/files?per_page=100')
    workflow = api('GET', f'/repos/{repo}/actions/workflows/{CI_WORKFLOW_FILE}')
    errors = evaluate(run, pr, files, workflow['id'])
    # Un evento viejo no debe publicar check sobre un HEAD distinto.
    if sha != run.get('head_sha'):
        print('SKIP: evento antiguo, espera el workflow_run del nuevo HEAD')
        return 0
    conclusion = 'failure' if errors else 'success'
    summary = ('Políticas automáticas, NO revisión de código independiente. '
               + (', '.join(errors) if errors else 'Rutas y CI confiable verificadas.'))
    result = api('POST', f'/repos/{repo}/check-runs', {
        'name': GATE_NAME, 'head_sha': sha, 'status': 'completed',
        'conclusion': conclusion,
        'details_url': run.get('html_url', ''),
        'output': {'title': 'Políticas de PR: ' + conclusion.upper(), 'summary': summary}
    })
    print(json.dumps({'pr': pr['number'], 'head': sha, 'gate': conclusion,
                      'reasons': errors, 'check_id': result['id']}, sort_keys=True))
    return 1 if errors else 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, KeyError, HTTPError, URLError, TimeoutError, OSError) as exc:
        print('GATE_ERROR_CERRADO: ' + type(exc).__name__, file=sys.stderr)
        sys.exit(2)
