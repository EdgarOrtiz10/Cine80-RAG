"""Carga de workflows n8n y utilidades de grafo (solo conexiones `main`)."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

# Nodos que reenvían su entrada sin transformarla: al rastrear de dónde viene
# `$json` hay que atravesarlos y seguir subiendo.
PASS_THROUGH_TYPES = {
    "n8n-nodes-base.if",
    "n8n-nodes-base.filter",
    "n8n-nodes-base.switch",
    "n8n-nodes-base.noOp",
    "n8n-nodes-base.wait",
}

SHEETS_WRITE_OPS = {"append", "appendOrUpdate", "update", "delete", "clear"}

SUCCESS_TEXT_RE = re.compile(r"exitosa|registrad|guardad|eliminad|✅", re.IGNORECASE)
FAILURE_TEXT_RE = re.compile(r"no pude|no se|error|fall[oó]|⚠️|❌", re.IGNORECASE)


def is_success_text(text: str) -> bool:
    return bool(SUCCESS_TEXT_RE.search(text)) and not FAILURE_TEXT_RE.search(text)


@dataclass
class Workflow:
    id: str
    name: str
    nodes: dict[str, dict[str, Any]]
    parents: dict[str, list[str]] = field(default_factory=dict)
    children: dict[str, list[str]] = field(default_factory=dict)
    active: bool = False
    version_id: str | None = None
    active_version_id: str | None = None

    def node_type(self, name: str) -> str:
        return self.nodes[name].get("type", "")

    def params(self, name: str) -> dict[str, Any]:
        return self.nodes[name].get("parameters") or {}

    def ignored(self, name: str, rule_id: str) -> bool:
        """Supresión explícita: `qa-ignore: RULE_ID` en las notas del nodo."""
        notes = self.nodes[name].get("notes") or ""
        return f"qa-ignore: {rule_id}" in notes or "qa-ignore: *" in notes


def load_workflow(path: str | Path) -> Workflow:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return parse_workflow(raw)


def parse_workflow(raw: dict[str, Any]) -> Workflow:
    """Acepta la salida de `get_workflow_details` ({workflow: {...}}) o el JSON crudo."""
    wf = raw.get("workflow", raw)
    nodes = {n["name"]: n for n in wf.get("nodes", [])}
    parents: dict[str, list[str]] = {n: [] for n in nodes}
    children: dict[str, list[str]] = {n: [] for n in nodes}
    for source, outputs in (wf.get("connections") or {}).items():
        for branch in outputs.get("main") or []:
            for conn in branch or []:
                target = conn["node"]
                if source in nodes and target in nodes:
                    children[source].append(target)
                    parents[target].append(source)
    return Workflow(
        id=wf.get("id", "unknown"),
        name=wf.get("name", ""),
        nodes=nodes,
        parents=parents,
        children=children,
        active=bool(wf.get("active")),
        version_id=wf.get("versionId"),
        active_version_id=wf.get("activeVersionId"),
    )


def iter_strings(value: Any) -> Iterator[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from iter_strings(v)
    elif isinstance(value, list):
        for v in value:
            yield from iter_strings(v)


def is_telegram_send(wf: Workflow, name: str) -> bool:
    if wf.node_type(name) != "n8n-nodes-base.telegram":
        return False
    p = wf.params(name)
    return p.get("resource", "message") == "message" and p.get("operation", "sendMessage") in {
        "sendMessage",
        "editMessageText",
    }


def is_sheets_write(wf: Workflow, name: str) -> bool:
    return (
        wf.node_type(name) == "n8n-nodes-base.googleSheets"
        and wf.params(name).get("operation") in SHEETS_WRITE_OPS
    )


def is_guard(wf: Workflow, name: str) -> bool:
    """Nodo capaz de detener el flujo si los datos no son válidos."""
    t = wf.node_type(name)
    if t in {"n8n-nodes-base.if", "n8n-nodes-base.filter", "n8n-nodes-base.switch"}:
        return True
    if t == "n8n-nodes-base.code":
        return "throw " in (wf.params(name).get("jsCode") or "")
    return False
