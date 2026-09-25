"""A1 Linter: análisis estático de un workflow n8n.

Uso:
  python -m qa.lint_workflow <workflow.json> [--format text|json] [--min-severity low|medium|high]

<workflow.json> es la salida de `get_workflow_details` del MCP de n8n o el JSON exportado.
Código de salida: 1 si hay hallazgos `high`, 0 en otro caso.
"""
from __future__ import annotations

import argparse
import json
import sys

from .graph import load_workflow
from .rules import SEVERITY_ORDER, run_rules

ICONS = {"high": "🔴", "medium": "🟠", "low": "🟡"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("path")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--min-severity", choices=list(SEVERITY_ORDER), default="low")
    args = parser.parse_args(argv)

    wf = load_workflow(args.path)
    threshold = SEVERITY_ORDER[args.min_severity]
    findings = [f for f in run_rules(wf) if SEVERITY_ORDER[f.severity] <= threshold]

    if args.format == "json":
        json.dump(
            {"workflow_id": wf.id, "workflow_name": wf.name, "findings": [f.to_dict() for f in findings]},
            sys.stdout,
            ensure_ascii=False,
            indent=2,
        )
        print()
    else:
        print(f"{wf.name} ({wf.id}) — {len(wf.nodes)} nodos, {len(findings)} hallazgos")
        for f in findings:
            print(f"\n{ICONS[f.severity]} [{f.rule_id}] {f.title}\n   nodo: {f.node}  fp: {f.fingerprint}\n   {f.detail}")

    return 1 if any(f.severity == "high" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
