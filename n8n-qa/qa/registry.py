"""A7 (mínimo en F1): registro de bugs deduplicado por fingerprint.

El MCP de n8n solo permite INSERTAR filas en Data Tables (no leerlas ni actualizarlas),
así que la fuente de verdad es state/bug_registry.json (versionado en git) y la Data
Table `bug_registry` se usa como bitácora append-only.

Uso:
  python -m qa.registry merge <findings.json>... [--registry state/bug_registry.json]

Cada <findings.json> es la salida --format json de lint_workflow o check_execution.
Imprime JSON con `new` (filas listas para add_data_table_rows) y `recurring`.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_REGISTRY = Path(__file__).parent.parent / "state" / "bug_registry.json"


def _load_findings(path: str) -> list[dict]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return data["findings"] if isinstance(data, dict) else data


def merge(registry: dict, findings: list[dict], now: str) -> tuple[list[dict], list[dict]]:
    new, recurring = [], []
    for f in findings:
        entry = registry.get(f["fingerprint"])
        if entry:
            entry["last_seen"] = now
            entry["occurrences"] += 1
            # Un bug marcado como resuelto que reaparece es una regresión.
            if entry["status"] == "published":
                entry["status"] = "regression"
            recurring.append(entry)
            continue
        entry = {
            "bug_id": f"QA-{len(registry) + 1:04d}",
            "fingerprint": f["fingerprint"],
            "rule_id": f["rule_id"],
            "workflow_id": f["workflow_id"],
            "node": f["node"],
            "severity": f["severity"],
            "status": "open",
            "title": f["title"],
            "evidence": f["detail"][:1000],
            "root_cause": "",
            "fix_version_id": "",
            "first_seen": now,
            "last_seen": now,
            "occurrences": 1,
        }
        registry[f["fingerprint"]] = entry
        new.append(entry)
    return new, recurring


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("merge")
    m.add_argument("findings", nargs="+")
    m.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    args = parser.parse_args(argv)

    reg_path = Path(args.registry)
    registry = json.loads(reg_path.read_text(encoding="utf-8")) if reg_path.exists() else {}
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    findings = [f for p in args.findings for f in _load_findings(p)]
    new, recurring = merge(registry, findings, now)

    reg_path.parent.mkdir(parents=True, exist_ok=True)
    reg_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    json.dump({"new": new, "recurring": recurring}, sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
