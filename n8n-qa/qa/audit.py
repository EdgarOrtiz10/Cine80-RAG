"""A6 Auditor: auditoría determinista de un borrador frente a la versión publicada.

Uso:
  python -m qa.audit <publicado.json> <borrador.json> [--policy assertions/<wf>.json]
                     [--fixes-dir fixes] [--out audits/<archivo>]

<publicado.json>: salida de `get_workflow_version` (versión activa) o de `get_workflow_details`.
<borrador.json>:  salida de `get_workflow_details` (borrador actual).

Principio: el Auditor NO lee el razonamiento del Fixer. Solo ve el diff, la política del
workflow y el registro de cambios atribuidos (fixes/*.json + reviewed/*.json). Todo cambio que
no esté atribuido a un parche QA registrado o a un diff revisado por un humano bloquea.

Veredictos: APROBADO (sin hallazgos high ni medium) · REVISAR (solo medium) · RECHAZADO (algún high).
Código de salida: 0 APROBADO, 1 REVISAR, 2 RECHAZADO.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .graph import parse_workflow
from .rules import run_rules

ROOT = Path(__file__).parent.parent
RISKY_TYPES = {
    "n8n-nodes-base.httpRequest": "llamada HTTP saliente",
    "n8n-nodes-base.executeCommand": "ejecución de comandos",
    "n8n-nodes-base.ssh": "SSH",
    "n8n-nodes-base.n8n": "API de administración de n8n",
}
RISKY_CODE_RE = re.compile(r"\bfetch\(|require\(|child_process|process\.env|\beval\(|new Function\(")
COMPARED_FIELDS = ("type", "typeVersion", "parameters", "disabled", "onError", "retryOnFail", "maxTries",
                   "waitBetweenTries", "alwaysOutputData", "executeOnce")


@dataclass
class AuditFinding:
    severity: str
    kind: str
    node: str
    detail: str


def _load(path: str | Path) -> dict[str, Any]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    wf = raw.get("workflow", raw)
    # get_workflow_version usa `workflowId`; sin normalizar, las huellas del linter no coinciden.
    wf.setdefault("id", wf.get("workflowId"))
    return wf


def _edges(wf: dict[str, Any]) -> set[tuple[str, int, str]]:
    out = set()
    for src, outputs in (wf.get("connections") or {}).items():
        for kind, branches in outputs.items():
            for idx, branch in enumerate(branches or []):
                for conn in branch or []:
                    out.add((f"{src}", idx if kind == "main" else -1, f"{conn['node']}|{kind}"))
    return out


def attributed_nodes(fixes_dir: Path) -> dict[str, list[str]]:
    """Nodo -> archivos de fix o de revisión que justifican su cambio."""
    attributed: dict[str, list[str]] = {}
    for path in sorted(list(fixes_dir.glob("*.json")) + list((fixes_dir / "reviewed").glob("*.json"))):
        data = json.loads(path.read_text(encoding="utf-8"))
        ops = data if isinstance(data, list) else data.get("operations", [])
        names = set(data.get("nodes", [])) if isinstance(data, dict) else set()
        for op in ops:
            for key in ("nodeName", "source", "target"):
                if op.get(key):
                    names.add(op[key])
            if (op.get("node") or {}).get("name"):
                names.add(op["node"]["name"])
        for n in names:
            attributed.setdefault(n, []).append(path.name)
    return attributed


def audit(published: dict, draft: dict, policy: dict, attributed: dict[str, list[str]]) -> dict[str, Any]:
    pub_nodes = {n["name"]: n for n in published.get("nodes", [])}
    dra_nodes = {n["name"]: n for n in draft.get("nodes", [])}
    sensitive = set(policy.get("sensitive_nodes", []))
    findings: list[AuditFinding] = []
    changes: list[dict[str, Any]] = []

    def note_change(kind: str, node: str, detail: str) -> None:
        changes.append({"kind": kind, "node": node, "detail": detail, "attributed_to": attributed.get(node, [])})
        is_note = node.startswith("Zona:") or dra_nodes.get(node, pub_nodes.get(node, {})).get("type") == "n8n-nodes-base.stickyNote"
        if not attributed.get(node) and not is_note:
            findings.append(AuditFinding("high", "cambio no atribuido", node,
                                         f"{kind}: {detail}. No aparece en ningún fixes/*.json ni reviewed/*.json."))
        if node in sensitive:
            findings.append(AuditFinding("high", "nodo sensible modificado", node,
                                         f"{kind} en un nodo de seguridad declarado en la política. Requiere revisión humana explícita."))

    for name in sorted(set(dra_nodes) - set(pub_nodes)):
        n = dra_nodes[name]
        note_change("nodo añadido", name, n.get("type", ""))
        if n.get("type") in RISKY_TYPES:
            findings.append(AuditFinding("high", "tipo de nodo de riesgo", name, RISKY_TYPES[n["type"]]))
    for name in sorted(set(pub_nodes) - set(dra_nodes)):
        note_change("nodo eliminado", name, pub_nodes[name].get("type", ""))
        if pub_nodes[name].get("type") != "n8n-nodes-base.stickyNote":
            findings.append(AuditFinding("medium", "nodo eliminado", name, "Verifica que ninguna rama dependía de él."))
    for name in sorted(set(pub_nodes) & set(dra_nodes)):
        a, b = pub_nodes[name], dra_nodes[name]
        diff = [f for f in COMPARED_FIELDS if json.dumps(a.get(f), sort_keys=True) != json.dumps(b.get(f), sort_keys=True)]
        if diff:
            note_change("nodo modificado", name, ", ".join(diff))
        if a.get("onError") == "continueErrorOutput" and b.get("onError") != "continueErrorOutput":
            findings.append(AuditFinding("medium", "manejo de errores retirado", name,
                                         f"onError pasó de continueErrorOutput a {b.get('onError') or 'por defecto'}."))

    for name, n in dra_nodes.items():
        code = (n.get("parameters") or {}).get("jsCode") or ""
        if RISKY_CODE_RE.search(code) and code != ((pub_nodes.get(name) or {}).get("parameters") or {}).get("jsCode"):
            findings.append(AuditFinding("high", "código de riesgo", name,
                                         f"Uso nuevo de {RISKY_CODE_RE.search(code).group(0)} en un Code node."))

    added_edges = _edges(draft) - _edges(published)
    removed_edges = _edges(published) - _edges(draft)
    for src, idx, tgt in sorted(added_edges | removed_edges):
        tgt_node = tgt.split("|")[0]
        if not (attributed.get(src) or attributed.get(tgt_node)):
            findings.append(AuditFinding("high", "conexión no atribuida", src,
                                         f"{'+' if (src, idx, tgt) in added_edges else '-'} {src}[{idx}] → {tgt}"))

    lint_pub = {f.fingerprint: f for f in run_rules(parse_workflow(published))}
    lint_dra = {f.fingerprint: f for f in run_rules(parse_workflow(draft))}
    for fp, f in lint_dra.items():
        if fp not in lint_pub and f.rule_id != "VD-01":
            findings.append(AuditFinding("high", f"regresión de linter {f.rule_id}", f.node, f.title))
    lint_fixed = sorted({f"{f.rule_id} {f.node}" for fp, f in lint_pub.items() if fp not in lint_dra})

    unverifiable = ["Credenciales: la API de n8n no las devuelve en versiones ni detalles; revisa en la UI "
                    "que ningún nodo cambió de credencial."]
    if published.get("settings") is None:
        unverifiable.append("Settings del workflow (p. ej. errorWorkflow): la versión publicada no los incluye.")

    severities = {f.severity for f in findings}
    verdict = "RECHAZADO" if "high" in severities else "REVISAR" if "medium" in severities else "APROBADO"
    return {
        "workflow_id": draft.get("id") or published.get("workflowId"),
        "published_version": published.get("versionId"),
        "draft_version": draft.get("versionId"),
        "verdict": verdict,
        "findings": [f.__dict__ for f in findings],
        "changes": changes,
        "edges": {"added": len(added_edges), "removed": len(removed_edges)},
        "lint_fixed": lint_fixed,
        "unverifiable": unverifiable,
    }


def to_markdown(r: dict[str, Any]) -> str:
    icon = {"APROBADO": "✅", "REVISAR": "🟠", "RECHAZADO": "🔴"}[r["verdict"]]
    lines = [
        f"# Auditoría QA — {r['workflow_id']}",
        "",
        f"**Veredicto: {icon} {r['verdict']}**",
        "",
        f"- Publicado: `{r['published_version']}`",
        f"- Borrador auditado: `{r['draft_version']}`",
        f"- Conexiones: +{r['edges']['added']} / -{r['edges']['removed']}",
        "",
        "## Hallazgos del auditor",
        "",
    ]
    lines += [f"- **{f['severity']}** · {f['kind']} · `{f['node']}` — {f['detail']}" for f in r["findings"]] or ["Ninguno."]
    lines += ["", "## Cambios y su atribución", "", "| Cambio | Nodo | Detalle | Atribuido a |", "|---|---|---|---|"]
    lines += [f"| {c['kind']} | {c['node']} | {c['detail']} | {', '.join(c['attributed_to']) or '—'} |" for c in r["changes"]]
    lines += ["", "## Hallazgos del linter que desaparecen", ""]
    lines += [f"- {x}" for x in r["lint_fixed"]] or ["Ninguno."]
    lines += ["", "## No verificable automáticamente", ""]
    lines += [f"- {x}" for x in r["unverifiable"]]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("published")
    parser.add_argument("draft")
    parser.add_argument("--policy")
    parser.add_argument("--fixes-dir", default=str(ROOT / "fixes"))
    parser.add_argument("--out", help="Ruta base; escribe <out>.md y <out>.json")
    args = parser.parse_args(argv)

    policy = json.loads(Path(args.policy).read_text(encoding="utf-8")).get("audit_policy", {}) if args.policy else {}
    report = audit(_load(args.published), _load(args.draft), policy, attributed_nodes(Path(args.fixes_dir)))
    md = to_markdown(report)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.with_suffix(".md").write_text(md, encoding="utf-8")
        out.with_suffix(".json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(md)
    return {"APROBADO": 0, "REVISAR": 1, "RECHAZADO": 2}[report["verdict"]]


if __name__ == "__main__":
    sys.exit(main())
