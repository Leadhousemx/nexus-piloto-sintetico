"""Consulta de solo lectura al API de GitHub. No autoriza merge ni declara deployment DONE.

Uso: python verificar_pr.py <owner/repo> <numero_pr>
Opcional: GITHUB_TOKEN de lectura en entorno; nunca se imprime.
"""
import json
import os
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError


def get(path):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "nexus-piloto-verificador"}
    if os.getenv("GITHUB_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    with urlopen(Request("https://api.github.com" + path, headers=headers), timeout=15) as resp:
        return json.load(resp)


def verificar(repo, number):
    pr = get(f"/repos/{repo}/pulls/{number}")
    sha = pr["head"]["sha"]
    result = {"repo": repo, "pr": number, "head_sha": sha, "estado": "NO_APTO", "razones": []}
    if pr["state"] != "open" or pr["draft"]:
        result["razones"].append("PR_NO_ABIERTO_O_DRAFT")
    files = get(f"/repos/{repo}/pulls/{number}/files?per_page=100")
    if len(files) >= 100:
        result["razones"].append("CAMBIOS_NO_COMPLETOS")
    if any(f["filename"].startswith(".github/") for f in files):
        result["razones"].append("CAMBIO_DE_CI_REQUIERE_APROBACION_HUMANA")
    suites = get(f"/repos/{repo}/commits/{sha}/check-runs?per_page=100")
    jobs = [x for x in suites.get("check_runs", []) if x.get("name") == "Piloto CI / Pruebas" and x.get("app", {}).get("slug") == "github-actions"]
    if len(jobs) != 1 or jobs[0].get("status") != "completed" or jobs[0].get("conclusion") != "success":
        result["razones"].append("CI_NO_VERDE_PARA_HEAD")
    reviews = get(f"/repos/{repo}/pulls/{number}/reviews?per_page=100")
    if len(reviews) >= 100:
        result["razones"].append("REVIEWS_NO_COMPLETAS")
    valid = [x for x in reviews if x.get("commit_id") == sha and x.get("user", {}).get("login") != pr["user"]["login"]]
    if not valid or valid[-1].get("state") != "APPROVED":
        result["razones"].append("APROBACION_INDEPENDIENTE_HEAD_AUSENTE")
    if not result["razones"]:
        result["estado"] = "APTO_PARA_REVISION_HUMANA"
    return result


if __name__ == "__main__":
    if len(sys.argv) != 3 or "/" not in sys.argv[1] or not sys.argv[2].isdigit():
        sys.exit("Uso: python verificar_pr.py owner/repo numero_pr")
    try:
        outcome = verificar(sys.argv[1], int(sys.argv[2]))
        print(json.dumps(outcome, indent=2, ensure_ascii=False))
        sys.exit(0 if outcome["estado"] == "APTO_PARA_REVISION_HUMANA" else 1)
    except (HTTPError, OSError, ValueError, KeyError) as exc:
        print(json.dumps({"estado": "NO_VERIFICABLE", "tipo_error": type(exc).__name__}))
        sys.exit(2)
