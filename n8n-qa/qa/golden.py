"""A5 Tester: casos golden reproducibles con pin data (sin efectos reales).

Uso:
  python -m qa.golden list <workflowId>
  python -m qa.golden build <workflowId> <case>        -> pinData JSON para test_workflow
  python -m qa.golden check <workflowId> <case> <execution.json>

Estructura: golden/<workflowId>/_base.json   pins de todos los nodos con credenciales
            golden/<workflowId>/<case>.json  {description, origin_bug, message|update, pins, assertions}

`message` (texto) o `update` (update completo de Telegram) define el disparo. El usuario es
ficticio (no está en la allowlist), así que el builder también fija la salida de
'Filtro Allowlist' con el mismo update.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .check_execution import check_execution

GOLDEN_DIR = Path(__file__).parent.parent / "golden"
FAKE_USER = {"id": 999000111, "is_bot": False, "first_name": "QA", "last_name": "Test", "language_code": "es"}


def _load(wf_id: str, name: str) -> dict:
    return json.loads((GOLDEN_DIR / wf_id / f"{name}.json").read_text(encoding="utf-8"))


def build_pin_data(wf_id: str, case_name: str) -> dict:
    base, case = _load(wf_id, "_base"), _load(wf_id, case_name)
    update = case.get("update") or {
        "update_id": 900000001,
        "message": {
            "message_id": 1,
            "from": FAKE_USER,
            "chat": {"id": FAKE_USER["id"], "first_name": "QA", "last_name": "Test", "type": "private"},
            "date": 1790350000,
            "text": case["message"],
        },
    }
    pin_data = {**base["pins"], **base["entry"]}
    pin_data["Telegram Trigger"] = [{"json": update}]
    pin_data["Filtro Allowlist"] = [{"json": update}]
    pin_data.update(case.get("pins", {}))
    return pin_data


def check_case(wf_id: str, case_name: str, execution: dict) -> list:
    case = _load(wf_id, case_name)
    return check_execution(execution, {"workflow_id": wf_id, "assertions": case["assertions"]})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list").add_argument("workflow_id")
    b = sub.add_parser("build")
    b.add_argument("workflow_id")
    b.add_argument("case")
    c = sub.add_parser("check")
    c.add_argument("workflow_id")
    c.add_argument("case")
    c.add_argument("execution")
    args = parser.parse_args(argv)

    if args.cmd == "list":
        for p in sorted((GOLDEN_DIR / args.workflow_id).glob("[!_]*.json")):
            case = json.loads(p.read_text(encoding="utf-8"))
            print(f"{p.stem}\t{case.get('origin_bug', '-')}\t{case['description']}")
        return 0
    if args.cmd == "build":
        json.dump(build_pin_data(args.workflow_id, args.case), sys.stdout, ensure_ascii=False)
        print()
        return 0

    execution = json.loads(Path(args.execution).read_text(encoding="utf-8"))
    findings = check_case(args.workflow_id, args.case, execution)
    status = (execution.get("execution") or {}).get("status")
    for f in findings:
        print(f"FAIL {f.title}\n     {f.detail}")
    print(f"{'PASS' if not findings else 'FAIL'} {args.case} (status={status})")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
