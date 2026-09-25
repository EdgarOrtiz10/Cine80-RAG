"""A2 Forense: valida los datos de una ejecución contra aserciones por workflow.

Uso:
  python -m qa.check_execution <execution.json> <assertions.json> [--format text|json]

<execution.json> es la salida de `get_execution` con includeData=true.
<assertions.json> vive en assertions/<workflowId>.json.

Tipos de aserción:
  nonempty_fields  {node, fields[]}        SF-01: cada item de salida trae esos campos no vacíos
  agent_fallback   {agent, tools[], no_data_pattern}
                                           AG-01: una tool devolvió [] y el agente respondió
                                           "sin datos" sin probar las demás tools
  node_ran         {node}                  GC: el nodo debe haberse ejecutado (golden cases)
  node_not_run     {node}                  GC: el nodo NO debe haberse ejecutado
Además, toda ejecución con status=error genera EX-01.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from .rules import Finding


def _run_data(execution: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    return ((execution.get("data") or {}).get("resultData") or {}).get("runData") or {}


def _output_items(run: dict[str, Any], kind: str = "main") -> list[dict[str, Any]]:
    branches = ((run.get("data") or {}).get(kind)) or []
    return [item.get("json", {}) for branch in branches for item in (branch or [])]


def _is_empty(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def check_nonempty_fields(wf_id: str, exec_id: str, runs: dict, a: dict) -> list[Finding]:
    findings = []
    for i, run in enumerate(runs.get(a["node"], [])):
        for j, item in enumerate(_output_items(run)):
            missing = [f for f in a["fields"] if _is_empty(item.get(f))]
            if missing:
                findings.append(
                    Finding(
                        "SF-01",
                        "high",
                        wf_id,
                        a["node"],
                        f"'{a['node']}' terminó OK con campos vacíos",
                        f"Ejecución {exec_id}, run {i}, item {j}: vacíos {', '.join(missing)}. "
                        f"Salida: {json.dumps(item, ensure_ascii=False)[:300]}",
                    )
                )
    return findings


def check_agent_fallback(wf_id: str, exec_id: str, runs: dict, a: dict) -> list[Finding]:
    pattern = re.compile(a.get("no_data_pattern", r"no encontr|no hay|sin registros|no tengo datos"), re.IGNORECASE)
    findings = []
    for run in runs.get(a["agent"], []):
        answer = " ".join(str(item.get("output", "")) for item in _output_items(run))
        if not pattern.search(answer):
            continue
        called = [t for t in a["tools"] if t in runs]
        empty = [t for t in called if all(not _output_items(r, "ai_tool") for r in runs[t])]
        not_called = [t for t in a["tools"] if t not in runs]
        if empty and not_called:
            findings.append(
                Finding(
                    "AG-01",
                    "medium",
                    wf_id,
                    a["agent"],
                    f"'{a['agent']}' respondió 'sin datos' tras una sola tool vacía",
                    f"Ejecución {exec_id}: tools vacías {empty}; no consultó {not_called}. "
                    f"Respuesta: {answer[:200]}",
                )
            )
    return findings


def check_node_ran(wf_id: str, exec_id: str, runs: dict, a: dict) -> list[Finding]:
    if a["node"] in runs:
        return []
    return [Finding("GC-FAIL", "high", wf_id, a["node"], f"'{a['node']}' debía ejecutarse y no corrió",
                    f"Ejecución {exec_id}. Nodos ejecutados: {', '.join(sorted(runs))[:600]}")]


def check_node_not_run(wf_id: str, exec_id: str, runs: dict, a: dict) -> list[Finding]:
    if a["node"] not in runs:
        return []
    return [Finding("GC-FAIL", "high", wf_id, a["node"], f"'{a['node']}' no debía ejecutarse y corrió",
                    f"Ejecución {exec_id}.")]


CHECKS = {
    "nonempty_fields": check_nonempty_fields,
    "agent_fallback": check_agent_fallback,
    "node_ran": check_node_ran,
    "node_not_run": check_node_not_run,
}


def check_execution(execution: dict[str, Any], assertions: dict[str, Any]) -> list[Finding]:
    meta = execution.get("execution") or {}
    wf_id = meta.get("workflowId") or assertions.get("workflow_id", "unknown")
    exec_id = str(meta.get("id", "?"))
    findings: list[Finding] = []

    if meta.get("status") == "error":
        result = (execution.get("data") or {}).get("resultData") or {}
        err = result.get("error") or {}
        node = (err.get("node") or {}).get("name") or result.get("lastNodeExecuted") or "?"
        findings.append(
            Finding(
                "EX-01",
                "high",
                wf_id,
                node,
                f"Ejecución fallida en '{node}'",
                f"Ejecución {exec_id}: {err.get('message', 'sin mensaje')}",
            )
        )

    runs = _run_data(execution)
    for a in assertions.get("assertions", []):
        findings.extend(CHECKS[a["type"]](wf_id, exec_id, runs, a))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("execution")
    parser.add_argument("assertions")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)

    execution = json.loads(Path(args.execution).read_text(encoding="utf-8"))
    assertions = json.loads(Path(args.assertions).read_text(encoding="utf-8"))
    findings = check_execution(execution, assertions)

    if args.format == "json":
        json.dump([f.to_dict() for f in findings], sys.stdout, ensure_ascii=False, indent=2)
        print()
    else:
        for f in findings:
            print(f"[{f.rule_id}/{f.severity}] {f.title}\n   {f.detail}  fp: {f.fingerprint}")
        if not findings:
            print("OK: sin hallazgos")
    return 1 if any(f.severity == "high" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
